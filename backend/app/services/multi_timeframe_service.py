
import asyncio
import httpx

from app.core.config import TRADING_PAIRS

from decimal import Decimal, InvalidOperation
from app.services.bitvavo_service import get_market_candles
from app.services.candle_service import validate_candles
from app.services.indicator_service import (
    analyze_trend,
    calculate_rsi,
    calculate_atr,
)


def evaluate_timeframes(
    daily: dict,
    four_hour: dict,
    hourly: dict,
) -> dict:
    """
    Evaluate a multi-timeframe watchlist candidate.

    Inputs must come from validated, completed candles.
    This is a screening heuristic, not a trade signal.
    """
    try:
        daily_bullish = daily["trend"] == "bullish"
        four_hour_bullish = four_hour["trend"] == "bullish"
        hourly_bullish = hourly["trend"] == "bullish"

        price_4h = Decimal(str(four_hour["price"]))
        ema20_4h = Decimal(str(four_hour["ema20"]))
        atr_4h = Decimal(str(four_hour["atr14"]))
        rsi_1h = Decimal(str(hourly["rsi14"]))

        if not all(
            v.is_finite()
            for v in (price_4h, ema20_4h, atr_4h, rsi_1h)
        ):
            raise ValueError("Non-finite indicator")

        if (
            price_4h <= 0
            or ema20_4h <= 0
            or atr_4h <= 0
            or not 0 <= rsi_1h <= 100
        ):
            raise ValueError("Invalid indicator values")

    except (KeyError, InvalidOperation, TypeError) as exc:
        raise ValueError("Invalid timeframe data") from exc

    # Proximity to EMA20: preliminary pullback heuristic
    ema_distance_atr = (
        abs(price_4h - ema20_4h) / atr_4h
    )

    pullback_zone = ema_distance_atr <= Decimal("1")
    momentum_confirmed = rsi_1h > Decimal("50")

    checks = {
        "daily_bullish": daily_bullish,
        "four_hour_bullish": four_hour_bullish,
        "near_4h_ema20": pullback_zone,
        "hourly_bullish": hourly_bullish,
        "hourly_rsi_above_50": momentum_confirmed,
    }

    if all(checks.values()):
        status = "candidate"
        reason = "Multi-timeframe conditions aligned"
    else:
        status = "watch"
        reason = "Multi-timeframe conditions not fully met"

    return {
        "status": status,
        "reason": reason,
        "checks": checks,
        "ema20_distance_atr": str(
            round(ema_distance_atr, 2)
        ),
        "rsi_1h": str(rsi_1h),
    }


async def analyze_market_timeframes(market: str) -> dict:
    """
    Analyze daily, 4-hour and 1-hour market conditions.
    Does not execute trades.
    """
    analyses = {}

    for interval in ("1d", "4h", "1h"):
        raw_candles = await get_market_candles(
            market=market,
            interval=interval,
            limit=250,
        )

        validated = validate_candles(
            raw_candles,
            interval,
        )

        candles = validated["candles"]
        quality = validated["quality"]

        if (
            len(candles) < 200
            or quality["invalid_count"] > 0
            or quality["has_gaps"]
        ):
            return {
                "market": market,
                "status": "skipped",
                "reason": f"Insufficient {interval} candle quality",
                "quality": quality,
            }

        trend = analyze_trend(candles)
        closes = [candle["close"] for candle in candles]

        rsi = calculate_rsi(closes, 14)
        atr = calculate_atr(candles, 14)

        analyses[interval] = {
            **trend,
            "rsi14": str(round(rsi, 2)),
            "atr14": str(atr),
        }

    evaluation = evaluate_timeframes(
        daily=analyses["1d"],
        four_hour=analyses["4h"],
        hourly=analyses["1h"],
    )

    return {
        "market": market,
        **evaluation,
        "timeframes": analyses,
    }



async def scan_all_timeframes() -> dict:
    """
    Scan all watchlist markets on 1D, 4H and 1H.

    Returns candidates for manual TradingView analysis.
    No orders are executed.
    """
    semaphore = asyncio.Semaphore(4)

    async def scan_one(market: str) -> dict:
        async with semaphore:
            try:
                return await analyze_market_timeframes(market)
            except (
                httpx.HTTPError,
                ValueError,
                TypeError,
                KeyError,
                IndexError,
                ZeroDivisionError,
            ):
                return {
                    "market": market,
                    "status": "error",
                    "reason": "Multi-timeframe analysis failed",
                }

    results = await asyncio.gather(
        *(scan_one(market) for market in TRADING_PAIRS)
    )

    candidates = [
        item
        for item in results
        if item["status"] == "candidate"
    ]

    # Preliminary ranking: proximity to the 4H EMA20.
    # This does not measure expected profitability.
    candidates.sort(
        key=lambda item: Decimal(item["ema20_distance_atr"])
    )

    return {
        "scanned": len(results),
        "candidate_count": len(candidates),
        "watch_count": sum(
            item["status"] == "watch" for item in results
        ),
        "skipped_count": sum(
            item["status"] == "skipped" for item in results
        ),
        "error_count": sum(
            item["status"] == "error" for item in results
        ),
        "top_candidates": candidates[:3],
        "results": results,
    }
