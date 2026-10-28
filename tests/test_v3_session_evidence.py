"""Synthetic decoder adversarial cases, never historical trade examples."""
import csv
import copy
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import v3_session_evidence as evidence


def row(**changes):
    item = dict(zip(evidence.HEADER, (
        "2025-03-11", "2025-03-11T22:00:00.000000001Z", "7", "ES", "ESH5", "10",
        "FUT", "202503", "", "", "TRD", "100", "100", "1", "1", "B", "", "H", "XCME",
    )))
    item.update(changes)
    return item


def payload(*items, header=None):
    stream = StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(evidence.HEADER if header is None else header)
    writer.writerows([item[key] for key in evidence.HEADER] for item in items)
    return stream.getvalue().encode()


def audit(*items, **options):
    return evidence.audit_csv(payload(*items), captured_at_utc="2026-10-28T07:56:14+00:00",
                              complete_http_body=options.get("complete", False))


def receipt():
    result = audit(row(), complete=True)
    return {"schema_version": "hoshi-v3-session-source-receipt-1",
            "use": "historical-sample-metadata-not-opening-gap-cases-or-runtime-inputs",
            "capture": {"url": evidence.SAMPLE_URL, "http": 200, "bytes": result["source_bytes"],
                        "sha256": result["source_sha256"], "complete_http_body": True,
                        "captured_at_utc": result["captured_at_utc"], "content_type": "text/csv",
                        "content_length_header": str(result["source_bytes"]),
                        "rights_for_repository_redistribution_verified": False},
            "audit": result, "limitations": ["Synthetic validator fixture; no actual network capture or historical case."]}


