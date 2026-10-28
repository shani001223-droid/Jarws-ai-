"""Reference proximity is not observed stop inventory or a win rate."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import v3_liquidity_evidence as l


def receipt():
    return json.loads((ROOT/"knowledge_base/06_LIQUIDITY_GOD/liquidity_observations_20261028.json").read_text())


class V3LiquidityTests(unittest.TestCase):
    def test_cluster_references_are_prior_confirmed_and_prefix_stable(self):
        p=receipt();windows=l.check_receipt(p,ROOT)
        for entry in p["cluster_cases"]:
            f=entry["case"]["features"];bars=windows[entry["source_window_sha256"]]
            prefix=[b for b in bars if b["close_time"]<=f["event"]["close_time"]]
            self.assertEqual(l.cluster_features(prefix,f["event"]["date"],f["kind"]),f)
            self.assertIsNone(l.cluster_case(prefix,f["event"]["date"],f["kind"])["outcome"])
            self.assertLess(f["second_pivot"]["confirmed_at"],f["prior_available_at"])
            self.assertLessEqual(f["separation_bps"],25)

    def test_absent_event_excursion_is_not_a_completed_raid(self):
        p=receipt();l.check_receipt(p,ROOT)
        c=p["cluster_cases"][1]["case"]
        self.assertFalse(c["features"]["event_wick_beyond_outer"])
        self.assertEqual(c["outcome"]["first_beyond_outer_bar"]["date"],"2021-04-10")
        self.assertEqual(c["outcome"]["first_post_excursion_reclaim"]["date"],"2021-04-10")
        # Apr 6 is already below the cluster but has not made the required excursion.
        self.assertNotEqual(c["outcome"]["first_post_excursion_reclaim"]["date"],"2021-04-06")

    def test_outer_excursion_does_not_guarantee_reversal_or_execution(self):
        p=receipt();l.check_receipt(p,ROOT)
        first,last=(p["cluster_cases"][k]["case"] for k in (0,2))
        self.assertFalse(first["features"]["event_close_reclaims_entire_cluster"])
        self.assertEqual(first["outcome"]["first_post_excursion_reclaim"]["date"],"2020-06-02")
        self.assertIsNone(last["outcome"]["first_post_excursion_reclaim"])
        for entry in p["cluster_cases"]:
            f=entry["case"]["features"]
            self.assertFalse(f["actual_stop_inventory_known"])
            self.assertIsNone(f["win_probability"])
            self.assertEqual(f["decision"],"WAIT")
            self.assertIsNone(entry["case"]["outcome"]["strategy_pnl"])

    def test_corrupted_cluster_or_outcome_or_source_rejected(self):
        for key in ("boundary","outcome","source"):
            p=deepcopy(receipt())
            if key=="boundary":p["cluster_cases"][0]["case"]["features"]["upper"]+=1
            elif key=="outcome":p["cluster_cases"][1]["case"]["outcome"]["first_post_excursion_reclaim"]=None
            else:p["source_file_sha256"]="0"*64
            with self.assertRaises(AssertionError):l.check_receipt(p,ROOT)

    def test_twenty_bar_reference_is_prior_only_and_outcomes_are_separate(self):
        p=receipt();windows=l.check_receipt(p,ROOT)
        for entry in p["reclaim_cases"]:
            f=entry["case"]["features"];bars=windows[entry["source_window_sha256"]]
            prefix=[b for b in bars if b["close_time"]<=f["event"]["close_time"]]
            self.assertEqual(l.reclaim_features(prefix,f["event"]["date"],f["kind"]),f)
            self.assertIsNone(l.reclaim_case(prefix,f["event"]["date"],f["kind"])["outcome"])
            self.assertLess(f["reference_date"],f["event"]["date"])
            self.assertFalse(f["published_intraday_order_parity"])

    def test_plus_one_absence_and_same_day_reclaim_do_not_become_wins(self):
        p=receipt();l.check_receipt(p,ROOT)
        cases=[e["case"] for e in p["reclaim_cases"]]
        for c in (cases[0],cases[2]):
            self.assertTrue(c["features"]["plus_one_setup"])
            self.assertFalse(c["outcome"]["next_day_reference_in_recorded_range"])
            self.assertFalse(c["outcome"]["next_day_opens_beyond_entry_side"])
        self.assertTrue(cases[1]["features"]["same_day_closing_reclaim"])
        self.assertGreater(cases[1]["outcome"]["raw_close_change_pct"],0)
        self.assertTrue(all(c["outcome"]["strategy_pnl"] is None for c in cases))

    def test_tied_reference_uses_most_recent_day_and_rejects_forged_age(self):
        p=receipt();w=l.check_receipt(p,ROOT)
        e=p["reclaim_cases"][0];f=e["case"]["features"]
        bars=deepcopy(w[e["source_window_sha256"]]);k=next(k for k,b in enumerate(bars) if l.utc_day(b["time"])==f["event"]["date"])
        # Synthetic duplicate anchor tests tie policy, not a historical claim.
        bars[k-1]["high"]=f["reference"]
        tied=l.reclaim_features(bars,f["event"]["date"],"high")
        self.assertEqual(tied["reference_age_bars"],1)
        self.assertFalse(tied["same_day_age_gate"])
        p["reclaim_cases"][0]["case"]["features"]["reference_age_bars"]+=1
        with self.assertRaises(AssertionError):l.check_receipt(p,ROOT)

    def test_unfilled_cost_illustrations_bound_modeled_risk_and_cash(self):
        for price in (1,4800,59769.13,1e12):
            f=l.cost_illustration(price)
            for row in f["cost_sensitivity"]:
                self.assertLessEqual(row["modeled_stop_loss"],50+1e-10)
                self.assertLessEqual(row["entry_cash_with_modeled_cost"],10000+1e-8)
            self.assertGreater(f["cost_sensitivity"][0]["net_target_to_stop_loss_ratio"],
                               f["cost_sensitivity"][-1]["net_target_to_stop_loss_ratio"])
            self.assertIsNone(f["strategy_pnl"])
        for invalid in (0,-1,float('nan'),float('inf'),True):
            with self.assertRaises(AssertionError):l.cost_illustration(invalid)

    def test_barriers_keep_ambiguity_and_do_not_invent_account_results(self):
        p=receipt();w=l.check_receipt(p,ROOT)
        cases=[e["case"] for e in p["execution_cases"]]
        self.assertEqual([c["outcome"]["first_barrier_observation"]["classification"] for c in cases],
                         ["ambiguous_both_barriers_same_bar","target_reference_only_first","stop_reference_only_first"])
        for e in p["execution_cases"]:
            f=e["case"]["features"];bars=w[e["source_window_sha256"]]
            prefix=[b for b in bars if b["close_time"]<=f["event"]["close_time"]]
            self.assertEqual(l.execution_features(prefix,f["event"]["date"]),f)
            self.assertIsNone(l.execution_case(prefix,f["event"]["date"])["outcome"])
            self.assertIsNone(e["case"]["outcome"]["drawdown"])
        p["execution_cases"][0]["case"]["outcome"]["first_barrier_observation"]["classification"]="target_reference_only_first"
        with self.assertRaises(AssertionError):l.check_receipt(p,ROOT)

    def test_gap_open_is_not_filled_at_the_stop_reference(self):
        p=receipt();w=l.check_receipt(p,ROOT);e=p["execution_cases"][2]
        f=e["case"]["features"];bars=deepcopy(w[e["source_window_sha256"]])
        k=next(k for k,b in enumerate(bars) if l.utc_day(b["time"])==f["event"]["date"])
        bars[k+1]["open"]=.9*f["illustration"]["stop_reference"]
        c=l.execution_case(bars,f["event"]["date"])
        self.assertEqual(c["outcome"]["first_barrier_observation"]["classification"],"opens_at_or_beyond_stop_reference")
        self.assertIsNone(c["outcome"]["strategy_pnl"])


if __name__ == "__main__":unittest.main()
