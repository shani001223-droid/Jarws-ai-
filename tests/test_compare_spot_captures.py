"""Offline capture-overlap audit tests; synthetic data only, no network."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from cloud_backend.paper_evaluation import PaperEvaluationError
from scripts import capture_spot_history as capture
from scripts import compare_spot_captures as compare

NOW = 1_800_000_000_000
STEP = 900_000


def capture_fixture(shift=0, symbol="BTCUSDT", revise_volume=False):
    now = NOW + shift * STEP
    first = (now // STEP - 499) * STEP
    binance, kraken = [], []
    for i in range(500):
        t = first + i * STEP
        base = "11" if revise_volume and i == 200 else "10"
        binance.append([t, "100", "101", "99", "100", base,
                        t + STEP - 1, "1100" if base == "11" else "1000",
                        5, "4", "400", "0"])
        kraken.append([t // 1000, "100", "101", "99", "100",
                       "100", "10", 5])
    key = "XXBTZUSD" if symbol == "BTCUSDT" else "XETHZUSD"
    peer = {"error": [], "result": {key: kraken, "last": "0"}}
    return capture.capture_spot_history(
        symbol, fetch_json=lambda u: peer if "kraken.com" in u else binance,
        clock=lambda: now / 1000)


def save_pair(directory, prefix, pair):
    data, receipt = pair
    source = directory / (prefix + ".json")
    proof = directory / (prefix + ".receipt")
    source.write_text(json.dumps(data), encoding="utf-8")
    proof.write_text("HOSHI_CAPTURE_RECEIPT " + json.dumps(receipt) + "\n",
                     encoding="utf-8")
    return source, proof


class CaptureOverlapTests(unittest.TestCase):
    def test_one_new_closed_bar_and_exact_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, old_receipt = save_pair(root, "old", capture_fixture())
            new, new_receipt = save_pair(root, "new", capture_fixture(1))
            result = compare.compare_capture_files(old, old_receipt, new, new_receipt)
            self.assertEqual(result["overlapping_identical_closed_bars"], 498)
            self.assertEqual(result["newer_closed_bars"], 1)
            self.assertEqual(result["fully_post_capture_closed_bars"], 1)
            self.assertEqual(result["partial_at_capture_closed_bars"], 0)
            self.assertEqual(result["first_fully_post_capture_open_at_ms"], NOW)
            self.assertEqual(result["newer_first_open_at_ms"], NOW)
            self.assertFalse(result["orders_enabled"])
            self.assertFalse(result["independent_venue_authenticated"])
            self.assertFalse(result["forward_paper_fills_verified"])
            self.assertFalse(result["profitability_verified"])

    def test_revised_old_volume_refused_despite_individually_valid_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(1, revise_volume=True))
            with self.assertRaisesRegex(PaperEvaluationError,
                                        "historical_capture_candle_revised"):
                compare.compare_capture_files(old, proof_old, new, proof_new)

    def test_same_snapshot_is_not_forward_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture())
            with self.assertRaisesRegex(PaperEvaluationError,
                                        "captures_not_chronologically_newer"):
                compare.compare_capture_files(old, proof_old, new, proof_new)

    def test_sparse_overlap_or_wrong_market_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            for suffix, pair, reason in (
                ("gap", capture_fixture(490), "insufficient_contiguous_capture_overlap"),
                ("symbol", capture_fixture(1, "ETHUSDT"), "incompatible_capture_identity"),
            ):
                with self.subTest(suffix=suffix):
                    new, proof_new = save_pair(root, suffix, pair)
                    with self.assertRaisesRegex(PaperEvaluationError, reason):
                        compare.compare_capture_files(old, proof_old, new, proof_new)

    def test_new_bars_must_close_after_earlier_capture_time(self):
        # The first receipt can still pass its own binding when its data
        # is one interval stale. That old receipt must not make a candle
        # already closed at the earlier capture look like forward evidence.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale_pair = capture_fixture()
            stale_pair[1]["captured_at_ms"] = NOW + STEP
            stale_pair[1]["source_fetched_at"] = {
                "binance": (NOW + STEP) // 1000,
                "kraken": (NOW + STEP) // 1000,
            }
            old, old_receipt = save_pair(root, "stale", stale_pair)
            new, new_receipt = save_pair(root, "later", capture_fixture(2))
            with self.assertRaisesRegex(
                    PaperEvaluationError, "new_closed_bar_not_after_earlier_capture"):
                compare.compare_capture_files(old, old_receipt, new, new_receipt)
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(compare.main([
                    "--earlier", str(old), "--earlier-receipt", str(old_receipt),
                    "--later", str(new), "--later-receipt", str(new_receipt),
                ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())

    def test_partial_bar_not_counted_as_fully_post_capture(self):
        # The next 15m bar began before the old receipt was taken, so
        # its close alone cannot establish one entire prospective bar.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            earlier_pair = capture_fixture()
            earlier_pair[1]["captured_at_ms"] = NOW + 1
            old, proof_old = save_pair(root, "old", earlier_pair)
            partial, partial_receipt = save_pair(root, "partial", capture_fixture(1))
            with self.assertRaisesRegex(
                    PaperEvaluationError, "no_full_post_capture_closed_candle"):
                compare.compare_capture_files(old, proof_old, partial, partial_receipt)
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(compare.main([
                    "--earlier", str(old), "--earlier-receipt", str(proof_old),
                    "--later", str(partial), "--later-receipt", str(partial_receipt),
                ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())

            later, proof_later = save_pair(root, "later", capture_fixture(2))
            report = compare.compare_capture_files(old, proof_old, later, proof_later)
            self.assertEqual(report["newer_closed_bars"], 2)
            self.assertEqual(report["partial_at_capture_closed_bars"], 1)
            self.assertEqual(report["fully_post_capture_closed_bars"], 1)
            self.assertEqual(report["first_fully_post_capture_open_at_ms"], NOW + STEP)

    def test_tampered_receipt_or_data_fails_without_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(1))
            command = ["--earlier", str(old), "--earlier-receipt", str(proof_old),
                       "--later", str(new), "--later-receipt", str(proof_new)]
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(compare.main(command), 0)
            self.assertEqual(json.loads(stdout.getvalue())["newer_closed_bars"], 1)
            data = json.loads(new.read_text(encoding="utf-8"))
            data["candles"][80][5] += 1
            new.write_text(json.dumps(data), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(compare.main(command), 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("WAIT:", stderr.getvalue())
            self.assertNotIn("BTCUSDT", stderr.getvalue())


    def test_optional_prospective_replay_scores_only_fully_new_bars(self):
        # The first extra bar opened one millisecond before the old receipt.
        # It can warm the replay but cannot be a scored entry interval.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            earlier = capture_fixture()
            earlier[1]["captured_at_ms"] = NOW + 1
            old, proof_old = save_pair(root, "old", earlier)
            later, proof_later = save_pair(root, "later", capture_fixture(2))
            ordinary = compare.compare_capture_files(old, proof_old, later, proof_later)
            self.assertNotIn("prospective_paper_replay", ordinary)
            result = compare.compare_capture_files(
                old, proof_old, later, proof_later,
                prospective_strategy="trend_pullback")
            replay = result["prospective_paper_replay"]
            self.assertEqual(replay["first_scored_entry_at_ms"], NOW + STEP)
            self.assertEqual(replay["scored_closed_bars"], 1)
            self.assertEqual(replay["prior_closed_warmup_bars"], 64)
            self.assertEqual(replay["strategy_resolved_trade_count"], 0)
            self.assertEqual(replay["terminal_forced_mark_count"], 0)
            self.assertEqual(replay["simulation"]["trade_count"], 0)
            self.assertEqual(replay["simulation"]["net_pnl"], 0)
            self.assertIsNone(replay["win_probability"])
            stress = replay["double_cost_same_series_sensitivity"]
            self.assertEqual(stress["fee_bps"], 20)
            self.assertEqual(stress["slippage_bps"], 10)
            self.assertEqual(stress["baseline_trade_count"], 0)
            self.assertEqual(stress["double_cost_trade_count"], 0)
            self.assertEqual(stress["double_cost_net_pnl_usdt"], 0)
            self.assertEqual(stress["double_cost_minus_baseline_net_pnl_usdt"], 0)
            self.assertFalse(stress["independent_evaluation"])
            self.assertFalse(stress["profitability_verified"])
            self.assertFalse(replay["forward_paper_fills_verified"])
            self.assertFalse(replay["independent_venue_authenticated"])
            self.assertFalse(replay["profitability_verified"])
            self.assertTrue(all(t["entry_time"] >= NOW + STEP
                                for t in replay["simulation"]["trades"]))
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(compare.main([
                    "--earlier", str(old), "--earlier-receipt", str(proof_old),
                    "--later", str(later), "--later-receipt", str(proof_later),
                    "--prospective-replay", "breakout_retest",
                ]), 0)
            cli = json.loads(output.getvalue())["prospective_paper_replay"]
            self.assertEqual(cli["strategy"], "breakout_retest")
            self.assertEqual(cli["first_scored_entry_at_ms"], NOW + STEP)
            self.assertEqual(errors.getvalue(), "")

    def test_prospective_replay_refuses_invalid_or_partial_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            earlier = capture_fixture()
            earlier[1]["captured_at_ms"] = NOW + 1
            old, proof_old = save_pair(root, "old", earlier)
            partial, proof_partial = save_pair(root, "partial", capture_fixture(1))
            with self.assertRaisesRegex(PaperEvaluationError,
                                        "no_full_post_capture_closed_candle"):
                compare.compare_capture_files(
                    old, proof_old, partial, proof_partial,
                    prospective_strategy="trend_pullback")
            with self.assertRaisesRegex(PaperEvaluationError,
                                        "unsupported_prospective_strategy"):
                compare.compare_capture_files(
                    old, proof_old, partial, proof_partial,
                    prospective_strategy="unbounded_scalp")
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(compare.main([
                    "--earlier", str(old), "--earlier-receipt", str(proof_old),
                    "--later", str(partial), "--later-receipt", str(proof_partial),
                    "--prospective-replay", "trend_pullback",
                ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())


    def test_prospective_double_cost_retains_losses_forced_marks_and_unmatched_entries(self):
        # Deterministic mocked engine outputs test the reporting/partition
        # contract, NOT a claim of actual modeled or market performance.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, old_receipt = save_pair(root, "old", capture_fixture())
            new, new_receipt = save_pair(root, "new", capture_fixture(2))
            baseline = {
                "net_pnl": -2.5, "max_drawdown_pct": 1.0,
                "trades": [{"entry_time": NOW, "exit_time": NOW + STEP - 1,
                            "net_pnl": -2.5, "terminal_forced_mark": False}],
                "input_candles": ["not_exported"],
            }
            stressed = {
                "net_pnl": -7.0, "max_drawdown_pct": 2.5,
                "trades": [{"entry_time": NOW + STEP, "exit_time": NOW + 2 * STEP - 1,
                            "net_pnl": -7.0, "terminal_forced_mark": True}],
                "input_candles": ["not_exported"],
            }
            with patch.object(compare, "backtest", side_effect=[baseline, stressed]) as run:
                report = compare.compare_capture_files(
                    old, old_receipt, new, new_receipt,
                    prospective_strategy="trend_pullback")
            self.assertEqual(run.call_count, 2)
            self.assertEqual(run.call_args_list[0].kwargs["entry_not_before"], NOW)
            self.assertEqual(run.call_args_list[1].kwargs["entry_not_before"], NOW)
            stress = report["prospective_paper_replay"]["double_cost_same_series_sensitivity"]
            self.assertEqual(stress["baseline_net_pnl_usdt"], -2.5)
            self.assertEqual(stress["double_cost_net_pnl_usdt"], -7.0)
            self.assertEqual(stress["double_cost_minus_baseline_net_pnl_usdt"], -4.5)
            self.assertEqual(stress["shared_entry_count"], 0)
            self.assertEqual(stress["baseline_only_entry_count"], 1)
            self.assertEqual(stress["double_cost_only_entry_count"], 1)
            self.assertEqual(stress["double_cost_terminal_forced_mark_count"], 1)
            self.assertEqual(stress["double_cost_strategy_resolved_trade_count"], 0)
            self.assertEqual(stress["double_cost_max_drawdown_pct"], 2.5)
            self.assertEqual(stress["simulation"]["trades"][0]["net_pnl"], -7.0)
            self.assertNotIn("input_candles", stress["simulation"])
            self.assertFalse(stress["profitability_verified"])

    def test_prospective_double_cost_refuses_noncausal_stress_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, old_receipt = save_pair(root, "old", capture_fixture())
            new, new_receipt = save_pair(root, "new", capture_fixture(2))
            baseline = {"net_pnl": 0.0, "max_drawdown_pct": 0.0, "trades": []}
            noncausal = {
                "net_pnl": 100.0, "max_drawdown_pct": 0.0,
                "trades": [{"entry_time": NOW - STEP, "exit_time": NOW + STEP - 1,
                            "net_pnl": 100.0, "terminal_forced_mark": False}],
            }
            with patch.object(compare, "backtest", side_effect=[baseline, noncausal]):
                with self.assertRaisesRegex(
                        PaperEvaluationError, "noncausal_prospective_replay"):
                    compare.compare_capture_files(
                        old, old_receipt, new, new_receipt,
                        prospective_strategy="trend_pullback")
            output, errors = io.StringIO(), io.StringIO()
            with patch.object(compare, "backtest", side_effect=[baseline, noncausal]):
                with redirect_stdout(output), redirect_stderr(errors):
                    self.assertEqual(compare.main([
                        "--earlier", str(old), "--earlier-receipt", str(old_receipt),
                        "--later", str(new), "--later-receipt", str(new_receipt),
                        "--prospective-replay", "trend_pullback",
                    ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())

    def test_replay_rejects_future_overlap_and_false_terminal_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(2))
            empty = {"net_pnl": 0.0, "trades": [], "trade_count": 0}
            cases = [
                [{"entry_time": NOW, "exit_time": NOW + 3*STEP - 1,
                  "net_pnl": -1.0, "terminal_forced_mark": False}],
                [{"entry_time": NOW, "exit_time": NOW + 2*STEP - 1,
                  "net_pnl": -1.0, "terminal_forced_mark": False},
                 {"entry_time": NOW + STEP, "exit_time": NOW + 2*STEP - 1,
                  "net_pnl": -2.0, "terminal_forced_mark": False}],
                [{"entry_time": NOW, "exit_time": NOW + STEP - 1,
                  "net_pnl": -1.0, "terminal_forced_mark": True}],
            ]
            for trades in cases:
                with self.subTest(trades=trades):
                    bad = {"net_pnl": sum(x["net_pnl"] for x in trades),
                           "trades": trades, "trade_count": len(trades)}
                    with patch.object(compare, "backtest", side_effect=[bad, empty]):
                        with self.assertRaisesRegex(
                                PaperEvaluationError, "noncausal_prospective_replay"):
                            compare.compare_capture_files(
                                old, proof_old, new, proof_new,
                                prospective_strategy="trend_pullback")

    def test_replay_rejects_missing_or_unreconciled_paper_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(2))
            empty = {"net_pnl": 0.0, "trades": [], "trade_count": 0}
            cases = [
                ({"net_pnl": 5.0, "trades": [], "trade_count": 0},
                 "unreconciled_prospective_paper_ledger"),
                ({"net_pnl": 0.0, "trades": [{
                    "entry_time": NOW, "net_pnl": 0.0,
                    "terminal_forced_mark": False}]},
                 "invalid_prospective_paper_ledger"),
                ({"net_pnl": 0.0, "trades": [], "trade_count": 1},
                 "unreconciled_prospective_paper_ledger"),
            ]
            for bad, reason in cases:
                with self.subTest(reason=reason):
                    with patch.object(compare, "backtest", side_effect=[bad, empty]):
                        with self.assertRaisesRegex(PaperEvaluationError, reason):
                            compare.compare_capture_files(
                                old, proof_old, new, proof_new,
                                prospective_strategy="trend_pullback")
            output, errors = io.StringIO(), io.StringIO()
            with patch.object(compare, "backtest", side_effect=[
                    {"net_pnl": 1.0, "trades": []}, empty]):
                with redirect_stdout(output), redirect_stderr(errors):
                    self.assertEqual(compare.main([
                        "--earlier", str(old), "--earlier-receipt", str(proof_old),
                        "--later", str(new), "--later-receipt", str(proof_new),
                        "--prospective-replay", "trend_pullback",
                    ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())


    def test_replay_rejects_inconsistent_cash_drawdown_and_outcome_breakdown(self):
        # These are synthetic engine stubs, NOT real forward performance.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(2))
            diagnostics = {
                "terminal_forced_close_count": 0,
                "strategy_resolved_trade_count": 0,
                "terminal_forced_close_net_pnl_usdt": 0.0,
                "strategy_resolved_net_pnl_usdt": 0.0,
                "close_mark_max_drawdown_pct": 0.0,
                "close_mark_peak_equity_usdt": 1000.0,
                "close_mark_low_equity_usdt": 1000.0,
            }
            valid = {
                "net_pnl": 0.0, "trades": [], "trade_count": 0,
                "initial_equity": 1000.0, "ending_equity": 1000.0,
                "max_drawdown_pct": 0.0,
                "execution_diagnostics": diagnostics,
            }
            with patch.object(compare, "backtest", side_effect=[valid, valid]):
                report = compare.compare_capture_files(
                    old, proof_old, new, proof_new,
                    prospective_strategy="trend_pullback")
            self.assertEqual(report["prospective_paper_replay"]["simulation"]["ending_equity"], 1000)
            bad_cases = [
                ({"ending_equity": 1005.0},
                 "unreconciled_prospective_paper_ledger"),
                ({"initial_equity": 900.0, "ending_equity": 900.0},
                 "unreconciled_prospective_paper_ledger"),
                ({"ending_equity": None},
                 "invalid_prospective_paper_ledger"),
                ({"max_drawdown_pct": float("nan")},
                 "invalid_prospective_paper_ledger"),
                ({"max_drawdown_pct": -0.1},
                 "invalid_prospective_paper_ledger"),
                ({"execution_diagnostics": dict(
                    diagnostics, terminal_forced_close_count=1)},
                 "unreconciled_prospective_paper_ledger"),
                ({"execution_diagnostics": dict(
                    diagnostics, close_mark_peak_equity_usdt=900.0)},
                 "unreconciled_prospective_paper_ledger"),
            ]
            for changes, reason in bad_cases:
                for side in (0, 1):
                    with self.subTest(changes=changes, side=side):
                        bad = dict(valid, **changes)
                        simulated = [bad, valid] if side == 0 else [valid, bad]
                        with patch.object(compare, "backtest", side_effect=simulated):
                            with self.assertRaisesRegex(PaperEvaluationError, reason):
                                compare.compare_capture_files(
                                    old, proof_old, new, proof_new,
                                    prospective_strategy="trend_pullback")


    def test_replay_refuses_wrong_strategy_cost_window_or_partial_metadata(self):
        # Synthetic engine outputs only. Both baseline and doubled-cost
        # metadata must describe the actual requested segment and config.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(2))
            cfg = compare.SimulationConfig()
            stress_cfg = compare.SimulationConfig(
                equity=cfg.equity, risk_pct=cfg.risk_pct,
                daily_loss_limit=cfg.daily_loss_limit,
                fee_bps=cfg.fee_bps * 2, slippage_bps=cfg.slippage_bps * 2)
            from dataclasses import asdict
            def stub(config):
                return {
                    "mode": "historical-paper-simulation",
                    "orders_enabled": False,
                    "rule_version": compare.RULE_VERSION,
                    "strategy": "trend_pullback", "interval": "15m",
                    "start_at": NOW - 64 * STEP,
                    "end_at": NOW + 2 * STEP - 1,
                    "bars": 66, "config": asdict(config),
                    "initial_equity": 1000.0, "ending_equity": 1000.0,
                    "net_pnl": 0.0, "trades": [], "trade_count": 0,
                    "max_drawdown_pct": 0.0,
                }
            valid = [stub(cfg), stub(stress_cfg)]
            with patch.object(compare, "backtest", side_effect=valid):
                result = compare.compare_capture_files(
                    old, proof_old, new, proof_new,
                    prospective_strategy="trend_pullback")
            replay = result["prospective_paper_replay"]
            self.assertTrue(replay["modeled_strategy_cost_window_metadata_reconciled"])
            self.assertTrue(replay["double_cost_same_series_sensitivity"][
                "modeled_strategy_cost_window_metadata_reconciled"])
            bad_cases = [
                {"strategy": "breakout_retest"},
                {"orders_enabled": True},
                {"start_at": NOW - 62 * STEP},
                {"end_at": NOW + 3 * STEP - 1},
                {"bars": 65},
                {"config": dict(asdict(cfg), fee_bps=99)},
                {"config": dict(asdict(cfg), risk_pct=True)},
                {"mode": "live-order-simulation"},
                {"rule_version": "unknown"},
            ]
            for change in bad_cases:
                for side in (0, 1):
                    with self.subTest(change=change, side=side):
                        corrupted = [dict(valid[0]), dict(valid[1])]
                        update = dict(change)
                        if "config" in update and side == 1:
                            update["config"] = dict(
                                asdict(stress_cfg), **{
                                    k: v for k, v in update["config"].items()
                                    if k in ("fee_bps", "risk_pct")})
                        corrupted[side].update(update)
                        with patch.object(compare, "backtest", side_effect=corrupted):
                            with self.assertRaisesRegex(
                                    PaperEvaluationError,
                                    "unreconciled_prospective_replay_metadata"):
                                compare.compare_capture_files(
                                    old, proof_old, new, proof_new,
                                    prospective_strategy="trend_pullback")
            partial = {"mode": "historical-paper-simulation",
                       "net_pnl": 0.0, "trades": []}
            with patch.object(compare, "backtest", side_effect=[partial, valid[1]]):
                output, errors = io.StringIO(), io.StringIO()
                with redirect_stdout(output), redirect_stderr(errors):
                    self.assertEqual(compare.main([
                        "--earlier", str(old), "--earlier-receipt", str(proof_old),
                        "--later", str(new), "--later-receipt", str(proof_new),
                        "--prospective-replay", "trend_pullback",
                    ]), 2)
                self.assertEqual(output.getvalue(), "")
                self.assertIn("WAIT:", errors.getvalue())


    def test_replay_reconciles_per_trade_costs_and_rejects_tampering(self):
        # Synthetic paper trades only; this is not exchange fill evidence.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(2))
            cfg = compare.SimulationConfig()
            stress = compare.SimulationConfig(
                equity=cfg.equity, risk_pct=cfg.risk_pct,
                daily_loss_limit=cfg.daily_loss_limit,
                fee_bps=cfg.fee_bps * 2, slippage_bps=cfg.slippage_bps * 2)

            def modeled(config):
                qty, raw_entry, raw_exit = 2.0, 100.0, 102.0
                entry = raw_entry * (1 + config.slippage_bps / 10_000)
                exit_price = raw_exit * (1 - config.slippage_bps / 10_000)
                fees = qty * config.fee_bps / 10_000 * (entry + exit_price)
                buy = qty * (entry - raw_entry)
                sell = qty * (raw_exit - exit_price)
                gross = qty * (raw_exit - raw_entry)
                pnl = gross - buy - sell - fees
                trade = {
                    "entry_time": NOW, "exit_time": NOW + STEP - 1,
                    "terminal_forced_mark": False, "net_pnl": pnl,
                    "entry_reference_open": raw_entry,
                    "exit_reference_price": raw_exit, "entry": entry,
                    "exit": exit_price, "quantity": qty, "fees": fees,
                    "modeled_buy_slippage_cost_usdt": buy,
                    "modeled_sell_slippage_cost_usdt": sell,
                    "reference_gross_pnl_before_modeled_costs_usdt": gross,
                }
                return {"net_pnl": pnl, "trade_count": 1, "trades": [trade],
                        "max_drawdown_pct": 0.0}

            valid = [modeled(cfg), modeled(stress)]
            with patch.object(compare, "backtest", side_effect=valid):
                result = compare.compare_capture_files(
                    old, proof_old, new, proof_new,
                    prospective_strategy="trend_pullback")
            replay = result["prospective_paper_replay"]
            self.assertTrue(replay["modeled_execution_costs_reconciled"])
            self.assertTrue(replay["double_cost_same_series_sensitivity"][
                "modeled_execution_costs_reconciled"])
            self.assertIsNone(compare._verified_execution_costs(
                {"trades": []}, cfg))
            legacy = {"trades": [{"entry_time": NOW, "exit_time": NOW + STEP - 1,
                                  "terminal_forced_mark": False, "net_pnl": -1.0}]}
            self.assertFalse(compare._verified_execution_costs(legacy, cfg))
            for side in (0, 1):
                for key in ("entry", "exit", "quantity", "fees",
                            "modeled_buy_slippage_cost_usdt",
                            "modeled_sell_slippage_cost_usdt",
                            "reference_gross_pnl_before_modeled_costs_usdt"):
                    with self.subTest(side=side, key=key):
                        bad = [dict(valid[0]), dict(valid[1])]
                        bad[side]["trades"] = [dict(bad[side]["trades"][0])]
                        bad[side]["trades"][0][key] += 0.5
                        with patch.object(compare, "backtest", side_effect=bad):
                            with self.assertRaisesRegex(
                                    PaperEvaluationError,
                                    "unreconciled_prospective_execution_costs"):
                                compare.compare_capture_files(
                                    old, proof_old, new, proof_new,
                                    prospective_strategy="trend_pullback")
            partial = [dict(valid[0]), dict(valid[1])]
            partial[1]["trades"] = [dict(partial[1]["trades"][0])]
            del partial[1]["trades"][0]["fees"]
            with patch.object(compare, "backtest", side_effect=partial):
                output, errors = io.StringIO(), io.StringIO()
                with redirect_stdout(output), redirect_stderr(errors):
                    self.assertEqual(compare.main([
                        "--earlier", str(old), "--earlier-receipt", str(proof_old),
                        "--later", str(new), "--later-receipt", str(proof_new),
                        "--prospective-replay", "trend_pullback",
                    ]), 2)
                self.assertEqual(output.getvalue(), "")
                self.assertIn("WAIT:", errors.getvalue())


    def test_zero_trade_aggregate_costs_must_reconcile_on_both_replays(self):
        # Zero trades are a valid outcome, not a license for hidden costs.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, old_receipt = save_pair(root, "old", capture_fixture())
            new, new_receipt = save_pair(root, "new", capture_fixture(2))
            cost_keys = (
                "modeled_buy_slippage_cost_usdt",
                "modeled_sell_slippage_cost_usdt",
                "modeled_total_slippage_cost_usdt",
                "modeled_fees_plus_slippage_cost_usdt",
            )
            valid = {
                "net_pnl": 0.0, "trades": [], "trade_count": 0,
                "initial_equity": 1000.0, "ending_equity": 1000.0,
                "max_drawdown_pct": 0.0, "fees_paid": 0.0,
                "execution_diagnostics": {
                    **{key: 0.0 for key in cost_keys},
                    "terminal_forced_close_count": 0,
                    "strategy_resolved_trade_count": 0,
                    "terminal_forced_close_net_pnl_usdt": 0.0,
                    "strategy_resolved_net_pnl_usdt": 0.0,
                    "close_mark_max_drawdown_pct": 0.0,
                    "close_mark_peak_equity_usdt": 1000.0,
                    "close_mark_low_equity_usdt": 1000.0,
                },
            }
            with patch.object(compare, "backtest", side_effect=[valid, valid]):
                report = compare.compare_capture_files(
                    old, old_receipt, new, new_receipt,
                    prospective_strategy="trend_pullback")
            self.assertIsNone(report["prospective_paper_replay"][
                "modeled_execution_costs_reconciled"])
            for change in ("fees", "buy", "sell", "partial", "nonfinite"):
                for side in (0, 1):
                    with self.subTest(change=change, side=side):
                        bad = dict(valid)
                        bad["execution_diagnostics"] = dict(valid["execution_diagnostics"])
                        if change == "fees":
                            bad["fees_paid"] = 0.5
                        elif change == "partial":
                            del bad["execution_diagnostics"][cost_keys[0]]
                        elif change == "nonfinite":
                            bad["execution_diagnostics"][cost_keys[2]] = float("nan")
                        else:
                            key = cost_keys[0 if change == "buy" else 1]
                            bad["execution_diagnostics"][key] = 0.5
                        cases = [bad, valid] if side == 0 else [valid, bad]
                        with patch.object(compare, "backtest", side_effect=cases):
                            with self.assertRaisesRegex(
                                    PaperEvaluationError,
                                    "unreconciled_prospective_execution_costs"):
                                compare.compare_capture_files(
                                    old, old_receipt, new, new_receipt,
                                    prospective_strategy="trend_pullback")
            bad = dict(valid, fees_paid=1.0)
            output, errors = io.StringIO(), io.StringIO()
            with patch.object(compare, "backtest", side_effect=[valid, bad]):
                with redirect_stdout(output), redirect_stderr(errors):
                    self.assertEqual(compare.main([
                        "--earlier", str(old), "--earlier-receipt", str(old_receipt),
                        "--later", str(new), "--later-receipt", str(new_receipt),
                        "--prospective-replay", "trend_pullback",
                    ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())

    def test_nonempty_cost_aggregate_claim_requires_trade_evidence(self):
        cfg = compare.SimulationConfig()
        legacy = {"trades": [{"entry_time": NOW,
                              "exit_time": NOW + STEP - 1,
                              "terminal_forced_mark": False, "net_pnl": -1.0}]}
        self.assertFalse(compare._verified_execution_costs(legacy, cfg))
        for claimed in (
            dict(legacy, fees_paid=0.0),
            dict(legacy, execution_diagnostics={
                "modeled_buy_slippage_cost_usdt": 0.0}),
        ):
            with self.assertRaisesRegex(
                    PaperEvaluationError,
                    "unreconciled_prospective_execution_costs"):
                compare._verified_execution_costs(claimed, cfg)


    def test_exit_reason_timestamp_and_ambiguity_audit_on_both_replays(self):
        # Only modeled paper-engine metadata; not exchange-attested fills.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, old_receipt = save_pair(root, "old", capture_fixture())
            new, new_receipt = save_pair(root, "new", capture_fixture(2))
            def trade(reason="stop", **overrides):
                item = {
                    "entry_time": NOW, "exit_time": NOW + STEP - 1,
                    "net_pnl": -1.0, "terminal_forced_mark": False,
                    "reason": reason,
                    "exit_time_precision": "bar_close_upper_bound_intrabar_unknown",
                    "stop_target_same_bar": True,
                    "gap_beyond_stop_pct": None,
                }
                item.update(overrides)
                return item
            valid = {"net_pnl": -1.0, "trade_count": 1,
                     "max_drawdown_pct": 1.0, "trades": [trade()]}
            self.assertTrue(compare._verified_exit_semantics(valid, NOW + 2*STEP - 1))
            self.assertIsNone(compare._verified_exit_semantics(
                {"trades": []}, NOW + 2*STEP - 1))
            self.assertFalse(compare._verified_exit_semantics(
                {"trades": [{"entry_time": NOW, "exit_time": NOW + STEP - 1,
                             "net_pnl": -1.0, "terminal_forced_mark": False}]},
                NOW + 2*STEP - 1))
            valid_gap = trade(
                "gap_stop", exit_time=NOW + STEP,
                exit_time_precision="bar_open_exact",
                stop_target_same_bar=False, gap_beyond_stop_pct=0.2)
            self.assertTrue(compare._verified_exit_semantics(
                {"trades": [valid_gap]}, NOW + 2*STEP - 1))
            valid_terminal = trade(
                "end_of_sample", exit_time=NOW + 2*STEP - 1,
                exit_time_precision="bar_close_exact",
                terminal_forced_mark=True, stop_target_same_bar=False)
            self.assertTrue(compare._verified_exit_semantics(
                {"trades": [valid_terminal]}, NOW + 2*STEP - 1))
            with patch.object(compare, "backtest", side_effect=[valid, valid]):
                report = compare.compare_capture_files(
                    old, old_receipt, new, new_receipt,
                    prospective_strategy="trend_pullback")
            replay = report["prospective_paper_replay"]
            self.assertTrue(replay["modeled_exit_reason_and_timing_reconciled"])
            self.assertTrue(replay["double_cost_same_series_sensitivity"][
                "modeled_exit_reason_and_timing_reconciled"])
            cases = [
                {"reason": "end_of_sample"},
                {"reason": "unknown_exit"},
                {"exit_time_precision": "bar_open_exact"},
                {"exit_time": NOW + STEP},
                {"stop_target_same_bar": "yes"},
                {"gap_beyond_stop_pct": 0.1},
                {"terminal_forced_mark": True},
                {"reason": "gap_stop", "exit_time": NOW + STEP,
                 "exit_time_precision": "bar_open_exact",
                 "stop_target_same_bar": False, "gap_beyond_stop_pct": None},
            ]
            for changes in cases:
                for side in (0, 1):
                    with self.subTest(changes=changes, side=side):
                        corrupted = dict(valid)
                        corrupted["trades"] = [trade(**changes)]
                        simulations = ([corrupted, valid] if side == 0
                                       else [valid, corrupted])
                        # The earlier causal ledger rightly rejects an
                        # early forced mark before the exit-label audit runs.
                        expected_error = (
                            "noncausal_prospective_replay"
                            if changes == {"terminal_forced_mark": True}
                            else "unreconciled_prospective_exit_semantics")
                        with patch.object(compare, "backtest", side_effect=simulations):
                            with self.assertRaisesRegex(
                                    PaperEvaluationError, expected_error):
                                compare.compare_capture_files(
                                    old, old_receipt, new, new_receipt,
                                    prospective_strategy="trend_pullback")
            partial = dict(valid)
            partial["trades"] = [trade()]
            del partial["trades"][0]["exit_time_precision"]
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(compare, "backtest", side_effect=[valid, partial]):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(compare.main([
                        "--earlier", str(old), "--earlier-receipt", str(old_receipt),
                        "--later", str(new), "--later-receipt", str(new_receipt),
                        "--prospective-replay", "trend_pullback",
                    ]), 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("WAIT:", stderr.getvalue())


    def test_modeled_trade_prices_must_match_local_closed_candle_path(self):
        # Synthetic OHLC only. A consistent PnL ledger is insufficient if
        # a modeled entry, stop, target or exit price was invented.
        from types import SimpleNamespace
        def bar(t, o, h, l, c):
            return SimpleNamespace(time=t, close_time=t + STEP - 1,
                                   open=o, high=h, low=l, close=c)
        bars = [
            bar(NOW, 100, 102, 98, 100),
            bar(NOW + STEP, 100, 100.5, 99.5, 100),
            bar(NOW + 2 * STEP, 103, 104, 102, 103),
        ]
        stop = {
            "entry_time": NOW, "exit_time": NOW + STEP - 1,
            "entry_reference_open": 100.0, "exit_reference_price": 99.0,
            "reference_stop": 99.0, "reference_target": 101.0,
            "reason": "stop", "stop_target_same_bar": True,
            "gap_beyond_stop_pct": None,
        }
        self.assertTrue(compare._verified_candle_price_anchors(
            {"trades": [stop]}, bars))
        self.assertIsNone(compare._verified_candle_price_anchors(
            {"trades": []}, bars))
        legacy = dict(stop)
        del legacy["reference_stop"], legacy["reference_target"]
        self.assertFalse(compare._verified_candle_price_anchors(
            {"trades": [legacy]}, bars))
        # A favorable target gap is capped at the target, not the open.
        gap_target = {
            "entry_time": NOW + STEP, "exit_time": NOW + 2 * STEP,
            "entry_reference_open": 100.0, "exit_reference_price": 102.0,
            "reference_stop": 99.0, "reference_target": 102.0,
            "reason": "target_gap_open", "stop_target_same_bar": False,
            "gap_beyond_stop_pct": None,
        }
        self.assertTrue(compare._verified_candle_price_anchors(
            {"trades": [gap_target]}, bars))
        cases = (
            (stop, {"entry_reference_open": 100.25}),
            (stop, {"exit_reference_price": 100.0}),
            (stop, {"reason": "target"}),
            (stop, {"stop_target_same_bar": False}),
            (stop, {"reference_stop": 97.0}),
            (stop, {"reference_target": 103.0}),
            (stop, {"exit_time": NOW + 2 * STEP - 1}),
            (gap_target, {"exit_reference_price": 103.0}),
            (gap_target, {"reference_stop": 101.0}),
            (stop, {"reference_target": None}),
        )
        for original, change in cases:
            with self.subTest(change=change):
                corrupted = dict(original, **change)
                with self.assertRaisesRegex(
                        PaperEvaluationError,
                        "unreconciled_prospective_candle_prices"):
                    compare._verified_candle_price_anchors(
                        {"trades": [corrupted]}, bars)
        partial = dict(stop)
        del partial["reference_target"]
        with self.assertRaisesRegex(
                PaperEvaluationError, "unreconciled_prospective_candle_prices"):
            compare._verified_candle_price_anchors({"trades": [partial]}, bars)

    def test_candle_price_anchor_audit_on_both_prospective_replays(self):
        # Synthetic capture, synthetic modeled trades; no exchange fills.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, old_receipt = save_pair(root, "old", capture_fixture())
            new, new_receipt = save_pair(root, "new", capture_fixture(2))
            # Complete modeled execution fields are mandatory when a trade
            # claims entry/exit reference prices; use each side's actual
            # baseline/doubled fee and slippage configuration.
            cfg = compare.SimulationConfig()
            stress_cfg = compare.SimulationConfig(
                equity=cfg.equity, risk_pct=cfg.risk_pct,
                daily_loss_limit=cfg.daily_loss_limit,
                fee_bps=cfg.fee_bps * 2, slippage_bps=cfg.slippage_bps * 2)
            def modeled(config):
                qty, raw_entry, raw_exit = 1.0, 100.0, 99.0
                entry = raw_entry * (1 + config.slippage_bps / 10_000)
                exit_price = raw_exit * (1 - config.slippage_bps / 10_000)
                fees = qty * config.fee_bps / 10_000 * (entry + exit_price)
                buy = qty * (entry - raw_entry)
                sell = qty * (raw_exit - exit_price)
                gross = qty * (raw_exit - raw_entry)
                pnl = gross - buy - sell - fees
                trade = {
                    "entry_time": NOW, "exit_time": NOW + STEP - 1,
                    "net_pnl": pnl, "terminal_forced_mark": False,
                    "entry_reference_open": raw_entry,
                    "exit_reference_price": raw_exit,
                    "reference_stop": 99.0, "reference_target": 101.0,
                    "reason": "stop", "exit_time_precision":
                        "bar_close_upper_bound_intrabar_unknown",
                    "stop_target_same_bar": True, "gap_beyond_stop_pct": None,
                    "entry": entry, "exit": exit_price, "quantity": qty,
                    "fees": fees, "modeled_buy_slippage_cost_usdt": buy,
                    "modeled_sell_slippage_cost_usdt": sell,
                    "reference_gross_pnl_before_modeled_costs_usdt": gross,
                }
                return {"net_pnl": pnl, "trade_count": 1,
                        "max_drawdown_pct": 1.0, "trades": [trade]}
            valid = [modeled(cfg), modeled(stress_cfg)]
            with patch.object(compare, "backtest", side_effect=valid):
                report = compare.compare_capture_files(
                    old, old_receipt, new, new_receipt,
                    prospective_strategy="trend_pullback")
            replay = report["prospective_paper_replay"]
            self.assertTrue(replay["modeled_candle_price_anchors_reconciled"])
            self.assertTrue(replay["double_cost_same_series_sensitivity"][
                "modeled_candle_price_anchors_reconciled"])
            for side in (0, 1):
                # Raw-price mutations are checked directly above; at CLI
                # level those are correctly caught first by the existing
                # fee/slippage audit. Change only reference stop/target here
                # so this new candle-path guard is the first rejecting check.
                for field, value in (("reference_stop", 97.0),
                                     ("reference_target", 103.0)):
                    with self.subTest(side=side, field=field):
                        corrupted = dict(valid[side])
                        corrupted["trades"] = [dict(
                            valid[side]["trades"][0], **{field: value})]
                        pair = ([corrupted, valid[1]] if side == 0
                                else [valid[0], corrupted])
                        with patch.object(compare, "backtest", side_effect=pair):
                            with self.assertRaisesRegex(
                                    PaperEvaluationError,
                                    "unreconciled_prospective_candle_prices"):
                                compare.compare_capture_files(
                                    old, old_receipt, new, new_receipt,
                                    prospective_strategy="trend_pullback")


if __name__ == "__main__":
    unittest.main()
