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



def _verified_exit_semantics(simulation: dict, last_closed: int) -> bool | None:
    """Reconcile modeled exit reasons, timestamp precision and ambiguity labels.

    True means the LOCAL paper engine's complete exit annotations agree with
    its timestamps. False means legacy synthetic stubs provide no such
    evidence. None means zero trades. None of these authenticates fills.
    """
    trades = simulation["trades"]
    if not trades:
        return None
    keys = ("reason", "exit_time_precision", "stop_target_same_bar",
            "gap_beyond_stop_pct")
    claims = [any(key in trade for key in keys) for trade in trades]
    if not any(claims):
        return False
    if not all(claims):
        raise PaperEvaluationError("unreconciled_prospective_exit_semantics")
    open_reasons = {"gap_stop", "stop_at_open", "target_gap_open"}
    intrabar_reasons = {"stop", "target"}
    close_reasons = {"time_exit", "end_of_sample"}
    for trade in trades:
        if any(key not in trade for key in keys):
            raise PaperEvaluationError("unreconciled_prospective_exit_semantics")
        reason, precision = trade["reason"], trade["exit_time_precision"]
        exit_at = trade["exit_time"]
        if reason in open_reasons:
            wanted, remainder = "bar_open_exact", 0
        elif reason in intrabar_reasons:
            wanted, remainder = "bar_close_upper_bound_intrabar_unknown", STEP_MS - 1
        elif reason in close_reasons:
            wanted, remainder = "bar_close_exact", STEP_MS - 1
        else:
            raise PaperEvaluationError("unreconciled_prospective_exit_semantics")
        gap = trade["gap_beyond_stop_pct"]
        if (type(reason) is not str or type(precision) is not str
                or precision != wanted or exit_at % STEP_MS != remainder
                or trade["terminal_forced_mark"] != (reason == "end_of_sample")
                or (reason == "end_of_sample" and exit_at != last_closed)
                or type(trade["stop_target_same_bar"]) is not bool
                or (trade["stop_target_same_bar"] and reason != "stop")
                or (reason == "gap_stop" and
                    (type(gap) not in (int, float) or not math.isfinite(gap)
                     or gap <= 0))
                or (reason != "gap_stop" and gap is not None)):
            raise PaperEvaluationError("unreconciled_prospective_exit_semantics")
    return True



