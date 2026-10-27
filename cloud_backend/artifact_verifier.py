"""Validate real HOSHI product-ad outputs before claiming a backend job completed.

Verification has no outbound requests, shell access, extra paid AI usage or
side effects. Only short-lived, bounded in-memory artifacts are inspected.
"""
from __future__ import annotations

import base64
import binascii
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from PIL import Image, UnidentifiedImageError

try:
    from .ad_studio import CATALOG, choose_products
except ImportError:  # for direct uvicorn from cloud_backend
    from ad_studio import CATALOG, choose_products


class ArtifactVerificationError(ValueError):
    """A generated artifact failed a check; safe for a bounded regeneration."""


_MAX_ZIP_BYTES = 5_000_000
_MAX_ENTRY_BYTES = 3_000_000
_MAX_TOTAL_UNCOMPRESSED = 10_000_000


def _decode(value: object, limit: int) -> bytes:
    if not isinstance(value, str) or len(value) > (limit * 4 // 3) + 10:
        raise ArtifactVerificationError("Invalid encoded artifact size.")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        raise ArtifactVerificationError("Invalid encoded artifact.") from None
    if not decoded or len(decoded) > limit:
        raise ArtifactVerificationError("Artifact exceeded verification limit.")
    return decoded


def verify_ad_pack(pack: object, message: str) -> dict:
    """Raise a predictable error if any expected image, caption or ZIP is wrong."""
    keys = choose_products(message)
    if not isinstance(pack, dict) or pack.get("ok") is not True or pack.get("completed") is not True:
        raise ArtifactVerificationError("Generator did not complete.")
    if pack.get("task") != "create_product_ads":
        raise ArtifactVerificationError("Unexpected generator task.")
    products = pack.get("products")
    if not isinstance(products, list) or len(products) != len(keys):
        raise ArtifactVerificationError("Product metadata does not match request.")

    expected_names = {
        name
        for key in keys
        for name in (
            f"{key}_feed_1080x1350.png",
            f"{key}_story_1080x1920.png",
            f"{key}_caption.txt",
            f"{key}_video_storyboard.txt",
        )
    }
    zip_bytes = _decode(pack.get("zip_base64"), _MAX_ZIP_BYTES)
    preview_bytes = _decode(pack.get("preview_base64"), _MAX_ENTRY_BYTES)
    try:
        with ZipFile(BytesIO(zip_bytes)) as archive:
            entries = archive.infolist()
            names = [info.filename for info in entries]
            if (len(names) != len(expected_names) or len(set(names)) != len(names)
                    or set(names) != expected_names):
                raise ArtifactVerificationError("ZIP contents do not match expected deliverables.")
            if any(info.file_size > _MAX_ENTRY_BYTES or info.file_size < 1 for info in entries):
                raise ArtifactVerificationError("ZIP entry is missing or too large.")
            if sum(info.file_size for info in entries) > _MAX_TOTAL_UNCOMPRESSED:
                raise ArtifactVerificationError("Expanded ZIP exceeds verification limit.")

            for index, key in enumerate(keys):
                product = CATALOG[key]
                metadata = products[index]
                if (not isinstance(metadata, dict) or
                        metadata.get("product") != product["name"] + " " + product["subtitle"] or
                        metadata.get("price") != product["price"] or
                        metadata.get("caption") != product["caption"]):
                    raise ArtifactVerificationError("Product details do not match trusted catalog.")
                for kind, size in (("feed_1080x1350", (1080, 1350)),
                                   ("story_1080x1920", (1080, 1920))):
                    img_bytes = archive.read(f"{key}_{kind}.png")
                    try:
                        with Image.open(BytesIO(img_bytes)) as image:
                            if image.format != "PNG" or image.size != size:
                                raise ArtifactVerificationError("Image format or dimensions are wrong.")
                            image.verify()
                    except (UnidentifiedImageError, OSError, ValueError):
                        raise ArtifactVerificationError("Generated image is corrupt.") from None
                    if index == 0 and kind.startswith("feed") and preview_bytes != img_bytes:
                        raise ArtifactVerificationError("Preview does not match downloadable image.")

                caption = archive.read(f"{key}_caption.txt").decode("utf-8")
                storyboard = archive.read(f"{key}_video_storyboard.txt").decode("utf-8")
                if product["caption"] not in caption:
                    raise ArtifactVerificationError("Product caption is incomplete.")
                if "not a rendered video" not in storyboard.lower():
                    raise ArtifactVerificationError("Storyboard is misrepresented as a rendered video.")
    except (BadZipFile, OSError, UnicodeError, EOFError):
        raise ArtifactVerificationError("Generated ZIP could not be verified.") from None

    return {"passed": True, "checks": ["catalog", "zip_entries", "png_dimensions", "captions", "storyboards", "preview"]}
