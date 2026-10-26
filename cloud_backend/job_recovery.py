"""Operator-only, fail-closed recovery of Hoshi SQLite jobs (Task 29).

Recovery NEVER starts workers, replays unknown side effects, or trusts a stale
timestamp as proof a worker is dead. A trusted operator must first stop all
workers using this database and explicitly acknowledge that fact. No HTTP
route, background thread, or browser token is provided.
"""
from __future__ import annotations

import secrets
import time
from pathlib import Path

try:
    from .job_records import JobRecordStore, JobStateError, JobCapacityError, _ID_RE
    from .job_queue import ScheduledJobQueue, QueueCapacityError, _clock
    from .verified_artifact_store import VerifiedArtifactStore, ArtifactStorageError
except ImportError:
    from job_records import JobRecordStore, JobStateError, JobCapacityError, _ID_RE
    from job_queue import ScheduledJobQueue, QueueCapacityError, _clock
    from verified_artifact_store import VerifiedArtifactStore, ArtifactStorageError


class JobRecoveryError(ValueError):
    """Sanitized failure code without paths, prompts or secrets."""


_REQUIRED_CHECKPOINTS = (
    ("planner", "trusted_scope"),
    ("designer", "catalog_theme"),
    ("coder", "local_renderer"),
    ("tester", "zip_png_copy_verified"),
    ("persist", "sha256_verified"),
)


