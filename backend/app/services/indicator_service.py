
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



def calculate_rsi(prices: list, period: int = 14) -> Decimal:
    """
    Calculate RSI using Wilder's smoothing method.

    Prices must be ordered from oldest to newest.
    """
    if period < 1:
        raise ValueError("Period must be positive")

    if len(prices) < period + 1:
        raise ValueError(
            f"At least {period + 1} prices are required"
        )

    try:
        values = [Decimal(str(price)) for price in prices]
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid price data") from exc

    if not all(value.is_finite() and value > 0 for value in values):
        raise ValueError("Prices must be finite and positive")

    changes = [
        values[i] - values[i - 1]
        for i in range(1, len(values))
    ]

    gains = [max(change, Decimal(0)) for change in changes]
    losses = [max(-change, Decimal(0)) for change in changes]

    period_decimal = Decimal(period)

    avg_gain = sum(gains[:period]) / period_decimal
    avg_loss = sum(losses[:period]) / period_decimal

    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (
            avg_gain * (period_decimal - 1) + gain
        ) / period_decimal

        avg_loss = (
            avg_loss * (period_decimal - 1) + loss
        ) / period_decimal

    if avg_loss == 0:
        return Decimal(50) if avg_gain == 0 else Decimal(100)

    if avg_gain == 0:
        return Decimal(0)

    rs = avg_gain / avg_loss

    return Decimal(100) - Decimal(100) / (Decimal(1) + rs)


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




def calculate_atr(candles: list, period: int = 14) -> Decimal:
    """
    Calculate ATR using Wilder's smoothing.
    Candles must be ordered oldest to newest.
    """
    if period < 1:
        raise ValueError("Period must be positive")

    if len(candles) < period + 1:
        raise ValueError(
            f"At least {period + 1} candles are required"
        )

    true_ranges = []
    previous_close = None

    for candle in candles:
        try:
            high = Decimal(str(candle["high"]))
            low = Decimal(str(candle["low"]))
            close = Decimal(str(candle["close"]))
        except (KeyError, InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("Invalid candle data") from exc

        if (
            not all(v.is_finite() and v > 0 for v in (high, low, close))
            or high < low
            or not low <= close <= high
        ):
            raise ValueError("Invalid OHLC data")

        if previous_close is not None:
            true_range = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )
            true_ranges.append(true_range)

        previous_close = close

    period_decimal = Decimal(period)

    atr = sum(true_ranges[:period]) / period_decimal

    for true_range in true_ranges[period:]:
        atr = (
            atr * (period_decimal - 1) + true_range
        ) / period_decimal

    return atr
