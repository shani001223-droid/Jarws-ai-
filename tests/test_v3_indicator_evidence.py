"""Closed-bar causality, warmup, scaling and finite-history dependence."""
from copy import deepcopy
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import v3_indicator_evidence as f


def receipt():
    return json.loads((ROOT/'knowledge_base/08_INDICATORS_AND_ORDERFLOW/indicator_observations_20261028.json').read_text())


class V3IndicatorTests(unittest.TestCase):
    def test_seed_arithmetic_and_flat_or_one_sided_oscillators(self):
        self.assertEqual(f.smoothing([1,2,3,4],3),[None,None,2,3])
        self.assertAlmostEqual(f.smoothing([1,2,3,4],3,1/3)[-1],8/3)
        self.assertEqual(f.rsi(list(range(1,31)))[-1],100)
        self.assertEqual(f.rsi(list(range(31,1,-1)))[-1],0)
        self.assertTrue(all(v is None for v in f.rsi([100]*30)))
        with self.assertRaises(AssertionError):f.smoothing([1,float('nan')],2)

    def test_snapshot_is_prefix_stable_and_future_path_is_separate(self):
        p=receipt();windows=f.check_receipt(p,ROOT)
        for e in p['momentum_cases']:
            bars=windows[e['source_window_sha256']];d=e['diagnostic']
            self.assertEqual(f.fixed_case(bars[:61])['features'],d['features'])
            self.assertIsNone(f.fixed_case(bars[:61])['outcome'])
            mutated=deepcopy(bars)
            for b in mutated[61:]:b.update(open=1,high=1,low=1,close=1)
            self.assertEqual(f.fixed_case(mutated)['features'],d['features'])
            self.assertEqual(d['features']['earliest_after_close'],bars[60]['close_time']+1)
            self.assertFalse(d['independent_holdout'])
            self.assertIsNone(d['outcome']['strategy_pnl'])

    def test_finite_history_can_change_signal_while_rolling_windows_agree(self):
        p=receipt();f.check_receipt(p,ROOT)
        for e in p['momentum_cases']:
            a=e['diagnostic']['features'];b=e['diagnostic']['shorter_history_same_instant']
            self.assertEqual(a['bar'],b['bar'])
            for key in ('sma20','stochastic_fast_k14','roc12_pct','band20_population_sigma'):
                self.assertEqual(a[key],b[key])
            self.assertNotEqual(a['rsi14'],b['rsi14'])
            self.assertNotEqual(a['ema20'],b['ema20'])
            self.assertIsNone(a['win_probability'])
            self.assertEqual(a['decision'],'WAIT')
        d=p['momentum_cases'][0]['diagnostic']
        self.assertGreater(d['features']['histogram'],0)
        self.assertLess(d['shorter_history_same_instant']['histogram'],0)

    def test_scale_invariance_and_warmup_or_flat_denominators(self):
        p=receipt();windows=f.check_receipt(p,ROOT);bars=next(iter(windows.values()))
        scaled=deepcopy(bars)
        for b in scaled:
            for key in ('open','high','low','close'):b[key]*=10
        a=f.snapshot(bars,60);b=f.snapshot(scaled,60)
        for key in ('rsi14','stochastic_fast_k14','roc12_pct'):self.assertAlmostEqual(a[key],b[key])
        for key in ('sma20','ema20','macd12_26','atr14'):self.assertAlmostEqual(a[key]*10,b[key])
        self.assertIsNone(f.snapshot(bars,32))
        flat=deepcopy(bars)
        for bar in flat:bar.update(open=100,high=100,low=100,close=100)
        d=f.snapshot(flat,60)
        self.assertIsNone(d['rsi14']);self.assertIsNone(d['stochastic_fast_k14'])
        self.assertEqual(d['atr14'],0);self.assertEqual(d['band20_population_sigma'],0)

    def test_hash_features_outcomes_and_population_corruption_rejected(self):
        for kind in ('source','features','outcome','omitted','duplicate'):
            p=receipt()
            if kind=='source':p['source_file_sha256']='0'*64
            elif kind=='features':p['momentum_cases'][0]['diagnostic']['features']['rsi14']+=1
            elif kind=='outcome':p['momentum_cases'][0]['diagnostic']['outcome']['raw_close_change_pct']+=1
            elif kind=='omitted':p['momentum_cases'].pop()
            else:p['momentum_cases'][2]=deepcopy(p['momentum_cases'][0])
            with self.assertRaises(AssertionError):f.check_receipt(p,ROOT)

    def test_trade_profiles_conserve_base_volume_but_rebinning_changes_poc(self):
        p=receipt();f.check_receipt(p,ROOT)
        for e in p['volume_cases']:
            d=e['diagnostic'];a=d['profile_1_usdt'];b=d['profile_5_usdt']
            for profile in (a,b):
                self.assertEqual(sum((D(r['base_volume']) for r in profile['bins']),D(0)),D(d['minute_base_volume']))
                self.assertGreaterEqual(D(profile['value_area_volume_pct']),70)
                self.assertLessEqual(D(profile['value_area_volume_pct']),100)
            self.assertGreater(a['occupied_bins'],b['occupied_bins'])
            self.assertFalse(d['session_profile_available'])
            self.assertFalse(d['archive_whole_file_rechecked_offline'])
        d=p['volume_cases'][2]['diagnostic']
        self.assertFalse(D(d['profile_5_usdt']['poc_low_inclusive'])<=D(d['profile_1_usdt']['poc_low_inclusive'])<D(d['profile_5_usdt']['poc_high_exclusive']))

    def test_anchor_choice_can_reverse_relative_price_label_and_proxy_is_distinct(self):
        p=receipt();windows=f.check_receipt(p,ROOT)
        e=p['volume_cases'][1];d=e['diagnostic'];close=D(str(windows[e['source_window_sha256']][60]['close']))
        self.assertGreater(close,D(d['capture_anchor']['quote_divided_by_base_vwap']))
        self.assertLess(close,D(d['later_clock_anchor']['quote_divided_by_base_vwap']))
        for e in p['volume_cases']:
            for key in ('capture_anchor','later_clock_anchor'):
                a=e['diagnostic'][key]
                self.assertNotEqual(a['quote_divided_by_base_vwap'],a['hlc3_bar_proxy'])
            self.assertEqual(e['diagnostic']['earliest_after_close'],e['aggregate_capture']['end_exclusive_ms'])
            self.assertEqual(e['diagnostic']['decision'],'WAIT')

    def test_profile_exact_edges_ties_and_overshoot_are_declared(self):
        trades=[{'price':D(100),'quantity':D(2)},{'price':D(105),'quantity':D(4)}]
        p=f.profile(trades,'5')
        self.assertEqual(p['poc_low_inclusive'],'105')
        self.assertEqual(p['value_area_volume_pct'],'100')
        tied=f.profile([{'price':D(100),'quantity':D(1)},{'price':D(101),'quantity':D(1)}],'1')
        self.assertEqual(tied['poc_tied_low_boundaries'],['100','101'])
        self.assertEqual(tied['poc_low_inclusive'],'100')
        with self.assertRaises(AssertionError):f.profile(trades,'0')

    def test_aggregate_omissions_native_mismatch_and_forged_profile_rejected(self):
        for kind in ('missing_trade','native_mismatch','profile','missing_window','duplicate_window'):
            p=receipt();e=p['volume_cases'][0];a=e['aggregate_capture']
            if kind=='missing_trade':
                lines=a['response_body'].splitlines(keepends=True);lines.pop(20);a['response_body']=''.join(lines)
                a['subset_rows']-=1;a['subset_sha256']=sha256(a['response_body'].encode()).hexdigest()
            elif kind=='native_mismatch':
                # Rehashed but altered quantity must still fail native-minute reconciliation.
                lines=a['response_body'].splitlines(keepends=True);fields=lines[0].strip().split(',')
                fields[2]='999';lines[0]=','.join(fields)+'\n';a['response_body']=''.join(lines)
                a['subset_sha256']=sha256(a['response_body'].encode()).hexdigest()
            elif kind=='profile':e['diagnostic']['profile_1_usdt']['poc_low_inclusive']='1'
            elif kind=='missing_window':p['volume_cases'].pop()
            else:p['volume_cases'][2]=deepcopy(p['volume_cases'][0])
            with self.assertRaises(AssertionError):f.check_receipt(p,ROOT)


if __name__=='__main__':unittest.main()