class JobRecovery:
    """Explicit trusted recovery, with SQLite transactions and no auto-replay.

    Only an immutable rehashed Flora artifact with complete role checkpoints
    can be reconciled to success. Otherwise an interrupted running job is
    quarantined as failed, never automatically requeued. A trusted operator
    can create ONE fresh job for the strictly offline Flora kind when there
    is no stored artifact, checkpoint or orphan directory. That replacement
    remains pending until a separately configured trusted handler runs it.
    """

    def __init__(self, queue: ScheduledJobQueue, artifacts: VerifiedArtifactStore):
        if not isinstance(queue, ScheduledJobQueue) or not isinstance(artifacts, VerifiedArtifactStore):
            raise TypeError("Expected a private queue and verified artifact store")
        if queue.store.path.resolve() != artifacts.jobs.path.resolve():
            raise JobRecoveryError("store_mismatch")
        self.queue = queue
        self.artifacts = artifacts
        with queue.store._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS hoshi_job_recovery_retries (
                original_job_id TEXT PRIMARY KEY,
                replacement_job_id TEXT NOT NULL UNIQUE,
                created_ms INTEGER NOT NULL
            )""")

    @staticmethod
    def _guard(job_id: str, operator_stopped: bool) -> None:
        if not isinstance(job_id, str) or not _ID_RE.fullmatch(job_id):
            raise JobRecoveryError("invalid_job_id")
        if operator_stopped is not True:
            raise JobRecoveryError("workers_must_be_stopped")

    def recover_interrupted(self, job_id: str, *, operator_stopped: bool,
                            now_ms: int | None = None,
                            min_age_seconds: int = 300) -> dict:
        """Reconcile a stale running job only after the operator stops workers.

        No blind replay: valid SHA-verified artifact -> succeeded; absent or
        corrupted evidence -> failed/review. A recent running job is untouched.
        """
        self._guard(job_id, operator_stopped)
        if type(min_age_seconds) is not int or not 300 <= min_age_seconds <= 604800:
            raise JobRecoveryError("invalid_recovery_age")
        now = _clock(now_ms)
        with self.queue._transaction() as conn:
            row = conn.execute("""SELECT j.kind, j.status, j.version,
                    j.updated_ms AS job_updated, q.state, q.attempts,
                    q.updated_ms AS queue_updated
                FROM hoshi_jobs j JOIN hoshi_job_queue q ON q.job_id=j.id
                WHERE j.id=?""", (job_id,)).fetchone()
            if row is None or row["status"] != "running" or row["state"] != "running":
                raise JobRecoveryError("job_not_running")
            if now - max(row["job_updated"], row["queue_updated"]) < min_age_seconds * 1000:
                raise JobRecoveryError("job_not_stale")
            valid = False
            has_metadata = self.artifacts.metadata(job_id) is not None
            if row["kind"] == "create_product_ads" and has_metadata:
                try:
                    data = self.artifacts.read_verified(job_id)
                    checkpoints = self.artifacts.checkpoints(job_id)
                    valid = bool(data) and [
                        (c["stage"], c["evidence_code"]) for c in checkpoints
                    ] == list(_REQUIRED_CHECKPOINTS)
                except (ArtifactStorageError, OSError, ValueError):
                    valid = False
            target = "succeeded" if valid else "failed"
            detail = ("artifacts_verified" if valid else
                      "recovery_artifact_invalid" if has_metadata else
                      "recovery_review_required")
            updated = conn.execute("""UPDATE hoshi_jobs
                SET status=?, detail_code=?, updated_ms=?, version=version+1
                WHERE id=? AND status='running' AND version=?""",
                (target, detail, now, job_id, row["version"]))
            if updated.rowcount != 1:
                raise JobRecoveryError("stale_recovery")
            changed = conn.execute("""UPDATE hoshi_job_queue
                SET state=?, updated_ms=? WHERE job_id=? AND state='running'
                AND attempts=?""",
                (target, now, job_id, row["attempts"]))
            if changed.rowcount != 1:
                raise JobRecoveryError("stale_recovery")
            return {"job_id": job_id, "state": target, "detail_code": detail,
                    "attempts": row["attempts"], "replayed": False}

    def retry_offline_failed(self, job_id: str, *, operator_stopped: bool,
                             now_ms: int | None = None) -> dict:
        """Create one new pending job, never reuse a failed worker's job ID.

        Restricts retry to offline create_product_ads with zero evidence and
        a stopped prior worker. Old handlers cannot finish the new job ID.
        Does not invent a product selection or register/start a worker.
        """
        self._guard(job_id, operator_stopped)
        now = _clock(now_ms)
        with self.queue._transaction() as conn:
            row = conn.execute("""SELECT j.kind, j.status, j.detail_code,
                    q.state, q.attempts
                FROM hoshi_jobs j JOIN hoshi_job_queue q ON q.job_id=j.id
                WHERE j.id=?""", (job_id,)).fetchone()
            if row is None or row["kind"] != "create_product_ads" or (
                row["status"] != "failed" or row["state"] != "failed"
                or row["attempts"] != 1
                or row["detail_code"] not in (
                    "recovery_review_required", "executor_failed",
                    "invalid_executor_result"
                )
            ):
                raise JobRecoveryError("unsafe_retry")
            prior = conn.execute("""SELECT replacement_job_id
                FROM hoshi_job_recovery_retries WHERE original_job_id=?""",
                (job_id,)).fetchone()
            if prior is not None:
                existing = conn.execute("""SELECT status FROM hoshi_jobs
                    WHERE id=?""", (prior["replacement_job_id"],)).fetchone()
                if existing is None:
                    raise JobRecoveryError("retry_record_inconsistent")
                return {"original_job_id": job_id,
                        "replacement_job_id": prior["replacement_job_id"],
                        "state": existing["status"], "executed": False}
            if conn.execute("""SELECT 1 FROM hoshi_job_recovery_retries
                WHERE replacement_job_id=?""", (job_id,)).fetchone():
                raise JobRecoveryError("retry_limit_reached")
            # Even an unindexed orphan ZIP/temp file blocks replay: the
            # original handler may have performed an unrecorded write.
            directory = self.artifacts.root / job_id
            if directory.exists() or directory.is_symlink():
                raise JobRecoveryError("artifact_review_required")
            if self.artifacts.metadata(job_id) is not None or self.artifacts.checkpoints(job_id):
                raise JobRecoveryError("artifact_review_required")
            active = conn.execute("""SELECT COUNT(*) FROM hoshi_job_queue
                WHERE state IN ('pending','running')""").fetchone()[0]
            if active >= self.queue.max_pending:
                raise QueueCapacityError("Queue is full")
            count = conn.execute("SELECT COUNT(*) FROM hoshi_jobs").fetchone()[0]
            if count >= self.queue.store.max_records:
                raise JobCapacityError("Job metadata capacity reached")
            new_id = "hjob_" + secrets.token_urlsafe(18)
            conn.execute("""INSERT INTO hoshi_jobs
                (id,kind,status,request_fingerprint,created_ms,updated_ms,version,detail_code)
                VALUES (?,'create_product_ads','queued',NULL,?,?,1,'')""",
                (new_id, now, now))
            conn.execute("""INSERT INTO hoshi_job_queue
                (job_id,due_ms,state,attempts,updated_ms)
                VALUES (?,?,'pending',0,?)""", (new_id, now, now))
            conn.execute("""INSERT INTO hoshi_job_recovery_retries
                (original_job_id,replacement_job_id,created_ms)
                VALUES (?,?,?)""", (job_id, new_id, now))
            return {"original_job_id": job_id, "replacement_job_id": new_id,
                    "state": "queued", "executed": False}
