
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


INTERVAL_MS = {
    "15m": 15 * 60 * 1000,
    "1h": 60 * 60 * 1000,
    "4h": 4 * 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
}


def validate_candles(candles, interval, now_ms=None):
    if interval not in INTERVAL_MS:
        raise ValueError(f"Unsupported interval: {interval}")

    if now_ms is None:
        now_ms = int(
            datetime.now(timezone.utc).timestamp() * 1000
        )

    duration = INTERVAL_MS[interval]
    valid_candles = []
    invalid_count = 0
    unfinished_count = 0
    seen_timestamps = set()

    for candle in sorted(candles, key=lambda c: c["timestamp"]):
        timestamp = candle["timestamp"]

        # Check that candle has finished
        if timestamp + duration > now_ms:
            unfinished_count += 1
            continue

        # Check duplicate timestamps
        if timestamp in seen_timestamps:
            invalid_count += 1
            continue

        seen_timestamps.add(timestamp)

        try:
            open_price = Decimal(str(candle["open"]))
            high = Decimal(str(candle["high"]))
            low = Decimal(str(candle["low"]))
            close = Decimal(str(candle["close"]))
            volume = Decimal(str(candle["volume"]))

            values = (open_price, high, low, close, volume)

            if not all(value.is_finite() for value in values):
                raise ValueError("Non-finite value")

            if (
                low <= 0
                or volume < 0
                or high < low
                or not low <= open_price <= high
                or not low <= close <= high
            ):
                raise ValueError("Invalid OHLCV data")

        except (InvalidOperation, ValueError, KeyError, TypeError):
            invalid_count += 1
            continue

        valid_candles.append(candle)

    # Detect missing intervals
    missing_count = 0

    for previous, current in zip(
        valid_candles, valid_candles[1:]
    ):
        difference = current["timestamp"] - previous["timestamp"]

        if difference > duration:
            missing_count += difference // duration - 1

    return {
        "candles": valid_candles,
        "quality": {
            "valid_count": len(valid_candles),
            "invalid_count": invalid_count,
            "unfinished_count": unfinished_count,
            "missing_count": missing_count,
            "has_gaps": missing_count > 0,
        },
    }
