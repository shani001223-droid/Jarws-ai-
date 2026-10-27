"""Task 41: bounded, read-only, hypothetical BTC/ETH spot risk illustrations.

No executable quote, order, position, leverage, account or guaranteed stop.
Uses Task 40's correlated watchlist and Task 38/39 closed-candle evidence.
"""
from __future__ import annotations

import math

try:
    from .setup_assessment import assess_spot_setup, SetupAssessmentError, VERSION as SETUP_VERSION
    from .market_structure import analyze_market_structure, MarketStructureError
    from .market_indicators import analyze_market_indicators, MarketIndicatorsError, FORMULA_VERSION
except ImportError:  # direct Uvicorn main:app inside the backend Docker image
    from setup_assessment import assess_spot_setup, SetupAssessmentError, VERSION as SETUP_VERSION
    from market_structure import analyze_market_structure, MarketStructureError
    from market_indicators import analyze_market_indicators, MarketIndicatorsError, FORMULA_VERSION

VERSION = "spot-paper-risk-v1"
FRAMES = ("15m", "1h", "4h")
EVIDENCE = frozenset(("confirmed_structure", "ema_trend", "rsi_momentum",
                      "volume_participation", "session_vwap", "atr_volatility_guard"))


class PaperRiskError(ValueError):
    """Untrusted analyzer output or invalid hypothetical budget."""


def _finite(value, name: str, low: float, high: float) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not low <= value <= high):
        raise PaperRiskError(name)
    return float(value)


def validate_paper_settings(equity_usdt: float, risk_pct: float,
                            fee_bps: float, slippage_bps: float) -> tuple:
    """Validate all hypothetical inputs before any public provider request."""
    return (_finite(equity_usdt, "invalid_equity", 10, 100_000),
            _finite(risk_pct, "invalid_risk_pct", .1, 1),
            _finite(fee_bps, "invalid_fee_bps", 1, 100),
            _finite(slippage_bps, "invalid_slippage_bps", 1, 100))


def _identity(assessment: dict, structure: dict, indicators: dict) -> None:
    """Fail closed if the three analyzers do not describe the same closed bars."""
    try:
        if (not all(isinstance(x, dict) for x in (assessment, structure, indicators))
                or assessment["symbol"] not in ("BTCUSDT", "ETHUSDT")
                or any(x["symbol"] != assessment["symbol"] for x in (structure, indicators))
                or any(x["market"] != "spot" or x["orders_enabled"] is not False
                       for x in (assessment, structure, indicators))
                or assessment["mode"] != "paper-watchlist-research-only"
                or assessment["version"] != SETUP_VERSION
                or assessment["independently_cross_checked"] is not False
                or assessment["entry_stop_tp_available"] is not False
                or assessment["structure_alignment"] != structure["alignment"]
                or (assessment["decision"] == "paper_watchlist_only"
                    and structure["alignment"] != "all_three_bullish_structure")
                or structure["mode"] != "structure-research-only"
                or indicators["mode"] != "indicators-research-only"
                or indicators["formula_version"] != FORMULA_VERSION
                or assessment["decision"] not in ("wait", "paper_watchlist_only")
                or type(assessment["positive_families"]) is not int
                or not 0 <= assessment["positive_families"] <= 6
                or assessment["families_checked"] != 6
                or set(assessment["evidence"]) != EVIDENCE
                or set(assessment["last_closed_at"]) != set(FRAMES)
                or set(structure["timeframes"]) != set(FRAMES)
                or set(indicators["timeframes"]) != set(FRAMES)):
            raise PaperRiskError("invalid_analysis_identity")
        positive = sum(item["status"] == "supports_watchlist"
                       for item in assessment["evidence"].values())
        if (positive != assessment["positive_families"]
                or any(item["status"] not in ("supports_watchlist", "does_not_support")
                       for item in assessment["evidence"].values())
                or (assessment["decision"] == "paper_watchlist_only") != (positive == 6)):
            raise PaperRiskError("inconsistent_watchlist")
        for tf in FRAMES:
            s, m = structure["timeframes"][tf], indicators["timeframes"][tf]
            stamp = assessment["last_closed_at"][tf]
            if (type(stamp) is not int or stamp < 0
                    or type(s["last_closed_at"]) is not int
                    or type(m["last_closed_at"]) is not int
                    or s["last_closed_at"] != stamp or m["last_closed_at"] != stamp
                    or _finite(s["last_close"], "invalid_price", 1, 1e9)
                       != _finite(m["last_close"], "invalid_price", 1, 1e9)
                    or type(s["pivot_confirmation_bars"]) is not int
                    or s["pivot_confirmation_bars"] != 2):
                raise PaperRiskError("mismatched_analysis_snapshot")
    except (KeyError, TypeError, AttributeError) as exc:
        raise PaperRiskError("invalid_analysis_shape") from exc


