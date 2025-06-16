"""Trading utilities for EchoNode."""

import os
import logging
from typing import Optional

import ccxt

logger = logging.getLogger(__name__)


def get_exchange() -> ccxt.bitunix:
    """Create and return the Bitunix exchange instance using env vars."""
    key = os.getenv("BITUNIX_KEY")
    secret = os.getenv("BITUNIX_SECRET")
    if not key or not secret:
        raise EnvironmentError("BITUNIX_KEY and BITUNIX_SECRET must be set")
    return ccxt.bitunix({
        "apiKey": key,
        "secret": secret,
    })


def place_order(exchange: ccxt.bitunix, symbol: str, side: str, amount: float,
                price: Optional[float] = None) -> dict:
    """Place a market or limit order and return the order info."""
    logger.info("Placing %s order for %s %s", side, amount, symbol)
    if price is None:
        return exchange.create_market_order(symbol, side, amount)
    return exchange.create_limit_order(symbol, side, amount, price)
