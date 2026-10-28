
from app.services.report_service import build_report


def test_report_shows_missing_conditions():
    scan = {
        "scanned": 1,
        "candidate_count": 0,
        "watch_count": 1,
        "skipped_count": 0,
        "error_count": 0,
        "results": [
            {
                "market": "BTC-EUR",
                "status": "watch",
                "reason": "Conditions not fully met",
                "checks": {
                    "daily_bullish": False,
    "four_hour_bullish": False,
    "four_hour_pullback": True,
    "hourly_bullish": True,
    "hourly_rsi_above_50": True,
                },
                "timeframes": {
                    "1h": {
                        "trend": "bullish",
                        "rsi14": "53.69",
                    }
                },
            }
        ],
    }

    report = build_report(scan)
    btc = report["markets"][0]

    assert report["summary"]["scanned"] == 1
    assert btc["status"] == "watch"
    assert btc["checks_passed"] == 3
    assert btc["checks_total"] == 5
    assert len(btc["missing"]) == 2
    assert "1D trend bullish" in btc["missing"]
    assert btc["timeframes"]["1h"]["rsi14"] == "53.69"


def test_report_handles_skipped_market():
    scan = {
        "scanned": 1,
        "candidate_count": 0,
        "watch_count": 0,
        "skipped_count": 1,
        "error_count": 0,
        "results": [
            {
                "market": "HBAR-EUR",
                "status": "skipped",
                "reason": "Insufficient 1h candle quality",
            }
        ],
    }

    report = build_report(scan)
    market = report["markets"][0]

    assert market["status"] == "skipped"
    assert market["checks_passed"] == 0
    assert market["missing"] == []
