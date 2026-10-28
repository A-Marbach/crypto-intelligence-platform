
import httpx

from app.core.config import TRADING_PAIRS

BITVAVO_API_URL = "https://api.bitvavo.com/v2"


async def get_market_prices():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{BITVAVO_API_URL}/ticker/price"
        )
        response.raise_for_status()

    prices = {
        item["market"]: item["price"]
        for item in response.json()
    }

    return [
        {
            "market": market,
            "price_eur": prices.get(market),
            "available": market in prices,
        }
        for market in TRADING_PAIRS
    ]


async def get_market_candles(
    market: str,
    interval: str = "1h",
    limit: int = 200,
    client: httpx.AsyncClient | None = None,
):
    async def fetch(http_client: httpx.AsyncClient):
        response = await http_client.get(
            f"{BITVAVO_API_URL}/{market}/candles",
            params={"interval": interval, "limit": limit},
        )
        response.raise_for_status()
        return response.json()

    if client is None:
        async with httpx.AsyncClient(timeout=10.0) as new_client:
            raw_candles = await fetch(new_client)
    else:
        raw_candles = await fetch(client)

    candles = [
        {
            "timestamp": int(candle[0]),
            "open": candle[1],
            "high": candle[2],
            "low": candle[3],
            "close": candle[4],
            "volume": candle[5],
        }
        for candle in raw_candles
    ]

    return sorted(candles, key=lambda item: item["timestamp"])
