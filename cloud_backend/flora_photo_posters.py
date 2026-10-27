"""Task 45 foundation: offline Flora poster previews from caller-supplied photo bytes.

No HTTP upload, filesystem write, social posting, or photo ownership claim.
A preview remains a DRAFT even when its caller attests rights and price review.
"""
from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

try:
    from .ad_studio import _font
    from .flora_catalog import FloraCatalogError, catalogue_snapshot, inspect_owner_photo
except ImportError:  # direct Uvicorn import from cloud_backend/
    from ad_studio import _font
    from flora_catalog import FloraCatalogError, catalogue_snapshot, inspect_owner_photo


class FloraPosterError(ValueError):
    """An input or poster failed bounded offline validation."""


_SIZES = {"feed": (1080, 1350), "story": (1080, 1920)}
_MAX_OUTPUT_BYTES = 10_000_000


def render_flora_photo_preview(product_id: str, photo_bytes: bytes, mime_type: str,
                               placement: str = "feed", *,
                               rights_attested: bool = False,
                               price_reviewed: bool = False) -> dict:
    """Return a real PNG draft, metadata and an immutable source digest in memory.

    Attestations are caller claims, not independent rights/price verification.
    No amount of caller input makes this output approved or publishable.
    Synthetic test photos are not evidence of genuine Flora product photos.
    """
    if type(product_id) is not str or product_id not in ("gold_kit", "shampoo"):
        raise FloraPosterError("Unknown Flora product.")
    if type(placement) is not str or placement not in _SIZES:
        raise FloraPosterError("Unsupported poster placement.")
    if type(rights_attested) is not bool or type(price_reviewed) is not bool:
        raise FloraPosterError("Approval attestations must be booleans.")
    try:
        record = catalogue_snapshot(product_id)["products"][0]
        photo_report = inspect_owner_photo(photo_bytes, mime_type)
        if (record["id"] != product_id or record["photo"]["approved_for_publication"] is not False
                or record["price"]["reconfirm_before_publication"] is not True):
            raise FloraPosterError("Catalogue approval state is inconsistent.")
    except FloraCatalogError:
        raise FloraPosterError("Catalogue or photo verification failed.") from None

    width, height = _SIZES[placement]
    dark = product_id == "shampoo"
    background = (16, 22, 27) if dark else (249, 245, 237)
    foreground = (244, 235, 219) if dark else (58, 46, 33)
    accent = (217, 173, 99) if dark else (150, 102, 46)
    canvas = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(canvas)
    draw.text((90, 105), "FLORA BY M/S&Co.", fill=foreground, font=_font(42, True))
    draw.line((90, 180, width - 90, 180), fill=accent, width=4)
    draw.text((90, 230), record["name"], fill=foreground, font=_font(45, True))

    photo_top = 330
    photo_height = 630 if placement == "feed" else 1110
    photo_box = (90, photo_top, width - 90, photo_top + photo_height)
    draw.rectangle(photo_box, fill=(235, 230, 220), outline=accent, width=5)
    try:
        with Image.open(BytesIO(photo_bytes)) as source:
            source = ImageOps.exif_transpose(source)
            # Contain, never crop or synthesize product details.
            fitted = ImageOps.contain(source.convert("RGB"), (width - 200, photo_height - 20))
            x = (width - fitted.width) // 2
            y = photo_top + (photo_height - fitted.height) // 2
            canvas.paste(fitted, (x, y))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise FloraPosterError("Photo decode failed.") from None

    footer_top = photo_top + photo_height + 52
    draw.text((90, footer_top), record["unit"], fill=foreground, font=_font(36))
    draw.text((90, footer_top + 62), "DRAFT PRICE: " + record["price"]["display"],
              fill=accent, font=_font(40, True))
    draw.text((90, height - 145), "DRAFT - NOT APPROVED FOR PUBLICATION",
              fill=foreground, font=_font(27, True))
    draw.text((90, height - 100), "Confirm photo rights, price and stock before posting.",
              fill=foreground, font=_font(21))
    buffer = BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    png = buffer.getvalue()
    if not png or len(png) > _MAX_OUTPUT_BYTES:
        raise FloraPosterError("Poster output exceeded safe limit.")
    # Reopen the exact returned bytes: metadata alone is not output verification.
    try:
        with Image.open(BytesIO(png)) as verify:
            if verify.format != "PNG" or verify.size != (width, height):
                raise FloraPosterError("Poster format or dimensions are invalid.")
            verify.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise FloraPosterError("Poster could not be verified.") from None
    return {
        "product_id": product_id,
        "placement": placement,
        "canvas_px": [width, height],
        "source_photo_sha256": photo_report["sha256"],
        "preview_sha256": hashlib.sha256(png).hexdigest(),
        "preview_png": png,
        "preview_filename": f"flora_{product_id}_{placement}_DRAFT.png",
        "status": "draft_not_approved",
        "caller_rights_attested": rights_attested,
        "caller_price_reviewed": price_reviewed,
        "rights_independently_verified": False,
        "current_price_independently_verified": False,
        "approved_for_publication": False,
        "published": False,
        "saved": False,
        "requires_owner_review": True,
    }
