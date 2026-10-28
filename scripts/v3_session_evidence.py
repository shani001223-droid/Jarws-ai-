"""Offline CME v2 sample audit; this is not a feed, calendar or gap strategy.

Primary layout checked 2026-10-28:
https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457223239/Time%2Band%2BSales

A public ES part-file includes spreads as well as outright contracts. Preserve
exact instrument identity and nanoseconds; never call a part-file's endpoints
the exchange session's last/first trades. No prices are exported. Sample access
does not establish redistribution permission or original historical arrival.
"""
from __future__ import annotations

import argparse
import calendar
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import io
import json
from pathlib import Path
import re

SCHEMA = "hoshi-v3-session-source-audit-1"
LAYOUT_URL = "https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457223239/Time%2Band%2BSales"
SAMPLE_URL = "https://www.cmegroup.com/files/download/xcme-tick-es-fut-20250312-part-00039-c000.csv"
MAX_BYTES = 256_000_000
MAX_ROWS = 2_000_000
MAX_GROUPS = 500
HEADER = (
    "Transaction_Date", "Transaction_Time", "Sequence_Number", "Ticker_Symbol",
    "Instrument_Symbol", "Security_ID", "Future_Option_Index_Indicator",
    "Delivery_Date", "Put_Call_Indicator", "Strike_Price", "Market_Data_Report_Type",
    "Trade_Price_Formatted", "Trade_Price_Decimal", "Trade_Quantity", "Vol_Quantity",
    "Trade_Aggressor", "Close_Open_Type", "User_Defined", "Exchange_Code",
)
MONTHS = {code: month for month, code in enumerate("FGHJKMNQUVXZ", 1)}
STAMP = re.compile(r"(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})\.(\d{9})Z")


def timestamp_ns(value: str) -> int:
    """Require the documented UTC/nanosecond form; do not truncate to micros."""
    match = STAMP.fullmatch(value)
    if not match:
        raise ValueError("unsupported_timestamp_precision_or_zone")
    day, hour, minute, second, fraction = match.groups()
    try:
        stamp = datetime.fromisoformat(f"{day}T{hour}:{minute}:{second}+00:00")
    except ValueError as exc:
        raise ValueError("invalid_timestamp") from exc
    return calendar.timegm(stamp.utctimetuple()) * 1_000_000_000 + int(fraction)


def _decimal(value: str) -> Decimal:
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid_numeric_field") from exc
    if not number.is_finite():
        raise ValueError("nonfinite_numeric_field")
    return number


def _positive_integer(value: str) -> int:
    if not value.isascii() or not value.isdecimal() or int(value) <= 0:
        raise ValueError("invalid_positive_integer")
    return int(value)


def _outright(row: dict) -> bool:
    if row["Future_Option_Index_Indicator"] != "FUT":
        return False
    match = re.fullmatch(re.escape(row["Ticker_Symbol"]) + r"([FGHJKMNQUVXZ])(\d{1,2})",
                         row["Instrument_Symbol"])
    if not match:
        return False
    delivery = row["Delivery_Date"]
    if not re.fullmatch(r"\d{6}", delivery):
        raise ValueError("invalid_delivery_month")
    code, year_suffix = match.groups()
    if (int(delivery[4:]) != MONTHS[code]
            or not delivery[:4].endswith(year_suffix)):
        raise ValueError("contract_delivery_identity_conflict")
    return True


