"""Prove that a backend ad task is accepted only with validated real files.

The automatic retry is bounded to a side-effect-free, local generator.
"""
import base64
from io import BytesIO
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

from fastapi import HTTPException
from starlette.requests import Request

from cloud_backend.ad_studio import create_ad_pack
from cloud_backend.artifact_verifier import verify_ad_pack, ArtifactVerificationError
from cloud_backend import main


def test_request(ip="127.0.0.77"):
    return Request({
        "type": "http", "method": "POST", "path": "/api/agent/execute",
        "headers": [], "client": (ip, 7777), "scheme": "https",
        "server": ("localhost", 443),
    })


class AgentSelfRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.message = "Flora shampoo ad banao"
        cls.valid = create_ad_pack(cls.message)

    def setUp(self):
        main._AD_RECENT.clear()
        self.addCleanup(main._AD_RECENT.clear)

    def test_actual_ad_pack_has_a_verified_manifest(self):
        checks = verify_ad_pack(self.valid, self.message)
        self.assertTrue(checks["passed"])
        self.assertIn("png_dimensions", checks["checks"])
        self.assertIn("preview", checks["checks"])

    def test_false_completed_flag_is_not_enough(self):
        altered = {**self.valid, "completed": False}
        with self.assertRaises(ArtifactVerificationError):
            verify_ad_pack(altered, self.message)

    def test_corrupt_base64_is_rejected(self):
        altered = {**self.valid, "zip_base64": "NOT-A-ZIP!"}
        with self.assertRaises(ArtifactVerificationError):
            verify_ad_pack(altered, self.message)

    def test_zip_missing_story_image_is_rejected(self):
        old = base64.b64decode(self.valid["zip_base64"])
        new = BytesIO()
        with ZipFile(BytesIO(old)) as src, ZipFile(new, "w", compression=ZIP_DEFLATED) as dst:
            for name in src.namelist():
                if name.endswith("story_1080x1920.png"):
                    continue
                dst.writestr(name, src.read(name))
        altered = {**self.valid, "zip_base64": base64.b64encode(new.getvalue()).decode("ascii")}
        with self.assertRaisesRegex(ArtifactVerificationError, "ZIP contents"):
            verify_ad_pack(altered, self.message)

    def test_catalog_metadata_tampering_is_rejected(self):
        altered = {**self.valid, "products": [{**self.valid["products"][0], "price": "RS. 999"}]}
        with self.assertRaisesRegex(ArtifactVerificationError, "trusted catalog"):
            verify_ad_pack(altered, self.message)

    def test_one_corrupt_result_is_regenerated_once(self):
        bad = {**self.valid, "zip_base64": "corrupt"}
        with patch.object(main, "create_ad_pack", side_effect=[bad, dict(self.valid)]) as rendered:
            result = main.agent_execute(
                main.AgentTaskRequest(task="create_product_ads", message=self.message),
                test_request(),
            )
        self.assertEqual(rendered.call_count, 2)
        self.assertTrue(result["completed"])
        self.assertEqual(result["verification"]["attempts"], 2)
        self.assertTrue(result["verification"]["passed"])

    def test_two_corrupt_results_fail_closed_without_infinite_retries(self):
        bad = {**self.valid, "zip_base64": "corrupt", "private": "sk-secret"}
        with patch.object(main, "create_ad_pack", return_value=bad) as rendered:
            with self.assertRaises(HTTPException) as error:
                main.agent_execute(
                    main.AgentTaskRequest(task="create_product_ads", message=self.message),
                    test_request("127.0.0.88"),
                )
        self.assertEqual(rendered.call_count, 2)
        self.assertEqual(error.exception.status_code, 502)
        self.assertNotIn("sk-secret", str(error.exception.detail))

    def test_good_result_does_not_waste_a_second_render(self):
        with patch.object(main, "create_ad_pack", return_value=dict(self.valid)) as rendered:
            result = main.agent_execute(
                main.AgentTaskRequest(task="create_product_ads", message=self.message),
                test_request("127.0.0.89"),
            )
        rendered.assert_called_once()
        self.assertEqual(result["verification"]["attempts"], 1)


if __name__ == "__main__":
    unittest.main()
