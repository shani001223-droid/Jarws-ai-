"""Task 34: real scoped specialists, evidence gates and no autonomous side effects."""
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from cloud_backend.job_queue import ScheduledJobQueue
from cloud_backend.job_records import JobRecordStore
from cloud_backend.role_delegation import run_product_ad_roles
from cloud_backend.specialist_orchestrator import orchestrate_flora_campaign


class ScopedSpecialistTests(unittest.TestCase):
    def test_real_two_product_campaign_has_verified_nested_deliverables(self):
        result = orchestrate_flora_campaign(("gold_kit", "shampoo"))
        self.assertTrue(result["ok"], result.get("error_code"))
        self.assertEqual(result["status"], "verified_in_memory")
        self.assertFalse(result["persisted"])
        self.assertFalse(result["queued_job_completed"])
        self.assertFalse(result["published"])
        self.assertEqual(
            [s["specialist"] for s in result["specialists"]],
            ["catalog_planner", "creative_specialist", "artifact_auditor",
             "creative_specialist", "artifact_auditor", "campaign_packager"],
        )
        self.assertTrue(all(s["status"] == "verified" for s in result["specialists"]))
        artifact = result["artifact"]
        data = base64.b64decode(artifact["zip_base64"], validate=True)
        self.assertEqual(artifact["size_bytes"], len(data))
        self.assertEqual(artifact["sha256"], hashlib.sha256(data).hexdigest())
        with ZipFile(BytesIO(data)) as outer:
            self.assertEqual(set(outer.namelist()),
                             {"manifest.json", "gold_kit.zip", "shampoo.zip"})
            manifest = json.loads(outer.read("manifest.json"))
            self.assertEqual(manifest, result["manifest"])
            self.assertFalse(manifest["rendered_video"])
            for product in manifest["products"]:
                inner = outer.read(product["filename"])
                self.assertEqual(product["sha256"], hashlib.sha256(inner).hexdigest())
                self.assertEqual(product["bytes"], len(inner))
                with ZipFile(BytesIO(inner)) as zipped:
                    key = product["product_key"]
                    self.assertEqual(set(zipped.namelist()), {
                        f"{key}_feed_1080x1350.png",
                        f"{key}_story_1080x1920.png",
                        f"{key}_caption.txt",
                        f"{key}_video_storyboard.txt",
                    })

    def test_single_product_is_supported_without_claiming_mp4(self):
        result = orchestrate_flora_campaign(["shampoo"])
        self.assertTrue(result["ok"], result.get("error_code"))
        self.assertEqual([p["product_key"] for p in result["manifest"]["products"]],
                         ["shampoo"])
        self.assertFalse(result["manifest"]["rendered_video"])

    def test_scope_rejects_arbitrary_tools_and_duplicates_before_execution(self):
        calls = []
        def delegate(key):
            calls.append(key)
            raise AssertionError("should never be called")
        for keys, code in (
            ("shampoo", "invalid_campaign_scope"),
            ([], "invalid_campaign_scope"),
            (["shampoo", "shampoo"], "duplicate_product"),
            (["shampoo", "gold_kit", "shampoo"], "invalid_campaign_scope"),
            (["../private"], "unapproved_product"),
            (["render_anime"], "unapproved_product"),
            ([True], "unapproved_product"),
            ([None], "unapproved_product"),
            ([{"tool": "shell"}], "unapproved_product"),
        ):
            with self.subTest(keys=keys):
                result = orchestrate_flora_campaign(keys, delegate=delegate)
                self.assertFalse(result["ok"])
                self.assertEqual(result["error_code"], code)
                self.assertIsNone(result["artifact"])
        self.assertEqual(calls, [])

    def test_fake_success_receipts_and_artifacts_do_not_pass_audit(self):
        cases = [
            {"ok": True, "status": "verified_in_memory", "kind": "create_product_ads",
             "product_key": "shampoo", "persisted": False,
             "queued_job_completed": False, "role_order": ["planner", "designer", "coder", "tester"],
             "steps": [{"role": r, "status": "verified"} for r in
                       ("planner", "designer", "coder", "tester")],
             "artifact": {"zip_base64": base64.b64encode(b"not a zip").decode()},
             "artifact_sha256": hashlib.sha256(b"not a zip").hexdigest(),
             "artifact_size_bytes": 9},
        ]
        for fake in cases:
            result = orchestrate_flora_campaign(["shampoo"], delegate=lambda _: fake)
            self.assertFalse(result["ok"])
            self.assertEqual(result["failed_specialist"], "artifact_auditor")
            self.assertEqual(result["error_code"], "artifact_unverified")
            self.assertIsNone(result["artifact"])

    def test_digest_tamper_and_role_receipt_tamper_rejected(self):
        genuine = run_product_ad_roles("shampoo")
        self.assertTrue(genuine["ok"])
        digest_tamper = dict(genuine, artifact_sha256="0" * 64)
        result = orchestrate_flora_campaign(["shampoo"], delegate=lambda _: digest_tamper)
        self.assertEqual(result["error_code"], "artifact_digest_mismatch")
        role_tamper = dict(genuine, steps=[{"role": "planner", "status": "verified"}])
        result = orchestrate_flora_campaign(["shampoo"], delegate=lambda _: role_tamper)
        self.assertEqual(result["error_code"], "invalid_role_evidence")

    def test_stop_between_specialists_discards_partial_artifacts(self):
        seen = []
        counter = [0]
        def stop():
            counter[0] += 1
            return counter[0] == 3  # after first real delegated creative, before audit
        result = orchestrate_flora_campaign(
            ("shampoo", "gold_kit"),
            delegate=lambda key: (seen.append(key), run_product_ad_roles(key))[1],
            stop_requested=stop,
        )
        self.assertEqual(seen, ["shampoo"])
        self.assertEqual(result["status"], "canceled")
        self.assertEqual(result["error_code"], "operator_stopped")
        self.assertIsNone(result["artifact"])
        self.assertFalse(result["queued_job_completed"])

    def test_bad_stop_handler_and_exceptions_fail_closed_without_leaking(self):
        result = orchestrate_flora_campaign(
            ["shampoo"], stop_requested=lambda: (_ for _ in ()).throw(
                RuntimeError("PRIVATE_API_TOKEN")))
        self.assertEqual(result["error_code"], "stop_check_failed")
        self.assertNotIn("PRIVATE_API_TOKEN", str(result))
        result = orchestrate_flora_campaign(["shampoo"], stop_requested=lambda: "yes")
        self.assertEqual(result["error_code"], "invalid_stop_result")
        result = orchestrate_flora_campaign(
            ["shampoo"], delegate=lambda _: (_ for _ in ()).throw(
                RuntimeError("PRIVATE_API_TOKEN")))
        self.assertEqual(result["error_code"], "specialist_failed")
        self.assertNotIn("PRIVATE_API_TOKEN", str(result))
        self.assertIsNone(result["artifact"])

    def test_does_not_claim_or_complete_queued_jobs(self):
        with tempfile.TemporaryDirectory() as folder:
            store = JobRecordStore(Path(folder) / "jobs.sqlite")
            queue = ScheduledJobQueue(store)
            job = store.create("create_product_ads")
            queue.enqueue(job["id"], now_ms=1000)
            result = orchestrate_flora_campaign(["shampoo"])
            self.assertTrue(result["ok"])
            self.assertEqual(store.get(job["id"])["status"], "queued")
            self.assertEqual(queue.status(job["id"])["state"], "pending")
            self.assertFalse(result["queued_job_completed"])


if __name__ == "__main__":
    unittest.main()