def _verified_candle_price_anchors(simulation: dict, segment: list) -> bool | None:
    """Bind MODELED entries and exits to the supplied closed 15m candles.

    True verifies only local OHLC/strategy arithmetic, not provider identity,
    executable prices, independent fills or performance. Legacy synthetic
    stubs without stop/target anchors are explicitly unverified (False).
    """
    trades = simulation["trades"]
    if not trades:
        return None
    anchor_keys = ("reference_stop", "reference_target")
    claimed = [any(key in trade for key in anchor_keys) for trade in trades]
    if not any(claimed):
        return False
    if not all(claimed):
        raise PaperEvaluationError("unreconciled_prospective_candle_prices")
    required = (
        "entry_time", "exit_time", "entry_reference_open",
        "exit_reference_price", "reference_stop", "reference_target",
        "reason", "stop_target_same_bar", "gap_beyond_stop_pct",
    )
    first = segment[0].time
    last = len(segment) - 1

    def same(a, b):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-7)

    for trade in trades:
        if any(key not in trade for key in required):
            raise PaperEvaluationError("unreconciled_prospective_candle_prices")
        entry_at, exit_at = trade["entry_time"], trade["exit_time"]
        if (type(entry_at) is not int or type(exit_at) is not int
                or entry_at % STEP_MS
                or exit_at % STEP_MS not in (0, STEP_MS - 1)):
            raise PaperEvaluationError("unreconciled_prospective_candle_prices")
        entry_i = (entry_at - first) // STEP_MS
        exit_i = (exit_at - first) // STEP_MS
        if not (0 <= entry_i <= exit_i <= last
                and segment[entry_i].time == entry_at
                and segment[exit_i].time <= exit_at <= segment[exit_i].close_time):
            raise PaperEvaluationError("unreconciled_prospective_candle_prices")
        entry_bar, exit_bar = segment[entry_i], segment[exit_i]
        raw_entry = trade["entry_reference_open"]
        raw_exit = trade["exit_reference_price"]
        stop, target = trade["reference_stop"], trade["reference_target"]
        if (any(type(x) not in (int, float) or not math.isfinite(x)
                for x in (raw_entry, raw_exit, stop, target))
                or not 0 < stop < raw_entry < target
                or not same(raw_entry, entry_bar.open)
                or type(trade["stop_target_same_bar"]) is not bool):
            raise PaperEvaluationError("unreconciled_prospective_candle_prices")
        # A position cannot survive a previous bar that already crossed an
        # exit boundary; the next-open/stop-first model must exit immediately.
        for previous in segment[entry_i:exit_i]:
            if previous.low <= stop or previous.high >= target:
                raise PaperEvaluationError("unreconciled_prospective_candle_prices")
        if exit_i - entry_i > 96:
            raise PaperEvaluationError("unreconciled_prospective_candle_prices")
        if exit_bar.open < stop:
            reason, expected_exit = "gap_stop", exit_bar.open
            expected_gap = (stop - exit_bar.open) / stop * 100
        elif exit_bar.open == stop:
            reason, expected_exit = "stop_at_open", exit_bar.open
            expected_gap = None
        elif exit_bar.open >= target:
            reason, expected_exit = "target_gap_open", target
            expected_gap = None
        elif exit_bar.low <= stop:
            reason, expected_exit = "stop", stop
            expected_gap = None
        elif exit_bar.high >= target:
            reason, expected_exit = "target", target
            expected_gap = None
        elif exit_i - entry_i == 96:
            reason, expected_exit = "time_exit", exit_bar.close
            expected_gap = None
        elif exit_i == last:
            reason, expected_exit = "end_of_sample", exit_bar.close
            expected_gap = None
        else:
            raise PaperEvaluationError("unreconciled_prospective_candle_prices")
        ambiguous = (reason == "stop" and exit_bar.high >= target
                     and stop < exit_bar.open < target)
        gap = trade["gap_beyond_stop_pct"]
        if (trade["reason"] != reason
                or not same(raw_exit, expected_exit)
                or trade["stop_target_same_bar"] != ambiguous
                or (expected_gap is None and gap is not None)
                or (expected_gap is not None and (
                    type(gap) not in (int, float) or not math.isfinite(gap)
                    or not same(gap, expected_gap)))):
            raise PaperEvaluationError("unreconciled_prospective_candle_prices")
    return True


def _verified_prior_closed_volume(simulation: dict, segment: list) -> bool | None:
    """Reconcile modeled participation to PREVIOUS closed 15m base volume.

    The current entry bar's volume is future information at the next-open
    decision: it is disclosed ex post, never used to veto the entry. This
    audit checks local, unsigned OHLCV only, not executable market depth.
    """
    trades = simulation["trades"]
    diagnostics = simulation.get("execution_diagnostics")
    if diagnostics is not None and type(diagnostics) is not dict:
        raise PaperEvaluationError("unreconciled_prospective_prior_volume")
    diagnostic_keys = (
        "paper_entries_with_zero_volume_entry_bar_ex_post",
        "paper_entries_opened",
    )
    if not trades:
        if diagnostics is not None:
            for key in diagnostic_keys:
                if key in diagnostics and (
                        type(diagnostics[key]) is not int or diagnostics[key] != 0):
                    raise PaperEvaluationError("unreconciled_prospective_prior_volume")
        return None
    keys = (
        "prior_closed_bar_base_volume",
        "entry_bar_zero_volume_ex_post",
        "modeled_entry_qty_pct_of_prior_closed_bar_volume",
    )
    claimed = [any(key in trade for key in keys) for trade in trades]
    if not any(claimed):
        return False
    if not all(claimed):
        raise PaperEvaluationError("unreconciled_prospective_prior_volume")
    first = segment[0].time
    ex_post_zero = 0
    for trade in trades:
        if any(key not in trade for key in keys):
            raise PaperEvaluationError("unreconciled_prospective_prior_volume")
        entry_at, qty = trade["entry_time"], trade.get("quantity")
        if (type(entry_at) is not int or entry_at % STEP_MS
                or type(qty) not in (int, float) or not math.isfinite(qty)
                or qty <= 0):
            raise PaperEvaluationError("unreconciled_prospective_prior_volume")
        i = (entry_at - first) // STEP_MS
        if not (1 <= i < len(segment) and segment[i].time == entry_at):
            raise PaperEvaluationError("unreconciled_prospective_prior_volume")
        previous, current = segment[i - 1].volume, segment[i].volume
        reported = trade["prior_closed_bar_base_volume"]
        if (any(type(v) not in (int, float) or not math.isfinite(v)
                for v in (previous, current, reported))
                or previous <= 0 or current < 0
                or not math.isclose(reported, previous,
                                    rel_tol=1e-9, abs_tol=1e-9)):
            raise PaperEvaluationError("unreconciled_prospective_prior_volume")
        zero = current == 0
        if type(trade["entry_bar_zero_volume_ex_post"]) is not bool or (
                trade["entry_bar_zero_volume_ex_post"] != zero):
            raise PaperEvaluationError("unreconciled_prospective_prior_volume")
        ex_post_zero += int(zero)
        try:
            pct = qty / previous * 100
        except (OverflowError, ZeroDivisionError):
            pct = float("inf")
        wanted = pct if math.isfinite(pct) else None
        reported_pct = trade["modeled_entry_qty_pct_of_prior_closed_bar_volume"]
        if wanted is None:
            if reported_pct is not None:
                raise PaperEvaluationError("unreconciled_prospective_prior_volume")
        elif (type(reported_pct) not in (int, float)
              or not math.isfinite(reported_pct)
              or not math.isclose(reported_pct, wanted,
                                  rel_tol=1e-9, abs_tol=1e-7)):
            raise PaperEvaluationError("unreconciled_prospective_prior_volume")
    if diagnostics is not None:
        expected = {
            "paper_entries_with_zero_volume_entry_bar_ex_post": ex_post_zero,
            "paper_entries_opened": len(trades),
        }
        for key, value in expected.items():
            if key in diagnostics and (
                    type(diagnostics[key]) is not int or diagnostics[key] != value):
                raise PaperEvaluationError("unreconciled_prospective_prior_volume")
    return True


