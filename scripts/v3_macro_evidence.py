"""Bounded original daily macro diagnostics, not causal replay or runtime data.

Current retrieved history can contain revisions. Observation dates are not
original publication/arrival timestamps; unsupported licensed series stay None.
"""
import csv
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
import io
import json
import re
from urllib.parse import urlencode
import math

PUBLIC_SERIES={'DTWEXBGS','DCOILWTICO','DGS2','DGS10','DFII10','DFF'}
POLICY_RELEASES={
    'emergency_cut_2020':('2020-03-15T17:00:00-04:00',[0,0.25],'20200315'),
    'liftoff_2022':('2022-03-16T14:00:00-04:00',[0.25,0.5],'20220316'),
    'large_cut_2024':('2024-09-18T14:00:00-04:00',[4.75,5.0],'20240918'),
}


def check_capture(c):
    series=c['series'];assert series in PUBLIC_SERIES
    start=date.fromisoformat(c['requested_start']);end=date.fromisoformat(c['requested_end'])
    assert start<=end and c['http_status']==200
    assert c['request_url']==f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd={start}&coed={end}'
    body=c['response_body'];assert len(body.encode())<200000
    assert sha256(body.encode()).hexdigest()==c['source_sha256']
    captured=datetime.fromisoformat(c['captured_at_utc']);assert captured.utcoffset() is not None
    assert captured.date()>=end
    rows=list(csv.reader(io.StringIO(body)))
    assert rows and rows[0] in (['observation_date',series],['DATE',series])
    result={};previous=None
    for row in rows[1:]:
        assert len(row)==2
        day=date.fromisoformat(row[0]);assert start<=day<=end and (previous is None or day>previous)
        value=None if row[1] in ('','.') else Decimal(row[1])
        assert value is None or value.is_finite()
        result[day.isoformat()]=value;previous=day
    assert result
    return result


def endpoint_change(c):
    values=check_capture(c);a=values.get(c['requested_start']);b=values.get(c['requested_end'])
    status='missing_endpoint' if a is None or b is None else 'nonpositive_base' if a<=0 else 'observed'
    return {'start_date':c['requested_start'],'end_date':c['requested_end'],
            'start_value':str(a) if a is not None else None,'end_value':str(b) if b is not None else None,
            'status':status,'arithmetic_change_pct':float((b/a-1)*100) if status=='observed' else None,
            'same_instant_prices':False,'original_publication_and_arrival_times':None}


def paired_intervals(first,second):
    left=check_capture(first);right=check_capture(second)
    assert first['requested_start']==second['requested_start'] and first['requested_end']==second['requested_end']
    dates=sorted(d for d in set(left)&set(right) if left[d] is not None and right[d] is not None)
    intervals=[]
    for a,b in zip(dates,dates[1:]):
        x=(left[b]/left[a]-1)*100 if left[a]>0 else None
        y=(right[b]/right[a]-1)*100 if right[a]>0 else None
        intervals.append({'start_date':a,'end_date':b,'calendar_days':(date.fromisoformat(b)-date.fromisoformat(a)).days,
                          'first_change_pct':float(x) if x is not None else None,
                          'second_change_pct':float(y) if y is not None else None})
    complete=[r for r in intervals if r['first_change_pct'] is not None and r['second_change_pct'] is not None]
    corr=None
    if len(complete)>=3:
        x=[r['first_change_pct'] for r in complete];y=[r['second_change_pct'] for r in complete]
        mx=math.fsum(x)/len(x);my=math.fsum(y)/len(y)
        xx=math.fsum((v-mx)**2 for v in x);yy=math.fsum((v-my)**2 for v in y)
        if xx>0 and yy>0:corr=math.fsum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(xx*yy)
    return {'method':'hoshi-common-date-arithmetic-interval-correlation-1','common_observation_dates':dates,
            'intervals':intervals,'complete_interval_count':len(complete),'pearson_change_correlation':corr,
            'forward_fill_used':False,'synchronized_intraday_prices':False,'independent_holdout':False}


def money_flow_case(captures):
    assert set(captures)=={'DTWEXBGS','DCOILWTICO'}
    assert all(c['series']==key for key,c in captures.items())
    return {'method':'hoshi-bounded-public-dollar-oil-context-1',
            'broad_fed_dollar':endpoint_change(captures['DTWEXBGS']),
            'cushing_wti_spot':endpoint_change(captures['DCOILWTICO']),
            'paired_changes':paired_intervals(captures['DTWEXBGS'],captures['DCOILWTICO']),
            'ice_dxy_price_series':None,'gold_benchmark_price_series':None,'equity_benchmark_price_series':None,
            'measured_capital_flows':None,'original_vintage_verified':False,
            'decision':'WAIT','win_probability':None,'orders_enabled':False}


