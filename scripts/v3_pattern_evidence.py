"""Offline pattern measurements from hash-checked historical candles.

Original HOSHI geometric research conventions, NOT a TA-Lib port, trained
model, runtime signal, probability or order simulator. Features and subsequent
outcomes have different availability times. No network requests are made.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from statistics import fmean, median

from v3_structure_evidence import check_window, pivots, utc_day

SOURCE = "knowledge_base/01_MARKET_STRUCTURE/structure_observations_20261028.json"
CANDLE_VERSION = "hoshi-candle-geometry-1"


def candle_features(bars, index):
    b = bars[index]
    op, hi, lo, cl = (b[k] for k in ("open", "high", "low", "close"))
    span, body = hi-lo, abs(cl-op)
    upper, lower = hi-max(op, cl), min(op, cl)-lo
    shape = {"range": span, "body": body, "upper_wick": upper, "lower_wick": lower,
             "body_fraction": body/span if span else None,
             "upper_fraction": upper/span if span else None,
             "lower_fraction": lower/span if span else None,
             "close_location": (cl-lo)/span if span else None}
    labels = []
    if span:
        if body/span <= .10:
            labels.append("doji_geometry")
        if 0 < body/span <= .35 and lower >= 2*body and upper/span <= .15:
            labels.append("lower_wick_geometry")
        if 0 < body/span <= .35 and upper >= 2*body and lower/span <= .15:
            labels.append("upper_wick_geometry")
    if index:
        p = bars[index-1]
        po, pc = p["open"], p["close"]
        if pc < po and cl > op and op <= pc and cl >= po and (op < pc or cl > po):
            labels.append("bullish_body_engulfing")
        if pc > po and cl < op and cl <= po and op >= pc and (cl < po or op > pc):
            labels.append("bearish_body_engulfing")
        if hi < p["high"] and lo > p["low"]:
            labels.append("strict_inside_bar")
        if hi > p["high"] and lo < p["low"]:
            labels.append("strict_outside_bar")
    return {"method": CANDLE_VERSION, "measurements": shape, "labels": labels}


def candle_case(bars, event_date):
    index = next(i for i, b in enumerate(bars) if utc_day(b["time"]) == event_date)
    b = bars[index]
    features = candle_features(bars, index)
    result = {"event_date": event_date, "known_at": b["close_time"],
              "ohlc": {k: b[k] for k in ("open", "high", "low", "close")},
              "features": features,
              "previous_ohlc": {k: bars[index-1][k] for k in ("open", "high", "low", "close")} if index else None}
    future = bars[index+1:index+6]
    if len(future) != 5:
        return {**result, "outcome_status": "incomplete", "outcome": None}
    return {**result, "outcome_status": "observed", "outcome": {
        "available_at": future[-1]["close_time"], "next_date": utc_day(future[0]["time"]),
        "next_close": future[0]["close"],
        "next_close_above_event_high": future[0]["close"] > b["high"],
        "next_close_below_event_low": future[0]["close"] < b["low"],
        "fifth_date": utc_day(future[-1]["time"]), "fifth_close": future[-1]["close"],
        "forward_close_change_pct": (future[-1]["close"]/b["close"]-1)*100}}


def two_turn_case(bars, kind, first_date, second_date):
    """A custom two-turn candidate, not a certified textbook recognizer.

    Same-kind consecutive strict pivots; >=3 bars apart; price difference /
    mean price <=3%. Freeze the intervening extreme as neckline, then inspect
    TEN bars after second-pivot confirmation. A close through the outer extreme
    cancels a later break. No fills or PnL are computed.
    """
    assert kind in ("low", "high")
    i, j = (next(n for n, b in enumerate(bars) if utc_day(b["time"]) == day)
            for day in (first_date, second_date))
    assert j-i >= 3 and j+2 < len(bars)
    known = j+2
    prefix = bars[:known+1]
    turns = [p for p in pivots(prefix) if p["kind"] == kind]
    first = next(p for p in turns if p["pivot_at"] == bars[i]["close_time"])
    second = next(p for p in turns if p["pivot_at"] == bars[j]["close_time"])
    assert turns.index(second) == turns.index(first)+1
    difference = abs(first["price"]-second["price"])/((first["price"]+second["price"])/2)
    neck = max(b["high"] for b in bars[i+1:j]) if kind == "low" else min(b["low"] for b in bars[i+1:j])
    beyond = lambda close: close > neck if kind == "low" else close < neck
    outer = min(first["price"], second["price"]) if kind == "low" else max(first["price"], second["price"])
    invalid = lambda close: close < outer if kind == "low" else close > outer
    result = {"method": "hoshi-two-turn-1", "kind": kind,
              "first_date": first_date, "second_date": second_date,
              "turns": [first, second], "known_at": bars[known]["close_time"],
              "relative_difference": difference, "tolerance": .03,
              "similarity_pass": difference <= .03, "frozen_neckline": neck,
              "outer_invalidation_level": outer,
              "already_beyond_neckline_at_formation": beyond(bars[known]["close"])}
    future = bars[known+1:known+11]
    if len(future) != 10:
        return {**result, "outcome_status": "incomplete", "outcome": None}
    event = lambda b: {"date": utc_day(b["time"]), "available_at": b["close_time"], "close": b["close"]}
    broken = next((event(b) for b in future if beyond(b["close"])), None)
    cancelled = next((event(b) for b in future if invalid(b["close"])), None)
    eligible = bool(result["similarity_pass"] and not result["already_beyond_neckline_at_formation"]
                    and broken and (not cancelled or broken["available_at"] < cancelled["available_at"]))
    return {**result, "outcome_status": "observed", "outcome": {
        "available_at": future[-1]["close_time"], "future_bars": 10,
        "first_neckline_beyond_close": broken, "first_outer_invalidation_close": cancelled,
        "eligible_break_before_cancellation": eligible}}


def harmonic_case(bars, dates):
    """Five consecutive alternating pivots; ratio diagnostics, NOT a match.

    Only two necessary Gartley ratios are compared with explicit +/-0.03
    exploratory tolerance. Passing either/both is not full pattern validation.
    No projected D price is called an observed fill or confirmed turning point.
    """
    assert len(dates) == 5 and len(set(dates)) == 5 and dates == sorted(dates)
    last = next(i for i, b in enumerate(bars) if utc_day(b["time"]) == dates[-1])
    assert last+2 < len(bars)
    points = pivots(bars[:last+3])
    selected = [p for p in points if utc_day(p["pivot_at"]) in dates]
    assert len(selected) == 5, "Ambiguous same-bar high/low or unavailable pivot"
    offset = points.index(selected[0])
    assert selected == points[offset:offset+5], "Skipping inconvenient pivots is a different method"
    assert all(a["kind"] != b["kind"] and a["pivot_at"] < b["pivot_at"]
               for a, b in zip(selected, selected[1:]))
    x, a, b, c, d = (p["price"] for p in selected)
    xa, ab, bc, cd = abs(a-x), abs(b-a), abs(c-b), abs(d-c)
    assert min(xa, ab, bc) > 0
    ratios = {"AB_over_XA": ab/xa, "BC_over_AB": bc/ab, "CD_over_BC": cd/bc,
              "AD_over_XA": abs(d-a)/xa, "CD_over_AB": cd/ab}
    return {"method": "hoshi-five-pivot-ratios-1", "dates": dates, "points": selected,
            "known_at": bars[last+2]["close_time"], "ratios": ratios,
            "gartley_necessary_ratio_diagnostics": {
                "tolerance_absolute_ratio_units": .03,
                "AB_near_0_618": abs(ratios["AB_over_XA"]-.618) <= .03,
                "AD_near_0_786": abs(ratios["AD_over_XA"]-.786) <= .03},
            "classification": "ratio_measurements_only", "pattern_validated": False,
            "win_probability": None, "orders_enabled": False}


def candle_event_study(bars):
    """Exhaustive descriptive five-bar endpoint study within ONE source window.

    All bullish-body-engulfing events are retained, including incomplete tails
    and overlapping windows. No context filter, fills, trade sizing, stop/target,
    strategy PnL or independent holdout is claimed. Cost columns are arithmetic
    sensitivity to invented fixed deductions, not observed exchange costs.
    """
    events, indices = [], []
    for i in range(1, len(bars)):
        if "bullish_body_engulfing" not in candle_features(bars, i)["labels"]:
            continue
        c = candle_case(bars, utc_day(bars[i]["time"]))
        events.append({"event_date": c["event_date"], "known_at": c["known_at"],
                       "observed_close": bars[i]["close"], "outcome_status": c["outcome_status"],
                       "outcome": {k: c["outcome"][k] for k in ("available_at", "fifth_date", "fifth_close", "forward_close_change_pct")}
                       if c["outcome"] else None})
        indices.append(i)
    values = [x["outcome"]["forward_close_change_pct"] for x in events if x["outcome"]]
    baseline = [(bars[i+5]["close"]/bars[i]["close"]-1)*100
                for i in range(1, len(bars)-5)]
    overlaps = sum(b-a < 5 for n, a in enumerate(indices) for b in indices[n+1:])
    return {"method": "hoshi-engulfing-endpoints-1", "status": "exploratory_descriptive_not_holdout",
            "window_start": utc_day(bars[0]["time"]), "window_end": utc_day(bars[-1]["time"]),
            "bars": len(bars), "signal_comparisons": len(bars)-1, "events": events,
            "detected_events": len(events), "observed_endpoints": len(values),
            "incomplete_endpoints": len(events)-len(values), "overlapping_forward_window_pairs": overlaps,
            "positive_endpoints": sum(x > 0 for x in values),
            "nonpositive_endpoints": sum(x <= 0 for x in values),
            "mean_raw_close_change_pct": fmean(values) if values else None,
            "median_raw_close_change_pct": median(values) if values else None,
            "all_eligible_bar_baseline": {"observed_endpoints": len(baseline),
                "mean_raw_close_change_pct": fmean(baseline) if baseline else None,
                "median_raw_close_change_pct": median(baseline) if baseline else None},
            "assumed_cost_sensitivity": [{"assumed_fixed_deduction_percentage_points": cost,
                "mean_raw_change_minus_deduction": fmean(values)-cost if values else None}
                for cost in (0., .20, .50)],
            "win_probability": None, "strategy_pnl": None, "orders_enabled": False}


def check_receipt(payload, root):
    assert payload["schema_version"] == "hoshi-v3-pattern-evidence-1"
    assert payload["source_receipt"] == SOURCE
    assert payload["data_license"] == "CC BY-NC-SA 4.0"
    raw = (Path(root) / SOURCE).read_bytes()
    assert sha256(raw).hexdigest() == payload["source_receipt_sha256"]
    source = json.loads(raw)
    windows = {item["source_sha256"]: check_window(item) for item in source["observations"]}
    assert len(payload["candle_cases"]) == 3
    for entry in payload["candle_cases"]:
        assert candle_case(windows[entry["source_window_sha256"]], entry["case"]["event_date"]) == entry["case"]
    for entry in payload.get("classical_cases", []):
        case = entry["case"]
        assert two_turn_case(windows[entry["source_window_sha256"]], case["kind"],
                             case["first_date"], case["second_date"]) == case
    for entry in payload.get("harmonic_cases", []):
        assert harmonic_case(windows[entry["source_window_sha256"]], entry["case"]["dates"]) == entry["case"]
    for entry in payload.get("pattern_studies", []):
        assert candle_event_study(windows[entry["source_window_sha256"]]) == entry["case"]
    return windows
