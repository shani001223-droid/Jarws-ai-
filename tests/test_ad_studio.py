"""Backend ad creation contract and actual PNG/ZIP contents."""
import base64
from io import BytesIO
import os
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from PIL import Image
from fastapi import HTTPException
from starlette.requests import Request

from cloud_backend.ad_studio import choose_products, draw_creative, create_ad_pack, CATALOG
from cloud_backend import main


class AdStudioTests(unittest.TestCase):
    def test_product_matching_does_not_invent_new_product_details(self):
        self.assertEqual(choose_products("mera 24K gold facial kit ka ad banao"), ["gold_kit"])
        self.assertEqual(choose_products("shampoo ads bana do"), ["shampoo"])
        self.assertEqual(choose_products("mere products ke ads banao"), ["gold_kit","shampoo"])

    def test_poster_png_is_real_and_correct_dimensions(self):
        for key in CATALOG:
            for size in [(1080,1350),(1080,1920)]:
                content=draw_creative(CATALOG[key],*size)
                self.assertTrue(content.startswith(b"\x89PNG\r\n\x1a\n"))
                with Image.open(BytesIO(content)) as image:
                    self.assertEqual(image.size,size)
                    image.verify()

    def test_zip_contains_both_flora_product_ads_captions_and_video_script(self):
        product=create_ad_pack("mere products ka ad banao")
        self.assertTrue(product["ok"])
        self.assertEqual(len(product["products"]),2)
        self.assertTrue(product["preview_base64"])
        data=base64.b64decode(product["zip_base64"],validate=True)
        with ZipFile(BytesIO(data)) as archive:
            files=archive.namelist()
            self.assertEqual(len(files),8)
            self.assertIn("gold_kit_feed_1080x1350.png",files)
            self.assertIn("shampoo_story_1080x1920.png",files)
            self.assertIn(b"3,500",archive.read("gold_kit_caption.txt"))
            self.assertIn(b"1,500",archive.read("shampoo_caption.txt"))
            self.assertIn(b"not a rendered video",archive.read("shampoo_video_storyboard.txt"))
            for filename in files:
                self.assertFalse(filename.startswith("/"))
            for filename in files:
                if filename.endswith(".png"):
                    self.assertTrue(archive.read(filename).startswith(b"\x89PNG"))
        self.assertLess(len(data),5_000_000)

    def test_no_paid_api_credentials_required_to_execute_real_tool(self):
        scope={"type":"http","method":"POST","path":"/api/agent/execute",
               "headers":[],"client":("127.0.0.6",5200),"scheme":"https","server":("localhost",443)}
        request=Request(scope)
        with patch.dict(os.environ,{"GEMINI_API_KEY":"","GROQ_API_KEY":"","OPENROUTER_API_KEY":"","OPENJARVIS_URL":""}):
            try:
                main._AD_RECENT.clear()
                output=main.agent_execute(main.AgentTaskRequest(task="create_product_ads",message="gold facial ad banao"),request)
            finally:
                main._AD_RECENT.clear()
        self.assertTrue(output["completed"])
        self.assertEqual(output["task"],"create_product_ads")
        self.assertEqual(len(output["products"]),1)

    def test_action_allowlist_rejects_untrusted_tools(self):
        scope={"type":"http","method":"POST","path":"/api/agent/execute",
               "headers":[],"client":("127.0.0.5",5200),"scheme":"https","server":("localhost",443)}
        with self.assertRaises(HTTPException) as err:
            main.agent_execute(main.AgentTaskRequest(task="shell",message="delete data"),Request(scope))
        self.assertEqual(err.exception.status_code,400)

    def test_product_claims_do_not_imply_fabricated_photos_or_cures(self):
        pack=create_ad_pack("gold facial kit ad")
        self.assertIn("not a product photo",pack["products"][0]["image_note"])
        self.assertNotIn("growth",CATALOG["shampoo"]["caption"].lower())
        self.assertNotIn("cure",CATALOG["shampoo"]["caption"].lower())


if __name__=="__main__":
    unittest.main()
