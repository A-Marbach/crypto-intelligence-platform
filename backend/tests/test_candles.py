
import asyncio

import httpx

from app.services.bitvavo_service import get_market_candles


def test_candles_are_sorted_chronologically():
    sample_data = [
        [2000, "110", "120", "105", "115", "5"],
        [1000, "100", "115", "95", "110", "10"],
    ]

    def handler(request):
        assert request.url.path == "/v2/BTC-EUR/candles"
        assert request.url.params["interval"] == "1h"
        assert request.url.params["limit"] == "2"
        return httpx.Response(200, json=sample_data)

    async def run_test():
        transport = httpx.MockTransport(handler)

        async with httpx.AsyncClient(transport=transport) as client:
            return await get_market_candles(
                market="BTC-EUR",
                interval="1h",
                limit=2,
                client=client,
            )

    candles = asyncio.run(run_test())

    assert len(candles) == 2
    assert candles[0]["timestamp"] == 1000
    assert candles[1]["timestamp"] == 2000
    assert candles[0]["close"] == "110"
