
import asyncio
from datetime import datetime, timezone

from app.services.bitvavo_service import get_market_candles
from app.services.candle_service import (
    INTERVAL_MS,
    validate_candles,
)


def format_time(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(
        timestamp_ms / 1000,
        tz=timezone.utc,
    ).strftime("%Y-%m-%d %H:%M UTC")


async def check_market(market: str) -> None:
    interval = "1h"
    duration = INTERVAL_MS[interval]

    print(f"\n{'=' * 50}")
    print(f"MARKET: {market}")
    print(f"{'=' * 50}")

    raw_candles = await get_market_candles(
        market=market,
        interval=interval,
        limit=500,
    )

    validated = validate_candles(
        raw_candles,
        interval,
    )

    candles = validated["candles"]
    quality = validated["quality"]

    print(f"Valid candles: {quality['valid_count']}")
    print(f"Invalid candles: {quality['invalid_count']}")
    print(f"Unfinished candles: {quality['unfinished_count']}")
    print(f"Missing candles: {quality['missing_count']}")

    if candles:
        print(f"First candle: {format_time(candles[0]['timestamp'])}")
        print(f"Last candle:  {format_time(candles[-1]['timestamp'])}")

    gaps_found = 0

    for previous, current in zip(candles, candles[1:]):
        previous_ts = previous["timestamp"]
        current_ts = current["timestamp"]

        difference = current_ts - previous_ts

        if difference > duration:
            gaps_found += 1

            missing = difference // duration - 1

            print("\nGAP DETECTED")
            print(f"Previous: {format_time(previous_ts)}")
            print(f"Next:     {format_time(current_ts)}")
            print(f"Missing intervals: {missing}")

            for index in range(1, missing + 1):
                missing_ts = previous_ts + index * duration
                print(f"Missing:  {format_time(missing_ts)}")

    if gaps_found == 0:
        print("\nNo gaps detected.")


async def main() -> None:
    await check_market("HBAR-EUR")
    await check_market("UNI-EUR")


if __name__ == "__main__":
    asyncio.run(main())
