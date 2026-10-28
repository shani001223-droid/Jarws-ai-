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


class V3COTTests(unittest.TestCase):
    def test_actual_accounting_changes_do_not_become_capital_flow(self):
        p=receipt();f.check_receipt(p)
        a=p['cot_cases'][0]['diagnostic'];b=p['cot_cases'][2]['diagnostic']
        self.assertEqual(a['weekly_change_contracts']['noncommercial_net_contracts'],-20202)
        self.assertEqual(b['weekly_change_contracts']['noncommercial_net_contracts'],-7852)
        for e in p['cot_cases']:
            d=e['diagnostic']
            for row in d['observations']:
                self.assertEqual(row['noncommercial_net_contracts']+row['commercial_net_contracts']+row['nonreportable_net_contracts'],0)
            self.assertIsNone(d['capital_inflow_dollars']);self.assertIsNone(d['gold_price_reaction_or_trade_return'])

    def test_documented_ion_delay_is_not_the_normal_friday_schedule(self):
        d=receipt()['cot_cases'][1]['diagnostic']
        self.assertEqual(d['documented_asof_to_publication_calendar_days'],24)
        self.assertEqual(d['documented_delay_from_normal_schedule_calendar_days'],21)
        self.assertEqual(d['weekly_change_contracts']['noncommercial_net_contracts'],2608)
        self.assertIsNone(d['first_publication_time_and_arrival'])
        self.assertFalse(d['original_vintage_verified'])

    def test_unknown_release_and_long_term_extremes_stay_unknown(self):
        p=receipt();f.check_receipt(p)
        for e in p['cot_cases']:
            d=e['diagnostic'];self.assertIsNone(d['long_term_extreme_percentile'])
            self.assertEqual(d['decision'],'WAIT');self.assertIsNone(d['win_probability']);self.assertFalse(d['orders_enabled'])
        for k in (0,2):
            d=p['cot_cases'][k]['diagnostic']
            self.assertIsNone(d['publication']['documented_publication_date'])
            self.assertIsNone(d['documented_asof_to_publication_calendar_days'])

    def test_zero_open_interest_is_not_a_zero_percentile(self):
        c=deepcopy(receipt()['cot_cases'][0]['capture']);rows=json.loads(c['response_body'])
        for row in rows:
            for key in f.COT_FIELDS[4:]:row[key]='0'
        d=f.cot_capture(changed(c,json.dumps(rows)))
        self.assertTrue(all(r['noncommercial_net_pct_of_open_interest'] is None for r in d))

    def test_wrong_family_market_schema_and_position_labels_rejected(self):
        for key,value in (('futonly_or_combined','Combined'),('cftc_contract_market_code','088692'),
                          ('market_and_exchange_names','XAUUSD SPOT'),('report_date_as_yyyy_mm_dd','2020-03-04T00:00:00.000')):
            c=receipt()['cot_cases'][0]['capture'];rows=json.loads(c['response_body']);rows[0][key]=value
            with self.assertRaises(AssertionError):f.cot_capture(changed(c,json.dumps(rows)))
        c=receipt()['cot_cases'][0]['capture'];rows=json.loads(c['response_body']);del rows[0]['noncomm_positions_short_all']
        with self.assertRaises(AssertionError):f.cot_capture(changed(c,json.dumps(rows)))

    def test_negative_fractional_or_unbalanced_contracts_rejected(self):
        for value in ('-1','1.5','NaN','366174'):
            c=receipt()['cot_cases'][0]['capture'];rows=json.loads(c['response_body'])
            rows[0]['noncomm_positions_long_all']=value
            with self.assertRaises(AssertionError):f.cot_capture(changed(c,json.dumps(rows)))

    def test_source_hash_query_and_forged_diagnostic_rejected(self):
        for kind in ('hash','url','duplicate','summary','release'):
            p=receipt();e=p['cot_cases'][0];c=e['capture']
            if kind=='hash':c['source_sha256']='0'*64
            elif kind=='url':c['request_url']=c['request_url'].replace('6dca-aqww','kh3c-gbw2')
            elif kind=='duplicate':
                rows=json.loads(c['response_body']);e['capture']=changed(c,json.dumps([rows[0],rows[0]]))
            elif kind=='summary':e['diagnostic']['weekly_change_contracts']['noncommercial_net_contracts']+=1
            else:e['publication']['documented_publication_date']='2020-03-13'
            with self.assertRaises(AssertionError):f.check_receipt(p)


