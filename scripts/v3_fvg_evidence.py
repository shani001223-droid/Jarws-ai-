"""Original offline FVG lifecycle diagnostics, not creator parity or runtime.

Native minute captures remain immutable in their existing receipt. A geometry
feature uses only its completed A/B/C bars; future paths have separate clocks.
"""
from hashlib import sha256
import json
import math

from v3_ict_evidence import check_receipt as check_source, record, gap_features as clock_gap

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


def inversion_case(bars,index):
    parent=geometry(bars,index);assert parent is not None
    bull=parent['direction']=='long'
    stop=min(index+21,len(bars))
    failure=next((k for k in range(index+1,stop)
                  if (bars[k]['close']<parent['low'] if bull else bars[k]['close']>parent['high'])),None)
    if failure is None:
        return {'status':'no_close_failure_within_20_bars' if len(bars)-index-1>=20 else 'incomplete_failure_window',
                'parent':parent,'features':None,'outcome':None}
    broken=bars[failure]
    old_wick=next(b for b in bars[index+1:failure+1]
                  if (b['low']<=parent['low'] if bull else b['high']>=parent['high']))
    f={'method':'hoshi-first-close-failure-inversion-1','parent':parent,
       'direction':'short' if bull else 'long','low':parent['low'],'high':parent['high'],
       'midpoint':parent['midpoint'],'old_wick_retirement':record(old_wick),'failure':record(broken),
       'earliest_after_close':broken['close_time']+1,'provider_arrival_time':None,
       'creator_parity_validated':False,'decision':'WAIT','win_probability':None,'orders_enabled':False}
    future=bars[failure+1:failure+6]
    if len(future)!=5:return {'status':'inverted','parent':parent,'features':f,'outcome':None}
    contact=hold=invalid=None
    long=f['direction']=='long'
    for b in future:
        overlap=b['low']<=f['high'] and b['high']>=f['low']
        if overlap and contact is None:contact=record(b)
        breached=b['close']<f['low'] if long else b['close']>f['high']
        if breached:invalid=record(b);break
        held=b['close']>=f['midpoint'] if long else b['close']<=f['midpoint']
        if overlap and held and hold is None:hold=record(b)
    return {'status':'inverted','parent':parent,'features':f,'outcome':{
        'horizon_bars':5,'available_at':future[-1]['close_time']+1,'path':[record(b) for b in future],
        'first_contact':contact,'first_contact_closing_hold':hold,'first_invalidating_close':invalid,
        'raw_close_change_pct':(future[-1]['close']/broken['close']-1)*100,
        'fill_known':False,'strategy_pnl':None}}


def intersection(first,second):
    if first['direction']==second['direction']:return None
    low=max(first['low'],second['low']);high=min(first['high'],second['high'])
    return {'low':low,'high':high,'midpoint':(low+high)/2} if low<high else None


def balance_case(bars,index):
    parent=geometry(bars,index);assert parent is not None
    pair=None
    for k in range(index+1,min(index+21,len(bars))):
        later=geometry(bars,k)
        overlap=intersection(parent,later) if later is not None else None
        if overlap is not None:pair=(k,later,overlap);break
    if pair is None:
        return {'status':'no_opposite_gap_overlap_within_20_bars' if len(bars)-index-1>=20 else 'incomplete_pair_window',
                'features':None,'outcome':None}
    k,later,overlap=pair
    f={'method':'hoshi-first-opposite-wick-gap-overlap-1','first':parent,'second':later,**overlap,
       'earliest_after_close':later['earliest_after_close'],'provider_arrival_time':None,
       'forming_bars_shared':later['a']['time']<=parent['c']['time'],
       'directional_bias':None,'creator_parity_validated':False,'decision':'WAIT','win_probability':None}
    future=bars[k+1:k+6]
    if len(future)!=5:return {'status':'overlap_found','features':f,'outcome':None}
    return {'status':'overlap_found','features':f,'outcome':{
        'horizon_bars':5,'available_at':future[-1]['close_time']+1,'path':[record(b) for b in future],
        'first_contact':next((record(b) for b in future if b['low']<=f['high'] and b['high']>=f['low']),None),
        'first_close_below':next((record(b) for b in future if b['close']<f['low']),None),
        'first_close_above':next((record(b) for b in future if b['close']>f['high']),None),
        'fill_known':False,'strategy_pnl':None}}


def inversion_balance_case(bars):
    index=next((i for i in range(2,len(bars)) if geometry(bars,i) is not None),None)
    return {'selection':'first_chronological_parent_then_first_close_failure_and_first_opposite_overlap',
            'inversion':inversion_case(bars,index) if index is not None else None,
            'balance':balance_case(bars,index) if index is not None else None,
            'independent_holdout':False}