def audit_csv(raw: bytes, *, captured_at_utc: str, complete_http_body: bool) -> dict:
    """Describe one source payload, without certifying any session boundaries.

    The caller is a trusted offline researcher, not an HTTP client. A true
    complete_http_body means EOF was observed for this part-file only. It never
    means all parts, corrections, adjacent sessions or source permissions exist.
    """
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("invalid_capture_size")
    if type(complete_http_body) is not bool:
        raise ValueError("invalid_capture_completeness")
    try:
        captured = datetime.fromisoformat(captured_at_utc)
        if captured.tzinfo is None or captured.utcoffset().total_seconds() != 0:
            raise ValueError("capture_time_requires_utc")
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid_capture_time") from exc
    capture_ns = (calendar.timegm(captured.utctimetuple()) * 1_000_000_000
                  + captured.microsecond * 1000)
    rows = 0
    report_types, instrument_kinds = Counter(), Counter()
    groups, previous_by_ticker = {}, {}
    sequence_regressions = 0
    non_outright_trade_rows = 0
    unusable_trade_reasons = Counter()
    unsequenced_volume_rows = 0
    try:
        reader = csv.reader(io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8-sig", newline=""),
                            strict=True)
        if tuple(next(reader)) != HEADER:
            raise ValueError("unsupported_csv_layout")
        for fields in reader:
            rows += 1
            if rows > MAX_ROWS or len(fields) != len(HEADER) or any(len(x) > 120 for x in fields):
                raise ValueError("invalid_or_oversized_record")
            row = dict(zip(HEADER, fields))
            stamp = row["Transaction_Time"]
            instant = timestamp_ns(stamp)
            if instant > capture_ns:
                raise ValueError("observation_after_capture")
            if row["Transaction_Date"] != stamp[:10]:
                raise ValueError("transaction_date_conflict")
            if row["Exchange_Code"] != "XCME" or row["Ticker_Symbol"] != "ES":
                raise ValueError("unexpected_source_product")
            security_id = _positive_integer(row["Security_ID"])
            kind = row["Future_Option_Index_Indicator"]
            report = row["Market_Data_Report_Type"]
            if kind not in ("FUT", "OPT") or report not in ("TRD", "VOL"):
                raise ValueError("unsupported_record_type")
            report_types[report] += 1
            instrument_kinds[kind] += 1
            if report == "VOL":
                if row["Sequence_Number"] == "":
                    unsequenced_volume_rows += 1
                else:
                    _positive_integer(row["Sequence_Number"])
                continue  # Implied-volume records cannot supply a traded price.
            seq = _positive_integer(row["Sequence_Number"])
            ticker = row["Ticker_Symbol"]
            if ticker in previous_by_ticker and seq < previous_by_ticker[ticker]:
                sequence_regressions += 1
            previous_by_ticker[ticker] = seq
            if row["Trade_Quantity"] == "":
                # The actual sample has TRD/O rows without quantity. Do not
                # fabricate a quantity or certify these as executed trades.
                unusable_trade_reasons["missing_trade_quantity"] += 1
                continue
            _decimal(row["Trade_Price_Decimal"])  # Negative futures prices are not globally invalid.
            quantity = _decimal(row["Trade_Quantity"])
            if quantity <= 0 or quantity != quantity.to_integral_value():
                raise ValueError("invalid_executed_trade_quantity")
            if not _outright(row):
                non_outright_trade_rows += 1
                continue
            key = (row["Instrument_Symbol"], security_id, row["Delivery_Date"], row["Exchange_Code"])
            if key not in groups:
                if len(groups) >= MAX_GROUPS:
                    raise ValueError("too_many_instruments")
                groups[key] = {"instrument": key[0], "security_id": security_id,
                               "delivery_month": key[2], "exchange": key[3], "trade_rows": 0,
                               "first_observed_utc": stamp, "last_observed_utc": stamp,
                               "timestamp_regressions_in_file_order": 0,
                               "_previous": instant, "_first": instant, "_last": instant}
            group = groups[key]
            group["trade_rows"] += 1
            if instant < group["_previous"]:
                group["timestamp_regressions_in_file_order"] += 1
            if instant < group["_first"]:
                group["_first"], group["first_observed_utc"] = instant, stamp
            if instant > group["_last"]:
                group["_last"], group["last_observed_utc"] = instant, stamp
            group["_previous"] = instant
    except (csv.Error, UnicodeError, StopIteration) as exc:
        raise ValueError("malformed_csv") from exc
    if rows == 0:
        raise ValueError("empty_capture")
    instruments = [{k: v for k, v in group.items() if not k.startswith("_")}
                   for _, group in sorted(groups.items())]
    return {"schema_version": SCHEMA, "layout_reference_url": LAYOUT_URL,
            "source_origin_verified_by_parser": False,
            "source_sha256": sha256(raw).hexdigest(), "source_bytes": len(raw),
            "captured_at_utc": captured_at_utc, "complete_http_body": complete_http_body,
            "coverage_scope": "one-published-part-file-not-certified-session",
            "rows": rows, "report_types": dict(sorted(report_types.items())),
            "instrument_kinds": dict(sorted(instrument_kinds.items())),
            "non_outright_trade_rows": non_outright_trade_rows,
            "unusable_trade_rows": sum(unusable_trade_reasons.values()),
            "unusable_trade_reasons": dict(sorted(unusable_trade_reasons.items())),
            "unsequenced_volume_rows": unsequenced_volume_rows,
            "trade_report_sequence_regressions_in_file_order": sequence_regressions,
            "sequence_regression_scope": "file-order-within-ticker-across-contracts-not-proof-of-feed-error",
            "outright_instruments": instruments,
            "session_calendar_verified": False, "adjacent_session_coverage_verified": False,
            "executed_trade_coverage_certified": False,
            "original_historical_arrival_utc": None, "redistribution_permission_verified": False,
            "actual_trade_prices_published": False, "eligible_opening_gap_case_count": 0,
            "decision": "WAIT", "entry": None, "stop_loss": None, "take_profit": None,
            "win_probability": None, "orders_enabled": False}


