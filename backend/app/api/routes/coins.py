
from fastapi import APIRouter, HTTPException
import httpx

from app.core.config import ALLOWED_COINS, TRADING_PAIRS
from app.services.bitvavo_service import get_market_prices

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
