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
        self.assertTrue(all(t["entry_time"] >= self.bars[210].time
                            for t in result["holdout"]["trades"]))

    def test_no_trade_outcome_is_preserved(self):
        flat = [replace(b, open=100, high=100.1, low=99.9, close=100, volume=10)
                for b in self.bars]
        result = ev.evaluate_chronological(flat, "ETHUSDT", "breakout_retest")
        self.assertTrue(result["holdout_no_trades"])
        self.assertEqual(result["holdout"]["trade_count"], 0)
        self.assertEqual(result["holdout"]["net_pnl"], 0)
        self.assertIsNone(result["holdout"]["win_rate_pct"])

    def test_negative_results_are_not_suppressed(self):
        def fake_backtest(bars, strategy, cfg):
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
                                  "--input", str(source), "--strategy", "trend_pullback"],
                                 cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result["split"]["holdout_scored_bars"], 90)
            self.assertFalse(result["orders_enabled"])
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
        def losing_backtest(bars, strategy, cfg):
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
        def premature_backtest(bars, strategy, cfg):
            return {"trade_count": 1, "net_pnl": -1,
                    "trades": [{"entry_time": bars[63].time, "net_pnl": -1}],
                    "input_candles": []}
        with patch.object(ev, "backtest", side_effect=premature_backtest):
            with self.assertRaisesRegex(ev.PaperEvaluationError, "lookahead_or_warmup_trade"):
                ev.evaluate_rolling_robustness(self.bars, "BTCUSDT", "trend_pullback")



if __name__ == "__main__":
    unittest.main()
