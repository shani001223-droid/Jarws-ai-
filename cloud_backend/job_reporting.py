"""Read-only, private, evidence-gated job progress and final reports (Task 30).

This is a *pull* report for an authenticated operator, not a notification
service, worker, task scheduler, or proof that production has been deployed.
Only stable enums, bounded timestamps and verified artifact metadata leave
this module. It never includes prompts, secrets, file paths or screenshots.
"""
from __future__ import annotations

from .job_records import JobRecordStore, _ID_RE
from .job_queue import ScheduledJobQueue
from .verified_artifact_store import VerifiedArtifactStore, ArtifactStorageError
from .job_recovery import _REQUIRED_CHECKPOINTS

# Explicitly recognized failure reasons; arbitrary worker text never leaves.
_FAILURE_CODES = frozenset({
    "executor_failed", "invalid_executor_result", "no_executor_artifacts",
    "recovery_artifact_invalid", "recovery_review_required",
})
_TERMINAL = frozenset({"succeeded", "failed", "canceled"})
_STAGES = tuple(stage for stage, _ in _REQUIRED_CHECKPOINTS)


def build_job_report(jobs: JobRecordStore, job_id: str,
                     artifacts: VerifiedArtifactStore | None = None) -> dict | None:
    """Build a bounded read-only report; return None for unknown/invalid IDs.

    Success is only a *verified final report* after an immutable Flora ZIP is
    rehashed and every trusted role checkpoint matches. A DB status flag
    alone is not completion evidence. The API never sends notifications.
    """
    if not isinstance(jobs, JobRecordStore):
        raise TypeError("Expected private job records")
    if not isinstance(job_id, str) or not _ID_RE.fullmatch(job_id):
        return None
    if artifacts is not None and (
        not isinstance(artifacts, VerifiedArtifactStore)
        or artifacts.jobs.path.resolve() != jobs.path.resolve()
    ):
        raise ValueError("Artifact store mismatch")
    job = jobs.get(job_id)
    if job is None:
        return None
    queue = ScheduledJobQueue(jobs).status(job_id)
    state = job["status"]
    report = {
        "job_id": job["id"],
        "kind": job["kind"],
        "status": state,
        "version": job["version"],
        "updated_ms": job["updated_ms"],
        "queue": None if queue is None else {
            "state": queue["state"],
            "due_ms": queue["due_ms"],
            "attempts": queue["attempts"],
        },
        "phase": "review_required",
        "message_code": "state_needs_review",
        "blocker_code": None,
        "attention_scope": "none",
        "quiet": True,
        "notifications_sent": False,
        "report_ready": False,
        "evidence": {"verified": False, "checkpoint_stages": []},
        "final_artifact": None,
    }
    # Never report arbitrary checkpoint strings or caller-supplied text.
    checkpoints = []
    if artifacts is not None:
        try:
            checkpoints = artifacts.checkpoints(job_id)
        except (ArtifactStorageError, OSError, ValueError):
            checkpoints = []
    matched = [
        stage for stage, code in _REQUIRED_CHECKPOINTS
        if any(c.get("stage") == stage and c.get("evidence_code") == code
               for c in checkpoints)
    ]
    report["evidence"]["checkpoint_stages"] = matched
    queue_state = queue["state"] if queue else None

    if state == "planned" and queue is None:
        report.update(phase="planned", message_code="awaiting_operator_schedule",
                      blocker_code="not_scheduled", attention_scope="operator")
    elif state == "queued" and queue_state == "pending":
        # The API registers no executor; scheduling is not execution.
        report.update(phase="queued", message_code="awaiting_trusted_executor",
                      blocker_code="executor_not_configured", attention_scope="operator")
    elif state == "running" and queue_state == "running":
        # A running DB row may represent a crashed process; no live heartbeat.
        report.update(phase="unconfirmed_running", message_code="worker_state_unverified")
    elif state == "failed" and queue_state in ("failed", None):
        code = job["detail_code"]
        safe_code = code if code in _FAILURE_CODES else "job_failed_review"
        report.update(phase="blocked", message_code="job_failed",
                      blocker_code=safe_code, attention_scope="operator",
                      report_ready=True)
    elif state == "canceled" and queue_state in ("canceled", None):
        report.update(phase="stopped", message_code="job_canceled",
                      report_ready=True)
    elif state == "succeeded" and queue_state == "succeeded":
        verified = False
        metadata = None
        if (job["kind"] == "create_product_ads"
                and job["detail_code"] == "artifacts_verified"
                and artifacts is not None
                and [(c.get("stage"), c.get("evidence_code")) for c in checkpoints]
                == list(_REQUIRED_CHECKPOINTS)):
            try:
                metadata = artifacts.metadata(job_id)
                if metadata is not None and metadata["name"] == "flora_ads.zip":
                    # Re-read and rehash actual bytes. Metadata alone is not proof.
                    verified = bool(artifacts.read_verified(job_id))
            except (ArtifactStorageError, OSError, ValueError):
                verified = False
        if verified:
            report.update(phase="completed", message_code="verified_final_report",
                          report_ready=True,
                          final_artifact={
                              "name": "flora_ads.zip",
                              "sha256": metadata["sha256"],
                              "size_bytes": metadata["size_bytes"],
                              "download_path": f"/api/agent/jobs/{job_id}/artifacts/download",
                          })
            report["evidence"]["verified"] = True
        else:
            report.update(phase="review_required",
                          message_code="completion_evidence_missing",
                          blocker_code="artifact_verification_required",
                          attention_scope="operator")
    else:
        # A job/queue disagreement is not a successful final report.
        report.update(phase="review_required", message_code="state_mismatch",
                      blocker_code="queue_reconciliation_required",
                      attention_scope="operator")
    return report
