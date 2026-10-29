"""Private WAV energy-to-timing handoff for an existing Hoshi storyboard.

Waveform energy is NOT speech recognition, phoneme alignment or lip-sync.
No images, characters or video are animated by this module.
"""
from __future__ import annotations

from array import array
import hashlib
from io import BytesIO
import math
import sys
import wave


class AudioEnergyError(ValueError):
    """The supplied WAV cannot be bound safely to a voice timing plan."""


def build_audio_energy_handoff(wav: bytes, voice_timing: dict) -> dict:
    """Produce bounded per-shot energy windows at the animatic's 12 FPS.

    Windows are clamped to operator-supplied cue intervals. Background music,
    noise and silence cannot be distinguished from actual speech by energy.
    """
    if type(wav) is not bytes or type(voice_timing) is not dict:
        raise AudioEnergyError("An attested WAV and bound voice cues are required.")
    plan = voice_timing.get("plan")
    if (type(plan) is not dict or type(plan.get("cues")) is not list
            or len(plan["cues"]) != 3
            or type(plan.get("audio_sha256")) is not str
            or plan["audio_sha256"] != hashlib.sha256(wav).hexdigest()
            or type(voice_timing.get("plan_sha256")) is not str):
        raise AudioEnergyError("Voice cue plan does not bind to this WAV.")
    try:
        with wave.open(BytesIO(wav), "rb") as stream:
            rate, count = stream.getframerate(), stream.getnframes()
            if (stream.getcomptype() != "NONE" or stream.getnchannels() != 1
                    or stream.getsampwidth() != 2 or rate not in (16000, 24000)
                    or not 30 <= count / rate <= 30.2):
                raise AudioEnergyError("Only 30-second mono 16-bit PCM WAV is supported.")
            raw = stream.readframes(count)
            if len(raw) != count * 2:
                raise AudioEnergyError("Truncated WAV audio.")
    except (wave.Error, OSError, EOFError, ValueError, ZeroDivisionError) as exc:
        raise AudioEnergyError("WAV cannot be decoded safely.") from exc
    samples = array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    fps = 12
    energy = []
    for frame in range(30 * fps):
        start = frame * rate // fps
        end = min((frame + 1) * rate // fps, count)
        if end <= start:
            raise AudioEnergyError("Insufficient WAV samples for frame timing.")
        rms = math.sqrt(sum(value * value for value in samples[start:end]) / (end - start)) / 32768
        energy.append(rms)
    shots = []
    total_active = 0
    for index, cue in enumerate(plan["cues"]):
        if (type(cue) is not dict or type(cue.get("shot_id")) is not str
                or type(cue.get("speaker_id")) is not str
                or type(cue.get("start_ms")) is not int
                or type(cue.get("end_ms")) is not int
                or not index * 10000 <= cue["start_ms"] < cue["end_ms"] <= (index + 1) * 10000):
            raise AudioEnergyError("Voice cue intervals are invalid.")
        frame_indices = [frame for frame in range(index * 120, (index + 1) * 120)
                         if (frame * 1000 // fps < cue["end_ms"]
                             and (frame + 1) * 1000 // fps > cue["start_ms"])]
        peak = max((energy[frame] for frame in frame_indices), default=0)
        threshold = max(0.015, peak * 0.20)
        windows = []
        active_start = None
        active_end = None
        for frame in frame_indices:
            begin = max(frame * 1000 // fps, cue["start_ms"])
            end = min((frame + 1) * 1000 // fps, cue["end_ms"])
            active = energy[frame] >= threshold and end > begin
            if active:
                total_active += 1
                if active_start is None:
                    active_start = begin
                active_end = end
            elif active_start is not None:
                windows.append([active_start, active_end])
                active_start = active_end = None
        if active_start is not None:
            windows.append([active_start, active_end])
        shots.append({"shot_id": cue["shot_id"], "speaker_id": cue["speaker_id"],
                      "energy_windows_ms": windows})
    return {
        "schema_version": 1,
        "audio_sha256": hashlib.sha256(wav).hexdigest(),
        "voice_timing_sha256": voice_timing["plan_sha256"],
        "frame_rate": fps,
        "frames_analyzed": 360,
        "active_frames": total_active,
        "shots": shots,
        "source": "wav_rms_energy_only_not_speech_or_phoneme_verified",
        "lip_sync_generated": False,
        "character_animation_generated": False,
        "owner_approved": False,
    }