def rate_endpoint(c):
    values=check_capture(c);a=values.get(c['requested_start']);b=values.get(c['requested_end'])
    return {'start_date':c['requested_start'],'end_date':c['requested_end'],
            'start_percent':str(a) if a is not None else None,'end_percent':str(b) if b is not None else None,
            'change_basis_points':float((b-a)*100) if a is not None and b is not None else None,
            'bond_price_return':None,'original_publication_and_arrival_times':None}


def rate_case(captures,announcement):
    assert set(captures)=={'DGS2','DGS10','DFII10','DFF'}
    assert all(c['series']==key for key,c in captures.items())
    starts={c['requested_start'] for c in captures.values()};ends={c['requested_end'] for c in captures.values()}
    assert len(starts)==len(ends)==1
    dt=datetime.fromisoformat(announcement['release_time']);assert dt.utcoffset() is not None
    assert next(iter(starts))<dt.date().isoformat()<next(iter(ends))
    levels={k:rate_endpoint(c) for k,c in captures.items()}
    spreads={}
    for key,a,b in (('ten_minus_two_bp','DGS10','DGS2'),('nominal_minus_real_ten_bp','DGS10','DFII10')):
        av=check_capture(captures[a]);bv=check_capture(captures[b])
        spread=lambda d:float((av[d]-bv[d])*100) if av.get(d) is not None and bv.get(d) is not None else None
        start=spread(next(iter(starts)));end=spread(next(iter(ends)))
        spreads[key]={'start':start,'end':end,'change_bp':end-start if start is not None and end is not None else None}
    return {'method':'hoshi-rate-level-and-spread-changes-1','announcement':announcement,
            'rates':levels,'spreads':spreads,'same_instant_intraday_observations':False,
            'nominal_real_spread_is_pure_inflation_expectation':False,'original_vintage_verified':False,
            'causal_policy_effect_estimated':False,'decision':'WAIT','win_probability':None,'orders_enabled':False}


COT_FIELDS=(
    'market_and_exchange_names','report_date_as_yyyy_mm_dd','cftc_contract_market_code',
    'futonly_or_combined','open_interest_all','noncomm_positions_long_all',
    'noncomm_positions_short_all','noncomm_postions_spread_all','comm_positions_long_all',
    'comm_positions_short_all','nonrept_positions_long_all','nonrept_positions_short_all',
)
COT_PUBLICATION_SOURCE='https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm'
COT_WINDOWS={
    'march_2020':('2020-03-03','2020-03-10','2020-03-13',None),
    'ion_2023':('2023-01-24','2023-01-31','2023-02-03','2023-02-24'),
    'august_2024':('2024-07-30','2024-08-06','2024-08-09',None),
}


def cot_query(start,end):
    params={'$select':','.join(COT_FIELDS),
            '$where':f"cftc_contract_market_code='088691' AND report_date_as_yyyy_mm_dd between '{start}T00:00:00' and '{end}T23:59:59'",
            '$order':'report_date_as_yyyy_mm_dd','$limit':'10'}
    return 'https://publicreporting.cftc.gov/resource/6dca-aqww.json?'+urlencode(params)


