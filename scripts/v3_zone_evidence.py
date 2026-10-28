"""Offline zone observations, with causal activation and no inferred orders.

Original research conventions, not an institutional-position detector or a
runtime trading engine. Historical outcome availability is separate from
feature availability. Source response bytes are never rewritten here.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math

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


def orderblock_features(bars, confirmation_date, direction):
    """Audit V2's formation arithmetic, not all its active-pattern/API gates.

    Frame-agnostic original convention; daily educational captures are not
    runtime 15m candidates. Availability is C's close, not origin or B's close.
    """
    assert direction in ("long", "short")
    i = next(i for i, b in enumerate(bars) if utc_day(b["time"]) == confirmation_date)
    assert i >= 21, "twenty bars strictly before displacement required"
    a, b, c = bars[i-2:i+1]
    bull = direction == "long"
    low, high = (a["high"], c["low"]) if bull else (c["high"], a["low"])
    baseline = math.fsum(abs(x["close"]-x["open"]) for x in bars[i-21:i-1])/20
    body = b["close"]-b["open"] if bull else b["open"]-b["close"]
    preceding = bars[i-6:i-1]
    reference = max(x["high"] for x in preceding) if bull else min(x["low"] for x in preceding)
    broke = b["close"] > reference if bull else b["close"] < reference
    opposite = [x for x in preceding if (x["close"] < x["open"] if bull else x["close"] > x["open"])]
    assert low < high and baseline > 0 and body >= 1.5*baseline and broke and opposite, "formation not qualified"
    origin = opposite[-1]
    return {"method": "hoshi-v2-orderblock-formation-audit-1", "direction": direction,
            "kind": "demand" if bull else "supply", "origin": bar_record(origin),
            "displacement": bar_record(b), "confirmation": bar_record(c),
            "known_at": c["close_time"], "zone_low": origin["low"], "zone_high": origin["high"],
            "gap_low": low, "gap_high": high, "preceding_20_body_mean": baseline,
            "directional_body": body, "body_multiple": body/baseline,
            "five_bar_break_reference": reference, "orders_enabled": False,
            "institutional_intent_known": False, "win_probability": None}


def orderblock_case(bars, confirmation_date, direction):
    f = orderblock_features(bars, confirmation_date, direction)
    observed = observe_zone(bars, f)
    if observed["outcome"] is not None:
        path = observed["outcome"]["path"]
        fully_crossed = next((b for b in path if (b["low"] <= f["gap_low"] if direction == "long"
                                                else b["high"] >= f["gap_high"])), None)
        observed["outcome"]["first_full_gap_crossing"] = fully_crossed
    return {"features": f, **observed}


def role_retest_features(bars, break_date, direction):
    """Original confirmed three-swing role-change hypotheses, not ICT parity.

    Highest/lowest body origin conventions differ by educator. Here the
    latest same-direction origin at/within two bars before the middle pivot
    is selected, strictly inside the first-to-middle leg. No trader intent
    or real stop order is inferred from an extreme being crossed.
    """
    assert direction in ("long", "short")
    i = next(i for i, b in enumerate(bars) if utc_day(b["time"]) == break_date)
    assert i >= 1
    known = pivots(bars[:i])
    assert len(known) >= 3
    first, middle, last = known[-3:]
    bull = direction == "long"
    assert [p["kind"] for p in (first,middle,last)] == (["low","high","low"] if bull else ["high","low","high"])
    assert first["pivot_at"] < middle["pivot_at"] < last["pivot_at"]
    assert all(p["confirmed_at"] < bars[i]["time"] for p in (first,middle,last))
    assert first["price"] != last["price"], "equal-extreme sequence is ambiguous"
    crossed = (bars[i-1]["close"] <= middle["price"] < bars[i]["close"] if bull else
               bars[i]["close"] < middle["price"] <= bars[i-1]["close"])
    assert crossed
    prior_after_middle = [b for b in bars[:i] if b["close_time"] > middle["confirmed_at"]]
    assert not any((b["close"] > middle["price"] if bull else b["close"] < middle["price"])
                   for b in prior_after_middle), "reference already broken"
    mid_i = next(k for k,b in enumerate(bars) if b["close_time"] == middle["pivot_at"])
    origins = [b for b in bars[max(0,mid_i-2):mid_i+1]
               if b["close_time"] > first["pivot_at"]
               and (b["close"] > b["open"] if bull else b["close"] < b["open"])]
    assert origins, "missing original-rule zone candle"
    origin = origins[-1]
    swept = last["price"] < first["price"] if bull else last["price"] > first["price"]
    return {"method": "hoshi-confirmed-three-swing-role-retest-1", "direction": direction,
            "kind": "demand" if bull else "supply", "origin": bar_record(origin),
            "first_swing": first, "middle_swing": middle, "last_swing": last,
            "variant": "swept_extreme_role_retest" if swept else "failed_swing_role_retest",
            "event": bar_record(bars[i]), "known_at": bars[i]["close_time"],
            "zone_low": origin["low"], "zone_high": origin["high"],
            "creator_parity_validated": False, "actual_stops_known": False,
            "institutional_intent_known": False, "orders_enabled": False, "win_probability": None}


def role_retest_case(bars, break_date, direction):
    f = role_retest_features(bars, break_date, direction)
    return {"features": f, **observe_zone(bars, f)}


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
    for entry in payload.get("orderblock_cases", []):
        f = entry["case"]["features"]
        assert orderblock_case(windows[entry["source_window_sha256"]],
                               f["confirmation"]["date"], f["direction"]) == entry["case"]
    for entry in payload.get("role_retest_cases", []):
        f = entry["case"]["features"]
        assert role_retest_case(windows[entry["source_window_sha256"]],
                                f["event"]["date"], f["direction"]) == entry["case"]
    return windows
