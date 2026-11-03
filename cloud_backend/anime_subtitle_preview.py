"""Offline, bounded SRT-on-decoded-frame contact sheet for private Anime Studio QC.

Displays *actual encoded MP4 frames* with shaped Hindi/Urdu/Roman Urdu SRT
captions for human readability review. It does not embed subtitles into the
video, recognize speech, verify rights, approve publishing or certify lip-sync.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unicodedata

from PIL import Image, ImageDraw, ImageFont, features

from cloud_backend.anime_subtitle_qc import (
    AnimeSubtitleQCError, validate_private_subtitles,
)
from cloud_backend.anime_thumbnail import _verify_video, AnimeThumbnailError
from cloud_backend.anime_thumbnail_title import (
    AnimeThumbnailTitleError, _require_title_font_cmap, _script_direction,
)


class AnimeSubtitlePreviewError(ValueError):
    """Invalid private media, subtitle provenance or shaped caption preview."""


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _srt_windows(subtitles: bytes) -> list[tuple[int, int, str]]:
    # Caller already validated exact three-block SRT and storyboard binding.
    blocks = subtitles.decode("utf-8").rstrip("\n").split("\n\n")
    windows = []
    for block in blocks:
        _, timing, caption = block.split("\n")
        start, end = timing.split(" --> ")
        def milliseconds(value: str) -> int:
            match = re.fullmatch(r"00:(\d\d):(\d\d),(\d{3})", value)
            if match is None:
                raise AnimeSubtitlePreviewError("Noncanonical private subtitle time.")
            return (int(match[1]) * 60 + int(match[2])) * 1000 + int(match[3])
        windows.append((milliseconds(start), milliseconds(end), caption))
    return windows


def build_private_subtitle_contact_sheet(manifest: dict, video: bytes,
                                         subtitles: bytes, font_bytes: bytes, *,
                                         font_rights_attested: bool) -> dict:
    """Render three cue-midpoint frames with real RAQM caption pixels.

    Operator-supplied font and source-media rights are only attested, not
    independently cleared. Output remains local and unapproved.
    """
    if (type(manifest) is not dict or type(video) is not bytes
            or not 100 <= len(video) <= 15_000_000
            or type(subtitles) is not bytes or not 1 <= len(subtitles) <= 20_000
            or type(font_bytes) is not bytes or not 1000 <= len(font_bytes) <= 8_000_000
            or font_rights_attested is not True):
        raise AnimeSubtitlePreviewError("Bounded local MP4/SRT and rights-attested font required.")
    if (manifest.get("stage") != "private_storyboard_animatic_only"
            or manifest.get("actual_mp4_rendered") is not True
            or manifest.get("owner_approved") is not False
            or manifest.get("published") is not False
            or manifest.get("uploaded") is not False
            or manifest.get("video_sha256") != _sha(video)
            or manifest.get("subtitles_sha256") != _sha(subtitles)):
        raise AnimeSubtitlePreviewError("Private media hashes or unapproved status mismatch.")
    try:
        subtitle_qc = validate_private_subtitles(manifest, subtitles)
    except AnimeSubtitleQCError:
        raise AnimeSubtitlePreviewError("SRT does not match its bound storyboard/cues.") from None
    if not features.check("raqm"):
        raise AnimeSubtitlePreviewError("Pillow libraqm shaping required for Urdu/Hindi.")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AnimeSubtitlePreviewError("Local FFmpeg and ffprobe required.")
    windows = _srt_windows(subtitles)
    if len(windows) != 3:
        raise AnimeSubtitlePreviewError("Exactly three captions required.")
    canvas = Image.new("RGB", (1440, 300), (10, 15, 25))
    draw = ImageDraw.Draw(canvas)
    samples = []
    try:
        with TemporaryDirectory(prefix="hoshi-subtitle-preview-") as directory:
            path = Path(directory) / "draft.mp4"
            path.write_bytes(video)
            media_qc = _verify_video(path, ffprobe)
            for shot, (start, end, caption) in enumerate(windows):
                if (not 1 <= len(caption) <= 180
                        or unicodedata.normalize("NFC", caption) != caption
                        or any(unicodedata.category(ch).startswith("C")
                               and ch not in ("\u200c", "\u200d") for ch in caption)):
                    raise AnimeSubtitlePreviewError("Unsafe or unnormalized caption.")
                _require_title_font_cmap(caption, font_bytes)
                direction, script = _script_direction(caption)
                # Sample the *actual SRT cue*, not a fixed 5s midpoint that
                # might fall outside an operator-supplied dialogue interval.
                frame_index = max(shot * 120, min(shot * 120 + 119,
                                  (start + end) * 12 // 2000))
                result = subprocess.run(
                    [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
                     "-i", str(path), "-vf", f"select=eq(n\\,{frame_index})",
                     "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                    capture_output=True, timeout=15, check=False)
                if result.returncode or not 100 <= len(result.stdout) <= 3_000_000:
                    raise AnimeSubtitlePreviewError("Exact encoded subtitle frame unavailable.")
                with Image.open(BytesIO(result.stdout)) as source:
                    if (source.format != "PNG" or source.size != (480, 270)
                            or getattr(source, "n_frames", 1) != 1):
                        raise AnimeSubtitlePreviewError("Unexpected decoded MP4 frame.")
                    frame = source.convert("RGB")
                    frame.load()
                left = shot * 480
                canvas.paste(frame, (left, 30))
                draw.rectangle((left + 8, 30 + 190, left + 472, 30 + 267),
                               fill=(6, 10, 19))
                anchor = (left + 240, 30 + 230)
                safe = (left + 20, 30 + 194, left + 460, 30 + 264)
                chosen = None
                for size in range(34, 13, -2):
                    font = ImageFont.truetype(BytesIO(font_bytes), size=size,
                                              layout_engine=ImageFont.Layout.RAQM)
                    bounds = draw.textbbox(anchor, caption, font=font,
                                           anchor="mm", direction=direction,
                                           stroke_width=1)
                    if (bounds[0] >= safe[0] and bounds[1] >= safe[1]
                            and bounds[2] <= safe[2] and bounds[3] <= safe[3]
                            and bounds[2] > bounds[0] and bounds[3] > bounds[1]):
                        chosen = (font, size, bounds)
                        break
                if chosen is None:
                    raise AnimeSubtitlePreviewError(
                        "Caption cannot fit the review-safe area; revise subtitle.")
                font, size, bounds = chosen
                ink = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
                ImageDraw.Draw(ink).text(
                    anchor, caption, font=font, anchor="mm",
                    direction=direction, fill=(255, 255, 255, 255),
                    stroke_width=1, stroke_fill=(0, 0, 0, 255))
                ink_box = ink.getchannel("A").getbbox()
                if (ink_box is None or ink_box[0] < safe[0]
                        or ink_box[1] < safe[1] or ink_box[2] > safe[2]
                        or ink_box[3] > safe[3]):
                    raise AnimeSubtitlePreviewError("Blank or clipped subtitle ink.")
                canvas.paste(ink, (0, 0), ink)
                draw.text((left + 9, 8),
                          f"SHOT {shot + 1} | FRAME {frame_index} | CUE {start}-{end}ms",
                          fill=(240, 240, 240))
                samples.append({
                    "shot_index": shot + 1, "cue_start_ms": start,
                    "cue_end_ms": end, "decoded_frame_index": frame_index,
                    "decoded_frame_rgb_sha256": _sha(frame.tobytes()),
                    "caption_utf8": caption, "caption_direction": direction,
                    "caption_script_hint": script, "font_size_px": size,
                    "text_layout_bbox_px": list(bounds),
                    "text_ink_bbox_px": list(ink_box),
                })
        output = BytesIO()
        canvas.save(output, "PNG")
        png = output.getvalue()
    except AnimeSubtitlePreviewError:
        raise
    except (AnimeThumbnailError, AnimeThumbnailTitleError, OSError,
            subprocess.TimeoutExpired, ValueError, TypeError):
        raise AnimeSubtitlePreviewError("Offline subtitle preview validation failed.") from None
    if not 100 <= len(png) <= 6_000_000:
        raise AnimeSubtitlePreviewError("Subtitle contact sheet exceeds size limit.")
    return {
        "filename": "hoshi_subtitle_review_PRIVATE_DRAFT.png",
        "png_bytes": png, "png_sha256": _sha(png),
        "source_video_sha256": _sha(video),
        "source_subtitles_sha256": _sha(subtitles),
        "source_font_sha256": _sha(font_bytes),
        "media_qc": media_qc, "subtitle_qc": subtitle_qc,
        "samples": samples, "resolution": [1440, 300],
        "status": "actual_mp4_frames_with_shaped_srt_private_review_only",
        "font_rights_attested_not_independently_verified": True,
        "subtitle_pixels_rendered_in_review_png_not_video": True,
        "subtitles_embedded_in_video": False,
        "spoken_words_independently_verified": False,
        "visual_readability_human_review_required": True,
        "source_rights_independently_verified": False,
        "owner_approved": False, "release_authorized": False,
        "publication_permitted": False,
    }