class SessionEvidenceTests(unittest.TestCase):
    def test_nine_digit_instants_are_not_rounded_to_microseconds(self):
        self.assertEqual(evidence.timestamp_ns("1970-01-01T00:00:00.000000001Z"), 1)
        self.assertEqual(evidence.timestamp_ns("1970-01-01T00:00:01.999999999Z"), 1999999999)
        a = row(Transaction_Time="2025-03-11T22:00:00.000000002Z")
        b = row(Sequence_Number="8")
        result = audit(a, b)
        instrument = result["outright_instruments"][0]
        self.assertEqual(instrument["first_observed_utc"], b["Transaction_Time"])
        self.assertEqual(instrument["last_observed_utc"], a["Transaction_Time"])
        self.assertEqual(instrument["timestamp_regressions_in_file_order"], 1)

    def test_spread_first_row_and_implied_volume_are_not_outright_trades(self):
        spread = row(Instrument_Symbol="ESH5-ESM5", Security_ID="20")
        volume = row(Market_Data_Report_Type="VOL", Trade_Price_Decimal="", Trade_Quantity="",
                     Sequence_Number="")
        result = audit(spread, volume, row(Sequence_Number="8"))
        self.assertEqual(result["non_outright_trade_rows"], 1)
        self.assertEqual(result["report_types"], {"TRD": 2, "VOL": 1})
        self.assertEqual(result["unsequenced_volume_rows"], 1)
        self.assertEqual(result["outright_instruments"][0]["trade_rows"], 1)

    def test_missing_quantity_open_record_is_quarantined_without_imputation(self):
        marker = row(Trade_Quantity="", Close_Open_Type="O")
        result = audit(marker, row(Sequence_Number="8"))
        self.assertEqual(result["unusable_trade_rows"], 1)
        self.assertEqual(result["unusable_trade_reasons"], {"missing_trade_quantity": 1})
        self.assertEqual(result["outright_instruments"][0]["trade_rows"], 1)
        self.assertFalse(result["executed_trade_coverage_certified"])
        self.assertEqual(audit(marker)["outright_instruments"], [])

    def test_delivery_month_and_security_identity_do_not_collapse(self):
        result = audit(row(), row(Instrument_Symbol="ESM5", Delivery_Date="202506", Security_ID="11"),
                       row(Security_ID="12"))
        self.assertEqual(len(result["outright_instruments"]), 3)
        with self.assertRaisesRegex(ValueError, "contract_delivery_identity_conflict"):
            audit(row(Delivery_Date="202506"))
        with self.assertRaisesRegex(ValueError, "contract_delivery_identity_conflict"):
            audit(row(Delivery_Date="202403"))

    def test_complete_part_is_not_complete_session_or_permission(self):
        result = audit(row(), complete=True)
        self.assertTrue(result["complete_http_body"])
        for key in ("source_origin_verified_by_parser", "session_calendar_verified",
                    "adjacent_session_coverage_verified", "redistribution_permission_verified",
                    "actual_trade_prices_published", "orders_enabled"):
            self.assertFalse(result[key], key)
        self.assertEqual(result["eligible_opening_gap_case_count"], 0)
        self.assertEqual(result["decision"], "WAIT")
        for key in ("entry", "stop_loss", "take_profit", "win_probability",
                    "original_historical_arrival_utc"):
            self.assertIsNone(result[key], key)
        self.assertNotIn("source_url", result)  # Parsing cannot prove HTTP origin.
        for instrument in result["outright_instruments"]:
            self.assertFalse(any("price" in key.lower() for key in instrument))

    def test_nonfinite_price_and_invalid_execution_quantity_rejected(self):
        for price in ("NaN", "Infinity", "-Infinity", "abc"):
            with self.subTest(price=price), self.assertRaises(ValueError):
                audit(row(Trade_Price_Decimal=price))
        for quantity in ("0", "-1", "0.5", "NaN"):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                audit(row(Trade_Quantity=quantity))
        self.assertEqual(audit(row(Trade_Price_Decimal="-1"))["outright_instruments"][0]["trade_rows"], 1)

    def test_unsupported_timezone_precision_or_calendar_rejected(self):
        for stamp in ("2025-03-11T22:00:00Z", "2025-03-11T22:00:00.000000001-05:00",
                      "2025-02-30T22:00:00.000000001Z", "2025-03-11T25:00:00.000000001Z"):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                audit(row(Transaction_Time=stamp))
        with self.assertRaisesRegex(ValueError, "transaction_date_conflict"):
            audit(row(Transaction_Date="2025-03-12"))

    def test_future_observations_and_unzoned_capture_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "observation_after_capture"):
            evidence.audit_csv(payload(row()), captured_at_utc="2025-03-11T21:59:59+00:00",
                               complete_http_body=True)
        for stamp in ("2026-10-28T07:56:14", "2026-10-28T12:56:14+05:00", None):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                evidence.audit_csv(payload(row()), captured_at_utc=stamp, complete_http_body=False)

    def test_wrong_product_record_type_or_identifier_rejected(self):
        for fields in ({"Ticker_Symbol": "NQ"}, {"Exchange_Code": "XNYM"},
                       {"Market_Data_Report_Type": "QUOTE"}, {"Security_ID": "0"},
                       {"Sequence_Number": "-2"}, {"Future_Option_Index_Indicator": "UNKNOWN"}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                audit(row(**fields))

    def test_sequence_regressions_recorded_not_silently_sorted_away(self):
        result = audit(row(Sequence_Number="8"), row(Sequence_Number="7"))
        self.assertEqual(result["trade_report_sequence_regressions_in_file_order"], 1)
        self.assertFalse(result["adjacent_session_coverage_verified"])

    def test_header_width_empty_and_completeness_fail_closed(self):
        for raw in (b"", payload(), payload(row(), header=reversed(evidence.HEADER)),
                    payload(row()).rsplit(b",", 1)[0] + b"\r\n"):
            with self.subTest(raw_size=len(raw)), self.assertRaises(ValueError):
                evidence.audit_csv(raw, captured_at_utc="2026-10-28T07:56:14+00:00",
                                   complete_http_body=False)
        with self.assertRaisesRegex(ValueError, "invalid_capture_completeness"):
            evidence.audit_csv(payload(row()), captured_at_utc="2026-10-28T07:56:14+00:00",
                               complete_http_body="true")

    def test_resource_bounds_are_enforced(self):
        with patch.object(evidence, "MAX_BYTES", 10), self.assertRaises(ValueError):
            audit(row())
        with patch.object(evidence, "MAX_ROWS", 1), self.assertRaises(ValueError):
            audit(row(), row())
        with patch.object(evidence, "MAX_GROUPS", 1), self.assertRaises(ValueError):
            audit(row(), row(Security_ID="11"))
        with self.assertRaises(ValueError):
            audit(row(Trade_Price_Formatted="x" * 121))

    def test_metadata_receipt_cannot_prove_source_authenticity(self):
        item = receipt()
        evidence.check_receipt(item)
        self.assertFalse(item["audit"]["source_origin_verified_by_parser"])
        self.assertEqual(item["audit"]["eligible_opening_gap_case_count"], 0)

    def test_metadata_rejects_invented_price_probability_permission_or_case(self):
        for changes in ({"win_probability": 0.92}, {"entry": 100}, {"orders_enabled": True},
                        {"redistribution_permission_verified": True}, {"eligible_opening_gap_case_count": 3},
                        {"session_calendar_verified": True}, {"confidence": 92}):
            item = receipt(); item["audit"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(AssertionError):
                evidence.check_receipt(item)
        item = receipt(); item["audit"]["outright_instruments"][0]["price"] = 100
        with self.assertRaises(AssertionError):
            evidence.check_receipt(item)

    def test_metadata_counts_and_hashes_must_reconcile(self):
        original = receipt()
        for field, value in (("rows", True), ("rows", 2), ("unusable_trade_rows", 1),
                             ("non_outright_trade_rows", 1), ("source_bytes", 1),
                             ("source_sha256", "0" * 64), ("unsequenced_volume_rows", 1)):
            item = copy.deepcopy(original); item["audit"][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                evidence.check_receipt(item)

    def test_metadata_rejects_reversed_clock_and_delivery_conflict(self):
        item = receipt(); instrument = item["audit"]["outright_instruments"][0]
        instrument["first_observed_utc"] = "2025-03-12T22:00:00.000000001Z"
        with self.assertRaises(AssertionError):
            evidence.check_receipt(item)
        item = receipt(); item["audit"]["outright_instruments"][0]["delivery_month"] = "202506"
        with self.assertRaises(ValueError):
            evidence.check_receipt(item)

    def test_metadata_requires_exact_capture_receipt_and_fails_on_unknown_fields(self):
        for field, value in (("url", "https://example.com/guessed.csv"), ("complete_http_body", False),
                             ("content_length_header", "unknown"),
                             ("rights_for_repository_redistribution_verified", True)):
            item = receipt(); item["capture"][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                evidence.check_receipt(item)
        item = receipt(); item["raw_market_prices"] = [100]
        with self.assertRaises(AssertionError):
            evidence.check_receipt(item)


if __name__ == "__main__":
    unittest.main()
