"""One bounded V2 snapshot for the trading-only desk; no model calls or orders.

V3's source-blocked curriculum is deliberately not loaded or called complete.
Every displayed price comes from closed candles. Paper plans require both the
existing six-family long setup and all five existing V2 confluence conditions.
"""
from __future__ import annotations

import math

try:
    from .market_structure import analyze_market_structure
    from .market_indicators import analyze_market_indicators
    from .setup_assessment import _evaluate
    from .paper_risk import build_paper_risk, validate_paper_settings
    from .strategy_engine import confluence_score
    from .brain import knowledge_index
    from .trading_research import INTERVALS
except ImportError:  # existing Docker root: uvicorn main:app
    from market_structure import analyze_market_structure
    from market_indicators import analyze_market_indicators
    from setup_assessment import _evaluate
    from paper_risk import build_paper_risk, validate_paper_settings
    from strategy_engine import confluence_score
    from brain import knowledge_index
    from trading_research import INTERVALS

VERSION = "hoshi-trading-desk-v1"
FRAMES = ("15m", "1h", "4h")

def _require_same_venue_aggregation(histories: dict) -> None:
    """Reconcile every fully overlapping 1h/4h OHLCV bar with closed 15m.

    Earlier higher-frame candles inside the 15m window influence EMA/ATR,
    structure and setup checks too; checking only the newest parent misses
    internally contradictory lookback evidence. The oldest partial parent
    outside that window is intentionally not claimed as verified. This is
    SAME-VENUE consistency, not independent exchange authentication.
    """
    quarter_ms = INTERVALS["15m"]
    quarters = {bar.time: bar for bar in histories["15m"]}
    first_open = histories["15m"][0].time
    last_close = histories["15m"][-1].close_time
    for tf in ("1h", "4h"):
        covered = 0
        parents = histories[tf]
        for parent in parents:
            # A parent partially outside the available 15m lookback cannot
            # be checked. The newest parent MUST be fully represented.
            if parent.time < first_open or parent.close_time > last_close:
                if parent is parents[-1]:
                    raise ValueError("missing_latest_cross_timeframe_coverage")
                continue
            children = [quarters.get(parent.time + i * quarter_ms)
                        for i in range(INTERVALS[tf] // quarter_ms)]
            if any(child is None for child in children):
                raise ValueError("missing_cross_timeframe_closed_bars")
            if children[-1].close_time != parent.close_time:
                raise ValueError("cross_timeframe_close_boundary_mismatch")
            aggregate = (
                children[0].open, max(child.high for child in children),
                min(child.low for child in children), children[-1].close,
                math.fsum(child.volume for child in children),
            )
            actual = (parent.open, parent.high, parent.low, parent.close, parent.volume)
            for i, (observed, computed) in enumerate(zip(actual, aggregate)):
                # Binance independently rounds higher-frame base volumes.
                # Price extremes should agree much more tightly.
                tolerance = (2e-7 + 1e-8 * max(abs(observed), abs(computed))
                             if i == 4 else 1e-8 * max(1, abs(observed), abs(computed)))
                if (not math.isfinite(observed) or not math.isfinite(computed)
                        or abs(observed - computed) > tolerance):
                    raise ValueError("cross_timeframe_ohlcv_mismatch")
            covered += 1
        if covered == 0:
            raise ValueError("missing_cross_timeframe_coverage")


def build_trading_desk(histories: dict, symbol: str, now_ms: int,
                       fetched_at: int, equity_usdt: float = 100,
                       risk_pct: float = .5, fee_bps: float = 10,
                       slippage_bps: float = 5) -> dict:
    """Compute from ONE fetched history set; no optimistic missing-data fallback."""
    settings = validate_paper_settings(equity_usdt, risk_pct, fee_bps, slippage_bps)
    if (type(now_ms) is not int or type(fetched_at) is not int
            or fetched_at * 1000 > now_ms + 5_000
            or fetched_at * 1000 < now_ms - 120_000):
        raise ValueError("invalid_source_time")
    # Parallel provider reads can straddle a candle boundary. Historical
    # freshness permits an older bar; a current paper desk must instead use
    # the latest closed bar of EACH timeframe at the same as-of instant.
    if type(now_ms) is not int or now_ms <= 0 or not isinstance(histories, dict) or set(histories) != set(FRAMES):
        raise ValueError("invalid_snapshot_boundary")
    for tf in FRAMES:
        bars = histories[tf]
        expected_close = (now_ms // INTERVALS[tf]) * INTERVALS[tf] - 1
        if not bars or type(bars[-1].close_time) is not int or bars[-1].close_time != expected_close:
            raise ValueError("mixed_or_lagging_closed_candle_snapshot")
        # A candle cannot have been obtained before its closing instant.
        # A cached pre-boundary fetch must never authorize a post-boundary
        # paper plan, even if the supplied OHLC series claims the new close.
        # The fetch timestamp is rounded to whole seconds by _public_data.
        if fetched_at * 1000 <= expected_close:
            raise ValueError("noncausal_closed_candle_fetch")
    # Validates every candle, frame, close time and freshness before analysis.
    confluence = confluence_score(histories, symbol, now_ms, "long")
    _require_same_venue_aggregation(histories)
    structure = analyze_market_structure(histories, symbol)
    indicators = analyze_market_indicators(histories, symbol)
    setup = _evaluate(structure, indicators)
    risk = build_paper_risk(setup, structure, indicators, *settings)
    ready = (risk["decision"] == "paper_plan_only"
             and confluence["decision"] == "paper_watchlist_only")
    reason = ("bounded_paper_illustration" if ready else
              "v2_conditions_incomplete" if risk["decision"] == "paper_plan_only"
              else risk["reason_code"])
    frames = {}
    for tf in FRAMES:
        s, m = structure["timeframes"][tf], indicators["timeframes"][tf]
        frames[tf] = {
            "last_closed_at": s["last_closed_at"], "last_close": s["last_close"],
            "structure": s["structure"], "support": s["support"],
            "resistance": s["resistance"],
            "rsi14": m["values"]["rsi14"], "ema20": m["values"]["ema20"],
            "ema50": m["values"]["ema50"], "atr14": m["values"]["atr14"],
        }
    return {
        "version": VERSION, "symbol": symbol, "market": "spot",
        "mode": "paper-assistant-only", "orders_enabled": False,
        "win_probability": None, "direction": "long_study_only",
        "decision": "paper_plan_only" if ready else "wait", "reason_code": reason,
        "paper_plan": risk["paper_plan"] if ready else None,
        "as_of_ms": now_ms, "fetched_at": fetched_at,
        "expires_at_ms": min(now_ms + 60_000, fetched_at * 1000 + 120_000),
        "source": "Binance Spot public closed candles (single venue)",
        "independently_cross_checked": False,
        "price_kind": "last_closed_candle_not_live_quote",
        "timeframes": frames, "confluence": confluence, "setup": setup,
        "knowledge_version": knowledge_index()["version"],
        "v3_runtime_integration": "pending",
        "assumptions": {"equity_usdt": settings[0], "risk_pct": settings[1],
                        "fee_bps_each_side": settings[2],
                        "adverse_slippage_bps_each_side": settings[3]},
        "limits": ["Single venue; no independent price verification in this response.",
                   "No live news, macro clearance or order-book evidence attached.",
                   "Five V2 checks are correlated rule coverage, not win probability.",
                   "Illustrative long-only spot math; no fills, leverage or real orders.",
                   "Gaps and variable costs can exceed the modeled paper loss."],
    }
