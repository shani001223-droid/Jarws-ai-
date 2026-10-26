"""Task 26: SQLite scheduler, due-time, worker isolation and concurrency."""
import concurrent.futures
import sqlite3
import tempfile
import unittest
from pathlib import Path
from threading import Event

from cloud_backend.job_records import JobRecordStore, JobStateError
from cloud_backend.job_queue import (
    QueueCapacityError, ScheduledJobQueue, WorkerOutcome
)


class ScheduledJobQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "private.sqlite"
        self.store = JobRecordStore(self.db)
        self.queue = ScheduledJobQueue(self.store, max_pending=2, max_running=1)

    def create(self, kind="build_game"):
        return self.store.create(kind)["id"]

    def test_scheduled_delay_reopen_and_registered_handler_gate(self):
        job_id = self.create()
        queued = self.queue.enqueue(job_id, delay_seconds=10, now_ms=1000)
        self.assertEqual(queued, self.queue.enqueue(job_id, delay_seconds=0, now_ms=1001))
        self.assertEqual(queued["due_ms"], 11000)
        self.assertEqual(self.store.get(job_id)["status"], "queued")
        reopened = ScheduledJobQueue(JobRecordStore(self.db))
        self.assertEqual(reopened.status(job_id), queued)
        self.assertIsNone(reopened.claim_due(set(), now_ms=20000))
        self.assertIsNone(reopened.claim_due({"build_game"}, now_ms=10999))
        claimed = reopened.claim_due({"build_game"}, now_ms=11000)
        self.assertEqual(claimed["job_id"], job_id)
        self.assertEqual(claimed["attempts"], 1)
        self.assertEqual(self.store.get(job_id)["status"], "running")
        self.assertIsNone(reopened.claim_due({"build_game"}, now_ms=11001))

    def test_full_capacity_and_validation_fail_closed(self):
        ids = [self.create() for _ in range(3)]
        for job_id in ids[:2]:
            self.queue.enqueue(job_id, now_ms=1000)
        with self.assertRaises(QueueCapacityError):
            self.queue.enqueue(ids[2], now_ms=1000)
        self.assertEqual(self.store.get(ids[2])["status"], "planned")
        for invalid in (-1, 86401, True, 0.1, "30"):
            with self.assertRaises(ValueError):
                self.queue.enqueue(ids[2], delay_seconds=invalid)
        with self.assertRaises(JobStateError):
            self.queue.enqueue("hjob_bad")
        with self.assertRaises(ValueError):
            self.queue.claim_due({"execute_shell"})
        self.assertEqual(self.store.get(ids[2])["status"], "planned")

    def test_atomic_claim_concurrency_and_max_running(self):
        ids = [self.create(), self.create()]
        for job_id in ids:
            self.queue.enqueue(job_id, now_ms=1000)
        def claim(_):
            return self.queue.claim_due({"build_game"}, now_ms=1000)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            claims = list(pool.map(claim, range(20)))
        winners = [c for c in claims if c is not None]
        self.assertEqual(len(winners), 1)
        self.assertEqual(len({c["job_id"] for c in winners}), 1)
        self.assertEqual(self.store.get(winners[0]["job_id"])["status"], "running")
        self.queue.finish(winners[0]["job_id"], WorkerOutcome(detail_code="executor_failed"), now_ms=1100)
        other = self.queue.claim_due({"build_game"}, now_ms=1101)
        self.assertIsNotNone(other)
        self.assertNotEqual(other["job_id"], winners[0]["job_id"])

    def test_worker_is_opt_in_and_never_claims_unregistered_kind(self):
        ids = [self.create("build_game"), self.create("chart_analysis")]
        for job_id in ids:
            self.queue.enqueue(job_id, now_ms=1000)
        self.assertIsNone(self.queue.run_once({}, now_ms=1000))
        self.assertEqual(self.store.get(ids[0])["status"], "queued")
        processed = self.queue.run_once(
            {"chart_analysis": lambda job_id: WorkerOutcome(detail_code="no_executor_artifacts")},
            now_ms=1000
        )
        self.assertEqual(processed["job_id"], ids[1])
        self.assertEqual(processed["state"], "failed")
        self.assertEqual(self.store.get(ids[0])["status"], "queued")
        self.assertEqual(self.store.get(ids[1])["detail_code"], "no_executor_artifacts")

    def test_exception_and_bad_handler_result_never_mark_success(self):
        first = self.create()
        self.queue.enqueue(first, now_ms=1000)
        def raise_private(_):
            raise RuntimeError("SECRET_DO_NOT_PERSIST")
        result = self.queue.run_once({"build_game": raise_private}, now_ms=1000)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(self.store.get(first)["detail_code"], "executor_failed")
        second = self.create()
        self.queue.enqueue(second, now_ms=1000)
        self.queue.run_once({"build_game": lambda _: "fake success"}, now_ms=1000)
        self.assertEqual(self.store.get(second)["detail_code"], "invalid_executor_result")
        with sqlite3.connect(self.db) as conn:
            self.assertNotIn("SECRET_DO_NOT_PERSIST", str(conn.execute(
                "SELECT * FROM hoshi_jobs").fetchall()))

    def test_success_requires_explicit_verified_artifact_code(self):
        job_id = self.create("create_product_ads")
        self.queue.enqueue(job_id, now_ms=1000)
        self.queue.claim_due({"create_product_ads"}, now_ms=1000)
        with self.assertRaises(JobStateError):
            self.queue.finish(job_id, WorkerOutcome(succeeded=True, detail_code="done"), now_ms=1001)
        self.assertEqual(self.store.get(job_id)["status"], "running")
        self.queue.finish(job_id, WorkerOutcome(succeeded=True, detail_code="artifacts_verified"), now_ms=1001)
        self.assertEqual(self.store.get(job_id)["status"], "succeeded")
        with self.assertRaises(JobStateError):
            self.queue.finish(job_id, WorkerOutcome(), now_ms=1002)

    def test_pending_cancel_and_running_cancel_refused(self):
        first, second = self.create(), self.create()
        self.queue.enqueue(first, now_ms=1000)
        self.queue.enqueue(second, now_ms=1000)
        canceled = self.queue.cancel_pending(first, now_ms=1001)
        self.assertEqual(canceled["state"], "canceled")
        self.assertEqual(self.store.get(first)["status"], "canceled")
        self.queue.claim_due({"build_game"}, now_ms=1002)
        with self.assertRaises(JobStateError):
            self.queue.cancel_pending(second, now_ms=1003)
        self.assertEqual(self.store.get(second)["status"], "running")

    def test_explicit_worker_poll_respects_stop_and_tick_limits(self):
        job_id = self.create("chart_analysis")
        self.queue.enqueue(job_id, now_ms=0)
        stopped = Event()
        def trusted_handler(_):
            stopped.set()
            return WorkerOutcome(detail_code="preflight_only")
        processed = self.queue.poll(
            {"chart_analysis": trusted_handler}, stopped,
            interval_seconds=0.1, max_ticks=3
        )
        self.assertEqual(processed, 1)
        self.assertEqual(self.store.get(job_id)["status"], "failed")
        self.assertEqual(self.queue.poll({}, stopped, max_ticks=1), 0)
        with self.assertRaises(ValueError):
            self.queue.poll({}, Event(), interval_seconds=0)
        with self.assertRaises(ValueError):
            self.queue.poll({}, Event(), max_ticks=0)

    def test_invalid_success_and_no_handler_do_not_mutate_queue(self):
        job_id = self.create()
        self.queue.enqueue(job_id, now_ms=1000)
        with self.assertRaises(ValueError):
            self.queue.run_once({"execute_shell": lambda _: WorkerOutcome()}, now_ms=1000)
        self.assertEqual(self.store.get(job_id)["status"], "queued")
        with self.assertRaises(ValueError):
            self.queue.run_once({"build_game": "not callable"}, now_ms=1000)
        self.assertEqual(self.store.get(job_id)["status"], "queued")


if __name__ == "__main__":
    unittest.main()
