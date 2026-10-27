"""Task 39: deterministic closed-candle spot indicators, without trading actions.

The existing research module owns the SMA-seeded EMA and Wilder RSI/ATR
formulas. Reuse those exact implementations rather than silently introducing
a second definition. Only validated 15m/1h/4h closed bars may reach this code.
"""
from __future__ import annotations

import math

try:
    from .market_structure import MarketStructureError, _checked
    from .trading_research import ema, indicators
except ImportError:  # direct Uvicorn main:app inside Docker
    from market_structure import MarketStructureError, _checked
    from trading_research import ema, indicators

TIMEFRAMES = ("15m", "1h", "4h")
DAY_MS = 86_400_000
FORMULA_VERSION = "spot-indicators-v1"


class MarketIndicatorsError(ValueError):
    """Invalid source history or a non-finite indicator calculation."""


def _finite(value):
    if value is not None and (not isinstance(value, (int, float))
                              or not math.isfinite(value)):
        raise MarketIndicatorsError("nonfinite_indicator")
    return value


def _frame(bars, interval):
    try:
        _checked(bars, interval)
    except (MarketStructureError, ValueError, TypeError, KeyError) as exc:
        raise MarketIndicatorsError("invalid_closed_history") from exc
    # Strict limits also prevent overflow in weighted sums; these are not
    # assumptions about exchange accuracy or a substitute for source checks.
    if any(b.high > 1e12 or b.volume > 1e18 for b in bars):
        raise MarketIndicatorsError("out_of_range_history")
    closes = [b.close for b in bars]
    core = indicators(bars)
    e9, e21 = ema(closes, 9), ema(closes, 21)
    volume_mean = math.fsum(b.volume for b in bars[-20:]) / 20
    ratio = bars[-1].volume / volume_mean if volume_mean > 0 else None

    # UTC-session VWAP of HLC3, only when the complete session is represented
    # from its 00:00 UTC opening bar. Otherwise null, never a partial-day VWAP
    # falsely labelled as a full session. Zero volume also produces null.
    session_start = (bars[-1].time // DAY_MS) * DAY_MS
    session = [b for b in bars if b.time >= session_start]
    session_complete = bool(session and session[0].time == session_start)
    vwap = None
    if session_complete:
        volume = math.fsum(b.volume for b in session)
        if volume > 0:
            vwap = math.fsum(((b.high + b.low + b.close) / 3) * b.volume
                             for b in session) / volume

    values = {
        "ema9": e9[-1],
        "ema20": core["ema20"][-1],
        "ema21": e21[-1],
        "ema50": core["ema50"][-1],
        "rsi14": core["rsi14"][-1],
        "atr14": core["atr14"][-1],
        "volume_sma20_base": volume_mean,
        "volume_ratio20": ratio,
        "utc_session_vwap": vwap,
    }
    return {
        "last_closed_at": bars[-1].close_time,
        "last_close": bars[-1].close,
        "candles_used": len(bars),
        "values": {key: _finite(value) for key, value in values.items()},
        "vwap_session_start": session_start if session_complete else None,
        "vwap_full_session_from_open": session_complete,
    }


def analyze_market_indicators(histories, symbol):
    """Compute reproducible descriptive indicators, never entries or orders.

    Caller must independently enforce source freshness; these calculations
    cannot certify live Binance availability or Kraken cross-verification.
    """
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise MarketIndicatorsError("unsupported_pair")
    if not isinstance(histories, dict) or set(histories) != set(TIMEFRAMES):
        raise MarketIndicatorsError("missing_timeframes")
    try:
        frames = {tf: _frame(histories[tf], tf) for tf in TIMEFRAMES}
    except (ArithmeticError, OverflowError) as exc:
        raise MarketIndicatorsError("nonfinite_indicator") from exc
    return {
        "symbol": symbol,
        "market": "spot",
        "mode": "indicators-research-only",
        "orders_enabled": False,
        "formula_version": FORMULA_VERSION,
        "timeframes": frames,
        "formulas": {
            "ema": "SMA seed over N closes; thereafter EMA = prior + 2/(N+1)*(close-prior); N=9,20,21,50",
            "rsi14": "Wilder smoothing of 14 close-to-close gains/losses; flat=50, no losses=100, no gains=0",
            "atr14": "Wilder true range smoothing; first TR=high-low; seed mean of first 14 TR",
            "volume_sma20_base": "arithmetic mean of latest 20 closed base-volume bars (including latest)",
            "volume_ratio20": "latest closed base volume / volume_sma20; null when mean is zero",
            "utc_session_vwap": "sum(HLC3*base_volume)/sum(base_volume) from 00:00 UTC; null if session start or positive volume missing",
        },
        "note": "Descriptive, lagging single-venue indicators. No confidence score, entry/stop/TP, orders or performance claim. Live source and freshness require separate checks.",
    }
