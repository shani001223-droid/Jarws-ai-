"""Task 27: trusted role handoff, real in-memory output and failure boundaries."""
import base64
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from cloud_backend.role_delegation import run_product_ad_roles
from cloud_backend.job_records import JobRecordStore
from cloud_backend.job_queue import ScheduledJobQueue


class RoleDelegationTests(unittest.TestCase):
    def test_real_gold_kit_and_shampoo_outputs_are_verified_in_memory(self):
        for key in ("gold_kit", "shampoo"):
            with self.subTest(product=key):
                result = run_product_ad_roles(key)
                self.assertTrue(result["ok"], result.get("error_code"))
                self.assertEqual(result["status"], "verified_in_memory")
                self.assertEqual([s["role"] for s in result["steps"]],
                                 ["planner", "designer", "coder", "tester"])
                self.assertTrue(all(s["status"] == "verified" for s in result["steps"]))
                self.assertEqual(result["artifact"]["task"], "create_product_ads")
                self.assertEqual(result["artifact"]["mime_type"], "application/zip")
                self.assertEqual(len(result["artifact_sha256"]), 64)
                self.assertGreater(result["artifact_size_bytes"], 1000)
                self.assertFalse(result["persisted"])
                self.assertFalse(result["queued_job_completed"])

    def test_invalid_scope_fails_before_any_producer_call(self):
        calls = []
        def producer(message):
            calls.append(message)
            raise AssertionError("must never run")
        for key in ("", "../private", "gold_kit;rm -rf", "render_anime", None, 2, True):
            with self.subTest(key=key):
                result = run_product_ad_roles(key, producer=producer)
                self.assertFalse(result["ok"])
                self.assertEqual(result["failed_role"], "planner")
                self.assertEqual(result["error_code"], "unsupported_product")
                self.assertIsNone(result["artifact"])
        self.assertEqual(calls, [])

    def test_role_error_does_not_leak_secrets_or_false_success(self):
        def failing_producer(_):
            raise RuntimeError("PRIVATE_TOKEN_AND_LOCAL_PATH")
        result = run_product_ad_roles("shampoo", producer=failing_producer)
        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_role"], "coder")
        self.assertEqual(result["error_code"], "role_failed")
        self.assertNotIn("PRIVATE_TOKEN", str(result))
        self.assertIsNone(result["artifact"])
        self.assertFalse(result["queued_job_completed"])

    def test_tester_refuses_fake_success(self):
        def fake_producer(_):
            return {"zip_base64": base64.b64encode(b"not a zip").decode("ascii")}
        result = run_product_ad_roles(
            "gold_kit", producer=fake_producer,
            verifier=lambda pack, request: {"passed": True})
        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_role"], "tester")
        self.assertEqual(result["error_code"], "invalid_artifact")

    def test_tester_rejects_wrong_file_set_even_with_lying_verifier(self):
        buf = BytesIO()
        with ZipFile(buf, "w") as archive:
            archive.writestr("unexpected.txt", "fake")
        result = run_product_ad_roles(
            "gold_kit",
            producer=lambda _: {"zip_base64": base64.b64encode(buf.getvalue()).decode("ascii")},
            verifier=lambda pack, request: {"passed": True})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "unexpected_artifacts")

    def test_tester_rejects_negative_verification_and_size(self):
        result = run_product_ad_roles(
            "shampoo",
            producer=lambda _: {"zip_base64": base64.b64encode(b"test").decode("ascii")},
            verifier=lambda *_: {"passed": False})
        self.assertEqual(result["error_code"], "verification_failed")
        oversized = run_product_ad_roles(
            "shampoo",
            producer=lambda _: {"zip_base64": "A" * 7_000_000})
        self.assertEqual(oversized["error_code"], "artifact_too_large")
        self.assertEqual(oversized["failed_role"], "coder")

    def test_no_worker_registration_or_job_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            store = JobRecordStore(Path(folder) / "jobs.sqlite")
            queue = ScheduledJobQueue(store)
            job_id = store.create("create_product_ads")["id"]
            queue.enqueue(job_id, now_ms=1000)
            result = run_product_ad_roles("shampoo", producer=lambda _: {
                "zip_base64": "invalid",
            })
            self.assertFalse(result["ok"])
            self.assertEqual(store.get(job_id)["status"], "queued")
            self.assertEqual(queue.status(job_id)["state"], "pending")
            self.assertIsNone(queue.run_once({}, now_ms=2000))
            self.assertEqual(store.get(job_id)["status"], "queued")


if __name__ == "__main__":
    unittest.main()
