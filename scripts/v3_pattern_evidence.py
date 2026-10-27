"""Offline pattern measurements from hash-checked historical candles.

Original HOSHI geometric research conventions, NOT a TA-Lib port, trained
model, runtime signal, probability or order simulator. Features and subsequent
outcomes have different availability times. No network requests are made.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from v3_structure_evidence import check_window, utc_day

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
    return windows
