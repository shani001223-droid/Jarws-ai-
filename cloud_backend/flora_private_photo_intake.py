"""Privacy-first, offline Flora photo preparation for a PRIVATE draft only.

A caller-supplied source is inspected, decoded, EXIF-oriented, resized and
re-encoded onto a fresh RGB canvas. No raw source, EXIF, GPS, ICC profile or
original filename is saved or returned. This does not establish photo rights,
product identity, price accuracy or permission to publish.
"""
from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from cloud_backend.flora_catalog import FloraCatalogError, inspect_owner_photo


class FloraPrivatePhotoError(ValueError):
    """Unsafe or unrenderable proposed private Flora photo."""


_MAX_OUTPUT_BYTES = 16_000_000
_MAX_RENDER_SIDE = 2048


def prepare_private_flora_photo(photo_bytes: bytes, mime_type: str) -> dict:
    """Return a metadata-free PNG in memory and explicit non-approval flags.

    Original bytes are never persisted. Re-encoding is intentional; the source
    and sanitized digests remain distinct so downstream MP4 drafts can be
    traced without exposing the original photograph or its EXIF location.
    """
    try:
        source = inspect_owner_photo(photo_bytes, mime_type)
        with Image.open(BytesIO(photo_bytes)) as opened:
            if getattr(opened, "n_frames", 1) != 1:
                raise FloraPrivatePhotoError("Animated product photos are not accepted.")
            oriented = ImageOps.exif_transpose(opened)
            oriented.load()
            fitted = ImageOps.contain(
                oriented, (_MAX_RENDER_SIDE, _MAX_RENDER_SIDE),
                method=Image.Resampling.LANCZOS,
            )
            # Flatten transparent sources on white rather than introducing
            # black backgrounds or carrying original PNG metadata forward.
            rgba = fitted.convert("RGBA")
            clean = Image.new("RGB", rgba.size, "white")
            clean.paste(rgba, mask=rgba.getchannel("A"))
            clean.load()
            output = BytesIO()
            clean.save(output, format="PNG")
            sanitized = output.getvalue()
    except FloraPrivatePhotoError:
        raise
    except (FloraCatalogError, UnidentifiedImageError, OSError, ValueError,
            Image.DecompressionBombError):
        raise FloraPrivatePhotoError("Private photo could not be safely prepared.") from None

    if not 100 <= len(sanitized) <= _MAX_OUTPUT_BYTES:
        raise FloraPrivatePhotoError("Sanitized photo exceeds private size limit.")
    with Image.open(BytesIO(sanitized)) as verified:
        if (verified.format != "PNG" or verified.mode != "RGB"
                or getattr(verified, "n_frames", 1) != 1
                or verified.info):
            raise FloraPrivatePhotoError("Sanitized photo retained unsafe metadata.")
        verified.load()
        dimensions = [verified.width, verified.height]
    return {
        "sanitized_png_bytes": sanitized,
        "source_photo_sha256": source["sha256"],
        "sanitized_photo_sha256": hashlib.sha256(sanitized).hexdigest(),
        "source_mime_type": mime_type,
        "sanitized_mime_type": "image/png",
        "sanitized_canvas_px": dimensions,
        "orientation_normalized": True,
        "metadata_removed": True,
        "saved": False,
        "owner_rights_independently_verified": False,
        "approved_for_publication": False,
        "publication_permitted": False,
        "status": "private_sanitized_photo_draft_only",
    }
