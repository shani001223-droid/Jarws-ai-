"""Task 29: no replay without evidence; recovery requires stopped workers."""
import concurrent.futures
import hashlib
import tempfile
import unittest
from pathlib import Path

from cloud_backend.job_records import JobRecordStore, JobStateError
from cloud_backend.job_queue import ScheduledJobQueue, WorkerOutcome, QueueCapacityError
from cloud_backend.role_delegation import run_product_ad_roles
from cloud_backend.verified_artifact_store import VerifiedArtifactStore
from cloud_backend.job_recovery import JobRecovery, JobRecoveryError


class JobRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = run_product_ad_roles("shampoo")
        assert cls.pack["ok"]

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.db = root / "private.sqlite"
        self.jobs = JobRecordStore(self.db)
        self.queue = ScheduledJobQueue(self.jobs, max_pending=3)
        self.root = root / "private-artifacts"
        self.root.mkdir(mode=0o700)
        self.artifacts = VerifiedArtifactStore(self.jobs, self.root)
        self.recovery = JobRecovery(self.queue, self.artifacts)

    def running(self, kind="create_product_ads"):
        job = self.jobs.create(kind)["id"]
        self.queue.enqueue(job, now_ms=1000)
        self.queue.claim_due({kind}, now_ms=1000)
        return job

    def test_verified_artifact_reconciles_after_restart_without_replay(self):
        job = self.running()
        saved = self.artifacts.save_verified(job, self.pack)
        restarted = JobRecovery(
            ScheduledJobQueue(JobRecordStore(self.db)),
            VerifiedArtifactStore(JobRecordStore(self.db), self.root))
        result = restarted.recover_interrupted(
            job, operator_stopped=True, now_ms=400_000)
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(result["detail_code"], "artifacts_verified")
        self.assertFalse(result["replayed"])
        self.assertEqual(self.jobs.get(job)["status"], "succeeded")
        self.assertEqual(self.queue.status(job)["state"], "succeeded")
        self.assertEqual(self.artifacts.metadata(job), saved)
        self.assertEqual(hashlib.sha256(self.artifacts.read_verified(job)).hexdigest(),
                         saved["sha256"])
        with self.assertRaises(JobRecoveryError):
            restarted.recover_interrupted(
                job, operator_stopped=True, now_ms=500_000)
        with self.assertRaises(JobStateError):
            self.queue.finish(job, WorkerOutcome(detail_code="executor_failed"))

    def test_unverified_interruption_quarantines_then_new_pending_id(self):
        job = self.running()
        result = self.recovery.recover_interrupted(
            job, operator_stopped=True, now_ms=400_000)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["detail_code"], "recovery_review_required")
        self.assertEqual(self.queue.status(job)["state"], "failed")
        new = self.recovery.retry_offline_failed(
            job, operator_stopped=True, now_ms=400_001)
        self.assertNotEqual(job, new["replacement_job_id"])
        self.assertEqual(new["state"], "queued")
        self.assertFalse(new["executed"])
        self.assertEqual(self.jobs.get(job)["status"], "failed")
        self.assertEqual(self.jobs.get(new["replacement_job_id"])["status"], "queued")
        self.assertEqual(self.queue.status(new["replacement_job_id"])["attempts"], 0)
        self.assertEqual(new, self.recovery.retry_offline_failed(
            job, operator_stopped=True, now_ms=400_002))
        with self.assertRaises(JobRecoveryError):
            self.recovery.retry_offline_failed(
                new["replacement_job_id"], operator_stopped=True)

    def test_recovery_refuses_recent_running_and_live_worker(self):
        job = self.running()
        with self.assertRaisesRegex(JobRecoveryError, "workers_must_be_stopped"):
            self.recovery.recover_interrupted(job, operator_stopped=False, now_ms=500_000)
        with self.assertRaisesRegex(JobRecoveryError, "job_not_stale"):
            self.recovery.recover_interrupted(job, operator_stopped=True, now_ms=300_999)
        self.assertEqual(self.jobs.get(job)["status"], "running")
        self.assertEqual(self.queue.status(job)["state"], "running")
        for age in (0, 299, 604801, True, "300"):
            with self.assertRaises(JobRecoveryError):
                self.recovery.recover_interrupted(
                    job, operator_stopped=True, now_ms=500_000,
                    min_age_seconds=age)
        with self.assertRaises(JobRecoveryError):
            self.recovery.recover_interrupted(
                "../unsafe", operator_stopped=True, now_ms=500_000)

    def test_corrupted_artifact_never_becomes_success_or_retries(self):
        job = self.running()
        self.artifacts.save_verified(job, self.pack)
        (self.root / job / "flora_ads.zip").write_bytes(b"corrupted")
        result = self.recovery.recover_interrupted(
            job, operator_stopped=True, now_ms=400_000)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["detail_code"], "recovery_artifact_invalid")
        with self.assertRaises(JobRecoveryError):
            self.recovery.retry_offline_failed(job, operator_stopped=True)
        self.assertEqual(self.jobs.get(job)["status"], "failed")

    def test_partial_checkpoints_cannot_be_reconciled(self):
        job = self.running()
        self.artifacts.save_verified(job, self.pack)
        with self.jobs._connect() as conn:
            conn.execute("DELETE FROM hoshi_job_checkpoints WHERE job_id=? AND stage='tester'",
                         (job,))
        result = self.recovery.recover_interrupted(
            job, operator_stopped=True, now_ms=400_000)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["detail_code"], "recovery_artifact_invalid")

    def test_non_offline_kind_never_retried_or_falsely_succeeded(self):
        job = self.running("build_game")
        result = self.recovery.recover_interrupted(
            job, operator_stopped=True, now_ms=400_000)
        self.assertEqual(result["state"], "failed")
        with self.assertRaises(JobRecoveryError):
            self.recovery.retry_offline_failed(job, operator_stopped=True)

    def test_orphan_file_blocks_retry_even_without_database_metadata(self):
        job = self.running()
        self.recovery.recover_interrupted(job, operator_stopped=True, now_ms=400_000)
        directory = self.root / job
        directory.mkdir(mode=0o700)
        (directory / "flora_ads.zip").write_bytes(b"orphan")
        with self.assertRaisesRegex(JobRecoveryError, "artifact_review_required"):
            self.recovery.retry_offline_failed(job, operator_stopped=True)
        self.assertEqual(self.jobs.get(job)["status"], "failed")

    def test_concurrent_retry_is_single_idempotent_new_job(self):
        job = self.running()
        self.recovery.recover_interrupted(job, operator_stopped=True, now_ms=400_000)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(
                lambda _: self.recovery.retry_offline_failed(
                    job, operator_stopped=True, now_ms=400_001),
                range(12)))
        self.assertEqual(len({x["replacement_job_id"] for x in results}), 1)
        with self.jobs._connect() as conn:
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM hoshi_job_recovery_retries").fetchone()[0], 1)

    def test_queue_capacity_and_database_mismatch_fail_closed(self):
        job = self.running()
        self.recovery.recover_interrupted(job, operator_stopped=True, now_ms=400_000)
        for _ in range(3):
            self.queue.enqueue(self.jobs.create("build_game")["id"], now_ms=1000)
        with self.assertRaises(QueueCapacityError):
            self.recovery.retry_offline_failed(job, operator_stopped=True)
        with tempfile.TemporaryDirectory() as other:
            other_jobs = JobRecordStore(Path(other) / "other.sqlite")
            with self.assertRaisesRegex(JobRecoveryError, "store_mismatch"):
                JobRecovery(self.queue, VerifiedArtifactStore(other_jobs, self.root))


if __name__ == "__main__":
    unittest.main()