def _verified_modeled_risk_outcomes(simulation: dict,
                                    config: SimulationConfig) -> bool | None:
    """Audit modeled per-trade risk budgets and UTC realized-loss accounting.

    This checks only local simulated arithmetic. Neither a planned budget nor
    a daily entry lockout guarantees an exchange fill or maximum gap loss.
    """
    trades = simulation["trades"]
    diagnostics = simulation.get("execution_diagnostics")
    keys = (
        "risk_budget_at_entry_usdt", "planned_stop_loss_usdt",
        "risk_budget_breached", "planned_stop_loss_exceeded",
        "utc_day_gross_realized_loss_after_exit_usdt",
        "utc_day_gross_loss_cap_breached", "realized_loss_to_budget_multiple",
    )
    aggregate_keys = (
        "risk_budget_breach_count", "planned_stop_loss_exceeded_count",
        "max_loss_to_risk_budget_multiple", "utc_daily_gross_loss_cap_usdt",
        "utc_gross_loss_cap_breach_days",
        "max_utc_day_gross_realized_loss_usdt",
    )

    def fail():
        raise PaperEvaluationError("unreconciled_prospective_paper_risk")

    def finite(value):
        return type(value) in (int, float) and math.isfinite(value)

    def same(actual, expected):
        return finite(actual) and math.isclose(
            actual, expected, rel_tol=1e-9, abs_tol=1e-7)

    if diagnostics is not None and type(diagnostics) is not dict:
        fail()
    present_aggregates = (set(aggregate_keys) & set(diagnostics)
                          if diagnostics is not None else set())
    if present_aggregates and len(present_aggregates) != len(aggregate_keys):
        fail()
    if not trades:
        if present_aggregates:
            for key, expected in (
                ("risk_budget_breach_count", 0),
                ("planned_stop_loss_exceeded_count", 0),
                ("max_loss_to_risk_budget_multiple", None),
                ("utc_daily_gross_loss_cap_usdt", config.daily_loss_limit),
                ("utc_gross_loss_cap_breach_days", 0),
                ("max_utc_day_gross_realized_loss_usdt", 0.0),
            ):
                value = diagnostics[key]
                if (value is not None or expected is not None) and (
                        (expected is None and value is not None)
                        or (expected is not None and not same(value, expected))):
                    fail()
        return None
    claimed = [any(key in trade for key in keys) for trade in trades]
    if not any(claimed):
        if present_aggregates:
            fail()
        return False
    if not all(claimed):
        fail()
    cash, day_losses = config.equity, {}
    breaches = planned_breaches = 0
    max_multiple = None
    fee, slip = config.fee_bps / 10_000, config.slippage_bps / 10_000
    for trade in trades:
        if any(key not in trade for key in keys):
            fail()
        entry_at, exit_at = trade["entry_time"], trade["exit_time"]
        entry, stop, qty = (
            trade.get("entry"), trade.get("reference_stop"),
            trade.get("quantity"))
        net, budget, planned = (
            trade["net_pnl"], trade["risk_budget_at_entry_usdt"],
            trade["planned_stop_loss_usdt"])
        if (type(entry_at) is not int or type(exit_at) is not int
                or any(not finite(x) for x in (entry, stop, qty, net,
                                                budget, planned))
                or not 0 < stop < entry or qty <= 0 or budget <= 0
                or planned <= 0):
            fail()
        entry_day = entry_at // 86_400_000
        remaining = config.daily_loss_limit - day_losses.get(entry_day, 0.0)
        expected_budget = min(cash * config.risk_pct / 100, remaining)
        stop_exit = stop * (1 - slip)
        expected_planned = qty * (
            entry - stop_exit + fee * (entry + stop_exit))
        if (expected_budget <= 0
                or not same(budget, expected_budget)
                or not same(planned, expected_planned)
                or planned > budget + 1e-7):
            fail()
        loss = max(0.0, -net)
        breached = loss > budget + 1e-8
        planned_breached = loss > planned + 1e-8
        if (type(trade["risk_budget_breached"]) is not bool
                or trade["risk_budget_breached"] != breached
                or type(trade["planned_stop_loss_exceeded"]) is not bool
                or trade["planned_stop_loss_exceeded"] != planned_breached):
            fail()
        multiple = loss / budget if loss else None
        reported_multiple = trade["realized_loss_to_budget_multiple"]
        if ((multiple is None and reported_multiple is not None)
                or (multiple is not None
                    and not same(reported_multiple, multiple))):
            fail()
        exit_day = exit_at // 86_400_000
        day_losses[exit_day] = day_losses.get(exit_day, 0.0) + loss
        daily_loss = day_losses[exit_day]
        daily_breached = daily_loss > config.daily_loss_limit + 1e-8
        if (not same(trade["utc_day_gross_realized_loss_after_exit_usdt"],
                     daily_loss)
                or type(trade["utc_day_gross_loss_cap_breached"]) is not bool
                or trade["utc_day_gross_loss_cap_breached"] != daily_breached):
            fail()
        breaches += int(breached)
        planned_breaches += int(planned_breached)
        if multiple is not None:
            max_multiple = max(max_multiple or 0.0, multiple)
        cash += net
    if present_aggregates:
        expected = {
            "risk_budget_breach_count": breaches,
            "planned_stop_loss_exceeded_count": planned_breaches,
            "max_loss_to_risk_budget_multiple": max_multiple,
            "utc_daily_gross_loss_cap_usdt": config.daily_loss_limit,
            "utc_gross_loss_cap_breach_days": sum(
                loss > config.daily_loss_limit + 1e-8
                for loss in day_losses.values()),
            "max_utc_day_gross_realized_loss_usdt": max(
                day_losses.values(), default=0.0),
        }
        for key, wanted in expected.items():
            got = diagnostics[key]
            if ((wanted is None and got is not None)
                    or (wanted is not None and not same(got, wanted))):
                fail()
    return True



