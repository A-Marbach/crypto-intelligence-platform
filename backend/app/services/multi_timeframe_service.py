
import asyncio
from decimal import Decimal, InvalidOperation

import httpx

from app.core.config import TRADING_PAIRS
from app.services.bitvavo_service import get_market_candles
from app.services.candle_service import validate_candles
from app.services.indicator_service import (
    analyze_trend,
    calculate_atr,
    calculate_rsi,
)
from app.services.pullback_service import detect_pullback


def evaluate_timeframes(
    daily: dict,
    four_hour: dict,
    hourly: dict,
) -> dict:
    """
    Evaluate multi-timeframe conditions.

    Input data must come from validated, completed candles.
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

        values = (price_4h, ema20_4h, atr_4h, rsi_1h)

        if not all(value.is_finite() for value in values):
            raise ValueError("Non-finite indicator")

        if (
            price_4h <= 0
            or ema20_4h <= 0
            or atr_4h <= 0
            or not Decimal("0") <= rsi_1h <= Decimal("100")
        ):
            raise ValueError("Invalid indicator values")

    except (KeyError, InvalidOperation, TypeError) as exc:
        raise ValueError("Invalid timeframe data") from exc

    ema_distance_atr = abs(price_4h - ema20_4h) / atr_4h

    checks = {
        "daily_bullish": daily_bullish,
        "four_hour_bullish": four_hour_bullish,
        "near_4h_ema20": ema_distance_atr <= Decimal("1"),
        "hourly_bullish": hourly_bullish,
        "hourly_rsi_above_50": rsi_1h > Decimal("50"),
    }

    status = "candidate" if all(checks.values()) else "watch"

    return {
        "status": status,
        "reason": (
            "Multi-timeframe conditions aligned"
            if status == "candidate"
            else "Multi-timeframe conditions not fully met"
        ),
        "checks": checks,
        "ema20_distance_atr": str(round(ema_distance_atr, 2)),
        "rsi_1h": str(rsi_1h),
    }


async def analyze_market_timeframes(market: str) -> dict:
    """
    Analyze daily, 4-hour and 1-hour conditions
    including a preliminary 4H pullback pattern.

    No trades are executed.
    """
    analyses = {}
    four_hour_candles = None

    for interval in ("1d", "4h", "1h"):
        raw_candles = await get_market_candles(
            market=market,
            interval=interval,
            limit=250,
        )

        validated = validate_candles(raw_candles, interval)
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

        if interval == "4h":
            four_hour_candles = candles

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

    pullback = detect_pullback(four_hour_candles)

    # Replace simple EMA proximity with pullback detection.
    evaluation["checks"].pop("near_4h_ema20", None)

    evaluation["checks"]["four_hour_pullback"] = (
        pullback["status"] == "pullback_candidate"
    )

    # A candidate must satisfy every required condition.
    candidate = all(evaluation["checks"].values())

    evaluation["status"] = (
        "candidate" if candidate else "watch"
    )

    evaluation["reason"] = (
        "Multi-timeframe trend and pullback conditions aligned"
        if candidate
        else "Multi-timeframe conditions not fully met"
    )

    return {
        "market": market,
        **evaluation,
        "pullback": pullback,
        "timeframes": analyses,
    }


async def scan_all_timeframes() -> dict:
    """
    Analyze all 14 watchlist markets.

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

    # Preliminary ranking: 4H EMA20 proximity.
    # This is not a profitability score.
    candidates.sort(
        key=lambda item: Decimal(item["ema20_distance_atr"])
    )

    return {
        "scanned": len(results),
        "candidate_count": len(candidates),
        "watch_count": sum(
            item["status"] == "watch"
            for item in results
        ),
        "skipped_count": sum(
            item["status"] == "skipped"
            for item in results
        ),
        "error_count": sum(
            item["status"] == "error"
            for item in results
        ),
        "top_candidates": candidates[:3],
        "results": results,
    }
