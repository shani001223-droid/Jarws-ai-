"""Task 47: safe offline post-slot previews; no real scheduling or posting."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from cloud_backend import flora_post_planning, main


class FloraPostPlanningTests(unittest.TestCase):
    NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)

    def test_draft_without_slot_never_schedules(self):
        draft = flora_post_planning.preview_flora_post("shampoo", "instagram_feed", now=self.NOW)
        self.assertIsNone(draft["proposed_slot"])
        self.assertEqual(draft["status"], "draft_review_required")
        self.assertIn("RS. 1,500", draft["copy"]["english"])
        for flag in ("publishable", "approved", "persisted", "queued", "scheduled", "published", "external_account_connected", "auto_post_enabled"):
            self.assertIs(draft[flag], False)
        self.assertIs(draft["dry_run_only"], True)
        self.assertTrue(draft["approval_gates"])
        self.assertTrue(all(gate["approved"] is False for gate in draft["approval_gates"]))

    def test_proposed_karachi_time_is_not_a_scheduled_post(self):
        proposed = "2026-10-29T17:30:00+05:00"
        draft = flora_post_planning.preview_flora_post("gold_kit", "whatsapp_status", "awareness", proposed, now=self.NOW)
        self.assertEqual(draft["proposed_slot"]["local"], proposed)
        self.assertEqual(draft["proposed_slot"]["utc"], "2026-10-29T12:30:00+00:00")
        self.assertEqual(draft["proposed_slot"]["review_by_utc"], "2026-10-29T11:30:00+00:00")
        self.assertEqual(draft["proposed_slot"]["status"], "proposal_only_not_scheduled")
        self.assertFalse(draft["scheduled"])
        self.assertFalse(draft["published"])

    def test_revision_hash_is_stable_and_binds_slot_and_copy(self):
        a = flora_post_planning.preview_flora_post("gold_kit", "facebook_feed", now=self.NOW)
        b = flora_post_planning.preview_flora_post("gold_kit", "facebook_feed", now=self.NOW)
        c = flora_post_planning.preview_flora_post("gold_kit", "facebook_feed", "inquiries", "2026-10-30T18:00:00+05:00", now=self.NOW)
        d = flora_post_planning.preview_flora_post("shampoo", "facebook_feed", now=self.NOW)
        self.assertEqual(a["revision_sha256"], b["revision_sha256"])
        self.assertNotEqual(a["revision_sha256"], c["revision_sha256"])
        self.assertNotEqual(a["revision_sha256"], d["revision_sha256"])
        self.assertEqual(len(a["revision_sha256"]), 64)
        a["approval_gates"][0]["approved"] = True
        self.assertFalse(b["approval_gates"][0]["approved"])

    def test_rejects_invalid_times_and_wrong_timezone(self):
        invalid = (
            "2026-10-29T17:30:00Z", "2026-10-29T17:30:00+00:00",
            "2026-10-29T17:30+05:00", "2026-10-29T17:30:00+05:00\n",
            "2026-02-30T12:00:00+05:00", "../../secrets",
            "2026-10-28T18:00:00+05:00", "2026-12-31T12:00:00+05:00",
            123, "", "2026-10-29T17:30:00+04:00",
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(flora_post_planning.FloraPostPlanError):
                    flora_post_planning.preview_flora_post("gold_kit", "instagram_feed", proposed_local_time=value, now=self.NOW)

    def test_rejects_invalid_campaign_and_naive_clock(self):
        for product, platform, objective in (("unknown", "instagram_feed", "inquiries"), ("gold_kit", "telegram", "inquiries"), ("gold_kit", "instagram_feed", "publish")):
            with self.assertRaises(flora_post_planning.FloraPostPlanError):
                flora_post_planning.preview_flora_post(product, platform, objective, now=self.NOW)
        with self.assertRaises(flora_post_planning.FloraPostPlanError):
            flora_post_planning.preview_flora_post("gold_kit", "instagram_feed", now=datetime(2026, 10, 28))

    def test_fails_closed_if_campaign_approval_state_changes(self):
        with patch.object(flora_post_planning, "plan_flora_campaign", return_value={"status": "approved", "publishable": True}):
            with self.assertRaises(flora_post_planning.FloraPostPlanError):
                flora_post_planning.preview_flora_post("gold_kit", "instagram_feed", now=self.NOW)

    def test_http_is_read_only_and_has_no_store_headers(self):
        client = TestClient(main.app)
        response = client.get("/api/flora/post-preview", params={"product_id": "shampoo", "platform": "instagram_story"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertFalse(response.json()["scheduled"])
        self.assertFalse(response.json()["queued"])
        self.assertEqual(client.post("/api/flora/post-preview").status_code, 405)
        for params in ({"product_id": "unknown"}, {"platform": "telegram"}, {"objective": "post_now"}, {"proposed_local_time": "now"}):
            self.assertEqual(client.get("/api/flora/post-preview", params=params).status_code, 422)

    def test_http_future_slot_remains_proposal(self):
        slot = (datetime.now(timezone.utc) + timedelta(days=1)).astimezone(timezone(timedelta(hours=5))).replace(microsecond=0).isoformat()
        response = TestClient(main.app).get("/api/flora/post-preview", params={"proposed_local_time": slot})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["proposed_slot"]["local"], slot)
        self.assertFalse(response.json()["scheduled"])


if __name__ == "__main__":
    unittest.main()
