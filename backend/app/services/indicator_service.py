
from decimal import Decimal, InvalidOperation


def calculate_ema(prices: list, period: int) -> Decimal:
    """
    Calculate EMA using an SMA as the initial value.

    Prices must be ordered from oldest to newest.
    """
    if period < 1:
        raise ValueError("Period must be positive")

    if len(prices) < period:
        raise ValueError(
            f"At least {period} prices are required"
        )

    try:
        values = [Decimal(str(price)) for price in prices]
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid price data") from exc

    if not all(price.is_finite() and price > 0 for price in values):
        raise ValueError("Prices must be finite and positive")

    # Initial EMA: simple moving average
    ema = sum(values[:period]) / Decimal(period)

    # Exponential weighting factor
    multiplier = Decimal(2) / Decimal(period + 1)

    for price in values[period:]:
        ema = (price - ema) * multiplier + ema

    return ema


def analyze_trend(candles: list) -> dict:
    """
    Analyze trend using EMA20 and EMA50.
    Requires at least 200 consecutive, closed candles.
    """
    if len(candles) < 200:
        raise ValueError(
            "At least 200 candles are required"
        )

    closes = [candle["close"] for candle in candles]

    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    current_price = Decimal(str(closes[-1]))

    if current_price > ema20 > ema50:
        trend = "bullish"
    elif current_price < ema20 < ema50:
        trend = "bearish"
    else:
        trend = "neutral"

    return {
        "price": str(current_price),
        "ema20": str(ema20),
        "ema50": str(ema50),
        "trend": trend,
    }
