"""Manual, read-only consistency audit of two separate public spot captures.

Usage:
  python -m scripts.compare_spot_captures \
    --earlier old.json --earlier-receipt old.receipt \
    --later new.json --later-receipt new.receipt

This only checks local, UNSIGNED receipt bindings and overlapping closed bars.
It does not authenticate either exchange, verify fills, run a forward strategy,
fetch network data, write files, or place orders.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cloud_backend.paper_evaluation import (
    STEP_MS, PaperEvaluationError, attach_capture_receipt,
    evaluate_chronological,
)
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
                          later: Path, later_receipt: Path) -> dict:
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
    return {
        "mode": "manual_local_spot_capture_overlap_audit",
        "status": "unsigned_local_captures_overlap_consistent",
        "symbol": symbol_a, "interval": "15m", "orders_enabled": False,
        "earlier_candle_sha256": candle_hash_a,
        "later_candle_sha256": candle_hash_b,
        "earlier_unsigned_receipt_sha256": receipt_hash_a,
        "later_unsigned_receipt_sha256": receipt_hash_b,
        "overlapping_identical_closed_bars": len(old_overlap),
        "newer_closed_bars": len(new_bars),
        "newer_first_open_at_ms": new_bars[0].time,
        "newer_last_closed_at_ms": new_bars[-1].close_time,
        "independent_venue_authenticated": False,
        "forward_paper_fills_verified": False,
        "profitability_verified": False,
        "limitations": [
            "Both captures and receipts are local, operator-supplied and unsigned.",
            "An overlap match detects revisions but cannot authenticate provider identity or earlier history.",
            "New closed candles are NOT independently observed paper fills or a forward strategy result.",
            "No signal, order, leverage, calibrated win probability or profit claim.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare two unsigned manual spot captures; no orders or network")
    parser.add_argument("--earlier", required=True, type=Path)
    parser.add_argument("--earlier-receipt", required=True, type=Path)
    parser.add_argument("--later", required=True, type=Path)
    parser.add_argument("--later-receipt", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = compare_capture_files(args.earlier, args.earlier_receipt,
                                       args.later, args.later_receipt)
        output = json.dumps(report, sort_keys=True, allow_nan=False)
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
        print("WAIT: captures missing, changed, incompatible or unverifiable; no comparison emitted.",
              file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
