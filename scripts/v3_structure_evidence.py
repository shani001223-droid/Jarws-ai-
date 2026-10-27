"""Offline, causal OHLCV evidence for V3 chapters; no network or trade signals.

Historical candles are one-venue observations, not executable prices or model
training. The two-right-bar rule matches the existing structure vocabulary.
Weekly aggregation is Monday 00:00 UTC through Sunday 23:59:59.999 UTC and
deliberately drops partial weeks. This is research tooling, not runtime wiring.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from urllib.parse import parse_qs, urlsplit

DAY = 86_400_000
WEEK = 7 * DAY


def utc_day(stamp):
    return datetime.fromtimestamp(stamp / 1000, timezone.utc).date().isoformat()


def normalized(rows):
    assert isinstance(rows, list) and 5 <= len(rows) <= 1000
    result = []
    for row in rows:
        assert isinstance(row, list) and len(row) == 12
        start, end = row[0], row[6]
        assert type(start) is int and type(end) is int
        assert start >= 0 and start % DAY == 0 and end == start + DAY - 1
        values = [float(row[i]) for i in (1, 2, 3, 4, 5)]
        assert all(math.isfinite(x) for x in values)
        op, hi, lo, cl, vol = values
        assert 0 < lo <= min(op, cl) <= max(op, cl) <= hi and vol >= 0
        assert not result or start == result[-1]["time"] + DAY
        result.append(dict(time=start, close_time=end, open=op, high=hi,
                           low=lo, close=cl, volume=vol))
    return result


def pivots(bars):
    """Return strict 2-left/2-right pivots with their actual knowledge times."""
    result = []
    for i in range(2, len(bars) - 2):
        bar = bars[i]
        others = bars[i-2:i] + bars[i+1:i+3]
        for kind in ("high", "low"):
            price = bar[kind]
            qualifies = (all(price > b[kind] for b in others) if kind == "high"
                         else all(price < b[kind] for b in others))
            if qualifies:
                result.append({"kind": kind, "price": price,
                               "pivot_at": bar["close_time"],
                               "confirmed_at": bars[i+2]["close_time"]})
    return result


def summarize(bars):
    known = pivots(bars)
    highs = [x for x in known if x["kind"] == "high"][-2:]
    lows = [x for x in known if x["kind"] == "low"][-2:]
    state = "insufficient_confirmed_swings"
    if len(highs) == len(lows) == 2:
        if highs[-1]["price"] > highs[-2]["price"] and lows[-1]["price"] > lows[-2]["price"]:
            state = "higher_highs_higher_lows"
        elif highs[-1]["price"] < highs[-2]["price"] and lows[-1]["price"] < lows[-2]["price"]:
            state = "lower_highs_lower_lows"
        else:
            state = "mixed_structure"
    close = bars[-1]["close"] if bars else None
    return {"bar_count": len(bars), "last_close": close,
            "last_closed_at": bars[-1]["close_time"] if bars else None,
            "structure": state, "last_two_highs": highs, "last_two_lows": lows,
            "close_below_latest_confirmed_low": bool(lows and close < lows[-1]["price"]),
            "close_above_latest_confirmed_high": bool(highs and close > highs[-1]["price"])}


def full_weeks(bars):
    """Aggregate only complete Monday-to-Sunday UTC weeks in this prefix."""
    groups = {}
    for b in bars:
        weekday = datetime.fromtimestamp(b["time"] / 1000, timezone.utc).weekday()
        groups.setdefault(b["time"] - weekday * DAY, []).append(b)
    result = []
    for start, group in sorted(groups.items()):
        if len(group) != 7 or group[0]["time"] != start or group[-1]["time"] != start + 6*DAY:
            continue
        result.append({"time": start, "close_time": start + WEEK - 1,
                       "open": group[0]["open"], "high": max(b["high"] for b in group),
                       "low": min(b["low"] for b in group), "close": group[-1]["close"],
                       "volume": sum(b["volume"] for b in group)})
    return result


def snapshot(bars, as_of_date):
    prefix = [b for b in bars if utc_day(b["time"]) <= as_of_date]
    assert prefix and utc_day(prefix[-1]["time"]) == as_of_date
    day_state = summarize(prefix)
    prior = prefix[-21:-1] if len(prefix) >= 21 else []
    band = {"lookback_bars": 20, "upper": max(b["high"] for b in prior) if prior else None,
            "lower": min(b["low"] for b in prior) if prior else None}
    return {"as_of_date": as_of_date, "as_of_utc": datetime.fromtimestamp(
                prefix[-1]["close_time"]/1000, timezone.utc).isoformat(timespec="milliseconds"),
            "daily": day_state, "weekly": summarize(full_weeks(prefix)), "prior_20_day_band": band}


def breakout_case(bars, event_date):
    """Separate a prior-only event from a fixed five-bar retrospective outcome.

    The event is a close beyond the PRECEDING 20 daily wick extremes. A later
    wick overlap with the frozen boundary is only a geometric contact, never a
    fill. Forward close change is an unsigned-direction price observation, not
    short/long PnL. No thresholds are fit to these selected teaching cases.
    """
    index = next(i for i, b in enumerate(bars) if utc_day(b["time"]) == event_date)
    assert index >= 20
    event, prior = bars[index], bars[index-20:index]
    upper, lower = max(b["high"] for b in prior), min(b["low"] for b in prior)
    direction = "above" if event["close"] > upper else "below" if event["close"] < lower else None
    assert direction is not None, "No qualifying close-break event"
    level = upper if direction == "above" else lower
    result = {"event_date": event_date, "known_at": event["close_time"],
              "direction": direction, "frozen_level": level, "event_close": event["close"],
              "prior_window_start": utc_day(prior[0]["time"]),
              "prior_window_end": utc_day(prior[-1]["time"]), "prior_bars": 20}
    future = bars[index+1:index+6]
    if len(future) != 5:
        return {**result, "outcome_status": "incomplete", "outcome": None}
    contacts = [utc_day(b["time"]) for b in future if b["low"] <= level <= b["high"]]
    returned = [utc_day(b["time"]) for b in future
                if (b["close"] <= level if direction == "above" else b["close"] >= level)]
    return {**result, "outcome_status": "observed", "outcome": {
        "available_at": future[-1]["close_time"], "future_bars": 5,
        "contact_dates": contacts, "close_back_across_dates": returned,
        "fifth_date": utc_day(future[-1]["time"]), "fifth_close": future[-1]["close"],
        "forward_close_change_pct": (future[-1]["close"]/event["close"]-1)*100}}


def check_window(item):
    """Hash-check exact captured response, validate URL bounds and replay facts."""
    assert item["status"] == "fetched" and item["symbol"] == "BTCUSDT"
    assert item["interval"] == "1d" and item["timezone"] == "UTC"
    body = item["response_body"]
    assert isinstance(body, str) and len(body.encode()) <= 700_000
    assert sha256(body.encode()).hexdigest() == item["source_sha256"]
    url = urlsplit(item["request_url"])
    assert url.scheme == "https" and url.netloc == "data-api.binance.vision"
    assert url.path == "/api/v3/klines"
    params = parse_qs(url.query, strict_parsing=True)
    assert set(params) == {"symbol", "interval", "startTime", "endTime", "limit"}
    assert params["symbol"] == ["BTCUSDT"] and params["interval"] == ["1d"]
    assert params["limit"] == ["1000"]
    bars = normalized(json.loads(body))
    assert len(bars) == item["rows"]
    assert bars[0]["time"] == int(params["startTime"][0])
    assert bars[-1]["close_time"] == int(params["endTime"][0])
    fetched = datetime.fromisoformat(item["retrieved_at_utc"])
    assert fetched.utcoffset().total_seconds() == 0
    assert int(fetched.timestamp()*1000) > bars[-1]["close_time"]
    assert item["snapshots"] and len(item["snapshots"]) <= 30
    assert len({x["as_of_date"] for x in item["snapshots"]}) == len(item["snapshots"])
    for expected in item["snapshots"]:
        assert snapshot(bars, expected["as_of_date"]) == expected
    for expected in item.get("breakout_cases", []):
        assert breakout_case(bars, expected["event_date"]) == expected
    return bars