def _verified_original_target_accounting(simulation: dict,
                                         config: SimulationConfig) -> bool | None:
    """Reconcile the modeled ORIGINAL signal-target opportunity at entry.

    This checks only internal next-open paper arithmetic. The claimed original
    signal target itself is NOT independently authenticated against a venue,
    and these ratios are not observed fills or calibrated probabilities.
    """
    trades = simulation["trades"]
    diagnostics = simulation.get("execution_diagnostics")
    aggregate_keys = (
        "paper_entries_original_signal_remaining_rr_below_1r",
        "paper_entries_original_signal_net_upside_nonpositive",
    )
    keys = (
        "original_signal_target",
        "remaining_original_signal_reward_risk_at_entry",
        "original_signal_target_net_gain_per_unit_usdt",
        "remaining_original_signal_net_reward_risk_at_entry",
    )

    def fail():
        raise PaperEvaluationError("unreconciled_prospective_original_target")

    def finite(value):
        return type(value) in (int, float) and math.isfinite(value)

    def same(value, expected):
        return finite(value) and math.isclose(
            value, expected, rel_tol=1e-9, abs_tol=1e-7)

    if diagnostics is not None and type(diagnostics) is not dict:
        fail()
    present = (set(aggregate_keys) & set(diagnostics)
               if diagnostics is not None else set())
    if present and len(present) != len(aggregate_keys):
        fail()
    if not trades:
        if present and any(
                type(diagnostics[key]) is not int or diagnostics[key] != 0
                for key in aggregate_keys):
            fail()
        return None
    claims = [any(key in trade for key in keys) for trade in trades]
    if not any(claims):
        if present:
            fail()
        return False
    if not all(claims):
        fail()
    fee, slip = config.fee_bps / 10_000, config.slippage_bps / 10_000
    below_one, nonpositive = 0, 0
    for trade in trades:
        if any(key not in trade for key in keys):
            fail()
        entry = trade.get("entry")
        stop = trade.get("reference_stop")
        target = trade.get("reference_target")
        original = trade["original_signal_target"]
        if (any(not finite(v) for v in (entry, stop, target, original))
                or not 0 < stop < entry < original
                or not same(target, entry + 2 * (entry - stop))):
            fail()
        planned_exit = stop * (1 - slip)
        planned_loss_per_unit = (
            entry - planned_exit + fee * (entry + planned_exit))
        if not math.isfinite(planned_loss_per_unit) or planned_loss_per_unit <= 0:
            fail()
        gross_rr = (original - entry) / (entry - stop)
        original_exit = original * (1 - slip)
        net_gain = original_exit - entry - fee * (entry + original_exit)
        net_rr = net_gain / planned_loss_per_unit
        if (any(not math.isfinite(v) for v in (gross_rr, net_gain, net_rr))
                or not same(
                    trade["remaining_original_signal_reward_risk_at_entry"],
                    gross_rr)
                or not same(
                    trade["original_signal_target_net_gain_per_unit_usdt"],
                    net_gain)
                or not same(
                    trade["remaining_original_signal_net_reward_risk_at_entry"],
                    net_rr)):
            fail()
        below_one += int(gross_rr < 1)
        nonpositive += int(net_gain <= 0)
    if present:
        for key, expected in zip(aggregate_keys, (below_one, nonpositive)):
            if type(diagnostics[key]) is not int or diagnostics[key] != expected:
                fail()
    return True



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
        baseline_exit_semantics_verified = _verified_exit_semantics(
            simulation, b[-1].close_time)
        stress_exit_semantics_verified = _verified_exit_semantics(
            stressed, b[-1].close_time)
        baseline_candle_prices_verified = _verified_candle_price_anchors(
            simulation, segment)
        stress_candle_prices_verified = _verified_candle_price_anchors(
            stressed, segment)
        baseline_volume_verified = _verified_prior_closed_volume(
            simulation, segment)
        stress_volume_verified = _verified_prior_closed_volume(
            stressed, segment)
        baseline_risk_verified = _verified_modeled_risk_outcomes(
            simulation, baseline_config)
        stress_risk_verified = _verified_modeled_risk_outcomes(
            stressed, stress_config)
        baseline_original_target_verified = _verified_original_target_accounting(
            simulation, baseline_config)
        stress_original_target_verified = _verified_original_target_accounting(
            stressed, stress_config)
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
            "modeled_exit_reason_and_timing_reconciled": baseline_exit_semantics_verified,
            "modeled_candle_price_anchors_reconciled": baseline_candle_prices_verified,
            "modeled_prior_closed_volume_reconciled": baseline_volume_verified,
            "modeled_risk_budget_and_utc_loss_reconciled": baseline_risk_verified,
            "modeled_original_signal_target_cost_ratios_reconciled": baseline_original_target_verified,
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
                "modeled_exit_reason_and_timing_reconciled": stress_exit_semantics_verified,
                "modeled_candle_price_anchors_reconciled": stress_candle_prices_verified,
                "modeled_prior_closed_volume_reconciled": stress_volume_verified,
                "modeled_risk_budget_and_utc_loss_reconciled": stress_risk_verified,
                "modeled_original_signal_target_cost_ratios_reconciled": stress_original_target_verified,
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
