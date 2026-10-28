
import pytest

from app.services.pullback_service import detect_pullback


def make_candles(closes):
    return [
        {
            "open": str(price),
            "high": str(price + 2),
            "low": str(price - 2),
            "close": str(price),
            "volume": "10",
        }
        for price in closes
    ]


def test_rejects_insufficient_data():
    candles = make_candles([100] * 50)

    with pytest.raises(ValueError):
        detect_pullback(candles)


def test_constant_market_has_no_pullback():
    candles = make_candles([100] * 200)

    result = detect_pullback(candles)

    assert result["status"] == "no_pullback"


def test_rising_market_without_retracement():
    closes = list(range(100, 300))
    candles = make_candles(closes)

    result = detect_pullback(candles)

    assert result["status"] == "no_pullback"
    assert result["checks"]["retracement"] is False


def test_pullback_returns_required_checks():
    closes = list(range(100, 295))
    closes += [297, 296, 294, 293, 294]
    candles = make_candles(closes)

    result = detect_pullback(candles)

    assert len(result["checks"]) == 5
    assert "near_ema20" in result["checks"]
    assert "retracement_atr" in result
    assert result["checks"]["recovering"] is True
