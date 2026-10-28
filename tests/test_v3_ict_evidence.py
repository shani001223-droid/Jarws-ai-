"""Native minute-bar evidence clocks, causality and unknown execution."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import v3_ict_evidence as i


def receipt():
    return json.loads((ROOT / "knowledge_base/05_ICT_COMPLETE/ict_intraday_observations_20261028.json").read_text())


def stamp(s):
    return int(datetime.fromisoformat(s).timestamp()*1000)


class V3ICTTests(unittest.TestCase):
    def test_first_selection_and_features_do_not_see_future(self):
        p = receipt()
        for item, bars in zip(p["observations"], i.check_receipt(p)):
            scan = item["gap_scan"]; f = scan["first_case"]["features"]
            k = next(k for k,b in enumerate(bars) if b["time"] == f["c"]["time"])
            prefix = bars[:k+1]
            self.assertEqual(i.gap_features(prefix,k),f)
            self.assertEqual(i.gap_scan(prefix)["first_case"]["features"],f)
            self.assertIsNone(i.gap_case(prefix,k)["outcome"])
            self.assertEqual(scan["eligible_c_open_times"][0],f["c"]["time"])
            self.assertEqual(f["earliest_after_close"],f["source_bar_closed_at"]+1)

    def test_dst_window_boundaries_and_weekends(self):
        for day, utc_hour, offset in (("2024-01-05",15,"-05:00"),("2024-08-08",14,"-04:00")):
            start = stamp(f"{day}T{utc_hour:02d}:00:00+00:00")
            c = i.clock(start)
            self.assertTrue(c["local_time"].endswith(offset))
            self.assertIn("silver_am",c["active_windows"])
            self.assertNotIn("silver_am",i.clock(start-1)["active_windows"])
            self.assertNotIn("silver_am",i.clock(start+60*i.MINUTE)["active_windows"])
        self.assertEqual(i.clock(stamp("2024-08-10T14:30:00+00:00"))["active_windows"],[])

    def test_full_gap_cross_has_priority_over_rejection_close(self):
        p = receipt(); i.check_receipt(p)
        cases = [o["gap_scan"]["first_case"] for o in p["observations"]]
        for case in (cases[0],cases[2]):
            out = case["outcome"]
            self.assertIsNotNone(out["first_full_gap_crossing"])
            self.assertIsNone(out["first_eligible_geometric_retest"])
            self.assertFalse(out["fill_known"])
            self.assertIsNone(out["strategy_pnl"])
        self.assertIsNone(cases[1]["outcome"]["first_contact"])
        self.assertTrue(all(c["features"]["decision"] == "WAIT" for c in cases))

    def test_missing_minutes_or_forged_digest_or_outcome_rejected(self):
        p = receipt(); raw = json.loads(p["observations"][0]["response_body"])
        del raw[10]
        with self.assertRaises(AssertionError): i.normalize(raw)
        for target in ("source_sha256","gap_scan"):
            forged = deepcopy(p)
            o = forged["observations"][0]
            if target == "source_sha256": o[target] = "0"*64
            else: o[target]["first_case"]["outcome"]["first_full_gap_crossing"] = None
            with self.assertRaises(AssertionError): i.check_receipt(forged)

    def test_gap_finishing_at_window_end_is_not_an_entry(self):
        # Synthetic geometry checks a clock boundary only; not historical evidence.
        base = stamp("2024-01-05T15:57:00+00:00")
        synthetic = [{"time":base+k*i.MINUTE,"close_time":base+(k+1)*i.MINUTE-1,
                      "open":p,"high":p+1,"low":p-1,"close":p,"volume":1}
                     for k,p in enumerate((100,102,104))]
        f = i.gap_features(synthetic,2)
        self.assertEqual(f["clock"]["local_time"],"2024-01-05T11:00:00-05:00")
        self.assertEqual(f["eligible_windows"],[])
        self.assertIsNone(f["win_probability"])


if __name__ == "__main__": unittest.main()
