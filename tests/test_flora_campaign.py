"""Task 44: review-only Flora campaign plans and HTTP safety gates."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from cloud_backend import flora_campaign, main
from cloud_backend.ad_studio import CATALOG


class FloraCampaignTests(unittest.TestCase):
    def test_each_platform_has_specific_canvas_and_safe_copy(self):
        expected = {
            "instagram_feed": "1080x1350",
            "instagram_story": "1080x1920",
            "facebook_feed": "1080x1350",
            "whatsapp_status": "1080x1920",
        }
        for platform, size in expected.items():
            with self.subTest(platform=platform):
                plan = flora_campaign.plan_flora_campaign("shampoo", platform)
                self.assertEqual(plan["creative_brief"]["canvas_px"], size)
                self.assertEqual(plan["platform"], platform)
                self.assertEqual(plan["status"], "draft_review_required")
                self.assertIn("500 ml", plan["copy"]["english"])
                self.assertIn("RS. 1,500", plan["copy"]["roman_urdu"])
                self.assertIn("reconfirm before posting", plan["copy"]["english"])
                self.assertFalse(plan["publishable"])
                self.assertFalse(plan["scheduled"])
                self.assertFalse(plan["published"])
                self.assertFalse(plan["auto_post_enabled"])
                self.assertFalse(plan["orders_enabled"])
                self.assertFalse(plan["photo_rights_verified"])
                self.assertFalse(plan["price_verified"])
                self.assertEqual(plan["creative_brief"]["asset_status"], "illustrated_template_only")
                self.assertEqual(len(plan["review_steps"]), 4)

    def test_two_objectives_are_distinct_and_no_unproven_claims(self):
        inquiry = flora_campaign.plan_flora_campaign("gold_kit", "instagram_feed", "inquiries")
        awareness = flora_campaign.plan_flora_campaign("gold_kit", "instagram_feed", "awareness")
        self.assertNotEqual(inquiry["copy"]["english"], awareness["copy"]["english"])
        self.assertIn("6-piece facial kit", awareness["copy"]["english"])
        for plan in (inquiry, awareness):
            text = str(plan["copy"]).lower()
            for claim in ("cure", "guaranteed", "hair growth", "clinically proven", "discount", "free shipping"):
                self.assertNotIn(claim, text)

    def test_rejects_unknown_ids_platforms_and_objectives(self):
        for product, platform, objective in (
            ("../private", "instagram_feed", "inquiries"),
            ("gold_kit", "telegram", "inquiries"),
            ("shampoo", "instagram_feed", "post_now"),
            (None, "instagram_feed", "inquiries"),
        ):
            with self.subTest(product=product, platform=platform, objective=objective):
                with self.assertRaises(flora_campaign.FloraCampaignError):
                    flora_campaign.plan_flora_campaign(product, platform, objective)

    def test_fails_closed_on_price_drift(self):
        with patch.dict(CATALOG["gold_kit"], {"price": "RS. 99"}):
            with self.assertRaises(flora_campaign.FloraCampaignError):
                flora_campaign.plan_flora_campaign("gold_kit", "instagram_story")

    def test_no_mutable_shared_hashtag_state(self):
        first = flora_campaign.plan_flora_campaign("gold_kit", "instagram_feed")
        first["copy"]["hashtags"].clear()
        self.assertTrue(flora_campaign.plan_flora_campaign("gold_kit", "instagram_feed")["copy"]["hashtags"])

    def test_read_only_api_headers_and_rejection(self):
        client = TestClient(main.app)
        ok = client.get("/api/flora/campaign-draft", params={
            "product_id": "shampoo", "platform": "whatsapp_status", "objective": "awareness",
        })
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.headers["cache-control"], "no-store")
        self.assertEqual(ok.headers["x-content-type-options"], "nosniff")
        self.assertEqual(ok.json()["creative_brief"]["canvas_px"], "1080x1920")
        self.assertFalse(ok.json()["publishable"])
        self.assertNotIn("zip_base64", ok.text)
        for params in ({"product_id": "bad"}, {"platform": "tiktok"}, {"objective": "publish"}):
            bad = client.get("/api/flora/campaign-draft", params=params)
            self.assertEqual(bad.status_code, 422)
        self.assertEqual(client.post("/api/flora/campaign-draft").status_code, 405)


if __name__ == "__main__":
    unittest.main()
