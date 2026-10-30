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
from cloud_backend.anime_subtitle_burnin import (
    AnimeSubtitleBurninError, _encoded_comparison_evidence,
    _encoded_cue_audio_evidence,
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


def _verify_sampled_caption_gating(ffmpeg: str, source: Path, captioned: Path,
                                   windows: list[tuple[int, int, str]]) -> None:
    """Independently sample actual encoded caption visibility and cue edges.

    Compare bottom subtitle band against the same decoded source frame, with
    the upper band as a lossy-reencode control. This detects missing overlays
    and captions leaking outside cue boundaries at sampled frames; it does NOT
    prove glyph content, every intervening frame, speech or lip-sync.
    """
    if len(windows) != 3:
        raise AnimePrivateBundleError("Three subtitle cues required for ink checks.")
    from cloud_backend.anime_subtitle_burnin import _encoded_rgb_frame

    for shot, (start, end, _) in enumerate(windows):
        first, last = shot * 120, shot * 120 + 119
        active = [n for n in range(first, last + 1)
                  if start * 12 <= (2 * n + 1) * 500 < end * 12]
        if not active:
            raise AnimePrivateBundleError("Subtitle cue has no encoded frames.")
        # Include both shot edges: they expose captions left on outside a cue.
        for frame in sorted({first, active[len(active) // 2], last}):
            original = _encoded_rgb_frame(ffmpeg, source, frame)
            encoded = _encoded_rgb_frame(ffmpeg, captioned, frame)
            def changed(region: tuple[int, int, int, int]) -> int:
                a = original.crop(region).tobytes()
                b = encoded.crop(region).tobytes()
                return sum(1 for offset in range(0, len(a), 3)
                           if max(abs(a[offset + channel] - b[offset + channel])
                                  for channel in range(3)) >= 55)
            # Equal-sized upper control estimates normal H.264 re-encode noise.
            control = changed((12, 100, 468, 143))
            caption = changed((12, 222, 468, 265))
            if frame in active:
                if caption < max(80, control * 2 + 40):
                    raise AnimePrivateBundleError(
                        "Encoded subtitle ink absent in sampled active cue.")
            elif caption > max(200, control * 3 + 100):
                raise AnimePrivateBundleError(
                    "Encoded subtitle overlay leaks outside sampled cue.")


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
        # A matching PNG digest alone is insufficient: an edited provenance
        # document could re-hash an unrelated but valid PNG. Re-decode the
        # source and captioned MP4s and rebuild the actual comparison pixels.
        records = meta.get("visual_evidence_samples")
        if (type(records) is not list or len(records) != 3
                or meta.get("visual_evidence_decoded_from_both_mp4s") is not True
                or meta.get("visual_evidence_human_review_required") is not True
                or meta.get("visual_evidence_resolution") != [960, 900]):
            raise AnimePrivateBundleError("Missing actual encoded-frame evidence.")
        reference = []
        for index, (record, (start, end, _)) in enumerate(zip(records, windows)):
            expected_frame = max(index * 120, min(index * 120 + 119,
                                                   (start + end) * 12 // 2000))
            if (type(record) is not dict
                    or record.get("shot_index") != index + 1
                    or record.get("cue_start_ms") != start
                    or record.get("cue_end_ms") != end
                    or type(record.get("decoded_frame_index")) is not int
                    or record["decoded_frame_index"] != expected_frame
                    or type(record.get("original_decoded_rgb_sha256")) is not str):
                raise AnimePrivateBundleError("Invalid encoded comparison cue.")
            reference.append({
                "decoded_frame_index": expected_frame,
                "decoded_frame_rgb_sha256": record["original_decoded_rgb_sha256"],
                "cue_start_ms": start, "cue_end_ms": end,
            })
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise AnimePrivateBundleError("Local ffmpeg required.")
        regenerated, decoded_records = _encoded_comparison_evidence(
            ffmpeg, root.parent / SOURCE_VIDEO, root / VIDEO, reference)
        if regenerated != visual or decoded_records != records:
            raise AnimePrivateBundleError(
                "Comparison pixels differ from actual encoded MP4 frames.")
        _verify_sampled_caption_gating(
            ffmpeg, root.parent / SOURCE_VIDEO, root / VIDEO, windows)
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
        # Hashes and a regenerated waveform only prove the saved WAVs agree
        # with saved JSON. Independently decode the actual captioned MP4 AAC
        # and compare the exact listening bytes and cue metadata, so a forged
        # WAV with rewritten local hashes cannot masquerade as encoded speech.
        regenerated_clips, regenerated_samples = _encoded_cue_audio_evidence(
            ffmpeg, root / VIDEO, windows, actual_qc["audio_codec"])
        if (regenerated_samples != samples
                or len(regenerated_clips) != len(clips)
                or any(a["filename"] != b["filename"]
                       or a["wav_bytes"] != b["wav_bytes"]
                       for a, b in zip(regenerated_clips, clips))):
            raise AnimePrivateBundleError(
                "AAC listening clips differ from actual encoded MP4 audio.")
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
            AnimeSubtitleBurninError,
            AnimeThumbnailError, OSError, ValueError, TypeError, KeyError,
            AttributeError, UnicodeError, json.JSONDecodeError):
        raise AnimePrivateBundleError("Private review bundle failed integrity checks.") from None
