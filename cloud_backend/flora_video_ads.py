"""Task 46 foundation: bounded offline Flora MP4 DRAFT from a validated photo.

Only trusted Python callers may supply bytes. FFmpeg/ffprobe must be installed
locally; there is no HTTP upload, remote fetch, posting, or scheduled worker.
No audio is bundled. Caller-attested WAV rights are NOT independently verified.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave

from PIL import Image

try:
    from .flora_photo_posters import FloraPosterError, render_flora_photo_preview
except ImportError:  # direct Uvicorn import from cloud_backend/
    from flora_photo_posters import FloraPosterError, render_flora_photo_preview


class FloraVideoError(ValueError):
    """A requested offline draft is invalid, unavailable or unverifiable."""


_DURATION_SECONDS = 3
_FRAME_RATE = 12
_MAX_MP4_BYTES = 5_000_000
_MAX_WAV_BYTES = 1_000_000
_FRAME_SIZES = {"feed": (360, 450), "story": (360, 640)}


def _validate_wav(audio: bytes) -> None:
    if type(audio) is not bytes or not (44 <= len(audio) <= _MAX_WAV_BYTES):
        raise FloraVideoError("Audio must be a bounded PCM WAV.")
    try:
        with wave.open(BytesIO(audio), "rb") as sound:
            rate = sound.getframerate()
            duration = sound.getnframes() / rate if rate else 0
            if (sound.getcomptype() != "NONE" or sound.getsampwidth() != 2
                    or sound.getnchannels() not in (1, 2)
                    or rate not in (16000, 24000, 44100, 48000)
                    or not (3 <= duration <= 5)):
                raise FloraVideoError("WAV must be 16-bit PCM, 3-5 seconds.")
            expected_bytes = sound.getnframes() * sound.getnchannels() * sound.getsampwidth()
            if len(sound.readframes(sound.getnframes())) != expected_bytes:
                raise FloraVideoError("Truncated WAV audio.")
    except (wave.Error, EOFError, OSError, ValueError, ZeroDivisionError):
        raise FloraVideoError("Invalid WAV audio.") from None


def _probe_video(path: Path, probe: str, size: tuple[int, int], has_audio: bool) -> None:
    try:
        result = subprocess.run(
            [probe, "-v", "error", "-show_entries",
             "stream=codec_type,codec_name,width,height:format=duration,format_name",
             "-of", "json", str(path)],
            capture_output=True, timeout=8, check=False,
        )
        if result.returncode != 0 or len(result.stdout) > 16000:
            raise FloraVideoError("MP4 probe failed.")
        metadata = json.loads(result.stdout)
        video = [s for s in metadata["streams"] if s.get("codec_type") == "video"]
        audio = [s for s in metadata["streams"] if s.get("codec_type") == "audio"]
        container = metadata["format"]
        duration = float(container["duration"])
        if (len(video) != 1 or video[0].get("codec_name") != "h264"
                or (video[0].get("width"), video[0].get("height")) != size
                or len(audio) != int(has_audio)
                or (has_audio and audio[0].get("codec_name") != "aac")
                or "mp4" not in container.get("format_name", "")
                or not (2.7 <= duration <= 3.3)):
            raise FloraVideoError("MP4 codec, size, audio or duration mismatch.")
    except (subprocess.TimeoutExpired, OSError, KeyError, TypeError, ValueError, IndexError,
            json.JSONDecodeError):
        raise FloraVideoError("MP4 could not be independently inspected.") from None


def render_flora_video_draft(product_id: str, photo_bytes: bytes, mime_type: str,
                             placement: str = "story", *,
                             audio_wav: bytes | None = None,
                             audio_rights_attested: bool = False) -> dict:
    """Produce a 3-second H.264 MP4 in memory, always a non-publishable DRAFT.

    A genuine product photo, current price and audio rights require separate
    owner verification. Silent previews contain no copyrighted soundtrack.
    """
    if type(placement) is not str or placement not in _FRAME_SIZES:
        raise FloraVideoError("Unsupported video placement.")
    if type(audio_rights_attested) is not bool:
        raise FloraVideoError("Audio rights attestation must be boolean.")
    if audio_wav is None:
        if audio_rights_attested:
            raise FloraVideoError("No audio supplied for rights attestation.")
    else:
        if not audio_rights_attested:
            raise FloraVideoError("Audio requires explicit caller rights attestation.")
        _validate_wav(audio_wav)

    encoder, probe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not encoder or not probe:
        raise FloraVideoError("Offline FFmpeg and ffprobe are required.")
    try:
        poster = render_flora_photo_preview(product_id, photo_bytes, mime_type, placement)
    except FloraPosterError:
        raise FloraVideoError("Product photo or catalogue validation failed.") from None

    size = _FRAME_SIZES[placement]
    try:
        with tempfile.TemporaryDirectory(prefix="hoshi-flora-video-") as directory:
            root = Path(directory)
            frame_path = root / "draft.png"
            wav_path = root / "audio.wav"
            video_path = root / "draft.mp4"
            with Image.open(BytesIO(poster["preview_png"])) as image:
                image.convert("RGB").resize(size, Image.Resampling.LANCZOS).save(
                    frame_path, format="PNG")
            cmd = [
                encoder, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-loop", "1", "-framerate", str(_FRAME_RATE), "-i", str(frame_path),
            ]
            if audio_wav is not None:
                wav_path.write_bytes(audio_wav)
                cmd += ["-i", str(wav_path)]
            cmd += [
                "-map", "0:v:0",
            ]
            if audio_wav is not None:
                cmd += ["-map", "1:a:0"]
            cmd += [
                "-t", str(_DURATION_SECONDS), "-frames:v", str(_FRAME_RATE * _DURATION_SECONDS),
                "-vf", "fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3,format=yuv420p",
                "-c:v", "libx264", "-threads", "2", "-preset", "ultrafast", "-crf", "32",
                "-pix_fmt", "yuv420p", "-r", str(_FRAME_RATE),
            ]
            if audio_wav is None:
                cmd += ["-an"]
            else:
                cmd += ["-c:a", "aac", "-b:a", "64k"]
            cmd += ["-movflags", "+faststart", "-f", "mp4", str(video_path)]
            result = subprocess.run(cmd, capture_output=True, timeout=35, check=False)
            if result.returncode != 0 or not video_path.is_file():
                raise FloraVideoError("Offline video encoding failed.")
            if not (0 < video_path.stat().st_size <= _MAX_MP4_BYTES):
                raise FloraVideoError("MP4 exceeds the output size limit.")
            _probe_video(video_path, probe, size, audio_wav is not None)
            mp4 = video_path.read_bytes()
    except (OSError, subprocess.TimeoutExpired):
        raise FloraVideoError("Offline video rendering unavailable or timed out.") from None

    return {
        "product_id": product_id,
        "placement": placement,
        "canvas_px": list(size),
        "duration_seconds": _DURATION_SECONDS,
        "frame_rate": _FRAME_RATE,
        "codec": "h264",
        "audio_status": ("caller_supplied_wav_rights_unverified"
                         if audio_wav is not None else "silent_no_music"),
        "source_photo_sha256": poster["source_photo_sha256"],
        "poster_sha256": poster["preview_sha256"],
        "video_sha256": hashlib.sha256(mp4).hexdigest(),
        "video_mp4": mp4,
        "filename": f"flora_{product_id}_{placement}_DRAFT.mp4",
        "status": "draft_not_approved",
        "approved_for_publication": False,
        "published": False,
        "scheduled": False,
        "saved": False,
        "photo_rights_independently_verified": False,
        "audio_rights_independently_verified": False,
        "current_price_independently_verified": False,
        "requires_owner_review": True,
    }