class V3BTCCorrelationTests(unittest.TestCase):
    def test_actual_endpoint_changes_are_not_win_probabilities(self):
        p=receipt();f.check_receipt(p)
        cases=p['btc_cases']
        self.assertAlmostEqual(cases[0]['diagnostic']['btc_spot_usdt']['arithmetic_close_change_pct'],-21.70918312658341)
        self.assertAlmostEqual(cases[1]['diagnostic']['btc_spot_usdt']['arithmetic_close_change_pct'],3.974817724881148)
        for e in cases:
            d=e['diagnostic']
            self.assertEqual(d['decision'],'WAIT');self.assertIsNone(d['win_probability']);self.assertFalse(d['orders_enabled'])
            self.assertIsNone(d['equity_benchmark_correlation']);self.assertIsNone(d['gold_benchmark_correlation'])
            self.assertFalse(d['same_instant_observations']);self.assertFalse(d['structural_regime_change_tested'])

    def test_three_calendar_day_interval_uses_same_btc_endpoints(self):
        from decimal import Decimal
        d=receipt()['btc_cases'][2]['diagnostic']['btc_vs_broad_dollar']
        i=next(v for v in d['intervals'] if v['start_date']=='2024-08-02')
        self.assertEqual(i['end_date'],'2024-08-05');self.assertEqual(i['calendar_days'],3)
        c=receipt()['btc_cases'][2]['capture'];prices=f.crypto_capture(c)
        expected=float((prices['2024-08-05']/prices['2024-08-02']-Decimal(1))*100)
        self.assertEqual(i['first_change_pct'],expected)
        self.assertEqual(d['complete_interval_count'],5)
        self.assertNotIn('2024-08-03',d['common_observation_dates'])
        self.assertFalse(d['forward_fill_used'])

    def test_prefix_pairing_cannot_see_later_btc_closes(self):
        e=receipt()['btc_cases'][0];prices=f.crypto_capture(e['capture'])
        macro=f.check_capture(receipt()['money_flow_cases'][0]['captures']['DTWEXBGS'])
        short={k:v for k,v in prices.items() if k<='2020-03-13'}
        a=f.paired_daily_values(short,macro)['intervals']
        b=f.paired_daily_values(prices,macro)['intervals']
        self.assertEqual(a,b[:len(a)])

    def test_timestamp_units_ohlc_and_date_corruption_rejected(self):
        for kind in ('unit','close_clock','price','duplicate'):
            c=receipt()['btc_cases'][0]['capture'];rows=json.loads(c['response_body'])
            if kind=='unit':rows[0][0]*=1000;rows[0][6]*=1000
            elif kind=='close_clock':rows[0][6]+=1
            elif kind=='price':rows[0][4]='0'
            else:rows[1]=rows[0]
            with self.assertRaises(AssertionError):f.crypto_capture(changed(c,json.dumps(rows)))

    def test_quote_venue_hash_and_comparison_alias_rejected(self):
        for kind in ('quote','venue','hash','macro','summary'):
            p=receipt();e=p['btc_cases'][0];c=e['capture']
            if kind=='quote':c['symbol']='BTCUSD'
            elif kind=='venue':c['venue']='Binance Futures'
            elif kind=='hash':c['source_sha256']='0'*64
            elif kind=='macro':c['requested_start']='2020-03-08'
            else:e['diagnostic']['btc_vs_broad_dollar']['pearson_change_correlation']=0.99
            with self.assertRaises(AssertionError):f.check_receipt(p)

    def test_positive_endpoint_paths_do_not_imply_positive_interval_correlation(self):
        p=receipt();f.check_receipt(p)
        b=p['btc_cases'][1]['diagnostic'];m=p['money_flow_cases'][1]['diagnostic']
        self.assertGreater(b['btc_spot_usdt']['arithmetic_close_change_pct'],0)
        self.assertGreater(m['broad_fed_dollar']['arithmetic_change_pct'],0)
        self.assertLess(b['btc_vs_broad_dollar']['pearson_change_correlation'],0)
        self.assertFalse(b['independent_holdout']);self.assertFalse(b['causal_effect_estimated'])


if __name__=='__main__':unittest.main()
