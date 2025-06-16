"""Trading utilities for EchoNode."""

from __future__ import annotations

import logging
import os
from typing import Optional

from . import bitunix_api

logger = logging.getLogger(__name__)


class BitunixExchange:
    """Minimal ccxt-style wrapper around :mod:`bitunix_api`."""

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 500):
        return bitunix_api.fetch_ohlcv(symbol, interval=timeframe, limit=limit)

    def create_market_order(self, symbol: str, side: str, amount: float):
        return bitunix_api.create_market_order(symbol, side, amount)

    def create_limit_order(
        self, symbol: str, side: str, amount: float, price: float
    ):
        return bitunix_api.create_limit_order(symbol, side, amount, price)


def get_exchange() -> BitunixExchange:
    """Return an authenticated Bitunix exchange wrapper."""
    key = os.getenv("BITUNIX_KEY")
    secret = os.getenv("BITUNIX_SECRET")
    if not key or not secret:
        raise EnvironmentError("BITUNIX_KEY and BITUNIX_SECRET must be set")
    return BitunixExchange()


def place_order(
    exchange: BitunixExchange, symbol: str, side: str, amount: float,
    price: Optional[float] = None
) -> dict:
    """Place a market or limit order and return the order info."""
    logger.info("Placing %s order for %s %s", side, amount, symbol)
    if price is None:
        return exchange.create_market_order(symbol, side, amount)
    return exchange.create_limit_order(symbol, side, amount, price)
