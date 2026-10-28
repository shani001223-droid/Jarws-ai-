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


if __name__ == "__main__":
    unittest.main()
