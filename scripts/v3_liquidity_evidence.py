"""Offline reference clusters: no actual stops, intent, signals or fills."""
from hashlib import sha256
import json

from v3_structure_evidence import check_window, pivots, utc_day
from v3_zone_evidence import bar_record

SOURCE="knowledge_base/01_MARKET_STRUCTURE/structure_observations_20261028.json"


def cluster_features(bars,event_date,kind,tolerance_bps=25):
    assert kind in ("high","low") and tolerance_bps==25
    k=next(k for k,b in enumerate(bars) if utc_day(b["time"])==event_date)
    assert k>=5
    prior=bars[:k];event=bars[k]
    side=[p for p in pivots(prior) if p["kind"]==kind][-2:]
    assert len(side)==2,"two prior confirmed pivots required"
    a,b=side
    assert b["confirmed_at"]<event["time"]
    lower,upper=sorted((a["price"],b["price"]))
    separation=(upper-lower)/((upper+lower)/2)*10000
    outer=upper if kind=="high" else lower
    intervening=[x for x in prior if x["close_time"]>b["confirmed_at"]]
    prior_crossed=any(x["high"]>outer if kind=="high" else x["low"]<outer for x in intervening)
    beyond=event["high"]>outer if kind=="high" else event["low"]<outer
    reclaimed=bool(beyond and (event["close"]<lower if kind=="high" else event["close"]>upper))
    return {"method":"hoshi-latest-two-confirmed-cluster-25bp-1","kind":kind,
            "event":bar_record(event),"earliest_after_close":event["close_time"]+1,
            "prior_available_at":prior[-1]["close_time"]+1,
            "first_pivot":a,"second_pivot":b,"lower":lower,"upper":upper,
            "separation_bps":separation,"tolerance_bps":tolerance_bps,
            "within_tolerance":separation<=tolerance_bps,"outer_reference":outer,
            "prior_wick_beyond_outer_since_second_confirmation":prior_crossed,
            "event_wick_beyond_outer":beyond,"event_close_reclaims_entire_cluster":reclaimed,
            "actual_stop_inventory_known":False,"institutional_intent_known":False,
            "provider_arrival_time":None,"decision":"WAIT","win_probability":None}


def cluster_case(bars,event_date,kind):
    f=cluster_features(bars,event_date,kind)
    k=next(k for k,b in enumerate(bars) if utc_day(b["time"])==event_date)
    future=bars[k+1:k+6]
    if len(future)!=5:return {"features":f,"outcome":None}
    outer=f["outer_reference"]
    seen=f["event_wick_beyond_outer"]
    reclaim=None
    for b in future:
        beyond=b["high"]>outer if kind=="high" else b["low"]<outer
        seen=seen or beyond
        across=b["close"]<f["lower"] if kind=="high" else b["close"]>f["upper"]
        if seen and across:
            reclaim=bar_record(b);break
    return {"features":f,"outcome":{
        "horizon_bars":5,"available_at":future[-1]["close_time"]+1,
        "path":[bar_record(b) for b in future],
        "first_beyond_outer_bar":next((bar_record(b) for b in future
            if (b["high"]>outer if kind=="high" else b["low"]<outer)),None),
        "first_post_excursion_reclaim":reclaim,
        "raw_close_change_pct":(future[-1]["close"]/f["event"]["close"]-1)*100,
        "fill_known":False,"strategy_pnl":None,"orders_enabled":False}}


def check_receipt(payload,root):
    assert payload["schema_version"]=="hoshi-v3-liquidity-evidence-1"
    assert payload["data_license"]=="CC BY-NC-SA 4.0"
    assert payload["source_file"]==SOURCE
    raw=(root/SOURCE).read_bytes()
    assert sha256(raw).hexdigest()==payload["source_file_sha256"]
    source=json.loads(raw)
    windows={o["source_sha256"]:check_window(o) for o in source["observations"]}
    assert len(payload["cluster_cases"])==3
    for entry in payload["cluster_cases"]:
        f=entry["case"]["features"]
        assert cluster_case(windows[entry["source_window_sha256"]],f["event"]["date"],f["kind"])==entry["case"]
    return windows
