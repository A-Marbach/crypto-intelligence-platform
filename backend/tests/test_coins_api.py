
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
