"""Closed-bar causality, warmup, scaling and finite-history dependence."""
from copy import deepcopy
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


if __name__=='__main__':unittest.main()
