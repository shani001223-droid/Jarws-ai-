"""Original offline indicator arithmetic; no vendor parity or trading runtime.

Finite captured history is explicitly seeded. Unavailable warmup and flat
oscillator denominators remain None instead of becoming fake signals.
"""
from hashlib import sha256
import json
import math

from v3_ict_evidence import check_receipt as check_source, record

SOURCE='knowledge_base/05_ICT_COMPLETE/ict_intraday_observations_20261028.json'


def smoothing(values,period,alpha=None):
    assert isinstance(period,int) and not isinstance(period,bool) and period>=2
    assert all(isinstance(x,(float,int)) and math.isfinite(x) for x in values)
    out=[None]*len(values)
    if len(values)<period:return out
    a=2/(period+1) if alpha is None else alpha
    assert 0<a<=1
    out[period-1]=math.fsum(values[:period])/period
    for i in range(period,len(values)):
        out[i]=a*values[i]+(1-a)*out[i-1]
    return out


def rsi(values,period=14):
    assert isinstance(period,int) and not isinstance(period,bool) and period>=2
    assert all(isinstance(x,(float,int)) and math.isfinite(x) for x in values)
    changes=[b-a for a,b in zip(values,values[1:])]
    gain=smoothing([max(x,0) for x in changes],period,1/period)
    loss=smoothing([max(-x,0) for x in changes],period,1/period)
    return [None]+[100*g/(g+l) if g is not None and g+l>0 else None for g,l in zip(gain,loss)] if values else []


def snapshot(bars,index,seed_start=0):
    assert 0<=seed_start<=index<len(bars)
    local=bars[seed_start:index+1];closes=[b['close'] for b in local]
    if len(local)<34:return None
    assert all(c>0 and math.isfinite(c) for c in closes)
    fast=smoothing(closes,12);slow=smoothing(closes,26)
    macd=[fast[i]-slow[i] for i in range(25,len(closes))]
    signal=smoothing(macd,9)[-1]
    sma=math.fsum(closes[-20:])/20
    sigma=math.sqrt(math.fsum((c-sma)**2 for c in closes[-20:])/20)
    recent=local[-14:];hi=max(b['high'] for b in recent);lo=min(b['low'] for b in recent)
    tr=[max(b['high']-b['low'],abs(b['high']-a['close']),abs(b['low']-a['close'])) for a,b in zip(local,local[1:])]
    value=rsi(closes)[-1]
    return {'method':'hoshi-finite-seed-indicator-snapshot-1','bar':record(bars[index]),
            'seed_start':local[0]['time'],'seed_bars':len(local),
            'sma20':sma,'ema20':smoothing(closes,20)[-1],
            'rsi14':value,'rsi_state':'flat_or_unavailable' if value is None else 'above_70' if value>70 else 'below_30' if value<30 else 'between_30_and_70',
            'macd12_26':macd[-1],'signal9':signal,'histogram':macd[-1]-signal,
            'atr14':smoothing(tr,14,1/14)[-1],
            'stochastic_fast_k14':100*(closes[-1]-lo)/(hi-lo) if hi>lo else None,
            'roc12_pct':(closes[-1]/closes[-13]-1)*100,
            'band20_population_sigma':sigma,'band20_lower':sma-2*sigma,'band20_upper':sma+2*sigma,
            'earliest_after_close':bars[index]['close_time']+1,'provider_arrival_time':None,
            'vendor_parity_validated':False,'decision':'WAIT','win_probability':None,'orders_enabled':False}


def fixed_case(bars):
    index=60
    assert len(bars)>index
    future=bars[index+1:index+6]
    out=None
    if len(future)==5:
        out={'horizon_bars':5,'available_at':future[-1]['close_time']+1,
             'path':[record(b) for b in future],
             'raw_close_change_pct':(future[-1]['close']/bars[index]['close']-1)*100,
             'fill_known':False,'strategy_pnl':None}
    return {'selection':'fixed_zero_based_index_60_without_indicator_or_outcome_filter',
            'features':snapshot(bars,index),'shorter_history_same_instant':snapshot(bars,index,20),
            'outcome':out,'independent_holdout':False}


def check_receipt(payload,root):
    assert payload['schema_version']=='hoshi-v3-indicator-evidence-1'
    assert payload['data_license']=='CC BY-NC-SA 4.0' and payload['source_file']==SOURCE
    raw=(root/SOURCE).read_bytes()
    assert sha256(raw).hexdigest()==payload['source_file_sha256']
    source=json.loads(raw);checked=check_source(source,root)
    windows={entry['source_sha256']:bars for entry,bars in zip(source['observations'],checked)}
    cases=payload['momentum_cases']
    assert len(cases)==len(windows)
    assert {e['source_window_sha256'] for e in cases}==set(windows)
    for entry in cases:assert fixed_case(windows[entry['source_window_sha256']])==entry['diagnostic']
    return windows
