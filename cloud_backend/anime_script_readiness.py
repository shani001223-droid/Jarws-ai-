"""Offline Task 56 script-readiness audit; no approvals, voices or media.

Counts are estimates from written dialogue, never measured speech duration.
Only the four immutable, locally authored editorial drafts are accepted.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from cloud_backend.anime_series import series_manifest
from cloud_backend.anime_scripts import pilot_script, validate_pilot
from cloud_backend.anime_episode_two import episode_two_script, validate_episode_two
from cloud_backend.anime_episode_three import episode_three_script, validate_episode_three
from cloud_backend.anime_episode_four import episode_four_script, validate_episode_four

DRAFT_FACTORIES = (pilot_script, episode_two_script, episode_three_script, episode_four_script)
DRAFT_VALIDATORS = (validate_pilot, validate_episode_two, validate_episode_three, validate_episode_four)
BLOCKERS = (
    "human_roman_urdu_editorial_review",
    "measured_table_read_and_action_pacing",
    "owner_screenplay_approval",
    "voice_cast_consent_and_recording_rights",
)
WORDS_PER_MINUTE_REFERENCE = 120  # Illustrative only, not an observed performance.


def _canonical(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _episode_row(draft: dict, episode_number: int, outline_digest: str) -> dict:
    if not isinstance(draft, dict) or draft != DRAFT_FACTORIES[episode_number - 1]():
        raise ValueError("untrusted_or_modified_draft")
    DRAFT_VALIDATORS[episode_number - 1](draft)
    if draft["episode_id"] != f"EP{episode_number:03d}":
        raise ValueError("episode_id")
    if draft["source_outline_sha256"] != outline_digest:
        raise ValueError("outline_revision")
    if draft["approval"] != "editorial_draft_not_reviewed":
        raise ValueError("false_approval")
    if any(draft[key] is not False for key in
           ("human_reviewed", "spoken_duration_verified", "rendered")):
        raise ValueError("false_completion")
    if episode_number > 1:
        previous = DRAFT_FACTORIES[episode_number - 2]()
        if draft.get("previous_episode_id") != previous["episode_id"]:
            raise ValueError("broken_previous_episode")
        if draft.get("previous_episode_sha256") != previous["sha256"]:
            raise ValueError("broken_revision_chain")
    scenes = draft["scenes"]
    if not scenes or any(not scene["dialogue"] for scene in scenes):
        raise ValueError("empty_scene")
    words = sum(len(turn["text"].split()) for scene in scenes for turn in scene["dialogue"])
    turns = sum(len(scene["dialogue"]) for scene in scenes)
    planned = sum(scene["planned_seconds"] for scene in scenes)
    if planned != draft["planned_seconds"] or planned != 1800:
        raise ValueError("invalid_planned_slots")
    # This number intentionally excludes acting, silences, blocking and transitions.
    estimated = words * 60 // WORDS_PER_MINUTE_REFERENCE
    return {
        "episode_id": draft["episode_id"],
        "draft_sha256": draft["sha256"],
        "scene_count": len(scenes),
        "dialogue_turns": turns,
        "dialogue_words": words,
        "planned_scene_seconds": planned,
        "illustrative_spoken_seconds_at_120_wpm": estimated,
        "illustrative_unaccounted_seconds": max(0, planned - estimated),
        "measured_runtime_seconds": None,
        "human_reviewed": False,
        "approved": False,
        "verified_30_minute_screenplay": False,
        "production_ready": False,
        "blockers": list(BLOCKERS),
    }


def _payload() -> dict:
    manifest = series_manifest()
    rows = [_episode_row(factory(), i, manifest["sha256"])
            for i, factory in enumerate(DRAFT_FACTORIES, 1)]
    return {
        "schema_version": 1,
        "title": manifest["title"],
        "source_outline_sha256": manifest["sha256"],
        "scope": "EP001-EP004 locally authored editorial drafts only",
        "target_episode_seconds": 1800,
        "reference_wpm": WORDS_PER_MINUTE_REFERENCE,
        "reference_is_measured": False,
        "episodes": rows,
        "reviewed_scripts": 0,
        "approved_scripts": 0,
        "production_ready_scripts": 0,
        "remaining_individual_scripts": manifest["target_episodes"] - len(rows),
        "published": False,
        "external_media_generated": False,
    }


def build_readiness_report() -> dict:
    """Return an immutable-by-copy, deterministic private QA report."""
    result = _payload()
    result["sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    validate_readiness_report(result)
    return result


def validate_readiness_report(report: dict) -> None:
    """Reject changed counts, forged reviews and even re-hashed report edits."""
    if not isinstance(report, dict):
        raise ValueError("invalid_report")
    expected = _payload()
    if set(report) != set(expected) | {"sha256"}:
        raise ValueError("report_schema")
    if any(type(report.get(k)) is not type(v) or report[k] != v
           for k, v in expected.items()):
        raise ValueError("report_tampering_or_false_completion")
    if report.get("sha256") != hashlib.sha256(_canonical(expected)).hexdigest():
        raise ValueError("report_digest")