def check_receipt(payload: dict, root=None) -> None:
    """Validate metadata invariants, not the unbundled source's truth or license."""
    assert set(payload) == {"schema_version", "use", "capture", "audit", "limitations"}
    assert payload["schema_version"] == "hoshi-v3-session-source-receipt-1"
    assert payload["use"] == "historical-sample-metadata-not-opening-gap-cases-or-runtime-inputs"
    capture, audit = payload["capture"], payload["audit"]
    assert set(capture) == {"url", "http", "bytes", "sha256", "complete_http_body",
                            "captured_at_utc", "content_type", "content_length_header",
                            "rights_for_repository_redistribution_verified"}
    assert capture["url"] == SAMPLE_URL and capture["http"] == 200
    assert capture["content_type"] == "text/csv"
    assert capture["rights_for_repository_redistribution_verified"] is False
    assert capture["complete_http_body"] is True
    assert re.fullmatch(r"[a-f0-9]{64}", capture["sha256"])
    assert type(capture["bytes"]) is int and 0 < capture["bytes"] <= MAX_BYTES
    assert capture["content_length_header"] == str(capture["bytes"])
    expected_keys = {
        "schema_version", "layout_reference_url", "source_origin_verified_by_parser",
        "source_sha256", "source_bytes", "captured_at_utc", "complete_http_body",
        "coverage_scope", "rows", "report_types", "instrument_kinds", "non_outright_trade_rows",
        "unusable_trade_rows", "unusable_trade_reasons", "unsequenced_volume_rows",
        "trade_report_sequence_regressions_in_file_order", "sequence_regression_scope",
        "outright_instruments", "session_calendar_verified", "adjacent_session_coverage_verified",
        "executed_trade_coverage_certified", "original_historical_arrival_utc",
        "redistribution_permission_verified", "actual_trade_prices_published",
        "eligible_opening_gap_case_count", "decision", "entry", "stop_loss", "take_profit",
        "win_probability", "orders_enabled",
    }
    assert set(audit) == expected_keys
    assert audit["schema_version"] == SCHEMA and audit["layout_reference_url"] == LAYOUT_URL
    for field, source in (("source_sha256", "sha256"), ("source_bytes", "bytes"),
                          ("captured_at_utc", "captured_at_utc"),
                          ("complete_http_body", "complete_http_body")):
        assert audit[field] == capture[source]
    assert audit["coverage_scope"] == "one-published-part-file-not-certified-session"
    assert audit["sequence_regression_scope"] == "file-order-within-ticker-across-contracts-not-proof-of-feed-error"
    for key in ("source_origin_verified_by_parser", "session_calendar_verified",
                "adjacent_session_coverage_verified", "executed_trade_coverage_certified",
                "redistribution_permission_verified", "actual_trade_prices_published", "orders_enabled"):
        assert audit[key] is False, key
    for key in ("original_historical_arrival_utc", "entry", "stop_loss", "take_profit", "win_probability"):
        assert audit[key] is None, key
    assert type(audit["eligible_opening_gap_case_count"]) is int
    assert audit["eligible_opening_gap_case_count"] == 0 and audit["decision"] == "WAIT"
    for key in ("rows", "non_outright_trade_rows", "unusable_trade_rows", "unsequenced_volume_rows",
                "trade_report_sequence_regressions_in_file_order"):
        assert type(audit[key]) is int and 0 <= audit[key] <= MAX_ROWS
    assert audit["rows"] > 0
    reports, kinds = audit["report_types"], audit["instrument_kinds"]
    for counts, allowed in ((reports, {"TRD", "VOL"}), (kinds, {"FUT", "OPT"})):
        assert counts and set(counts) <= allowed
        assert all(type(value) is int and value > 0 for value in counts.values())
        assert sum(counts.values()) == audit["rows"]
    reasons = audit["unusable_trade_reasons"]
    assert set(reasons) <= {"missing_trade_quantity"}
    assert all(type(value) is int and value > 0 for value in reasons.values())
    assert sum(reasons.values()) == audit["unusable_trade_rows"]
    assert audit["unsequenced_volume_rows"] <= reports.get("VOL", 0)
    assert audit["trade_report_sequence_regressions_in_file_order"] <= reports.get("TRD", 0)
    captured = datetime.fromisoformat(capture["captured_at_utc"])
    assert captured.tzinfo is not None and captured.utcoffset().total_seconds() == 0
    capture_ns = calendar.timegm(captured.utctimetuple()) * 1_000_000_000 + captured.microsecond * 1000
    assert len(audit["outright_instruments"]) <= MAX_GROUPS
    keys, usable = set(), 0
    for instrument in audit["outright_instruments"]:
        assert set(instrument) == {"instrument", "security_id", "delivery_month", "exchange", "trade_rows",
                                    "first_observed_utc", "last_observed_utc",
                                    "timestamp_regressions_in_file_order"}
        key = (instrument["instrument"], instrument["security_id"], instrument["delivery_month"], instrument["exchange"])
        assert key not in keys and instrument["exchange"] == "XCME"
        keys.add(key)
        assert type(instrument["security_id"]) is int and instrument["security_id"] > 0
        assert _outright({"Future_Option_Index_Indicator": "FUT", "Ticker_Symbol": "ES",
                           "Instrument_Symbol": instrument["instrument"], "Delivery_Date": instrument["delivery_month"]})
        assert type(instrument["trade_rows"]) is int and 0 < instrument["trade_rows"] <= audit["rows"]
        assert (type(instrument["timestamp_regressions_in_file_order"]) is int
                and 0 <= instrument["timestamp_regressions_in_file_order"] <= instrument["trade_rows"])
        assert (timestamp_ns(instrument["first_observed_utc"])
                <= timestamp_ns(instrument["last_observed_utc"]) <= capture_ns)
        usable += instrument["trade_rows"]
    assert usable + audit["non_outright_trade_rows"] + audit["unusable_trade_rows"] == reports.get("TRD", 0)
    assert (isinstance(payload["limitations"], list) and 1 <= len(payload["limitations"]) <= 20
            and all(isinstance(x, str) and 1 <= len(x) <= 2000 for x in payload["limitations"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="Trusted local CME ES v2 sample CSV; no network requests")
    parser.add_argument("--captured-at-utc", required=True)
    parser.add_argument("--complete-http-body", action="store_true",
                        help="EOF was observed for this part-file, not a complete exchange session")
    args = parser.parse_args()
    if args.capture.stat().st_size > MAX_BYTES:
        parser.error("capture exceeds size bound")
    result = audit_csv(args.capture.read_bytes(), captured_at_utc=args.captured_at_utc,
                       complete_http_body=args.complete_http_body)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
