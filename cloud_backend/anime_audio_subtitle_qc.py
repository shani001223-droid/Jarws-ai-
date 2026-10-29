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
            windows_qc.append({
                "shot_index": index + 1,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "decoded_rms": round(rms, 6),
                "audible_energy_detected": rms >= AUDIBLE_RMS_THRESHOLD,
            })
        return {
            "status": "encoded_audio_energy_measured_not_speech_recognition",
            "sample_rate_hz": SAMPLE_RATE,
            "threshold_normalized_rms": AUDIBLE_RMS_THRESHOLD,
            "caption_windows": windows_qc,
            "all_caption_windows_have_audio_energy": all(
                item["audible_energy_detected"] for item in windows_qc),
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
