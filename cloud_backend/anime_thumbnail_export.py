"""Create a private, review-only 1280x720 still from a verified selected frame.

No title, typography, owner approval, rights clearance, publishing or upload.
Upscaling a 480x270 frame does not create professional high-resolution artwork.
"""
from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from cloud_backend.anime_thumbnail import HEIGHT, WIDTH
from cloud_backend.anime_thumbnail_selection import (
    AnimeThumbnailSelectionError, record_private_thumbnail_selection,
)


class AnimeThumbnailExportError(ValueError):
    """Invalid or altered private selection, video, contact sheet or preview."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_private_selected_thumbnail_preview(manifest: dict, video_mp4: bytes,
                                             contact_png: bytes,
                                             selection: dict) -> dict:
    """Reverify the complete contact sheet and selection before any export.

    The only input artwork is the already-encoded original MP4 frame. This
    deliberately does not draw a potentially broken Urdu/Devanagari title.
    """
    if type(selection) is not dict:
        raise AnimeThumbnailExportError("An existing private editorial selection is required.")
    shot = selection.get("selected_shot")
    note = selection.get("editor_note")
    if type(shot) is not int or type(note) is not str:
        raise AnimeThumbnailExportError("Invalid selected shot or editorial note.")
    try:
        expected = record_private_thumbnail_selection(
            manifest, video_mp4, contact_png,
            selected_shot=shot, note=note,
            inspected=selection.get("human_inspection_attested_not_independently_verified"))
    except AnimeThumbnailSelectionError:
        raise AnimeThumbnailExportError("Original media and selection could not be verified.") from None
    # No arbitrary extra approval fields or changed source digests are accepted.
    if selection != expected:
        raise AnimeThumbnailExportError("Private editorial selection record was modified.")
    try:
        with Image.open(BytesIO(contact_png)) as source:
            if (source.format != "PNG"
                    or source.size != (WIDTH * 3, HEIGHT + 30)
                    or getattr(source, "n_frames", 1) != 1):
                raise AnimeThumbnailExportError("Unexpected original contact sheet.")
            source.load()
            selected = source.convert("RGB").crop(
                ((shot - 1) * WIDTH, 30, shot * WIDTH, HEIGHT + 30))
        preview = selected.resize((1280, 720), Image.Resampling.LANCZOS)
        output = BytesIO()
        preview.save(output, format="PNG")
        png = output.getvalue()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        raise AnimeThumbnailExportError("Selected draft frame could not be exported.") from None
    if not 100 <= len(png) <= 6_000_000:
        raise AnimeThumbnailExportError("Exported preview exceeded private size limits.")
    return {
        "filename": "hoshi_selected_thumbnail_DRAFT.png",
        "png_bytes": png,
        "png_sha256": _sha(png),
        "source_manifest_sha256": selection["source_manifest_sha256"],
        "source_video_sha256": selection["source_video_sha256"],
        "source_contact_png_sha256": selection["source_contact_png_sha256"],
        "selected_shot": shot,
        "selected_frame_index": selection["selected_frame_index"],
        "selected_decoded_frame_rgb_sha256": selection["selected_decoded_frame_rgb_sha256"],
        "title_utf8_not_rendered": selection["title_utf8_not_rendered"],
        "source_frame_resolution": [WIDTH, HEIGHT],
        "preview_resolution": [1280, 720],
        "upscaled_from_low_resolution": True,
        "status": "private_upscaled_selected_still_not_final_thumbnail",
        "typography_added": False,
        "final_thumbnail_designed": False,
        "source_rights_independently_verified": False,
        "owner_approved": False,
        "release_authorized": False,
        "publication_permitted": False,
    }
