"""Manual, read-only consistency audit of two separate public spot captures.

Usage:
  python -m scripts.compare_spot_captures \
    --earlier old.json --earlier-receipt old.receipt \
    --later new.json --later-receipt new.receipt

By default this checks only local, UNSIGNED receipts and overlapping closed bars.
The optional --prospective-replay scores only fully post-capture closed bars
with fixed default modeled paper settings; it is NOT independent forward fills.
No exchange authentication, network fetch, file writes or orders.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
import sys
from pathlib import Path

from cloud_backend.paper_evaluation import (
    STEP_MS, WARMUP_BARS, PaperEvaluationError, attach_capture_receipt,
    evaluate_chronological,
)
from cloud_backend.trading_research import RULE_VERSION, SimulationConfig, backtest
from scripts.evaluate_trading_paper import load_capture_receipt, load_local


def _verified_local_capture(data_path: Path, receipt_path: Path):
    symbol, bars = load_local(data_path)
    # Reuse the exact evaluator's bounded contiguous-candle, SHA-256 and
    # receipt binding rules. Its modeled strategy result is NOT used as
    # forward performance or as an independent market observation.
    report = evaluate_chronological(bars, symbol, "trend_pullback")
    receipt = load_capture_receipt(receipt_path)
    bound = attach_capture_receipt(report, receipt)
    return symbol, bars, receipt, bound["capture_receipt"]["receipt_sha256"], report["input_candle_sha256"]


def _verified_prospective_ledger(simulation: dict, first_scored: int,
                                 last_closed: int,
                                 expected_initial_equity: float) -> list[int]:
    """Validate local MODELED trade chronology and net-PnL reconciliation.

    This does not authenticate any exchange observation or paper fill.
    """
    if type(simulation) is not dict or type(simulation.get("trades")) is not list:
        raise PaperEvaluationError("invalid_prospective_paper_ledger")
    net = simulation.get("net_pnl")
    if type(net) not in (int, float) or not math.isfinite(net):
        raise PaperEvaluationError("invalid_prospective_paper_ledger")
    trades = simulation["trades"]
    if ("trade_count" in simulation
            and (type(simulation["trade_count"]) is not int
                 or simulation["trade_count"] != len(trades))):
        raise PaperEvaluationError("unreconciled_prospective_paper_ledger")
    entries, pnl, previous_exit = [], [], None
    for trade in trades:
        if type(trade) is not dict:
            raise PaperEvaluationError("invalid_prospective_paper_ledger")
        entry, exit_at = trade.get("entry_time"), trade.get("exit_time")
        gain, forced = trade.get("net_pnl"), trade.get("terminal_forced_mark")
        if (type(entry) is not int or type(exit_at) is not int
                or type(gain) not in (int, float) or not math.isfinite(gain)
                or type(forced) is not bool):
            raise PaperEvaluationError("invalid_prospective_paper_ledger")
        if (entry < first_scored or entry % STEP_MS
                or not entry <= exit_at <= last_closed
                or exit_at % STEP_MS not in (0, STEP_MS - 1)
                or (previous_exit is not None and entry <= previous_exit)
                or (forced and exit_at != last_closed)):
            raise PaperEvaluationError("noncausal_prospective_replay")
        entries.append(entry)
        pnl.append(gain)
        previous_exit = exit_at
    try:
        reconciled = math.isclose(math.fsum(pnl), net, rel_tol=1e-9, abs_tol=1e-7)
    except (OverflowError, ValueError):
        reconciled = False
    if not reconciled:
        raise PaperEvaluationError("unreconciled_prospective_paper_ledger")

    # The modeled trade sum must also agree with the reported cash ledger.
    # Checking trade PnL alone misses a broken ending-equity or risk report.
    # Legacy synthetic engine stubs omit both equity fields; the real engine
    # emits both. Never accept just one half of the equity identity.
    has_start = "initial_equity" in simulation
    has_end = "ending_equity" in simulation
    if has_start != has_end:
        raise PaperEvaluationError("invalid_prospective_paper_ledger")
    if has_start:
        start, end = simulation["initial_equity"], simulation["ending_equity"]
        if (type(start) not in (int, float) or type(end) not in (int, float)
                or not math.isfinite(start) or not math.isfinite(end)):
            raise PaperEvaluationError("invalid_prospective_paper_ledger")
        if (not math.isclose(start, expected_initial_equity,
                             rel_tol=1e-12, abs_tol=1e-8)
                or not math.isclose(end - start, net,
                                    rel_tol=1e-9, abs_tol=1e-7)):
            raise PaperEvaluationError("unreconciled_prospective_paper_ledger")
    if "max_drawdown_pct" in simulation:
        drawdown = simulation["max_drawdown_pct"]
        # Do not cap at 100%: an adverse modeled gap can exceed cash equity.
        if (type(drawdown) not in (int, float)
                or not math.isfinite(drawdown) or drawdown < 0):
            raise PaperEvaluationError("invalid_prospective_paper_ledger")

    diagnostics = simulation.get("execution_diagnostics")
    if diagnostics is not None:
        if type(diagnostics) is not dict:
            raise PaperEvaluationError("invalid_prospective_paper_ledger")
        forced = [trade["net_pnl"] for trade in trades
                  if trade["terminal_forced_mark"]]
        resolved = [trade["net_pnl"] for trade in trades
                    if not trade["terminal_forced_mark"]]
        for key, expected in (
                ("terminal_forced_close_count", len(forced)),
                ("strategy_resolved_trade_count", len(resolved)),
                ("terminal_forced_close_net_pnl_usdt", math.fsum(forced)),
                ("strategy_resolved_net_pnl_usdt", math.fsum(resolved))):
            value = diagnostics.get(key)
            if (type(value) not in (int, float)
                    or not math.isfinite(value)
                    or (type(expected) is int and
                        (type(value) is not int or value != expected))
                    or (type(expected) is float and not math.isclose(
                        value, expected, rel_tol=1e-9, abs_tol=1e-7))):
                raise PaperEvaluationError("unreconciled_prospective_paper_ledger")
        for key in ("close_mark_max_drawdown_pct",
                    "close_mark_peak_equity_usdt",
                    "close_mark_low_equity_usdt"):
            value = diagnostics.get(key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise PaperEvaluationError("invalid_prospective_paper_ledger")
        if (diagnostics["close_mark_max_drawdown_pct"] < 0
                or diagnostics["close_mark_peak_equity_usdt"]
                < diagnostics["close_mark_low_equity_usdt"]
                or (has_start and diagnostics["close_mark_peak_equity_usdt"]
                    < simulation["initial_equity"] - 1e-7)):
            raise PaperEvaluationError("unreconciled_prospective_paper_ledger")
    return entries


def _verified_replay_metadata(simulation: dict, strategy: str,
                              config: SimulationConfig, segment: list) -> bool:
    """Check the engine actually reports the requested strategy/cost/window.

    Synthetic legacy test stubs without ANY metadata are explicitly unverified;
    real backtest outputs include every field. A partial or contradictory
    metadata claim must fail closed rather than masquerade as the requested
    fixed-default or double-cost prospective replay.
    """
    expected = {
        "mode": "historical-paper-simulation",
        "orders_enabled": False,
        "rule_version": RULE_VERSION,
        "strategy": strategy,
        "interval": "15m",
        "start_at": segment[0].time,
        "end_at": segment[-1].close_time,
        "bars": len(segment),
        "config": asdict(config),
    }
    if not any(key in simulation for key in expected):
        return False
    for key, wanted in expected.items():
        value = simulation.get(key)
        if key == "config":
            if (type(value) is not dict or set(value) != set(wanted)
                    or any(type(value[k]) is not type(wanted[k])
                           or value[k] != wanted[k] for k in wanted)):
                raise PaperEvaluationError("unreconciled_prospective_replay_metadata")
        elif type(value) is not type(wanted) or value != wanted:
            raise PaperEvaluationError("unreconciled_prospective_replay_metadata")
    return True



def _verified_execution_costs(simulation: dict, config: SimulationConfig) -> bool | None:
    """Reconcile modeled fills against the requested fees and slippage.

    None means no trades to audit; False means legacy synthetic trades without
    execution fields. Neither state is independently observed fills.
    Partial fields or contradictory cost/PnL arithmetic fail closed.
    """
    trades = simulation["trades"]
    # The real paper engine emits fees_paid and four aggregate cost totals,
    # including for ZERO trades. Previously an empty ledger returned early,
    # so a nonzero/partial cost claim could pass as a clean zero-trade run.
    diagnostics = simulation.get("execution_diagnostics")
    cost_keys = (
        "modeled_buy_slippage_cost_usdt",
        "modeled_sell_slippage_cost_usdt",
        "modeled_total_slippage_cost_usdt",
        "modeled_fees_plus_slippage_cost_usdt",
    )
    has_cost_totals = type(diagnostics) is dict and any(
        key in diagnostics for key in cost_keys)
    if has_cost_totals and any(key not in diagnostics for key in cost_keys):
        raise PaperEvaluationError("unreconciled_prospective_execution_costs")
    has_fees_paid = "fees_paid" in simulation
    if not trades:
        if has_fees_paid:
            value = simulation["fees_paid"]
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or not math.isclose(value, 0.0, abs_tol=1e-7)):
                raise PaperEvaluationError("unreconciled_prospective_execution_costs")
        if has_cost_totals:
            for key in cost_keys:
                value = diagnostics[key]
                if (type(value) not in (int, float) or not math.isfinite(value)
                        or not math.isclose(value, 0.0, abs_tol=1e-7)):
                    raise PaperEvaluationError("unreconciled_prospective_execution_costs")
        return None
    keys = (
        "entry_reference_open", "exit_reference_price", "entry", "exit",
        "quantity", "fees", "modeled_buy_slippage_cost_usdt",
        "modeled_sell_slippage_cost_usdt",
        "reference_gross_pnl_before_modeled_costs_usdt",
    )
    present = [any(key in trade for key in keys) for trade in trades]
    if not any(present):
        # Legacy synthetic trade stubs can be unverified, but cannot claim
        # verified aggregate fees or slippage without per-trade evidence.
        if has_cost_totals or has_fees_paid:
            raise PaperEvaluationError("unreconciled_prospective_execution_costs")
        return False
    if not all(present):
        raise PaperEvaluationError("unreconciled_prospective_execution_costs")
    fee, slip = config.fee_bps / 10_000, config.slippage_bps / 10_000
    for trade in trades:
        if any(key not in trade for key in keys):
            raise PaperEvaluationError("unreconciled_prospective_execution_costs")
        values = [trade[key] for key in keys]
        if (any(type(value) not in (int, float) or not math.isfinite(value)
                for value in values)
                or any(trade[key] <= 0 for key in (
                    "entry_reference_open", "exit_reference_price",
                    "entry", "exit", "quantity"))
                or any(trade[key] < 0 for key in (
                    "fees", "modeled_buy_slippage_cost_usdt",
                    "modeled_sell_slippage_cost_usdt"))):
            raise PaperEvaluationError("unreconciled_prospective_execution_costs")
        raw_entry = trade["entry_reference_open"]
        raw_exit = trade["exit_reference_price"]
        entry, exit_price, qty = trade["entry"], trade["exit"], trade["quantity"]
        expected = {
            "entry": raw_entry * (1 + slip),
            "exit": raw_exit * (1 - slip),
            "fees": qty * fee * (entry + exit_price),
            "modeled_buy_slippage_cost_usdt": qty * (entry - raw_entry),
            "modeled_sell_slippage_cost_usdt": qty * (raw_exit - exit_price),
            "reference_gross_pnl_before_modeled_costs_usdt": (
                qty * (raw_exit - raw_entry)),
        }
        expected["net_pnl"] = (
            expected["reference_gross_pnl_before_modeled_costs_usdt"]
            - expected["modeled_buy_slippage_cost_usdt"]
            - expected["modeled_sell_slippage_cost_usdt"] - expected["fees"])
        if any(not math.isfinite(wanted) or not math.isclose(
                trade[key], wanted, rel_tol=1e-9, abs_tol=1e-7)
                for key, wanted in expected.items()):
            raise PaperEvaluationError("unreconciled_prospective_execution_costs")
    try:
        fees = math.fsum(t["fees"] for t in trades)
        buy = math.fsum(t["modeled_buy_slippage_cost_usdt"] for t in trades)
        sell = math.fsum(t["modeled_sell_slippage_cost_usdt"] for t in trades)
    except (OverflowError, ValueError) as exc:
        raise PaperEvaluationError(
            "unreconciled_prospective_execution_costs") from exc
    if has_fees_paid:
        value = simulation["fees_paid"]
        if (type(value) not in (int, float) or not math.isfinite(value)
                or not math.isfinite(fees)
                or not math.isclose(value, fees, rel_tol=1e-9, abs_tol=1e-7)):
            raise PaperEvaluationError("unreconciled_prospective_execution_costs")
    if has_cost_totals:
        totals = (buy, sell, buy + sell, buy + sell + fees)
        for key, wanted in zip(cost_keys, totals):
            actual = diagnostics[key]
            if (type(actual) not in (int, float)
                    or not math.isfinite(actual) or not math.isfinite(wanted)
                    or not math.isclose(actual, wanted,
                                        rel_tol=1e-9, abs_tol=1e-7)):
                raise PaperEvaluationError("unreconciled_prospective_execution_costs")
    return True

def compare_capture_files(earlier: Path, earlier_receipt: Path,
                          later: Path, later_receipt: Path, *,
                          prospective_strategy: str | None = None) -> dict:
    if prospective_strategy is not None and prospective_strategy not in (
            "trend_pullback", "breakout_retest"):
        raise PaperEvaluationError("unsupported_prospective_strategy")
    symbol_a, a, proof_a, receipt_hash_a, candle_hash_a = _verified_local_capture(
        earlier, earlier_receipt)
    symbol_b, b, proof_b, receipt_hash_b, candle_hash_b = _verified_local_capture(
        later, later_receipt)
    if symbol_a != symbol_b or not a or not b:
        raise PaperEvaluationError("incompatible_capture_identity")
    if (proof_b["captured_at_ms"] <= proof_a["captured_at_ms"]
            or b[0].time < a[0].time
            or b[-1].time <= a[-1].time):
        raise PaperEvaluationError("captures_not_chronologically_newer")

    # Both individual samples were already checked for exact 15m cadence.
    # The intersection must be a contiguous suffix/prefix, not merely a few
    # matching timestamps. This detects silent historical OHLCV revisions
    # even if each independently supplied unsigned receipt was recomputed.
    first_shared = max(a[0].time, b[0].time)
    old_overlap = [bar for bar in a if bar.time >= first_shared]
    new_overlap = [bar for bar in b if bar.time <= a[-1].time]
    if (len(old_overlap) < 20 or len(old_overlap) != len(new_overlap)
            or old_overlap[0].time != new_overlap[0].time
            or old_overlap[-1].time != new_overlap[-1].time):
        raise PaperEvaluationError("insufficient_contiguous_capture_overlap")
    for old, new in zip(old_overlap, new_overlap):
        if old != new:
            raise PaperEvaluationError("historical_capture_candle_revised")

    new_bars = b[len(new_overlap):]
    if (not new_bars or new_bars[0].time != a[-1].time + STEP_MS
            or new_bars[-1].time != b[-1].time):
        raise PaperEvaluationError("missing_new_closed_candle_or_gap")
    # A valid unsigned receipt can be recorded up to two intervals after its
    # last included bar. If the next bar had already CLOSED by that earlier
    # capture, it was not a newly closed observation after the first sample.
    # Never count stale, operator-supplied history as a forward observation.
    if new_bars[0].close_time <= proof_a["captured_at_ms"]:
        raise PaperEvaluationError("new_closed_bar_not_after_earlier_capture")
    # A bar that started before the earlier receipt was captured is only
    # partially prospective, even if its close occurred afterwards. Require
    # at least one entire, fully closed bar that opened after that receipt.
    # Preserve partial bars in the overlap audit but never count them as
    # full post-capture observations.
    fully_post_capture = [bar for bar in new_bars
                          if bar.time >= proof_a["captured_at_ms"]]
    if not fully_post_capture:
        raise PaperEvaluationError("no_full_post_capture_closed_candle")
    report = {
        "mode": "manual_local_spot_capture_overlap_audit",
        "status": "unsigned_local_captures_overlap_consistent",
        "symbol": symbol_a, "interval": "15m", "orders_enabled": False,
        "earlier_candle_sha256": candle_hash_a,
        "later_candle_sha256": candle_hash_b,
        "earlier_unsigned_receipt_sha256": receipt_hash_a,
        "later_unsigned_receipt_sha256": receipt_hash_b,
        "overlapping_identical_closed_bars": len(old_overlap),
        "newer_closed_bars": len(new_bars),
        "fully_post_capture_closed_bars": len(fully_post_capture),
        "partial_at_capture_closed_bars": len(new_bars) - len(fully_post_capture),
        "first_fully_post_capture_open_at_ms": fully_post_capture[0].time,
        "newer_first_open_at_ms": new_bars[0].time,
        "newer_last_closed_at_ms": new_bars[-1].close_time,
        "independent_venue_authenticated": False,
        "forward_paper_fills_verified": False,
        "profitability_verified": False,
        "limitations": [
            "Both captures and receipts are local, operator-supplied and unsigned.",
            "An overlap match detects revisions but cannot authenticate provider identity or earlier history.",
            "Only bars opened after the earlier receipt count as fully post-capture observations; partial bars are excluded.",
            "New closed candles are NOT independently observed paper fills or a forward strategy result.",
            "No signal, order, leverage, calibrated win probability or profit claim.",
        ],
    }
    if prospective_strategy is not None:
        # This opt-in replay scores ONLY bars whose entire interval began
        # after the earlier unsigned receipt. Earlier bars are warmup only.
        # The same local later capture supplies prices; this is NOT an
        # independent forward-fill observation or exchange attestation.
        first_scored = fully_post_capture[0].time
        scored_index = next(i for i, bar in enumerate(b) if bar.time == first_scored)
        if scored_index < WARMUP_BARS:
            raise PaperEvaluationError("insufficient_prospective_warmup")
        segment = b[scored_index - WARMUP_BARS:]
        baseline_config = SimulationConfig()
        simulation = backtest(
            segment, prospective_strategy, baseline_config,
            entry_not_before=first_scored,
        )
        # Same exact scored candles, strategy and risk defaults; ONLY both
        # adverse fee/slippage assumptions are doubled. This sensitivity is
        # neither an independent dataset nor a claim that PnL must decrease:
        # changed fills/sizing can change subsequent entries and exits.
        stress_config = SimulationConfig(
            equity=baseline_config.equity,
            risk_pct=baseline_config.risk_pct,
            daily_loss_limit=baseline_config.daily_loss_limit,
            fee_bps=baseline_config.fee_bps * 2,
            slippage_bps=baseline_config.slippage_bps * 2,
        )
        stressed = backtest(
            segment, prospective_strategy, stress_config,
            entry_not_before=first_scored,
        )
        baseline_metadata_verified = _verified_replay_metadata(
            simulation, prospective_strategy, baseline_config, segment)
        stress_metadata_verified = _verified_replay_metadata(
            stressed, prospective_strategy, stress_config, segment)
        baseline_entries = _verified_prospective_ledger(
            simulation, first_scored, b[-1].close_time, baseline_config.equity)
        stress_entries = _verified_prospective_ledger(
            stressed, first_scored, b[-1].close_time, stress_config.equity)
        baseline_costs_verified = _verified_execution_costs(simulation, baseline_config)
        stress_costs_verified = _verified_execution_costs(stressed, stress_config)
        baseline_set, stress_set = set(baseline_entries), set(stress_entries)
        forced = [trade for trade in simulation["trades"]
                  if trade["terminal_forced_mark"]]
        resolved = [trade for trade in simulation["trades"]
                    if not trade["terminal_forced_mark"]]
        report["prospective_paper_replay"] = {
            "status": "modeled_local_unsigned_same_series_not_independent",
            "strategy": prospective_strategy,
            "first_scored_entry_at_ms": first_scored,
            "scored_closed_bars": len(b) - scored_index,
            "prior_closed_warmup_bars": WARMUP_BARS,
            "fixed_default_paper_settings": True,
            "modeled_trade_chronology_and_pnl_reconciled": True,
            "modeled_execution_costs_reconciled": baseline_costs_verified,
            "modeled_strategy_cost_window_metadata_reconciled": baseline_metadata_verified,
            "strategy_resolved_trade_count": len(resolved),
            "terminal_forced_mark_count": len(forced),
            "resolved_trade_net_pnl_usdt": sum(
                trade["net_pnl"] for trade in resolved),
            "terminal_forced_mark_net_pnl_usdt": sum(
                trade["net_pnl"] for trade in forced),
            "win_probability": None,
            "independent_venue_authenticated": False,
            "forward_paper_fills_verified": False,
            "profitability_verified": False,
            "simulation": {k: v for k, v in simulation.items()
                           if k != "input_candles"},
            "double_cost_same_series_sensitivity": {
                "status": "modeled_same_series_not_independent",
                "fee_bps": stress_config.fee_bps,
                "slippage_bps": stress_config.slippage_bps,
                "baseline_net_pnl_usdt": simulation["net_pnl"],
                "double_cost_net_pnl_usdt": stressed["net_pnl"],
                "double_cost_minus_baseline_net_pnl_usdt": (
                    stressed["net_pnl"] - simulation["net_pnl"]),
                "baseline_trade_count": len(baseline_entries),
                "double_cost_trade_count": len(stress_entries),
                "shared_entry_count": len(baseline_set & stress_set),
                "baseline_only_entry_count": len(baseline_set - stress_set),
                "double_cost_only_entry_count": len(stress_set - baseline_set),
                "double_cost_strategy_resolved_trade_count": sum(
                    not trade["terminal_forced_mark"] for trade in stressed["trades"]),
                "double_cost_terminal_forced_mark_count": sum(
                    trade["terminal_forced_mark"] for trade in stressed["trades"]),
                "double_cost_max_drawdown_pct": stressed["max_drawdown_pct"],
                "modeled_trade_chronology_and_pnl_reconciled": True,
                "modeled_execution_costs_reconciled": stress_costs_verified,
                "modeled_strategy_cost_window_metadata_reconciled": stress_metadata_verified,
                "simulation": {k: v for k, v in stressed.items()
                               if k != "input_candles"},
                "independent_evaluation": False,
                "profitability_verified": False,
                "limitations": [
                    "This is the same operator-supplied later capture, not independent holdout data.",
                    "Both sides' fees and adverse slippage are doubled; changing fills and risk sizing may change entry timestamps, so PnL is not guaranteed monotonic.",
                    "All negative, zero-trade, gap, ambiguity, drawdown and forced terminal outcomes remain in the modeled simulation.",
                    "Modeled entry/exit chronology and net PnL are locally checked, not real fills.",
                    "No authenticated fills, calibrated win probability, executable quote or profitability claim.",
                ],
            },
            "limitations": [
                "Only fully post-earlier-capture bars are scored; 64 earlier closed bars are warmup context, never entries.",
                "Both local receipts are unsigned; later candles are operator supplied, not independently authenticated.",
                "Next-open fills, fees, slippage, gap stops and stop-first ambiguity are modeled, not observed.",
                "Forced end-of-sample marks are not resolved strategy exits; modeled net PnL includes them.",
                "Nonoverlapping modeled trade lifecycles and net PnL are reconciled, not exchange-attested.",
                "Zero trades, losses and drawdown remain visible; no independent forward performance or profitability proof.",
            ],
        }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare two unsigned manual spot captures; no orders or network")
    parser.add_argument("--earlier", required=True, type=Path)
    parser.add_argument("--earlier-receipt", required=True, type=Path)
    parser.add_argument("--later", required=True, type=Path)
    parser.add_argument("--later-receipt", required=True, type=Path)
    parser.add_argument("--prospective-replay",
                        choices=("trend_pullback", "breakout_retest"),
                        help="Optional fixed-default modeled replay of fully post-capture bars; NOT independent fills")
    args = parser.parse_args(argv)
    try:
        report = compare_capture_files(args.earlier, args.earlier_receipt,
                                       args.later, args.later_receipt,
                                       prospective_strategy=args.prospective_replay)
        output = json.dumps(report, sort_keys=True, allow_nan=False)
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
        print("WAIT: captures missing, changed, incompatible or unverifiable; no comparison emitted.",
              file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
