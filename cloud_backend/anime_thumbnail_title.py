"""Private title typography for a *verified* Hoshi Anime Studio thumbnail preview.

A local operator supplies a font they are allowed to use. RAQM is mandatory
for Hindi/Urdu shaping; missing glyphs and visual quality still need human QC.
Never grants rights clearance, owner approval, publishing, or production release.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import unicodedata

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError, features

from cloud_backend.anime_thumbnail import _validate_title, AnimeThumbnailError


class AnimeThumbnailTitleError(ValueError):
    """Untrusted preview, title, font or unshaped draft."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _script_direction(title: str) -> tuple[str, str]:
    arabic = any(("\u0600" <= ch <= "\u08ff") or ("\ufb50" <= ch <= "\ufdff")
                 or ("\ufe70" <= ch <= "\ufeff") for ch in title)
    devanagari = any("\u0900" <= ch <= "\u097f" for ch in title)
    if arabic and devanagari:
        raise AnimeThumbnailTitleError("Use one title script per draft for reliable direction.")
    return ("rtl", "urdu_arabic") if arabic else (
        ("ltr", "hindi_devanagari") if devanagari else ("ltr", "roman_urdu_latin"))


def render_private_titled_thumbnail(preview: dict, font_bytes: bytes, *,
                                    font_rights_attested: bool) -> dict:
    """Render a *draft* title onto an already independently verified preview.

    Callers must first use build_private_selected_thumbnail_preview() with the
    original MP4, contact sheet and selection. This function verifies its
    immediate preview inputs, not the entire upstream media independently.
    """
    if (type(preview) is not dict
            or preview.get("status") != "private_upscaled_selected_still_not_final_thumbnail"
            or preview.get("preview_resolution") != [1280, 720]
            or preview.get("upscaled_from_low_resolution") is not True
            or preview.get("typography_added") is not False
            or preview.get("owner_approved") is not False
            or preview.get("release_authorized") is not False
            or preview.get("publication_permitted") is not False):
        raise AnimeThumbnailTitleError("An unapproved verified selected-frame preview is required.")
    png = preview.get("png_bytes")
    title = preview.get("title_utf8_not_rendered")
    if (type(png) is not bytes or not 100 <= len(png) <= 6_000_000
            or preview.get("png_sha256") != _sha(png)):
        raise AnimeThumbnailTitleError("Original selected-frame PNG integrity mismatch.")
    try:
        _validate_title(title)
    except AnimeThumbnailError:
        raise AnimeThumbnailTitleError("Unsafe or missing source-bound title.") from None
    if (len(title) > 80 or unicodedata.normalize("NFC", title) != title
            or any(unicodedata.category(c) in ("Cc", "Cs") for c in title)):
        raise AnimeThumbnailTitleError("Title is too long, unnormalized or unsafe.")
    direction, script = _script_direction(title)
    if (font_rights_attested is not True or type(font_bytes) is not bytes
            or not 1000 <= len(font_bytes) <= 8_000_000):
        raise AnimeThumbnailTitleError("Bounded operator-owned/licensed font required.")
    if not features.check("raqm"):
        raise AnimeThumbnailTitleError("Pillow libraqm complex-text shaping is required.")
    try:
        with Image.open(BytesIO(png)) as source:
            if (source.format != "PNG" or source.size != (1280, 720)
                    or getattr(source, "n_frames", 1) != 1):
                raise AnimeThumbnailTitleError("Unexpected selected preview dimensions or format.")
            source.load()
            canvas = source.convert("RGBA")
        font = None
        for size in range(88, 29, -2):
            candidate = ImageFont.truetype(BytesIO(font_bytes), size=size,
                                           layout_engine=ImageFont.Layout.RAQM)
            box = ImageDraw.Draw(canvas).textbbox(
                (0, 0), title, font=candidate, direction=direction, stroke_width=2)
            if 0 < box[2] - box[0] <= 1120 and 0 < box[3] - box[1] <= 124:
                font = candidate
                break
        if font is None:
            raise AnimeThumbnailTitleError("Title does not fit the safe design area.")
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rectangle((0, 540, 1279, 719), fill=(8, 13, 25, 215))
        draw.text((640, 630), title, font=font, anchor="mm", direction=direction,
                  fill=(255, 255, 255, 255), stroke_width=2,
                  stroke_fill=(4, 7, 14, 255))
        canvas = Image.alpha_composite(canvas, overlay).convert("RGB")
        output = BytesIO()
        canvas.save(output, format="PNG")
        rendered = output.getvalue()
    except (OSError, ValueError, TypeError, UnidentifiedImageError,
            Image.DecompressionBombError):
        raise AnimeThumbnailTitleError("Local complex-text font or image render failed.") from None
    if not 100 <= len(rendered) <= 7_000_000:
        raise AnimeThumbnailTitleError("Rendered title draft exceeded size limits.")
    return {
        "filename": "hoshi_selected_thumbnail_TITLED_PRIVATE_DRAFT.png",
        "png_bytes": rendered,
        "png_sha256": _sha(rendered),
        "source_preview_sha256": _sha(png),
        "source_video_sha256": preview["source_video_sha256"],
        "source_manifest_sha256": preview["source_manifest_sha256"],
        "source_contact_png_sha256": preview["source_contact_png_sha256"],
        "selected_shot": preview["selected_shot"],
        "title_utf8_rendered": title,
        "title_direction": direction,
        "title_script_hint": script,
        "font_sha256": _sha(font_bytes),
        "font_shaping_engine": "libraqm",
        "preview_resolution": [1280, 720],
        "upscaled_from_low_resolution": True,
        "typography_added": True,
        "glyph_coverage_independently_verified": False,
        "font_rights_attested_not_independently_verified": True,
        "source_rights_independently_verified": False,
        "manual_typography_and_art_review_required": True,
        "status": "private_titled_thumbnail_draft_not_final",
        "final_thumbnail_designed": False,
        "owner_approved": False,
        "release_authorized": False,
        "publication_permitted": False,
    }
