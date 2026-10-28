"""Offline reference clusters: no actual stops, intent, signals or fills."""
from hashlib import sha256
import json
import math

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


def reclaim_features(bars,event_date,kind):
    """Original closed-day proxy, not published intraday Turtle Soup fills."""
    assert kind in ("high","low")
    k=next(k for k,b in enumerate(bars) if utc_day(b["time"])==event_date)
    assert k>=20
    prior=bars[k-20:k];event=bars[k]
    reference=(max if kind=="high" else min)(b[kind] for b in prior)
    # Most recent tied occurrence prevents an older equal extreme inflating age.
    anchor=max(j for j in range(k-20,k) if bars[j][kind]==reference)
    age=k-anchor
    excursion=event["high"]>reference if kind=="high" else event["low"]<reference
    reclaimed=event["close"]<reference if kind=="high" else event["close"]>reference
    return {"method":"hoshi-prior20-reclaim-1","kind":kind,"event":bar_record(event),
            "prior_start":utc_day(prior[0]["time"]),"prior_end":utc_day(prior[-1]["time"]),
            "reference":reference,"reference_date":utc_day(bars[anchor]["time"]),
            "reference_age_bars":age,"age_units":"Binance UTC daily bars, including weekends",
            "earliest_after_close":event["close_time"]+1,"provider_arrival_time":None,
            "new_twenty_bar_extreme":excursion,"same_day_closing_reclaim":bool(excursion and reclaimed),
            "same_day_age_gate":bool(excursion and age>=4),
            "plus_one_setup":bool(excursion and age>=3 and not reclaimed),
            "historical_tick_size_known":False,"published_intraday_order_parity":False,
            "institutional_intent_known":False,"decision":"WAIT","win_probability":None}


def reclaim_case(bars,event_date,kind):
    f=reclaim_features(bars,event_date,kind)
    k=next(k for k,b in enumerate(bars) if utc_day(b["time"])==event_date)
    future=bars[k+1:k+6]
    if len(future)!=5:return {"features":f,"outcome":None}
    nxt=future[0];ref=f["reference"]
    return {"features":f,"outcome":{
        "horizon_bars":5,"available_at":future[-1]["close_time"]+1,
        "path":[bar_record(b) for b in future],
        "next_day_reference_in_recorded_range":nxt["low"]<=ref<=nxt["high"],
        "next_day_opens_beyond_entry_side":nxt["open"]<ref if kind=="high" else nxt["open"]>ref,
        "next_day_close_reclaims":nxt["close"]<ref if kind=="high" else nxt["close"]>ref,
        "raw_close_change_pct":(future[-1]["close"]/f["event"]["close"]-1)*100,
        "same_bar_entry_stop_order_known":False,"fill_known":False,
        "strategy_pnl":None,"orders_enabled":False}}


def cost_illustration(reference):
    """Unrounded hypothetical long-only arithmetic, never an executable order."""
    assert isinstance(reference,(int,float)) and not isinstance(reference,bool)
    assert math.isfinite(reference) and 0<reference<=1e12
    stop,target=.99*reference,1.02*reference
    rows=[]
    for bps in (0,5,15,50):
        rate=bps/10000
        loss=reference-stop+rate*(reference+stop)
        gain=target-reference-rate*(reference+target)
        quantity=min(50/loss,10000/(reference*(1+rate)))
        rows.append({"assumed_cost_bps_per_leg":bps,"modeled_loss_per_unit_at_stop":loss,
                     "modeled_gain_per_unit_at_target":gain,"net_target_to_stop_loss_ratio":gain/loss,
                     "unrounded_quantity":quantity,"modeled_stop_loss":quantity*loss,
                     "entry_cash_with_modeled_cost":quantity*reference*(1+rate)})
    return {"method":"hoshi-unfilled-barrier-cost-illustration-1","reference_price":reference,
            "stop_reference":stop,"target_reference":target,"assumed_equity":10000,
            "assumed_loss_budget":50,"assumed_cash_cap":10000,"cost_sensitivity":rows,
            "actual_fee_or_slippage_verified":False,"historical_filters_verified":False,
            "entry_fill_known":False,"orders_enabled":False,"strategy_pnl":None}


def execution_features(bars,event_date):
    event=next(b for b in bars if utc_day(b["time"])==event_date)
    return {"event":bar_record(event),"earliest_after_close":event["close_time"]+1,
            "provider_arrival_time":None,"illustration":cost_illustration(event["close"]),
            "decision":"WAIT","win_probability":None}


def execution_case(bars,event_date):
    f=execution_features(bars,event_date)
    k=next(k for k,b in enumerate(bars) if utc_day(b["time"])==event_date)
    future=bars[k+1:k+6]
    if len(future)!=5:return {"features":f,"outcome":None}
    stop=f["illustration"]["stop_reference"];target=f["illustration"]["target_reference"]
    terminal=None
    for b in future:
        if b["open"]<=stop:label="opens_at_or_beyond_stop_reference"
        elif b["open"]>=target:label="opens_at_or_beyond_target_reference"
        elif b["low"]<=stop and b["high"]>=target:label="ambiguous_both_barriers_same_bar"
        elif b["low"]<=stop:label="stop_reference_only_first"
        elif b["high"]>=target:label="target_reference_only_first"
        else:continue
        terminal={"classification":label,"bar":bar_record(b),"available_at":b["close_time"]+1}
        break
    return {"features":f,"outcome":{
        "horizon_bars":5,"available_at":future[-1]["close_time"]+1,
        "path":[bar_record(b) for b in future],"first_barrier_observation":terminal,
        "entry_at_reference_proven":False,"intrabar_sequence_known":False,
        "strategy_pnl":None,"drawdown":None,"orders_enabled":False}}


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
    for entry in payload.get("reclaim_cases",[]):
        f=entry["case"]["features"]
        assert reclaim_case(windows[entry["source_window_sha256"]],f["event"]["date"],f["kind"])==entry["case"]
    for entry in payload.get("execution_cases",[]):
        f=entry["case"]["features"]
        assert execution_case(windows[entry["source_window_sha256"]],f["event"]["date"])==entry["case"]
    return windows
