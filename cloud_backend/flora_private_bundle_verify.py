"""Read-only, offline verification of one private Flora photo-to-MP4 draft.

This checks actual media bytes and a decoded video frame, not just JSON hashes.
It cannot independently establish ownership, price accuracy, or permission to
publish. No network, approval mutation, or input-directory writes occur.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageStat, UnidentifiedImageError

from .flora_video_ads import FloraVideoError, _probe_video


class FloraPrivateBundleError(ValueError):
    """A private draft bundle is incomplete, altered or unsafe to review."""


_POSTER_SIZES = {"feed": (1080, 1350), "story": (1080, 1920)}
_VIDEO_SIZES = {"feed": (360, 450), "story": (360, 640)}
_LIMITS = {"photo": 16_000_000, "poster": 10_000_000,
           "video": 5_000_000, "provenance": 32_000}


def _read_regular(directory: Path, name: str, limit: int) -> bytes:
    # O_NONBLOCK prevents a named pipe from hanging before fstat can reject it.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(directory / name, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or not (0 < before.st_size <= limit):
            raise FloraPrivateBundleError("Unexpected private file type or size.")
        if before.st_mode & 0o077:
            raise FloraPrivateBundleError("Private bundle file permissions are too broad.")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read(limit + 1)
        after = os.fstat(fd)
        if (len(data) != before.st_size or before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns):
            raise FloraPrivateBundleError("Private bundle file changed during inspection.")
        return data
    finally:
        os.close(fd)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_sha(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _image(data: bytes, size: tuple[int, int] | None = None) -> Image.Image:
    try:
        with Image.open(BytesIO(data)) as opened:
            if (opened.format != "PNG" or opened.mode != "RGB"
                    or getattr(opened, "n_frames", 1) != 1 or opened.info
                    or (size is not None and opened.size != size)):
                raise FloraPrivateBundleError("Unexpected PNG format, metadata or dimensions.")
            opened.load()
            return opened.copy()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise FloraPrivateBundleError("Private PNG could not be decoded.") from None


def _decoded_midpoint(mp4: bytes, size: tuple[int, int]) -> Image.Image:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise FloraPrivateBundleError("Local FFmpeg and ffprobe are required.")
    try:
        with tempfile.TemporaryDirectory(prefix="hoshi-flora-verify-") as temp:
            path = Path(temp) / "private.mp4"
            path.write_bytes(mp4)
            _probe_video(path, ffprobe, size, False)
            result = subprocess.run(
                [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-ss", "1.5", "-i", str(path), "-frames:v", "1",
                 "-f", "image2pipe", "-vcodec", "png", "pipe:1"],
                capture_output=True, timeout=15, check=False,
            )
            if (result.returncode != 0 or not (100 < len(result.stdout) <= 3_000_000)):
                raise FloraPrivateBundleError("Encoded MP4 midpoint could not be decoded.")
            return _image(result.stdout, size)
    except (FloraVideoError, OSError, subprocess.TimeoutExpired):
        raise FloraPrivateBundleError("Encoded MP4 failed offline verification.") from None


def verify_private_flora_bundle(directory: Path, product_id: str,
                                placement: str = "story") -> dict:
    """Verify the exact four-file create-only draft, without approving it.

    A matching local hash is not an authenticity signature. The independent
    decoded-frame comparison checks that the MP4 depicts its saved poster.
    """
    if product_id not in ("gold_kit", "shampoo") or placement not in _POSTER_SIZES:
        raise FloraPrivateBundleError("Unsupported Flora draft identity.")
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise FloraPrivateBundleError("Expected an existing non-symlink private directory.")
    stem = f"flora_{product_id}_PRIVATE_photo"
    photo_name = stem + ".png"
    provenance_name = stem + "_provenance.json"
    poster_name = f"flora_{product_id}_{placement}_DRAFT.png"
    video_name = f"flora_{product_id}_{placement}_DRAFT.mp4"
    expected = {photo_name, provenance_name, poster_name, video_name}
    if {p.name for p in directory.iterdir()} != expected:
        raise FloraPrivateBundleError("Private draft has missing or unexpected files.")
    try:
        photo = _read_regular(directory, photo_name, _LIMITS["photo"])
        poster = _read_regular(directory, poster_name, _LIMITS["poster"])
        video = _read_regular(directory, video_name, _LIMITS["video"])
        raw_json = _read_regular(directory, provenance_name, _LIMITS["provenance"])
        meta = json.loads(raw_json)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        raise FloraPrivateBundleError("Private draft files or provenance are unreadable.") from None
    if not isinstance(meta, dict):
        raise FloraPrivateBundleError("Private provenance must be an object.")
    render = meta.get("private_render")
    if not isinstance(render, dict):
        raise FloraPrivateBundleError("Missing private MP4 provenance.")
    for key, value in {
        "product_id": product_id,
        "sanitized_mime_type": "image/png",
        "status": "private_sanitized_photo_draft_only",
        "orientation_normalized": True,
        "metadata_removed": True,
        "saved": False,
        "caller_rights_attested_not_independently_verified": True,
        "owner_rights_independently_verified": False,
        "approved_for_publication": False,
        "publication_permitted": False,
        "owner_approved": False,
        "published": False,
        "uploaded": False,
    }.items():
        if meta.get(key) != value or type(meta.get(key)) is not type(value):
            raise FloraPrivateBundleError("Private provenance or approval state mismatch.")
    for key, value in {
        "placement": placement,
        "poster_filename": poster_name,
        "video_filename": video_name,
        "codec": "h264",
        "duration_seconds": 3,
        "audio_status": "silent_no_music",
        "ffprobe_verified_locally": True,
        "photo_rights_independently_verified": False,
        "current_price_independently_verified": False,
        "owner_approved": False,
        "publication_permitted": False,
    }.items():
        if render.get(key) != value or type(render.get(key)) is not type(value):
            raise FloraPrivateBundleError("Private render identity or approval mismatch.")
    for value in (meta.get("source_photo_sha256"), meta.get("sanitized_photo_sha256"),
                  render.get("poster_sha256"), render.get("video_sha256")):
        if not _require_sha(value):
            raise FloraPrivateBundleError("Invalid private SHA-256 provenance.")
    if (meta["sanitized_photo_sha256"] != _digest(photo)
            or render["poster_sha256"] != _digest(poster)
            or render["video_sha256"] != _digest(video)):
        raise FloraPrivateBundleError("Private draft bytes do not match provenance.")
    photo_image = _image(photo)
    if (not 400 <= min(photo_image.size) <= max(photo_image.size) <= 2048
            or meta.get("sanitized_canvas_px") != list(photo_image.size)):
        raise FloraPrivateBundleError("Sanitized photo dimensions do not match provenance.")
    poster_image = _image(poster, _POSTER_SIZES[placement])
    midpoint = _decoded_midpoint(video, _VIDEO_SIZES[placement])
    expected_frame = poster_image.resize(_VIDEO_SIZES[placement], Image.Resampling.LANCZOS)
    difference = ImageStat.Stat(ImageChops.difference(midpoint, expected_frame)).mean
    # Lossy CRF32 H.264 changes pixels; a different poster is not acceptable.
    if sum(difference) / 3 > 18:
        raise FloraPrivateBundleError("Encoded MP4 does not visually match its DRAFT poster.")
    return {
        "status": "private_draft_verified_not_approved",
        "product_id": product_id,
        "placement": placement,
        "sanitized_photo_sha256": _digest(photo),
        "poster_sha256": _digest(poster),
        "video_sha256": _digest(video),
        "encoded_midpoint_checked": True,
        "owner_approved": False,
        "publication_permitted": False,
        "real_photo_rights_verified": False,
        "current_price_verified": False,
    }
