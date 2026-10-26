"""Private, bounded, verified artifact persistence for Hoshi (Task 28).

Only a trusted Python caller can persist a completed, independently verified
Flora ad pack for a *running* job. HTTP callers cannot upload artifacts or
write checkpoints. Storage requires an operator-owned 0700 absolute directory
on a persistent volume; Render's default filesystem is not redeploy durable.
No prompt, key, screenshot or arbitrary filename is stored.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import os
from pathlib import Path
import re
import stat
import time

try:
    from .artifact_verifier import verify_ad_pack, ArtifactVerificationError
    from .job_records import JobRecordStore, _ID_RE
except ImportError:
    from artifact_verifier import verify_ad_pack, ArtifactVerificationError
    from job_records import JobRecordStore, _ID_RE

_PRODUCT_REQUESTS = {
    "gold_kit": "Create Flora gold facial kit ads",
    "shampoo": "Create Flora shampoo ads",
}
_STAGES = (
    ("planner", "trusted_scope"),
    ("designer", "catalog_theme"),
    ("coder", "local_renderer"),
    ("tester", "zip_png_copy_verified"),
)
_MAX_BYTES = 5_000_000
_FILENAME = "flora_ads.zip"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class ArtifactStorageError(ValueError):
    """Safe error category; never contains user data or filesystem paths."""


def _private_dir(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ArtifactStorageError("private_directory_unavailable")
    mode = path.stat().st_mode
    if mode & 0o077 or not stat.S_ISDIR(mode):
        raise ArtifactStorageError("private_directory_permissions")


class VerifiedArtifactStore:
    """A small operator-only store; read access must be authenticated by caller."""

    def __init__(self, jobs: JobRecordStore, root: str | Path):
        if not isinstance(jobs, JobRecordStore):
            raise TypeError("Expected a job record store")
        directory = Path(root)
        if not directory.is_absolute():
            raise ArtifactStorageError("absolute_directory_required")
        _private_dir(directory)
        self.jobs = jobs
        self.root = directory
        with jobs._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS hoshi_verified_artifacts (
                job_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                created_ms INTEGER NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS hoshi_job_checkpoints (
                job_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                evidence_code TEXT NOT NULL,
                created_ms INTEGER NOT NULL,
                PRIMARY KEY (job_id, stage)
            )""")

    @staticmethod
    def _valid_id(job_id: str) -> None:
        if not isinstance(job_id, str) or not _ID_RE.fullmatch(job_id):
            raise ArtifactStorageError("invalid_job_id")

    @staticmethod
    def _metadata(row):
        return None if row is None else {
            "job_id": row["job_id"], "name": row["name"],
            "sha256": row["sha256"], "size_bytes": row["size_bytes"],
            "created_ms": row["created_ms"],
        }

    def _running(self, conn, job_id: str) -> bool:
        row = conn.execute("""SELECT j.kind, j.status, q.state
            FROM hoshi_jobs j JOIN hoshi_job_queue q ON j.id=q.job_id
            WHERE j.id=?""", (job_id,)).fetchone()
        return bool(row and row["kind"] == "create_product_ads" and
                    row["status"] == "running" and row["state"] == "running")

    def _job_directory(self, job_id: str) -> Path:
        directory = self.root / job_id
        try:
            directory.mkdir(mode=0o700, exist_ok=True)
            _private_dir(directory)
        except OSError:
            raise ArtifactStorageError("private_directory_unavailable") from None
        return directory

    @staticmethod
    def _decode_verified(result: dict) -> tuple[bytes, str]:
        if not isinstance(result, dict) or result.get("ok") is not True or (
            result.get("kind") != "create_product_ads" or
            result.get("status") != "verified_in_memory" or
            result.get("persisted") is not False
        ):
            raise ArtifactStorageError("unverified_result")
        key = result.get("product_key")
        if type(key) is not str or key not in _PRODUCT_REQUESTS:
            raise ArtifactStorageError("unsupported_product")
        steps = result.get("steps")
        if not isinstance(steps, list) or len(steps) != len(_STAGES):
            raise ArtifactStorageError("unverified_roles")
        for step, (stage, evidence) in zip(steps, _STAGES):
            if not isinstance(step, dict) or (
                step.get("role"), step.get("status"), step.get("evidence_code")
            ) != (stage, "verified", evidence):
                raise ArtifactStorageError("unverified_roles")
        pack = result.get("artifact")
        try:
            if verify_ad_pack(pack, _PRODUCT_REQUESTS[key]).get("passed") is not True:
                raise ArtifactStorageError("verification_failed")
        except (ArtifactVerificationError, ValueError, TypeError, KeyError):
            raise ArtifactStorageError("verification_failed") from None
        encoded = pack.get("zip_base64")
        if not isinstance(encoded, str) or len(encoded) > (_MAX_BYTES * 4 // 3) + 12:
            raise ArtifactStorageError("invalid_artifact")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            raise ArtifactStorageError("invalid_artifact") from None
        if not data or len(data) > _MAX_BYTES:
            raise ArtifactStorageError("invalid_artifact")
        digest = hashlib.sha256(data).hexdigest()
        if result.get("artifact_sha256") != digest or result.get("artifact_size_bytes") != len(data):
            raise ArtifactStorageError("digest_mismatch")
        return data, digest

    def save_verified(self, job_id: str, result: dict) -> dict:
        """Persist a trusted four-role result; never marks a job succeeded.

        Exclusive 0600 file creation plus atomic hard-link publication prevents
        overwrite. An interrupted metadata write leaves a safe orphan which
        can be re-attached only if the same verified digest is presented.
        """
        self._valid_id(job_id)
        data, digest = self._decode_verified(result)
        with self.jobs._connect() as conn:
            if not self._running(conn, job_id):
                raise ArtifactStorageError("job_not_running")
        directory = self._job_directory(job_id)
        final = directory / _FILENAME
        temporary = directory / ("." + os.urandom(12).hex() + ".tmp")
        try:
            fd = os.open(str(temporary), os.O_CREAT | os.O_EXCL | os.O_WRONLY |
                         getattr(os, "O_NOFOLLOW", 0), 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, final, follow_symlinks=False)
            except FileExistsError:
                # Immutable existing blob must match, never silently overwrite.
                if self._read_file(final, digest, len(data)) != data:
                    raise ArtifactStorageError("artifact_conflict")
            # Best-effort directory fsync after atomic publication.
            dirfd = os.open(str(directory), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(dirfd)
            finally:
                os.close(dirfd)
        except ArtifactStorageError:
            raise
        except (OSError, ValueError):
            raise ArtifactStorageError("artifact_write_failed") from None
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

        now = time.time_ns() // 1_000_000
        with self.jobs._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if not self._running(conn, job_id):
                    raise ArtifactStorageError("job_not_running")
                old = conn.execute(
                    "SELECT * FROM hoshi_verified_artifacts WHERE job_id=?",
                    (job_id,)
                ).fetchone()
                if old is not None and (
                    old["sha256"] != digest or old["size_bytes"] != len(data)
                    or old["name"] != _FILENAME
                ):
                    raise ArtifactStorageError("artifact_conflict")
                if old is None:
                    conn.execute("""INSERT INTO hoshi_verified_artifacts
                        (job_id,name,sha256,size_bytes,created_ms)
                        VALUES (?,?,?,?,?)""",
                        (job_id, _FILENAME, digest, len(data), now))
                for stage, evidence in (*_STAGES, ("persist", "sha256_verified")):
                    existing = conn.execute("""SELECT evidence_code FROM hoshi_job_checkpoints
                        WHERE job_id=? AND stage=?""", (job_id, stage)).fetchone()
                    if existing is not None and existing["evidence_code"] != evidence:
                        raise ArtifactStorageError("checkpoint_conflict")
                    if existing is None:
                        conn.execute("""INSERT INTO hoshi_job_checkpoints
                            (job_id,stage,evidence_code,created_ms)
                            VALUES (?,?,?,?)""", (job_id, stage, evidence, now))
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        metadata = self.metadata(job_id)
        if metadata is None:
            raise ArtifactStorageError("artifact_not_recorded")
        return metadata

    @staticmethod
    def _read_file(path: Path, digest: str, expected_size: int) -> bytes:
        try:
            fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or (
                    info.st_size != expected_size or info.st_size > _MAX_BYTES
                ):
                    raise ArtifactStorageError("artifact_integrity_failed")
                data = stream.read(_MAX_BYTES + 1)
        except ArtifactStorageError:
            raise
        except OSError:
            raise ArtifactStorageError("artifact_unavailable") from None
        if len(data) != expected_size or hashlib.sha256(data).hexdigest() != digest:
            raise ArtifactStorageError("artifact_integrity_failed")
        return data

    def metadata(self, job_id: str) -> dict | None:
        self._valid_id(job_id)
        with self.jobs._connect() as conn:
            return self._metadata(conn.execute(
                "SELECT * FROM hoshi_verified_artifacts WHERE job_id=?", (job_id,)
            ).fetchone())

    def checkpoints(self, job_id: str) -> list[dict]:
        self._valid_id(job_id)
        with self.jobs._connect() as conn:
            rows = conn.execute("""SELECT stage,evidence_code,created_ms
                FROM hoshi_job_checkpoints WHERE job_id=?
                ORDER BY CASE stage
                    WHEN 'planner' THEN 1 WHEN 'designer' THEN 2
                    WHEN 'coder' THEN 3 WHEN 'tester' THEN 4 ELSE 5 END""",
                (job_id,)).fetchall()
        return [dict(row) for row in rows]

    def read_verified(self, job_id: str) -> bytes:
        """Rehash on every private download; never serve tampered/missing data."""
        metadata = self.metadata(job_id)
        if metadata is None:
            raise ArtifactStorageError("artifact_not_found")
        directory = self.root / job_id
        _private_dir(directory)
        if metadata["name"] != _FILENAME or not _DIGEST.fullmatch(metadata["sha256"]):
            raise ArtifactStorageError("artifact_integrity_failed")
        return self._read_file(directory / _FILENAME, metadata["sha256"],
                               metadata["size_bytes"])
