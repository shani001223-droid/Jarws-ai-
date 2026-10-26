"""Deterministic Hoshi milestone planner; no worker or job side effects.

Each milestone requires verifiable evidence before a future scheduler may mark
it completed. A plan is never a substitute for a rendered file or APK.
"""
from math import ceil

try:
    from .goal_spec import goal_to_deliverables
except ImportError:  # direct uvicorn main:app from cloud_backend/
    from goal_spec import goal_to_deliverables


def plan_milestones(message: str) -> dict:
    spec = goal_to_deliverables(message)
    deliverables = spec["deliverables"]
    milestones = []
    for index, deliverable in enumerate(deliverables):
        dependencies = [milestones[-1]["id"]] if milestones else []
        milestones.append({
            "id": deliverable["id"],
            "order": index + 1,
            "depends_on": dependencies,
            "output_format": deliverable["format"],
            "acceptance": deliverable["acceptance"],
            "verification": "Inspect actual output, run format/quality checks and record artifact evidence.",
            "status": "not_started",
            "evidence": [],
        })

    batches = None
    if spec["intent"] == "render_anime":
        count = spec["scope"].get("episode_count")
        if count is not None and count > 0:
            # Metadata only. No episodes are queued or claimed as rendered.
            size = min(10, count)
            batches = {
                "batch_size": size,
                "batch_count": ceil(count / size),
                "requires_episode_level_qc": True,
                "note": "Process one batch at a time after worker, storage, budget and QC gates are implemented.",
            }

    return {
        "intent": spec["intent"],
        "mode": spec["mode"],
        "execution_status": "not_started",
        "plan_only": True,
        "job_created": False,
        "milestones": milestones,
        "batching": batches,
        "blockers": spec["blockers"],
        "next_milestone": milestones[0]["id"] if milestones and spec["executor_ready"] else None,
        "notes": "Milestones and dependencies are a proposed acceptance plan. No task has run.",
    }
