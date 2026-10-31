"""Task 43: owner-reported Flora catalogue and safe photo intake inspection.

Read-only, fixed products; no uploads, image persistence, external publishing,
automatic price changes, fabricated photographs, or medical claims.
"""
from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image, UnidentifiedImageError

try:
    from .ad_studio import CATALOG
except ImportError:  # direct uvicorn import from cloud_backend
    from ad_studio import CATALOG


class FloraCatalogError(ValueError):
    """A catalogue record or proposed photo failed safe validation."""


# Prices are owner-reported from the existing Flora ad workflow, not scraped,
# independently checked, or guaranteed to be current at checkout.
_OWNER_REPORTED_PRICES = {"gold_kit": 3500, "shampoo": 1500}
_UNITS = {"gold_kit": "6-piece facial kit", "shampoo": "500 ml"}
_MIME_FORMAT = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}
_MAX_PHOTO_BYTES = 8_000_000
_MIN_SIDE = 400
_MAX_SIDE = 4096


def catalogue_snapshot(product_id: str | None = None) -> dict:
    """Return fresh detached JSON-safe values from the existing ad catalogue.

    No images are bundled or inferred from decorative art. A genuine photo
    remains missing until its owner supplies and approves the actual file.
    """
    if product_id is not None and product_id not in _OWNER_REPORTED_PRICES:
        raise FloraCatalogError("Unknown Flora product.")
    if set(CATALOG) != set(_OWNER_REPORTED_PRICES):
        raise FloraCatalogError("Flora catalogue and ad renderer are out of sync.")
    keys = (product_id,) if product_id is not None else tuple(_OWNER_REPORTED_PRICES)
    products = []
    for key in keys:
        item = CATALOG[key]
        amount = _OWNER_REPORTED_PRICES[key]
        if item.get("price") != f"RS. {amount:,}" or item.get("brand") != "FLORA BY M/S&Co.":
            raise FloraCatalogError("Owner-reported price or brand does not match ad renderer.")
        products.append({
            "id": key,
            "brand": item["brand"],
            "name": item["name"] + " " + item["subtitle"],
            "unit": _UNITS[key],
            "price": {
                "amount_pkr": amount,
                "display": item["price"],
                "source": "owner_reported_existing_project",
                "current_price_independently_verified": False,
                "reconfirm_before_publication": True,
            },
            "details": list(item["details"]),
            "photo": {
                "status": "not_provided",
                "asset_path": None,
                "sha256": None,
                "rights_verified": False,
                "approved_for_publication": False,
            },
            "creative_status": "illustrated_template_only",
        })
    return {
        "catalogue_version": "flora-owner-reported-v1",
        "read_only": True,
        "no_external_price_check": True,
        "no_actual_product_photos_available": True,
        "products": products,
    }


def inspect_owner_photo(data: bytes, mime_type: str) -> dict:
    """Validate proposed photo bytes offline without saving or approving them.

    The returned digest can support a future operator-controlled approval
    record. It does not itself establish ownership, rights or photo provenance.
    """
    if type(data) is not bytes or not (0 < len(data) <= _MAX_PHOTO_BYTES):
        raise FloraCatalogError("Invalid or oversized photo.")
    expected = _MIME_FORMAT.get(mime_type)
    if expected is None:
        raise FloraCatalogError("Unsupported photo format.")
    try:
        with Image.open(BytesIO(data)) as photo:
            width, height = photo.size
            if photo.format != expected or not (
                _MIN_SIDE <= width <= _MAX_SIDE and _MIN_SIDE <= height <= _MAX_SIDE
            ):
                raise FloraCatalogError("Photo format or dimensions are invalid.")
            if getattr(photo, "n_frames", 1) != 1:
                raise FloraCatalogError("Animated product photos are not accepted.")
            photo.verify()
        # Pillow verify() checks container structure but does not guarantee
        # that JPEG/WebP pixel data can actually be decoded. Fail before a
        # downstream poster/MP4 silently loses a corrupted source image.
        with Image.open(BytesIO(data)) as decoded:
            decoded.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise FloraCatalogError("Photo could not be verified.") from None
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "mime_type": mime_type,
        "width": width,
        "height": height,
        "saved": False,
        "owner_rights_verified": False,
        "approved_for_publication": False,
    }
