"""Synthetic clocks/prices prove arithmetic rules, not actual historical cases."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import v3_session_endpoint_evidence as evidence

IDENTITY = {"exchange": "SYNTH", "instrument": "TESTH5", "security_id": 1,
            "delivery_month": "202503"}
AS_OF = "2025-03-12T22:02:00.000000000Z"


def plan(**changes):
    return {"identity": copy.deepcopy(IDENTITY),
            "pre_start": "2025-03-12T20:00:00.000000000Z",
            "close": "2025-03-12T21:00:00.000000000Z",
            "reopen": "2025-03-12T22:00:00.000000000Z",
            "post_end": "2025-03-12T22:01:00.000000000Z",
            "calendar_available_at": "2025-03-01T00:00:00.000000000Z",
            "coverage_available_at": "2025-03-12T22:01:00.000000000Z",
            "calendar_applicable": True, "adjacent_windows_complete": True,
            "corrections_complete": True, "research_use_permitted": True, **changes}


def event(trade_id="pre", **changes):
    return {"trade_id": trade_id, "identity": copy.deepcopy(IDENTITY),
            "event_time": "2025-03-12T20:59:59.999999999Z",
            "available_at": "2025-03-12T21:00:00.000000000Z",
            "arrival_order": 1, "event_order": 1, "revision": 0,
            "action": "TRADE", "price": "100.25", "quantity": 1, **changes}


def after(**changes):
    defaults = {"event_time": "2025-03-12T22:00:00.000000000Z",
                "available_at": "2025-03-12T22:00:00.000000001Z", "price": "102.50"}
    return event("post", **{**defaults, **changes})


def run(events=None, **changes):
    return evidence.study_endpoints([event(), after()] if events is None else events,
                                    plan(**changes), as_of=AS_OF)


class SessionEndpointEvidenceTests(unittest.TestCase):
    def test_exact_arithmetic_never_becomes_trade_or_certification(self):
        result = run()
        self.assertEqual(result["study_status"], "uncertified_research_geometry")
        self.assertEqual(result["geometry"]["signed_gap"], "2.25")
        self.assertEqual(result["geometry"]["midpoint"], "101.375")
        self.assertEqual(result["geometry"]["width"], "2.25")
        self.assertEqual(result["decision"], "WAIT")
        self.assertFalse(result["certified_historical_case"])
        self.assertFalse(result["orders_enabled"])
        for field in ("entry", "stop_loss", "take_profit", "win_probability"):
            self.assertIsNone(result[field])

    def test_negative_and_zero_gap_are_distinct_from_missing(self):
        falling = run([event(), after(price="99.25")])
        self.assertEqual(falling["geometry"]["signed_gap"], "-1.00")
        equal = run([event(), after(price="100.25")])
        self.assertEqual(equal["geometry"]["signed_gap"], "0.00")
        missing = run([event()])
        self.assertIsNone(missing["geometry"])
        self.assertIn("missing_post_reopen_trade", missing["reasons"])
        negative = run([event(price="-10"), after(price="-9")])
        self.assertEqual(negative["geometry"]["midpoint"], "-9.5")

    def test_event_time_selects_endpoint_not_file_or_arrival_order(self):
        older = event("older", event_time="2025-03-12T20:59:59.999999998Z",
                      available_at="2025-03-12T21:00:01.000000000Z", price="90")
        later = event("later", event_time="2025-03-12T22:00:00.000000001Z",
                      available_at="2025-03-12T22:00:00.000000002Z", price="110")
        result = run([later, older, after(), event()])
        self.assertEqual(result["geometry"]["pre_trade_id"], "pre")
        self.assertEqual(result["geometry"]["post_trade_id"], "post")
        self.assertEqual(result["geometry"]["signed_gap"], "2.25")

    def test_exact_contract_cannot_roll_into_another_delivery_or_spread(self):
        for changes in ({"instrument": "ALSOH5"}, {"security_id": 2},
                        {"instrument": "TESTM5", "delivery_month": "202506"},
                        {"exchange": "OTHER"}):
            other = {**IDENTITY, **changes}
            result = run([event(), after(identity=other)])
            self.assertIsNone(result["geometry"])
            self.assertIn("missing_post_reopen_trade", result["reasons"])

    def test_spread_continuous_and_conflicting_delivery_identity_not_accepted(self):
        for changes in ({"instrument": "TESTH5-TESTM5"}, {"instrument": "TEST1"},
                        {"instrument": "TESTH2025C100"}, {"delivery_month": "202506"},
                        {"delivery_month": "202403"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                run([event(), after(identity={**IDENTITY, **changes})])

    def test_all_unverified_requirements_fail_without_exposing_geometry(self):
        for flag in ("calendar_applicable", "adjacent_windows_complete", "corrections_complete",
                     "research_use_permitted"):
            with self.subTest(flag=flag):
                result = run(**{flag: False})
                self.assertIsNone(result["geometry"])
                self.assertIn("unverified_" + flag, result["reasons"])

    def test_missing_or_later_calendar_coverage_and_original_arrival(self):
        for field in ("calendar_available_at", "coverage_available_at"):
            for value in (None, "2026-10-28T00:00:00.000000000Z"):
                with self.subTest(field=field, value=value):
                    self.assertIsNone(run(**{field: value})["geometry"])
        result = run([event(), after(available_at=None)])
        self.assertIn("missing_original_arrival", result["reasons"])
        self.assertIsNone(result["geometry"])

    def test_capture_dated_a_year_later_is_not_original_historical_receipt(self):
        result = run([event(available_at="2026-10-28T00:00:00.000000000Z"),
                      after(available_at="2026-10-28T00:00:01.000000000Z")])
        self.assertIsNone(result["geometry"])
        self.assertIn("missing_pre_break_trade", result["reasons"])

    def test_late_correction_only_changes_decisions_after_its_arrival(self):
        correction = event(revision=1, price="99.25",
                           available_at="2025-03-12T22:03:00.000000000Z")
        original = run()
        self.assertEqual(run([after(), correction, event()]), original)
        revised = evidence.study_endpoints([after(), correction, event()], plan(),
                                          as_of="2025-03-12T22:04:00.000000000Z")
        self.assertEqual(revised["geometry"]["signed_gap"], "3.25")
        self.assertEqual(original["geometry"]["signed_gap"], "2.25")

    def test_appending_future_observations_does_not_change_past_diagnostic(self):
        future = event("future", event_time="2025-03-13T20:59:59.999999999Z",
                       available_at=None, price="95")
        self.assertEqual(run([event(), future, after()]), run())
        future["available_at"] = "2025-03-13T21:00:00.000000000Z"
        self.assertEqual(run([future, after(), event()]), run())

    def test_cancellation_reselects_previous_actual_print_not_cancel_price(self):
        earlier = event("earlier", event_time="2025-03-12T20:59:58.000000000Z",
                        available_at="2025-03-12T20:59:58.000000001Z", price="99.75")
        cancel = event(revision=1, action="CANCEL", price=None, quantity=None,
                       available_at="2025-03-12T22:00:30.000000000Z")
        result = run([cancel, event(), after(), earlier])
        self.assertEqual(result["geometry"]["pre_trade_id"], "earlier")
        self.assertEqual(result["geometry"]["signed_gap"], "2.75")
        self.assertIsNone(run([event(), after(), cancel])["geometry"])

    def test_revision_gaps_unknown_originals_and_mutated_identity_fail_closed(self):
        for changed in (event(revision=2),
                        event(revision=1, event_time="2025-03-12T20:59:58.000000000Z"),
                        event(revision=1, event_order=2)):
            changed["available_at"] = "2025-03-12T22:00:30.000000000Z"
            with self.subTest(changed=changed):
                self.assertIsNone(run([event(), after(), changed])["geometry"])
        self.assertIn("missing_original_revision", run([event(revision=1), after()])["reasons"])

    def test_half_open_bounds_and_asserted_closure_conflicts(self):
        for stamp in ("2025-03-12T21:00:00.000000000Z", "2025-03-12T21:59:59.999999999Z"):
            item = event("conflict", event_time=stamp, available_at="2025-03-12T22:00:30.000000000Z")
            self.assertIn("trade_during_asserted_closure", run([event(), after(), item])["reasons"])
        outside = after(event_time="2025-03-12T22:01:00.000000000Z",
                        available_at="2025-03-12T22:01:00.000000000Z")
        self.assertIsNone(run([event(), outside])["geometry"])

    def test_unfinished_or_impossible_coverage_not_known_in_advance(self):
        self.assertIn("post_window_not_finished",
                      run(post_end="2025-03-12T22:03:00.000000000Z")["reasons"])
        self.assertIn("coverage_asserted_before_window_end",
                      run(coverage_available_at="2025-03-12T22:00:30.000000000Z")["reasons"])

    def test_equal_clocks_need_true_exchange_order_not_lexical_ids(self):
        ambiguous = event("other", arrival_order=2, price="97")
        self.assertIn("ambiguous_exchange_order", run([event(), after(), ambiguous])["reasons"])
        ordered = {**ambiguous, "event_order": 2}
        self.assertEqual(run([event(), after(), ordered])["geometry"]["pre_trade_id"], "other")
        with self.assertRaisesRegex(ValueError, "ambiguous_arrival_order"):
            run([event(), after(), {**ambiguous, "arrival_order": 1}])

    def test_bad_values_precision_unknown_fields_and_resource_limits(self):
        for changes in ({"price": "NaN"}, {"price": "1e999"}, {"price": "0e999"},
                        {"price": "0.0000000000001"}, {"price": 100.25},
                        {"quantity": True}, {"quantity": 0}, {"revision": -1},
                        {"available_at": "2025-03-12T20:00:00.000000000Z"},
                        {"event_time": "2025-03-12T20:59:59Z"}, {"confidence": 92}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                run([event(**changes), after()])
        with self.assertRaises(ValueError):
            run(calendar_applicable=1)
        with self.assertRaises(ValueError):
            run(close="2025-03-12T22:00:00.000000000Z")
        with patch.object(evidence, "MAX_EVENTS", 1), self.assertRaises(ValueError):
            run()

    def test_actual_retained_source_still_yields_zero_cases_no_price_access(self):
        path = Path(__file__).resolve().parents[1] / "knowledge_base/05_ICT_COMPLETE/session_source_audit_20261028.json"
        receipt = json.loads(path.read_text())
        result = evidence.unresolved_source_requirements(receipt)
        self.assertEqual(result["eligible_opening_gap_case_count"], 0)
        self.assertEqual(len(result["reasons"]), 5)
        self.assertEqual(result["source_sha256"], receipt["capture"]["sha256"])
        self.assertIsNone(result["geometry"])
        self.assertFalse(result["certified_historical_case"])
        manifest = json.loads((path.parents[1] / "manifest.json").read_text())
        chapter = next(item for item in manifest["documents"]
                       if item["path"].endswith("session_opening_gaps_ndog_nwog_and_2024_context.md"))
        self.assertEqual(chapter["source_review"]["partial_deliverable"]["actual_metadata_preflight"], result)
        tampered = copy.deepcopy(receipt)
        tampered["audit"]["session_calendar_verified"] = True
        with self.assertRaises(AssertionError):
            evidence.unresolved_source_requirements(tampered)


if __name__ == "__main__":
    unittest.main()
