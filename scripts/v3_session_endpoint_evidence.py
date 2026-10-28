"""Offline bitemporal endpoint arithmetic, NOT a CME feed or trading engine.

This is an original normalized research format. No source adapter currently
supplies its arrival/correction/calendar/coverage assertions. Synthetic tests
exercise the algorithm; they are not historical NDOG/NWOG cases. Caller flags
cannot independently prove a calendar, complete tape or license. No network,
runtime API, source prices, order capability or win probability is provided.

Primary field/state distinctions checked 2026-10-28:
https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457223239/Time%2Band%2BSales
https://www.cmegroup.com/trading-hours.html
The latter is a CURRENT page, not a certified historical calendar.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext
import re

from v3_session_evidence import timestamp_ns, check_receipt, MONTHS

SCHEMA = "hoshi-v3-session-endpoint-diagnostic-1"
MAX_EVENTS = 10000
IDENTITY = {"exchange", "instrument", "security_id", "delivery_month"}
PLAN = {"identity", "pre_start", "close", "reopen", "post_end",
        "calendar_available_at", "coverage_available_at", "calendar_applicable",
        "adjacent_windows_complete", "corrections_complete", "research_use_permitted"}
EVENT = {"trade_id", "identity", "event_time", "available_at", "arrival_order",
         "event_order", "revision", "action", "price", "quantity"}


def _stamp(value):
    if not isinstance(value, str) or len(value) != 30:
        raise ValueError("invalid_normalized_clock")
    return timestamp_ns(value)


def _integer(value, low=0, high=10**18):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid_normalized_integer")
    return value


def _identity(value):
    if not isinstance(value, dict) or set(value) != IDENTITY:
        raise ValueError("invalid_contract_identity")
    if not isinstance(value["exchange"], str) or not re.fullmatch(r"[A-Z0-9]{1,16}", value["exchange"]):
        raise ValueError("invalid_contract_identity")
    symbol = value["instrument"]
    match = re.fullmatch(r"([A-Z]{1,8})([FGHJKMNQUVXZ])(\d{1,4})", symbol) if isinstance(symbol, str) else None
    if not match:
        raise ValueError("unsupported_outright_contract_symbol")
    _integer(value["security_id"], 1)
    month = value["delivery_month"]
    if (not isinstance(month, str) or not re.fullmatch(r"[12]\d{3}(0[1-9]|1[0-2])", month)):
        raise ValueError("invalid_contract_identity")
    if MONTHS[match[2]] != int(month[-2:]) or not month[:4].endswith(match[3]):
        raise ValueError("contract_delivery_identity_conflict")
    return tuple(value[key] for key in sorted(IDENTITY))


def _price(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("invalid_normalized_price")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid_normalized_price") from exc
    if (not number.is_finite() or abs(number) > Decimal("1e12")
            or not -12 <= number.as_tuple().exponent <= 12):
        raise ValueError("invalid_normalized_price")
    return number


def _result(reasons):
    return {"schema_version": SCHEMA, "study_status": "insufficient_evidence",
            "reasons": sorted(set(reasons)), "geometry": None,
            "certified_historical_case": False, "decision": "WAIT",
            "entry": None, "stop_loss": None, "take_profit": None,
            "win_probability": None, "orders_enabled": False,
            "evidence_scope": "caller-asserted-normalized-research-not-source-certification"}


def study_endpoints(events, plan, *, as_of):
    """Select as-of known prints inside explicit half-open search windows.

    TRADE replaces the same ID at the next consecutive revision; CANCEL removes
    it. Identity, original event time and exchange order cannot change. These
    are research conventions, NOT claims about a vendor's correction protocol.
    Input arrival_order must describe genuine receipt ordering, not a sequence
    invented by sorting a final tape. Missing arrival or coverage yields WAIT.
    """
    decision = _stamp(as_of)
    if not isinstance(plan, dict) or set(plan) != PLAN:
        raise ValueError("invalid_endpoint_plan")
    identity = _identity(plan["identity"])
    start, close, reopen, end = (_stamp(plan[key]) for key in ("pre_start", "close", "reopen", "post_end"))
    if not start < close < reopen < end:
        raise ValueError("invalid_session_boundaries")
    flags = ("calendar_applicable", "adjacent_windows_complete", "corrections_complete", "research_use_permitted")
    if any(type(plan[key]) is not bool for key in flags):
        raise ValueError("invalid_evidence_assertion")
    reasons = ["unverified_" + key for key in flags if not plan[key]]
    if end > decision:
        reasons.append("post_window_not_finished")
    for key in ("calendar_available_at", "coverage_available_at"):
        if plan[key] is None:
            reasons.append("missing_" + key)
        elif _stamp(plan[key]) > decision:
            reasons.append("future_" + key)
    if (plan["coverage_available_at"] is not None
            and _stamp(plan["coverage_available_at"]) < end):
        reasons.append("coverage_asserted_before_window_end")
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise ValueError("invalid_event_count")
    normalized, arrival_keys = [], set()
    for event in events:
        if not isinstance(event, dict) or set(event) != EVENT:
            raise ValueError("invalid_normalized_event")
        contract = _identity(event["identity"])
        if not isinstance(event["trade_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", event["trade_id"]):
            raise ValueError("invalid_trade_id")
        instant = _stamp(event["event_time"])
        order = _integer(event["event_order"])
        revision = _integer(event["revision"])
        arrival_order = _integer(event["arrival_order"])
        if event["action"] == "TRADE":
            price = _price(event["price"])
            _integer(event["quantity"], 1)
        elif event["action"] == "CANCEL" and event["price"] is None and event["quantity"] is None:
            price = None
        else:
            raise ValueError("invalid_trade_action_or_fields")
        if contract != identity or instant > decision:
            continue
        if event["available_at"] is None:
            reasons.append("missing_original_arrival")
            continue
        arrival = _stamp(event["available_at"])
        if arrival < instant:
            raise ValueError("arrival_before_observation")
        if arrival > decision:
            continue
        receipt_key = (arrival, arrival_order)
        if receipt_key in arrival_keys:
            raise ValueError("ambiguous_arrival_order")
        arrival_keys.add(receipt_key)
        normalized.append((receipt_key, event, instant, order, revision, price))
    # Bad or absent prerequisites must not expose even plausible endpoint prices.
    if reasons:
        return _result(reasons)
    states = {}
    for _, event, instant, order, revision, price in sorted(normalized, key=lambda item: item[0]):
        previous = states.get(event["trade_id"])
        if previous is None:
            if revision != 0 or event["action"] != "TRADE":
                return _result(["missing_original_revision"])
        elif revision != previous[0] + 1 or (instant, order) != previous[1:3]:
            return _result(["revision_or_identity_conflict"])
        states[event["trade_id"]] = (revision, instant, order, price)
    active = [(instant, order, trade_id, price) for trade_id, (_, instant, order, price) in states.items()
              if price is not None]
    if any(close <= instant < reopen for instant, _, _, _ in active):
        return _result(["trade_during_asserted_closure"])
    before = [item for item in active if start <= item[0] < close]
    after = [item for item in active if reopen <= item[0] < end]
    if not before or not after:
        return _result(["missing_pre_break_trade" if not before else "missing_post_reopen_trade"])
    # Never use receipt order or a lexical ID to resolve equal exchange clocks.
    for group in (before, after):
        keys = [(item[0], item[1]) for item in group]
        if len(set(keys)) != len(keys):
            return _result(["ambiguous_exchange_order"])
    left, right = max(before, key=lambda item: item[:2]), min(after, key=lambda item: item[:2])
    with localcontext() as context:
        context.prec = 64
        gap = right[3] - left[3]
        midpoint = (left[3] + right[3]) / 2
    result = _result([])
    result.update(study_status="uncertified_research_geometry", geometry={
        "pre_trade_id": left[2], "post_trade_id": right[2],
        "pre_event_ns": left[0], "post_event_ns": right[0],
        "signed_gap": str(gap), "width": str(abs(gap)), "midpoint": str(midpoint),
        "price_units": "same-identified-instrument-price-units-no-tick-rounding-or-fill"})
    return result


def unresolved_source_requirements(receipt):
    """Explain the actual metadata receipt's gaps without accessing raw prices."""
    check_receipt(receipt)
    audit = receipt["audit"]
    reasons = [key for key in ("session_calendar_verified", "adjacent_session_coverage_verified",
                               "executed_trade_coverage_certified", "redistribution_permission_verified")
               if audit[key] is False]
    if audit["original_historical_arrival_utc"] is None:
        reasons.append("original_historical_arrival_utc")
    result = _result(reasons)
    result["source_sha256"] = audit["source_sha256"]
    result["eligible_opening_gap_case_count"] = 0
    return result
