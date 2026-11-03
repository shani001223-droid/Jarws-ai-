"""Task 48: no invented sales, no PII, and strict offline report boundaries."""
import copy
import unittest
from unittest.mock import patch

from cloud_backend import flora_reporting
from cloud_backend.ad_studio import CATALOG


class FloraReportingTests(unittest.TestCase):
    def sale(self, **changes):
        row = {
            "record_id": "sale_001", "date": "2026-10-27",
            "product_id": "shampoo", "units": 2,
            "received_pkr": 2900, "refunded_pkr": 100,
            "source": "owner_manual_export",
        }
        row.update(changes)
        return row

    def campaign(self, **changes):
        row = {
            "record_id": "ad_001", "date": "2026-10-27",
            "platform": "instagram_feed",
            "campaign_revision_sha256": "a" * 64,
            "impressions": 1000, "clicks": 80, "inquiries": 5,
            "source": "platform_export", "spend_pkr": 400,
        }
        row.update(changes)
        return row

    def report(self, sales=None, campaigns=None):
        return flora_reporting.build_flora_evidence_report(
            "2026-10-01", "2026-10-31",
            [] if sales is None else sales, [] if campaigns is None else campaigns,
        )

    def test_missing_records_are_unknown_not_zero(self):
        report = self.report()
        self.assertEqual(report["status"], "no_source_records")
        self.assertIsNone(report["sales"])
        self.assertIsNone(report["campaigns"])
        self.assertFalse(report["independently_reconciled"])
        self.assertFalse(report["publishable"])
        self.assertFalse(report["external_accounts_accessed"])

    def test_grounded_aggregation_no_list_price_multiplication(self):
        rows = [self.sale(), self.sale(
            record_id="sale_002", product_id="gold_kit", units=1,
            received_pkr=3200, refunded_pkr=0, source="private_shop_export",
        )]
        report = self.report(rows, [self.campaign()])
        self.assertEqual(report["sales"]["received_pkr"], 6100)
        self.assertEqual(report["sales"]["refunded_pkr"], 100)
        self.assertEqual(report["sales"]["net_pkr"], 6000)
        self.assertEqual(report["sales"]["units"], 3)
        self.assertEqual(report["sales"]["by_product"]["shampoo"]["net_pkr"], 2800)
        self.assertEqual(report["campaigns"]["impressions"], 1000)
        self.assertEqual(report["campaigns"]["spend_pkr"], 400)
        for field in ("conversion_rate", "return_on_ad_spend", "profit_pkr"):
            self.assertIsNone(report[field])
        self.assertFalse(report["attribution_verified"])
        self.assertNotIn("sale_001", str(report))
        self.assertNotIn("ad_001", str(report))

    def test_partial_spend_is_unknown_not_zero(self):
        report = self.report([], [self.campaign(spend_pkr=None)])
        self.assertIsNone(report["sales"])
        self.assertIsNone(report["campaigns"]["spend_pkr"])
        self.assertFalse(report["campaigns"]["spend_coverage_complete"])

    def test_input_order_does_not_change_digest_and_no_mutation(self):
        sales = [self.sale(), self.sale(record_id="sale_002")]
        before = copy.deepcopy(sales)
        a = self.report(sales, [self.campaign()])
        b = self.report(list(reversed(sales)), [self.campaign()])
        self.assertEqual(a["source_revision_sha256"], b["source_revision_sha256"])
        self.assertEqual(sales, before)
        self.assertEqual(len(a["source_revision_sha256"]), 64)

    def test_date_window_validation(self):
        for start, end in (("2026-02-30", "2026-03-01"),
                           ("2026-10-31", "2026-10-01"),
                           ("2026-01-01", "2026-12-31"),
                           ("2026-10-01\n", "2026-10-31")):
            with self.subTest(start=start, end=end):
                with self.assertRaises(flora_reporting.FloraReportingError):
                    flora_reporting.build_flora_evidence_report(start, end, [], [])
        with self.assertRaises(flora_reporting.FloraReportingError):
            self.report([self.sale(date="2026-09-30")])

    def test_rejects_personal_data_and_unknown_sources(self):
        for row in (
            self.sale(customer_phone="03001234567"),
            self.sale(source="unknown"),
            self.sale(source=[]),
            self.sale(product_id=[]),
            self.sale(product_id="../secrets"),
            self.sale(record_id="../../x"),
            self.sale(campaign_revision_sha256="bad"),
            self.sale(units=True),
            self.sale(received_pkr=10, refunded_pkr=11),
            self.sale(refunded_pkr=-1),
            self.sale(received_pkr=10_000_001),
        ):
            with self.subTest(row=row):
                with self.assertRaises(flora_reporting.FloraReportingError):
                    self.report([row])

    def test_rejects_campaign_errors_and_pii(self):
        for row in (
            self.campaign(account_token="secret"),
            self.campaign(platform="telegram"),
            self.campaign(campaign_revision_sha256="A" * 64),
            self.campaign(clicks=1001),
            self.campaign(impressions=True),
            self.campaign(spend_pkr=-1),
            self.campaign(source="unknown"),
            self.campaign(source=[]),
            self.campaign(platform=[]),
        ):
            with self.subTest(row=row):
                with self.assertRaises(flora_reporting.FloraReportingError):
                    self.report([], [row])

    def test_duplicate_ids_and_excessive_rows(self):
        with self.assertRaises(flora_reporting.FloraReportingError):
            self.report([self.sale(), self.sale()])
        with self.assertRaises(flora_reporting.FloraReportingError):
            self.report([], [self.campaign(), self.campaign()])
        with self.assertRaises(flora_reporting.FloraReportingError):
            self.report([self.sale()] * 251)
        with self.assertRaises(flora_reporting.FloraReportingError):
            flora_reporting.build_flora_evidence_report(
                "2026-10-01", "2026-10-31", tuple(), []
            )

    def test_catalogue_drift_fails_closed(self):
        with patch.dict(CATALOG["shampoo"], {"price": "RS. 999"}):
            with self.assertRaises(flora_reporting.FloraReportingError):
                self.report([self.sale()])

    def test_report_is_pure_offline_and_unverified_even_with_tags(self):
        tagged = self.sale(campaign_revision_sha256="a" * 64)
        report = self.report([tagged], [self.campaign()])
        self.assertEqual(report["source_status"], "operator_supplied_unverified")
        self.assertFalse(report["attribution_verified"])
        self.assertFalse(report["persisted"])
        self.assertFalse(report["orders_created"])


if __name__ == "__main__":
    unittest.main()
