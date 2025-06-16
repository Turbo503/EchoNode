# ---------------------------------------------------------------
# Thin, ccxt-style REST adapter for Bitunix spot market.
# Only the endpoints EchoNode needs: klines, depth, market & limit orders.
# ---------------------------------------------------------------
from __future__ import annotations

import os
import time
import hmac
import hashlib
import json
import requests
from typing import Any, Dict, List

# --- credentials & base URL ------------------------------------
BASE = "https://openapi.bitunix.com"  # REST host
API_KEY = os.getenv("BITUNIX_KEY")
API_SECRET = os.getenv("BITUNIX_SECRET")
HEADERS = {"Content-Type": "application/json"}

# --- internal helpers ------------------------------------------

def _sign(query: str) -> str:
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()


def _auth_headers(query: str) -> Dict[str, str]:
    if not API_KEY or not API_SECRET:
        raise EnvironmentError("Set BITUNIX_KEY and BITUNIX_SECRET")

    h = HEADERS.copy()
    h["X-API-KEY"] = API_KEY
    h["X-SIGNATURE"] = _sign(query)
    return h


def _get(path: str, params: Dict[str, Any]) -> Any:
    r = requests.get(f"{BASE}{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()["data"]


def _post(path: str, payload: Dict[str, Any]) -> Any:
    nonce = str(int(time.time() * 1000))
    query = f"timestamp={nonce}"
    r = requests.post(
        f"{BASE}{path}?{query}",
        headers=_auth_headers(query),
        data=json.dumps(payload),
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["data"]

# --- public REST wrappers --------------------------------------

def fetch_ohlcv(symbol: str, interval: str = "1m", limit: int = 500) -> List[List]:
    """Return raw klines as list."""
    tf_map = {"1m": "1", "5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D"}
    ivl = tf_map.get(interval, "1")
    return _get(
        "/api/spot/v1/market/kline",
        {"symbol": symbol.replace("/", ""), "interval": ivl, "limit": limit},
    )


def fetch_order_book(symbol: str, depth: int = 20) -> Dict[str, Any]:
    return _get(
        "/api/spot/v1/market/depth",
        {"symbol": symbol.replace("/", ""), "limit": depth},
    )


def create_market_order(symbol: str, side: str, quantity: float) -> Dict[str, Any]:
    return _post(
        "/api/spot/v1/order",
        {
            "symbol": symbol.replace("/", ""),
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity,
        },
    )


def create_limit_order(
    symbol: str, side: str, quantity: float, price: float
) -> Dict[str, Any]:
    return _post(
        "/api/spot/v1/order",
        {
            "symbol": symbol.replace("/", ""),
            "side": side.upper(),
            "type": "LIMIT",
            "price": f"{price:.2f}",
            "quantity": quantity,
            "timeInForce": "GTC",
        },
    )
