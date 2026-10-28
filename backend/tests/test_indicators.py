
from decimal import Decimal

import pytest

from app.services.indicator_service import (
    calculate_ema,
    calculate_rsi,
    calculate_atr,
    analyze_trend,
)


def test_ema_with_constant_prices():
    prices = [100] * 50

    result = calculate_ema(prices, 20)

    assert result == Decimal("100")


def test_ema_with_rising_prices():
    prices = list(range(100, 300))

    ema20 = calculate_ema(prices, 20)
    ema50 = calculate_ema(prices, 50)

    assert ema20 > ema50


def test_ema_with_insufficient_data():
    prices = [100, 101, 102]

    with pytest.raises(ValueError):
        calculate_ema(prices, 20)


def test_bullish_trend():
    candles = [
        {"close": str(price)}
        for price in range(100, 300)
    ]

    result = analyze_trend(candles)

    assert result["trend"] == "bullish"
    assert Decimal(result["ema20"]) > Decimal(result["ema50"])


def test_rejects_insufficient_candles():
    candles = [{"close": "100"}] * 50

    with pytest.raises(ValueError):
        analyze_trend(candles)



def test_rsi_with_rising_prices():
    prices = list(range(100, 130))

    result = calculate_rsi(prices)

    assert result == Decimal("100")


def test_rsi_with_falling_prices():
    prices = list(range(130, 100, -1))

    result = calculate_rsi(prices)

    assert result == Decimal("0")


def test_rsi_with_constant_prices():
    prices = [100] * 30

    result = calculate_rsi(prices)

    assert result == Decimal("50")


def test_rsi_with_mixed_prices():
    prices = [
        100, 102, 101, 103, 100,
        105, 104, 107, 103, 106,
        108, 105, 110, 109, 111,
        108, 112, 110, 114, 113,
    ]

    result = calculate_rsi(prices)

    assert Decimal("0") < result < Decimal("100")


def test_rsi_with_insufficient_data():
    prices = [100, 102, 103]

    with pytest.raises(ValueError):
        calculate_rsi(prices, period=14)



def test_atr_constant_range():
    candles = [
        {
            "high": "110",
            "low": "90",
            "close": "100",
        }
        for _ in range(30)
    ]

    result = calculate_atr(candles)

    assert result == Decimal("20")


def test_atr_with_price_movement():
    candles = [
        {
            "high": str(110 + i),
            "low": str(90 + i),
            "close": str(100 + i),
        }
        for i in range(30)
    ]

    result = calculate_atr(candles)

    assert result > 0


def test_atr_insufficient_data():
    candles = [
        {"high": "110", "low": "90", "close": "100"}
    ]

    with pytest.raises(ValueError):
        calculate_atr(candles)


def test_atr_rejects_invalid_candle():
    candles = [
        {"high": "90", "low": "110", "close": "100"}
        for _ in range(30)
    ]

    with pytest.raises(ValueError):
        calculate_atr(candles)
