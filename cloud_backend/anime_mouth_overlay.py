"""Offline, rights-attested two-state mouth-sprite preview for Hoshi Anime Studio.

An operator supplies original transparent mouth-open PNG sprites and positions.
RMS energy windows turn each sprite on/off inside the corresponding voice cue.
This is *not* phoneme lip-sync, voice verification, or automatic face tracking.
"""
from __future__ import annotations

from io import BytesIO
import hashlib

from PIL import Image, UnidentifiedImageError


class MouthOverlayError(ValueError):
    """Invalid, unlicensed or mismatched mouth-overlay preview input."""


MAX_SPRITE_BYTES = 250_000


def bind_mouth_overlay(plan: object, sprites: object, voice_timing: object,
                       audio_energy: object, *, rights_attested: bool = False) -> dict:
    """Bind exactly three original PNG sprites to the verified audio-energy handoff."""
    if rights_attested is not True:
        raise MouthOverlayError("Explicit rights attestation for mouth sprites is required.")
    if (type(plan) is not dict or set(plan) != {"schema_version", "sprites"}
            or type(plan["schema_version"]) is not int or plan["schema_version"] != 1
            or type(plan["sprites"]) is not list or len(plan["sprites"]) != 3
            or type(sprites) not in (tuple, list) or len(sprites) != 3):
        raise MouthOverlayError("Exactly three v1 mouth-sprite entries are required.")
    if (type(voice_timing) is not dict or type(audio_energy) is not dict
            or type(voice_timing.get("plan")) is not dict
            or type(voice_timing["plan"].get("cues")) is not list
            or len(voice_timing["plan"]["cues"]) != 3
            or type(voice_timing.get("plan_sha256")) is not str
            or audio_energy.get("voice_timing_sha256") != voice_timing["plan_sha256"]
            or type(voice_timing["plan"].get("audio_sha256")) is not str
            or type(audio_energy.get("audio_sha256")) is not str
            or audio_energy["audio_sha256"] != voice_timing["plan"]["audio_sha256"]
            or type(audio_energy.get("schema_version")) is not int
            or audio_energy["schema_version"] != 1
            or type(audio_energy.get("shots")) is not list
            or len(audio_energy["shots"]) != 3
            or type(audio_energy.get("frame_rate")) is not int
            or audio_energy["frame_rate"] != 12):
        raise MouthOverlayError("Bound voice timing and WAV energy are required.")
    bound = []
    for index, (entry, source, cue, activity) in enumerate(zip(
            plan["sprites"], sprites, voice_timing["plan"]["cues"],
            audio_energy["shots"])):
        if (type(cue) is not dict or type(activity) is not dict
                or type(cue.get("shot_id")) is not str
                or type(cue.get("speaker_id")) is not str
                or type(activity.get("shot_id")) is not str
                or type(activity.get("speaker_id")) is not str):
            raise MouthOverlayError("Bound voice cue or audio activity is invalid.")
        if type(entry) is not dict or set(entry) != {
                "shot_id", "speaker_id", "png_sha256", "x", "y"}:
            raise MouthOverlayError("Mouth sprite entry schema is invalid.")
        if (type(source) is not bytes or not 80 <= len(source) <= MAX_SPRITE_BYTES
                or type(entry["shot_id"]) is not str
                or entry["shot_id"] != cue["shot_id"]
                or entry["shot_id"] != activity["shot_id"]
                or type(entry["speaker_id"]) is not str
                or entry["speaker_id"] != cue["speaker_id"]
                or entry["speaker_id"] != activity["speaker_id"]
                or type(entry["png_sha256"]) is not str
                or entry["png_sha256"] != hashlib.sha256(source).hexdigest()
                or type(entry["x"]) is not int or type(entry["y"]) is not int
                or not 0 <= entry["x"] <= 472 or not 0 <= entry["y"] <= 262):
            raise MouthOverlayError("Mouth sprite source, speaker or coordinates mismatch.")
        try:
            with Image.open(BytesIO(source)) as image:
                if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
                    raise MouthOverlayError("Mouth sprites must be single-frame PNG.")
                if image.mode != "RGBA" or not (8 <= image.width <= 128
                                                 and 8 <= image.height <= 128):
                    raise MouthOverlayError("Mouth sprites must be small transparent RGBA PNG.")
                image.load()
                low, high = image.getchannel("A").getextrema()
                if low != 0 or high == 0:
                    raise MouthOverlayError("Mouth sprite must contain visible and transparent pixels.")
                if entry["x"] + image.width > 480 or entry["y"] + image.height > 270:
                    raise MouthOverlayError("Mouth sprite extends outside the frame.")
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise MouthOverlayError("Mouth sprite could not be decoded safely.") from None
        if (type(cue) is not dict or type(activity) is not dict
                or type(cue.get("start_ms")) is not int
                or type(cue.get("end_ms")) is not int
                or not index * 10000 <= cue["start_ms"] < cue["end_ms"] <= (index + 1) * 10000):
            raise MouthOverlayError("Bound dialogue cue interval is invalid.")
        windows = activity.get("energy_windows_ms")
        if type(windows) is not list or len(windows) > 120:
            raise MouthOverlayError("Invalid bounded audio activity windows.")
        previous = index * 10000
        normalized = []
        for window in windows:
            if (type(window) is not list or len(window) != 2
                    or any(type(v) is not int for v in window)
                    or not cue["start_ms"] <= window[0] < window[1] <= cue["end_ms"]
                    or window[0] < previous):
                raise MouthOverlayError("Audio activity windows must be ordered and in-shot.")
            normalized.append(list(window))
            previous = window[1]
        bound.append({
            "shot_id": entry["shot_id"], "speaker_id": entry["speaker_id"],
            "png_sha256": entry["png_sha256"], "x": entry["x"], "y": entry["y"],
            "width": image.width, "height": image.height,
            "energy_windows_ms": normalized,
            "sprite_visible_frames_expected": bool(normalized),
        })
    return {
        "schema_version": 1,
        "source": "operator_positioned_original_two_state_mouth_sprite_audio_energy_only",
        "audio_sha256": audio_energy["audio_sha256"],
        "voice_timing_sha256": voice_timing["plan_sha256"],
        "sprites": bound,
        "two_state_sprite_animation_generated": any(
            item["sprite_visible_frames_expected"] for item in bound),
        "phoneme_lip_sync_generated": False,
        "voice_language_verified": False,
        "face_tracking_performed": False,
        "visual_alignment_verified": False,
        "owner_approved": False,
    }


def sprite_enable_expression(shot_index: int, windows: list[list[int]]) -> str:
    """FFmpeg expression from bounded, already-validated shot-local intervals."""
    if not windows:
        return "0"
    return "+".join(
        f"gte(t,{(start - shot_index * 10000) / 1000:.3f})*"
        f"lt(t,{(end - shot_index * 10000) / 1000:.3f})"
        for start, end in windows
    )
