
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_coins_count():
    response = client.get("/api/v1/coins")

    assert response.status_code == 200
    assert response.json()["count"] == 14


def test_invalid_market():
    response = client.get(
        "/api/v1/coins/INVALID-EUR/candles"
    )

    assert response.status_code == 404


def test_invalid_interval():
    response = client.get(
        "/api/v1/coins/BTC-EUR/candles",
        params={"interval": "2h"},
    )

    assert response.status_code == 422


def test_bitvavo_api_failure():
    with patch(
        "app.api.routes.coins.get_market_candles",
        new_callable=AsyncMock,
    ) as mock_candles:
        mock_candles.side_effect = httpx.ConnectError(
            "Bitvavo unavailable"
        )

        response = client.get(
            "/api/v1/coins/BTC-EUR/candles"
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Unable to retrieve Bitvavo candles"
    }



def test_trend_bullish():
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
        "app.api.routes.coins.get_market_candles",
        new_callable=AsyncMock,
    ) as mock_candles:
        mock_candles.return_value = candles

        with patch(
            "app.api.routes.coins.validate_candles",
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

            response = client.get(
                "/api/v1/coins/BTC-EUR/trend"
            )

    assert response.status_code == 200
    assert response.json()["trend"] == "bullish"


def test_trend_insufficient_data():
    with patch(
        "app.api.routes.coins.get_market_candles",
        new_callable=AsyncMock,
    ) as mock_candles:
        mock_candles.return_value = []

        response = client.get(
            "/api/v1/coins/BTC-EUR/trend"
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Not enough completed candles"
    )


def test_trend_bitvavo_failure():
    with patch(
        "app.api.routes.coins.get_market_candles",
        new_callable=AsyncMock,
    ) as mock_candles:
        mock_candles.side_effect = httpx.ConnectError(
            "Bitvavo unavailable"
        )

        response = client.get(
            "/api/v1/coins/BTC-EUR/trend"
        )

    assert response.status_code == 502
