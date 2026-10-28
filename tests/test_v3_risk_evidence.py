"""Meaningful boundaries, independent enumeration, and model-risk counterexamples."""
from copy import deepcopy
import itertools
import json
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import v3_risk_evidence as f


class V3RiskTests(unittest.TestCase):
    def test_binary_optimum_is_local_maximum_not_a_paper_recommendation(self):
        k=f.binary_kelly(.55,1);self.assertAlmostEqual(k,.1)
        value=f.expected_log_growth(.55,1,k)
        for nearby in (k-.001,k+.001):self.assertLess(f.expected_log_growth(.55,1,nearby),value)
        self.assertEqual(f.binary_kelly(.45,1),0)
        self.assertEqual(f.expected_log_growth(.55,1,0),0)

    def test_overbetting_and_probability_error_can_reverse_log_growth(self):
        self.assertGreater(f.expected_log_growth(.55,1,.1),0)
        self.assertLess(f.expected_log_growth(.55,1,.2),0)
        self.assertLess(f.expected_log_growth(.51,1,.1),0)

    def test_finite_run_probability_matches_independent_full_enumeration(self):
        p=.6;n=6;length=3;expected=0
        for seq in itertools.product((0,1),repeat=n):
            if '000' in ''.join(map(str,seq)):
                wins=sum(seq);expected+=p**wins*(1-p)**(n-wins)
        self.assertAlmostEqual(f.loss_run_probability(p,n,length),expected,places=14)
        self.assertGreater(f.loss_run_probability(.55,100,10),.45**10)
        self.assertEqual(f.loss_run_probability(.55,0,10),0)
        self.assertAlmostEqual(f.loss_run_probability(0,10,10),1)
        self.assertAlmostEqual(f.loss_run_probability(1,100,10),0)

    def test_same_final_wealth_can_hide_different_drawdown_paths(self):
        a=f.wealth_path(100,[.5,-.2,-.2]);b=f.wealth_path(100,[-.2,.5,-.2])
        self.assertAlmostEqual(a['ending_equity'],b['ending_equity'])
        self.assertAlmostEqual(a['maximum_drawdown_fraction'],.36)
        self.assertAlmostEqual(b['maximum_drawdown_fraction'],.2)
        # The first loss is measured from initial wealth, not omitted.
        c=f.wealth_path(100,[-.25]);self.assertAlmostEqual(c['maximum_drawdown_fraction'],.25)
        zero=f.wealth_path(100,[-1,.5]);self.assertEqual(zero['ending_equity'],0)
        self.assertEqual(zero['maximum_drawdown_fraction'],1)

    def test_joint_exposure_changes_variance_and_invalid_covariance_is_rejected(self):
        self.assertAlmostEqual(f.two_asset_variance([.5,.5],[[.04,0],[0,.04]]),.02)
        self.assertAlmostEqual(f.two_asset_variance([.5,.5],[[.04,.04],[.04,.04]]),.04)
        for w,c in (([.8,.8],[[.04,0],[0,.04]]),([.5,.5],[[.04,.1],[.1,.04]]),([.5,.5],[[.04,.01],[0,.04]])):
            with self.assertRaises(AssertionError):f.two_asset_variance(w,c)

    def test_nonfinite_boolean_invalid_domain_and_unbounded_work_rejected(self):
        for p in (True,math.nan,math.inf,-.1,1.1,0,1):
            with self.assertRaises(AssertionError):f.binary_kelly(p,1)
        for args in ((.55,1,1),(.55,0,.1),(.55,1,-.1)):
            with self.assertRaises(AssertionError):f.expected_log_growth(*args)
        for args in ((.55,1001,10),(.55,100,0),(.55,100,101),(.55,True,10)):
            with self.assertRaises(AssertionError):f.loss_run_probability(*args)
        with self.assertRaises(AssertionError):f.wealth_path(100,[-1.01])

    def test_receipt_is_synthetic_and_forged_probabilities_or_account_results_rejected(self):
        p=json.loads((ROOT/'knowledge_base/10_TRADING_PSYCHOLOGY_AND_RISK/risk_arithmetic_20261028.json').read_text())
        d=f.check_receipt(p);self.assertIsNone(d['win_probability'])
        self.assertEqual(d['decision'],'WAIT');self.assertFalse(d['orders_enabled'])
        for key,value in (('win_probability',.92),('orders_enabled',True)):
            q=deepcopy(p);q['diagnostic'][key]=value
            with self.assertRaises(AssertionError):f.check_receipt(q)


if __name__=='__main__':unittest.main()