def quality_features(bars,index):
    """V2-style formation arithmetic on minutes, not full V2 qualification."""
    assert index>=21
    gap=geometry(bars,index);assert gap is not None
    b=bars[index-1];prior=bars[index-21:index-1];recent=bars[index-6:index-1]
    baseline=math.fsum(abs(x['close']-x['open']) for x in prior)/20
    bull=gap['direction']=='long'
    body=b['close']-b['open'] if bull else b['open']-b['close']
    reference=max(x['high'] for x in recent) if bull else min(x['low'] for x in recent)
    broke=b['close']>reference if bull else b['close']<reference
    opposite=[x for x in recent if (x['close']<x['open'] if bull else x['close']>x['open'])]
    origin=opposite[-1] if opposite else None
    large=baseline>0 and body>=1.5*baseline
    overlap=None
    if origin is not None:
        low=max(gap['low'],origin['low']);high=min(gap['high'],origin['high'])
        if low<high:overlap={'low':low,'high':high}
    return {'method':'hoshi-minute-gap-formation-quality-1','gap':gap,
            'baseline_start':prior[0]['time'],'baseline_end':prior[-1]['close_time'],
            'prior_body_mean':baseline,'directional_b_body':body,
            'body_multiple':body/baseline if baseline>0 else None,
            'body_gate':large,'five_bar_break_reference':reference,'break_gate':broke,
            'origin':record(origin) if origin is not None else None,'origin_gate':origin is not None,
            'gap_origin_positive_intersection':overlap,
            'qualified_formation':bool(large and broke and origin is not None),
            'earliest_after_close':gap['earliest_after_close'],'provider_arrival_time':None,
            'full_v2_timeframe_or_strategy_qualification':False,'decision':'WAIT','win_probability':None}


def quality_case(bars,index):
    f=quality_features(bars,index);gap=f['gap'];origin=f['origin']
    future=bars[index+1:index+6]
    if len(future)!=5:return {'features':f,'outcome':None}
    bull=gap['direction']=='long'
    far=closing=origin_close=contact=joint=hold=None
    for b in future:
        touched=b['low']<=gap['high'] and b['high']>=gap['low']
        origin_touched=bool(origin and b['low']<=origin['high'] and b['high']>=origin['low'])
        wick=b['low']<=gap['low'] if bull else b['high']>=gap['high']
        failed=b['close']<gap['low'] if bull else b['close']>gap['high']
        origin_failed=bool(origin and (b['close']<origin['low'] if bull else b['close']>origin['high']))
        if touched and contact is None:contact=record(b)
        if touched and origin_touched and joint is None:joint=record(b)
        if wick and far is None:far=record(b)
        if failed and closing is None:closing=record(b)
        if origin_failed and origin_close is None:origin_close=record(b)
        held=b['close']>=gap['midpoint'] if bull else b['close']<=gap['midpoint']
        if touched and held and far is None and hold is None:hold=record(b)
    return {'features':f,'outcome':{
        'horizon_bars':5,'available_at':future[-1]['close_time']+1,'path':[record(b) for b in future],
        'first_gap_contact':contact,'first_gap_far_wick':far,'first_gap_far_close':closing,
        'first_origin_closing_breach':origin_close,'first_bar_overlapping_gap_and_origin':joint,
        'first_partial_gap_contact_hold_before_far_wick':hold,
        'raw_close_change_pct':(future[-1]['close']/gap['c']['close']-1)*100,
        'same_price_gap_origin_fill_proven':False,'fill_known':False,'strategy_pnl':None}}


def first_quality_case(bars):
    candidates=[i for i in range(21,len(bars)) if geometry(bars,i) is not None]
    qualified=[i for i in candidates if quality_features(bars,i)['qualified_formation']]
    return {'selection':'first_qualified_formation_without_future_outcome_condition',
            'candidate_count':len(candidates),'qualified_count':len(qualified),
            'qualified_c_open_times':[bars[i]['time'] for i in qualified],
            'first_unfiltered_candidate':quality_case(bars,candidates[0]) if candidates else None,
            'case':quality_case(bars,qualified[0]) if qualified else None,
            'independent_holdout':False}


def first_joint_hold(bars,index,quality):
    """First same-bar price-range/closing hold before gap/origin cancellation."""
    gap=quality['gap'];origin=quality['origin'];bull=gap['direction']=='long'
    if not quality['qualified_formation']:return None
    for b in bars[index+1:index+6]:
        far=b['low']<=gap['low'] if bull else b['high']>=gap['high']
        origin_fail=b['close']<origin['low'] if bull else b['close']>origin['high']
        if far or origin_fail:return None
        overlap=b['low']<=gap['high'] and b['high']>=gap['low']
        ob_overlap=b['low']<=origin['high'] and b['high']>=origin['low']
        held=b['close']>=gap['midpoint'] if bull else b['close']<=gap['midpoint']
        if overlap and ob_overlap and held:return record(b)
    return None


