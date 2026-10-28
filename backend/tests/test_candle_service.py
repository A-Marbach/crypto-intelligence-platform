
from app.services.candle_service import validate_candles


HOUR = 3_600_000


def make_candle(timestamp, close="100"):
    return {
        "timestamp": timestamp,
        "open": "100",
        "high": "110",
        "low": "90",
        "close": close,
        "volume": "10",
    }


def test_excludes_unfinished_candle():
    candles = [
        make_candle(0),
        make_candle(HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=HOUR + 30 * 60 * 1000,
    )

    assert result["quality"]["valid_count"] == 1
    assert result["quality"]["unfinished_count"] == 1


def test_detects_missing_candles():
    candles = [
        make_candle(0),
        make_candle(2 * HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=3 * HOUR,
    )

    assert result["quality"]["missing_count"] == 1
    assert result["quality"]["has_gaps"] is True


def test_rejects_invalid_prices():
    candles = [
        make_candle(0, close="200"),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=HOUR,
    )

    assert result["quality"]["valid_count"] == 0
    assert result["quality"]["invalid_count"] == 1


def test_accepts_valid_candles():
    candles = [
        make_candle(0),
        make_candle(HOUR),
    ]

    result = validate_candles(
        candles,
        interval="1h",
        now_ms=2 * HOUR,
    )

    assert result["quality"]["valid_count"] == 2
    assert result["quality"]["has_gaps"] is False