def cot_capture(c):
    assert c['dataset_id']=='6dca-aqww' and c['report_family']=='legacy-futures-only'
    assert c['contract_market_code']=='088691' and c['http_status']==200
    start=date.fromisoformat(c['requested_start']);end=date.fromisoformat(c['requested_end'])
    assert (end-start).days==7 and start.weekday()==end.weekday()==1
    assert c['request_url']==cot_query(start.isoformat(),end.isoformat())
    captured=datetime.fromisoformat(c['captured_at_utc']);assert captured.utcoffset() is not None
    assert captured.date()>end
    body=c['response_body'];assert len(body.encode())<200000
    assert sha256(body.encode()).hexdigest()==c['source_sha256']
    rows=json.loads(body);assert isinstance(rows,list) and len(rows)==2
    result=[]
    for row,day in zip(rows,(start,end)):
        assert set(row)==set(COT_FIELDS)
        assert row['report_date_as_yyyy_mm_dd']==day.isoformat()+'T00:00:00.000'
        assert row['market_and_exchange_names']=='GOLD - COMMODITY EXCHANGE INC.'
        assert row['cftc_contract_market_code']=='088691' and row['futonly_or_combined']=='FutOnly'
        counts={}
        for key in COT_FIELDS[4:]:
            assert isinstance(row[key],str) and re.fullmatch(r'[0-9]+',row[key])
            counts[key]=int(row[key])
        oi=counts['open_interest_all'];long=counts['noncomm_positions_long_all'];short=counts['noncomm_positions_short_all']
        spread=counts['noncomm_postions_spread_all'];cl=counts['comm_positions_long_all'];cs=counts['comm_positions_short_all']
        nl=counts['nonrept_positions_long_all'];ns=counts['nonrept_positions_short_all']
        assert long+spread+cl+nl==short+spread+cs+ns==oi
        result.append({'position_date':day.isoformat(),'open_interest_contracts':oi,
                       'noncommercial_long_contracts':long,'noncommercial_short_contracts':short,
                       'noncommercial_spreading_contracts':spread,'noncommercial_net_contracts':long-short,
                       'noncommercial_net_pct_of_open_interest':float(Decimal(long-short)/oi*100) if oi else None,
                       'commercial_net_contracts':cl-cs,'nonreportable_net_contracts':nl-ns,
                       'long_short_open_interest_reconciled':True})
    return result


def cot_case(c,publication):
    rows=cot_capture(c);before,after=rows
    assert publication['timezone']=='America/New_York'
    expected=date.fromisoformat(publication['normally_expected_publication_date'])
    asof=date.fromisoformat(after['position_date']);assert (expected-asof).days==3
    actual=publication['documented_publication_date']
    age=delay=None
    if actual is not None:
        actual=date.fromisoformat(actual);assert actual>=expected
        assert publication['source_url']==COT_PUBLICATION_SOURCE
        age=(actual-asof).days;delay=(actual-expected).days
    else:assert publication['source_url'] is None
    return {'method':'hoshi-legacy-gold-position-accounting-and-release-lag-1','observations':rows,
            'weekly_change_contracts':{key:after[key]-before[key] for key in (
                'open_interest_contracts','noncommercial_long_contracts','noncommercial_short_contracts',
                'noncommercial_spreading_contracts','noncommercial_net_contracts')},
            'publication':publication,'documented_asof_to_publication_calendar_days':age,
            'documented_delay_from_normal_schedule_calendar_days':delay,
            'first_publication_time_and_arrival':None,'original_vintage_verified':False,
            'position_date_is_price_timestamp':False,'long_term_extreme_percentile':None,
            'gold_price_reaction_or_trade_return':None,'capital_inflow_dollars':None,
            'decision':'WAIT','win_probability':None,'orders_enabled':False}


def check_receipt(payload,root=None):
    assert payload['schema_version']=='hoshi-v3-macro-evidence-1'
    assert payload['use']=='bounded-retrospective-source-research-not-runtime-or-training'
    cases=payload['money_flow_cases'];assert len(cases)==3
    assert {c['id'] for c in cases}=={'covid_2020','ukraine_2022','august_2024'}
    for c in cases:assert money_flow_case(c['captures'])==c['diagnostic']
    if 'rate_cases' in payload:
        entries=payload['rate_cases'];assert len(entries)==3
        assert {e['id'] for e in entries}==set(POLICY_RELEASES)
        for e in entries:
            stamp,target,suffix=POLICY_RELEASES[e['id']];a=e['announcement']
            assert a['release_time']==stamp and a['target_range_percent']==target
            assert a['timezone']=='America/New_York'
            assert a['source_url']==f'https://www.federalreserve.gov/newsevents/pressreleases/monetary{suffix}a.htm'
            assert rate_case(e['captures'],a)==e['diagnostic']
    if 'cot_cases' in payload:
        entries=payload['cot_cases'];assert len(entries)==3
        assert {e['id'] for e in entries}==set(COT_WINDOWS)
        for e in entries:
            start,end,expected,actual=COT_WINDOWS[e['id']];c=e['capture'];p=e['publication']
            assert c['requested_start']==start and c['requested_end']==end
            assert p['normally_expected_publication_date']==expected and p['documented_publication_date']==actual
            assert cot_case(c,p)==e['diagnostic']
    return cases
