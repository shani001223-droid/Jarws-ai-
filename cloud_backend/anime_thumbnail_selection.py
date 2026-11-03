"""Private, create-only selection of an *existing* decoded anime thumbnail frame.

A selection is an editorial preference, not a final designed thumbnail,
owner approval, asset-rights verification, upload, or release authorization.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, UnidentifiedImageError

from cloud_backend.anime_thumbnail import (
    FRAME_INDICES, HEIGHT, MAX_VIDEO_BYTES, WIDTH, _verify_video,
    AnimeThumbnailError,
)


class AnimeThumbnailSelectionError(ValueError):
    """Tampered candidate evidence or invalid private editorial selection."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_private_thumbnail_selection(manifest: dict, video_mp4: bytes,
                                       contact_png: bytes, *,
                                       selected_shot: int, note: str,
                                       inspected: bool) -> dict:
    """Re-decode every candidate from the actual MP4 before recording a choice."""
    if (type(manifest) is not dict or type(video_mp4) is not bytes
            or not 100 <= len(video_mp4) <= MAX_VIDEO_BYTES
            or type(contact_png) is not bytes
            or not 100 <= len(contact_png) <= 3_000_000
            or type(selected_shot) is not int or selected_shot not in (1, 2, 3)
            or inspected is not True or type(note) is not str
            or not 8 <= len(note.strip()) <= 500
            or any(ord(c) < 32 or c in "\u202e\u202d\u2066\u2067\u2068\u2069"
                   for c in note)):
        raise AnimeThumbnailSelectionError("Bounded media and explicit inspected shot choice/note required.")
    candidates = manifest.get("thumbnail_candidates")
    if (manifest.get("stage") != "private_storyboard_animatic_only"
            or manifest.get("actual_mp4_rendered") is not True
            or manifest.get("owner_approved") is not False
            or manifest.get("published") is not False
            or manifest.get("uploaded") is not False
            or manifest.get("video_sha256") != _sha(video_mp4)
            or type(candidates) is not dict
            or candidates.get("source_video_sha256") != _sha(video_mp4)
            or candidates.get("png_sha256") != _sha(contact_png)
            or candidates.get("status") != "three_actual_decoded_frame_candidates_not_final_thumbnail"
            or candidates.get("candidate_selected") is not False
            or candidates.get("owner_approved") is not False
            or candidates.get("publication_permitted") is not False
            or candidates.get("typography_added") is not False
            or candidates.get("manual_design_review_required") is not True
            or candidates.get("resolution_per_candidate") != [WIDTH, HEIGHT]):
        raise AnimeThumbnailSelectionError("Draft, contact sheet or unapproved provenance mismatch.")
    entries = candidates.get("candidate_frames")
    if (type(entries) is not list or len(entries) != 3
            or any(type(e) is not dict
                   or type(e.get("shot_index")) is not int
                   or e["shot_index"] != i
                   or type(e.get("frame_index")) is not int
                   or e["frame_index"] != FRAME_INDICES[i - 1]
                   or type(e.get("decoded_frame_rgb_sha256")) is not str
                   or len(e["decoded_frame_rgb_sha256"]) != 64
                   for i, e in enumerate(entries, 1))):
        raise AnimeThumbnailSelectionError("Exact three-frame provenance required.")
    try:
        with Image.open(BytesIO(contact_png)) as source:
            if (source.format != "PNG"
                    or source.size != (WIDTH * 3, HEIGHT + 30)
                    or getattr(source, "n_frames", 1) != 1):
                raise AnimeThumbnailSelectionError("Unexpected contact sheet.")
            sheet = source.convert("RGB")
            sheet.load()
        ffprobe, ffmpeg = shutil.which("ffprobe"), shutil.which("ffmpeg")
        if not ffprobe or not ffmpeg:
            raise AnimeThumbnailSelectionError("Local offline FFmpeg/ffprobe required.")
        expected_sheet = Image.new("RGB", (WIDTH * 3, HEIGHT + 30), (12, 15, 24))
        expected_draw = ImageDraw.Draw(expected_sheet)
        with TemporaryDirectory(prefix="hoshi-thumbnail-select-") as tmp:
            path = Path(tmp) / "draft.mp4"
            path.write_bytes(video_mp4)
            media = _verify_video(path, ffprobe)
            if candidates.get("media_qc") != media:
                raise AnimeThumbnailSelectionError("Candidate media metadata differs from actual MP4.")
            for i, entry in enumerate(entries):
                result = subprocess.run(
                    [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
                     "-i", str(path), "-vf",
                     f"select=eq(n\\,{FRAME_INDICES[i]})", "-frames:v", "1",
                     "-f", "image2pipe", "-vcodec", "png", "-"],
                    capture_output=True, timeout=15, check=False)
                if result.returncode or not 100 <= len(result.stdout) <= 3_000_000:
                    raise AnimeThumbnailSelectionError("Candidate frame cannot be independently decoded.")
                with Image.open(BytesIO(result.stdout)) as image:
                    if image.format != "PNG" or image.size != (WIDTH, HEIGHT):
                        raise AnimeThumbnailSelectionError("Unexpected decoded frame.")
                    frame = image.convert("RGB")
                    frame.load()
                expected = _sha(frame.tobytes())
                expected_sheet.paste(frame, (i * WIDTH, 30))
                expected_draw.text((i * WIDTH + 10, 9),
                                   f"SHOT {i + 1} | frame {FRAME_INDICES[i]}",
                                   fill=(240, 240, 240))
                if entry["decoded_frame_rgb_sha256"] != expected:
                    raise AnimeThumbnailSelectionError("Frame digest differs from actual decoded video.")
            if sheet.tobytes() != expected_sheet.tobytes():
                raise AnimeThumbnailSelectionError("Contact pixels or shot labels differ from actual decoded video.")
    except (OSError, subprocess.TimeoutExpired, AnimeThumbnailError,
            UnidentifiedImageError, SyntaxError, ValueError) as exc:
        if isinstance(exc, AnimeThumbnailSelectionError):
            raise
        raise AnimeThumbnailSelectionError("Actual thumbnail evidence could not be verified.") from None
    try:
        manifest_bytes = json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise AnimeThumbnailSelectionError("Invalid bounded draft manifest.") from None
    return {
        "schema_version": 1,
        "scope": "private_editorial_candidate_selection_not_release",
        "selected_shot": selected_shot,
        "selected_frame_index": FRAME_INDICES[selected_shot - 1],
        "selected_decoded_frame_rgb_sha256":
            entries[selected_shot - 1]["decoded_frame_rgb_sha256"],
        "human_inspection_attested_not_independently_verified": True,
        "editor_note": note.strip(),
        "source_manifest_sha256": _sha(manifest_bytes),
        "source_video_sha256": _sha(video_mp4),
        "source_contact_png_sha256": _sha(contact_png),
        "all_three_candidate_frames_independently_verified": True,
        "title_utf8_not_rendered": candidates.get("title_utf8_not_rendered"),
        "final_thumbnail_designed": False,
        "typography_verified": False,
        "source_rights_independently_verified": False,
        "owner_approved": False,
        "release_authorized": False,
        "publication_permitted": False,
    }
