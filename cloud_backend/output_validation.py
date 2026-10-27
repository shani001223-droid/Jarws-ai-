"""Task 35: strict, offline format checks for *trusted generated* outputs.

No filesystem paths, network, execution, uploads or publication. These checks
are not a sandbox for hostile documents/code and do not certify correctness.
"""
from __future__ import annotations

import ast
import hashlib
from io import BytesIO
import json
import re
import warnings
from zipfile import BadZipFile, ZIP_STORED, ZipFile

from PIL import Image, UnidentifiedImageError

try:
    from .ad_studio import CATALOG
except ImportError:  # Direct Uvicorn working-directory import.
    from ad_studio import CATALOG


_MAX_SOURCE = 64_000
_MAX_JSON = 64_000
_MAX_PNG = 3_000_000
_MAX_INNER = 5_000_000
_MAX_CAMPAIGN = 10_100_000
_SHA = re.compile(r"^[0-9a-f]{64}$")
_KEYS = frozenset(("gold_kit", "shampoo"))


class OutputFormatError(ValueError):
    """Stable, non-sensitive failure code."""


def _bytes(value: object, limit: int) -> bytes:
    if type(value) is not bytes or not value or len(value) > limit:
        raise OutputFormatError("invalid_output_size")
    return value


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_python_source(source: object) -> dict:
    """Check UTF-8 Python syntax only. NEVER execute or trust the code."""
    data = _bytes(source, _MAX_SOURCE)
    try:
        text = data.decode("utf-8", errors="strict")
        if "\x00" in text:
            raise ValueError()
        tree = ast.parse(text, mode="exec")
        compile(tree, "<generated-output>", "exec", dont_inherit=True)
    except (UnicodeError, SyntaxError, ValueError, MemoryError, RecursionError):
        raise OutputFormatError("invalid_python_source") from None
    return {"format": "python", "bytes": len(data), "sha256": _digest(data),
            "syntax_only": True, "executed": False}


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def _no_constant(_):
    raise ValueError("non_finite")


def validate_json_document(source: object) -> dict:
    """Validate strict JSON bytes; reject duplicate keys and non-finite numbers."""
    data = _bytes(source, _MAX_JSON)
    try:
        text = data.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_unique_pairs,
                           parse_constant=_no_constant)
        if not isinstance(value, (dict, list)):
            raise ValueError("top_level")
    except (UnicodeError, ValueError, RecursionError, MemoryError):
        raise OutputFormatError("invalid_json_document") from None
    return {"format": "json", "bytes": len(data), "sha256": _digest(data),
            "parsed": True}


