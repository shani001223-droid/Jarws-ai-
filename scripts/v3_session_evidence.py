"""Offline futures sample audits; not a feed, calendar or gap strategy.

Primary layout checked 2026-10-28:
https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457223239/Time%2Band%2BSales

A public ES part-file includes spreads as well as outright contracts. Preserve
exact instrument identity and nanoseconds; never call a part-file's endpoints
the exchange session's last/first trades. No prices are exported. Sample access
does not establish redistribution permission or original historical arrival.
The separate vendor-screening validator checks metadata counters and flags;
it does not decode/replay an unbundled vendor tape or certify its provenance.
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


def vendor_flag_status(action: str, flags: int) -> dict:
    """MBP-1 action/bit distinctions, not a clock or permission certificate.

    Primary definitions checked 2026-10-28:
    https://databento.com/docs/conventions/common-fields-enums-types
    A book Cancel is NOT a correction/cancellation of an executed trade.
    """
    if action not in ("A", "C", "M", "R", "T") or type(flags) is not int or not 0 <= flags <= 255:
        raise ValueError("invalid_mbp1_action_or_flags")
    return {"trade_record": action == "T", "snapshot": bool(flags & 32),
            "bad_receive_timestamp": bool(flags & 8), "possible_book_gap": bool(flags & 4),
            "proves_original_hoshi_arrival": False}


def check_vendor_screening(payload: dict, root=None) -> None:
    """Mechanical checks only; the raw 350 MB public sample is not bundled."""
    assert set(payload) == {"schema_version", "use", "capture", "observations", "profiling_method",
                            "source_quality", "decision", "entry", "stop_loss", "take_profit",
                            "win_probability", "orders_enabled", "checked_primary_sources", "limitations"}
    assert payload["schema_version"] == "hoshi-v3-vendor-sample-screening-1"
    assert payload["use"] == "metadata-only-source-screening-not-priced-gap-cases-or-runtime"
    capture, obs, quality = payload["capture"], payload["observations"], payload["source_quality"]
    assert set(capture) == {"url", "started_at_utc", "http", "content_type", "content_length",
                            "content_disposition", "bytes", "sha256", "complete_http_body",
                            "captured_at_utc", "raw_prices_published", "permissions_verified"}
    assert capture["url"] == "https://hist.databento.com/v0/dataset/sample/download/glbx.mdp3/mbp-1?sample_type=futures"
    assert type(capture["http"]) is int and capture["http"] == 200
    assert capture["content_type"] == "text/csv" and capture["complete_http_body"] is True
    assert capture["content_disposition"] == 'attachment; filename="databento_glbx.mdp3_mbp_1.csv"'
    assert type(capture["bytes"]) is int and 0 < capture["bytes"] <= 512_000_000
    assert capture["content_length"] is None or capture["content_length"] == str(capture["bytes"])
    assert re.fullmatch(r"[a-f0-9]{64}", capture["sha256"])
    assert capture["raw_prices_published"] is False and capture["permissions_verified"] is False
    instants = []
    for key in ("started_at_utc", "captured_at_utc"):
        # Capture clocks are explicitly microsecond UTC metadata, not trade clocks.
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00", capture[key])
        stamp = datetime.fromisoformat(capture[key])
        instants.append(calendar.timegm(stamp.utctimetuple()) * 1_000_000_000 + stamp.microsecond * 1000)
    assert instants[0] <= instants[1]
    assert set(obs) == {"header", "rows", "action_counts", "flag_counts", "source_symbol",
                        "provider_publisher_id", "provider_instrument_id", "trade_record_rows",
                        "trade_record_date_counts", "event_window_utc", "vendor_receive_window_utc",
                        "trade_record_event_window_utc", "trade_record_event_regressions",
                        "trade_record_receive_regressions", "flagged_trade_rows", "first_record"}
    assert obs["header"] == ["ts_recv", "ts_event", "rtype", "publisher_id", "instrument_id",
                              "action", "side", "depth", "price", "size", "flags", "ts_in_delta",
                              "sequence", "bid_px_00", "ask_px_00", "bid_sz_00", "ask_sz_00",
                              "bid_ct_00", "ask_ct_00", "symbol"]
    assert type(obs["rows"]) is int and 0 < obs["rows"] <= 5_000_000
    assert re.fullmatch(r"ES[FGHJKMNQUVXZ]\d{1,2}", obs["source_symbol"])
    for key in ("provider_publisher_id", "provider_instrument_id"):
        assert type(obs[key]) is int and obs[key] > 0
    for counts in (obs["action_counts"], obs["flag_counts"]):
        assert counts and all(type(v) is int and 0 < v <= obs["rows"] for v in counts.values())
        assert sum(counts.values()) == obs["rows"]
    assert set(obs["action_counts"]) <= {"A", "C", "M", "R", "T"}
    assert all(re.fullmatch(r"0|[1-9]\d{0,2}", k) and int(k) <= 255 for k in obs["flag_counts"])
    assert type(obs["trade_record_rows"]) is int
    assert 0 < obs["trade_record_rows"] == obs["action_counts"].get("T", 0)
    days = obs["trade_record_date_counts"]
    assert days and sum(days.values()) == obs["trade_record_rows"]
    assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", k) and type(v) is int and v > 0
               for k, v in days.items())
    for day in days:
        datetime.fromisoformat(day)  # Reject a plausible-looking impossible civil date.
    bounds = {}
    for key in ("event_window_utc", "vendor_receive_window_utc", "trade_record_event_window_utc"):
        assert isinstance(obs[key], list) and len(obs[key]) == 2
        bounds[key] = tuple(timestamp_ns(x) for x in obs[key])
        assert bounds[key][0] <= bounds[key][1] <= instants[1]
    assert (bounds["event_window_utc"][0] <= bounds["trade_record_event_window_utc"][0]
            <= bounds["trade_record_event_window_utc"][1] <= bounds["event_window_utc"][1])
    assert min(days) == obs["trade_record_event_window_utc"][0][:10]
    assert max(days) == obs["trade_record_event_window_utc"][1][:10]
    for key in ("trade_record_event_regressions", "trade_record_receive_regressions"):
        assert type(obs[key]) is int and 0 <= obs[key] < obs["trade_record_rows"]
    assert set(obs["flagged_trade_rows"]) == {"bad_receive_timestamp", "snapshot", "maybe_bad_book"}
    for label, mask in (("bad_receive_timestamp", 8), ("snapshot", 32), ("maybe_bad_book", 4)):
        count = obs["flagged_trade_rows"][label]
        assert type(count) is int and 0 <= count <= obs["trade_record_rows"]
        assert count <= sum(v for k, v in obs["flag_counts"].items() if int(k) & mask)
    first = obs["first_record"]
    assert set(first) == {"action", "flags", "event_utc", "vendor_receive_utc"}
    vendor_flag_status(first["action"], first["flags"])
    assert obs["action_counts"].get(first["action"], 0) > 0
    assert obs["flag_counts"].get(str(first["flags"]), 0) > 0
    for label, mask in (("bad_receive_timestamp", 8), ("snapshot", 32), ("maybe_bad_book", 4)):
        if first["flags"] & mask:
            if first["action"] == "T":
                assert obs["flagged_trade_rows"][label] >= 1
            else:
                assert obs["flagged_trade_rows"][label] < sum(
                    v for k, v in obs["flag_counts"].items() if int(k) & mask)
    for key, window in (("event_utc", "event_window_utc"), ("vendor_receive_utc", "vendor_receive_window_utc")):
        assert bounds[window][0] <= timestamp_ns(first[key]) <= bounds[window][1]
    assert set(quality) == {"metadata_validator_proves_origin", "contract_definition_mapping_verified",
                            "historical_calendar_verified", "adjacent_session_coverage_verified",
                            "correction_coverage_verified", "vendor_capture_equals_hoshi_arrival",
                            "original_hoshi_arrival_utc", "redistribution_permission_verified",
                            "price_gap_computed", "actual_trade_prices_published", "eligible_opening_gap_case_count"}
    for key, value in quality.items():
        if key == "original_hoshi_arrival_utc":
            assert value is None
        elif key == "eligible_opening_gap_case_count":
            assert type(value) is int and value == 0
        else:
            assert value is False, key
    assert payload["decision"] == "WAIT" and payload["orders_enabled"] is False
    assert all(payload[key] is None for key in ("entry", "stop_loss", "take_profit", "win_probability"))
    for key in ("limitations", "checked_primary_sources"):
        assert (isinstance(payload[key], list) and 1 <= len(payload[key]) <= 20
                and all(isinstance(x, str) and 1 <= len(x) <= 2500 for x in payload[key]))
    assert all(x.startswith("https://") for x in payload["checked_primary_sources"])
    assert isinstance(payload["profiling_method"], str) and 1 <= len(payload["profiling_method"]) <= 1000


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
