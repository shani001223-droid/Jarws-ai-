"""Evidence causality/lifecycle checks; no account-return assertions."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import v3_zone_evidence as z


def receipt():
    return json.loads((ROOT / "knowledge_base/03_SUPPLY_DEMAND_ORDERBLOCKS/zone_observations_20261028.json").read_text())


class V3ZoneTests(unittest.TestCase):
    def test_pivot_features_activate_only_after_confirmation(self):
        p = receipt(); windows = z.check_receipt(p, ROOT)
        for entry in p["pivot_zone_cases"]:
            f = entry["case"]["features"]; bars = windows[entry["source_window_sha256"]]
            early = [b for b in bars if b["close_time"] < f["known_at"]]
            with self.assertRaises(StopIteration):
                z.pivot_zone_features(early, f["origin"]["date"], f["kind"])
            available = [b for b in bars if b["close_time"] <= f["known_at"]]
            self.assertEqual(z.pivot_zone_features(available, f["origin"]["date"], f["kind"]), f)
            self.assertIsNone(z.pivot_zone_case(available, f["origin"]["date"], f["kind"])["outcome"])

    def test_noncontact_and_breached_contact_are_not_winning_trades(self):
        p = receipt(); z.check_receipt(p, ROOT)
        cases = [e["case"] for e in p["pivot_zone_cases"]]
        self.assertEqual(cases[0]["outcome"]["first_closing_rejection"]["date"], "2020-03-16")
        self.assertIsNone(cases[1]["outcome"]["first_contact"])
        o = cases[2]["outcome"]
        self.assertEqual(o["first_contact"]["date"], "2022-11-08")
        self.assertEqual(o["first_close_breach"]["date"], "2022-11-08")
        self.assertIsNone(o["first_closing_rejection"])
        self.assertFalse(o["fill_known"])
        self.assertIsNone(o["strategy_pnl"])

    def test_zone_receipt_rejects_forged_boundary_or_outcome(self):
        for target in ("boundary", "outcome"):
            p = receipt()
            if target == "boundary":
                p["pivot_zone_cases"][0]["case"]["features"]["zone_low"] += 1
            else:
                p["pivot_zone_cases"][2]["case"]["outcome"]["first_close_breach"] = None
            with self.assertRaises(AssertionError):
                z.check_receipt(p, ROOT)

    def test_orderblock_origin_is_unavailable_until_c_closes(self):
        p = receipt(); windows = z.check_receipt(p, ROOT)
        for entry in p["orderblock_cases"]:
            f = entry["case"]["features"]; bars = windows[entry["source_window_sha256"]]
            prefix = [b for b in bars if b["close_time"] <= f["known_at"]]
            with self.assertRaises(StopIteration):
                z.orderblock_features(prefix[:-1], f["confirmation"]["date"], f["direction"])
            self.assertEqual(z.orderblock_features(prefix, f["confirmation"]["date"], f["direction"]), f)
            self.assertIsNone(z.orderblock_case(prefix, f["confirmation"]["date"], f["direction"])["outcome"])
            self.assertLess(f["origin"]["close_time"], f["displacement"]["close_time"])
            self.assertGreaterEqual(f["body_multiple"], 1.5)

    def test_gap_crossing_wick_and_close_invalidation_are_different(self):
        p = receipt(); z.check_receipt(p, ROOT)
        cases = [x["case"] for x in p["orderblock_cases"]]
        first = cases[0]["outcome"]
        self.assertEqual(first["first_full_gap_crossing"]["date"], "2020-05-10")
        self.assertEqual(first["first_wick_breach"]["date"], "2020-05-10")
        self.assertIsNone(first["first_close_breach"])
        self.assertIsNone(cases[1]["outcome"]["first_contact"])
        self.assertEqual(cases[2]["outcome"]["first_close_breach"]["date"], "2022-09-09")
        self.assertTrue(all(c["features"]["win_probability"] is None for c in cases))

    def test_orderblock_receipt_rejects_fabricated_origin(self):
        p = receipt()
        p["orderblock_cases"][0]["case"]["features"]["origin"]["date"] = "2020-05-06"
        with self.assertRaises(AssertionError):
            z.check_receipt(p, ROOT)


if __name__ == "__main__":
    unittest.main()
