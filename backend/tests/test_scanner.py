
import asyncio
from unittest.mock import AsyncMock, patch

from app.services.scanner_service import scan_market


def test_scanner_identifies_bullish_candidate():
    candles = [
        {
            "timestamp": i * 3_600_000,
            "open": str(100 + i),
            "high": str(110 + i),
            "low": str(90 + i),
            "close": str(100 + i),
            "volume": "10",
        }
        for i in range(250)
    ]

    with patch(
        "app.services.scanner_service.get_market_candles",
        new_callable=AsyncMock,
    ) as mock_fetch:
        mock_fetch.return_value = candles

        with patch(
            "app.services.scanner_service.validate_candles"
        ) as mock_validate:
            mock_validate.return_value = {
                "candles": candles,
                "quality": {
                    "valid_count": 250,
                    "invalid_count": 0,
                    "unfinished_count": 0,
                    "missing_count": 0,
                    "has_gaps": False,
                },
            }

            result = asyncio.run(
                scan_market("BTC-EUR", "1h")
            )

    assert result["market"] == "BTC-EUR"
    assert result["trend"] == "bullish"
    assert result["status"] == "interesting"
    assert float(result["rsi14"]) > 50
    assert float(result["atr_percent"]) > 0
