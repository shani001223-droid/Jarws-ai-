"""Source integrity, date alignment and explicitly missing financial evidence."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import v3_macro_evidence as f


def receipt():
    return json.loads((ROOT/'knowledge_base/09_GLOBAL_MONEY_FLOW/macro_observations_20261028.json').read_text())


def changed(c,body):
    c=deepcopy(c);c['response_body']=body;c['source_sha256']=sha256(body.encode()).hexdigest();return c


class V3MacroTests(unittest.TestCase):
    def test_exact_common_intervals_keep_weekends_and_no_forward_fill(self):
        p=receipt();f.check_receipt(p)
        for e in p['money_flow_cases']:
            d=e['diagnostic']['paired_changes']
            self.assertFalse(d['forward_fill_used'])
            self.assertTrue(any(i['calendar_days']==3 for i in d['intervals']))
            self.assertEqual(len(d['intervals']),len(d['common_observation_dates'])-1)
        e=p['money_flow_cases'][0];a=e['captures']['DTWEXBGS'];b=e['captures']['DCOILWTICO']
        lines=b['response_body'].splitlines(keepends=True);del lines[3]
        shorter=f.paired_intervals(a,changed(b,''.join(lines)))
        self.assertEqual(shorter['complete_interval_count'],e['diagnostic']['paired_changes']['complete_interval_count']-1)
        self.assertTrue(any(i['calendar_days']==2 for i in shorter['intervals']))

    def test_missing_endpoint_and_licensed_inputs_are_not_zero_or_aliases(self):
        p=receipt();f.check_receipt(p)
        for e in p['money_flow_cases']:
            d=e['diagnostic']
            for key in ('ice_dxy_price_series','gold_benchmark_price_series','equity_benchmark_price_series','measured_capital_flows','win_probability'):
                self.assertIsNone(d[key])
            self.assertEqual(d['decision'],'WAIT')
            self.assertFalse(d['original_vintage_verified'])
        c=p['money_flow_cases'][0]['captures']['DTWEXBGS'];lines=c['response_body'].splitlines()
        lines[1]=lines[1].split(',')[0]+','
        d=f.endpoint_change(changed(c,'\n'.join(lines)+'\n'))
        self.assertEqual(d['status'],'missing_endpoint');self.assertIsNone(d['arithmetic_change_pct'])

    def test_correlation_known_scale_and_zero_variance_are_distinct(self):
        # Synthetic mathematical fixture, not an additional historical case.
        c=receipt()['money_flow_cases'][0]['captures']['DTWEXBGS']
        dates=['2020-03-09','2020-03-10','2020-03-11','2020-03-12']
        def capture(values,series):
            a=deepcopy(c);a.update(series=series,requested_end=dates[-1])
            a['request_url']=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd={dates[0]}&coed={dates[-1]}'
            return changed(a,'observation_date,'+series+'\n'+''.join(d+','+v+'\n' for d,v in zip(dates,values)))
        a=capture(['100','101','103.02','106.1106'],'DTWEXBGS')
        b=capture(['200','202','206.04','212.2212'],'DCOILWTICO')
        self.assertAlmostEqual(f.paired_intervals(a,b)['pearson_change_correlation'],1)
        flat=capture(['100']*4,'DCOILWTICO')
        self.assertIsNone(f.paired_intervals(a,flat)['pearson_change_correlation'])

    def test_prefix_intervals_do_not_use_future_observations(self):
        e=receipt()['money_flow_cases'][0];captures={}
        end='2020-03-13'
        for key,c in e['captures'].items():
            lines=c['response_body'].splitlines();body=lines[0]+'\n'+''.join(line+'\n' for line in lines[1:] if line.split(',')[0]<=end)
            c=changed(c,body);c['requested_end']=end
            c['request_url']=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={key}&cosd={c["requested_start"]}&coed={end}'
            captures[key]=c
        short=f.money_flow_case(captures)['paired_changes']['intervals']
        self.assertEqual(short,e['diagnostic']['paired_changes']['intervals'][:len(short)])

    def test_rehashed_invalid_dates_nonfinite_and_forged_summary_rejected(self):
        for kind in ('hash','date','duplicate','nan','summary'):
            p=receipt();e=p['money_flow_cases'][0];c=e['captures']['DTWEXBGS']
            if kind=='hash':c['source_sha256']='0'*64
            elif kind=='summary':e['diagnostic']['broad_fed_dollar']['arithmetic_change_pct']+=1
            else:
                lines=c['response_body'].splitlines(keepends=True)
                if kind=='date':lines[1]='2020-03-08,100\n'
                elif kind=='duplicate':lines.insert(2,lines[1])
                else:lines[1]='2020-03-09,NaN\n'
                e['captures']['DTWEXBGS']=changed(c,''.join(lines))
            with self.assertRaises(AssertionError):f.check_receipt(p)

    def test_rate_units_negative_real_yields_and_price_returns_are_separate(self):
        p=receipt();f.check_receipt(p)
        jan=p['rate_cases'][1]['diagnostic']
        self.assertEqual(jan['rates']['DFF']['change_basis_points'],25)
        self.assertEqual(jan['rates']['DFII10']['start_percent'],'-0.69')
        self.assertEqual(jan['rates']['DFII10']['change_basis_points'],-3)
        for e in p['rate_cases']:
            for r in e['diagnostic']['rates'].values():
                self.assertIsNone(r['bond_price_return'])
                self.assertIsNone(r['original_publication_and_arrival_times'])

    def test_policy_cut_and_observed_long_yield_need_not_share_direction(self):
        p=receipt();f.check_receipt(p)
        d=p['rate_cases'][2]['diagnostic']
        self.assertEqual(d['rates']['DFF']['change_basis_points'],-50)
        self.assertEqual(d['rates']['DGS10']['change_basis_points'],8)
        self.assertEqual(d['spreads']['ten_minus_two_bp'],{'start':6.0,'end':18.0,'change_bp':12.0})
        self.assertFalse(d['causal_policy_effect_estimated'])
        self.assertFalse(d['nominal_real_spread_is_pure_inflation_expectation'])

    def test_rate_missing_observation_never_fills_an_inflation_spread(self):
        e=deepcopy(receipt()['rate_cases'][0]);c=e['captures']['DFII10']
        lines=c['response_body'].splitlines();lines[-1]=lines[-1].split(',')[0]+','
        e['captures']['DFII10']=changed(c,'\n'.join(lines)+'\n')
        d=f.rate_case(e['captures'],e['announcement'])
        self.assertIsNone(d['rates']['DFII10']['change_basis_points'])
        self.assertIsNone(d['spreads']['nominal_minus_real_ten_bp']['end'])
        self.assertEqual(d['decision'],'WAIT')

    def test_release_clock_target_and_series_alias_tampering_rejected(self):
        for kind in ('time','target','series','omitted'):
            p=receipt();e=p['rate_cases'][0]
            if kind=='time':e['announcement']['release_time']='2020-03-15T17:00:00+00:00'
            elif kind=='target':e['announcement']['target_range_percent']=[0.25,0.50]
            elif kind=='series':e['captures']['DGS2']=deepcopy(e['captures']['DGS10'])
            else:p['rate_cases'].pop()
            with self.assertRaises(AssertionError):f.check_receipt(p)


if __name__=='__main__':unittest.main()
