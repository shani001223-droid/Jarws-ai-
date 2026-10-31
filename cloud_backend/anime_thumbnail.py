"""Offline, original-frame thumbnail candidate contact sheet for Hoshi Anime Studio.

This is a private *draft selection aid*, not a finished promotional thumbnail.
It decodes three actual MP4 frames without external services or uploads.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import unicodedata
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, UnidentifiedImageError


class AnimeThumbnailError(ValueError):
    """Invalid media, title, rights attestation or local decoder output."""


WIDTH, HEIGHT, FPS = 480, 270, 12
FRAME_INDICES = (60, 180, 300)
MAX_VIDEO_BYTES = 15_000_000
MAX_FRAME_BYTES = 3_000_000
# Reject escape-like text and direction/line controls that can mislead a human
# reviewing title metadata. ZWNJ/ZWJ are retained for Urdu/Hindi shaping.
FORBIDDEN_TITLE_CHARS = "<>\\\u202e\u202d\u2066\u2067\u2068\u2069"
_ALLOWED_JOINERS = {"\u200c", "\u200d"}


def _validate_title(title: str) -> None:
    if (type(title) is not str or not 1 <= len(title) <= 120
            or title != title.strip()
            or unicodedata.normalize("NFC", title) != title
            or any(ch in FORBIDDEN_TITLE_CHARS
                   or (unicodedata.category(ch).startswith("C")
                       and ch not in _ALLOWED_JOINERS)
                   or unicodedata.category(ch) in ("Zl", "Zp")
                   for ch in title)):
        raise AnimeThumbnailError("Safe nonempty Hindi/Urdu/Roman Urdu title required.")


def _verify_video(path: Path, ffprobe: str) -> dict:
    """Count decoded frames; allow silent draft or one AAC audio stream."""
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-count_frames", "-show_entries",
             "stream=codec_type,codec_name,width,height,avg_frame_rate,nb_read_frames:"
             "format=duration,format_name", "-of", "json", str(path)],
            capture_output=True, timeout=25, check=False)
        if result.returncode or not 1 <= len(result.stdout) <= 16000:
            raise AnimeThumbnailError("Unable to probe actual private MP4.")
        info = json.loads(result.stdout)
        streams = info["streams"]
        video = [s for s in streams if s.get("codec_type") == "video"]
        audio = [s for s in streams if s.get("codec_type") == "audio"]
        duration = float(info["format"]["duration"])
        if (len(streams) not in (1, 2) or len(video) != 1
                or len(audio) != len(streams) - 1
                or video[0].get("codec_name") != "h264"
                or (video[0].get("width"), video[0].get("height")) != (WIDTH, HEIGHT)
                or video[0].get("avg_frame_rate") != "12/1"
                or video[0].get("nb_read_frames") != "360"
                or (audio and audio[0].get("codec_name") != "aac")
                or "mp4" not in info["format"].get("format_name", "")
                or not 29.8 <= duration <= 30.3):
            raise AnimeThumbnailError("Wrong MP4 streams, duration or decoded frames.")
        return {"video_codec": "h264", "audio_codec": "aac" if audio else None,
                "frame_count": 360, "frame_rate": FPS,
                "duration_seconds": round(duration, 3)}
    except (OSError, subprocess.TimeoutExpired, KeyError, ValueError, TypeError,
            IndexError, AttributeError):
        raise AnimeThumbnailError("Actual MP4 probe failed.") from None


def build_private_thumbnail_candidates(video_mp4: bytes, *, title: str,
                                       rights_attested: bool,
                                       ffmpeg_binary: str | None = None,
                                       ffprobe_binary: str | None = None) -> dict:
    """Return a SHA-bound three-frame PNG contact sheet for manual selection.

    Title is kept in UTF-8 metadata: drawing it with a fallback Latin font
    would silently corrupt Urdu/Devanagari shaping. A human designer must add
    proper typography and approve a release-quality thumbnail later.
    """
    _validate_title(title)
    if rights_attested is not True:
        raise AnimeThumbnailError("Original video/frame rights must be attested.")
    if type(video_mp4) is not bytes or not 100 <= len(video_mp4) <= MAX_VIDEO_BYTES:
        raise AnimeThumbnailError("Bounded original MP4 bytes required.")
    ffmpeg = ffmpeg_binary or shutil.which("ffmpeg")
    ffprobe = ffprobe_binary or shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AnimeThumbnailError("Local FFmpeg and ffprobe required.")
    sheet = Image.new("RGB", (WIDTH * 3, HEIGHT + 30), (12, 15, 24))
    draw = ImageDraw.Draw(sheet)
    frames = []
    try:
        with TemporaryDirectory(prefix="hoshi-thumbnail-") as directory:
            path = Path(directory) / "draft.mp4"
            path.write_bytes(video_mp4)
            media = _verify_video(path, ffprobe)
            for shot, frame_index in enumerate(FRAME_INDICES, 1):
                result = subprocess.run(
                    [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
                     "-i", str(path), "-vf", f"select=eq(n\\,{frame_index})",
                     "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                    capture_output=True, timeout=15, check=False)
                if result.returncode or not 100 <= len(result.stdout) <= MAX_FRAME_BYTES:
                    raise AnimeThumbnailError("Exact encoded candidate frame unavailable.")
                with Image.open(BytesIO(result.stdout)) as source:
                    if (source.format != "PNG" or source.size != (WIDTH, HEIGHT)
                            or getattr(source, "n_frames", 1) != 1):
                        raise AnimeThumbnailError("Unexpected candidate frame format.")
                    frame = source.convert("RGB")
                    frame.load()
                sheet.paste(frame, ((shot - 1) * WIDTH, 30))
                draw.text(((shot - 1) * WIDTH + 10, 9),
                          f"SHOT {shot} | frame {frame_index}", fill=(240, 240, 240))
                frames.append({"shot_index": shot, "frame_index": frame_index,
                               "decoded_frame_rgb_sha256":
                               hashlib.sha256(frame.tobytes()).hexdigest()})
        out = BytesIO()
        sheet.save(out, format="PNG")
        png = out.getvalue()
        return {
            "filename": "hoshi_thumbnail_candidates_DRAFT.png",
            "png_bytes": png,
            "png_sha256": hashlib.sha256(png).hexdigest(),
            "source_video_sha256": hashlib.sha256(video_mp4).hexdigest(),
            "title_utf8_not_rendered": title,
            "candidate_frames": frames,
            "media_qc": media,
            "status": "three_actual_decoded_frame_candidates_not_final_thumbnail",
            "resolution_per_candidate": [WIDTH, HEIGHT],
            "typography_added": False,
            "candidate_selected": False,
            "manual_design_review_required": True,
            "owner_approved": False,
            "publication_permitted": False,
        }
    except (OSError, subprocess.TimeoutExpired, ValueError, UnidentifiedImageError):
        raise AnimeThumbnailError("Could not create bounded offline thumbnail candidates.") from None
