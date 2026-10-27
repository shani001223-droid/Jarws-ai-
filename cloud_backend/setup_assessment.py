"""Task 40: explainable closed-candle spot-only multi-family setup assessment.

Watchlist filter, not a trading recommendation or order engine. Task 38/39
analyzers use ONE shared history. Distinct evidence families are correlated,
not statistically independent observations or separate exchange sources.
"""
from __future__ import annotations
import math

try:
    from .market_structure import analyze_market_structure, MarketStructureError
    from .market_indicators import analyze_market_indicators, MarketIndicatorsError
except ImportError:  # direct Uvicorn main:app inside Docker
    from market_structure import analyze_market_structure, MarketStructureError
    from market_indicators import analyze_market_indicators, MarketIndicatorsError

VERSION = "spot-setup-assessment-v1"
FRAMES = ("15m", "1h", "4h")


class SetupAssessmentError(ValueError):
    """Source history or an internal assessment invariant is invalid."""


def _number(value):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value)):
        raise SetupAssessmentError("invalid_indicator")
    return float(value)


def _signal(passed: bool, positive: str, negative: str) -> dict:
    return {"status": "supports_watchlist" if passed else "does_not_support",
            "reason_code": positive if passed else negative}


def _evaluate(structure: dict, indicators: dict) -> dict:
    """Combine six distinct evidence families; never compute win probability."""
    if (structure.get("symbol") != indicators.get("symbol")
            or structure.get("symbol") not in ("BTCUSDT", "ETHUSDT")
            or structure.get("orders_enabled") is not False
            or indicators.get("orders_enabled") is not False
            or structure.get("market") != "spot"
            or indicators.get("market") != "spot"
            or structure.get("alignment") not in (
                "all_three_bullish_structure", "all_three_bearish_structure",
                "mixed_timeframes", "insufficient_confirmation")
            or indicators.get("formula_version") != "spot-indicators-v1"):
        raise SetupAssessmentError("invalid_analysis_identity")
    try:
        structures = structure["timeframes"]
        metrics = indicators["timeframes"]
        if set(structures) != set(FRAMES) or set(metrics) != set(FRAMES):
            raise SetupAssessmentError("missing_timeframes")
        for tf in FRAMES:
            s, m = structures[tf], metrics[tf]
            if (s["last_closed_at"] != m["last_closed_at"]
                    or _number(s["last_close"]) != _number(m["last_close"])):
                raise SetupAssessmentError("mismatched_analysis_snapshot")
            if not isinstance(s["last_closed_at"], int) or isinstance(s["last_closed_at"], bool):
                raise SetupAssessmentError("invalid_closed_time")
            if _number(s["last_close"]) <= 0:
                raise SetupAssessmentError("invalid_price")
            for key in ("ema9", "ema20", "ema21", "ema50", "rsi14", "atr14"):
                v = _number(m["values"][key])
                if v < 0 or (key == "rsi14" and v > 100):
                    raise SetupAssessmentError("invalid_indicator")
            if _number(m["values"]["volume_sma20_base"]) < 0:
                raise SetupAssessmentError("invalid_volume")
            ratio = m["values"]["volume_ratio20"]
            if ratio is not None and _number(ratio) < 0:
                raise SetupAssessmentError("invalid_volume")
            vwap = m["values"]["utc_session_vwap"]
            if vwap is not None and _number(vwap) <= 0:
                raise SetupAssessmentError("invalid_vwap")
    except (KeyError, TypeError, AttributeError) as exc:
        raise SetupAssessmentError("invalid_analysis_shape") from exc

    f15 = metrics["15m"]["values"]
    bullish_structure = structure["alignment"] == "all_three_bullish_structure"
    ema_trend = all(
        metrics[tf]["last_close"] > metrics[tf]["values"]["ema20"]
        and metrics[tf]["values"]["ema9"] > metrics[tf]["values"]["ema21"]
        and metrics[tf]["values"]["ema20"] > metrics[tf]["values"]["ema50"]
        for tf in FRAMES
    )
    momentum = (52 <= f15["rsi14"] <= 68
                and all(50 <= metrics[tf]["values"]["rsi14"] <= 75
                        for tf in ("1h", "4h")))
    participation = (f15["volume_sma20_base"] > 0
                     and f15["volume_ratio20"] is not None
                     and f15["volume_ratio20"] >= 1.2)
    vwap = f15["utc_session_vwap"]
    vwap_confirmed = (metrics["15m"]["vwap_full_session_from_open"] is True
                      and vwap is not None
                      and metrics["15m"]["last_close"] > vwap)
    atr_pct = f15["atr14"] / metrics["15m"]["last_close"] * 100
    volatility_ok = 0.05 <= atr_pct <= 5.0

    evidence = {
        "confirmed_structure": _signal(bullish_structure, "all_frames_confirmed_higher_swings", "structure_not_aligned_bullish"),
        "ema_trend": _signal(ema_trend, "three_frame_ema_trend_aligned", "ema_trend_not_aligned"),
        "rsi_momentum": _signal(momentum, "bounded_bullish_rsi", "rsi_not_in_bounded_bullish_range"),
        "volume_participation": _signal(participation, "fifteen_minute_volume_above_baseline", "volume_not_confirmed"),
        "session_vwap": _signal(vwap_confirmed, "above_complete_utc_session_vwap", "vwap_unavailable_or_not_confirmed"),
        "atr_volatility_guard": _signal(volatility_ok, "bounded_fifteen_minute_atr", "atr_outside_guardrails"),
    }
    watchlist = all(x["status"] == "supports_watchlist" for x in evidence.values())
    return {
        "symbol": structure["symbol"], "market": "spot",
        "mode": "paper-watchlist-research-only", "orders_enabled": False,
        "version": VERSION,
        "decision": "paper_watchlist_only" if watchlist else "wait",
        "positive_families": sum(x["status"] == "supports_watchlist" for x in evidence.values()),
        "families_checked": len(evidence), "evidence": evidence,
        "last_closed_at": {tf: metrics[tf]["last_closed_at"] for tf in FRAMES},
        "structure_alignment": structure["alignment"],
        "independently_cross_checked": False,
        "entry_stop_tp_available": False,
        "note": "Distinct rule families share Binance spot candles and are correlated; not independent market sources, calibrated confidence, a profitable strategy, or a buy/sell recommendation. No entry, stop, TP or orders. Missing confirmation means WAIT.",
    }


def assess_spot_setup(histories: dict, symbol: str) -> dict:
    """Assess shared validated 15m/1h/4h histories without any future bars."""
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise SetupAssessmentError("unsupported_pair")
    if not isinstance(histories, dict) or set(histories) != set(FRAMES):
        raise SetupAssessmentError("missing_timeframes")
    try:
        structure = analyze_market_structure(histories, symbol)
        indicators = analyze_market_indicators(histories, symbol)
    except (MarketStructureError, MarketIndicatorsError, ArithmeticError, OverflowError) as exc:
        raise SetupAssessmentError("invalid_closed_history") from exc
    return _evaluate(structure, indicators)
