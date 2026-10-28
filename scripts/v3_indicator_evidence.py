"""Original offline indicator arithmetic; no vendor parity or trading runtime.

Finite captured history is explicitly seeded. Unavailable warmup and flat
oscillator denominators remain None instead of becoming fake signals.
"""
from hashlib import sha256
import csv
from decimal import Decimal as D, ROUND_FLOOR
from datetime import datetime, timezone
import io
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


def parse_aggregate_csv(body):
    rows=[]
    for raw in csv.reader(io.StringIO(body)):
        assert len(raw)==8 and raw[6] in ('True','False') and raw[7] in ('True','False')
        a,p,q,first,last,t=int(raw[0]),D(raw[1]),D(raw[2]),int(raw[3]),int(raw[4]),int(raw[5])
        assert p.is_finite() and q.is_finite() and p>0 and q>0 and 0<=first<=last and a>=0
        rows.append({'id':a,'price':p,'quantity':q,'first':first,'last':last,'time':t,'buyer_maker':raw[6]=='True'})
    assert rows
    for a,b in zip(rows,rows[1:]):
        assert b['id']==a['id']+1 and b['first']==a['last']+1 and b['time']>=a['time']
    return rows


def profile(trades,width):
    width=D(width);assert width.is_finite() and width>0
    bins={}
    for t in trades:
        k=int((t['price']/width).to_integral_value(rounding=ROUND_FLOOR))
        bins[k]=bins.get(k,D(0))+t['quantity']
    assert bins and max(bins)-min(bins)<10000
    total=sum(bins.values(),D(0));peak=max(bins.values())
    ties=sorted(k for k,v in bins.items() if v==peak);poc=ties[0]
    low=high=poc;included=bins[poc]
    while included<D('.70')*total:
        down=low-1 if low>min(bins) else None;up=high+1 if high<max(bins) else None
        if up is None or (down is not None and bins.get(down,D(0))>=bins.get(up,D(0))):
            low=down;included+=bins.get(low,D(0))
        else:high=up;included+=bins.get(high,D(0))
    return {'method':'hoshi-absolute-zero-half-open-price-bins-1','width_usdt':str(width),
            'quantity_unit':'BTC','base_volume':str(total),'occupied_bins':len(bins),
            'bins':[{'low_inclusive':str(k*width),'high_exclusive':str((k+1)*width),'base_volume':str(v)} for k,v in sorted(bins.items())],
            'poc_low_inclusive':str(poc*width),'poc_high_exclusive':str((poc+1)*width),
            'poc_tied_low_boundaries':[str(k*width) for k in ties],
            'value_area_method':'adjacent_larger_row_until_at_least_70pct_overshoot_allowed_ties_lower',
            'value_area_low_inclusive':str(low*width),'value_area_high_exclusive':str((high+1)*width),
            'value_area_base_volume':str(included),'value_area_volume_pct':str(included/total*100),
            'vendor_parity_validated':False}


def anchor_vwap(raw_rows,start,stop):
    rows=raw_rows[start:stop]
    volume=sum((D(r[5]) for r in rows),D(0));quote=sum((D(r[7]) for r in rows),D(0))
    assert volume>0
    proxy=sum(((D(r[2])+D(r[3])+D(r[4]))/3*D(r[5]) for r in rows),D(0))/volume
    actual=quote/volume
    return {'anchor_open_time':rows[0][0],'last_close_time':rows[-1][6],
            'base_volume':str(volume),'quote_volume':str(quote),'quote_divided_by_base_vwap':str(actual),
            'hlc3_bar_proxy':str(proxy),'proxy_minus_observed_vwap_bps':str((proxy/actual-1)*10000)}


def volume_case(raw_rows,capture):
    bar=raw_rows[60];start=bar[0];end=bar[6]+1
    assert capture['timestamp_unit']=='milliseconds' and capture['symbol']=='BTCUSDT' and capture['venue']=='Binance Spot'
    assert capture['start_inclusive_ms']==start and capture['end_exclusive_ms']==end and end-start==60000
    body=capture['response_body'];assert sha256(body.encode()).hexdigest()==capture['subset_sha256']
    trades=parse_aggregate_csv(body)
    assert len(trades)==capture['subset_rows'] and all(start<=t['time']<end for t in trades)
    before=parse_aggregate_csv(capture['last_row_before_window'])[0]
    after=parse_aggregate_csv(capture['first_row_after_window'])[0]
    assert before['time']<start<=trades[0]['time'] and trades[-1]['time']<end<=after['time']
    assert before['id']+1==trades[0]['id'] and trades[-1]['id']+1==after['id']
    assert before['last']+1==trades[0]['first'] and trades[-1]['last']+1==after['first']
    day=datetime.fromtimestamp(start/1000,timezone.utc).date().isoformat()
    name='BTCUSDT-aggTrades-'+day+'.zip'
    expected='https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/'+name
    assert capture['archive_url']==expected and capture['checksum_url']==expected+'.CHECKSUM'
    assert capture['checksum_response_body'].split()==[capture['archive_sha256'],name]
    assert len(capture['archive_sha256'])==64 and all(c in '0123456789abcdef' for c in capture['archive_sha256'])
    assert capture['archive_rows_scanned']>len(trades)
    quantity=sum((t['quantity'] for t in trades),D(0));quote=sum((t['quantity']*t['price'] for t in trades),D(0))
    count=sum(t['last']-t['first']+1 for t in trades)
    assert quantity==D(bar[5]) and quote==D(bar[7]) and count==bar[8]
    prices=[t['price'] for t in trades]
    assert [prices[0],max(prices),min(prices),prices[-1]]==[D(v) for v in bar[1:5]]
    return {'method':'hoshi-kline-and-archive-volume-case-1','selection':'fixed_minute_at_zero_based_capture_index_60',
            'bar_open_time':start,'earliest_after_close':end,'provider_arrival_time':None,
            'capture_anchor':anchor_vwap(raw_rows,0,61),'later_clock_anchor':anchor_vwap(raw_rows,30,61),
            'minute_aggregate_rows':len(trades),'minute_underlying_trade_count':count,
            'minute_vwap':str(quote/quantity),'minute_base_volume':str(quantity),
            'minute_ohlc':[str(v) for v in (prices[0],max(prices),min(prices),prices[-1])],
            'profile_1_usdt':profile(trades,'1'),'profile_5_usdt':profile(trades,'5'),
            'archive_whole_file_rechecked_offline':False,'subset_reconciles_with_native_minute':True,
            'session_profile_available':False,'decision':'WAIT','win_probability':None,'orders_enabled':False}


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
    if 'volume_cases' in payload:
        assert payload['aggregate_data_attribution']['data_license']=='CC BY-NC-SA 4.0'
        entries=payload['volume_cases']
        assert len(entries)==len(windows) and {e['source_window_sha256'] for e in entries}==set(windows)
        raws={e['source_sha256']:json.loads(e['response_body']) for e in source['observations']}
        for entry in entries:
            assert volume_case(raws[entry['source_window_sha256']],entry['aggregate_capture'])==entry['diagnostic']
    return windows
