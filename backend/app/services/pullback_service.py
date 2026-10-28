
from decimal import Decimal

from app.services.indicator_service import calculate_ema, calculate_atr


def detect_pullback(candles: list) -> dict:
    """
    Detect a preliminary 4H pullback setup.

    Requires at least 200 completed, consecutive candles.
    Data quality must be checked by the caller.
    """
    if len(candles) < 200:
        raise ValueError("At least 200 candles required")

    closes = [Decimal(str(c["close"])) for c in candles]

    # EMA20 immediately before the recent pullback window
    previous_ema20 = calculate_ema(closes[:-4], 20)
    current_ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    atr = calculate_atr(candles, 14)

    if atr <= 0:
        raise ValueError("ATR must be positive")

    current_price = closes[-1]

    # Look at the four candles before the latest one
    previous_closes = closes[-5:-1]
    previous_high = max(previous_closes)
    previous_low = min(previous_closes)

    bullish_trend = current_price > current_ema20 > ema50

    # Was the market previously extended above EMA20?
    previous_extension = (
        previous_high - previous_ema20
    ) / atr

    had_upward_extension = (
        previous_extension >= Decimal("0.5")
    )

    # Has price retreated at least half an ATR?
    retracement = (previous_high - current_price) / atr
    has_retracement = retracement >= Decimal("0.5")

    # Current price is reasonably close to EMA20
    ema_distance = abs(current_price - current_ema20) / atr
    near_ema20 = ema_distance <= Decimal("1")

    # Latest candle recovers relative to preceding close
    recovering = current_price > closes[-2]

    checks = {
        "bullish_4h": bullish_trend,
        "previous_extension": had_upward_extension,
        "retracement": has_retracement,
        "near_ema20": near_ema20,
        "recovering": recovering,
    }

    return {
        "status": (
            "pullback_candidate"
            if all(checks.values())
            else "no_pullback"
        ),
        "checks": checks,
        "ema_distance_atr": str(round(ema_distance, 2)),
        "retracement_atr": str(round(retracement, 2)),
        "previous_range_low": str(previous_low),
        "previous_range_high": str(previous_high),
    }
