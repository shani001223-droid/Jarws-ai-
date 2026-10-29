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
from fontTools.ttLib import TTFont, TTLibError

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



def _require_title_font_cmap(title: str, font_bytes: bytes) -> None:
    """Fail closed on missing Unicode characters before shaping a private draft.

    A Unicode cmap proves that the selected font *maps* each required codepoint,
    not that its GSUB/GPOS shaping, visual quality or licensing is acceptable.
    Joiners U+200C/U+200D are formatting controls, not visible glyphs.
    """
    if font_bytes[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
        raise AnimeThumbnailTitleError("Only bounded OpenType/TrueType fonts are supported.")
    font = None
    try:
        font = TTFont(BytesIO(font_bytes), lazy=True)
        cmap = font.getBestCmap()
        if not cmap:
            raise AnimeThumbnailTitleError("Font lacks a Unicode character map.")
        required = {ord(char) for char in title if char not in ("\u200c", "\u200d")}
        if any(not cmap.get(codepoint) or cmap[codepoint] == ".notdef"
               for codepoint in required):
            raise AnimeThumbnailTitleError(
                "Font lacks required title characters; supply a licensed script-capable font.")
    except AnimeThumbnailTitleError:
        raise
    except (TTLibError, OSError, ValueError, TypeError, AssertionError):
        raise AnimeThumbnailTitleError("Invalid or unsupported local title font.") from None
    finally:
        if font is not None:
            font.close()


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
    _require_title_font_cmap(title, font_bytes)
    try:
        with Image.open(BytesIO(png)) as source:
            if (source.format != "PNG" or source.size != (1280, 720)
                    or getattr(source, "n_frames", 1) != 1):
                raise AnimeThumbnailTitleError("Unexpected selected preview dimensions or format.")
            source.load()
            canvas = source.convert("RGBA")
        # Measure at the exact final RAQM anchor, including the stroke. Measuring
        # at (0, 0) with Pillow's default anchor can miss real clipping for RTL
        # scripts with nontrivial bearings and ascenders/descenders.
        safe_area = (80, 554, 1200, 705)  # inset inside the dark lower band
        anchor = (640, 630)
        font = None
        layout_box = None
        selected_font_size = None
        for size in range(88, 29, -2):
            candidate = ImageFont.truetype(BytesIO(font_bytes), size=size,
                                           layout_engine=ImageFont.Layout.RAQM)
            box = ImageDraw.Draw(canvas).textbbox(
                anchor, title, font=candidate, anchor="mm",
                direction=direction, stroke_width=2)
            if (box[0] >= safe_area[0] and box[1] >= safe_area[1]
                    and box[2] <= safe_area[2] and box[3] <= safe_area[3]
                    and box[2] > box[0] and box[3] > box[1]):
                font, layout_box, selected_font_size = candidate, box, size
                break
        if font is None:
            raise AnimeThumbnailTitleError("Title does not fit the safe design area.")
        # Draw text separately from the opaque title band so an empty/blank
        # glyph outline cannot be mistaken for successfully rendered lettering.
        text_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(text_layer).text(
            anchor, title, font=font, anchor="mm", direction=direction,
            fill=(255, 255, 255, 255), stroke_width=2,
            stroke_fill=(4, 7, 14, 255))
        ink_box = text_layer.getchannel("A").getbbox()
        if (ink_box is None or ink_box[0] < safe_area[0]
                or ink_box[1] < safe_area[1] or ink_box[2] > safe_area[2]
                or ink_box[3] > safe_area[3]):
            raise AnimeThumbnailTitleError("Title ink is blank or outside safe design area.")
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(overlay).rectangle(
            (0, 540, 1279, 719), fill=(8, 13, 25, 215))
        canvas = Image.alpha_composite(
            Image.alpha_composite(canvas, overlay), text_layer).convert("RGB")
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
        "title_font_size_px": selected_font_size,
        "title_layout_bbox_px": list(layout_box),
        "title_ink_bbox_px": list(ink_box),
        "title_safe_area_px": list(safe_area),
        "title_ink_presence_and_safe_bounds_checked": True,
        "preview_resolution": [1280, 720],
        "upscaled_from_low_resolution": True,
        "typography_added": True,
        "font_unicode_cmap_coverage_verified": True,
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
