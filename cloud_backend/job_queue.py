"""Private bounded SQLite scheduler for Hoshi's future trusted executors.

No model prompts, secrets, screenshots, arbitrary commands or user payloads are
stored. Scheduling does NOT start an executor: the operator must explicitly
register trusted, bounded Python handlers and run a worker. No worker is
installed or started by the public Hoshi web app or the default API process.
Recovery of interrupted running jobs is intentionally left to Task 29.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import re
import time
from typing import Callable, Mapping

try:
    from .job_records import JobRecordStore, JobStateError, KINDS, _ID_RE
except ImportError:
    from job_records import JobRecordStore, JobStateError, KINDS, _ID_RE


class QueueCapacityError(Exception):
    """A bounded queue cannot accept another job."""


@dataclass(frozen=True)
class WorkerOutcome:
    """Result from a trusted handler, never from untrusted API input."""
    succeeded: bool = False
    detail_code: str = "executor_failed"


def _clock(now_ms: int | None) -> int:
    if now_ms is None:
        return time.time_ns() // 1_000_000
    if type(now_ms) is not int or now_ms < 0:
        raise ValueError("Invalid scheduler clock")
    return now_ms


def _validate_id(job_id: str) -> None:
    if not isinstance(job_id, str) or not _ID_RE.fullmatch(job_id):
        raise JobStateError("Invalid job ID")


def _detail(code: str) -> bool:
    return isinstance(code, str) and len(code) <= 48 and bool(
        re.fullmatch(r"[a-z][a-z0-9_]*", code)
    )


class ScheduledJobQueue:
    """Atomic due-time scheduling and single-process-safe worker claims.

    Multiple workers on the same SQLite database use BEGIN IMMEDIATE to
    serialize claims. A crashed running handler remains running, not silently
    retried; later recovery must verify side effects before requeueing.
    """

    def __init__(self, store: JobRecordStore, max_pending: int = 16,
                 max_running: int = 1):
        if not isinstance(store, JobRecordStore):
            raise TypeError("Expected an authenticated job record store")
        if type(max_pending) is not int or not 1 <= max_pending <= 128:
            raise ValueError("Invalid queue capacity")
        if type(max_running) is not int or not 1 <= max_running <= 4:
            raise ValueError("Invalid running limit")
        self.store = store
        self.max_pending = max_pending
        self.max_running = max_running
        with store._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS hoshi_job_queue (
                job_id TEXT PRIMARY KEY,
                due_ms INTEGER NOT NULL,
                state TEXT NOT NULL CHECK (
                    state IN ('pending','running','succeeded','failed','canceled')
                ),
                attempts INTEGER NOT NULL DEFAULT 0,
                updated_ms INTEGER NOT NULL
            )""")
            conn.execute("""CREATE INDEX IF NOT EXISTS hoshi_queue_due
                            ON hoshi_job_queue (state, due_ms)""")

    @contextmanager
    def _transaction(self):
        with self.store._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise

    @staticmethod
    def _queue_row(row):
        if row is None:
            return None
        return {name: row[name] for name in
                ("job_id", "state", "due_ms", "attempts")}

    def status(self, job_id: str) -> dict | None:
        _validate_id(job_id)
        with self.store._connect() as conn:
            return self._queue_row(conn.execute(
                "SELECT job_id, state, due_ms, attempts FROM hoshi_job_queue WHERE job_id=?",
                (job_id,)
            ).fetchone())

    def enqueue(self, job_id: str, delay_seconds: int = 0,
                now_ms: int | None = None) -> dict:
        """Idempotently queue a planned record; never executes it."""
        _validate_id(job_id)
        if type(delay_seconds) is not int or not 0 <= delay_seconds <= 86_400:
            raise ValueError("Delay must be 0..86400 whole seconds")
        now = _clock(now_ms)
        with self._transaction() as conn:
            job = conn.execute(
                "SELECT status FROM hoshi_jobs WHERE id=?", (job_id,)
            ).fetchone()
            if job is None:
                raise JobStateError("Job not found")
            existing = conn.execute(
                "SELECT job_id, state, due_ms, attempts FROM hoshi_job_queue WHERE job_id=?",
                (job_id,)
            ).fetchone()
            if existing is not None:
                if job["status"] == "queued" and existing["state"] == "pending":
                    return self._queue_row(existing)
                raise JobStateError("Job has already been claimed or finalized")
            if job["status"] != "planned":
                raise JobStateError("Only planned jobs can be scheduled")
            count = conn.execute(
                "SELECT COUNT(*) FROM hoshi_job_queue WHERE state IN ('pending','running')"
            ).fetchone()[0]
            if count >= self.max_pending:
                raise QueueCapacityError("Queue is full")
            due = now + delay_seconds * 1000
            conn.execute(
                """INSERT INTO hoshi_job_queue(job_id,due_ms,state,attempts,updated_ms)
                   VALUES (?,?,'pending',0,?)""",
                (job_id, due, now)
            )
            updated = conn.execute(
                """UPDATE hoshi_jobs SET status='queued', version=version+1,
                   updated_ms=?, detail_code='' WHERE id=? AND status='planned'""",
                (now, job_id)
            )
            if updated.rowcount != 1:
                raise JobStateError("Job changed while scheduling")
            return {"job_id": job_id, "state": "pending", "due_ms": due, "attempts": 0}

    def claim_due(self, registered_kinds, now_ms: int | None = None) -> dict | None:
        """Claim one due job only when a trusted executor is registered."""
        kinds = frozenset(registered_kinds)
        if not kinds.issubset(KINDS):
            raise ValueError("Unknown worker kind")
        if not kinds:
            return None
        now = _clock(now_ms)
        with self._transaction() as conn:
            active = conn.execute(
                "SELECT COUNT(*) FROM hoshi_job_queue WHERE state='running'"
            ).fetchone()[0]
            if active >= self.max_running:
                return None
            placeholders = ",".join("?" for _ in kinds)
            row = conn.execute(
                f"""SELECT q.job_id, q.due_ms, q.attempts, j.kind
                    FROM hoshi_job_queue q JOIN hoshi_jobs j ON j.id=q.job_id
                    WHERE q.state='pending' AND j.status='queued'
                      AND q.due_ms <= ? AND j.kind IN ({placeholders})
                    ORDER BY q.due_ms, q.job_id LIMIT 1""",
                (now, *sorted(kinds))
            ).fetchone()
            if row is None:
                return None
            updated = conn.execute(
                """UPDATE hoshi_jobs SET status='running', version=version+1,
                   updated_ms=?, detail_code='' WHERE id=? AND status='queued'""",
                (now, row["job_id"])
            )
            if updated.rowcount != 1:
                raise JobStateError("Job changed during claim")
            conn.execute(
                """UPDATE hoshi_job_queue SET state='running', attempts=attempts+1,
                   updated_ms=? WHERE job_id=? AND state='pending'""",
                (now, row["job_id"])
            )
            return {"job_id": row["job_id"], "kind": row["kind"],
                    "due_ms": row["due_ms"], "attempts": row["attempts"] + 1}

    def finish(self, job_id: str, outcome: WorkerOutcome,
               now_ms: int | None = None) -> dict:
        """Terminal outcome only; success requires trusted artifact verification."""
        _validate_id(job_id)
        if not isinstance(outcome, WorkerOutcome) or not _detail(outcome.detail_code):
            raise JobStateError("Invalid worker outcome")
        if outcome.succeeded and outcome.detail_code != "artifacts_verified":
            raise JobStateError("Success requires verified artifacts")
        if not outcome.succeeded and outcome.detail_code == "artifacts_verified":
            raise JobStateError("Failure cannot claim verified artifacts")
        now = _clock(now_ms)
        state = "succeeded" if outcome.succeeded else "failed"
        with self._transaction() as conn:
            row = conn.execute(
                "SELECT state FROM hoshi_job_queue WHERE job_id=?", (job_id,)
            ).fetchone()
            if row is None or row["state"] != "running":
                raise JobStateError("Job is not running")
            updated = conn.execute(
                """UPDATE hoshi_jobs SET status=?, version=version+1,
                   updated_ms=?, detail_code=? WHERE id=? AND status='running'""",
                (state, now, outcome.detail_code, job_id)
            )
            if updated.rowcount != 1:
                raise JobStateError("Job changed before completion")
            conn.execute(
                "UPDATE hoshi_job_queue SET state=?, updated_ms=? WHERE job_id=?",
                (state, now, job_id)
            )
            return self._queue_row(conn.execute(
                "SELECT job_id,state,due_ms,attempts FROM hoshi_job_queue WHERE job_id=?",
                (job_id,)
            ).fetchone())

    def cancel_pending(self, job_id: str, now_ms: int | None = None) -> dict:
        """Cancel before dispatch; running/external actions cannot be undone."""
        _validate_id(job_id)
        now = _clock(now_ms)
        with self._transaction() as conn:
            row = conn.execute(
                "SELECT state FROM hoshi_job_queue WHERE job_id=?", (job_id,)
            ).fetchone()
            if row is None or row["state"] != "pending":
                raise JobStateError("Only unclaimed jobs can be canceled")
            updated = conn.execute(
                """UPDATE hoshi_jobs SET status='canceled', version=version+1,
                   updated_ms=?, detail_code='canceled_before_dispatch'
                   WHERE id=? AND status='queued'""",
                (now, job_id)
            )
            if updated.rowcount != 1:
                raise JobStateError("Job changed before cancellation")
            conn.execute(
                "UPDATE hoshi_job_queue SET state='canceled', updated_ms=? WHERE job_id=?",
                (now, job_id)
            )
            return self.status(job_id)

    def run_once(self, handlers: Mapping[str, Callable[[str], WorkerOutcome]],
                 now_ms: int | None = None) -> dict | None:
        """Run at most one explicitly registered trusted handler synchronously.

        This is an operator-controlled worker primitive, not a background
        daemon. Handlers must enforce their own timeouts and verify artifacts.
        """
        if not isinstance(handlers, Mapping) or not all(
            kind in KINDS and callable(fn) for kind, fn in handlers.items()
        ):
            raise ValueError("Only trusted allowlisted handlers are accepted")
        claim = self.claim_due(handlers.keys(), now_ms)
        if claim is None:
            return None
        try:
            outcome = handlers[claim["kind"]](claim["job_id"])
            if not isinstance(outcome, WorkerOutcome):
                outcome = WorkerOutcome(detail_code="invalid_executor_result")
        except Exception:
            # No exception text or private handler payload is persisted.
            outcome = WorkerOutcome(detail_code="executor_failed")
        self.finish(claim["job_id"], outcome, now_ms)
        return {"job_id": claim["job_id"], "state":
                "succeeded" if outcome.succeeded else "failed"}
