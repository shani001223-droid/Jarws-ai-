"""Independent bounded PCM-energy evidence for a private anime SRT review.

This measures whether the *encoded MP4 soundtrack* contains energy in each
caption window. It does not identify speech, language, spoken words, lip-sync,
voice rights, or whether the sound belongs to the captioned character.
"""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import subprocess
import sys


class AnimeAudioSubtitleQCError(ValueError):
    """Encoded soundtrack unavailable or not independently measurable."""


SAMPLE_RATE = 16000
AUDIBLE_RMS_THRESHOLD = 0.001
# A brief click or beep can raise whole-window RMS. This is only a
# conservative signal-coverage gate, never proof of speech or language.
ACTIVE_FRAME_MS = 20
ACTIVE_FRAME_RMS_THRESHOLD = 0.003
MIN_ACTIVE_FRAME_FRACTION = 0.05
# Repeated short beeps can exceed total frame occupancy without any
# continuous dialogue-like interval. This is still only a signal heuristic.
MIN_LONGEST_ACTIVE_RUN_MS = 150


def measure_encoded_caption_audio(video_path: Path, manifest: dict, ffmpeg: str) -> dict:
    """Decode bounded mono PCM and report actual energy in the three SRT windows.

    The caller must first validate the exact MP4 structure and SRT against the
    storyboard/voice-cue plan. Never infer speech content from signal energy.
    """
    if type(manifest) is not dict or not ffmpeg:
        raise AnimeAudioSubtitleQCError("Bounded manifest and local FFmpeg required.")
    source = manifest.get("subtitle_timing_source")
    if source == "fixed_ten_second_shots":
        windows = [(i * 10000, (i + 1) * 10000) for i in range(3)]
    elif source == "operator_supplied_voice_cues_not_audio_verified":
        handoff = manifest.get("voice_timing_handoff")
        if type(handoff) is not dict or type(handoff.get("plan")) is not dict:
            raise AnimeAudioSubtitleQCError("Validated voice cue plan required.")
        cues = handoff["plan"].get("cues")
        if type(cues) is not list or len(cues) != 3:
            raise AnimeAudioSubtitleQCError("Exactly three voice cues required.")
        windows = []
        for i, cue in enumerate(cues):
            if type(cue) is not dict:
                raise AnimeAudioSubtitleQCError("Invalid cue.")
            start, end = cue.get("start_ms"), cue.get("end_ms")
            if (type(start) is not int or type(end) is not int
                    or not i * 10000 <= start < start + 200 <= end <= (i + 1) * 10000):
                raise AnimeAudioSubtitleQCError("Cue outside shot.")
            windows.append((start, end))
    else:
        raise AnimeAudioSubtitleQCError("Unknown subtitle timing source.")
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
             "-i", str(video_path), "-map", "0:a:0", "-vn", "-t", "30",
             "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le",
             "-f", "s16le", "-"],
            capture_output=True, check=False, timeout=25,
        )
        if (result.returncode != 0 or len(result.stdout) % 2
                or not 470000 * 2 <= len(result.stdout) <= 485000 * 2):
            raise AnimeAudioSubtitleQCError("Encoded soundtrack PCM decode failed.")
        pcm = array("h")
        pcm.frombytes(result.stdout)
        if sys.byteorder != "little":
            pcm.byteswap()
        windows_qc = []
        for index, (start_ms, end_ms) in enumerate(windows):
            start = start_ms * SAMPLE_RATE // 1000
            end = end_ms * SAMPLE_RATE // 1000
            samples = pcm[start:end]
            if not samples:
                raise AnimeAudioSubtitleQCError("Empty decoded caption window.")
            rms = math.sqrt(sum(int(value) ** 2 for value in samples) /
                            len(samples)) / 32768.0
            # Measure occupancy in independent 20 ms PCM frames so a single
            # high-amplitude transient cannot masquerade as sustained audio.
            frame_size = SAMPLE_RATE * ACTIVE_FRAME_MS // 1000
            active_frames = 0
            total_frames = 0
            current_active_run = 0
            longest_active_run = 0
            for offset in range(0, len(samples), frame_size):
                frame = samples[offset:offset + frame_size]
                frame_rms = math.sqrt(sum(int(v) ** 2 for v in frame) /
                                      len(frame)) / 32768.0
                is_active = frame_rms >= ACTIVE_FRAME_RMS_THRESHOLD
                active_frames += is_active
                current_active_run = current_active_run + 1 if is_active else 0
                longest_active_run = max(longest_active_run, current_active_run)
                total_frames += 1
            active_fraction = active_frames / total_frames
            longest_active_run_ms = longest_active_run * ACTIVE_FRAME_MS
            sustained = (rms >= AUDIBLE_RMS_THRESHOLD and
                         active_fraction >= MIN_ACTIVE_FRAME_FRACTION and
                         longest_active_run_ms >= MIN_LONGEST_ACTIVE_RUN_MS)
            windows_qc.append({
                "shot_index": index + 1,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "decoded_rms": round(rms, 6),
                "audible_energy_detected": rms >= AUDIBLE_RMS_THRESHOLD,
                "active_audio_frame_fraction": round(active_fraction, 4),
                "longest_contiguous_active_audio_ms": longest_active_run_ms,
                "sustained_audio_detected": sustained,
            })
        return {
            "status": "encoded_audio_energy_measured_not_speech_recognition",
            "sample_rate_hz": SAMPLE_RATE,
            "threshold_normalized_rms": AUDIBLE_RMS_THRESHOLD,
            "active_frame_ms": ACTIVE_FRAME_MS,
            "active_frame_threshold_normalized_rms": ACTIVE_FRAME_RMS_THRESHOLD,
            "minimum_active_frame_fraction": MIN_ACTIVE_FRAME_FRACTION,
            "minimum_longest_contiguous_active_audio_ms": MIN_LONGEST_ACTIVE_RUN_MS,
            "caption_windows": windows_qc,
            "all_caption_windows_have_audio_energy": all(
                item["audible_energy_detected"] for item in windows_qc),
            "all_caption_windows_have_sustained_audio": all(
                item["sustained_audio_detected"] for item in windows_qc),
            "spoken_words_independently_verified": False,
            "speech_language_independently_verified": False,
            "phoneme_sync_verified": False,
            "music_or_noise_can_trigger": True,
            "owner_approved": False,
            "publication_permitted": False,
        }
    except (OSError, subprocess.TimeoutExpired, OverflowError, ValueError) as exc:
        if isinstance(exc, AnimeAudioSubtitleQCError):
            raise
        raise AnimeAudioSubtitleQCError("Could not decode bounded MP4 audio.") from None
