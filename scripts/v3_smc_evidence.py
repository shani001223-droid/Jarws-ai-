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
from v3_zone_evidence import orderblock_features

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


def range_location(price, low, high):
    if low is None or high is None or low >= high:
        return {"status": "unavailable_or_invalid_range", "midpoint": None,
                "position_fraction": None, "location": None, "inside_range": False}
    midpoint = (low+high)/2
    location = ("outside_below" if price < low else "outside_above" if price > high else
                "discount" if price < midpoint else "premium" if price > midpoint else "equilibrium")
    return {"status": "observed" if low <= price <= high else "outside_reference_range",
            "midpoint": midpoint, "position_fraction": (price-low)/(high-low),
            "location": location, "inside_range": low <= price <= high}


def range_features(bars, event_date):
    f = structure_features(bars, event_date)
    i = next(i for i, b in enumerate(bars) if b["close_time"] == f["known_at"])
    high, low = f["latest_known_high"], f["latest_known_low"]
    price = f["event"]["close"]
    result = {"method": "hoshi-prior-confirmed-dealing-range-1", "event": f["event"],
              "known_at": f["known_at"], "high_anchor": high, "low_anchor": low,
              "price": price, **range_location(price, low["price"] if low else None,
                                                high["price"] if high else None),
              "orders_enabled": False, "fundamental_value_known": False, "win_probability": None}
    if i >= 20:
        prior = bars[i-20:i]
        lo, hi = min(b["low"] for b in prior), max(b["high"] for b in prior)
        result["alternate_prior_20_range"] = {"low": lo, "high": hi, **range_location(price, lo, hi)}
    else:
        result["alternate_prior_20_range"] = None
    close_known = pivots(bars[:i+1])
    close_highs = [p for p in close_known if p["kind"] == "high"]
    close_lows = [p for p in close_known if p["kind"] == "low"]
    ch = close_highs[-1] if close_highs else None
    cl = close_lows[-1] if close_lows else None
    result["alternate_asof_close_anchors"] = {
        "high_anchor": ch, "low_anchor": cl,
        **range_location(price, cl["price"] if cl else None, ch["price"] if ch else None)}
    return result


def range_case(bars, event_date):
    f = range_features(bars, event_date)
    i = next(i for i, b in enumerate(bars) if b["close_time"] == f["known_at"])
    future = bars[i+1:i+6]
    if len(future) != 5 or f["status"] == "unavailable_or_invalid_range":
        return {"features": f, "outcome_status": "incomplete_or_invalid_range", "outcome": None}
    low, high = f["low_anchor"]["price"], f["high_anchor"]["price"]
    below = next((b for b in future if b["close"] < low), None)
    above = next((b for b in future if b["close"] > high), None)
    return {"features": f, "outcome_status": "observed", "outcome": {
        "available_at": future[-1]["close_time"], "horizon_bars": 5,
        "path": [bar_record(b) for b in future],
        "first_close_below_frozen_low": bar_record(below) if below else None,
        "first_close_above_frozen_high": bar_record(above) if above else None,
        "raw_close_change_pct": (future[-1]["close"]/f["price"]-1)*100,
        "strategy_pnl": None, "fill_known": False}}


