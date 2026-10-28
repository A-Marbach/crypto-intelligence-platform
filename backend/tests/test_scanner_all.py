
import asyncio
from unittest.mock import AsyncMock, patch

import httpx

from app.core.config import TRADING_PAIRS
from app.services.scanner_service import scan_all_markets


def make_result(market, status="interesting", rsi="55"):
    return {
        "market": market,
        "interval": "1h",
        "status": status,
        "rsi14": rsi,
    }


def test_scans_all_14_markets():
    async def fake_scan(market, interval):
        return make_result(market)

    with patch(
        "app.services.scanner_service.scan_market",
        new_callable=AsyncMock,
    ) as mock_scan:
        mock_scan.side_effect = fake_scan
        result = asyncio.run(scan_all_markets("1h"))

    assert result["scanned"] == len(TRADING_PAIRS) == 14
    assert result["interesting_count"] == 14
    assert len(result["top_candidates"]) == 3
    assert mock_scan.await_count == 14


def test_one_market_failure_does_not_stop_scan():
    async def fake_scan(market, interval):
        if market == "BTC-EUR":
            raise httpx.ConnectError("API unavailable")
        return make_result(market)

    with patch(
        "app.services.scanner_service.scan_market",
        new_callable=AsyncMock,
    ) as mock_scan:
        mock_scan.side_effect = fake_scan
        result = asyncio.run(scan_all_markets("1h"))

    assert result["scanned"] == 14
    assert result["interesting_count"] == 13

    btc = next(
        item for item in result["results"]
        if item["market"] == "BTC-EUR"
    )
    assert btc["status"] == "error"


def test_no_opportunities():
    async def fake_scan(market, interval):
        return make_result(market, status="watch")

    with patch(
        "app.services.scanner_service.scan_market",
        new_callable=AsyncMock,
    ) as mock_scan:
        mock_scan.side_effect = fake_scan
        result = asyncio.run(scan_all_markets("1h"))

    assert result["scanned"] == 14
    assert result["interesting_count"] == 0
    assert result["top_candidates"] == []


def test_candidates_are_sorted_by_rsi():
    async def fake_scan(market, interval):
        values = {
            "BTC-EUR": "52",
            "ETH-EUR": "65",
            "SOL-EUR": "58",
        }
        return make_result(
            market,
            status="interesting" if market in values else "watch",
            rsi=values.get(market, "40"),
        )

    with patch(
        "app.services.scanner_service.scan_market",
        new_callable=AsyncMock,
    ) as mock_scan:
        mock_scan.side_effect = fake_scan
        result = asyncio.run(scan_all_markets("1h"))

    markets = [
        item["market"] for item in result["top_candidates"]
    ]

    assert markets == ["ETH-EUR", "SOL-EUR", "BTC-EUR"]
