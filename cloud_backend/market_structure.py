"""Closed-candle, reproducible multi-timeframe market structure research.

No exchange orders, futures data, predictive signals, model calls or secrets.
Inputs must already have passed trading_research.closed_candles. A pivot is
usable only AFTER two subsequent candles close (no look-ahead leakage).
"""
from __future__ import annotations

import math

try:
    from .trading_research import Candle, INTERVALS
except ImportError:  # Direct Uvicorn main:app
    from trading_research import Candle, INTERVALS

TIMEFRAMES = ("15m", "1h", "4h")
PIVOT_RADIUS = 2
MAX_LEVELS = 6


class MarketStructureError(ValueError):
    """Invalid, insufficient or untrusted closed-candle history."""


def _checked(bars: list[Candle], interval: str) -> None:
    if not isinstance(bars, list) or not 64 <= len(bars) <= 500:
        raise MarketStructureError("invalid_history")
    step = INTERVALS[interval]
    previous = None
    for b in bars:
        if not isinstance(b, Candle):
            raise MarketStructureError("invalid_candle")
        values = (b.open, b.high, b.low, b.close, b.volume)
        if (not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                    and math.isfinite(x) for x in values)
                or min(values[:4]) <= 0 or b.volume < 0
                or not b.low <= min(b.open, b.close) <= max(b.open, b.close) <= b.high
                or not isinstance(b.time, int) or b.time < 0 or b.time % step
                or b.close_time != b.time + step - 1
                or (previous is not None and b.time != previous + step)):
            raise MarketStructureError("invalid_candle")
        previous = b.time


def _swings(bars: list[Candle], radius: int = PIVOT_RADIUS):
    highs, lows = [], []
    # The right-hand confirmation bars must be fully closed; last radius
    # candles are NEVER eligible to become pivots.
    for i in range(radius, len(bars) - radius):
        b = bars[i]
        others = bars[i-radius:i] + bars[i+1:i+radius+1]
        if all(b.high > x.high for x in others):
            highs.append({"price": b.high, "pivot_at": b.close_time,
                          "confirmed_at": bars[i+radius].close_time})
        if all(b.low < x.low for x in others):
            lows.append({"price": b.low, "pivot_at": b.close_time,
                         "confirmed_at": bars[i+radius].close_time})
    return highs, lows


def _regime(highs: list[dict], lows: list[dict]) -> str:
    if len(highs) < 2 or len(lows) < 2:
        return "insufficient_confirmed_swings"
    high_now, high_prior = highs[-1]["price"], highs[-2]["price"]
    low_now, low_prior = lows[-1]["price"], lows[-2]["price"]
    if high_now > high_prior and low_now > low_prior:
        return "higher_highs_higher_lows"
    if high_now < high_prior and low_now < low_prior:
        return "lower_highs_lower_lows"
    return "mixed_structure"


def _frame(bars: list[Candle], interval: str) -> dict:
    _checked(bars, interval)
    highs, lows = _swings(bars)
    close = bars[-1].close
    # Only previously confirmed levels, never a tentative latest swing.
    supports = [x["price"] for x in lows if x["price"] <= close]
    resistances = [x["price"] for x in highs if x["price"] >= close]
    return {
        "last_closed_at": bars[-1].close_time,
        "last_close": close,
        "structure": _regime(highs, lows),
        "support": max(supports) if supports else None,
        "resistance": min(resistances) if resistances else None,
        "previous_20_low": min(b.low for b in bars[-21:-1]),
        "previous_20_high": max(b.high for b in bars[-21:-1]),
        "confirmed_swing_highs": highs[-MAX_LEVELS:],
        "confirmed_swing_lows": lows[-MAX_LEVELS:],
        "pivot_confirmation_bars": PIVOT_RADIUS,
    }


def analyze_market_structure(histories: dict, symbol: str) -> dict:
    """Analyze exact 15m/1h/4h closed histories, without making trade calls.

    Caller must obtain/validate recent closed bars and disclose the venue.
    This function cannot independently certify freshness or provider honesty.
    """
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise MarketStructureError("unsupported_pair")
    if not isinstance(histories, dict) or set(histories) != set(TIMEFRAMES):
        raise MarketStructureError("missing_timeframes")
    frames = {tf: _frame(histories[tf], tf) for tf in TIMEFRAMES}
    states = [frames[tf]["structure"] for tf in TIMEFRAMES]
    if all(s == "higher_highs_higher_lows" for s in states):
        alignment = "all_three_bullish_structure"
    elif all(s == "lower_highs_lower_lows" for s in states):
        alignment = "all_three_bearish_structure"
    elif "insufficient_confirmed_swings" in states:
        alignment = "insufficient_confirmation"
    else:
        alignment = "mixed_timeframes"
    return {
        "symbol": symbol, "market": "spot", "mode": "structure-research-only",
        "orders_enabled": False, "timeframes": frames,
        "alignment": alignment,
        "method": "strict 2-left/2-right closed-bar pivots; strict higher/lower swing comparisons; prior 20-bar high/low excludes latest close",
        "note": "Descriptive levels only, not entry/stop/target recommendations. Missing support/resistance is null, not invented. Provider and freshness must be checked separately.",
    }
