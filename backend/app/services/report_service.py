
from app.services.multi_timeframe_service import scan_all_timeframes


CHECK_LABELS = {
    "daily_bullish": "1D trend bullish",
    "four_hour_bullish": "4H trend bullish",
    "near_4h_ema20": "4H price near EMA20",
    "hourly_bullish": "1H trend bullish",
    "hourly_rsi_above_50": "1H RSI above 50",
}


def build_report(scan: dict) -> dict:
    markets = []

    for item in scan["results"]:
        checks = item.get("checks", {})

        passed = [
            CHECK_LABELS[key]
            for key in CHECK_LABELS
            if checks.get(key) is True
        ]

        missing = [
            CHECK_LABELS[key]
            for key in CHECK_LABELS
            if checks.get(key) is False
        ]

        report_item = {
            "market": item["market"],
            "status": item["status"],
            "checks_passed": len(passed),
            "checks_total": len(CHECK_LABELS),
            "passed": passed,
            "missing": missing,
            "reason": item.get("reason"),
        }

        if "timeframes" in item:
            report_item["timeframes"] = {
                interval: {
                    "trend": data["trend"],
                    "rsi14": data["rsi14"],
                }
                for interval, data in item["timeframes"].items()
            }

        markets.append(report_item)

    # Complete candidates first, then near-matches.
    # Skipped/error markets stay last.
    priority = {
        "candidate": 0,
        "watch": 1,
        "skipped": 2,
        "error": 3,
    }

    markets.sort(
        key=lambda item: (
            priority.get(item["status"], 4),
            -item["checks_passed"],
            item["market"],
        )
    )

    return {
        "summary": {
            "scanned": scan["scanned"],
            "candidates": scan["candidate_count"],
            "watch": scan["watch_count"],
            "skipped": scan["skipped_count"],
            "errors": scan["error_count"],
        },
        "markets": markets,
    }


async def generate_market_report() -> dict:
    scan = await scan_all_timeframes()
    return build_report(scan)