def study(bars):
    ledger=[];origins={};complete_indices=[]
    for i in range(2,len(bars)):
        g=geometry(bars,i)
        if g is None:continue
        case=lifecycle(bars,i);out=case['outcome']
        q=quality_features(bars,i) if i>=21 else None
        quality={'status':'insufficient_pre_B_bars','qualified_formation':None}
        if q is not None:
            quality={k:q[k] for k in ('prior_body_mean','directional_b_body','body_multiple','body_gate',
                                     'break_gate','origin_gate','qualified_formation')}
            quality.update(status='observed',origin_time=q['origin']['time'] if q['origin'] else None)
            if q['qualified_formation']:origins.setdefault(q['origin']['time'],[]).append(g['c']['time'])
        signed=out['raw_close_change_pct']*(1 if g['direction']=='long' else -1) if out is not None else None
        if out is not None:complete_indices.append(i)
        ledger.append({'index':i,'features':g,'clock_eligible':bool(clock_gap(bars,i)['eligible_windows']),
                       'quality':quality,'five_bar_outcome':out,'directional_endpoint_change_pct':signed,
                       'first_joint_hold_before_cancellation':first_joint_hold(bars,i,q) if out is not None and q is not None else None})
    complete=[x for x in ledger if x['five_bar_outcome'] is not None]
    out=lambda x:x['five_bar_outcome']
    pairs=sum(1 for n,i in enumerate(complete_indices) for j in complete_indices[n+1:] if 0<j-i<5)
    same_bar=lambda x:bool(out(x)['first_contact'] and out(x)['first_far_boundary_touch_or_breach'] and
                          out(x)['first_contact']['time']==out(x)['first_far_boundary_touch_or_breach']['time'])
    sign_counts={key:sum(1 for x in complete if (x['directional_endpoint_change_pct']>0 if key=='positive' else
                                               x['directional_endpoint_change_pct']<0 if key=='negative' else
                                               x['directional_endpoint_change_pct']==0))
                 for key in ('positive','negative','zero')}
    return {'method':'hoshi-complete-bounded-minute-gap-ledger-1','bars':len(bars),
            'three_bar_decisions':len(bars)-2,'strict_gap_count':len(ledger),
            'non_gap_decisions':len(bars)-2-len(ledger),
            'history_eligible_gap_count':sum(x['quality']['status']=='observed' for x in ledger),
            'insufficient_warmup_gap_count':sum(x['quality']['status']!='observed' for x in ledger),
            'qualified_formation_count':sum(x['quality']['qualified_formation'] is True for x in ledger),
            'clock_eligible_gap_count':sum(x['clock_eligible'] for x in ledger),
            'complete_five_bar_outcomes':len(complete),'incomplete_five_bar_outcomes':len(ledger)-len(complete),
            'contact_count':sum(out(x)['first_contact'] is not None for x in complete),
            'no_contact_count':sum(out(x)['first_contact'] is None for x in complete),
            'partial_hold_before_retirement_count':sum(out(x)['first_partial_contact_closing_hold'] is not None for x in complete),
            'far_boundary_touch_or_breach_count':sum(out(x)['first_far_boundary_touch_or_breach'] is not None for x in complete),
            'same_bar_first_contact_and_retirement_count':sum(same_bar(x) for x in complete),
            'qualified_joint_hold_before_cancellation_count':sum(x['first_joint_hold_before_cancellation'] is not None for x in ledger),
            'directional_endpoint_sign_counts':sign_counts,
            'positive_endpoint_without_contact_count':sum(x['directional_endpoint_change_pct']>0 and out(x)['first_contact'] is None for x in complete),
            'positive_endpoint_after_same_bar_contact_retirement_count':sum(x['directional_endpoint_change_pct']>0 and same_bar(x) for x in complete),
            'overlapping_complete_outcome_pairs':pairs,
            'reused_qualified_origin_groups':[{'origin_time':k,'c_open_times':v} for k,v in origins.items() if len(v)>1],
            'assumed_round_trip_friction_bps':30,
            'gap_width_below_assumed_friction_count':sum(x['features']['width_bps_of_c_close']<30 for x in ledger),
            'friction_is_hypothetical_not_measured_cost_or_pnl':True,
            'ledger':ledger,'all_decisions_wait':True,'independent_holdout':False,
            'simulated_trades':None,'strategy_pnl':None,'account_drawdown':None,'win_probability':None}


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
    for entry in payload.get('inversion_balance_cases',[]):
        assert inversion_balance_case(windows[entry['source_window_sha256']])==entry['diagnostic']
    for entry in payload.get('quality_cases',[]):
        assert first_quality_case(windows[entry['source_window_sha256']])==entry['diagnostic']
    if 'studies' in payload:
        entries=payload['studies']
        assert len(entries)==len(windows)
        assert {entry['source_window_sha256'] for entry in entries}==set(windows)
        for entry in entries:
            assert study(windows[entry['source_window_sha256']])==entry['study']
    return windows
