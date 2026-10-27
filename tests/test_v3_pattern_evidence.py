"""Original geometry conventions, causal cutoffs and actual-source receipts."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import v3_pattern_evidence as e
from v3_structure_evidence import DAY, utc_day


def bars(values):
    start = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()*1000)
    return [dict(time=start+i*DAY, close_time=start+(i+1)*DAY-1,
                 open=o, high=h, low=l, close=c, volume=1.)
            for i, (o, h, l, c) in enumerate(values)]


def receipt():
    return json.loads((ROOT / "knowledge_base/02_CANDLESTICK_AND_CHART_PATTERNS/pattern_observations_20261028.json").read_text())


class V3PatternTests(unittest.TestCase):
    def test_zero_range_is_not_an_automatic_doji(self):
        feature = e.candle_features(bars([(10.,10.,10.,10.)]), 0)
        self.assertIsNone(feature["measurements"]["body_fraction"])
        self.assertEqual(feature["labels"], [])

    def test_body_engulfing_is_not_the_same_as_wick_engulfing(self):
        b = bars([(12.,16.,6.,10.), (10.,14.,8.,13.)])
        labels = e.candle_features(b, 1)["labels"]
        self.assertIn("bullish_body_engulfing", labels)
        self.assertIn("strict_inside_bar", labels)
        self.assertNotIn("strict_outside_bar", labels)

    def test_tied_body_and_equal_range_boundaries_are_not_strict_events(self):
        b = bars([(12.,16.,6.,10.), (10.,16.,6.,12.)])
        self.assertNotIn("bullish_body_engulfing", e.candle_features(b, 1)["labels"])
        self.assertNotIn("strict_inside_bar", e.candle_features(b, 1)["labels"])

    def test_future_does_not_change_features_and_missing_outcome_is_null(self):
        b = bars([(10.,13.,8.,12.)]*8)
        stamp = utc_day(b[2]["time"])
        early, later = e.candle_case(b[:3], stamp), e.candle_case(b, stamp)
        self.assertEqual(early["features"], later["features"])
        self.assertIsNone(early["outcome"])
        self.assertEqual(later["outcome"]["available_at"], b[7]["close_time"])

    def test_actual_three_source_cases_are_replayed(self):
        p = receipt(); e.check_receipt(p, ROOT)
        cases = [entry["case"] for entry in p["candle_cases"]]
        self.assertIn("lower_wick_geometry", cases[0]["features"]["labels"])
        self.assertLess(cases[0]["outcome"]["forward_close_change_pct"], -36)
        self.assertIn("bullish_body_engulfing", cases[1]["features"]["labels"])
        self.assertFalse(cases[1]["outcome"]["next_close_above_event_high"])
        self.assertIn("doji_geometry", cases[2]["features"]["labels"])

    def test_corrupt_receipt_and_invented_outcome_rejected(self):
        p = receipt(); p["source_receipt_sha256"] = "0"*64
        with self.assertRaises(AssertionError): e.check_receipt(p, ROOT)
        p = receipt(); p["candle_cases"][0]["case"]["outcome"]["fifth_close"] += 100
        with self.assertRaises(AssertionError): e.check_receipt(p, ROOT)
        p = receipt(); p["source_receipt"] = "../../elsewhere.json"
        with self.assertRaises(AssertionError): e.check_receipt(p, ROOT)

    def test_classical_candidate_can_cancel_before_later_neckline_break(self):
        p = receipt(); e.check_receipt(p, ROOT)
        cases = [x["case"] for x in p["classical_cases"]]
        self.assertEqual(cases[0]["outcome"]["first_neckline_beyond_close"]["date"], "2020-04-06")
        self.assertTrue(cases[0]["outcome"]["eligible_break_before_cancellation"])
        self.assertIsNone(cases[1]["outcome"]["first_neckline_beyond_close"])
        self.assertEqual(cases[2]["outcome"]["first_outer_invalidation_close"]["date"], "2022-11-04")
        self.assertFalse(cases[2]["outcome"]["eligible_break_before_cancellation"])

    def test_classical_formation_features_survive_future_append(self):
        p = receipt(); windows = e.check_receipt(p, ROOT)
        entry = p["classical_cases"][0]; case = entry["case"]
        b = windows[entry["source_window_sha256"]]
        prefix = [x for x in b if x["close_time"] <= case["known_at"]]
        early = e.two_turn_case(prefix, case["kind"], case["first_date"], case["second_date"])
        self.assertIsNone(early["outcome"])
        self.assertEqual({k:v for k,v in early.items() if k not in ("outcome_status", "outcome")},
                         {k:v for k,v in case.items() if k not in ("outcome_status", "outcome")})
        p = receipt(); p["classical_cases"][0]["case"]["outcome"]["first_neckline_beyond_close"]["close"] += 1
        with self.assertRaises(AssertionError): e.check_receipt(p, ROOT)

    def test_one_near_fibonacci_ratio_does_not_become_a_validated_pattern(self):
        p = receipt(); e.check_receipt(p, ROOT)
        cases = [x["case"] for x in p["harmonic_cases"]]
        self.assertTrue(cases[0]["gartley_necessary_ratio_diagnostics"]["AB_near_0_618"])
        self.assertFalse(cases[0]["gartley_necessary_ratio_diagnostics"]["AD_near_0_786"])
        for case in cases:
            self.assertFalse(case["pattern_validated"])
            self.assertIsNone(case["win_probability"])
        p["harmonic_cases"][0]["case"]["pattern_validated"] = True
        with self.assertRaises(AssertionError): e.check_receipt(p, ROOT)

    def test_unconfirmed_or_substituted_harmonic_anchor_rejected(self):
        p = receipt(); windows = e.check_receipt(p, ROOT)
        entry = p["harmonic_cases"][0]; case = entry["case"]; b = windows[entry["source_window_sha256"]]
        prefix = [x for x in b if x["close_time"] <= case["points"][-1]["pivot_at"]]
        with self.assertRaises(AssertionError): e.harmonic_case(prefix, case["dates"])
        confirmed = [x for x in b if x["close_time"] <= case["known_at"]]
        self.assertEqual(e.harmonic_case(confirmed, case["dates"]), case)
        substituted = case["dates"][:]; substituted[1] = "2020-06-18"
        with self.assertRaises(AssertionError): e.harmonic_case(b, substituted)

    def test_no_event_and_incomplete_event_are_not_zero_return_evidence(self):
        no_event = bars([(10.,13.,9.,11.)]*9)
        empty = e.candle_event_study(no_event)
        self.assertEqual(empty["detected_events"], 0)
        self.assertIsNone(empty["mean_raw_close_change_pct"])
        tail = no_event[:]
        tail[-2] = {**tail[-2], "open":12., "close":10.}
        tail[-1] = {**tail[-1], "open":9., "close":13.}
        incomplete = e.candle_event_study(tail)
        self.assertEqual(incomplete["detected_events"], 1)
        self.assertEqual(incomplete["incomplete_endpoints"], 1)
        self.assertIsNone(incomplete["mean_raw_close_change_pct"])
        self.assertIsNone(incomplete["events"][0]["outcome"])

    def test_exhaustive_study_keeps_failed_overlapping_and_tail_events(self):
        p = receipt(); e.check_receipt(p, ROOT)
        studies = [x["case"] for x in p["pattern_studies"]]
        self.assertEqual([x["detected_events"] for x in studies], [23,15,19])
        self.assertEqual([x["observed_endpoints"] for x in studies], [23,14,19])
        self.assertEqual([x["overlapping_forward_window_pairs"] for x in studies], [10,1,4])
        self.assertAlmostEqual(studies[0]["mean_raw_close_change_pct"], .06357840362689461)
        self.assertAlmostEqual(studies[0]["assumed_cost_sensitivity"][1]["mean_raw_change_minus_deduction"], -.1364215963731054)
        self.assertLess(studies[2]["mean_raw_close_change_pct"], -1.)
        for study in studies:
            self.assertIsNone(study["strategy_pnl"])
            self.assertIsNone(study["win_probability"])
            self.assertEqual(study["status"], "exploratory_descriptive_not_holdout")
        p["pattern_studies"][2]["case"]["events"].pop()
        with self.assertRaises(AssertionError): e.check_receipt(p, ROOT)

    def test_rare_extension_is_separate_from_later_confirmation(self):
        p = receipt(); windows = e.check_receipt(p, ROOT)
        cases = [x["case"] for x in p["rare_cases"]]
        self.assertIsNone(cases[0]["outcome"]["first_confirmation"])
        self.assertEqual(cases[1]["outcome"]["first_confirmation"]["date"], "2021-04-03")
        self.assertEqual(cases[2]["outcome"]["first_confirmation"]["date"], "2022-09-28")
        entry = p["rare_cases"][1]; case = entry["case"]
        prefix = [b for b in windows[entry["source_window_sha256"]] if b["close_time"] <= case["known_at"]]
        early = e.inside_extension_case(prefix, case["inside_date"])
        self.assertIsNone(early["outcome"])
        self.assertEqual(early["reclaim_level"], case["reclaim_level"])

    def test_body_gap_is_not_a_full_range_gap_or_a_success_rate(self):
        p = receipt(); e.check_receipt(p, ROOT)
        gaps = [x["case"] for x in p["gap_summaries"]]
        self.assertEqual([x["strict_real_body_gaps"] for x in gaps], [28,24,36])
        self.assertEqual([x["strict_full_range_gaps"] for x in gaps], [0,0,0])
        self.assertTrue(all(x["pattern_success_rate"] is None for x in gaps))
        p["rare_cases"][0]["case"]["outcome"]["first_confirmation"] = {"date":"2020-02-17"}
        with self.assertRaises(AssertionError): e.check_receipt(p, ROOT)


if __name__ == "__main__":
    unittest.main()