def validate_png_media(source: object, *, expected_size: tuple[int, int]) -> dict:
    """Check real PNG decoding, dimensions and pixel budget, not image aesthetics."""
    data = _bytes(source, _MAX_PNG)
    if expected_size not in ((1080, 1350), (1080, 1920)):
        raise OutputFormatError("unsupported_image_dimensions")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as img:
                if img.format != "PNG" or img.size != expected_size or img.n_frames != 1:
                    raise ValueError("wrong_png")
                img.verify()
            with Image.open(BytesIO(data)) as img:
                img.load()
                if img.size != expected_size:
                    raise ValueError("wrong_png")
    except (OSError, ValueError, UnidentifiedImageError,
            Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise OutputFormatError("invalid_png_media") from None
    return {"format": "png", "bytes": len(data), "sha256": _digest(data),
            "width": expected_size[0], "height": expected_size[1]}


def _safe_entries(archive: ZipFile, expected: set[str], total_limit: int,
                  *, require_stored: bool = False) -> None:
    entries = archive.infolist()
    if len(entries) != len(expected) or {i.filename for i in entries} != expected:
        raise OutputFormatError("unexpected_archive_entries")
    if len({i.filename for i in entries}) != len(entries):
        raise OutputFormatError("duplicate_archive_entry")
    if any(i.is_dir() or i.flag_bits & 1 or i.file_size < 1
           or i.file_size > _MAX_INNER or i.compress_size < 1
           or (require_stored and i.compress_type != ZIP_STORED)
           or i.file_size > max(1000, i.compress_size * 100)
           for i in entries):
        raise OutputFormatError("unsafe_archive_entry")
    if sum(i.file_size for i in entries) > total_limit:
        raise OutputFormatError("archive_expansion_limit")


def _verify_inner(data: bytes, key: str) -> None:
    expected = {
        f"{key}_feed_1080x1350.png", f"{key}_story_1080x1920.png",
        f"{key}_caption.txt", f"{key}_video_storyboard.txt",
    }
    with ZipFile(BytesIO(data)) as inner:
        _safe_entries(inner, expected, 10_000_000)
        for label, size in (("feed_1080x1350", (1080, 1350)),
                            ("story_1080x1920", (1080, 1920))):
            validate_png_media(inner.read(f"{key}_{label}.png"), expected_size=size)
        caption = inner.read(f"{key}_caption.txt")
        storyboard = inner.read(f"{key}_video_storyboard.txt")
        if len(caption) > 16_000 or len(storyboard) > 16_000:
            raise OutputFormatError("oversized_campaign_copy")
        try:
            caption_text = caption.decode("utf-8")
            storyboard_text = storyboard.decode("utf-8")
        except UnicodeError:
            raise OutputFormatError("invalid_campaign_copy") from None
        if CATALOG[key]["caption"] not in caption_text or (
            "not a rendered video" not in storyboard_text.lower()
        ):
            raise OutputFormatError("unverified_campaign_copy")


def validate_campaign_zip(source: object) -> dict:
    """Independently check Task 34 nested ZIP + manifest and real PNG bytes.

    This is an allowlisted offline Flora campaign only. No MP4 claim, extraction,
    user-supplied paths or general archive handling.
    """
    data = _bytes(source, _MAX_CAMPAIGN)
    try:
        with ZipFile(BytesIO(data)) as outer:
            names = outer.namelist()
            if not 2 <= len(names) <= 3 or "manifest.json" not in names:
                raise OutputFormatError("invalid_campaign_archive")
            _safe_entries(outer, set(names), _MAX_CAMPAIGN,
                          require_stored=True)
            manifest_bytes = outer.read("manifest.json")
            validate_json_document(manifest_bytes)
            manifest = json.loads(manifest_bytes)
            if type(manifest) is not dict or set(manifest) != {
                "schema_version", "kind", "rendered_video", "products"
            } or type(manifest["schema_version"]) is not int or (
                manifest["schema_version"] != 1 or
                manifest["kind"] != "flora_offline_campaign" or
                manifest["rendered_video"] is not False
            ):
                raise OutputFormatError("invalid_campaign_manifest")
            products = manifest["products"]
            if type(products) is not list or not 1 <= len(products) <= 2:
                raise OutputFormatError("invalid_campaign_manifest")
            keys = []
            for item in products:
                if type(item) is not dict or set(item) != {
                    "product_key", "filename", "sha256", "bytes"
                }:
                    raise OutputFormatError("invalid_campaign_manifest")
                key = item["product_key"]
                if type(key) is not str or key not in _KEYS or key not in CATALOG or key in keys:
                    raise OutputFormatError("invalid_campaign_product")
                filename = key + ".zip"
                if item["filename"] != filename or type(item["bytes"]) is not int or (
                    item["bytes"] < 1 or item["bytes"] > _MAX_INNER
                ) or type(item["sha256"]) is not str or not _SHA.fullmatch(item["sha256"]):
                    raise OutputFormatError("invalid_campaign_manifest")
                keys.append(key)
            if set(names) != {"manifest.json", *(key + ".zip" for key in keys)}:
                raise OutputFormatError("unexpected_archive_entries")
            for item in products:
                payload = outer.read(item["filename"])
                if len(payload) != item["bytes"] or _digest(payload) != item["sha256"]:
                    raise OutputFormatError("campaign_digest_mismatch")
                _verify_inner(payload, item["product_key"])
    except (BadZipFile, OSError, EOFError, RuntimeError, UnicodeError):
        raise OutputFormatError("invalid_campaign_archive") from None
    return {"format": "flora_campaign_zip", "bytes": len(data),
            "sha256": _digest(data), "products": keys,
            "rendered_video": False, "verified_in_memory": True}
