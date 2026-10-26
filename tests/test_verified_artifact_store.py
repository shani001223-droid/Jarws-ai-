"""Task 28: immutable private artifacts, integrity, checkpoints and auth gates."""
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cloud_backend import main
from cloud_backend.job_records import JobRecordStore
from cloud_backend.job_queue import ScheduledJobQueue
from cloud_backend.role_delegation import run_product_ad_roles
from cloud_backend.verified_artifact_store import VerifiedArtifactStore, ArtifactStorageError


class FakeRequest:
    def __init__(self, token=""):
        self.headers = {"authorization": token}


class VerifiedArtifactStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Real trusted renderer and ZIP/PNG verifier, not fabricated bytes.
        cls.shampoo = run_product_ad_roles("shampoo")
        cls.gold = run_product_ad_roles("gold_kit")
        assert cls.shampoo["ok"] and cls.gold["ok"]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "private-artifacts"
        self.root.mkdir(mode=0o700)
        self.db = Path(self.temp.name) / "jobs.sqlite"
        self.jobs = JobRecordStore(self.db)
        self.queue = ScheduledJobQueue(self.jobs)
        self.artifacts = VerifiedArtifactStore(self.jobs, self.root)

    def running_job(self):
        job = self.jobs.create("create_product_ads")["id"]
        self.queue.enqueue(job, now_ms=1000)
        self.assertIsNotNone(self.queue.claim_due({"create_product_ads"}, now_ms=1000))
        return job

    def test_verified_zip_persists_reopens_and_records_bounded_checkpoints(self):
        job = self.running_job()
        first = self.artifacts.save_verified(job, self.shampoo)
        self.assertEqual(first["name"], "flora_ads.zip")
        self.assertEqual(first["sha256"], self.shampoo["artifact_sha256"])
        self.assertLessEqual(first["size_bytes"], 5_000_000)
        self.assertEqual(self.jobs.get(job)["status"], "running",
                         "Saving a ZIP must not fabricate job completion")
        self.assertEqual([r["stage"] for r in self.artifacts.checkpoints(job)],
                         ["planner", "designer", "coder", "tester", "persist"])
        self.assertEqual(self.artifacts.checkpoints(job)[-1]["evidence_code"],
                         "sha256_verified")
        self.assertEqual(self.artifacts.save_verified(job, self.shampoo), first)
        reopened = VerifiedArtifactStore(JobRecordStore(self.db), self.root)
        data = reopened.read_verified(job)
        self.assertEqual(hashlib.sha256(data).hexdigest(), first["sha256"])
        self.assertEqual((self.root / job).stat().st_mode & 0o077, 0)
        self.assertEqual((self.root / job / "flora_ads.zip").stat().st_mode & 0o077, 0)
        self.assertEqual(len(list((self.root / job).iterdir())), 1)
        self.assertNotIn("zip_base64", str(first))
        self.assertNotIn("Create Flora", str(reopened.checkpoints(job)))

    def test_planned_queued_wrong_kind_and_fake_roles_fail_closed(self):
        planned = self.jobs.create("create_product_ads")["id"]
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.save_verified(planned, self.shampoo)
        self.queue.enqueue(planned, now_ms=1000)
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.save_verified(planned, self.shampoo)
        self.assertFalse((self.root / planned).exists())
        wrong = self.jobs.create("build_game")["id"]
        self.queue.enqueue(wrong, now_ms=1000)
        self.queue.claim_due({"build_game"}, now_ms=1000)
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.save_verified(wrong, self.shampoo)
        # Running slot is occupied by the wrong kind; use separate database.
        with tempfile.TemporaryDirectory() as folder:
            jobs = JobRecordStore(Path(folder) / "other.sqlite")
            queue = ScheduledJobQueue(jobs)
            root = Path(folder) / "private"
            root.mkdir(mode=0o700)
            store = VerifiedArtifactStore(jobs, root)
            job = jobs.create("create_product_ads")["id"]
            queue.enqueue(job, now_ms=1000)
            queue.claim_due({"create_product_ads"}, now_ms=1000)
            altered = dict(self.shampoo)
            altered["artifact_sha256"] = "0" * 64
            with self.assertRaises(ArtifactStorageError):
                store.save_verified(job, altered)
            altered = dict(self.shampoo)
            altered["steps"] = [{"role": "tester", "status": "verified",
                                  "evidence_code": "zip_png_copy_verified"}]
            with self.assertRaises(ArtifactStorageError):
                store.save_verified(job, altered)
            self.assertIsNone(store.metadata(job))
            self.assertEqual(store.checkpoints(job), [])

    def test_immutable_no_overwrite_and_corruption_rejected(self):
        job = self.running_job()
        original = self.artifacts.save_verified(job, self.shampoo)
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.save_verified(job, self.gold)
        self.assertEqual(self.artifacts.metadata(job), original)
        path = self.root / job / "flora_ads.zip"
        path.write_bytes(b"tampered")
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.read_verified(job)
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.save_verified(job, self.shampoo)
        self.assertEqual(self.jobs.get(job)["status"], "running")

    def test_missing_or_symlink_artifact_cannot_be_read(self):
        job = self.running_job()
        self.artifacts.save_verified(job, self.shampoo)
        path = self.root / job / "flora_ads.zip"
        path.unlink()
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.read_verified(job)
        path.symlink_to(self.db)
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.read_verified(job)

    def test_invalid_id_and_insecure_storage_are_rejected(self):
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.metadata("../etc/passwd")
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.checkpoints("hjob_invalid")
        self.root.chmod(0o755)
        with self.assertRaises(ArtifactStorageError):
            VerifiedArtifactStore(self.jobs, self.root)
        self.root.chmod(0o700)
        link = Path(self.temp.name) / "linked"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ArtifactStorageError):
            VerifiedArtifactStore(self.jobs, link)
        with self.assertRaises(ArtifactStorageError):
            VerifiedArtifactStore(self.jobs, "relative/path")

    def test_metadata_survives_file_loss_without_false_success(self):
        job = self.running_job()
        self.artifacts.save_verified(job, self.shampoo)
        (self.root / job / "flora_ads.zip").unlink()
        self.assertIsNotNone(self.artifacts.metadata(job))
        with self.assertRaises(ArtifactStorageError):
            self.artifacts.read_verified(job)
        self.assertEqual(self.jobs.get(job)["status"], "running")

    def test_authenticated_download_metadata_no_public_write(self):
        job = self.running_job()
        self.artifacts.save_verified(job, self.shampoo)
        token = "private-test-token-" + "x" * 40
        env = {"HOSHI_JOB_API_TOKEN": token, "HOSHI_JOB_DB_PATH": str(self.db),
               "HOSHI_ARTIFACT_ROOT": str(self.root)}
        with patch.dict(os.environ, env):
            auth = FakeRequest("Bearer " + token)
            paths = {(r.path, method) for r in main.app.routes
                     for method in getattr(r, "methods", set())}
            self.assertIn(("/api/agent/jobs/{job_id}/artifacts", "GET"), paths)
            self.assertIn(("/api/agent/jobs/{job_id}/artifacts/download", "GET"), paths)
            self.assertNotIn(("/api/agent/jobs/{job_id}/artifacts", "POST"), paths)
            for invalid in (FakeRequest(), FakeRequest("Bearer wrong")):
                with self.assertRaises(main.HTTPException) as err:
                    main.get_job_artifacts(job, invalid)
                self.assertEqual(err.exception.status_code, 401)
                with self.assertRaises(main.HTTPException) as err:
                    main.download_job_artifact(job, invalid)
                self.assertEqual(err.exception.status_code, 401)
            listing = main.get_job_artifacts(job, auth)
            self.assertTrue(listing["persisted"])
            self.assertEqual(listing["artifact"]["sha256"], self.shampoo["artifact_sha256"])
            self.assertEqual(len(listing["checkpoints"]), 5)
            response = main.download_job_artifact(job, auth)
            self.assertEqual(response.media_type, "application/zip")
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(hashlib.sha256(response.body).hexdigest(),
                             self.shampoo["artifact_sha256"])
            self.assertEqual(main.get_job_artifacts(self.jobs.create("build_game")["id"], auth)["persisted"], False)
            with self.assertRaises(main.HTTPException) as missing:
                main.download_job_artifact("hjob_" + "A" * 24, auth)
            self.assertEqual(missing.exception.status_code, 404)
            with patch.dict(os.environ, {"HOSHI_ARTIFACT_ROOT": ""}):
                with self.assertRaises(main.HTTPException) as missing_config:
                    main.get_job_artifacts(job, auth)
                self.assertEqual(missing_config.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
