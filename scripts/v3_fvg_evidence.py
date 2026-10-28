"""Original offline FVG lifecycle diagnostics, not creator parity or runtime.

Native minute captures remain immutable in their existing receipt. A geometry
feature uses only its completed A/B/C bars; future paths have separate clocks.
"""
from hashlib import sha256
import json

from v3_ict_evidence import check_receipt as check_source, record

SOURCE="knowledge_base/05_ICT_COMPLETE/ict_intraday_observations_20261028.json"


def geometry(bars,index):
    assert 2<=index<len(bars)
    a,b,c=bars[index-2:index+1]
    bull=a["high"]<c["low"];bear=c["high"]<a["low"]
    if not (bull or bear):return None
    low,high=(a["high"],c["low"]) if bull else (c["high"],a["low"])
    return {"method":"hoshi-strict-outer-wick-gap-1","direction":"long" if bull else "short",
            "a":record(a),"b":record(b),"c":record(c),"low":low,"high":high,
            "midpoint":(low+high)/2,"width":high-low,"width_bps_of_c_close":(high-low)/c["close"]*10000,
            "earliest_after_close":c["close_time"]+1,"provider_arrival_time":None,
            "actual_untraded_prices_known":False,"creator_parity_validated":False,
            "decision":"WAIT","win_probability":None,"orders_enabled":False}


def lifecycle(bars,index):
    f=geometry(bars,index);assert f is not None
    future=bars[index+1:index+6]
    if len(future)!=5:return {"features":f,"outcome":None}
    contact=midpoint=far=rejection=None
    bull=f["direction"]=="long"
    for b in future:
        overlaps=b["low"]<=f["high"] and b["high"]>=f["low"]
        if overlaps and contact is None:contact=record(b)
        if b["low"]<=f["midpoint"]<=b["high"] and midpoint is None:midpoint=record(b)
        crossed=b["low"]<=f["low"] if bull else b["high"]>=f["high"]
        if crossed:far=record(b);break
        hold=b["close"]>=f["midpoint"] if bull else b["close"]<=f["midpoint"]
        if overlaps and hold and rejection is None:rejection=record(b)
    return {"features":f,"outcome":{
        "horizon_bars":5,"available_at":future[-1]["close_time"]+1,
        "path":[record(b) for b in future],"first_contact":contact,"first_midpoint_touch":midpoint,
        "first_far_boundary_touch_or_breach":far,"first_partial_contact_closing_hold":rejection,
        "raw_close_change_pct":(future[-1]["close"]/f["c"]["close"]-1)*100,
        "fill_known":False,"strategy_pnl":None}}


def first_case(bars):
    index=next((i for i in range(2,len(bars)) if geometry(bars,i) is not None),None)
    return {"selection":"first_chronological_strict_gap_without_clock_or_outcome_filter",
            "case":lifecycle(bars,index) if index is not None else None,
            "independent_holdout":False}


def check_receipt(payload,root):
    assert payload["schema_version"]=="hoshi-v3-fvg-evidence-1"
    assert payload["data_license"]=="CC BY-NC-SA 4.0" and payload["source_file"]==SOURCE
    raw=(root/SOURCE).read_bytes()
    assert sha256(raw).hexdigest()==payload["source_file_sha256"]
    source=json.loads(raw);checked=check_source(source,root)
    windows={item["source_sha256"]:bars for item,bars in zip(source["observations"],checked)}
    assert len(payload["first_gap_cases"])==3
    for entry in payload["first_gap_cases"]:
        assert first_case(windows[entry["source_window_sha256"]])==entry["diagnostic"]
    return windows
