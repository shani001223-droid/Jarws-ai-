"""SQLite-backed, metadata-only Hoshi job records.

Task 25 foundation: no worker, user prompt, API key, file contents or media is
stored here. The caller supplies an explicitly configured durable filesystem
path and handles authentication before accessing this store. Render's default
ephemeral disk does NOT survive a rebuild/redeploy.
"""
from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
import time
from pathlib import Path

KINDS = frozenset({"create_product_ads", "build_game", "render_anime", "chart_analysis"})
STATUSES = frozenset({"planned", "queued", "running", "succeeded", "failed", "canceled"})
TRANSITIONS = {
    "planned": frozenset({"queued", "canceled"}),
    "queued": frozenset({"running", "canceled"}),
    "running": frozenset({"succeeded", "failed", "canceled"}),
    "succeeded": frozenset(),
    "failed": frozenset(),
    "canceled": frozenset(),
}
_ID_RE = re.compile(r"^hjob_[A-Za-z0-9_-]{24}$")
_KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")


class JobCapacityError(Exception):
    """A configured free-tier storage cap has been reached."""


class JobStateError(Exception):
    """The requested state change is invalid or stale."""


class JobRecordStore:
    """Small, concurrent-safe job metadata store; never runs a job.

    Idempotency is scoped to a single store and task kind. The original key
    is never stored; SHA-256 is used solely to deduplicate retries.
    """

    def __init__(self, path: str | Path, max_records: int = 1000):
        self.path = Path(path)
        if not self.path.is_absolute() or not self.path.parent.is_dir():
            raise ValueError("Job database needs an existing absolute directory")
        if not 1 <= max_records <= 100_000:
            raise ValueError("Invalid job record capacity")
        self.max_records = max_records
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""CREATE TABLE IF NOT EXISTS hoshi_jobs (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                request_fingerprint TEXT UNIQUE,
                created_ms INTEGER NOT NULL,
                updated_ms INTEGER NOT NULL,
                version INTEGER NOT NULL DEFAULT 0,
                detail_code TEXT NOT NULL DEFAULT ''
            )""")

    def _connect(self):
        conn = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    @staticmethod
    def _row(row):
        if row is None:
            return None
        return {key: row[key] for key in (
            "id", "kind", "status", "created_ms", "updated_ms",
            "version", "detail_code"
        )}

    def create(self, kind: str, request_key: str | None = None) -> dict:
        if kind not in KINDS:
            raise ValueError("Unsupported job kind")
        if request_key is not None and not _KEY_RE.fullmatch(request_key):
            raise ValueError("Invalid idempotency key")
        fingerprint = (
            hashlib.sha256((kind + "\0" + request_key).encode("utf-8")).hexdigest()
            if request_key is not None else None
        )
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if fingerprint:
                    existing = conn.execute(
                        "SELECT * FROM hoshi_jobs WHERE request_fingerprint=?",
                        (fingerprint,)
                    ).fetchone()
                    if existing is not None:
                        conn.execute("COMMIT")
                        return self._row(existing)
                count = conn.execute("SELECT COUNT(*) FROM hoshi_jobs").fetchone()[0]
                if count >= self.max_records:
                    raise JobCapacityError("Job metadata capacity reached")
                now = time.time_ns() // 1_000_000
                job_id = "hjob_" + secrets.token_urlsafe(18)
                conn.execute(
                    """INSERT INTO hoshi_jobs
                       (id, kind, status, request_fingerprint, created_ms, updated_ms)
                       VALUES (?, ?, 'planned', ?, ?, ?)""",
                    (job_id, kind, fingerprint, now, now)
                )
                row = conn.execute("SELECT * FROM hoshi_jobs WHERE id=?", (job_id,)).fetchone()
                conn.execute("COMMIT")
                return self._row(row)
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def get(self, job_id: str) -> dict | None:
        if not isinstance(job_id, str) or not _ID_RE.fullmatch(job_id):
            return None
        with self._connect() as conn:
            return self._row(conn.execute(
                "SELECT * FROM hoshi_jobs WHERE id=?", (job_id,)
            ).fetchone())

    def transition(self, job_id: str, expected: str, target: str,
                   detail_code: str = "") -> dict:
        """Atomic state transition. Success requires an evidence code.

        This is for future authenticated workers only; no public transition
        endpoint is exposed. Version increments prevent stale writes.
        """
        if not isinstance(job_id, str) or not _ID_RE.fullmatch(job_id):
            raise JobStateError("Invalid job ID")
        if expected not in STATUSES or target not in TRANSITIONS[expected]:
            raise JobStateError("Invalid job transition")
        if not isinstance(detail_code, str) or len(detail_code) > 48 or (
            detail_code and not re.fullmatch(r"[a-z][a-z0-9_]*", detail_code)
        ):
            raise JobStateError("Invalid safe detail code")
        if target == "succeeded" and detail_code != "artifacts_verified":
            raise JobStateError("Cannot mark success without verified artifacts")
        now = time.time_ns() // 1_000_000
        with self._connect() as conn:
            cur = conn.execute(
                """UPDATE hoshi_jobs
                   SET status=?, updated_ms=?, version=version+1, detail_code=?
                   WHERE id=? AND status=?""",
                (target, now, detail_code, job_id, expected)
            )
            if cur.rowcount != 1:
                raise JobStateError("Job state changed or ID not found")
            return self._row(conn.execute(
                "SELECT * FROM hoshi_jobs WHERE id=?", (job_id,)
            ).fetchone())
