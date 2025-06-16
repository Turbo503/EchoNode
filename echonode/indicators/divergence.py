"""Simple divergence indicator based on RSI."""

from __future__ import annotations

import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_divergence(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """Return bullish and bearish divergence points.

    Parameters
    ----------
    df : DataFrame
        OHLCV data indexed by datetime.
    lookback : int, optional
        Bars to look back when comparing highs/lows, by default 20.

    Returns
    -------
    DataFrame
        DataFrame with 'Bullish' and 'Bearish' columns containing price
        levels for plotting divergence markers.
    """
    data = df.copy()
    data["RSI"] = rsi(data["Close"])
    data["Bullish"] = float("nan")
    data["Bearish"] = float("nan")

    for i in range(lookback, len(data)):
        cur_low = data["Low"].iloc[i]
        prev_low = data["Low"].iloc[i - lookback]
        cur_rsi = data["RSI"].iloc[i]
        prev_rsi = data["RSI"].iloc[i - lookback]
        if cur_low < prev_low and cur_rsi > prev_rsi:
            data.at[data.index[i], "Bullish"] = cur_low * 0.995
        cur_high = data["High"].iloc[i]
        prev_high = data["High"].iloc[i - lookback]
        if cur_high > prev_high and cur_rsi < prev_rsi:
            data.at[data.index[i], "Bearish"] = cur_high * 1.005

    return data[["Bullish", "Bearish"]]