def sequence_features(bars, confirmation_date, direction):
    """Original sweep -> fresh close-break -> C gap chain, not full V2.

    Sweep must be in the three bars STRICTLY before displacement B and reclaim
    the latest pivot known before its own open. No later timestamps are read.
    """
    assert direction in ("long", "short")
    i = next(i for i, b in enumerate(bars) if utc_day(b["time"]) == confirmation_date)
    assert i >= 21
    bull = direction == "long"
    b = i-1
    break_features = structure_features(bars, utc_day(bars[b]["time"]))
    break_passed = break_features["up_close_crossing" if bull else "down_close_crossing"]
    impulse_passed = break_features["displacement"]["up_qualified" if bull else "down_qualified"]
    sweeps = []
    for k in range(b-3, b):
        known = [p for p in pivots(bars[:k]) if p["kind"] == ("low" if bull else "high")]
        if not known:
            continue
        reference = known[-1]
        event = bars[k]
        reclaim = (event["low"] < reference["price"] < event["close"] if bull else
                   event["close"] < reference["price"] < event["high"])
        if reclaim:
            sweeps.append({"event": bar_record(event), "reference": reference,
                           "known_at": event["close_time"]})
    sweep = sweeps[-1] if sweeps else None
    try:
        formation = orderblock_features(bars, confirmation_date, direction)
    except AssertionError:
        formation = None
    initial_valid = bool(formation and (bars[i]["close"] >= formation["zone_low"] if bull
                                       else bars[i]["close"] <= formation["zone_high"]))
    missing = []
    if sweep is None:
        missing.append("no_prior_three_bar_sweep_reclaim")
    if not break_passed:
        missing.append("no_fresh_prior_reference_close_break")
    if not impulse_passed:
        missing.append("no_displacement")
    if formation is None:
        missing.append("no_qualified_orderblock_gap_formation")
    elif not initial_valid:
        missing.append("origin_close_invalid_at_confirmation")
    return {"method": "hoshi-sweep-break-gap-audit-1", "direction": direction,
            "confirmation": bar_record(bars[i]), "known_at": bars[i]["close_time"],
            "sweep": sweep, "break": break_features, "formation": formation,
            "price_sequence_qualified": not missing, "missing_price_conditions": missing,
            "decision": "WAIT", "runtime_integrated": False, "orders_enabled": False,
            "win_probability": None, "missing_full_strategy_inputs": [
                "higher_timeframe_alignment", "liquidity_target", "joint_orderblock_overlap",
                "global_flow", "session_and_news_context", "current_source_freshness_and_crosscheck",
                "actual_execution_inputs", "independent_calibration"]}


def sequence_case(bars, confirmation_date, direction):
    f = sequence_features(bars, confirmation_date, direction)
    i = next(i for i, b in enumerate(bars) if b["close_time"] == f["known_at"])
    future = bars[i+1:i+6]
    if len(future) != 5:
        return {"features": f, "outcome_status": "incomplete", "outcome": None}
    contact = eligible = invalidation = None
    if f["price_sequence_qualified"]:
        formation = f["formation"]
        lo, hi = formation["gap_low"], formation["gap_high"]
        bull = direction == "long"
        for bar in future:
            overlap = bar["low"] <= hi and bar["high"] >= lo
            if overlap and contact is None:
                contact = bar_record(bar)
            full_cross = bar["low"] <= lo if bull else bar["high"] >= hi
            block_breach = bar["close"] < formation["zone_low"] if bull else bar["close"] > formation["zone_high"]
            if full_cross or block_breach:
                invalidation = {"bar": bar_record(bar), "full_gap_crossing": full_cross,
                                "block_close_breach": block_breach}
                break
            hold = bar["close"] >= (lo+hi)/2 if bull else bar["close"] <= (lo+hi)/2
            if overlap and hold and eligible is None:
                eligible = bar_record(bar)
    return {"features": f, "outcome_status": "observed", "outcome": {
        "available_at": future[-1]["close_time"], "horizon_bars": 5,
        "path": [bar_record(b) for b in future], "first_gap_contact": contact,
        "first_eligible_geometric_retest": eligible, "first_invalidation": invalidation,
        "retest_status": ("not_qualified_at_formation" if not f["price_sequence_qualified"] else
                          "eligible_geometric_event_not_trade" if eligible else
                          "invalidated_before_eligible_retest" if invalidation else "no_eligible_retest_in_window"),
        "strategy_pnl": None, "fill_known": False}}


