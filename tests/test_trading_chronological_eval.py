"""Causal 15m chronological paper replay; no fabricated live market results."""
from dataclasses import replace
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cloud_backend import paper_evaluation as ev
from cloud_backend.trading_research import Candle, SimulationConfig
from test_paper_risk import history


class ChronologicalEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.bars = history("15m", count=300)

    def test_fixed_holdout_is_causal_and_exportable(self):
        result = ev.evaluate_chronological(self.bars, "BTCUSDT", "trend_pullback")
        self.assertEqual(result["split"]["training_bars"], 210)
        self.assertEqual(result["split"]["holdout_scored_bars"], 90)
        self.assertEqual(result["split"]["holdout_prior_warmup_bars"], 64)
        self.assertEqual(result["split"]["holdout_first_entry_earliest_at"], self.bars[210].time)
        self.assertEqual(len(result["input_candle_sha256"]), 64)
        self.assertFalse(result["orders_enabled"])
        self.assertFalse(result["independent_venue_verified"])
        self.assertIsNone(result["win_probability"])
        self.assertEqual(result["input_provenance"], "operator_supplied_unverified")
        self.assertNotIn("input_candles", result["holdout"])
        self.assertIn("execution_diagnostics", result["holdout"])
        self.assertIn("execution_diagnostics", result["training"])
        self.assertIn("risk_budget_breach_count", result["holdout"]["execution_diagnostics"])
        self.assertIn("max_loss_to_risk_budget_multiple", result["holdout"]["execution_diagnostics"])
        self.assertTrue(all(t["entry_time"] >= self.bars[210].time
                            for t in result["holdout"]["trades"]))

    def test_paper_entry_attempts_expose_daily_cap_lockout_without_fake_orders(self):
        from cloud_backend import trading_research as tr
        flat = [replace(b, open=100, high=101, low=99, close=100, volume=10)
                for b in self.bars]
        with patch.object(tr, "setup", return_value={"stop": 99.5, "reference_entry": 100}):
            report = ev.evaluate_chronological(
                flat, "BTCUSDT", "trend_pullback",
                SimulationConfig(daily_loss_limit=.1))
        d = report["holdout"]["execution_diagnostics"]
        self.assertGreater(d["paper_entry_attempts"], 0)
        self.assertGreater(d["paper_entries_skipped_utc_daily_loss_cap"], 0)
        self.assertEqual(
            d["paper_entry_attempts"],
            d["paper_entries_opened"] + d["paper_entries_skipped_invalid_gap"]
            + d["paper_entries_skipped_utc_daily_loss_cap"]
            + d["paper_entries_skipped_insufficient_risk_capacity"])
        self.assertEqual(d["paper_entries_opened"], report["holdout"]["trade_count"])
        self.assertFalse(report["orders_enabled"])
        self.assertLess(report["holdout"]["net_pnl"], 0)

    def test_paper_entry_attempts_reject_gapped_invalid_stop_without_trade(self):
        from cloud_backend import trading_research as tr
        flat = [replace(b, open=100, high=101, low=99, close=100, volume=10)
                for b in self.bars]
        with patch.object(tr, "setup", return_value={"stop": 100.5, "reference_entry": 101}):
            report = ev.evaluate_chronological(flat, "ETHUSDT", "trend_pullback")
        d = report["holdout"]["execution_diagnostics"]
        self.assertGreater(d["paper_entries_skipped_invalid_gap"], 0)
        self.assertEqual(d["paper_entry_attempts"], d["paper_entries_skipped_invalid_gap"])
        self.assertEqual(d["paper_entries_opened"], 0)
        self.assertEqual(report["holdout"]["trade_count"], 0)
        self.assertIsNone(report["holdout"]["win_rate_pct"])

    def test_paper_entry_rejects_raw_open_at_or_below_stop_before_slippage(self):
        from cloud_backend import trading_research as tr
        # A buy-side slippage adjustment can lift a raw opening of 99.99
        # or 100.00 above the 100.00 stop. Neither is a valid new long.
        # Synthetic candles and mocked setup are not market evidence.
        for opening in (99.99, 100.0):
            with self.subTest(opening=opening):
                bars = [replace(b, open=opening, high=102, low=99,
                                close=100.5, volume=10) for b in self.bars]
                with patch.object(tr, "setup", return_value={
                        "stop": 100.0, "reference_entry": 101.0}):
                    report = ev.evaluate_chronological(
                        bars, "BTCUSDT", "trend_pullback")
                diagnostics = report["holdout"]["execution_diagnostics"]
                self.assertGreater(diagnostics["paper_entry_attempts"], 0)
                self.assertEqual(diagnostics["paper_entry_attempts"],
                                 diagnostics["paper_entries_skipped_invalid_gap"])
                self.assertEqual(diagnostics["paper_entries_opened"], 0)
                self.assertEqual(report["holdout"]["trade_count"], 0)
                self.assertEqual(report["holdout"]["net_pnl"], 0)

        # A genuine opening ABOVE the stop must still be eligible for
        # ordinary next-open paper entry and conservative intrabar stop.
        bars = [replace(b, open=100.01, high=102, low=99,
                        close=100.5, volume=10) for b in self.bars]
        with patch.object(tr, "setup", return_value={
                "stop": 100.0, "reference_entry": 101.0}):
            valid = ev.evaluate_chronological(bars, "BTCUSDT", "trend_pullback")
        self.assertGreater(
            valid["holdout"]["execution_diagnostics"]["paper_entries_opened"], 0)
        self.assertGreater(valid["holdout"]["trade_count"], 0)

    def test_terminal_forced_close_is_disclosed_separately_from_strategy_exits(self):
        from cloud_backend import trading_research as tr
        # Synthetic sample: a single signal at the penultimate close enters
        # the final bar and cannot reach either stop or target before sample end.
        flat = [replace(b, open=100, high=101, low=99, close=100.2, volume=10)
                for b in self.bars]
        signal_time = flat[-2].time
        def last_signal(bars, strategy):
            return ({"stop": 90.0, "reference_entry": 100.2}
                    if bars[-1].time == signal_time else None)
        with patch.object(tr, "setup", side_effect=last_signal):
            report = tr.backtest(flat, "trend_pullback", SimulationConfig())
        self.assertEqual(report["trade_count"], 1)
        trade = report["trades"][0]
        self.assertEqual(trade["reason"], "end_of_sample")
        self.assertTrue(trade["terminal_forced_mark"])
        self.assertEqual(trade["exit_time_precision"], "bar_close_exact")
        diagnostics = report["execution_diagnostics"]
        self.assertEqual(diagnostics["terminal_forced_close_count"], 1)
        self.assertAlmostEqual(diagnostics["terminal_forced_close_net_pnl_usdt"],
                               trade["net_pnl"])
        self.assertEqual(diagnostics["strategy_resolved_trade_count"], 0)
        self.assertAlmostEqual(diagnostics["strategy_resolved_net_pnl_usdt"], 0)
        self.assertAlmostEqual(report["net_pnl"], trade["net_pnl"])
        self.assertFalse(report["orders_enabled"])

        with patch.object(tr, "setup", return_value=None):
            empty = tr.backtest(flat, "trend_pullback", SimulationConfig())
        self.assertEqual(empty["trade_count"], 0)
        self.assertEqual(empty["execution_diagnostics"]["terminal_forced_close_count"], 0)
        self.assertEqual(empty["execution_diagnostics"]["terminal_forced_close_net_pnl_usdt"], 0)
        self.assertEqual(empty["execution_diagnostics"]["strategy_resolved_trade_count"], 0)
        self.assertEqual(empty["execution_diagnostics"]["strategy_resolved_net_pnl_usdt"], 0)

    def test_no_trade_outcome_is_preserved(self):
        flat = [replace(b, open=100, high=100.1, low=99.9, close=100, volume=10)
                for b in self.bars]
        result = ev.evaluate_chronological(flat, "ETHUSDT", "breakout_retest")
        self.assertTrue(result["holdout_no_trades"])
        self.assertEqual(result["holdout"]["trade_count"], 0)
        self.assertEqual(result["holdout"]["net_pnl"], 0)
        self.assertIsNone(result["holdout"]["win_rate_pct"])

    def test_negative_results_are_not_suppressed(self):
        def fake_backtest(bars, strategy, cfg, *, entry_not_before=None):
            return {"trade_count": 1, "net_pnl": -3.5,
                    "win_rate_pct": 0.0, "trades": [{
                        "entry_time": bars[64].time if len(bars) > 64 else bars[0].time,
                        "net_pnl": -3.5, "reason": "gap_stop"}],
                    "input_candles": ["not_exposed"]}
        with patch.object(ev, "backtest", side_effect=fake_backtest):
            result = ev.evaluate_chronological(self.bars, "BTCUSDT", "trend_pullback")
        self.assertEqual(result["holdout"]["net_pnl"], -3.5)
        self.assertEqual(result["holdout"]["trades"][0]["reason"], "gap_stop")
        self.assertFalse(result["holdout_no_trades"])

    def test_gaps_duplicates_ohlcv_and_timestamp_forgery_are_rejected(self):
        variants = [
            replace(self.bars[70], time=self.bars[70].time + 1),
            replace(self.bars[70], time=self.bars[69].time),
            replace(self.bars[70], close_time=self.bars[70].close_time + 1),
            replace(self.bars[70], volume=-1),
            replace(self.bars[70], high=0),
            replace(self.bars[70], open=math.nan),
            replace(self.bars[70], time=True),
        ]
        for corrupt in variants:
            with self.subTest(corrupt=corrupt):
                sample = self.bars.copy()
                sample[70] = corrupt
                with self.assertRaises(ev.PaperEvaluationError):
                    ev.evaluate_chronological(sample, "BTCUSDT", "trend_pullback")

    def test_invalid_settings_and_short_or_oversized_samples(self):
        for data in (self.bars[:239], self.bars + self.bars[:201]):
            with self.assertRaises(ev.PaperEvaluationError):
                ev.evaluate_chronological(data, "BTCUSDT", "trend_pullback")
        for symbol, strategy in (("SOLUSDT", "trend_pullback"), ("BTCUSDT", "buy")):
            with self.assertRaises(ev.PaperEvaluationError):
                ev.evaluate_chronological(self.bars, symbol, strategy)
        # The existing SimulationConfig constructor itself rejects bool equity.
        with self.assertRaises(ValueError):
            SimulationConfig(equity=True)
        with self.assertRaises(ev.PaperEvaluationError):
            ev.evaluate_chronological(self.bars, "BTCUSDT", "trend_pullback",
                                      config=object())

    def test_extreme_finite_and_huge_integer_candles_fail_closed(self):
        # A coherent-looking 1e308 candle is finite, but can overflow EMA,
        # ATR, drawdown and JSON output. Huge ints can overflow isfinite().
        for extreme in (1e308, 10 ** 400):
            for field in ("prices", "volume"):
                with self.subTest(extreme_type=type(extreme).__name__, field=field):
                    sample = self.bars.copy()
                    original = sample[70]
                    sample[70] = (replace(original, open=extreme, high=extreme,
                                          low=extreme, close=extreme)
                                  if field == "prices" else
                                  replace(original, volume=extreme))
                    with self.assertRaisesRegex(ev.PaperEvaluationError, "invalid_ohlcv"):
                        ev.evaluate_chronological(sample, "BTCUSDT", "trend_pullback")

    def test_simulation_config_rejects_boolean_and_huge_integer_risk_fields(self):
        for field in ("equity", "risk_pct", "daily_loss_limit",
                      "fee_bps", "slippage_bps"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                SimulationConfig(**{field: True})
        with self.assertRaises(ValueError):
            SimulationConfig(fee_bps=10 ** 400)

    def test_offline_cli_refuses_finite_overflow_without_report(self):
        rows = [[b.time, b.open, b.high, b.low, b.close, b.volume, b.close_time]
                for b in self.bars]
        rows[70][1:5] = [1e308] * 4
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "extreme.json"
            source.write_text(json.dumps({"symbol": "BTCUSDT", "interval": "15m",
                                          "candles": rows}), encoding="utf-8")
            run = subprocess.run([sys.executable, "-m", "scripts.evaluate_trading_paper",
                                  "--input", str(source)],
                                 cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, "")
            self.assertNotIn(str(source), run.stderr)

    def test_hash_changes_when_a_valid_candle_changes(self):
        original = ev.evaluate_chronological(self.bars, "BTCUSDT", "breakout_retest")
        changed = self.bars.copy()
        changed[80] = replace(changed[80], volume=changed[80].volume + 1)
        modified = ev.evaluate_chronological(changed, "BTCUSDT", "breakout_retest")
        self.assertNotEqual(original["input_candle_sha256"], modified["input_candle_sha256"])

    def test_offline_cli_real_json_contract_and_fail_closed_input(self):
        # Actual local CLI execution; synthetic fixtures are NOT real venue data.
        rows = [[b.time, b.open, b.high, b.low, b.close, b.volume, b.close_time]
                for b in self.bars]
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "candles.json"
            source.write_text(json.dumps({"symbol": "BTCUSDT", "interval": "15m",
                                          "candles": rows}), encoding="utf-8")
            run = subprocess.run([sys.executable, "-m", "scripts.evaluate_trading_paper",
                                  "--input", str(source), "--strategy", "trend_pullback",
                                  "--rolling-robustness"],
                                 cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result["split"]["holdout_scored_bars"], 90)
            self.assertFalse(result["orders_enabled"])
            self.assertEqual(len(result["rolling_robustness"]["windows"]), 3)
            self.assertEqual(result["input_provenance"], "operator_supplied_unverified")
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["candles.json"])
            rows[10][6] += 1  # forged close timestamp
            source.write_text(json.dumps({"symbol": "BTCUSDT", "interval": "15m",
                                          "candles": rows}), encoding="utf-8")
            bad = subprocess.run([sys.executable, "-m", "scripts.evaluate_trading_paper",
                                  "--input", str(source)],
                                 cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, "")
            self.assertNotIn(str(source), bad.stderr)


    def test_offline_dataset_rejects_ambiguous_duplicate_json_keys(self):
        # The receipt already rejects duplicate fields; the source candle
        # file must do the same before any simulation or provenance hashing.
        from scripts.evaluate_trading_paper import load_local
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "candles.json"
            for raw in (
                '{"symbol":"BTCUSDT","symbol":"ETHUSDT","interval":"15m","candles":[]}',
                '{"symbol":"BTCUSDT","interval":"15m","candles":[],"candles":[]}',
            ):
                with self.subTest(raw=raw):
                    source.write_text(raw, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "duplicate_json_field"):
                        load_local(source)
                    run = subprocess.run([sys.executable, "-m",
                                          "scripts.evaluate_trading_paper",
                                          "--input", str(source)],
                                         cwd=Path(__file__).resolve().parents[1],
                                         capture_output=True, text=True, timeout=30)
                    self.assertEqual(run.returncode, 2)
                    self.assertEqual(run.stdout, "")
                    self.assertNotIn(str(source), run.stderr)

    def test_rolling_robustness_disjoint_scored_windows_and_cost_stress(self):
        result = ev.evaluate_rolling_robustness(self.bars, "BTCUSDT", "trend_pullback")
        self.assertEqual(result["split"]["holdout_scored_bars"], 90)
        robust = result["rolling_robustness"]
        self.assertFalse(robust["independent_venue_verified"])
        self.assertFalse(robust["forward_verified"])
        self.assertEqual(robust["scored_windows"], 3)
        windows = robust["windows"]
        self.assertEqual([w["first_scored_entry_at"] for w in windows],
                         [self.bars[i].time for i in (120, 180, 240)])
        self.assertEqual([w["scored_bars"] for w in windows], [60, 60, 60])
        self.assertTrue(all(w["prior_warmup_bars"] == 64 for w in windows))
        for w in windows:
            self.assertEqual(w["double_costs_status"], "evaluated")
            self.assertEqual(w["double_costs"]["config"]["fee_bps"], 20)
            self.assertEqual(w["double_costs"]["config"]["slippage_bps"], 10)
            self.assertNotIn("input_candles", w["baseline"])
            self.assertIn("execution_diagnostics", w["baseline"])
            self.assertIn("risk_budget_breach_count", w["baseline"]["execution_diagnostics"])
            self.assertNotIn("input_candles", w["double_costs"])
            for scenario in (w["baseline"], w["double_costs"]):
                self.assertTrue(all(t["entry_time"] >= w["first_scored_entry_at"]
                                    for t in scenario["trades"]))

    def test_rolling_zero_trades_and_high_cost_stress_unavailable(self):
        flat = [replace(b, open=100, high=100.1, low=99.9, close=100, volume=10)
                for b in self.bars]
        result = ev.evaluate_rolling_robustness(flat, "ETHUSDT", "breakout_retest",
                                                 SimulationConfig(fee_bps=60))
        self.assertTrue(result["holdout_no_trades"])
        for window in result["rolling_robustness"]["windows"]:
            self.assertTrue(window["baseline_no_trades"])
            self.assertEqual(window["baseline"]["net_pnl"], 0)
            self.assertIsNone(window["double_costs"])
            self.assertIsNone(window["double_costs_no_trades"])
            self.assertEqual(window["double_costs_status"],
                             "unavailable_config_exceeds_engine_bounds")

    def test_rolling_negative_gap_outcomes_preserved(self):
        def losing_backtest(bars, strategy, cfg, *, entry_not_before=None):
            return {"trade_count": 1, "net_pnl": -4.25,
                    "trades": [{"entry_time": bars[64].time, "net_pnl": -4.25,
                                "reason": "gap_stop"}], "input_candles": ["hidden"]}
        with patch.object(ev, "backtest", side_effect=losing_backtest):
            result = ev.evaluate_rolling_robustness(self.bars, "BTCUSDT", "trend_pullback")
        for w in result["rolling_robustness"]["windows"]:
            for scenario in (w["baseline"], w["double_costs"]):
                self.assertEqual(scenario["net_pnl"], -4.25)
                self.assertEqual(scenario["trades"][0]["reason"], "gap_stop")
                self.assertNotIn("input_candles", scenario)

    def test_rolling_rejects_warmup_trade_from_engine(self):
        calls = [0]
        def premature_backtest(bars, strategy, cfg, *, entry_not_before=None):
            calls[0] += 1
            # First two calls are primary train/holdout; the third is a rolling
            # window, whose last warmup bar must never count as an entry.
            entry = bars[63].time if calls[0] >= 3 else bars[64].time
            return {"trade_count": 1, "net_pnl": -1,
                    "trades": [{"entry_time": entry, "net_pnl": -1}],
                    "input_candles": []}
        with patch.object(ev, "backtest", side_effect=premature_backtest):
            with self.assertRaisesRegex(ev.PaperEvaluationError, "lookahead_or_warmup_trade"):
                ev.evaluate_rolling_robustness(self.bars, "BTCUSDT", "trend_pullback")



    def test_warmup_entry_boundary_prevents_hidden_positions_and_retains_scored_losses(self):
        from cloud_backend import trading_research as tr
        # Deterministic synthetic candles, NOT independent market evidence.
        flat = [replace(b, open=100, high=101, low=99, close=100, volume=10)
                for b in self.bars]
        with patch.object(tr, "setup", return_value={"stop": 99.5, "reference_entry": 100}):
            result = ev.evaluate_rolling_robustness(flat, "BTCUSDT", "trend_pullback")
        self.assertGreater(result["holdout"]["trade_count"], 0)
        self.assertLess(result["holdout"]["net_pnl"], 0)
        self.assertTrue(all(t["entry_time"] >= flat[210].time
                            for t in result["holdout"]["trades"]))
        for window in result["rolling_robustness"]["windows"]:
            for scenario in (window["baseline"], window["double_costs"]):
                self.assertGreater(scenario["trade_count"], 0)
                self.assertLess(scenario["net_pnl"], 0)
                self.assertTrue(all(t["entry_time"] >= window["first_scored_entry_at"]
                                    for t in scenario["trades"]))

    def test_engine_scored_boundary_does_not_carry_stale_warmup_signal(self):
        from cloud_backend import trading_research as tr
        flat = [replace(b, open=100, high=101, low=99, close=100, volume=10)
                for b in self.bars[:125]]
        cutoff = flat[64].time
        # Signal only on warmup bar 63; entry is allowed at first scored open.
        with patch.object(tr, "setup", return_value={"stop": 95, "reference_entry": 100}):
            scored = tr.backtest(flat, "trend_pullback", SimulationConfig(),
                                 entry_not_before=cutoff)
        self.assertEqual(scored["trades"][0]["entry_time"], cutoff)
        self.assertEqual(scored["initial_equity"], 1000)
        self.assertTrue(all(t["entry_time"] >= cutoff for t in scored["trades"]))
        for invalid in (True, cutoff + 1, flat[0].time - 900_000,
                        flat[-1].time + 900_000):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                tr.backtest(flat, "trend_pullback", SimulationConfig(),
                            entry_not_before=invalid)


if __name__ == "__main__":
    unittest.main()
