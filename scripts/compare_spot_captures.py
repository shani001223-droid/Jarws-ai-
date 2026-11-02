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
import json
import sys
from pathlib import Path

from cloud_backend.paper_evaluation import (
    STEP_MS, WARMUP_BARS, PaperEvaluationError, attach_capture_receipt,
    evaluate_chronological,
)
from cloud_backend.trading_research import SimulationConfig, backtest
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
        simulation = backtest(
            segment, prospective_strategy, SimulationConfig(),
            entry_not_before=first_scored,
        )
        if any(trade["entry_time"] < first_scored
               for trade in simulation["trades"]):
            raise PaperEvaluationError("noncausal_prospective_replay")
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
            "limitations": [
                "Only fully post-earlier-capture bars are scored; 64 earlier closed bars are warmup context, never entries.",
                "Both local receipts are unsigned; later candles are operator supplied, not independently authenticated.",
                "Next-open fills, fees, slippage, gap stops and stop-first ambiguity are modeled, not observed.",
                "Forced end-of-sample marks are not resolved strategy exits; modeled net PnL includes them.",
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
