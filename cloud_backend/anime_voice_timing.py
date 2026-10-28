"""Private, exact-byte voice cue handoff for a three-shot Hoshi animatic.

Cue timing is supplied by an operator and bound to an attested WAV and the
existing storyboard. It is NOT ASR, voice synthesis, dubbing or lip-sync.
"""
from __future__ import annotations

import hashlib
import json


class VoiceTimingError(ValueError):
    """Voice timing plan cannot be bound safely to storyboard and WAV."""


def bind_voice_timing_handoff(cue_plan: object, storyboard_handoff: object,
                              wav: bytes | None) -> dict:
    """Validate one caption-matching, character-bound cue per 10-second shot."""
    if type(wav) is not bytes or type(storyboard_handoff) is not dict:
        raise VoiceTimingError("Voice timing requires an attested WAV and bound storyboard.")
    if type(cue_plan) is not dict or set(cue_plan) != {
        "schema_version", "language", "audio_sha256", "cues"
    }:
        raise VoiceTimingError("Voice timing must use the exact v1 schema.")
    storyboard = storyboard_handoff.get("plan")
    if type(storyboard) is not dict:
        raise VoiceTimingError("Bound storyboard is missing.")
    if type(cue_plan["schema_version"]) is not int or cue_plan["schema_version"] != 1:
        raise VoiceTimingError("Unsupported voice timing schema.")
    if (type(cue_plan["language"]) is not str
            or cue_plan["language"] != storyboard["language"]):
        raise VoiceTimingError("Voice timing language must match storyboard.")
    digest = hashlib.sha256(wav).hexdigest()
    if type(cue_plan["audio_sha256"]) is not str or cue_plan["audio_sha256"] != digest:
        raise VoiceTimingError("Voice timing WAV SHA-256 mismatch.")
    cues = cue_plan["cues"]
    if type(cues) is not list or len(cues) != 3:
        raise VoiceTimingError("Exactly three voice cues are required.")
    bound_cues = []
    for index, cue in enumerate(cues):
        shot = storyboard["shots"][index]
        if type(cue) is not dict or set(cue) != {
            "shot_id", "speaker_id", "start_ms", "end_ms", "text"
        }:
            raise VoiceTimingError("Voice cue schema is invalid.")
        start, end = cue["start_ms"], cue["end_ms"]
        if (type(cue["shot_id"]) is not str or cue["shot_id"] != shot["shot_id"]
                or type(cue["speaker_id"]) is not str
                or cue["speaker_id"] not in shot["character_ids"]
                or type(cue["text"]) is not str or cue["text"] != shot["caption"]
                or type(start) is not int or type(end) is not int
                or not index * 10000 <= start
                or not start + 200 <= end <= (index + 1) * 10000):
            raise VoiceTimingError("Voice cue must match shot, character, caption and time window.")
        bound_cues.append({
            "shot_id": shot["shot_id"], "speaker_id": cue["speaker_id"],
            "start_ms": start, "end_ms": end, "text": cue["text"]
        })
    normalized = {
        "schema_version": 1, "language": storyboard["language"],
        "audio_sha256": digest, "storyboard_sha256": storyboard_handoff["plan_sha256"],
        "cues": bound_cues
    }
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    if len(raw) > 5000:
        raise VoiceTimingError("Voice timing metadata is oversized.")
    return {
        "plan": normalized, "plan_sha256": hashlib.sha256(raw).hexdigest(),
        "cue_timing_source": "operator_supplied_not_audio_verified",
        "lip_sync_generated": False, "voice_language_verified": False,
        "owner_approved": False
    }
