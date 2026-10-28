
from decimal import Decimal

import pytest

from app.services.indicator_service import (
    calculate_ema,
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
