"""Causal gap geometry and explicit unknown execution, using actual captures."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import v3_fvg_evidence as f


def receipt():
    return json.loads((ROOT/'knowledge_base/07_FVG_IMBALANCE/fvg_observations_20261028.json').read_text())


class V3FVGTests(unittest.TestCase):
    def test_first_gap_geometry_and_selection_are_causal(self):
        p=receipt();w=f.check_receipt(p,ROOT)
        for entry in p['first_gap_cases']:
            case=entry['diagnostic']['case'];features=case['features'];bars=w[entry['source_window_sha256']]
            i=next(i for i,b in enumerate(bars) if b['time']==features['c']['time'])
            self.assertEqual(f.geometry(bars[:i+1],i),features)
            self.assertEqual(f.first_case(bars[:i+1])['case']['features'],features)
            self.assertIsNone(f.lifecycle(bars[:i+1],i)['outcome'])
            self.assertEqual(features['earliest_after_close'],features['c']['close_time']+1)

    def test_equal_outer_edges_are_not_positive_width_gaps(self):
        bars=[{'time':k*60000,'close_time':(k+1)*60000-1,'open':p,'high':p+1,'low':p-1,'close':p}
              for k,p in enumerate((100,101,102))]
        self.assertIsNone(f.geometry(bars,2))
        bars[2].update(open=102.01,high=103.01,low=101.01,close=102.01)
        self.assertGreater(f.geometry(bars,2)['width'],0)

    def test_far_boundary_has_priority_over_same_bar_rejection(self):
        p=receipt();w=f.check_receipt(p,ROOT);entry=p['first_gap_cases'][0]
        bars=deepcopy(w[entry['source_window_sha256']]);features=entry['diagnostic']['case']['features']
        i=next(i for i,b in enumerate(bars) if b['time']==features['c']['time'])
        # Synthetic future tests lifecycle priority, not an additional real case.
        if features['direction']=='long':
            bars[i+1].update(low=features['low'],high=features['high']+1,close=features['high'])
        else:bars[i+1].update(high=features['high'],low=features['low']-1,close=features['low'])
        out=f.lifecycle(bars,i)['outcome']
        self.assertIsNotNone(out['first_contact'])
        self.assertIsNotNone(out['first_far_boundary_touch_or_breach'])
        self.assertIsNone(out['first_partial_contact_closing_hold'])

    def test_raw_future_change_does_not_imply_fills_or_probability(self):
        p=receipt();f.check_receipt(p,ROOT)
        for entry in p['first_gap_cases']:
            case=entry['diagnostic']['case']
            self.assertEqual(case['features']['decision'],'WAIT')
            self.assertIsNone(case['features']['win_probability'])
            self.assertFalse(case['outcome']['fill_known'])
            self.assertIsNone(case['outcome']['strategy_pnl'])

    def test_source_and_derived_gap_corruption_rejected(self):
        for kind in ('source','geometry','outcome'):
            p=receipt()
            if kind=='source':p['source_file_sha256']='0'*64
            elif kind=='geometry':p['first_gap_cases'][0]['diagnostic']['case']['features']['low']+=1
            else:p['first_gap_cases'][0]['diagnostic']['case']['outcome']['first_contact']=None
            with self.assertRaises(AssertionError):f.check_receipt(p,ROOT)

    def test_inversion_is_known_only_after_first_failure_close(self):
        p=receipt();w=f.check_receipt(p,ROOT)
        for entry in p['inversion_balance_cases'][:2]:
            inv=entry['diagnostic']['inversion'];features=inv['features'];bars=w[entry['source_window_sha256']]
            parent_i=next(i for i,b in enumerate(bars) if b['time']==features['parent']['c']['time'])
            k=next(i for i,b in enumerate(bars) if b['time']==features['failure']['time'])
            self.assertIsNone(f.inversion_case(bars[:k],parent_i)['features'])
            available=f.inversion_case(bars[:k+1],parent_i)
            self.assertEqual(available['features'],features)
            self.assertIsNone(available['outcome'])
            self.assertGreater(inv['outcome']['first_contact']['time'],features['failure']['time'])

    def test_balance_is_positive_opposite_overlap_at_second_confirmation(self):
        p=receipt();w=f.check_receipt(p,ROOT)
        for entry in p['inversion_balance_cases'][:2]:
            bal=entry['diagnostic']['balance'];features=bal['features'];bars=w[entry['source_window_sha256']]
            i=next(i for i,b in enumerate(bars) if b['time']==features['first']['c']['time'])
            k=next(i for i,b in enumerate(bars) if b['time']==features['second']['c']['time'])
            self.assertIsNone(f.balance_case(bars[:k],i)['features'])
            self.assertEqual(f.balance_case(bars[:k+1],i)['features'],features)
            self.assertIsNone(f.balance_case(bars[:k+1],i)['outcome'])
            self.assertTrue(features['forming_bars_shared'])
            self.assertIsNone(features['directional_bias'])
        base={'direction':'long','low':10,'high':12}
        self.assertIsNone(f.intersection(base,{'direction':'short','low':12,'high':14}))
        self.assertIsNone(f.intersection(base,{'direction':'long','low':11,'high':13}))

    def test_absence_is_not_zero_probability_and_inverted_holds_can_fail(self):
        p=receipt();f.check_receipt(p,ROOT)
        cases=[e['diagnostic'] for e in p['inversion_balance_cases']]
        for case in cases[:2]:
            self.assertIsNotNone(case['inversion']['outcome']['first_contact_closing_hold'])
            self.assertIsNotNone(case['inversion']['outcome']['first_invalidating_close'])
            self.assertIsNone(case['inversion']['outcome']['strategy_pnl'])
        self.assertEqual(cases[2]['inversion']['status'],'no_close_failure_within_20_bars')
        self.assertEqual(cases[2]['balance']['status'],'no_opposite_gap_overlap_within_20_bars')
        self.assertIsNone(cases[2]['inversion']['features'])
        p['inversion_balance_cases'][0]['diagnostic']['balance']['features']['low']+=1
        with self.assertRaises(AssertionError):f.check_receipt(p,ROOT)

    def test_quality_baseline_origin_and_first_selection_are_prior_only(self):
        p=receipt();w=f.check_receipt(p,ROOT)
        for entry in p['quality_cases']:
            d=entry['diagnostic'];features=d['case']['features'];bars=w[entry['source_window_sha256']]
            i=next(i for i,b in enumerate(bars) if b['time']==features['gap']['c']['time'])
            self.assertEqual(f.quality_features(bars[:i+1],i),features)
            self.assertIsNone(f.quality_case(bars[:i+1],i)['outcome'])
            self.assertEqual(f.first_quality_case(bars[:i+1])['case']['features'],features)
            self.assertLess(features['baseline_end'],features['gap']['b']['time'])
            self.assertLess(features['origin']['close_time'],features['gap']['b']['time'])
            self.assertGreaterEqual(features['body_multiple'],1.5)
            self.assertFalse(d['first_unfiltered_candidate']['features']['body_gate'])

    def test_gap_wick_close_and_origin_failure_are_distinct(self):
        p=receipt();f.check_receipt(p,ROOT)
        cases=[e['diagnostic']['case'] for e in p['quality_cases']]
        for c in cases:self.assertIsNone(c['features']['gap_origin_positive_intersection'])
        first=cases[0]['outcome']
        self.assertLess(first['first_gap_far_close']['time'],first['first_origin_closing_breach']['time'])
        second=cases[1]['outcome']
        self.assertIsNotNone(second['first_partial_gap_contact_hold_before_far_wick'])
        self.assertLess(second['first_gap_far_wick']['time'],second['first_bar_overlapping_gap_and_origin']['time'])
        self.assertIsNone(second['first_origin_closing_breach'])
        self.assertIsNone(cases[2]['outcome']['first_bar_overlapping_gap_and_origin'])
        self.assertTrue(all(c['outcome']['strategy_pnl'] is None for c in cases))

    def test_zero_body_baseline_is_unknown_not_infinite_confirmation(self):
        bars=[{'time':k*60000,'close_time':(k+1)*60000-1,'open':100,'high':101,'low':99,'close':100} for k in range(22)]
        bars[20].update(open=100,high=106,low=100,close=105)
        bars[21].update(open=105,high=106,low=104,close=105)
        features=f.quality_features(bars,21)
        self.assertIsNone(features['body_multiple'])
        self.assertFalse(features['qualified_formation'])
        p=receipt();p['quality_cases'][0]['diagnostic']['case']['features']['body_multiple']+=1
        with self.assertRaises(AssertionError):f.check_receipt(p,ROOT)

    def test_study_preserves_complete_population_and_window_dependence(self):
        p=receipt();windows=f.check_receipt(p,ROOT)
        for entry in p['studies']:
            s=entry['study'];bars=windows[entry['source_window_sha256']]
            actual=[i for i in range(2,len(bars)) if f.geometry(bars,i) is not None]
            self.assertEqual([x['index'] for x in s['ledger']],actual)
            self.assertEqual(s['strict_gap_count']+s['non_gap_decisions'],len(bars)-2)
            self.assertEqual(s['history_eligible_gap_count']+s['insufficient_warmup_gap_count'],len(actual))
            self.assertEqual(s['qualified_formation_count'],f.first_quality_case(bars)['qualified_count'])
            self.assertGreater(s['overlapping_complete_outcome_pairs'],0)
            self.assertTrue(s['reused_qualified_origin_groups'])
            self.assertFalse(s['independent_holdout'])

    def test_study_features_are_prefix_stable_and_censored_tails_stay_unknown(self):
        p=receipt();windows=f.check_receipt(p,ROOT)
        for entry in p['studies']:
            s=entry['study'];bars=windows[entry['source_window_sha256']]
            for row in s['ledger']:
                i=row['index'];at_confirmation=f.study(bars[:i+1])['ledger'][-1]
                for key in ('features','clock_eligible','quality'):
                    self.assertEqual(at_confirmation[key],row[key])
                self.assertIsNone(at_confirmation['five_bar_outcome'])
                if i+5>=len(bars):
                    self.assertIsNone(row['five_bar_outcome'])
                    self.assertIsNone(row['directional_endpoint_change_pct'])
            self.assertGreater(s['incomplete_five_bar_outcomes'],0)
            self.assertEqual(sum(s['directional_endpoint_sign_counts'].values()),s['complete_five_bar_outcomes'])
            self.assertEqual(s['contact_count']+s['no_contact_count'],s['complete_five_bar_outcomes'])
            self.assertIsNone(s['simulated_trades'])
            self.assertIsNone(s['account_drawdown'])
            self.assertIsNone(s['win_probability'])

    def test_study_rejects_forged_summary_omitted_or_duplicate_windows(self):
        for kind in ('summary','row','omitted','duplicate'):
            p=receipt()
            if kind=='summary':p['studies'][0]['study']['contact_count']+=1
            elif kind=='row':p['studies'][0]['study']['ledger'][0]['features']['low']+=1
            elif kind=='omitted':p['studies'].pop()
            else:p['studies'][2]=deepcopy(p['studies'][0])
            with self.assertRaises(AssertionError):f.check_receipt(p,ROOT)


if __name__=='__main__':unittest.main()
