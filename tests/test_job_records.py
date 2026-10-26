"""Task 25: real SQLite reopen/concurrency and privacy contracts."""
import concurrent.futures
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cloud_backend.job_records import JobCapacityError, JobRecordStore, JobStateError


class JobRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "hoshi_jobs.sqlite"
        self.store = JobRecordStore(self.path, max_records=3)

    def test_persists_across_new_connections_without_prompt_or_secret(self):
        job = self.store.create("build_game", "client-request-01")
        self.assertRegex(job["id"], r"^hjob_[A-Za-z0-9_-]{24}$")
        self.assertEqual(job["status"], "planned")
        self.assertEqual(job["version"], 0)
        self.assertNotIn("client-request-01", str(job))
        self.assertEqual(JobRecordStore(self.path).get(job["id"]), job)
        with sqlite3.connect(self.path) as conn:
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM hoshi_jobs"
            ).fetchone()[0], 1)
            self.assertNotIn("client-request-01", str(conn.execute(
                "SELECT * FROM hoshi_jobs"
            ).fetchone()))

    def test_idempotent_retries_do_not_create_extra_records(self):
        first = self.store.create("render_anime", "same-request")
        second = JobRecordStore(self.path).create("render_anime", "same-request")
        other_kind = self.store.create("build_game", "same-request")
        self.assertEqual(first, second)
        self.assertNotEqual(first["id"], other_kind["id"])

    def test_atomic_idempotency_under_parallel_requests(self):
        def submit(_):
            return JobRecordStore(self.path).create("chart_analysis", "parallel")["id"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            ids = list(pool.map(submit, range(12)))
        self.assertEqual(len(set(ids)), 1)

    def test_bounded_capacity_does_not_delete_user_records(self):
        self.store.create("build_game")
        self.store.create("render_anime")
        self.store.create("chart_analysis")
        with self.assertRaises(JobCapacityError):
            self.store.create("create_product_ads")
        self.assertEqual(len(self._all()), 3)

    def _all(self):
        with sqlite3.connect(self.path) as conn:
            return conn.execute("SELECT id FROM hoshi_jobs").fetchall()

    def test_transition_is_atomic_and_success_requires_evidence(self):
        job = self.store.create("create_product_ads")
        with self.assertRaises(JobStateError):
            self.store.transition(job["id"], "planned", "succeeded")
        queued = self.store.transition(job["id"], "planned", "queued")
        self.assertEqual(queued["version"], 1)
        with self.assertRaises(JobStateError):
            self.store.transition(job["id"], "planned", "canceled")
        running = self.store.transition(job["id"], "queued", "running")
        self.assertEqual(running["status"], "running")
        with self.assertRaises(JobStateError):
            self.store.transition(job["id"], "running", "succeeded")
        done = self.store.transition(job["id"], "running", "succeeded", "artifacts_verified")
        self.assertEqual(done["status"], "succeeded")
        self.assertEqual(done["version"], 3)
        with self.assertRaises(JobStateError):
            self.store.transition(job["id"], "succeeded", "queued")

    def test_rejects_bad_identifiers_and_untrusted_detail(self):
        with self.assertRaises(ValueError):
            self.store.create("execute_shell")
        for key in ("", "has spaces", "private@email", "x" * 81):
            with self.assertRaises(ValueError):
                self.store.create("build_game", key)
        self.assertIsNone(self.store.get("../db"))
        self.assertIsNone(self.store.get("hjob_bad"))
        job = self.store.create("build_game")
        with self.assertRaises(JobStateError):
            self.store.transition(job["id"], "planned", "queued", "Bearer secret")
        self.assertEqual(self.store.get(job["id"])["status"], "planned")

    def test_requires_explicit_existing_absolute_storage_location(self):
        with self.assertRaises(ValueError):
            JobRecordStore("relative.db")
        with self.assertRaises(ValueError):
            JobRecordStore(Path(self.temp.name) / "missing" / "db.sqlite")


if __name__ == "__main__":
    unittest.main()
