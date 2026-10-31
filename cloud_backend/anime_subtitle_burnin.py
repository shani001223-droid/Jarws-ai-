"""Create a real, *private* H.264 captioned pilot from a validated SRT.

This is an offline operator preview, not a published episode or speech/lip-sync
verification. Caption text is shaped by Pillow/libraqm into transparent PNG
overlays before FFmpeg; no FFmpeg drawtext fallback or shell interpolation.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import wave

from PIL import Image, ImageDraw, ImageFont

from cloud_backend.anime_subtitle_preview import (
    AnimeSubtitlePreviewError, build_private_subtitle_contact_sheet,
    _srt_windows,
)
from cloud_backend.anime_thumbnail import AnimeThumbnailError, _verify_video
from cloud_backend.anime_audio_waveform import build_encoded_audio_waveform


class AnimeSubtitleBurninError(ValueError):
    """Unsafe or unverifiable private subtitle burn-in."""


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _encoded_rgb_frame(ffmpeg: str, path: Path, index: int) -> Image.Image:
    """Decode one *actual encoded* frame; never trust a render-time PNG."""
    if type(index) is not int or not 0 <= index < 360:
        raise AnimeSubtitleBurninError("Invalid private comparison frame index.")
    process = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
         "-i", str(path), "-vf", f"select=eq(n\\,{index})",
         "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, timeout=15, check=False)
    if process.returncode or not 100 <= len(process.stdout) <= 3_000_000:
        raise AnimeSubtitleBurninError("Encoded comparison frame unavailable.")
    with Image.open(BytesIO(process.stdout)) as decoded:
        if (decoded.format != "PNG" or decoded.size != (480, 270)
                or getattr(decoded, "n_frames", 1) != 1):
            raise AnimeSubtitleBurninError("Invalid encoded comparison frame.")
        frame = decoded.convert("RGB")
        frame.load()
    return frame


def _encoded_comparison_evidence(ffmpeg: str, source: Path, output: Path,
                                 samples: list[dict]) -> tuple[bytes, list[dict]]:
    """Create a private original-vs-reencoded contact sheet for human review.

    Visual evidence is decoded from both real MP4 files. It is NOT automated
    proof of correct words, cue gaps, professional quality or owner approval.
    """
    if len(samples) != 3:
        raise AnimeSubtitleBurninError("Three verified caption samples required.")
    canvas = Image.new("RGB", (960, 900), (9, 13, 23))
    draw = ImageDraw.Draw(canvas)
    comparisons = []
    for shot, sample in enumerate(samples):
        frame_index = sample["decoded_frame_index"]
        original = _encoded_rgb_frame(ffmpeg, source, frame_index)
        captioned = _encoded_rgb_frame(ffmpeg, output, frame_index)
        original_hash = _sha(original.tobytes())
        if original_hash != sample["decoded_frame_rgb_sha256"]:
            raise AnimeSubtitleBurninError("Original frame differs from SRT review.")
        top = shot * 300
        canvas.paste(original, (0, top + 30))
        canvas.paste(captioned, (480, top + 30))
        draw.text((12, top + 9), f"SHOT {shot + 1} FRAME {frame_index} | ORIGINAL",
                  fill=(240, 240, 240))
        draw.text((492, top + 9), "CAPTIONED RE-ENCODED MP4",
                  fill=(240, 240, 240))
        comparisons.append({
            "shot_index": shot + 1,
            "decoded_frame_index": frame_index,
            "cue_start_ms": sample["cue_start_ms"],
            "cue_end_ms": sample["cue_end_ms"],
            "original_decoded_rgb_sha256": original_hash,
            "captioned_decoded_rgb_sha256": _sha(captioned.tobytes()),
        })
    buffer = BytesIO()
    canvas.save(buffer, "PNG")
    evidence = buffer.getvalue()
    if not 100 <= len(evidence) <= 8_000_000:
        raise AnimeSubtitleBurninError("Private comparison PNG exceeds size limit.")
    return evidence, comparisons


def _encoded_cue_audio_evidence(
    ffmpeg: str, output: Path, windows: list[tuple[int, int, str]],
    audio_codec: str,
) -> tuple[list[dict], list[dict]]:
    """Export bounded WAV listening clips from the *encoded* MP4 AAC track.

    Include 250 ms on either side of each caption, clipped to the 30s pilot.
    This is a human review handoff, never ASR, speech or lip-sync verification.
    A silent MP4 must not be given fabricated audio evidence.
    """
    if audio_codec != "aac":
        return [], []
    if len(windows) != 3:
        raise AnimeSubtitleBurninError("Three validated audio cues required.")
    clips, samples = [], []
    for index, (start, end, _) in enumerate(windows):
        first, last = max(0, start - 250), min(30000, end + 250)
        first_sample, last_sample = first * 16, last * 16
        if last_sample <= first_sample:
            raise AnimeSubtitleBurninError("Invalid private audio review interval.")
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
             "-i", str(output), "-map", "0:a:0", "-vn",
             "-af", ("aresample=16000,atrim=start_sample="
                     f"{first_sample}:end_sample={last_sample},"
                     "asetpts=PTS-STARTPTS"),
             "-ac", "1", "-c:a", "pcm_s16le", "-f", "s16le", "-"],
            capture_output=True, timeout=25, check=False)
        expected_bytes = (last_sample - first_sample) * 2
        if (result.returncode or len(result.stdout) % 2
                or not max(1, expected_bytes - 3200) <= len(result.stdout)
                <= expected_bytes + 640):
            raise AnimeSubtitleBurninError("Encoded AAC cue listening clip unavailable.")
        buffer = BytesIO()
        with wave.open(buffer, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(16000)
            writer.writeframes(result.stdout)
        wav = buffer.getvalue()
        if not 44 <= len(wav) <= 750_000:
            raise AnimeSubtitleBurninError("Private WAV review clip exceeds limit.")
        filename = f"hoshi_cue_{index + 1}_PRIVATE_REVIEW.wav"
        clips.append({"filename": filename, "wav_bytes": wav})
        samples.append({
            "shot_index": index + 1, "filename": filename,
            "cue_start_ms": start, "cue_end_ms": end,
            "excerpt_start_ms": first, "excerpt_end_ms_requested": last,
            "decoded_pcm_sample_count": len(result.stdout) // 2,
            "sample_rate_hz": 16000, "channels": 1,
            "sample_width_bytes": 2, "wav_sha256": _sha(wav),
            "decoded_from_actual_captioned_mp4_aac": True,
            "human_listening_review_required": True,
            "spoken_words_independently_verified": False,
            "phoneme_sync_verified": False,
        })
    return clips, samples


def render_private_subtitled_pilot(manifest: dict, video: bytes,
                                   subtitles: bytes, font_bytes: bytes, *,
                                   font_rights_attested: bool) -> dict:
    """Render cue-exact, shaped caption overlays into a new 30-second MP4.

    All input media, source SRT and font are checked by the existing independent
    actual-frame contact-sheet validator. Audio is stream-copied if present.
    Nothing changes the original video or manifest and no approval is granted.
    """
    try:
        review = build_private_subtitle_contact_sheet(
            manifest, video, subtitles, font_bytes,
            font_rights_attested=font_rights_attested)
    except AnimeSubtitlePreviewError as exc:
        raise AnimeSubtitleBurninError(str(exc)) from None
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AnimeSubtitleBurninError("Local FFmpeg and ffprobe required.")
    windows = _srt_windows(subtitles)
    if len(windows) != 3:
        raise AnimeSubtitleBurninError("Exactly three bound subtitle cues required.")

    try:
        with TemporaryDirectory(prefix="hoshi-private-subtitle-burnin-") as directory:
            root = Path(directory)
            source = root / "original.mp4"
            output = root / "captioned.mp4"
            source.write_bytes(video)
            command = [ffmpeg, "-hide_banner", "-loglevel", "error",
                       "-nostdin", "-i", str(source)]
            overlays = []
            for index, (start, end, caption) in enumerate(windows):
                sample = review["samples"][index]
                if (sample["caption_utf8"] != caption
                        or sample["cue_start_ms"] != start
                        or sample["cue_end_ms"] != end):
                    raise AnimeSubtitleBurninError("Caption review provenance mismatch.")
                # Use the exact font, size, anchor and direction already checked
                # by the actual decoded-frame readability validator.
                overlay = Image.new("RGBA", (480, 270), (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)
                draw.rectangle((8, 220, 472, 267), fill=(6, 10, 19, 190))
                font = ImageFont.truetype(
                    BytesIO(font_bytes), size=sample["font_size_px"],
                    layout_engine=ImageFont.Layout.RAQM)
                draw.text((240, 230), caption, font=font, anchor="mm",
                          direction=sample["caption_direction"],
                          fill=(255, 255, 255, 255),
                          stroke_width=1, stroke_fill=(0, 0, 0, 255))
                path = root / f"caption_{index}.png"
                overlay.save(path, "PNG")
                overlays.append(path)
                command.extend(["-loop", "1", "-framerate", "12", "-i", str(path)])

            filters = []
            previous = "[0:v]"
            for index, (start, end, _) in enumerate(windows):
                # Frame-index gating avoids floating-point time boundary drift.
                # SRT end is exclusive; frame center must be inside the cue.
                active = [n for n in range(360)
                          if start * 12 <= (2 * n + 1) * 500
                          and (2 * n + 1) * 500 < end * 12]
                if not active:
                    raise AnimeSubtitleBurninError("Cue has no renderable video frame.")
                # Validated cues are contiguous within their own 10-second shot.
                if active != list(range(active[0], active[-1] + 1)):
                    raise AnimeSubtitleBurninError("Noncontiguous subtitle frames.")
                target = f"[cap{index}]"
                filters.append(
                    f"{previous}[{index + 1}:v]overlay=x=0:y=0:"
                    f"enable='between(n,{active[0]},{active[-1]})':"
                    f"format=auto{target}")
                previous = target
            filters.append(f"{previous}format=yuv420p[v]")
            command.extend(["-filter_complex", ";".join(filters),
                            "-map", "[v]"])
            if review["media_qc"]["audio_codec"] == "aac":
                command.extend(["-map", "0:a:0", "-c:a", "copy"])
            command.extend(["-c:v", "libx264", "-preset", "ultrafast",
                            "-crf", "22", "-pix_fmt", "yuv420p",
                            "-r", "12", "-frames:v", "360",
                            "-t", "30", "-threads", "2",
                            "-movflags", "+faststart", "-y", str(output)])
            process = subprocess.run(
                command, capture_output=True, timeout=120, check=False)
            if process.returncode or not output.is_file():
                raise AnimeSubtitleBurninError("Offline captioned MP4 encoding failed.")
            if not 100 <= output.stat().st_size <= 15_000_000:
                raise AnimeSubtitleBurninError("Captioned MP4 exceeds private size limit.")
            encoded = output.read_bytes()
            media_qc = _verify_video(output, ffprobe)
            if media_qc["audio_codec"] != review["media_qc"]["audio_codec"]:
                raise AnimeSubtitleBurninError("Original AAC stream not preserved.")
            comparison_png, comparisons = _encoded_comparison_evidence(
                ffmpeg, source, output, review["samples"])
            audio_review_wavs, audio_review_samples = _encoded_cue_audio_evidence(
                ffmpeg, output, windows, media_qc["audio_codec"])
            waveform = build_encoded_audio_waveform(
                audio_review_wavs, audio_review_samples)
    except AnimeSubtitleBurninError:
        raise
    except (OSError, subprocess.TimeoutExpired, AnimeThumbnailError, ValueError,
            TypeError):
        raise AnimeSubtitleBurninError("Private caption burn-in failed validation.") from None

    return {
        "filename": "hoshi_anime_subtitled_PRIVATE_DRAFT.mp4",
        "video_mp4": encoded, "video_sha256": _sha(encoded),
        "visual_evidence_png": comparison_png,
        "visual_evidence_sha256": _sha(comparison_png),
        "visual_evidence_filename": "hoshi_subtitle_encoded_comparison_PRIVATE.png",
        "visual_evidence_resolution": [960, 900],
        "visual_evidence_samples": comparisons,
        "visual_evidence_decoded_from_both_mp4s": True,
        "visual_evidence_human_review_required": True,
        "audio_review_wavs": audio_review_wavs,
        "audio_waveform_png": waveform["png_bytes"],
        "audio_waveform_filename": (
            "hoshi_encoded_aac_waveform_PRIVATE.png"
            if waveform["png_bytes"] is not None else None),
        "audio_waveform_sha256": waveform.get("png_sha256"),
        "audio_waveform_resolution": waveform.get("resolution"),
        "audio_waveform_samples": waveform["samples"],
        "audio_waveform_status": waveform["status"],
        "audio_waveform_human_review_required": True,
        "audio_review_samples": audio_review_samples,
        "audio_review_decoded_from_actual_encoded_aac": bool(audio_review_samples),
        "audio_review_human_listening_required": True,
        "caption_ink_independently_machine_verified": False,
        "source_video_sha256": _sha(video),
        "source_subtitles_sha256": _sha(subtitles),
        "source_font_sha256": _sha(font_bytes),
        "media_qc": media_qc,
        "subtitle_qc": review["subtitle_qc"],
        "cue_windows_ms": [[start, end] for start, end, _ in windows],
        "subtitle_frame_gating": "12fps_center_in_half_open_srt_cue",
        "status": "actual_shaped_srt_burned_into_private_mp4_unapproved",
        "subtitles_embedded_in_video": True,
        "spoken_words_independently_verified": False,
        "audio_sync_independently_verified": False,
        "font_rights_attested_not_independently_verified": True,
        "source_rights_independently_verified": False,
        "human_readability_review_required": True,
        "owner_approved": False, "release_authorized": False,
        "publication_permitted": False,
    }
