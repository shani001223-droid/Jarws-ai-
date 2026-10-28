"""Original offline SMC geometry evidence, never runtime signals or fills.

Features use prior-confirmed reference levels and event-close information.
Later descriptive outcomes carry a separate availability clock. Terminology
is explicitly HOSHI's convention, not parity with a third-party indicator.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math

from v3_structure_evidence import check_window, pivots, summarize, utc_day
from v3_zone_evidence import bar_record

SOURCE = "knowledge_base/01_MARKET_STRUCTURE/structure_observations_20261028.json"


def displacement(bars, index):
    if index < 20:
        return {"status": "insufficient_prior_bars", "body_multiple": None,
                "up_qualified": None, "down_qualified": None}
    b = bars[index]
    baseline = math.fsum(abs(x["close"]-x["open"]) for x in bars[index-20:index])/20
    absolute_body = abs(b["close"]-b["open"])
    high = max(x["high"] for x in bars[index-5:index])
    low = min(x["low"] for x in bars[index-5:index])
    large = baseline > 0 and absolute_body >= 1.5*baseline
    return {"status": "observed" if baseline > 0 else "zero_body_baseline",
            "preceding_20_body_mean": baseline, "absolute_body": absolute_body,
            "body_multiple": absolute_body/baseline if baseline > 0 else None,
            "prior_five_high": high, "prior_five_low": low,
            "up_qualified": bool(large and b["close"] > b["open"] and b["close"] > high),
            "down_qualified": bool(large and b["close"] < b["open"] and b["close"] < low)}


def structure_features(bars, event_date):
    i = next(i for i, b in enumerate(bars) if utc_day(b["time"]) == event_date)
    assert i >= 1
    event, previous = bars[i], bars[i-1]
    prior = bars[:i]
    known = pivots(prior)
    assert all(p["confirmed_at"] < event["time"] for p in known)
    highs = [p for p in known if p["kind"] == "high"]
    lows = [p for p in known if p["kind"] == "low"]
    high = highs[-1] if highs else None
    low = lows[-1] if lows else None
    state = summarize(prior)["structure"]
    raw_up = bool(high and previous["close"] <= high["price"] < event["close"])
    raw_down = bool(low and event["close"] < low["price"] <= previous["close"])
    high_consumed = bool(high and any(b["close"] > high["price"] for b in prior
                                     if b["close_time"] > high["confirmed_at"]))
    low_consumed = bool(low and any(b["close"] < low["price"] for b in prior
                                   if b["close_time"] > low["confirmed_at"]))
    up = raw_up and not high_consumed
    down = raw_down and not low_consumed
    if up and down:
        label = "ambiguous_reference_crossing"
    elif up:
        label = ("bos_up" if state == "higher_highs_higher_lows" else
                 "choch_up" if state == "lower_highs_lower_lows" else "unclassified_up_break")
    elif down:
        label = ("bos_down" if state == "lower_highs_lower_lows" else
                 "choch_down" if state == "higher_highs_higher_lows" else "unclassified_down_break")
    elif raw_up or raw_down:
        label = "previously_broken_reference_recross"
    else:
        label = "no_new_close_break"
    return {"method": "hoshi-prior-confirmed-close-break-1", "event": bar_record(event),
            "known_at": event["close_time"], "prior_state": state,
            "prior_close": previous["close"], "latest_known_high": high, "latest_known_low": low,
            "up_close_crossing": up, "down_close_crossing": down,
            "raw_up_close_crossing": raw_up, "raw_down_close_crossing": raw_down,
            "high_reference_previously_broken": high_consumed, "low_reference_previously_broken": low_consumed,
            "up_wick_beyond_reference": bool(high and event["high"] > high["price"]),
            "down_wick_beyond_reference": bool(low and event["low"] < low["price"]),
            "label": label, "displacement": displacement(bars, i),
            "orders_enabled": False, "institutional_intent_known": False, "win_probability": None}


def structure_case(bars, event_date):
    f = structure_features(bars, event_date)
    i = next(i for i, b in enumerate(bars) if b["close_time"] == f["known_at"])
    future = bars[i+1:i+6]
    if len(future) != 5:
        return {"features": f, "outcome_status": "incomplete", "outcome": None}
    return {"features": f, "outcome_status": "observed", "outcome": {
        "available_at": future[-1]["close_time"], "horizon_bars": 5,
        "path": [bar_record(b) for b in future],
        "raw_close_change_pct": (future[-1]["close"]/f["event"]["close"]-1)*100,
        "strategy_pnl": None, "fill_known": False}}


def check_receipt(payload, root):
    assert payload["schema_version"] == "hoshi-v3-smc-evidence-1"
    assert payload["source_receipt"] == SOURCE
    assert payload["data_license"] == "CC BY-NC-SA 4.0"
    raw = (root / SOURCE).read_bytes()
    assert sha256(raw).hexdigest() == payload["source_receipt_sha256"]
    source = json.loads(raw)
    windows = {x["source_sha256"]: check_window(x) for x in source["observations"]}
    for entry in payload["structure_cases"]:
        f = entry["case"]["features"]
        assert structure_case(windows[entry["source_window_sha256"]], f["event"]["date"]) == entry["case"]
    return windows
