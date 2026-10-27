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


if __name__ == "__main__":
    unittest.main()
