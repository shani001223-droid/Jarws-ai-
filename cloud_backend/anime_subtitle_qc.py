"""Fail-closed private SRT-to-storyboard consistency check for Hoshi Anime Studio.

Checks exact UTF-8 subtitle text and timing against the bound operator plan.
It cannot establish that recorded speech contains the caption or is in sync.
No network, uploads, publication or approval side effects.
"""
from __future__ import annotations

import hashlib
import json
import re


class AnimeSubtitleQCError(ValueError):
    """Invalid or unbound private animatic subtitles."""


_TIMING = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\Z"
)


def _digest_plan(plan: dict) -> str:
    data = json.dumps(plan, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _milliseconds(parts: tuple[str, ...]) -> int:
    hours, minutes, seconds, millis = map(int, parts)
    if hours != 0 or minutes >= 60 or seconds >= 60:
        raise AnimeSubtitleQCError("Invalid SRT timestamp.")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def validate_private_subtitles(manifest: object, subtitles: bytes) -> dict:
    """Validate exactly three SRT blocks against storyboard or voice-cue plan.

    Manifest hashes and caller-provided cues remain operator provenance, not
    independent verification of spoken audio, language, rights or lip-sync.
    """
    if (type(manifest) is not dict or type(subtitles) is not bytes
            or not 1 <= len(subtitles) <= 20_000):
        raise AnimeSubtitleQCError("Bounded manifest and UTF-8 SRT required.")
    try:
        text = subtitles.decode("utf-8", errors="strict")
    except UnicodeError:
        raise AnimeSubtitleQCError("SRT is not valid UTF-8.") from None
    if (not text.endswith("\n\n") or "\r" in text or "\x00" in text
            or text.startswith("\ufeff")):
        raise AnimeSubtitleQCError("Noncanonical SRT line endings or encoding.")
    blocks = text[:-2].split("\n\n")
    if len(blocks) != 3:
        raise AnimeSubtitleQCError("Exactly three subtitle blocks required.")

    storyboard = manifest.get("storyboard_handoff")
    if type(storyboard) is not dict or type(storyboard.get("plan")) is not dict:
        raise AnimeSubtitleQCError("Storyboard provenance is required for subtitle QC.")
    plan = storyboard["plan"]
    shots = plan.get("shots")
    if (type(shots) is not list or len(shots) != 3
            or storyboard.get("plan_sha256") != _digest_plan(plan)):
        raise AnimeSubtitleQCError("Storyboard digest or three-shot plan mismatch.")

    source = manifest.get("subtitle_timing_source")
    voice = manifest.get("voice_timing_handoff")
    if source == "operator_supplied_voice_cues_not_audio_verified":
        if type(voice) is not dict or type(voice.get("plan")) is not dict:
            raise AnimeSubtitleQCError("Operator cue plan missing.")
        cue_plan = voice["plan"]
        cues = cue_plan.get("cues")
        if (type(cues) is not list or len(cues) != 3
                or voice.get("plan_sha256") != _digest_plan(cue_plan)
                or cue_plan.get("storyboard_sha256") != storyboard["plan_sha256"]
                or cue_plan.get("audio_sha256") != manifest.get("source_audio_sha256")
                or type(cue_plan.get("audio_sha256")) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", cue_plan["audio_sha256"])):
            raise AnimeSubtitleQCError("Cue digest or audio/storyboard binding mismatch.")
    elif source == "fixed_ten_second_shots":
        if voice is not None:
            raise AnimeSubtitleQCError("Fixed subtitle timing cannot carry a voice plan.")
        cues = None
    else:
        raise AnimeSubtitleQCError("Unknown subtitle timing source.")

    for index, block in enumerate(blocks):
        parts = block.split("\n")
        if len(parts) != 3 or parts[0] != str(index + 1):
            raise AnimeSubtitleQCError("SRT block numbering or layout mismatch.")
        match = _TIMING.fullmatch(parts[1])
        if match is None:
            raise AnimeSubtitleQCError("Invalid SRT time range.")
        start = _milliseconds(match.groups()[:4])
        end = _milliseconds(match.groups()[4:])
        shot = shots[index]
        if (type(shot) is not dict or type(shot.get("caption")) is not str
                or not 1 <= len(shot["caption"]) <= 180
                or parts[2] != shot["caption"]
                or any(ord(ch) < 32 or ch in "<>\u202e\u202d\u2066\u2067\u2068\u2069"
                       for ch in parts[2])):
            raise AnimeSubtitleQCError("Subtitle text differs from bound storyboard.")
        if cues is None:
            expected_start, expected_end = index * 10_000, (index + 1) * 10_000
        else:
            cue = cues[index]
            if (type(cue) is not dict
                    or cue.get("shot_id") != shot.get("shot_id")
                    or cue.get("text") != shot["caption"]
                    or type(cue.get("start_ms")) is not int
                    or type(cue.get("end_ms")) is not int):
                raise AnimeSubtitleQCError("Cue and storyboard shot mismatch.")
            expected_start, expected_end = cue["start_ms"], cue["end_ms"]
            if not (index * 10_000 <= expected_start
                    < expected_start + 200 <= expected_end
                    <= (index + 1) * 10_000):
                raise AnimeSubtitleQCError("Voice cue is outside its shot.")
        if start != expected_start or end != expected_end:
            raise AnimeSubtitleQCError("Subtitle interval differs from bound plan.")

    return {
        "status": "srt_matches_bound_storyboard_and_operator_timing",
        "subtitle_timing_source": source,
        "subtitle_blocks": 3,
        "spoken_words_independently_verified": False,
        "audio_sync_independently_verified": False,
        "owner_approved": False,
        "publication_permitted": False,
    }
