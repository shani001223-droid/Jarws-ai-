"""Offline zone observations, with causal activation and no inferred orders.

Original research conventions, not an institutional-position detector or a
runtime trading engine. Historical outcome availability is separate from
feature availability. Source response bytes are never rewritten here.
"""
from __future__ import annotations

from hashlib import sha256
import json

from v3_structure_evidence import check_window, pivots, utc_day

SOURCE = "knowledge_base/01_MARKET_STRUCTURE/structure_observations_20261028.json"


def bar_record(bar):
    return {"date": utc_day(bar["time"]), "close_time": bar["close_time"],
            **{k: bar[k] for k in ("open", "high", "low", "close")}}


def pivot_zone_features(bars, origin_date, kind):
    assert kind in ("demand", "supply")
    i = next(i for i, b in enumerate(bars) if utc_day(b["time"]) == origin_date)
    origin = bars[i]
    wanted = "low" if kind == "demand" else "high"
    pivot = next(p for p in pivots(bars)
                 if p["pivot_at"] == origin["close_time"] and p["kind"] == wanted)
    low = origin["low"] if kind == "demand" else max(origin["open"], origin["close"])
    high = min(origin["open"], origin["close"]) if kind == "demand" else origin["high"]
    assert low < high, "zero-width wick zone is ineligible"
    return {"method": "hoshi-confirmed-pivot-wick-zone-1", "kind": kind,
            "origin": bar_record(origin), "zone_low": low, "zone_high": high,
            "known_at": pivot["confirmed_at"], "confirmation": bar_record(bars[i+2]),
            "orders_enabled": False, "institutional_intent_known": False,
            "win_probability": None}


def observe_zone(bars, features, horizon=20):
    """First post-activation contact/rejection/breach, frozen 20-bar horizon.

    Stop the active lifecycle at the first invalidating close. Contact on that
    same bar does not override invalidation. Full OHLC paths cannot resolve
    within-bar fill order. A partial horizon produces a null outcome.
    """
    assert type(horizon) is int and horizon == 20
    active = next(i for i, b in enumerate(bars) if b["close_time"] == features["known_at"])
    future = bars[active+1:active+1+horizon]
    if len(future) != horizon:
        return {"outcome_status": "incomplete", "outcome": None}
    low, high = features["zone_low"], features["zone_high"]
    demand = features["kind"] == "demand"
    first_contact = first_rejection = close_breach = wick_breach = None
    contacts = []
    for b in future:
        if close_breach is not None:
            break
        contact = b["low"] <= high and b["high"] >= low
        wrong_close = b["close"] < low if demand else b["close"] > high
        wrong_wick = b["low"] < low if demand else b["high"] > high
        if wrong_wick and wick_breach is None:
            wick_breach = bar_record(b)
        if contact:
            contacts.append(b["close_time"])
            if first_contact is None:
                first_contact = bar_record(b)
        if wrong_close:
            close_breach = bar_record(b)
        elif contact and first_rejection is None and (b["close"] > high if demand else b["close"] < low):
            first_rejection = bar_record(b)
    return {"outcome_status": "observed", "outcome": {
        "horizon_bars": horizon, "available_at": future[-1]["close_time"],
        "path": [bar_record(b) for b in future], "first_contact": first_contact,
        "first_closing_rejection": first_rejection, "first_wick_breach": wick_breach,
        "first_close_breach": close_breach, "contact_bar_closes_before_or_at_breach": contacts,
        "status": "invalidated" if close_breach else "observed_without_close_breach",
        "strategy_pnl": None, "fill_known": False}}


def pivot_zone_case(bars, origin_date, kind):
    features = pivot_zone_features(bars, origin_date, kind)
    return {"features": features, **observe_zone(bars, features)}


def check_receipt(payload, root):
    assert payload["schema_version"] == "hoshi-v3-zone-evidence-1"
    assert payload["source_receipt"] == SOURCE
    assert payload["data_license"] == "CC BY-NC-SA 4.0"
    raw = (root / SOURCE).read_bytes()
    assert sha256(raw).hexdigest() == payload["source_receipt_sha256"]
    source = json.loads(raw)
    windows = {x["source_sha256"]: check_window(x) for x in source["observations"]}
    for entry in payload["pivot_zone_cases"]:
        f = entry["case"]["features"]
        assert pivot_zone_case(windows[entry["source_window_sha256"]],
                               f["origin"]["date"], f["kind"]) == entry["case"]
    return windows
