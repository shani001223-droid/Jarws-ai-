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
# Heavy near-full-scale plateaus can indicate a hard-limited/clipped mix.
# This is a conservative audio-quality warning, NOT proof of clipping or speech.
NEAR_FULL_SCALE_THRESHOLD = 0.99
MAX_NEAR_FULL_SCALE_SAMPLE_FRACTION = 0.10
# AAC can preserve a strong constant/DC signal, which raises RMS and activity
# without representing audible dialogue. Flag a large DC bias conservatively.
MAX_ABSOLUTE_DC_OFFSET = 0.05


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
            mean_sample = sum(int(value) for value in samples) / len(samples)
            mean_square = sum(int(value) ** 2 for value in samples) / len(samples)
            rms = math.sqrt(mean_square) / 32768.0
            ac_rms = math.sqrt(max(0.0, mean_square - mean_sample ** 2)) / 32768.0
            dc_offset = mean_sample / 32768.0
            possible_dc_bias = abs(dc_offset) >= MAX_ABSOLUTE_DC_OFFSET
            peak = max(abs(int(value)) for value in samples) / 32768.0
            near_full_scale_fraction = sum(
                abs(int(value)) >= NEAR_FULL_SCALE_THRESHOLD * 32768
                for value in samples) / len(samples)
            possible_hard_clipping = (
                rms >= 0.75 and
                near_full_scale_fraction >= MAX_NEAR_FULL_SCALE_SAMPLE_FRACTION)
            # Measure occupancy in independent 20 ms PCM frames so a single
            # high-amplitude transient cannot masquerade as sustained audio.
            frame_size = SAMPLE_RATE * ACTIVE_FRAME_MS // 1000
            active_frames = 0
            total_frames = 0
            current_active_run = 0
            longest_active_run = 0
            for offset in range(0, len(samples), frame_size):
                frame = samples[offset:offset + frame_size]
                frame_mean = sum(int(v) for v in frame) / len(frame)
                frame_mean_square = sum(int(v) ** 2 for v in frame) / len(frame)
                frame_ac_rms = math.sqrt(max(
                    0.0, frame_mean_square - frame_mean ** 2)) / 32768.0
                is_active = frame_ac_rms >= ACTIVE_FRAME_RMS_THRESHOLD
                active_frames += is_active
                current_active_run = current_active_run + 1 if is_active else 0
                longest_active_run = max(longest_active_run, current_active_run)
                total_frames += 1
            active_fraction = active_frames / total_frames
            longest_active_run_ms = longest_active_run * ACTIVE_FRAME_MS
            sustained = (ac_rms >= AUDIBLE_RMS_THRESHOLD and
                         active_fraction >= MIN_ACTIVE_FRAME_FRACTION and
                         longest_active_run_ms >= MIN_LONGEST_ACTIVE_RUN_MS)
            windows_qc.append({
                "shot_index": index + 1,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "decoded_rms": round(rms, 6),
                "ac_rms_dc_removed": round(ac_rms, 6),
                "dc_offset_normalized": round(dc_offset, 6),
                "possible_dc_bias_detected": possible_dc_bias,
                "peak_normalized": round(peak, 6),
                "near_full_scale_sample_fraction": round(near_full_scale_fraction, 4),
                "possible_hard_clipping_detected": possible_hard_clipping,
                "audible_energy_detected": ac_rms >= AUDIBLE_RMS_THRESHOLD,
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
            "maximum_absolute_dc_offset": MAX_ABSOLUTE_DC_OFFSET,
            "activity_uses_dc_removed_ac_rms": True,
            "near_full_scale_threshold": NEAR_FULL_SCALE_THRESHOLD,
            "maximum_near_full_scale_sample_fraction": MAX_NEAR_FULL_SCALE_SAMPLE_FRACTION,
            "caption_windows": windows_qc,
            "all_caption_windows_have_audio_energy": all(
                item["audible_energy_detected"] for item in windows_qc),
            "all_caption_windows_have_sustained_audio": all(
                item["sustained_audio_detected"] for item in windows_qc),
            "all_caption_windows_clear_of_possible_hard_clipping": all(
                not item["possible_hard_clipping_detected"] for item in windows_qc),
            "all_caption_windows_clear_of_possible_dc_bias": all(
                not item["possible_dc_bias_detected"] for item in windows_qc),
            "hard_clipping_detection_is_conservative_not_proof": True,
            "dc_bias_detection_is_conservative_not_speech_proof": True,
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