def build_paper_risk(assessment: dict, structure: dict, indicators: dict,
                     equity_usdt: float = 100, risk_pct: float = .5,
                     fee_bps: float = 10, slippage_bps: float = 5) -> dict:
    """Return WAIT or a cash-capped hypothetical 1R/2R plan, never an order.

    Entry is the last closed price plus assumed adverse slippage, not a live
    fill. Stops and targets may gap; venue lot sizes and liquidity are unknown.
    """
    equity, risk, fee_bps, slippage_bps = validate_paper_settings(
        equity_usdt, risk_pct, fee_bps, slippage_bps)
    fee, slip = fee_bps / 10_000, slippage_bps / 10_000
    _identity(assessment, structure, indicators)
    base = {
        "symbol": assessment["symbol"], "market": "spot",
        "mode": "hypothetical-paper-risk-only", "version": VERSION,
        "orders_enabled": False, "independently_cross_checked": False,
        "source_assessment_version": SETUP_VERSION,
        "last_closed_at": assessment["last_closed_at"],
        "decision": "wait", "paper_plan": None,
        "note": "Illustrative long-only spot math on single-venue closed candles. No executable quote, signal guarantee, live order, leverage or exchange lot-size check. Gaps, variable fees/slippage and liquidity can exceed the modeled loss; 1R/2R are not profit predictions.",
    }
    if assessment["decision"] != "paper_watchlist_only":
        return dict(base, reason_code="setup_not_confirmed")
    try:
        frame = structure["timeframes"]["15m"]
        vals = indicators["timeframes"]["15m"]["values"]
        support = frame.get("support")
        atr_value = vals["atr14"]
    except (KeyError, TypeError, AttributeError) as exc:
        raise PaperRiskError("invalid_analysis_shape") from exc
    if support is None:
        return dict(base, reason_code="no_confirmed_support")
    close = _finite(frame["last_close"], "invalid_price", 1, 1e9)
    support = _finite(support, "invalid_support", 1e-9, 1e9)
    atr = _finite(atr_value, "invalid_atr", 0, 1e9)
    if support > close or atr == 0:
        return dict(base, reason_code="no_usable_stop")
    buffer = max(.25 * atr, .001 * close)
    stop = support - buffer
    distance = close - stop
    if stop <= 0 or not .002 <= distance / close <= .05:
        return dict(base, reason_code="stop_distance_outside_guardrails")
    entry_fill = close * (1 + slip)
    stop_fill = stop * (1 - slip)
    loss_unit = entry_fill - stop_fill + fee * (entry_fill + stop_fill)
    if not math.isfinite(loss_unit) or loss_unit <= 0:
        raise PaperRiskError("invalid_cost_model")
    budget = equity * risk / 100
    quantity = math.floor(min(budget / loss_unit, equity / (entry_fill * (1 + fee))) * 1e8) / 1e8
    if quantity <= 0:
        return dict(base, reason_code="illustrative_size_too_small")
    targets = []
    for multiple in (1, 2):
        target = close + multiple * distance
        target_fill = target * (1 - slip)
        profit_unit = target_fill - entry_fill - fee * (entry_fill + target_fill)
        targets.append({"multiple_before_costs": multiple,
                        "reference_price": target,
                        "estimated_net_pnl_usdt": quantity * profit_unit,
                        "estimated_net_reward_risk": profit_unit / loss_unit})
    if targets[1]["estimated_net_reward_risk"] < 1:
        return dict(base, reason_code="estimated_costs_erase_reward")
    return dict(base, decision="paper_plan_only", reason_code="bounded_paper_illustration",
                paper_plan={
                    "side": "long", "reference_entry_close": close,
                    "estimated_entry_with_slippage": entry_fill,
                    "confirmed_support": support, "reference_stop": stop,
                    "stop_method": "confirmed_15m_support_minus_max_quarter_atr_or_0_1pct",
                    "estimated_stop_fill_with_slippage": stop_fill,
                    "stop_distance_pct": distance / close * 100,
                    "targets": targets,
                    "equity_usdt": equity, "risk_pct": risk,
                    "risk_budget_usdt": budget,
                    "estimated_quantity_base": quantity,
                    "estimated_notional_usdt": quantity * entry_fill,
                    "estimated_stop_loss_including_costs_usdt": quantity * loss_unit,
                    "assumed_fee_bps_each_side": fee_bps,
                    "assumed_adverse_slippage_bps_each_side": slippage_bps,
                    "fills_simulated": False, "exchange_order_validated": False,
                })


def assess_paper_risk(histories: dict, symbol: str, equity_usdt: float = 100,
                      risk_pct: float = .5, fee_bps: float = 10,
                      slippage_bps: float = 5) -> dict:
    """Run all three analyzers on the same validated closed-candle histories."""
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise PaperRiskError("unsupported_pair")
    try:
        assessment = assess_spot_setup(histories, symbol)
        structure = analyze_market_structure(histories, symbol)
        indicators = analyze_market_indicators(histories, symbol)
    except (SetupAssessmentError, MarketStructureError, MarketIndicatorsError,
            ArithmeticError, OverflowError) as exc:
        raise PaperRiskError("invalid_closed_history") from exc
    return build_paper_risk(assessment, structure, indicators,
                            equity_usdt, risk_pct, fee_bps, slippage_bps)
