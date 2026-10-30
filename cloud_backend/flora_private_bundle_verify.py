"""Read-only, offline verification of one private Flora photo-to-MP4 draft.

This checks actual media bytes and all 36 decoded video frames, not just JSON hashes.
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


def _image(data: bytes, size: tuple[int, int] | None = None,
           *, allow_decoder_aspect: bool = False) -> Image.Image:
    try:
        with Image.open(BytesIO(data)) as opened:
            if (opened.format != "PNG" or opened.mode != "RGB"
                    or getattr(opened, "n_frames", 1) != 1
                    or (opened.info and not (allow_decoder_aspect
                                            and set(opened.info) <= {"aspect"}))
                    or (size is not None and opened.size != size)):
                raise FloraPrivateBundleError("Unexpected PNG format, metadata or dimensions.")
            opened.load()
            return opened.copy()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise FloraPrivateBundleError("Private PNG could not be decoded.") from None


def _decoded_frames(mp4: bytes, size: tuple[int, int]) -> bytes:
    """Decode the entire fixed 36-frame DRAFT, with a bounded 37-frame cap.

    Sampling only three timestamps missed short substituted segments. Decoding
    the original encoded frames without frame-rate conversion also rejects
    truncated/extra-frame videos. No private input is modified or uploaded.
    """
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
                 "-i", str(path), "-map", "0:v:0", "-frames:v", "37",
                 "-vsync", "0", "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"],
                capture_output=True, timeout=30, check=False,
            )
            expected_bytes = size[0] * size[1] * 3 * 36
            if result.returncode != 0 or len(result.stdout) != expected_bytes:
                raise FloraPrivateBundleError(
                    "Encoded MP4 must contain exactly 36 decodable frames.")
            return result.stdout
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
    frame_size = _VIDEO_SIZES[placement]
    raw_frames = _decoded_frames(video, frame_size)
    expected_frame = poster_image.resize(frame_size, Image.Resampling.LANCZOS)
    black_frame = Image.new("RGB", frame_size)
    frame_bytes = frame_size[0] * frame_size[1] * 3
    # The source encoder uses 12 fps, with a 0.3-second fade-in and
    # fade-out beginning at 2.7s. Inspect ALL 36 encoded frames, including
    # fades, rather than trusting a few timestamps or locally rehashed JSON.
    for index in range(36):
        timestamp = index / 12
        opacity = max(0.0, min(1.0, timestamp / 0.3, (3.0 - timestamp) / 0.3))
        expected = Image.blend(black_frame, expected_frame, opacity)
        frame = Image.frombytes(
            "RGB", frame_size, raw_frames[index * frame_bytes:(index + 1) * frame_bytes])
        difference = ImageStat.Stat(ImageChops.difference(frame, expected)).mean
        # Fades add extra codec/quantization error, especially near black.
        tolerance = 24 if opacity < 1.0 else 18
        if sum(difference) / 3 > tolerance:
            raise FloraPrivateBundleError(
                "Encoded MP4 does not visually match its DRAFT poster at frame "
                + str(index) + ".")
    return {
        "status": "private_draft_verified_not_approved",
        "product_id": product_id,
        "placement": placement,
        "sanitized_photo_sha256": _digest(photo),
        "poster_sha256": _digest(poster),
        "video_sha256": _digest(video),
        "encoded_midpoint_checked": True,
        "encoded_three_samples_checked": True,
        "encoded_sample_times_seconds": [0.6, 1.5, 2.4],
        "encoded_full_frame_checked": True,
        "encoded_frames_checked": 36,
        "encoded_expected_frame_rate": 12,
        "owner_approved": False,
        "publication_permitted": False,
        "real_photo_rights_verified": False,
        "current_price_verified": False,
    }
