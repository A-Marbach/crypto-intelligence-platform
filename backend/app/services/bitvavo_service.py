
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
