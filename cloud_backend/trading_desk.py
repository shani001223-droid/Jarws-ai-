"""One bounded V2 snapshot for the trading-only desk; no model calls or orders.

V3's source-blocked curriculum is deliberately not loaded or called complete.
Every displayed price comes from closed candles. Paper plans require both the
existing six-family long setup and all five existing V2 confluence conditions.
"""
from __future__ import annotations

try:
    from .market_structure import analyze_market_structure
    from .market_indicators import analyze_market_indicators
    from .setup_assessment import _evaluate
    from .paper_risk import build_paper_risk, validate_paper_settings
    from .strategy_engine import confluence_score
    from .brain import knowledge_index
except ImportError:  # existing Docker root: uvicorn main:app
    from market_structure import analyze_market_structure
    from market_indicators import analyze_market_indicators
    from setup_assessment import _evaluate
    from paper_risk import build_paper_risk, validate_paper_settings
    from strategy_engine import confluence_score
    from brain import knowledge_index

VERSION = "hoshi-trading-desk-v1"
FRAMES = ("15m", "1h", "4h")


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
    # Validates every candle, frame, close time and freshness before analysis.
    confluence = confluence_score(histories, symbol, now_ms, "long")
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
