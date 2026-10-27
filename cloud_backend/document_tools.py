"""Bounded, offline document helpers for a trusted Hoshi Python operator.

No file paths, network, shell, upload routes or automatic AI processing.
Input and output are in-memory bytes. Untrusted files require a separate
resource-limited process before these helpers are exposed to end users.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import re

from PIL import Image, ImageOps, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter

MAX_INPUT = 3_000_000
MAX_OUTPUT = 6_000_000
MAX_PAGES = 16
MAX_PIXELS = 6_000_000
MAX_TEXT = 64_000
_PREVIEW = 4_000
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,79}$")
_TEXT_TYPES = {".txt": "text/plain", ".md": "text/markdown",
               ".json": "application/json"}
_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp"}


class DocumentSafetyError(ValueError):
    """A sanitized, expected rejection; never contains source file content."""


def _input(name: str, data: bytes) -> str:
    if (not isinstance(name, str) or not _NAME.fullmatch(name)
            or ".." in name or name.endswith((".", " "))):
        raise DocumentSafetyError("Unsafe file name.")
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_INPUT:
        raise DocumentSafetyError("File size or type is unsupported.")
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in _TEXT_TYPES and ext not in _IMAGE_TYPES and ext != ".pdf":
        raise DocumentSafetyError("File format is unsupported.")
    return ext


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _text(data: bytes) -> str:
    if len(data) > MAX_TEXT or b"\x00" in data:
        raise DocumentSafetyError("Text file exceeds safe limits.")
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeError:
        raise DocumentSafetyError("Text must be UTF-8.") from None


def _json_check(value: str) -> None:
    try:
        def invalid_constant(_value):
            raise ValueError("Non-standard JSON number")
        obj = json.loads(value, parse_constant=invalid_constant)
        if not isinstance(obj, (dict, list)):
            raise ValueError("Expected JSON object or list")
    except (ValueError, RecursionError):
        raise DocumentSafetyError("Invalid JSON document.") from None


def _pdf(data: bytes) -> PdfReader:
    if not data.startswith(b"%PDF-"):
        raise DocumentSafetyError("Invalid PDF header.")
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise DocumentSafetyError("Encrypted PDFs are unsupported.")
        count = len(reader.pages)
        if not 1 <= count <= MAX_PAGES:
            raise DocumentSafetyError("PDF page limit exceeded.")
        return reader
    except DocumentSafetyError:
        raise
    except Exception:
        raise DocumentSafetyError("PDF could not be parsed safely.") from None


def _image(data: bytes, ext: str) -> Image.Image:
    try:
        im = Image.open(BytesIO(data))
        expected = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG",
                    ".webp": "WEBP"}[ext]
        if im.format != expected or getattr(im, "n_frames", 1) != 1:
            raise DocumentSafetyError("Image encoding or frames unsupported.")
        w, h = im.size
        if not (1 <= w <= 8000 and 1 <= h <= 8000 and w * h <= MAX_PIXELS):
            raise DocumentSafetyError("Image dimensions exceed safe limits.")
        im.load()
        return im
    except DocumentSafetyError:
        raise
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        raise DocumentSafetyError("Image could not be decoded safely.") from None


def inspect_document(name: str, data: bytes) -> dict:
    """Return bounded text/dimensions only; never persist input or execute code."""
    ext = _input(name, data)
    base = {"name": name, "sha256": _digest(data), "bytes": len(data)}
    if ext in _TEXT_TYPES:
        text = _text(data)
        if ext == ".json":
            _json_check(text)
        return {**base, "kind": "project_text", "preview": text[:_PREVIEW],
                "characters": len(text), "truncated": len(text) > _PREVIEW}
    if ext in _IMAGE_TYPES:
        with _image(data, ext) as im:
            return {**base, "kind": "image", "width": im.width,
                    "height": im.height, "format": im.format}
    reader = _pdf(data)
    previews = []
    try:
        for page in reader.pages[:3]:
            # Extraction is deliberately limited to the first three pages.
            # PDF parsing must be sandboxed before use with hostile uploads.
            previews.append((page.extract_text() or "")[:_PREVIEW])
    except Exception:
        raise DocumentSafetyError("PDF text could not be extracted.") from None
    combined = "\n".join(part for part in previews if part).strip()[:_PREVIEW]
    return {**base, "kind": "pdf", "pages": len(reader.pages),
            "preview": combined, "partial_preview": len(reader.pages) > 3
            or sum(len(x) for x in previews) >= _PREVIEW}


def rotate_pdf(name: str, data: bytes, degrees: int, page_numbers: list[int]) -> dict:
    """Rotate only explicitly selected 1-based pages, preserving original bytes."""
    if _input(name, data) != ".pdf":
        raise DocumentSafetyError("PDF input required.")
    if type(degrees) is not int or degrees not in (90, 180, 270):
        raise DocumentSafetyError("Rotation must be 90, 180 or 270.")
    reader = _pdf(data)
    if (not isinstance(page_numbers, list) or not page_numbers
            or len(page_numbers) > MAX_PAGES
            or any(type(n) is not int or n < 1 or n > len(reader.pages)
                   for n in page_numbers)
            or len(set(page_numbers)) != len(page_numbers)):
        raise DocumentSafetyError("Invalid selected PDF pages.")
    selected = set(page_numbers)
    writer = PdfWriter()
    try:
        for i, page in enumerate(reader.pages, 1):
            if i in selected:
                page.rotate(degrees)
            writer.add_page(page)
        out = BytesIO()
        writer.write(out)
        payload = out.getvalue()
        if len(payload) > MAX_OUTPUT or len(_pdf(payload).pages) != len(reader.pages):
            raise DocumentSafetyError("Edited PDF failed verification.")
    except DocumentSafetyError:
        raise
    except Exception:
        raise DocumentSafetyError("PDF rotation failed.") from None
    return {"data": payload, "mime_type": "application/pdf",
            "sha256": _digest(payload), "pages": len(reader.pages),
            "rotated_pages": sorted(selected), "degrees": degrees}


def resize_image(name: str, data: bytes, max_side: int) -> dict:
    """Downscale to a metadata-stripped PNG; never upscale or overwrite input."""
    ext = _input(name, data)
    if ext not in _IMAGE_TYPES:
        raise DocumentSafetyError("Image input required.")
    if type(max_side) is not int or not 128 <= max_side <= 2048:
        raise DocumentSafetyError("Invalid image size.")
    with _image(data, ext) as im:
        oriented = ImageOps.exif_transpose(im)
        oriented.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        clean = Image.new("RGBA" if "A" in oriented.getbands() else "RGB",
                          oriented.size)
        clean.paste(oriented)
        output = BytesIO()
        clean.save(output, format="PNG", optimize=True)
        payload = output.getvalue()
    if len(payload) > MAX_OUTPUT:
        raise DocumentSafetyError("Resized image exceeds safe limits.")
    with Image.open(BytesIO(payload)) as check:
        check.verify()
    return {"data": payload, "mime_type": "image/png", "sha256": _digest(payload),
            "width": clean.width, "height": clean.height,
            "metadata_stripped": True}


def replace_project_text(name: str, data: bytes, old: str, new: str,
                         expected_sha256: str) -> dict:
    """One exact, optimistic-concurrency edit for trusted TXT/MD/JSON files."""
    ext = _input(name, data)
    if ext not in _TEXT_TYPES:
        raise DocumentSafetyError("Project text input required.")
    if not isinstance(expected_sha256, str) or expected_sha256 != _digest(data):
        raise DocumentSafetyError("Source revision mismatch.")
    if (not isinstance(old, str) or not old or len(old) > 1024
            or not isinstance(new, str) or len(new) > 4096
            or "\x00" in old or "\x00" in new):
        raise DocumentSafetyError("Invalid text replacement.")
    original = _text(data)
    if ext == ".json":
        _json_check(original)
    if original.count(old) != 1:
        raise DocumentSafetyError("Expected exactly one text match.")
    edited = original.replace(old, new, 1)
    payload = edited.encode("utf-8")
    if len(payload) > MAX_TEXT:
        raise DocumentSafetyError("Edited text exceeds safe limits.")
    if ext == ".json":
        _json_check(edited)
    return {"data": payload, "mime_type": _TEXT_TYPES[ext],
            "sha256": _digest(payload), "changed": True}
