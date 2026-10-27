"""Causality and corrupt-evidence regressions for curriculum research only."""
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("v3_structure_evidence", ROOT / "scripts/v3_structure_evidence.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


def rows(highs):
    start = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()*1000)
    return [[start+i*e.DAY, "10", str(high), "5", "10", "1",
             start+(i+1)*e.DAY-1, "10", 1, "1", "10", "0"] for i, high in enumerate(highs)]


class V3EvidenceTests(unittest.TestCase):
    def test_pivot_not_usable_until_second_later_close(self):
        bars = e.normalized(rows([11, 12, 20, 13, 14, 15]))
        self.assertEqual(e.pivots(bars[:4]), [])
        known = e.pivots(bars[:5])
        self.assertEqual(len(known), 1)
        self.assertEqual(known[0]["pivot_at"], bars[2]["close_time"])
        self.assertEqual(known[0]["confirmed_at"], bars[4]["close_time"])

    def test_equal_extrema_are_not_strict_pivots(self):
        bars = e.normalized(rows([11, 12, 20, 20, 13, 14, 15]))
        self.assertEqual(e.pivots(bars), [])

    def test_future_append_cannot_change_an_existing_snapshot(self):
        bars = e.normalized(rows([11, 12, 20, 13, 14, 15, 18, 16, 14]))
        stamp = e.utc_day(bars[4]["time"])
        self.assertEqual(e.snapshot(bars[:5], stamp), e.snapshot(bars, stamp))

    def test_partial_week_is_never_a_closed_week(self):
        bars = e.normalized(rows([20]*15))
        self.assertEqual(e.full_weeks(bars[:6]), [])
        week = e.full_weeks(bars[:7])
        self.assertEqual(len(week), 1)
        self.assertEqual(week[0]["close_time"], bars[6]["close_time"])
        self.assertEqual(len(e.full_weeks(bars[:13])), 1)

    def test_invalid_ohlc_gap_and_nonfinite_values_rejected(self):
        for mutate in (lambda r: r[2].__setitem__(3, "22"),
                       lambda r: r[2].__setitem__(2, "nan"),
                       lambda r: r.pop(2)):
            source = rows([20]*8)
            mutate(source)
            with self.assertRaises(AssertionError):
                e.normalized(source)

    def test_capture_receipts_and_every_historical_prefix_replay(self):
        payload = json.loads((ROOT / "knowledge_base/01_MARKET_STRUCTURE/structure_observations_20261028.json").read_text())
        self.assertEqual(len(payload["observations"]), 3)
        for item in payload["observations"]:
            bars = e.check_window(item)
            for index in range(5, len(bars)+1):
                stamp = e.utc_day(bars[index-1]["time"])
                self.assertEqual(e.snapshot(bars[:index], stamp), e.snapshot(bars, stamp))

    def test_digest_bounds_and_invented_snapshot_rejected(self):
        payload = json.loads((ROOT / "knowledge_base/01_MARKET_STRUCTURE/structure_observations_20261028.json").read_text())
        original = payload["observations"][0]
        for field, value in (("source_sha256", "0"*64), ("rows", 1),
                             ("request_url", original["request_url"].replace("BTCUSDT", "ETHUSDT"))):
            item = copy.deepcopy(original); item[field] = value
            with self.assertRaises(AssertionError): e.check_window(item)
        item = copy.deepcopy(original)
        item["snapshots"][0]["daily"]["last_close"] += 1
        with self.assertRaises(AssertionError): e.check_window(item)

    def test_breakout_uses_prior_window_and_keeps_missing_future_null(self):
        source = rows([20]*27)
        source[20][2] = "30"; source[20][4] = "25"
        bars = e.normalized(source)
        date = e.utc_day(bars[20]["time"])
        early = e.breakout_case(bars[:21], date)
        later = e.breakout_case(bars, date)
        self.assertEqual(early["frozen_level"], 20)
        self.assertEqual(early["outcome_status"], "incomplete")
        self.assertIsNone(early["outcome"])
        self.assertEqual(early["known_at"], later["known_at"])
        self.assertEqual(later["outcome"]["available_at"], bars[25]["close_time"])

    def test_breakout_rejects_non_events_and_made_up_forward_outcomes(self):
        bars = e.normalized(rows([20]*27))
        with self.assertRaises(AssertionError):
            e.breakout_case(bars, e.utc_day(bars[20]["time"]))
        payload = json.loads((ROOT / "knowledge_base/01_MARKET_STRUCTURE/structure_observations_20261028.json").read_text())
        item = copy.deepcopy(payload["observations"][0])
        item["breakout_cases"][0]["outcome"]["forward_close_change_pct"] += 1
        with self.assertRaises(AssertionError): e.check_window(item)

    def test_real_breakout_cases_retain_success_absence_and_failure(self):
        payload = json.loads((ROOT / "knowledge_base/01_MARKET_STRUCTURE/structure_observations_20261028.json").read_text())
        cases = [x["breakout_cases"][0] for x in payload["observations"]]
        self.assertEqual([x["frozen_level"] for x in cases], [7459.69, 35398.0, 21085.0])
        self.assertEqual(cases[0]["outcome"]["contact_dates"], ["2020-04-24", "2020-04-25"])
        self.assertEqual(cases[1]["outcome"]["contact_dates"], [])
        self.assertEqual(cases[2]["outcome"]["close_back_across_dates"][0], "2022-11-06")
        self.assertAlmostEqual(cases[2]["outcome"]["forward_close_change_pct"], -24.709577786057846)


if __name__ == "__main__":
    unittest.main()
