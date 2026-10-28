
from typing import Literal
from app.services.report_service import generate_market_report
import httpx
from fastapi import APIRouter, HTTPException
from app.services.scanner_service import scan_market, scan_all_markets
from app.core.config import TRADING_PAIRS
from app.services.scanner_service import scan_market
from app.services.multi_timeframe_service import (
    analyze_market_timeframes,
    scan_all_timeframes,
)

router = APIRouter(prefix="/scanner", tags=["Scanner"])


@router.get("/opportunities")
async def get_opportunities(
    interval: Literal["15m", "1h", "4h", "1d"] = "1h",
):
    return await scan_all_markets(interval)



@router.get("/report/summary")
async def get_market_report():
    return await generate_market_report()


@router.get("/multi-timeframe/opportunities")
async def get_multi_timeframe_opportunities():
    return await scan_all_timeframes()


@router.get("/multi-timeframe/{market}")
async def get_multi_timeframe_analysis(
    market: str,
):
    market = market.upper()

    if market not in TRADING_PAIRS:
        raise HTTPException(
            status_code=404,
            detail="Market not in watchlist",
        )

    try:
        return await analyze_market_timeframes(market)

    except (httpx.HTTPError, ValueError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Multi-timeframe analysis failed",
        ) from exc



@router.get("/{market}")
async def scan_single_market(
    market: str,
    interval: Literal["15m", "1h", "4h", "1d"] = "1h",
):
    market = market.upper()

    if market not in TRADING_PAIRS:
        raise HTTPException(
            status_code=404,
            detail="Market not in watchlist",
        )

    try:
        return await scan_market(market, interval)

    except (httpx.HTTPError, ValueError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Market scan failed",
        ) from exc
