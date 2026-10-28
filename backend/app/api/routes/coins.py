
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import ALLOWED_COINS, TRADING_PAIRS
from app.services.bitvavo_service import (
    get_market_candles,
    get_market_prices,
)
from app.services.candle_service import validate_candles


router = APIRouter(prefix="/coins", tags=["Coins"])


@router.get("")
def get_coins():
    return {
        "count": len(ALLOWED_COINS),
        "coins": ALLOWED_COINS,
        "trading_pairs": TRADING_PAIRS,
    }


@router.get("/prices")
async def get_coin_prices():
    try:
        return await get_market_prices()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Bitvavo market data unavailable",
        ) from exc


@router.get("/{market}/candles")
async def get_coin_candles(
    market: str,
    interval: Literal["15m", "1h", "4h", "1d"] = "1h",
    limit: int = Query(default=200, ge=1, le=1000),
):
    market = market.upper()

    if market not in TRADING_PAIRS:
        raise HTTPException(
            status_code=404,
            detail="Market not in watchlist",
        )

    try:
        candles = await get_market_candles(
            market=market,
            interval=interval,
            limit=limit,
        )
    except (httpx.HTTPError, ValueError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve Bitvavo candles",
        ) from exc

    result = validate_candles(candles, interval)

    return {
        "market": market,
        "interval": interval,
        "count": result["quality"]["valid_count"],
        "quality": result["quality"],
        "candles": result["candles"],
    }
