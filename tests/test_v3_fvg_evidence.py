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


if __name__=='__main__':unittest.main()
