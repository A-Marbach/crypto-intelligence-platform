
from decimal import Decimal

from app.services.bitvavo_service import get_market_candles
from app.services.candle_service import validate_candles
from app.services.indicator_service import (
    analyze_trend,
    calculate_rsi,
    calculate_atr,
)

import asyncio

import httpx

from app.core.config import TRADING_PAIRS


async def scan_market(market: str, interval: str = "1h") -> dict:
    """
    Analyze a market using completed candles.

    Returns a watchlist candidate, not a trade signal.
    """
    candles = await get_market_candles(
        market=market,
        interval=interval,
        limit=250,
    )

    result = validate_candles(candles, interval)
    quality = result["quality"]
    valid_candles = result["candles"]

    if (
        quality["invalid_count"] > 0
        or quality["has_gaps"]
        or len(valid_candles) < 200
    ):
        return {
            "market": market,
            "status": "skipped",
            "reason": "Insufficient candle data quality",
            "quality": quality,
        }

    trend = analyze_trend(valid_candles)

    closes = [candle["close"] for candle in valid_candles]

    rsi = calculate_rsi(closes, period=14)
    atr = calculate_atr(valid_candles, period=14)

    price = Decimal(trend["price"])
    atr_percent = (atr / price) * Decimal("100")

    positive_trend = trend["trend"] == "bullish"
    positive_momentum = rsi > Decimal("50")

    if positive_trend and positive_momentum:
        status = "interesting"
        reason = "Bullish EMA trend and positive RSI momentum"
    else:
        status = "watch"
        reason = "Trend or momentum conditions not fully met"

    return {
        "market": market,
        "interval": interval,
        "status": status,
        "reason": reason,
        "price": trend["price"],
        "ema20": trend["ema20"],
        "ema50": trend["ema50"],
        "trend": trend["trend"],
        "rsi14": str(round(rsi, 2)),
        "atr14": str(round(atr, 8)),
        "atr_percent": str(round(atr_percent, 2)),
        "quality": quality,
    }


async def scan_all_markets(interval: str = "1h") -> dict:
    semaphore = asyncio.Semaphore(4)

    async def scan_one(market: str) -> dict:
        async with semaphore:
            try:
                return await scan_market(market, interval)
            except (httpx.HTTPError, ValueError, IndexError,
                    KeyError, TypeError):
                return {
                    "market": market,
                    "interval": interval,
                    "status": "error",
                    "reason": "Market analysis failed",
                }

    results = await asyncio.gather(
        *(scan_one(market) for market in TRADING_PAIRS)
    )

    interesting = [
        item for item in results
        if item["status"] == "interesting"
    ]

    interesting.sort(
        key=lambda item: Decimal(item["rsi14"]),
        reverse=True,
    )

    return {
        "interval": interval,
        "scanned": len(results),
        "interesting_count": len(interesting),
        "top_candidates": interesting[:3],
        "results": results,
    }
