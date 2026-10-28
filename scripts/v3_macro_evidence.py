"""Bounded original daily macro diagnostics, not causal replay or runtime data.

Current retrieved history can contain revisions. Observation dates are not
original publication/arrival timestamps; unsupported licensed series stay None.
"""
import csv
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
import io
import math

PUBLIC_SERIES={'DTWEXBGS','DCOILWTICO','DGS2','DGS10','DFII10','EFFR'}


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
    return {'method':'hoshi-bounded-public-dollar-oil-context-1',
            'broad_fed_dollar':endpoint_change(captures['DTWEXBGS']),
            'cushing_wti_spot':endpoint_change(captures['DCOILWTICO']),
            'paired_changes':paired_intervals(captures['DTWEXBGS'],captures['DCOILWTICO']),
            'ice_dxy_price_series':None,'gold_benchmark_price_series':None,'equity_benchmark_price_series':None,
            'measured_capital_flows':None,'original_vintage_verified':False,
            'decision':'WAIT','win_probability':None,'orders_enabled':False}


def check_receipt(payload,root=None):
    assert payload['schema_version']=='hoshi-v3-macro-evidence-1'
    assert payload['use']=='bounded-retrospective-source-research-not-runtime-or-training'
    cases=payload['money_flow_cases'];assert len(cases)==3
    assert {c['id'] for c in cases}=={'covid_2020','ukraine_2022','august_2024'}
    for c in cases:assert money_flow_case(c['captures'])==c['diagnostic']
    return cases
