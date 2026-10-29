
import hashlib
import hmac
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

BITVAVO_BASE_URL = "https://api.bitvavo.com"


class BitvavoAccountService:
    def __init__(self):
        self.api_key = os.getenv("BITVAVO_API_KEY")
        self.api_secret = os.getenv("BITVAVO_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise ValueError("Bitvavo API-Zugangsdaten fehlen.")

    def get_balances(self):
        timestamp = str(int(time.time() * 1000))
        method = "GET"
        endpoint = "/v2/balance"

        message = timestamp + method + endpoint

        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "Bitvavo-Access-Key": self.api_key,
            "Bitvavo-Access-Timestamp": timestamp,
            "Bitvavo-Access-Signature": signature,
            "Bitvavo-Access-Window": "10000",
            "Accept": "application/json",
        }

        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                BITVAVO_BASE_URL + endpoint,
                headers=headers,
            )

        response.raise_for_status()
        data = response.json()

        return [
            {
                "symbol": item["symbol"],
                "available": item["available"],
                "in_order": item["inOrder"],
                "total": str(
                    float(item["available"]) + float(item["inOrder"])
                ),
            }
            for item in data
        ]
    
    def get_transactions(self):
        timestamp = str(int(time.time() * 1000))
        endpoint = "/v2/account/history"

        message = timestamp + "GET" + endpoint

        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "Bitvavo-Access-Key": self.api_key,
            "Bitvavo-Access-Timestamp": timestamp,
            "Bitvavo-Access-Signature": signature,
            "Bitvavo-Access-Window": "10000",
            "Accept": "application/json",
        }

        with httpx.Client(timeout=15.0) as client:
            response = client.get(
                BITVAVO_BASE_URL + endpoint,
                headers=headers,
            )

        response.raise_for_status()
        return response.json()

