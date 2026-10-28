
import asyncio
from datetime import datetime, timezone

import httpx


BASE_URL = "https://api.bitvavo.com/v2"

MARKETS = {
    "HBAR-EUR": [
        "2026-10-18T04:00:00Z",
        "2026-10-25T02:00:00Z",
    ],
    "UNI-EUR": [
        "2026-10-18T03:00:00Z",
        "2026-10-18T04:00:00Z",
        "2026-10-25T03:00:00Z",
    ],
}


def timestamp_ms(value: str) -> int:
    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )
    return int(dt.timestamp() * 1000)


async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        for market, missing_times in MARKETS.items():
            print(f"\nMARKET: {market}")

            for missing_time in missing_times:
                start = timestamp_ms(missing_time)
                end = start + 60 * 60 * 1000

                response = await client.get(
                    f"{BASE_URL}/{market}/candles",
                    params={
                        "interval": "1h",
                        "start": start,
                        "end": end,
                        "limit": 10,
                    },
                )

                response.raise_for_status()
                candles = response.json()

                print(f"\nRequested: {missing_time}")

                if not candles:
                    print("No candles returned")
                    continue

                for candle in candles:
                    candle_time = datetime.fromtimestamp(
                        candle[0] / 1000,
                        tz=timezone.utc,
                    )
                    print(
                        f"Returned: {candle_time.isoformat()} "
                        f"close={candle[4]}"
                    )


if __name__ == "__main__":
    asyncio.run(main())
