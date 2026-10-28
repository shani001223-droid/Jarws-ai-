"""Historical knowledge clocks and retained negative evidence, not profits."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import v3_smc_evidence as s


def receipt():
    return json.loads((ROOT / "knowledge_base/04_SMC_COMPLETE/smc_observations_20261028.json").read_text())


class V3SMCTests(unittest.TestCase):
    def test_structure_features_do_not_use_any_future_capture_bars(self):
        p = receipt(); windows = s.check_receipt(p, ROOT)
        for bars in windows.values():
            for i in range(1, len(bars)):
                date = s.utc_day(bars[i]["time"])
                full = s.structure_features(bars, date)
                self.assertEqual(full, s.structure_features(bars[:i+1], date))
                for key in ("latest_known_high", "latest_known_low"):
                    if full[key]:
                        self.assertLess(full[key]["confirmed_at"], bars[i]["time"])
        for entry in p["structure_cases"]:
            f = entry["case"]["features"]; bars = windows[entry["source_window_sha256"]]
            prefix = [b for b in bars if b["close_time"] <= f["known_at"]]
            self.assertIsNone(s.structure_case(prefix, f["event"]["date"])["outcome"])

    def test_wick_and_repeated_cross_do_not_become_fresh_breaks(self):
        p = receipt(); windows = s.check_receipt(p, ROOT)
        bars = windows[p["structure_cases"][0]["source_window_sha256"]]
        wick = s.structure_features(bars, "2020-04-07")
        self.assertTrue(wick["up_wick_beyond_reference"])
        self.assertFalse(wick["up_close_crossing"])
        repeat = s.structure_features(bars, "2020-04-08")
        self.assertTrue(repeat["raw_up_close_crossing"])
        self.assertEqual(repeat["label"], "previously_broken_reference_recross")
        self.assertFalse(repeat["up_close_crossing"])

    def test_missing_or_zero_baseline_is_not_displacement(self):
        bars = [{"open": 100., "close": 100., "high": 101., "low": 99.} for _ in range(20)]
        bars.append({"open": 100., "close": 103., "high": 104., "low": 99.})
        self.assertEqual(s.displacement(bars, 19)["status"], "insufficient_prior_bars")
        d = s.displacement(bars, 20)
        self.assertEqual(d["status"], "zero_body_baseline")
        self.assertIsNone(d["body_multiple"])
        self.assertFalse(d["up_qualified"])

    def test_forged_reference_and_future_return_are_rejected(self):
        for key in ("reference", "outcome"):
            p = receipt()
            if key == "reference":
                p["structure_cases"][0]["case"]["features"]["latest_known_high"]["price"] += 1
            else:
                p["structure_cases"][2]["case"]["outcome"]["raw_close_change_pct"] = 92
            with self.assertRaises(AssertionError):
                s.check_receipt(p, ROOT)

    def test_range_features_are_prefix_stable_and_outcomes_missing_at_event(self):
        p = receipt(); windows = s.check_receipt(p, ROOT)
        for entry in p["range_cases"]:
            f = entry["case"]["features"]; bars = windows[entry["source_window_sha256"]]
            prefix = [b for b in bars if b["close_time"] <= f["known_at"]]
            self.assertEqual(s.range_features(prefix, f["event"]["date"]), f)
            self.assertIsNone(s.range_case(prefix, f["event"]["date"])["outcome"])

    def test_outside_or_invalid_ranges_do_not_become_discount_premium(self):
        outside = s.range_location(250., 100., 200.)
        self.assertEqual(outside["location"], "outside_above")
        self.assertEqual(outside["position_fraction"], 1.5)
        self.assertFalse(outside["inside_range"])
        for low, high in ((None, 100.), (100., 100.), (101., 100.)):
            invalid = s.range_location(100., low, high)
            self.assertIsNone(invalid["position_fraction"])
            self.assertIsNone(invalid["midpoint"])
        self.assertEqual(s.range_location(150., 100., 200.)["location"], "equilibrium")

    def test_same_close_changes_label_only_under_disclosed_anchor_policy(self):
        p = receipt(); s.check_receipt(p, ROOT)
        f = p["range_cases"][2]["case"]["features"]
        self.assertEqual(f["event"]["date"], "2022-11-07")
        self.assertEqual(f["location"], "premium")
        alternate = f["alternate_asof_close_anchors"]
        self.assertEqual(alternate["location"], "discount")
        self.assertEqual(alternate["high_anchor"]["confirmed_at"], f["known_at"])
        p["range_cases"][2]["case"]["features"]["midpoint"] += 1
        with self.assertRaises(AssertionError):
            s.check_receipt(p, ROOT)

    def test_sequence_has_strict_event_order_and_no_future_features(self):
        p = receipt(); windows = s.check_receipt(p, ROOT)
        for entry in p["sequence_cases"]:
            f = entry["case"]["features"]; bars = windows[entry["source_window_sha256"]]
            prefix = [b for b in bars if b["close_time"] <= f["known_at"]]
            self.assertEqual(s.sequence_features(prefix, f["confirmation"]["date"], f["direction"]), f)
            self.assertIsNone(s.sequence_case(prefix, f["confirmation"]["date"], f["direction"])["outcome"])
            self.assertLess(f["sweep"]["known_at"], f["break"]["known_at"])
            self.assertLess(f["break"]["known_at"], f["known_at"])
            self.assertLess(f["sweep"]["reference"]["confirmed_at"], f["sweep"]["known_at"]-86_400_000+1)
            self.assertEqual(f["decision"], "WAIT")
            self.assertFalse(f["orders_enabled"])

    def test_missing_retest_or_same_bar_invalidation_cannot_be_filled_signal(self):
        p = receipt(); windows = s.check_receipt(p, ROOT)
        cases = [e["case"] for e in p["sequence_cases"]]
        self.assertEqual(cases[0]["outcome"]["retest_status"], "no_eligible_retest_in_window")
        self.assertEqual(cases[1]["outcome"]["first_eligible_geometric_retest"]["date"], "2021-05-14")
        invalid = cases[2]["outcome"]
        self.assertEqual(invalid["first_gap_contact"]["date"], invalid["first_invalidation"]["bar"]["date"])
        self.assertIsNone(invalid["first_eligible_geometric_retest"])
        bars = windows[p["sequence_cases"][0]["source_window_sha256"]]
        adjacent = s.sequence_features(bars, "2020-01-29", "long")
        self.assertFalse(adjacent["price_sequence_qualified"])
        self.assertIn("no_fresh_prior_reference_close_break", adjacent["missing_price_conditions"])

    def test_sequence_receipt_rejects_fabricated_retest(self):
        p = receipt()
        p["sequence_cases"][2]["case"]["outcome"]["first_eligible_geometric_retest"] = {"date": "2022-06-01"}
        with self.assertRaises(AssertionError):
            s.check_receipt(p, ROOT)

    def test_exhaustive_formation_ledger_preserves_rejected_and_adverse_cases(self):
        p = receipt(); s.check_receipt(p, ROOT)
        studies = [e["study"] for e in p["sequence_studies"]]
        self.assertEqual([x["directional_decisions"] for x in studies], [322,326,448])
        self.assertEqual([x["formation_count"] for x in studies], [17,10,17])
        self.assertEqual([x["qualified_price_chains"] for x in studies], [2,3,3])
        self.assertEqual([x["eligible_geometric_retest_chains"] for x in studies], [0,1,1])
        for x in studies:
            self.assertEqual(x["directional_decisions"], x["decisions_with_complete_five_bar_horizon"]+x["decisions_with_incomplete_horizon"])
            self.assertEqual(x["formation_count"], len(x["formation_rows"]))
            self.assertEqual(x["qualified_price_chains"], sum(x[k] for k in (
                "eligible_geometric_retest_chains", "invalid_before_eligible_retest_chains",
                "no_eligible_retest_chains", "incomplete_qualified_chains")))
            self.assertTrue(any(r["missing_price_conditions"] for r in x["formation_rows"]))
            self.assertTrue(all(r["decision"] == "WAIT" for r in x["formation_rows"]))
        p["sequence_studies"][0]["study"]["formation_rows"].pop()
        with self.assertRaises(AssertionError):
            s.check_receipt(p, ROOT)

    def test_zero_geometric_events_are_not_zero_drawdown_or_perfect_accuracy(self):
        p = receipt(); s.check_receipt(p, ROOT)
        x = p["sequence_studies"][0]["study"]
        self.assertEqual(x["eligible_geometric_retest_chains"], 0)
        for key in ("drawdown", "simulated_trade_count", "win_probability", "strategy_pnl"):
            self.assertIsNone(x[key])
        self.assertFalse(x["costs_measured"])
        self.assertFalse(x["independent_holdout"])

    def test_qualified_tail_chain_keeps_its_missing_horizon(self):
        p = receipt(); windows = s.check_receipt(p, ROOT)
        bars = windows[p["sequence_cases"][0]["source_window_sha256"]]
        prefix = [b for b in bars if s.utc_day(b["time"]) <= "2020-01-28"]
        x = s.sequence_study(prefix)
        self.assertEqual(x["incomplete_qualified_chains"], 1)
        row = next(r for r in x["formation_rows"] if r["confirmation_date"] == "2020-01-28")
        self.assertIsNone(row["raw_five_bar_close_change_pct"])
        self.assertEqual(row["outcome_status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
