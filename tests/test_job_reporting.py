"""Task 30: quiet pull reports never turn a DB status into fake completion."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import Response

from cloud_backend import main
from cloud_backend.job_records import JobRecordStore
from cloud_backend.job_queue import ScheduledJobQueue, WorkerOutcome
from cloud_backend.job_reporting import build_job_report
from cloud_backend.role_delegation import run_product_ad_roles
from cloud_backend.verified_artifact_store import VerifiedArtifactStore


class FakeRequest:
    def __init__(self, authorization=""):
        self.headers = {"authorization": authorization}


class JobReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = run_product_ad_roles("shampoo")
        assert cls.pack["ok"]

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        folder = Path(temp.name)
        self.db = folder / "private.sqlite"
        self.jobs = JobRecordStore(self.db)
        self.queue = ScheduledJobQueue(self.jobs)
        self.root = folder / "artifacts"
        self.root.mkdir(mode=0o700)
        self.artifacts = VerifiedArtifactStore(self.jobs, self.root)

    def make(self, kind="create_product_ads"):
        return self.jobs.create(kind)["id"]

    def running(self):
        job_id = self.make()
        self.queue.enqueue(job_id, now_ms=1000)
        self.queue.claim_due({"create_product_ads"}, now_ms=1000)
        return job_id

    def test_planned_queued_running_are_silent_and_never_final(self):
        job_id = self.make()
        report = build_job_report(self.jobs, job_id, self.artifacts)
        self.assertEqual(report["phase"], "planned")
        self.assertEqual(report["blocker_code"], "not_scheduled")
        self.assertEqual(report["attention_scope"], "operator")
        self.assertFalse(report["report_ready"])
        self.assertTrue(report["quiet"])
        self.assertFalse(report["notifications_sent"])
        self.assertIsNone(report["final_artifact"])
        self.queue.enqueue(job_id, now_ms=1000)
        report = build_job_report(self.jobs, job_id, self.artifacts)
        self.assertEqual(report["phase"], "queued")
        self.assertEqual(report["blocker_code"], "executor_not_configured")
        self.queue.claim_due({"create_product_ads"}, now_ms=1000)
        report = build_job_report(self.jobs, job_id, self.artifacts)
        self.assertEqual(report["phase"], "unconfirmed_running")
        self.assertFalse(report["evidence"]["verified"])
        self.assertFalse(report["report_ready"])

    def test_completed_requires_real_blob_and_five_checkpoints(self):
        job_id = self.running()
        self.artifacts.save_verified(job_id, self.pack)
        interim = build_job_report(self.jobs, job_id, self.artifacts)
        self.assertEqual(interim["phase"], "unconfirmed_running")
        self.assertEqual(interim["evidence"]["checkpoint_stages"],
                         ["planner", "designer", "coder", "tester", "persist"])
        self.assertFalse(interim["report_ready"])
        self.queue.finish(job_id, WorkerOutcome(
            succeeded=True, detail_code="artifacts_verified"), now_ms=1001)
        final = build_job_report(self.jobs, job_id, self.artifacts)
        self.assertEqual(final["phase"], "completed")
        self.assertTrue(final["report_ready"])
        self.assertTrue(final["evidence"]["verified"])
        self.assertEqual(final["final_artifact"]["sha256"],
                         self.pack["artifact_sha256"])
        self.assertEqual(final["final_artifact"]["name"], "flora_ads.zip")
        self.assertTrue(final["final_artifact"]["download_path"].startswith("/api/agent/jobs/"))
        self.assertNotIn(str(self.root), str(final))
        self.assertNotIn("Bearer", str(final))
        # Missing private volume cannot be treated as a completed delivery.
        without_store = build_job_report(self.jobs, job_id)
        self.assertEqual(without_store["phase"], "review_required")
        self.assertFalse(without_store["report_ready"])
        # Rehashed file, not metadata, is the source of completion proof.
        (self.root / job_id / "flora_ads.zip").write_bytes(b"tampered")
        damaged = build_job_report(self.jobs, job_id, self.artifacts)
        self.assertEqual(damaged["blocker_code"], "artifact_verification_required")
        self.assertFalse(damaged["evidence"]["verified"])
        self.assertIsNone(damaged["final_artifact"])

    def test_missing_or_corrupt_checkpoint_blocks_final(self):
        job_id = self.running()
        self.artifacts.save_verified(job_id, self.pack)
        self.queue.finish(job_id, WorkerOutcome(
            succeeded=True, detail_code="artifacts_verified"), now_ms=1001)
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE hoshi_job_checkpoints SET evidence_code=? "
                         "WHERE job_id=? AND stage='tester'",
                         ("fake_proof", job_id))
        report = build_job_report(self.jobs, job_id, self.artifacts)
        self.assertEqual(report["phase"], "review_required")
        self.assertFalse(report["report_ready"])
        self.assertNotIn("tester", report["evidence"]["checkpoint_stages"])

    def test_failed_canceled_and_unrecognized_codes_are_sanitized(self):
        failed = self.running()
        self.queue.finish(failed, WorkerOutcome(detail_code="private_secret_code"),
                          now_ms=1001)
        report = build_job_report(self.jobs, failed, self.artifacts)
        self.assertEqual(report["phase"], "blocked")
        self.assertEqual(report["blocker_code"], "job_failed_review")
        self.assertTrue(report["report_ready"])
        self.assertNotIn("private_secret_code", str(report))
        canceled = self.make()
        self.queue.enqueue(canceled, now_ms=1000)
        self.queue.cancel_pending(canceled, now_ms=1001)
        stopped = build_job_report(self.jobs, canceled, self.artifacts)
        self.assertEqual(stopped["phase"], "stopped")
        self.assertTrue(stopped["report_ready"])
        self.assertIsNone(stopped["final_artifact"])
        self.assertIsNone(build_job_report(self.jobs, "hjob_invalid", self.artifacts))

    def test_fake_success_flag_and_queue_disagreement_are_not_proof(self):
        fake = self.running()
        self.queue.finish(fake, WorkerOutcome(
            succeeded=True, detail_code="artifacts_verified"), now_ms=1001)
        self.assertEqual(build_job_report(self.jobs, fake, self.artifacts)["phase"],
                         "review_required")
        job_id = self.make()
        self.jobs.transition(job_id, "planned", "queued")
        mismatch = build_job_report(self.jobs, job_id, self.artifacts)
        self.assertEqual(mismatch["blocker_code"], "queue_reconciliation_required")

    def test_authenticated_api_no_store_no_notifications_and_no_public_write(self):
        token = "test-only-" + "x" * 40
        env = {"HOSHI_JOB_API_TOKEN": token, "HOSHI_JOB_DB_PATH": str(self.db),
               "HOSHI_ARTIFACT_ROOT": str(self.root)}
        job_id = self.make()
        with patch.dict(os.environ, env):
            paths = {(r.path, method) for r in main.app.routes
                     for method in getattr(r, "methods", set())}
            self.assertIn(("/api/agent/jobs/{job_id}/report", "GET"), paths)
            self.assertNotIn(("/api/agent/jobs/{job_id}/report", "POST"), paths)
            for bad in (FakeRequest(), FakeRequest("Bearer wrong")):
                with self.assertRaises(main.HTTPException) as denied:
                    main.get_private_job_report(job_id, bad, Response())
                self.assertEqual(denied.exception.status_code, 401)
            response = Response()
            result = main.get_private_job_report(
                job_id, FakeRequest("Bearer " + token), response)
            self.assertEqual(result["phase"], "planned")
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            with self.assertRaises(main.HTTPException) as missing:
                main.get_private_job_report("hjob_" + "Z" * 24,
                                            FakeRequest("Bearer " + token), Response())
            self.assertEqual(missing.exception.status_code, 404)
            with patch.dict(os.environ, {"HOSHI_ARTIFACT_ROOT": ""}):
                result = main.get_private_job_report(
                    job_id, FakeRequest("Bearer " + token), Response())
                self.assertEqual(result["phase"], "planned")
        with patch.dict(os.environ, {"HOSHI_JOB_API_TOKEN": "",
                                     "HOSHI_JOB_DB_PATH": ""}):
            with self.assertRaises(main.HTTPException) as unavailable:
                main.get_private_job_report(job_id, FakeRequest(), Response())
            self.assertEqual(unavailable.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
