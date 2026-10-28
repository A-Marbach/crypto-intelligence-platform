
from app.services.multi_timeframe_service import (
    evaluate_timeframes,
)

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import asyncio

from app.services.multi_timeframe_service import analyze_market_timeframes


def make_data():
    daily = {"trend": "bullish"}

    four_hour = {
        "trend": "bullish",
        "price": "100",
        "ema20": "99.5",
        "atr14": "2",
    }

    hourly = {
        "trend": "bullish",
        "rsi14": "56",
    }

    return daily, four_hour, hourly


def test_valid_candidate():
    result = evaluate_timeframes(*make_data())

    assert result["status"] == "candidate"
    assert all(result["checks"].values())


def test_bearish_daily_trend():
    daily, four_hour, hourly = make_data()
    daily["trend"] = "bearish"

    result = evaluate_timeframes(daily, four_hour, hourly)

    assert result["status"] == "watch"
    assert result["checks"]["daily_bullish"] is False


def test_no_pullback_zone():
    daily, four_hour, hourly = make_data()
    four_hour["price"] = "110"

    result = evaluate_timeframes(daily, four_hour, hourly)

    assert result["status"] == "watch"
    assert result["checks"]["near_4h_ema20"] is False


def test_weak_hourly_momentum():
    daily, four_hour, hourly = make_data()
    hourly["rsi14"] = "45"

    result = evaluate_timeframes(daily, four_hour, hourly)

    assert result["status"] == "watch"
    assert result["checks"]["hourly_rsi_above_50"] is False


def test_invalid_atr():
    daily, four_hour, hourly = make_data()
    four_hour["atr14"] = "0"

    try:
        evaluate_timeframes(daily, four_hour, hourly)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")



def test_no_pullback_prevents_candidate():
    candles = [
        {
            "timestamp": i * 3_600_000,
            "open": str(100 + i),
            "high": str(110 + i),
            "low": str(90 + i),
            "close": str(100 + i),
            "volume": "10",
        }
        for i in range(250)
    ]

    quality = {
    "valid_count": 250,
    "invalid_count": 0,
    "unfinished_count": 0,
    "missing_count": 0,
    "missing_timestamps": [],
    "has_gaps": False,
    "last_candle_timestamp": candles[-1]["timestamp"],
    "expected_last_timestamp": candles[-1]["timestamp"],
    "is_fresh": True,
}

    with (
        patch(
            "app.services.multi_timeframe_service.get_market_candles",
            new_callable=AsyncMock,
            return_value=candles,
        ),
        patch(
            "app.services.multi_timeframe_service.validate_candles",
            return_value={"candles": candles, "quality": quality},
        ),
        patch(
            "app.services.multi_timeframe_service.detect_pullback",
            return_value={
                "status": "no_pullback",
                "checks": {},
            },
        ),
    ):
        result = asyncio.run(analyze_market_timeframes("BTC-EUR"))

    assert result["status"] == "watch"
    assert result["checks"]["four_hour_pullback"] is False



def test_stale_candles_prevent_analysis():
    candles = [
        {
            "timestamp": i * 3_600_000,
            "open": "100",
            "high": "110",
            "low": "90",
            "close": "100",
            "volume": "10",
        }
        for i in range(250)
    ]

    quality = {
        "valid_count": 250,
        "invalid_count": 0,
        "unfinished_count": 0,
        "missing_count": 0,
        "has_gaps": False,
        "is_fresh": False,
    }

    with (
        patch(
            "app.services.multi_timeframe_service.get_market_candles",
            new_callable=AsyncMock,
            return_value=candles,
        ),
        patch(
            "app.services.multi_timeframe_service.validate_candles",
            return_value={"candles": candles, "quality": quality},
        ),
    ):
        result = asyncio.run(
            analyze_market_timeframes("BTC-EUR")
        )

    assert result["status"] == "skipped"
    assert result["reason"] == "Insufficient 1d candle quality"
    assert result["quality"]["is_fresh"] is False



def test_all_timeframes_use_same_analysis_timestamp():
    candles = [
        {
            "timestamp": i * 3_600_000,
            "open": "100",
            "high": "110",
            "low": "90",
            "close": "100",
            "volume": "10",
        }
        for i in range(250)
    ]

    quality = {
        "valid_count": 250,
        "invalid_count": 0,
        "unfinished_count": 0,
        "missing_count": 0,
        "has_gaps": False,
        "is_fresh": True,
    }

    timestamps = []

    def mock_validate(candles, interval, now_ms=None):
        timestamps.append(now_ms)

        return {
            "candles": candles,
            "quality": quality,
        }

    with (
        patch(
            "app.services.multi_timeframe_service.get_market_candles",
            new_callable=AsyncMock,
            return_value=candles,
        ),
        patch(
            "app.services.multi_timeframe_service.validate_candles",
            side_effect=mock_validate,
        ),
        patch(
            "app.services.multi_timeframe_service.detect_pullback",
            return_value={
                "status": "no_pullback",
                "checks": {},
            },
        ),
    ):
        asyncio.run(analyze_market_timeframes("BTC-EUR"))

    assert len(timestamps) == 3
    assert all(timestamp is not None for timestamp in timestamps)
    assert len(set(timestamps)) == 1



def test_analysis_uses_60_second_publication_buffer():
    candles = [
        {
            "timestamp": i * 3_600_000,
            "open": "100",
            "high": "110",
            "low": "90",
            "close": "100",
            "volume": "10",
        }
        for i in range(250)
    ]

    quality = {
        "valid_count": 250,
        "invalid_count": 0,
        "unfinished_count": 0,
        "missing_count": 0,
        "has_gaps": False,
        "is_fresh": True,
    }

    observed_timestamps = []

    def mock_validate(candles, interval, now_ms=None):
        observed_timestamps.append(now_ms)
        return {
            "candles": candles,
            "quality": quality,
        }

    fixed_time = datetime(
        2026, 10, 28, 21, 0, 30,
        tzinfo=timezone.utc,
    )

    with (
        patch(
            "app.services.multi_timeframe_service.datetime"
        ) as mock_datetime,
        patch(
            "app.services.multi_timeframe_service.get_market_candles",
            new_callable=AsyncMock,
            return_value=candles,
        ),
        patch(
            "app.services.multi_timeframe_service.validate_candles",
            side_effect=mock_validate,
        ),
        patch(
            "app.services.multi_timeframe_service.detect_pullback",
            return_value={
                "status": "no_pullback",
                "checks": {},
            },
        ),
    ):
        mock_datetime.now.return_value = fixed_time

        asyncio.run(
            analyze_market_timeframes("BTC-EUR")
        )

    expected_timestamp = (
        int(fixed_time.timestamp() * 1000) - 60_000
    )

    assert observed_timestamps == [
        expected_timestamp,
        expected_timestamp,
        expected_timestamp,
    ]
