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

from PIL import Image, ImageDraw, ImageFont

from cloud_backend.anime_subtitle_preview import (
    AnimeSubtitlePreviewError, build_private_subtitle_contact_sheet,
    _srt_windows,
)
from cloud_backend.anime_thumbnail import AnimeThumbnailError, _verify_video


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
