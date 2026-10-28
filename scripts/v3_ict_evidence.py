"""Original offline minute-bar gap/time evidence, not an ICT signal engine.

Original captions are attributed separately; no course recognizer parity,
trader intent, current freshness, execution fills or win probability is known.
The first eligible gap is selected chronologically, never by future outcome.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

MINUTE = 60_000
NY = ZoneInfo("America/New_York")
WINDOWS = {"silver_london": (180,240), "silver_am": (600,660), "silver_pm": (840,900)}


def normalize(rows):
    assert isinstance(rows,list) and 3 <= len(rows) <= 1000
    bars = []
    for row in rows:
        assert isinstance(row,list) and len(row)==12
        start,end=row[0],row[6]
        assert type(start) is int and type(end) is int and start>=0 and start%MINUTE==0
        assert end==start+MINUTE-1
        op,hi,lo,cl,volume,quote,taker,taker_quote=(float(row[k]) for k in (1,2,3,4,5,7,9,10))
        assert all(math.isfinite(v) for v in (op,hi,lo,cl,volume,quote,taker,taker_quote))
        assert 0<lo<=min(op,cl)<=max(op,cl)<=hi and volume>=0 and quote>=0
        assert 0<=taker<=volume+1e-8 and 0<=taker_quote<=quote+1e-8
        assert type(row[8]) is int and row[8]>=0
        assert not bars or start==bars[-1]["time"]+MINUTE
        bars.append({"time":start,"close_time":end,"open":op,"high":hi,"low":lo,"close":cl,"volume":volume})
    return bars


def clock(stamp):
    local=datetime.fromtimestamp(stamp/1000,timezone.utc).astimezone(NY)
    minute=local.hour*60+local.minute
    active=[name for name,(start,end) in WINDOWS.items() if local.weekday()<5 and start<=minute<end]
    return {"local_time":local.isoformat(),"timezone":"America/New_York",
            "active_windows":active,"weekday":local.weekday()}


def record(b):
    return {"time":b["time"],"close_time":b["close_time"],
            **{k:b[k] for k in ("open","high","low","close")}}


def gap_features(bars,index):
    assert 2<=index<len(bars)
    a,b,c=bars[index-2:index+1]
    bull=a["high"]<c["low"]
    bear=c["high"]<a["low"]
    assert bull or bear, "no strict three-bar gap"
    low,high=(a["high"],c["low"]) if bull else (c["high"],a["low"])
    # +1 is the first possible millisecond AFTER C is fully closed. Real
    # provider publication/arrival delay is unknown and is not assumed zero.
    earliest=c["close_time"]+1
    timing=clock(earliest)
    start_timing=clock(a["time"])
    same_date=timing["local_time"][:10]==start_timing["local_time"][:10]
    windows=[name for name in timing["active_windows"]
             if same_date and name in start_timing["active_windows"]]
    return {"method":"hoshi-minute-gap-clock-1","direction":"long" if bull else "short",
            "a":record(a),"b":record(b),"c":record(c),"gap_low":low,"gap_high":high,
            "source_bar_closed_at":c["close_time"],"earliest_after_close":earliest,
            "provider_arrival_time":None,"clock":timing,"eligible_windows":windows,
            "all_three_bars_within_same_window":bool(windows),"creator_parity_validated":False,
            "decision":"WAIT","orders_enabled":False,"win_probability":None}


def gap_case(bars,index):
    f=gap_features(bars,index)
    future=bars[index+1:index+6]
    if len(future)!=5:
        return {"features":f,"outcome_status":"incomplete","outcome":None}
    low,high=f["gap_low"],f["gap_high"]
    bull=f["direction"]=="long"
    contact=eligible=invalid=None
    for bar in future:
        overlaps=bar["low"]<=high and bar["high"]>=low
        if overlaps and contact is None:contact=record(bar)
        full=bar["low"]<=low if bull else bar["high"]>=high
        if full:
            invalid=record(bar);break
        hold=bar["close"]>=(low+high)/2 if bull else bar["close"]<=(low+high)/2
        still_in_window=bool(set(clock(bar["close_time"]+1)["active_windows"]) & set(f["eligible_windows"]))
        if f["eligible_windows"] and overlaps and hold and still_in_window and eligible is None:
            eligible=record(bar)
    return {"features":f,"outcome_status":"observed","outcome":{
        "horizon_bars":5,"available_at":future[-1]["close_time"]+1,
        "path":[record(b) for b in future],"first_contact":contact,
        "first_eligible_geometric_retest":eligible,"first_full_gap_crossing":invalid,
        "raw_close_change_pct":(future[-1]["close"]/f["c"]["close"]-1)*100,
        "fill_known":False,"strategy_pnl":None}}


def gap_scan(bars):
    formed=[]
    for i in range(2,len(bars)):
        try:f=gap_features(bars,i)
        except AssertionError:continue
        if f["eligible_windows"]:formed.append(i)
    return {"method":"hoshi-first-in-window-gap-1","minute_bars":len(bars),
            "eligible_gap_count":len(formed),"eligible_c_open_times":[bars[i]["time"] for i in formed],
            "selection":"first_chronological_eligible_gap_without_future_condition",
            "first_case":gap_case(bars,formed[0]) if formed else None,
            "all_decisions_wait":True,"strategy_pnl":None,"win_probability":None,
            "independent_holdout":False}


def context_features(bars):
    """Frozen thirty-minute envelope, not a day/week/session opening gap."""
    assert len(bars)>=30
    prior=bars[:30]
    earliest=prior[-1]["close_time"]+1
    timing=clock(earliest)
    assert len(timing["active_windows"])==1
    window=timing["active_windows"][0]
    assert timing["local_time"][11:16] in ("03:00","10:00","14:00")
    low=min(b["low"] for b in prior);high=max(b["high"] for b in prior)
    return {"method":"hoshi-prior-thirty-minute-envelope-1","prior_bars":30,
            "prior_start":prior[0]["time"],"prior_end":prior[-1]["close_time"],
            "earliest_after_close":earliest,"provider_arrival_time":None,
            "clock":timing,"window":window,"low":low,"high":high,
            "midpoint":(low+high)/2,"last_prior_close":prior[-1]["close"],
            "is_day_or_week_opening_gap":False,"directional_bias":None}


def context_case(bars):
    f=context_features(bars)
    active=bars[30:90]
    if len(active)!=60:return {"features":f,"outcome":None}
    return {"features":f,"outcome":{
        "horizon_bars":60,"available_at":active[-1]["close_time"]+1,
        "window_open":active[0]["open"],"window_low":min(b["low"] for b in active),
        "window_high":max(b["high"] for b in active),"window_close":active[-1]["close"],
        "first_above_bar":next((record(b) for b in active if b["high"]>f["high"]),None),
        "first_below_bar":next((record(b) for b in active if b["low"]<f["low"]),None),
        "intrabar_crossing_time_known":False,"bias_selected_from_outcome":False,
        "strategy_pnl":None,"orders_enabled":False}}


def ote_features(bars):
    """Original fixed-pre-hour wick range; NOT exact creator OTE parity."""
    base=context_features(bars)
    prior=bars[:30]
    low,high=base["low"],base["high"]
    span=high-low
    assert span>0
    li=next(k for k,b in enumerate(prior) if b["low"]==low)
    hi=next(k for k,b in enumerate(prior) if b["high"]==high)
    assert li!=hi,"same-candle extreme order is unknown"
    bull=li<hi
    level=lambda q: high-q*span if bull else low+q*span
    bounds=sorted((level(.62),level(.79)))
    return {"method":"hoshi-frozen-wick-ote-1","direction":"long" if bull else "short",
            "context":base,"low_anchor":record(prior[li]),"high_anchor":record(prior[hi]),
            "anchor_selection":"first_global_extremes_of_fixed_prior_30_bars",
            "range":span,"level_62":level(.62),"level_705":level(.705),"level_79":level(.79),
            "band_low":bounds[0],"band_high":bounds[1],
            "invalidation_reference":low if bull else high,
            "earliest_after_close":base["earliest_after_close"],
            "creator_parity_validated":False,"decision":"WAIT","win_probability":None}


def ote_case(bars):
    f=ote_features(bars)
    future=bars[30:35]
    if len(future)!=5:return {"features":f,"outcome":None}
    bull=f["direction"]=="long"
    contact=rejection=invalid=None
    for b in future:
        overlaps=b["low"]<=f["band_high"] and b["high"]>=f["band_low"]
        if overlaps and contact is None:contact=record(b)
        breached=b["low"]<=f["invalidation_reference"] if bull else b["high"]>=f["invalidation_reference"]
        if breached:invalid=record(b);break
        hold=b["close"]>=f["level_705"] if bull else b["close"]<=f["level_705"]
        if overlaps and hold and rejection is None:rejection=record(b)
    return {"features":f,"outcome":{
        "horizon_bars":5,"available_at":future[-1]["close_time"]+1,
        "path":[record(b) for b in future],"first_band_contact":contact,
        "first_closing_rejection":rejection,"first_anchor_touch_or_cross":invalid,
        "raw_close_change_pct":(future[-1]["close"]/f["context"]["last_prior_close"]-1)*100,
        "observed_fill":False,"strategy_pnl":None,"orders_enabled":False}}


def check_observation(item):
    assert item["symbol"]=="BTCUSDT" and item["interval"]=="1m" and item["venue"]=="Binance Spot"
    raw=item["response_body"]
    assert isinstance(raw,str) and len(raw.encode())<=250000
    assert sha256(raw.encode()).hexdigest()==item["source_sha256"]
    url=urlsplit(item["request_url"])
    assert url.scheme=="https" and url.netloc=="data-api.binance.vision" and url.path=="/api/v3/klines"
    params=parse_qs(url.query,strict_parsing=True)
    assert set(params)=={"symbol","interval","startTime","endTime","limit"}
    assert params["symbol"]==["BTCUSDT"] and params["interval"]==["1m"] and params["limit"]==["1000"]
    bars=normalize(json.loads(raw))
    assert len(bars)==item["rows"]==120
    assert bars[0]["time"]==int(params["startTime"][0]) and bars[-1]["close_time"]==int(params["endTime"][0])
    assert datetime.fromtimestamp(bars[0]["time"]/1000,timezone.utc).date().isoformat()==item["event_date_utc"]
    fetched=datetime.fromisoformat(item["retrieved_at_utc"])
    assert fetched.utcoffset().total_seconds()==0 and fetched.timestamp()*1000>bars[-1]["close_time"]
    assert gap_scan(bars)==item["gap_scan"]
    if "context_case" in item:assert context_case(bars)==item["context_case"]
    if "ote_case" in item:assert ote_case(bars)==item["ote_case"]
    return bars


def check_receipt(payload,root=None):
    assert payload["schema_version"]=="hoshi-v3-ict-intraday-evidence-1"
    assert payload["data_license"]=="CC BY-NC-SA 4.0"
    assert len(payload["observations"])==3
    return [check_observation(item) for item in payload["observations"]]
