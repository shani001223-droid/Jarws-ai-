"""Read-only integrity verification for an existing PRIVATE Anime Studio review bundle.

This is a local handoff guard, not human acceptance, rights clearance, speech
recognition, phoneme sync or publication permission. No network or writes.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import stat

from PIL import Image

from cloud_backend.anime_audio_waveform import (
    AnimeAudioWaveformError, build_encoded_audio_waveform,
)
from cloud_backend.anime_private_review_page import (
    AnimePrivateReviewPageError, VIDEO, VISUAL, WAVEFORM,
    build_private_review_page,
)
from cloud_backend.anime_subtitle_preview import _srt_windows
from cloud_backend.anime_thumbnail import AnimeThumbnailError, _verify_video


class AnimePrivateBundleError(ValueError):
    """Missing, modified or unsafe private reviewer evidence."""


PROVENANCE = "subtitle_burnin_provenance_PRIVATE.json"
PAGE = "hoshi_private_review_OFFLINE.html"
SOURCE_VIDEO = "hoshi_anime_animatic_DRAFT.mp4"
SOURCE_SRT = "hoshi_anime_animatic_DRAFT.srt"


def _read_regular(directory: Path, name: str, limit: int) -> bytes:
    """Read only fixed, bounded, non-symlink regular files."""
    path = directory / name
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or not 1 <= info.st_size <= limit:
            raise AnimePrivateBundleError("Unsafe or missing private file: " + name)
        data = path.read_bytes()
    except OSError:
        raise AnimePrivateBundleError("Cannot read private file: " + name) from None
    if not 1 <= len(data) <= limit:
        raise AnimePrivateBundleError("Invalid private file size: " + name)
    return data


def _match_hash(data: bytes, expected: object, name: str) -> None:
    actual = hashlib.sha256(data).hexdigest()
    if type(expected) is not str or actual != expected:
        raise AnimePrivateBundleError("Private SHA-256 mismatch: " + name)


def _check_png(data: bytes, dimensions: tuple[int, int], name: str) -> None:
    try:
        with Image.open(BytesIO(data)) as picture:
            if (picture.format != "PNG" or picture.size != dimensions
                    or getattr(picture, "n_frames", 1) != 1):
                raise AnimePrivateBundleError("Wrong private PNG: " + name)
            picture.load()
    except (OSError, ValueError, SyntaxError):
        raise AnimePrivateBundleError("Invalid private PNG: " + name) from None


def verify_private_review_bundle(directory: Path) -> dict:
    """Verify the saved HTML, source SRT, MP4, images and AAC-derived WAVs.

    Requires the original draft files in the parent directory. All names are
    fixed; no arbitrary paths from untrusted JSON are opened. Rebuilds the
    HTML and waveform from saved evidence, then probes the actual encoded MP4.
    """
    root = Path(directory)
    try:
        if (root.name != "subtitle_burnin_PRIVATE_DRAFT"
                or root.is_symlink() or not root.is_dir()
                or root.parent.is_symlink()):
            raise AnimePrivateBundleError("Expected a local private bundle directory.")
        meta = json.loads(_read_regular(root, PROVENANCE, 120_000))
        if type(meta) is not dict:
            raise AnimePrivateBundleError("Invalid private provenance object.")
        if (meta.get("review_page_filename") != PAGE
                or meta.get("review_page_human_review_required") is not True
                or meta.get("source_rights_independently_verified") is not False
                or meta.get("font_rights_attested_not_independently_verified") is not True):
            raise AnimePrivateBundleError("Unapproved review metadata required.")

        source = _read_regular(root.parent, SOURCE_VIDEO, 15_000_000)
        subtitles = _read_regular(root.parent, SOURCE_SRT, 20_000)
        _match_hash(source, meta.get("source_video_sha256"), SOURCE_VIDEO)
        _match_hash(subtitles, meta.get("source_subtitles_sha256"), SOURCE_SRT)
        windows = _srt_windows(subtitles)
        if len(windows) != 3:
            raise AnimePrivateBundleError("Three source subtitle cues required.")

        video = _read_regular(root, VIDEO, 15_000_000)
        _match_hash(video, meta.get("video_sha256"), VIDEO)
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            raise AnimePrivateBundleError("Local ffprobe required.")
        actual_qc = _verify_video(root / VIDEO, ffprobe)
        if meta.get("media_qc") != actual_qc:
            raise AnimePrivateBundleError("Encoded MP4 stream verification mismatch.")

        visual = _read_regular(root, VISUAL, 8_000_000)
        _match_hash(visual, meta.get("visual_evidence_sha256"), VISUAL)
        _check_png(visual, (960, 900), VISUAL)
        samples = meta.get("audio_review_samples")
        if type(samples) is not list or len(samples) not in (0, 3):
            raise AnimePrivateBundleError("Invalid private AAC cue list.")
        clips = []
        expected = {PROVENANCE, PAGE, VIDEO, VISUAL}
        for index, sample in enumerate(samples, 1):
            name = f"hoshi_cue_{index}_PRIVATE_REVIEW.wav"
            if type(sample) is not dict or sample.get("filename") != name:
                raise AnimePrivateBundleError("Invalid private WAV filename.")
            data = _read_regular(root, name, 750_000)
            _match_hash(data, sample.get("wav_sha256"), name)
            clips.append({"filename": name, "wav_bytes": data})
            expected.add(name)
        waveform = build_encoded_audio_waveform(clips, samples)
        if waveform["status"] != meta.get("audio_waveform_status"):
            raise AnimePrivateBundleError("Waveform status differs from actual audio.")
        if samples:
            png = _read_regular(root, WAVEFORM, 4_000_000)
            _match_hash(png, meta.get("audio_waveform_sha256"), WAVEFORM)
            _check_png(png, (1440, 660), WAVEFORM)
            if (png != waveform["png_bytes"]
                    or waveform["samples"] != meta.get("audio_waveform_samples")):
                raise AnimePrivateBundleError("AAC waveform does not match WAV samples.")
            expected.add(WAVEFORM)
        elif (meta.get("audio_waveform_filename") is not None
              or meta.get("audio_waveform_sha256") is not None
              or meta.get("audio_waveform_samples") != []):
            raise AnimePrivateBundleError("Silent source cannot claim waveform.")

        html = _read_regular(root, PAGE, 32_000)
        _match_hash(html, meta.get("review_page_sha256"), PAGE)
        if html != build_private_review_page(meta, windows):
            raise AnimePrivateBundleError("HTML does not match trusted review template.")
        # Refuse untracked files and symlinks in a purportedly complete bundle.
        if {entry.name for entry in root.iterdir()} != expected:
            raise AnimePrivateBundleError("Unexpected private bundle contents.")
        return {
            "status": "private_bundle_bytes_and_mp4_verified_human_review_pending",
            "file_count": len(expected),
            "video_sha256": meta["video_sha256"],
            "review_page_sha256": meta["review_page_sha256"],
            "owner_approved": False,
            "publication_permitted": False,
            "speech_or_lip_sync_verified": False,
            "rights_independently_verified": False,
        }
    except AnimePrivateBundleError:
        raise
    except (AnimePrivateReviewPageError, AnimeAudioWaveformError,
            AnimeThumbnailError, OSError, ValueError, TypeError, KeyError,
            AttributeError, UnicodeError, json.JSONDecodeError):
        raise AnimePrivateBundleError("Private review bundle failed integrity checks.") from None
