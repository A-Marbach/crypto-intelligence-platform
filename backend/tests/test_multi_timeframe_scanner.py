
import asyncio
from unittest.mock import AsyncMock, patch

import httpx

from app.core.config import TRADING_PAIRS
from app.services.multi_timeframe_service import (
    scan_all_timeframes,
)


def make_result(market, status="candidate", distance="0.5"):
    return {
        "market": market,
        "status": status,
        "ema20_distance_atr": distance,
    }


def test_scans_all_markets():
    async def fake_scan(market):
        return make_result(market)

    with patch(
        "app.services.multi_timeframe_service.analyze_market_timeframes",
        new_callable=AsyncMock,
    ) as mock_scan:
        mock_scan.side_effect = fake_scan
        result = asyncio.run(scan_all_timeframes())

    assert result["scanned"] == len(TRADING_PAIRS) == 14
    assert result["candidate_count"] == 14
    assert len(result["top_candidates"]) == 3
    assert mock_scan.await_count == 14


def test_no_candidates():
    async def fake_scan(market):
        return make_result(market, status="watch")

    with patch(
        "app.services.multi_timeframe_service.analyze_market_timeframes",
        new_callable=AsyncMock,
    ) as mock_scan:
        mock_scan.side_effect = fake_scan
        result = asyncio.run(scan_all_timeframes())

    assert result["candidate_count"] == 0
    assert result["watch_count"] == 14
    assert result["top_candidates"] == []


def test_one_market_error():
    async def fake_scan(market):
        if market == "BTC-EUR":
            raise httpx.ConnectError("Bitvavo unavailable")
        return make_result(market)

    with patch(
        "app.services.multi_timeframe_service.analyze_market_timeframes",
        new_callable=AsyncMock,
    ) as mock_scan:
        mock_scan.side_effect = fake_scan
        result = asyncio.run(scan_all_timeframes())

    assert result["scanned"] == 14
    assert result["error_count"] == 1
    assert result["candidate_count"] == 13


def test_candidate_ranking():
    async def fake_scan(market):
        distances = {
            "BTC-EUR": "0.8",
            "SOL-EUR": "0.2",
            "ETH-EUR": "0.5",
        }

        if market not in distances:
            return make_result(market, status="watch")

        return make_result(
            market,
            distance=distances[market],
        )

    with patch(
        "app.services.multi_timeframe_service.analyze_market_timeframes",
        new_callable=AsyncMock,
    ) as mock_scan:
        mock_scan.side_effect = fake_scan
        result = asyncio.run(scan_all_timeframes())

    markets = [
        item["market"]
        for item in result["top_candidates"]
    ]

    assert markets == ["SOL-EUR", "ETH-EUR", "BTC-EUR"]