def sequence_study(bars):
    """Exhaust all directional C decisions in one already-inspected capture.

    This is a descriptive curriculum ledger, not independent strategy
    evaluation. Preserve all formation rows, including rejected chains.
    """
    rows = []
    qualified = eligible = invalid_before = no_retest = incomplete_chains = 0
    for i in range(21, len(bars)):
        for direction in ("long", "short"):
            case = sequence_case(bars, utc_day(bars[i]["time"]), direction)
            f, outcome = case["features"], case["outcome"]
            if f["formation"] is None:
                continue
            q = f["price_sequence_qualified"]
            status = outcome["retest_status"] if outcome else "incomplete"
            qualified += q
            eligible += q and status == "eligible_geometric_event_not_trade"
            invalid_before += q and status == "invalidated_before_eligible_retest"
            no_retest += q and status == "no_eligible_retest_in_window"
            incomplete_chains += q and outcome is None
            rows.append({"confirmation_date": f["confirmation"]["date"], "direction": direction,
                         "known_at": f["known_at"], "origin_date": f["formation"]["origin"]["date"],
                         "sweep_date": f["sweep"]["event"]["date"] if f["sweep"] else None,
                         "break_label": f["break"]["label"], "price_sequence_qualified": q,
                         "missing_price_conditions": f["missing_price_conditions"],
                         "outcome_status": case["outcome_status"], "retest_status": status,
                         "outcome_available_at": outcome["available_at"] if outcome else None,
                         "eligible_retest_date": outcome["first_eligible_geometric_retest"]["date"]
                            if outcome and outcome["first_eligible_geometric_retest"] else None,
                         "invalidation_date": outcome["first_invalidation"]["bar"]["date"]
                            if outcome and outcome["first_invalidation"] else None,
                         "raw_five_bar_close_change_pct": (outcome["path"][-1]["close"]/f["confirmation"]["close"]-1)*100
                            if outcome else None,
                         "decision": f["decision"]})
    overlaps = sum(0 < b["known_at"]-a["known_at"] < 5*86_400_000
                   for i,a in enumerate(rows) for b in rows[i+1:])
    origins = {}
    for row in rows:
        origins.setdefault((row["origin_date"], row["direction"]), []).append(row["confirmation_date"])
    duplicate_origins = [{"origin_date": date, "direction": direction, "confirmation_dates": dates}
                         for (date,direction),dates in sorted(origins.items()) if len(dates) > 1]
    return {"method": "hoshi-exploratory-sequence-ledger-1", "sequence_method": "hoshi-sweep-break-gap-audit-1",
            "window_start": utc_day(bars[0]["time"]), "window_end": utc_day(bars[-1]["time"]),
            "source_bars": len(bars), "warmup_bars": 21,
            "directional_decisions": max(0,len(bars)-21)*2,
            "decisions_with_complete_five_bar_horizon": max(0,len(bars)-26)*2,
            "decisions_with_incomplete_horizon": min(5,max(0,len(bars)-21))*2,
            "formation_count": len(rows), "qualified_price_chains": qualified,
            "eligible_geometric_retest_chains": eligible, "invalid_before_eligible_retest_chains": invalid_before,
            "no_eligible_retest_chains": no_retest, "incomplete_qualified_chains": incomplete_chains,
            "formation_horizon_overlap_pairs": overlaps, "duplicate_origin_groups": duplicate_origins,
            "formation_rows": rows, "all_decisions_wait": True, "orders_submitted": 0,
            "simulated_trade_count": None, "win_probability": None, "strategy_pnl": None,
            "drawdown": None, "costs_measured": False, "independent_holdout": False}


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
    for entry in payload.get("range_cases", []):
        f = entry["case"]["features"]
        assert range_case(windows[entry["source_window_sha256"]], f["event"]["date"]) == entry["case"]
    for entry in payload.get("sequence_cases", []):
        f = entry["case"]["features"]
        assert sequence_case(windows[entry["source_window_sha256"]],
                             f["confirmation"]["date"], f["direction"]) == entry["case"]
    for entry in payload.get("sequence_studies", []):
        assert sequence_study(windows[entry["source_window_sha256"]]) == entry["study"]
    return windows
