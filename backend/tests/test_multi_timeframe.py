
from app.services.multi_timeframe_service import (
    evaluate_timeframes,
)

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
        "has_gaps": False,
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
