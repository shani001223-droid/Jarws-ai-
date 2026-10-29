"""Offline, create-only human QC record for a private Hoshi Anime Studio pilot.

Never grants release, publication, owner approval or asset-rights clearance.
The caller must inspect the actual rendered draft and provide three shot notes.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from PIL import Image

from cloud_backend.anime_visual_review import AnimeVisualReviewError, _verify_review_media
from cloud_backend.anime_subtitle_qc import AnimeSubtitleQCError, validate_private_subtitles


class AnimeReviewGateError(ValueError):
    """Invalid/tampered draft evidence or unsafe human QC request."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_private_review(manifest: dict, video: bytes, subtitles: bytes,
                          sheet: bytes, *, verdict: str, shot_notes: list[str],
                          inspected: bool) -> dict:
    """Bind a human's private-editing verdict to exact existing media bytes.

    This does not independently verify artwork rights, reviewer identity,
    spoken words, lip-sync, phone playback or production readiness.
    """
    if (type(manifest) is not dict or type(video) is not bytes
            or not 100 <= len(video) <= 15_000_000
            or type(subtitles) is not bytes or not 1 <= len(subtitles) <= 20_000
            or type(sheet) is not bytes or not 100 <= len(sheet) <= 3_000_000):
        raise AnimeReviewGateError("Bounded draft MP4, SRT, sheet and manifest required.")
    if (type(inspected) is not bool or not inspected
            or type(verdict) is not str
            or verdict not in ("private_qc_pass", "needs_revision")
            or type(shot_notes) is not list or len(shot_notes) != 3
            or any(type(note) is not str or not 8 <= len(note.strip()) <= 500
                   or any(ord(ch) < 32 and ch not in "\t" for ch in note)
                   for note in shot_notes)):
        raise AnimeReviewGateError("Explicit human inspection, verdict and three bounded shot notes required.")
    review = manifest.get("mouth_visual_review")
    if (type(review) is not dict
            or manifest.get("stage") != "private_storyboard_animatic_only"
            or manifest.get("actual_mp4_rendered") is not True
            or manifest.get("owner_approved") is not False
            or manifest.get("published") is not False
            or manifest.get("uploaded") is not False
            or manifest.get("video_sha256") != _sha(video)
            or manifest.get("subtitles_sha256") != _sha(subtitles)
            or review.get("source_video_sha256") != _sha(video)
            or review.get("png_sha256") != _sha(sheet)
            or review.get("owner_approved") is not False
            or review.get("visual_alignment_verified") is not False
            or review.get("manual_review_required") is not True):
        raise AnimeReviewGateError("Draft hashes, review evidence or unapproved status mismatch.")
    # The SRT hash alone does not prove captions or timestamps are meaningful:
    # validate the exact bytes against the storyboard and operator cue digest.
    try:
        subtitle_qc = validate_private_subtitles(manifest, subtitles)
    except AnimeSubtitleQCError:
        raise AnimeReviewGateError("Private SRT does not match bound storyboard/cues.") from None
    qc = review.get("media_qc")
    if (type(qc) is not dict or qc.get("status") !=
            "independently_probed_media_not_visual_approval"
            or qc.get("codec") != "h264" or qc.get("audio_codec") != "aac"
            or qc.get("decoded_video_frames") != 360
            or qc.get("width") != 480 or qc.get("height") != 270):
        raise AnimeReviewGateError("Independent encoded-media QC evidence missing.")
    # The original manifest's media_qc field is caller-controlled JSON. Re-probe
    # the exact submitted MP4 before allowing even a private editorial pass;
    # a matching SHA alone does not prove the bytes are playable H.264/AAC.
    try:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            raise AnimeReviewGateError("Local ffprobe is required for private QC.")
        with TemporaryDirectory(prefix="hoshi-private-qc-") as directory:
            video_path = Path(directory) / "review.mp4"
            video_path.write_bytes(video)
            verified_media = _verify_review_media(video_path, ffprobe)
    except (AnimeVisualReviewError, OSError):
        raise AnimeReviewGateError("Submitted MP4 failed independent media verification.") from None
    if any(qc.get(key) != verified_media[key] for key in (
            "status", "codec", "audio_codec", "decoded_video_frames",
            "width", "height", "frame_rate", "duration_seconds")):
        raise AnimeReviewGateError("Manifest media-QC metadata differs from actual MP4.")
    try:
        with Image.open(BytesIO(sheet)) as image:
            if image.format != "PNG" or image.size != (1440, 592):
                raise AnimeReviewGateError("Unexpected review sheet dimensions or format.")
            image.verify()
    except (OSError, ValueError, SyntaxError):
        raise AnimeReviewGateError("Corrupt private review PNG.") from None
    samples = review.get("samples")
    evidence = review.get("decoded_frame_pair_pixel_evidence")
    if (type(samples) is not list or len(samples) != 6
            or type(evidence) is not list or len(evidence) != 3):
        raise AnimeReviewGateError("Three-shot decoded-frame evidence required.")
    shot_ids = []
    for index in range(3):
        active, quiet = samples[index * 2:index * 2 + 2]
        entry = evidence[index]
        if (type(active) is not dict or type(quiet) is not dict
                or type(entry) is not dict
                or type(active.get("shot_id")) is not str
                or not 1 <= len(active["shot_id"]) <= 64
                or active["shot_id"] in shot_ids
                or quiet.get("shot_id") != active["shot_id"]
                or entry.get("shot_id") != active["shot_id"]
                or any(type(sample.get("frame_index")) is not int or
                       not index * 120 <= sample["frame_index"] < (index + 1) * 120
                       or type(sample.get("decoded_frame_rgb_sha256")) is not str
                       or len(sample["decoded_frame_rgb_sha256"]) != 64
                       for sample in (active, quiet))):
            raise AnimeReviewGateError("Invalid or mismatched shot/frame provenance.")
        comparable = (active.get("sample_kind") == "active"
                      and quiet.get("sample_kind") == "quiet"
                      and active.get("expected_sprite_visible") is True
                      and quiet.get("expected_sprite_visible") is False)
        if comparable:
            if (entry.get("status") != "sampled_pair_pixel_delta_not_alignment_proof"
                    or type(entry.get("roi_change_detected")) is not bool):
                raise AnimeReviewGateError("Comparable shot lacks real pixel-delta evidence.")
            if verdict == "private_qc_pass" and not entry["roi_change_detected"]:
                raise AnimeReviewGateError("Unchanged active mouth ROI requires revision.")
        elif entry.get("status") != "not_comparable_no_active_and_quiet_encoded_frames":
            raise AnimeReviewGateError("Non-comparable shot must remain explicitly unverified.")
        shot_ids.append(active["shot_id"])
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {
        "schema_version": 1,
        "scope": "private_local_editorial_qc_only_not_release_authorization",
        "human_inspection_attested_not_independently_verified": True,
        "verdict": verdict,
        "shot_notes": [{"shot_id": sid, "note": note.strip()}
                       for sid, note in zip(shot_ids, shot_notes)],
        "source_manifest_sha256": _sha(manifest_bytes),
        "source_video_sha256": _sha(video),
        "source_subtitles_sha256": _sha(subtitles),
        "subtitle_qc": subtitle_qc,
        "source_review_sheet_sha256": _sha(sheet),
        "owner_approved": False,
        "release_authorized": False,
        "publication_permitted": False,
        "asset_rights_independently_verified": False,
        "lip_sync_independently_verified": False,
        "physical_phone_qa_verified": False,
    }
