
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from app.services.scanner_service import scan_market, scan_all_markets
from app.core.config import TRADING_PAIRS
from app.services.scanner_service import scan_market


router = APIRouter(prefix="/scanner", tags=["Scanner"])


@router.get("/opportunities")
async def get_opportunities(
    interval: Literal["15m", "1h", "4h", "1d"] = "1h",
):
    return await scan_all_markets(interval)


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
