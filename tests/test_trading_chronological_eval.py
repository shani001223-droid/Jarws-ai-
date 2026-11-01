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

    def test_resolved_outcome_concentration_keeps_losses_and_excludes_terminal_marks(self):
        # Entirely synthetic modeled trades, not independently observed fills.
        trades = [
            {"entry_time": 0, "net_pnl": -5.0},
            {"entry_time": 900000, "net_pnl": 10.0},
            {"entry_time": 1800000, "net_pnl": -2.0},
            {"entry_time": 2700000, "net_pnl": -3.0},
            {"entry_time": 86400000, "net_pnl": 200.0,
             "terminal_forced_mark": True},
        ]
        d = ev._trade_outcome_concentration(trades)
        self.assertEqual(d["status"], "descriptive_modeled_only")
        self.assertEqual(d["trade_count_including_terminal_marks"], 5)
        self.assertEqual(d["strategy_resolved_trade_count"], 4)
        self.assertEqual(d["terminal_forced_mark_count"], 1)
        self.assertEqual(d["distinct_strategy_resolved_entry_utc_days"], 1)
        self.assertEqual(d["max_consecutive_strategy_resolved_losses"], 2)
        self.assertEqual(d["worst_strategy_resolved_net_pnl_usdt"], -5)
        self.assertEqual(d["largest_win_share_of_resolved_gross_profit_pct"], 100)
        self.assertEqual(d["largest_loss_share_of_resolved_gross_loss_pct"], 50)
        empty = ev._trade_outcome_concentration([])
        self.assertEqual(empty["status"], "no_strategy_resolved_trades")
        self.assertEqual(empty["max_consecutive_strategy_resolved_losses"], 0)
        self.assertIsNone(empty["worst_strategy_resolved_net_pnl_usdt"])
        self.assertIsNone(empty["largest_win_share_of_resolved_gross_profit_pct"])
        self.assertIsNone(empty["largest_loss_share_of_resolved_gross_loss_pct"])
        incomplete = ev._trade_outcome_concentration([
            {"entry_time": 0, "net_pnl": -4.0},
            {"entry_time": 900000}])
        self.assertEqual(incomplete["status"], "unavailable_incomplete_trade_outcomes")
        self.assertIsNone(incomplete["max_consecutive_strategy_resolved_losses"])
        self.assertEqual(incomplete["trade_count_including_terminal_marks"], 2)

    def test_concentration_overflow_never_fabricates_zero_percent_shares(self):
        # Synthetic finite trade PnL can overflow when aggregated. Previously
        # sum() silently became infinity, reporting a false 0% concentration.
        for values in ((1e308, 1e308), (-1e308, -1e308)):
            with self.subTest(values=values):
                trades = [
                    {"entry_time": i * 900000, "net_pnl": pnl}
                    for i, pnl in enumerate(values)
                ]
                summary = ev._trade_outcome_concentration(trades)
                self.assertEqual(summary["status"],
                                 "unavailable_nonfinite_resolved_gross_pnl")
                self.assertEqual(summary["strategy_resolved_trade_count"], 2)
                self.assertIsNone(
                    summary["largest_win_share_of_resolved_gross_profit_pct"])
                self.assertIsNone(
                    summary["largest_loss_share_of_resolved_gross_loss_pct"])
                self.assertEqual(
                    summary["max_consecutive_strategy_resolved_losses"],
                    2 if values[0] < 0 else 0)
        ordinary = ev._trade_outcome_concentration([
            {"entry_time": 0, "net_pnl": 0.1},
            {"entry_time": 900000, "net_pnl": 0.2},
            {"entry_time": 1800000, "net_pnl": 0.3},
            {"entry_time": 2700000, "net_pnl": -2.0},
        ])
        self.assertEqual(ordinary["status"], "descriptive_modeled_only")
        self.assertAlmostEqual(
            ordinary["largest_win_share_of_resolved_gross_profit_pct"], 50.0)
        self.assertEqual(
            ordinary["largest_loss_share_of_resolved_gross_loss_pct"], 100.0)

    def test_chronological_concentration_reports_are_scenario_specific(self):
        from cloud_backend import trading_research as tr
        with patch.object(tr, "setup", return_value=None):
            report = ev.evaluate_rolling_robustness(
                self.bars, "BTCUSDT", "trend_pullback",
                include_cost_guard_sensitivity=True,
                include_holdout_cost_stress=True)
        summary = report["outcome_concentration"]
        self.assertFalse(summary["authenticated_market_data"])
        self.assertFalse(summary["forward_verified"])
        self.assertIsNone(summary["calibrated_win_probability"])
        self.assertEqual(summary["holdout"]["status"], "no_strategy_resolved_trades")
        self.assertEqual(summary["holdout"]["strategy_resolved_trade_count"], 0)
        self.assertEqual(
            report["holdout_original_target_cost_guard_sensitivity"][
                "guarded_outcome_concentration"]["strategy_resolved_trade_count"], 0)
        self.assertEqual(
            report["holdout_double_cost_sensitivity"][
                "double_costs_outcome_concentration"]["strategy_resolved_trade_count"], 0)
        for window in report["rolling_robustness"]["windows"]:
            self.assertEqual(
                window["baseline_outcome_concentration"]["strategy_resolved_trade_count"], 0)
            self.assertEqual(
                window["double_costs_outcome_concentration"]["strategy_resolved_trade_count"], 0)
        self.assertFalse(report["orders_enabled"])

    def test_suspicious_bar_pnl_attribution_keeps_losses_and_zero_trades(self):
        # Ex-post descriptive association on synthetic OHLCV, not real fills.
        bars = [Candle(i * 900000, 100, 101, 99, 100, 10,
                       i * 900000 + 899999) for i in range(5)]
        bars[2] = replace(bars[2], volume=0, high=112)
        trades = [
            {"entry_time": bars[0].time, "exit_time": bars[2].close_time,
             "net_pnl": -3.5},
            {"entry_time": bars[3].time, "exit_time": bars[3].close_time,
             "net_pnl": 2.0},
        ]
        result = ev._execution_bar_quality(bars, trades)["modeled_pnl_attribution"]
        self.assertEqual(result["status"], "descriptive_modeled_only")
        self.assertEqual(result["flagged_trade_count"], 1)
        self.assertEqual(result["unflagged_trade_count"], 1)
        self.assertEqual(result["flagged_net_pnl_usdt"], -3.5)
        self.assertEqual(result["unflagged_net_pnl_usdt"], 2.0)
        self.assertEqual(result["flagged_gross_profit_usdt"], 0.0)
        self.assertEqual(result["flagged_gross_loss_usdt"], 3.5)
        self.assertEqual(result["all_trade_net_pnl_usdt"], -1.5)
        no_trades = ev._execution_bar_quality(bars, [])["modeled_pnl_attribution"]
        self.assertEqual(no_trades["status"], "no_modeled_trades")
        self.assertEqual(no_trades["all_trade_net_pnl_usdt"], 0.0)
        self.assertEqual(no_trades["flagged_trade_count"], 0)

    def test_suspicious_bar_pnl_attribution_fails_closed_on_missing_or_overflow(self):
        bars = [Candle(i * 900000, 100, 101, 99, 100, 10,
                       i * 900000 + 899999) for i in range(4)]
        base = {"entry_time": bars[1].time, "exit_time": bars[2].close_time}
        for trades in ([base], [{**base, "net_pnl": float("nan")}],
                       [{**base, "net_pnl": 1e308},
                        {**base, "net_pnl": 1e308}]):
            with self.subTest(trades=trades):
                report = ev._execution_bar_quality(bars, trades)
                attribution = report["modeled_pnl_attribution"]
                self.assertEqual(attribution["status"],
                                 "unavailable_incomplete_or_nonfinite_trade_pnl")
                self.assertIsNone(attribution["all_trade_net_pnl_usdt"])
                self.assertEqual(attribution["flagged_trade_count"] +
                                 attribution["unflagged_trade_count"], len(trades))
                self.assertEqual(report["trade_count"], len(trades))

    def test_modeled_trade_quality_exposure_flags_suspicious_execution_bars(self):
        # Synthetic candles and synthetic paper timestamps; not real exchange fills.
        bars = [Candle(i * 900000, 100, 101, 99, 100, 10,
                       i * 900000 + 899999) for i in range(6)]
        bars[2] = replace(bars[2], high=112, volume=0)
        bars[3] = replace(bars[3], open=103, high=105, low=99)
        bars[4] = replace(bars[4], high=100, low=100)
        trades = [
            {"entry_time": bars[1].time, "exit_time": bars[4].close_time},
            {"entry_time": bars[5].time, "exit_time": bars[5].time},
        ]
        exposure = ev._execution_bar_quality(bars, trades)
        self.assertEqual(exposure["trade_count"], 2)
        self.assertEqual(exposure["entry_zero_volume_count"], 0)
        self.assertEqual(exposure["exit_zero_volume_count"], 0)
        self.assertEqual(exposure["trades_spanning_zero_volume_count"], 1)
        self.assertEqual(exposure["trades_spanning_flat_ohlc_count"], 1)
        self.assertEqual(exposure["trades_spanning_open_gap_ge_2pct_count"], 1)
        self.assertEqual(exposure["trades_spanning_intrabar_range_ge_10pct_count"], 1)
        self.assertEqual(exposure["trades_spanning_any_flag_count"], 1)
        self.assertEqual(len(exposure["trade_exposures"]), 2)
        self.assertFalse(exposure["trade_exposures"][1]["spanned_zero_volume"])
        self.assertTrue(exposure["trade_exposures"][0]["spanned_zero_volume"])
        with self.assertRaisesRegex(ev.PaperEvaluationError,
                                    "paper_trade_outside_candle_sample"):
            ev._execution_bar_quality(bars, [{"entry_time": -900000,
                                               "exit_time": bars[2].close_time}])

    def test_exact_open_exit_excludes_post_exit_wicks_but_keeps_open_warnings(self):
        # These synthetic OHLC candles are not an intrabar path or exchange fill.
        bars = [Candle(i * 900000, 100, 101, 99, 100, 10,
                       i * 900000 + 899999) for i in range(4)]
        bars[2] = replace(bars[2], open=103, high=120, low=80,
                          close=103, volume=0)
        open_exit = {"entry_time": bars[1].time, "exit_time": bars[2].time,
                     "exit_time_precision": "bar_open_exact"}
        unknown_exit = {"entry_time": bars[1].time,
                        "exit_time": bars[2].close_time,
                        "exit_time_precision": "bar_close_upper_bound_intrabar_unknown"}
        report = ev._execution_bar_quality(bars, [open_exit, unknown_exit])
        at_open, intrabar = report["trade_exposures"]
        self.assertEqual(report["exit_open_only_count"], 1)
        self.assertTrue(at_open["exit_open_only"])
        self.assertTrue(at_open["exit_zero_volume"])
        self.assertTrue(at_open["spanned_zero_volume"])
        self.assertTrue(at_open["spanned_open_gap_ge_2pct"])
        self.assertFalse(at_open["spanned_intrabar_range_ge_10pct"])
        self.assertTrue(intrabar["spanned_intrabar_range_ge_10pct"])
        self.assertFalse(intrabar["exit_open_only"])

        # A flat candle after an open exit does not retroactively make the
        # already-closed position exposed to its closing OHLC shape.
        flat = list(bars)
        flat[2] = replace(flat[2], high=103, low=103, volume=10)
        at_open = ev._execution_bar_quality(flat, [open_exit])["trade_exposures"][0]
        at_close = ev._execution_bar_quality(flat, [unknown_exit])["trade_exposures"][0]
        self.assertFalse(at_open["spanned_flat_ohlc"])
        self.assertTrue(at_close["spanned_flat_ohlc"])
        with self.assertRaisesRegex(ev.PaperEvaluationError,
                                    "invalid_paper_exit_time_precision"):
            ev._execution_bar_quality(bars, [{
                **open_exit, "exit_time": bars[2].close_time}])

    def test_incomplete_synthetic_trade_record_never_invents_clean_exposure(self):
        bars = [Candle(i * 900000, 100, 101, 99, 100, 10,
                       i * 900000 + 899999) for i in range(3)]
        result = ev._execution_bar_quality(
            bars, [{"entry_time": bars[1].time, "net_pnl": -3.5}])
        self.assertEqual(result["trade_count"], 1)
        self.assertEqual(result["status"],
                         "unavailable_incomplete_trade_exit_timestamps")
        self.assertIsNone(result["trades_spanning_any_flag_count"])
        self.assertIsNone(result["trade_exposures"])

    def test_paper_execution_quality_zero_trades_and_same_sample_sensitivity(self):
        from cloud_backend import trading_research as tr
        with patch.object(tr, "setup", return_value=None):
            report = ev.evaluate_chronological(
                self.bars, "BTCUSDT", "trend_pullback",
                include_cost_guard_sensitivity=True)
        exposure = report["paper_execution_bar_quality"]
        self.assertFalse(exposure["authenticated_market_data"])
        self.assertFalse(exposure["observed_exchange_fills"])
        self.assertFalse(exposure["trade_rule_or_filter"])
        self.assertTrue(exposure["counts_overlap"])
        for partition in ("training", "holdout"):
            self.assertEqual(exposure[partition]["trade_count"], 0)
            self.assertEqual(exposure[partition]["trades_spanning_any_flag_count"], 0)
            self.assertEqual(exposure[partition]["trade_exposures"], [])
        guarded = report["holdout_original_target_cost_guard_sensitivity"]
        self.assertEqual(guarded["guarded_paper_execution_bar_quality"]["trade_count"], 0)

    def test_zero_volume_entry_refusal_propagates_to_holdout_and_stress(self):
        # Fully synthetic zero-volume PRIOR closed bars: neither baseline
        # nor doubled-cost replay admits next-open entries or a win rate.
        from cloud_backend import trading_research as tr
        flat = [replace(b, open=100, high=101, low=99,
                        close=100, volume=0) for b in self.bars]
        with patch.object(tr, "setup", return_value={
                "stop": 95, "reference_entry": 100}):
            report = ev.evaluate_chronological(
                flat, "BTCUSDT", "trend_pullback",
                include_holdout_cost_stress=True)
        base = report["holdout"]
        stressed = report["holdout_double_cost_sensitivity"]["double_costs_holdout"]
        for outcome in (base, stressed):
            d = outcome["execution_diagnostics"]
            self.assertGreater(d["paper_entry_attempts"], 0)
            self.assertEqual(d["paper_entries_skipped_prior_closed_zero_volume"],
                             d["paper_entry_attempts"])
            self.assertEqual(d["paper_entries_opened"], 0)
            self.assertEqual(outcome["trade_count"], 0)
            self.assertEqual(outcome["net_pnl"], 0)
            self.assertIsNone(outcome["win_rate_pct"])
            self.assertIsNone(outcome["profit_factor"])
        self.assertFalse(report["orders_enabled"])

    def test_prior_closed_volume_guard_is_causal_and_preserves_baseline(self):
        # Synthetic setup always proposes a next-open long. The entry bar's
        # final volume is not known at its open; use only prior closed volume.
        from cloud_backend import trading_research as tr
        flat = [replace(b, open=100, high=101, low=99,
                        close=100, volume=10) for b in self.bars]
        setup = {"stop": 99.5, "reference_entry": 100}
        with patch.object(tr, "setup", return_value=setup):
            report = ev.evaluate_chronological(
                flat, "BTCUSDT", "trend_pullback",
                include_prior_volume_guard_sensitivity=True)
        baseline = report["holdout"]
        guarded = report["holdout_prior_closed_volume_guard_sensitivity"]
        d = guarded["guarded_holdout"]["execution_diagnostics"]
        self.assertGreater(baseline["trade_count"], 0)
        self.assertEqual(guarded["baseline_trade_count"], baseline["trade_count"])
        self.assertEqual(guarded["baseline_net_pnl_usdt"], baseline["net_pnl"])
        self.assertEqual(guarded["guarded_holdout"]["trade_count"], 0)
        self.assertEqual(guarded["guarded_holdout"]["net_pnl"], 0)
        self.assertGreater(d["paper_entries_skipped_prior_closed_volume_cap"], 0)
        self.assertEqual(d["paper_entries_opened"], 0)
        self.assertIsNone(guarded["guarded_holdout"]["win_rate_pct"])
        self.assertFalse(guarded["forward_verified"])
        self.assertFalse(guarded["independent_venue_verified"])
        self.assertNotIn("holdout_prior_closed_volume_guard_sensitivity",
                         ev.evaluate_chronological(flat, "BTCUSDT", "trend_pullback"))
        # Ample prior volume admits the same entries and negative PnL.
        ample = [replace(b, volume=10000) for b in flat]
        with patch.object(tr, "setup", return_value=setup):
            ample_report = ev.evaluate_chronological(
                ample, "BTCUSDT", "trend_pullback",
                include_prior_volume_guard_sensitivity=True)
        self.assertEqual(
            ample_report["holdout_prior_closed_volume_guard_sensitivity"][
                "guarded_holdout"]["net_pnl"],
            ample_report["holdout"]["net_pnl"])
        self.assertGreater(
            ample_report["holdout_prior_closed_volume_guard_sensitivity"][
                "guarded_holdout"]["trade_count"], 0)
        self.assertTrue(all(
            t["modeled_entry_qty_pct_of_prior_closed_bar_volume"] <= 1
            for t in ample_report["holdout_prior_closed_volume_guard_sensitivity"][
                "guarded_holdout"]["trades"]))
        # Valid but tiny reported prior volume must not leak Infinity/NaN
        # into a JSON export; unavailable ratio is explicit None.
        tiny = [replace(b, volume=1e-320) for b in flat]
        with patch.object(tr, "setup", return_value=setup):
            tiny_report = ev.evaluate_chronological(
                tiny, "BTCUSDT", "trend_pullback")
        self.assertGreater(tiny_report["holdout"]["trade_count"], 0)
        self.assertIsNone(tiny_report["holdout"]["trades"][0][
            "modeled_entry_qty_pct_of_prior_closed_bar_volume"])
        self.assertNotIn("Infinity", json.dumps(tiny_report, allow_nan=False))
        for bad in (0, -1, 11, float("nan"), True, "1"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                tr.backtest(flat[:100], "trend_pullback", SimulationConfig(),
                            max_prior_volume_participation_pct=bad)
        for bad in (None, 1, "true"):
            with self.subTest(flag=bad), self.assertRaisesRegex(
                    ev.PaperEvaluationError, "invalid_prior_volume_guard_flag"):
                ev.evaluate_chronological(
                    flat, "BTCUSDT", "trend_pullback",
                    include_prior_volume_guard_sensitivity=bad)
        rolling = ev.evaluate_rolling_robustness(
            flat, "BTCUSDT", "trend_pullback",
            include_prior_volume_guard_sensitivity=True)
        self.assertIn("holdout_prior_closed_volume_guard_sensitivity", rolling)

    def test_sample_quality_counts_holdout_boundary_gaps_and_zero_volume(self):
        # Entirely synthetic contiguous 15m OHLCV, not authenticated data.
        from cloud_backend import trading_research as tr
        bars = [replace(b, open=100, high=101, low=99,
                        close=100, volume=10) for b in self.bars]
        bars[10] = replace(bars[10], volume=0)
        bars[250] = replace(bars[250], volume=0)
        # First holdout opening is compared with the final training close.
        bars[210] = replace(bars[210], open=103, high=104, low=99)
        bars[220] = replace(bars[220], high=111)
        bars[221] = replace(bars[221], high=100, low=100)
        with patch.object(tr, "setup", return_value=None):
            report = ev.evaluate_chronological(bars, "BTCUSDT", "trend_pullback")
        quality = report["sample_quality"]
        train, holdout, full = (quality[k] for k in
                                ("training", "holdout", "full_sample"))
        self.assertEqual(quality["status"], "descriptive_operator_supplied_unverified")
        self.assertFalse(quality["authenticated_market_data"])
        self.assertFalse(quality["trade_rule_or_filter"])
        self.assertEqual((train["bars"], holdout["bars"], full["bars"]),
                         (210, 90, 300))
        self.assertEqual((train["zero_volume_bars"],
                          holdout["zero_volume_bars"], full["zero_volume_bars"]),
                         (1, 1, 2))
        self.assertEqual((train["open_gap_ge_2pct_bars"],
                          holdout["open_gap_ge_2pct_bars"],
                          full["open_gap_ge_2pct_bars"]), (0, 1, 1))
        self.assertEqual(holdout["intrabar_range_ge_10pct_bars"], 1)
        self.assertEqual(holdout["flat_ohlc_bars"], 1)
        self.assertEqual(holdout["first_open_at_ms"], bars[210].time)
        self.assertEqual(holdout["last_close_at_ms"], bars[-1].close_time)
        self.assertEqual(report["holdout"]["trade_count"], 0)
        self.assertEqual(report["holdout"]["net_pnl"], 0)
        self.assertFalse(report["orders_enabled"])

    def test_sample_quality_avoids_overflow_from_valid_extreme_price_ratios(self):
        from cloud_backend import trading_research as tr
        # Direct descriptive helper is deliberately safe even when ratios
        # are astronomically large; no fabricated percent is serialized.
        tiny = Candle(0, 1e-150, 1e-150, 1e-150, 1e-150, 0, 899999)
        huge = Candle(900000, 1e150, 1e150, 1e150, 1e150, 0, 1799999)
        quality = ev._sample_quality([tiny, huge])
        self.assertEqual(quality["open_gap_ge_2pct_bars"], 1)
        self.assertEqual(quality["zero_volume_bars"], 2)
        self.assertEqual(quality["intrabar_range_ge_10pct_bars"], 0)
        self.assertEqual(quality["bars"], 2)

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
            + d["paper_entries_skipped_past_signal_target"]
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

    def test_next_open_at_or_above_original_target_cancels_stale_paper_entry(self):
        from cloud_backend import trading_research as tr
        # Synthetic next-open gap: the signal's original 2R target was
        # already reached at the opening. Repricing the target would chase.
        for opening in (110.0, 111.0):
            with self.subTest(opening=opening):
                bars = [replace(b, open=opening, high=112, low=94,
                                close=100, volume=10) for b in self.bars]
                with patch.object(tr, "setup", return_value={
                        "stop": 95.0, "reference_entry": 100.0,
                        "reference_target": 110.0}):
                    report = ev.evaluate_chronological(
                        bars, "BTCUSDT", "trend_pullback")
                d = report["holdout"]["execution_diagnostics"]
                self.assertGreater(d["paper_entry_attempts"], 0)
                self.assertEqual(d["paper_entry_attempts"],
                                 d["paper_entries_skipped_past_signal_target"])
                self.assertEqual(d["paper_entries_opened"], 0)
                self.assertEqual(report["holdout"]["trade_count"], 0)
                self.assertEqual(report["holdout"]["net_pnl"], 0)

        # A next open still below the original target remains eligible;
        # subsequent intrabar stop treatment remains conservative.
        bars = [replace(b, open=109.0, high=112, low=94,
                        close=100, volume=10) for b in self.bars]
        with patch.object(tr, "setup", return_value={
                "stop": 95.0, "reference_entry": 100.0,
                "reference_target": 110.0}):
            valid = ev.evaluate_chronological(
                bars, "BTCUSDT", "trend_pullback")
        self.assertGreater(
            valid["holdout"]["execution_diagnostics"]["paper_entries_opened"], 0)
        self.assertEqual(
            valid["holdout"]["execution_diagnostics"]["paper_entries_skipped_past_signal_target"], 0)

    def test_slippage_adjusted_next_open_at_signal_target_is_refused(self):
        from cloud_backend import trading_research as tr
        # Synthetic 5 bps buy slippage takes 109.98 above the original
        # 110.00 signal target, even though the raw opening was below it.
        # No new 2R target may be manufactured from that modeled fill.
        for opening, refused in ((109.98, True), (109.0, False)):
            with self.subTest(opening=opening):
                bars = [replace(b, open=opening, high=112, low=94,
                                close=100, volume=10) for b in self.bars]
                with patch.object(tr, "setup", return_value={
                        "stop": 95.0, "reference_entry": 100.0,
                        "reference_target": 110.0}):
                    report = ev.evaluate_chronological(
                        bars, "BTCUSDT", "trend_pullback")
                d = report["holdout"]["execution_diagnostics"]
                self.assertGreater(d["paper_entry_attempts"], 0)
                self.assertEqual(
                    d["paper_entry_attempts"],
                    d["paper_entries_opened"] + d["paper_entries_skipped_invalid_gap"]
                    + d["paper_entries_skipped_past_signal_target"]
                    + d["paper_entries_skipped_utc_daily_loss_cap"]
                    + d["paper_entries_skipped_insufficient_risk_capacity"])
                if refused:
                    self.assertEqual(d["paper_entry_attempts"],
                                     d["paper_entries_skipped_past_signal_target"])
                    self.assertEqual(d["paper_entries_opened"], 0)
                    self.assertEqual(report["holdout"]["trade_count"], 0)
                    self.assertEqual(report["holdout"]["net_pnl"], 0)
                else:
                    self.assertGreater(d["paper_entries_opened"], 0)
                    self.assertEqual(d["paper_entries_skipped_past_signal_target"], 0)
                    self.assertGreater(report["holdout"]["trade_count"], 0)
                self.assertFalse(report["orders_enabled"])

    def test_original_signal_remaining_reward_risk_disclosure(self):
        from cloud_backend import trading_research as tr
        # Synthetic next-open gaps are both below the original 110 target.
        # The 109 opening leaves less than 1R to that original target even
        # though the paper engine recomputes its own target as 2R.
        for opening, below_one in ((109.0, True), (100.0, False)):
            with self.subTest(opening=opening):
                bars = [replace(b, open=opening, high=112, low=94,
                                close=100, volume=10) for b in self.bars]
                with patch.object(tr, "setup", return_value={
                        "stop": 95.0, "reference_entry": 100.0,
                        "reference_target": 110.0}):
                    report = ev.evaluate_chronological(
                        bars, "BTCUSDT", "trend_pullback")
                trades = report["holdout"]["trades"]
                self.assertGreater(len(trades), 0)
                for trade in trades:
                    self.assertEqual(trade["original_signal_target"], 110.0)
                    expected = ((110.0 - trade["entry"])
                                / (trade["entry"] - trade["reference_stop"]))
                    self.assertAlmostEqual(
                        trade["remaining_original_signal_reward_risk_at_entry"],
                        expected)
                    self.assertAlmostEqual(
                        trade["reference_target"],
                        trade["entry"] + 2*(trade["entry"] - trade["reference_stop"]))
                    self.assertEqual(expected < 1, below_one)
                self.assertEqual(
                    report["holdout"]["execution_diagnostics"][
                        "paper_entries_original_signal_remaining_rr_below_1r"],
                    len(trades) if below_one else 0)
                self.assertFalse(report["orders_enabled"])

        with patch.object(tr, "setup", return_value=None):
            empty = ev.evaluate_chronological(self.bars, "ETHUSDT", "trend_pullback")
        self.assertEqual(
            empty["holdout"]["execution_diagnostics"][
                "paper_entries_original_signal_remaining_rr_below_1r"], 0)

    def test_original_target_cost_guard_sensitivity_is_opt_in_and_not_independent(self):
        from cloud_backend import trading_research as tr
        cfg = SimulationConfig(fee_bps=10, slippage_bps=5)
        for opening, refused in ((109.8, True), (109.0, False)):
            with self.subTest(opening=opening):
                bars = [replace(b, open=opening, high=112, low=94,
                                close=100, volume=10) for b in self.bars]
                with patch.object(tr, "setup", return_value={
                        "stop": 95.0, "reference_entry": 100.0,
                        "reference_target": 110.0}):
                    report = ev.evaluate_chronological(
                        bars, "BTCUSDT", "trend_pullback", cfg,
                        include_cost_guard_sensitivity=True)
                baseline = report["holdout"]
                scenario = report["holdout_original_target_cost_guard_sensitivity"]
                guarded = scenario["guarded_holdout"]
                d = guarded["execution_diagnostics"]
                self.assertEqual(scenario["status"], "same_holdout_counterfactual_not_independent")
                self.assertFalse(scenario["independent_venue_verified"])
                self.assertFalse(scenario["forward_verified"])
                self.assertFalse(baseline["reject_nonpositive_original_net_upside"])
                self.assertTrue(guarded["reject_nonpositive_original_net_upside"])
                self.assertGreater(baseline["trade_count"], 0)
                if refused:
                    self.assertEqual(guarded["trade_count"], 0)
                    self.assertEqual(guarded["net_pnl"], 0)
                    self.assertGreater(d["paper_entries_skipped_nonpositive_original_target_net_upside"], 0)
                else:
                    self.assertEqual(guarded["trade_count"], baseline["trade_count"])
                    self.assertEqual(guarded["net_pnl"], baseline["net_pnl"])
                    self.assertEqual(d["paper_entries_skipped_nonpositive_original_target_net_upside"], 0)
                self.assertEqual(
                    d["paper_entry_attempts"],
                    d["paper_entries_opened"] + d["paper_entries_skipped_invalid_gap"]
                    + d["paper_entries_skipped_past_signal_target"]
                    + d["paper_entries_skipped_utc_daily_loss_cap"]
                    + d["paper_entries_skipped_insufficient_risk_capacity"]
                    + d["paper_entries_skipped_nonpositive_original_target_net_upside"])
        with patch.object(tr, "setup", return_value=None):
            empty = ev.evaluate_chronological(
                self.bars, "ETHUSDT", "trend_pullback",
                include_cost_guard_sensitivity=True)
        self.assertEqual(empty["holdout"]["trade_count"], 0)
        self.assertEqual(
            empty["holdout_original_target_cost_guard_sensitivity"]["guarded_holdout"]["trade_count"], 0)
        with self.assertRaises(ev.PaperEvaluationError):
            ev.evaluate_chronological(
                self.bars, "BTCUSDT", "trend_pullback",
                include_cost_guard_sensitivity=1)

    def test_original_signal_net_upside_includes_exit_slippage_and_both_fees(self):
        from cloud_backend import trading_research as tr
        # Synthetic only: an original 110 target can be ABOVE the modeled
        # entry but already unprofitable net of two fees and sell slippage.
        for opening, net_positive, net_below_one in (
                (109.8, False, True), (109.0, True, True),
                (100.0, True, False)):
            with self.subTest(opening=opening):
                bars = [replace(b, open=opening, high=112, low=94,
                                close=100, volume=10) for b in self.bars]
                cfg = SimulationConfig(fee_bps=10, slippage_bps=5)
                with patch.object(tr, "setup", return_value={
                        "stop": 95.0, "reference_entry": 100.0,
                        "reference_target": 110.0}):
                    report = ev.evaluate_chronological(
                        bars, "BTCUSDT", "trend_pullback", cfg)
                trades = report["holdout"]["trades"]
                self.assertGreater(len(trades), 0)
                for trade in trades:
                    modeled_exit = 110.0*(1-cfg.slippage_bps/10_000)
                    per_unit = (modeled_exit-trade["entry"]
                                - cfg.fee_bps/10_000*(modeled_exit+trade["entry"]))
                    stop_loss_per_unit = (trade["planned_stop_loss_usdt"]
                                          / trade["quantity"])
                    self.assertAlmostEqual(
                        trade["original_signal_target_net_gain_per_unit_usdt"],
                        per_unit)
                    self.assertAlmostEqual(
                        trade["remaining_original_signal_net_reward_risk_at_entry"],
                        per_unit/stop_loss_per_unit)
                    self.assertEqual(per_unit > 0, net_positive)
                    self.assertEqual(per_unit/stop_loss_per_unit < 1,
                                     net_below_one)
                    self.assertGreater(
                        trade["remaining_original_signal_reward_risk_at_entry"], 0)
                d = report["holdout"]["execution_diagnostics"]
                self.assertEqual(
                    d["paper_entries_original_signal_net_upside_nonpositive"],
                    0 if net_positive else len(trades))
                self.assertFalse(report["orders_enabled"])

        with patch.object(tr, "setup", return_value=None):
            empty = ev.evaluate_chronological(self.bars, "ETHUSDT", "trend_pullback")
        self.assertEqual(
            empty["holdout"]["execution_diagnostics"][
                "paper_entries_original_signal_net_upside_nonpositive"], 0)

    def test_last_bar_time_expiry_is_strategy_resolved_not_terminal_mark(self):
        from cloud_backend import trading_research as tr
        # Synthetic 15m bars: signal index 63, next-open entry index 64,
        # 96-bar scheduled time exit index 160, exactly the sample's end.
        flat = [replace(b, open=100, high=101, low=99, close=100.2,
                        volume=10) for b in self.bars[:161]]
        signal_time = flat[63].time

        def one_signal(bars, strategy):
            return ({"stop": 90.0, "reference_entry": 100.2}
                    if bars[-1].time == signal_time else None)

        with patch.object(tr, "setup", side_effect=one_signal):
            scheduled = tr.backtest(flat, "trend_pullback", SimulationConfig())
            premature = tr.backtest(flat[:-1], "trend_pullback", SimulationConfig())
            stop_bar = flat.copy()
            stop_bar[-1] = replace(stop_bar[-1], low=89.0)
            stopped = tr.backtest(stop_bar, "trend_pullback", SimulationConfig())
        self.assertEqual(scheduled["trade_count"], 1)
        trade = scheduled["trades"][0]
        self.assertEqual(trade["reason"], "time_exit")
        self.assertEqual(trade["exit_time"], flat[-1].close_time)
        self.assertEqual(trade["exit_time_precision"], "bar_close_exact")
        self.assertFalse(trade["terminal_forced_mark"])
        diagnostics = scheduled["execution_diagnostics"]
        self.assertEqual(diagnostics["terminal_forced_close_count"], 0)
        self.assertEqual(diagnostics["strategy_resolved_trade_count"], 1)
        self.assertAlmostEqual(diagnostics["strategy_resolved_net_pnl_usdt"],
                               trade["net_pnl"])
        self.assertEqual(premature["trades"][0]["reason"], "end_of_sample")
        self.assertEqual(premature["execution_diagnostics"]["terminal_forced_close_count"], 1)
        self.assertEqual(stopped["trades"][0]["reason"], "stop")
        self.assertEqual(stopped["execution_diagnostics"]["terminal_forced_close_count"], 0)
        self.assertFalse(stopped["trades"][0]["terminal_forced_mark"])

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
        self.assertIsNone(diagnostics["strategy_resolved_win_rate_pct"])
        self.assertIsNone(diagnostics["strategy_resolved_expectancy_usdt"])
        self.assertIsNone(diagnostics["strategy_resolved_profit_factor"])
        self.assertAlmostEqual(report["net_pnl"], trade["net_pnl"])
        self.assertFalse(report["orders_enabled"])

        with patch.object(tr, "setup", return_value=None):
            empty = tr.backtest(flat, "trend_pullback", SimulationConfig())
        self.assertEqual(empty["trade_count"], 0)
        self.assertEqual(empty["execution_diagnostics"]["terminal_forced_close_count"], 0)
        self.assertEqual(empty["execution_diagnostics"]["terminal_forced_close_net_pnl_usdt"], 0)
        self.assertEqual(empty["execution_diagnostics"]["strategy_resolved_trade_count"], 0)
        self.assertEqual(empty["execution_diagnostics"]["strategy_resolved_net_pnl_usdt"], 0)
        self.assertIsNone(empty["execution_diagnostics"]["strategy_resolved_win_rate_pct"])
        self.assertIsNone(empty["execution_diagnostics"]["strategy_resolved_expectancy_usdt"])
        self.assertIsNone(empty["execution_diagnostics"]["strategy_resolved_profit_factor"])


    def test_modeled_fee_and_slippage_breakdown_reconciles_losses_and_zero_trades(self):
        from cloud_backend import trading_research as tr
        # Synthetic next-open entries and same-bar stops, never exchange fills.
        flat = [replace(b, open=100, high=101, low=99, close=100, volume=10)
                for b in self.bars[:130]]
        with patch.object(tr, "setup",
                          return_value={"stop": 99.5, "reference_entry": 100}):
            report = tr.backtest(flat, "trend_pullback", SimulationConfig())
        self.assertGreater(report["trade_count"], 0)
        self.assertLess(report["net_pnl"], 0)
        diagnostics = report["execution_diagnostics"]
        buy = sell = fees = 0.0
        for trade in report["trades"]:
            self.assertGreater(trade["modeled_buy_slippage_cost_usdt"], 0)
            self.assertGreater(trade["modeled_sell_slippage_cost_usdt"], 0)
            self.assertEqual(trade["entry_reference_open"], 100)
            self.assertEqual(trade["exit_reference_price"], 99.5)
            self.assertAlmostEqual(
                trade["reference_gross_pnl_before_modeled_costs_usdt"],
                trade["quantity"] * (trade["exit_reference_price"]
                                     - trade["entry_reference_open"]))
            self.assertAlmostEqual(
                trade["net_pnl"],
                trade["reference_gross_pnl_before_modeled_costs_usdt"]
                - trade["modeled_buy_slippage_cost_usdt"]
                - trade["modeled_sell_slippage_cost_usdt"] - trade["fees"])
            buy += trade["modeled_buy_slippage_cost_usdt"]
            sell += trade["modeled_sell_slippage_cost_usdt"]
            fees += trade["fees"]
        self.assertAlmostEqual(diagnostics["modeled_buy_slippage_cost_usdt"], buy)
        self.assertAlmostEqual(diagnostics["modeled_sell_slippage_cost_usdt"], sell)
        self.assertAlmostEqual(diagnostics["modeled_total_slippage_cost_usdt"],
                               buy + sell)
        self.assertAlmostEqual(diagnostics["modeled_fees_plus_slippage_cost_usdt"],
                               buy + sell + fees)
        self.assertAlmostEqual(report["fees_paid"], fees)
        self.assertAlmostEqual(report["net_pnl"],
                               sum(t["net_pnl"] for t in report["trades"]))
        with patch.object(tr, "setup", return_value=None):
            empty = tr.backtest(flat, "trend_pullback", SimulationConfig())
        self.assertEqual(empty["trade_count"], 0)
        self.assertEqual(empty["net_pnl"], 0)
        for key in ("modeled_buy_slippage_cost_usdt",
                    "modeled_sell_slippage_cost_usdt",
                    "modeled_total_slippage_cost_usdt",
                    "modeled_fees_plus_slippage_cost_usdt"):
            self.assertEqual(empty["execution_diagnostics"][key], 0)

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

    def test_strategy_resolved_metrics_exclude_terminal_mark_from_denominator(self):
        from cloud_backend import trading_research as tr
        # One early modeled stop, then a distinct terminal forced mark.
        # These synthetic candles and patched signals are not market evidence.
        flat = [replace(b, open=100, high=101, low=99, close=100.2, volume=10)
                for b in self.bars]
        first_signal, final_signal = flat[63].time, flat[-2].time

        def two_signals(bars, strategy):
            if bars[-1].time == first_signal:
                return {"stop": 99.5, "reference_entry": 100.2}
            if bars[-1].time == final_signal:
                return {"stop": 90.0, "reference_entry": 100.2}
            return None

        with patch.object(tr, "setup", side_effect=two_signals):
            report = tr.backtest(flat, "trend_pullback", SimulationConfig())
        self.assertEqual(report["trade_count"], 2)
        resolved = [t for t in report["trades"] if not t["terminal_forced_mark"]]
        terminal = [t for t in report["trades"] if t["terminal_forced_mark"]]
        self.assertEqual(len(resolved), 1)
        self.assertEqual(len(terminal), 1)
        self.assertLess(resolved[0]["net_pnl"], 0)
        diagnostics = report["execution_diagnostics"]
        self.assertEqual(diagnostics["strategy_resolved_trade_count"], 1)
        self.assertEqual(diagnostics["terminal_forced_close_count"], 1)
        self.assertAlmostEqual(diagnostics["strategy_resolved_net_pnl_usdt"],
                               resolved[0]["net_pnl"])
        self.assertEqual(diagnostics["strategy_resolved_win_rate_pct"], 0)
        self.assertAlmostEqual(diagnostics["strategy_resolved_expectancy_usdt"],
                               resolved[0]["net_pnl"])
        self.assertEqual(diagnostics["strategy_resolved_profit_factor"], 0)
        self.assertAlmostEqual(report["net_pnl"],
                               resolved[0]["net_pnl"] + terminal[0]["net_pnl"])
        self.assertFalse(report["orders_enabled"])

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


    def test_primary_holdout_double_cost_stress_retains_losses_and_boundary(self):
        from cloud_backend import trading_research as tr
        flat = [replace(b, open=100, high=101, low=99, close=100, volume=10)
                for b in self.bars]
        with patch.object(tr, "setup", return_value={"stop": 99.5,
                                                      "reference_entry": 100}):
            report = ev.evaluate_chronological(flat, "BTCUSDT", "trend_pullback",
                                               include_holdout_cost_stress=True)
        stress = report["holdout_double_cost_sensitivity"]
        self.assertEqual(stress["status"], "evaluated_same_holdout_not_independent")
        self.assertFalse(stress["independent_venue_verified"])
        self.assertFalse(stress["forward_verified"])
        self.assertEqual(stress["baseline_trade_count"], report["holdout"]["trade_count"])
        self.assertEqual(stress["baseline_net_pnl_usdt"], report["holdout"]["net_pnl"])
        self.assertGreater(stress["baseline_trade_count"], 0)
        self.assertLess(stress["baseline_net_pnl_usdt"], 0)
        self.assertGreater(stress["double_costs_trade_count"], 0)
        self.assertLess(stress["double_costs_net_pnl_usdt"], 0)
        self.assertEqual(stress["double_costs_holdout"]["config"]["fee_bps"], 20)
        self.assertEqual(stress["double_costs_holdout"]["config"]["slippage_bps"], 10)
        self.assertNotIn("input_candles", stress["double_costs_holdout"])
        self.assertEqual(stress["double_costs_paper_execution_bar_quality"]["trade_count"],
                         stress["double_costs_trade_count"])
        self.assertTrue(all(t["entry_time"] >= flat[210].time
                            for t in stress["double_costs_holdout"]["trades"]))

    def test_primary_holdout_double_cost_stress_zero_and_bounds(self):
        from cloud_backend import trading_research as tr
        with patch.object(tr, "setup", return_value=None):
            report = ev.evaluate_chronological(self.bars, "ETHUSDT", "trend_pullback",
                                               include_holdout_cost_stress=True)
        stress = report["holdout_double_cost_sensitivity"]
        self.assertEqual(stress["baseline_trade_count"], 0)
        self.assertEqual(stress["baseline_net_pnl_usdt"], 0)
        self.assertEqual(stress["double_costs_trade_count"], 0)
        self.assertEqual(stress["double_costs_net_pnl_usdt"], 0)
        self.assertEqual(stress["double_costs_paper_execution_bar_quality"]["trade_count"], 0)
        self.assertNotIn("holdout_double_cost_sensitivity",
                         ev.evaluate_chronological(self.bars, "ETHUSDT", "trend_pullback"))
        unavailable = ev.evaluate_chronological(
            self.bars, "ETHUSDT", "trend_pullback",
            SimulationConfig(fee_bps=60), include_holdout_cost_stress=True)
        self.assertEqual(unavailable["holdout_double_cost_sensitivity"]["status"],
                         "unavailable_config_exceeds_engine_bounds")
        self.assertIsNone(unavailable["holdout_double_cost_sensitivity"]["double_costs_holdout"])
        for bad in (None, 1, "true"):
            with self.subTest(bad=bad), self.assertRaisesRegex(
                    ev.PaperEvaluationError, "invalid_holdout_cost_stress_flag"):
                ev.evaluate_chronological(self.bars, "BTCUSDT", "trend_pullback",
                                          include_holdout_cost_stress=bad)

    def test_rolling_forwards_primary_holdout_cost_stress(self):
        report = ev.evaluate_rolling_robustness(
            self.bars, "BTCUSDT", "trend_pullback",
            include_holdout_cost_stress=True)
        self.assertIn("holdout_double_cost_sensitivity", report)
        self.assertIn("rolling_robustness", report)
        self.assertEqual(report["holdout_double_cost_sensitivity"]["double_costs_holdout"]["config"]["fee_bps"], 20)


if __name__ == "__main__":
    unittest.main()
