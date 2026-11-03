"""Private, operator-reviewed frame contact sheet for a rendered Hoshi mouth animatic.

Extracts actual decoded MP4 frames with a fixed FFmpeg argv (never shell).
The rectangle is a location guide, NOT automatic face/mouth alignment proof.
No uploads, external models, approval or production side effects.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageStat

MAX_VIDEO_BYTES = 15_000_000
MAX_FRAME_BYTES = 3_000_000
FRAME_WIDTH, FRAME_HEIGHT = 480, 270


class AnimeVisualReviewError(ValueError):
    """Unsafe video, invalid overlay or unavailable decoded review frame."""


def _sample_times(overlay: dict) -> list[dict]:
    """Select *decodable* 12 FPS frames, never a sub-frame activity midpoint.

    The renderer gates sprites on FFmpeg's frame timestamps. Sampling arbitrary
    milliseconds can falsely label a frame active when no encoded frame ever
    intersects a very short energy window. Every sample below is an exact
    decoded frame index from the 360-frame pilot.
    """
    if (type(overlay) is not dict or type(overlay.get("sprites")) is not list
            or len(overlay["sprites"]) != 3):
        raise AnimeVisualReviewError("Three validated mouth-overlay shots required.")
    samples = []
    for index, sprite in enumerate(overlay["sprites"]):
        if (type(sprite) is not dict
                or type(sprite.get("shot_id")) is not str
                or not 1 <= len(sprite["shot_id"]) <= 64
                or type(sprite.get("speaker_id")) is not str
                or not 1 <= len(sprite["speaker_id"]) <= 64
                or any(type(sprite.get(key)) is not int for key in
                       ("x", "y", "width", "height"))
                or not 0 <= sprite["x"] < FRAME_WIDTH
                or not 0 <= sprite["y"] < FRAME_HEIGHT
                or not 8 <= sprite["width"] <= 128
                or not 8 <= sprite["height"] <= 128
                or sprite["x"] + sprite["width"] > FRAME_WIDTH
                or sprite["y"] + sprite["height"] > FRAME_HEIGHT
                or type(sprite.get("energy_windows_ms")) is not list
                or len(sprite["energy_windows_ms"]) > 120):
            raise AnimeVisualReviewError("Invalid bounded mouth-overlay review metadata.")
        windows = sprite["energy_windows_ms"]
        previous = index * 10000
        for window in windows:
            if (type(window) is not list or len(window) != 2
                    or any(type(t) is not int for t in window)
                    or not index * 10000 <= window[0] < window[1] <= (index + 1) * 10000
                    or window[0] < previous):
                raise AnimeVisualReviewError("Invalid mouth activity windows.")
            previous = window[1]

        # Exact presentation timestamps for the 120 frames of this 10s shot.
        # Use fractional milliseconds for interval tests, never rounded values.
        frames = [(index * 120 + offset, index * 10000 + offset * 1000 / 12)
                  for offset in range(120)]
        active_frames = [(frame, ms) for frame, ms in frames
                         if any(start <= ms < end for start, end in windows)]
        quiet_frames = [(frame, ms) for frame, ms in frames
                        if not any(start <= ms < end for start, end in windows)]
        if active_frames:
            active_frame = active_frames[len(active_frames) // 2][0]
            active_kind = "active"
        else:
            active_frame = index * 120 + 60
            active_kind = "no_renderable_activity" if windows else "no_activity"
        if quiet_frames:
            if active_frames:
                quiet_frame = min(quiet_frames, key=lambda item:
                                  (abs(item[0] - active_frame), item[0]))[0]
            else:
                quiet_frame = quiet_frames[0][0]
            quiet_kind = "quiet"
        else:
            quiet_frame = index * 120 + 119
            quiet_kind = "no_quiet_interval"

        for kind, frame in ((active_kind, active_frame), (quiet_kind, quiet_frame)):
            local_ms = (frame - index * 120) * 1000 / 12
            absolute_ms = index * 10000 + local_ms
            visible = any(start <= absolute_ms < end for start, end in windows)
            samples.append({
                "shot_id": sprite["shot_id"], "speaker_id": sprite["speaker_id"],
                "sample_kind": kind, "frame_index": frame,
                "time_ms": round(absolute_ms),
                "expected_sprite_visible": visible,
                "x": sprite["x"], "y": sprite["y"],
                "width": sprite["width"], "height": sprite["height"],
            })
    return samples


def _verify_review_media(path: Path, ffprobe: str) -> dict:
    """Independently decode-count the exact private pilot before showing samples.

    Six sampled frames alone cannot prove that an arbitrary supplied video is
    the expected 30-second H.264/AAC pilot. No inferred approval or lip sync.
    """
    try:
        completed = subprocess.run(
            [ffprobe, "-v", "error", "-count_frames", "-show_entries",
             "stream=codec_type,codec_name,width,height,avg_frame_rate,nb_read_frames:"
             "format=duration,format_name", "-of", "json", str(path)],
            capture_output=True, timeout=25, check=False,
        )
        if completed.returncode != 0 or not 1 <= len(completed.stdout) <= 16000:
            raise AnimeVisualReviewError("Private review MP4 probe failed.")
        info = json.loads(completed.stdout)
        streams = info["streams"]
        if type(streams) is not list or len(streams) != 2:
            raise AnimeVisualReviewError("Review requires exactly one video and AAC audio stream.")
        video = [item for item in streams if item.get("codec_type") == "video"]
        audio = [item for item in streams if item.get("codec_type") == "audio"]
        duration = float(info["format"]["duration"])
        if (len(video) != 1 or len(audio) != 1
                or video[0].get("codec_name") != "h264"
                or audio[0].get("codec_name") != "aac"
                or (video[0].get("width"), video[0].get("height")) !=
                (FRAME_WIDTH, FRAME_HEIGHT)
                or video[0].get("avg_frame_rate") != "12/1"
                or video[0].get("nb_read_frames") != "360"
                or "mp4" not in info["format"].get("format_name", "")
                or not 29.8 <= duration <= 30.3):
            raise AnimeVisualReviewError("Review MP4 codec, frame count or duration mismatch.")
        return {
            "codec": "h264", "audio_codec": "aac",
            "width": FRAME_WIDTH, "height": FRAME_HEIGHT,
            "frame_rate": 12, "decoded_video_frames": 360,
            "duration_seconds": round(duration, 3),
            "status": "independently_probed_media_not_visual_approval",
        }
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError,
            AttributeError, IndexError):
        raise AnimeVisualReviewError("Could not independently verify review MP4.") from None



def _pair_pixel_evidence(active: Image.Image, quiet: Image.Image,
                         rectangle: tuple[int, int, int, int]) -> dict:
    """Measure actual decoded RGB differences, not anatomical alignment.

    Camera pans, lighting, backgrounds and compression can all cause changes;
    this metric must never be interpreted as proof of a correctly placed mouth.
    """
    if (active.mode != "RGB" or quiet.mode != "RGB"
            or active.size != (FRAME_WIDTH, FRAME_HEIGHT)
            or quiet.size != (FRAME_WIDTH, FRAME_HEIGHT)):
        raise AnimeVisualReviewError("Comparable RGB decoded frames required.")
    x, y, width, height = rectangle
    if (any(type(v) is not int for v in rectangle)
            or not 0 <= x < FRAME_WIDTH or not 0 <= y < FRAME_HEIGHT
            or width < 1 or height < 1
            or x + width > FRAME_WIDTH or y + height > FRAME_HEIGHT):
        raise AnimeVisualReviewError("Invalid mouth ROI for pixel comparison.")
    difference = ImageChops.difference(active, quiet)
    full_sums = ImageStat.Stat(difference).sum
    roi_sums = ImageStat.Stat(
        difference.crop((x, y, x + width, y + height))).sum
    roi_pixels = width * height
    outside_pixels = FRAME_WIDTH * FRAME_HEIGHT - roi_pixels
    roi_mean = sum(roi_sums) / (3 * roi_pixels)
    outside_mean = ((sum(full_sums) - sum(roi_sums)) /
                    (3 * outside_pixels)) if outside_pixels else 0.0
    return {
        "status": "sampled_pair_pixel_delta_not_alignment_proof",
        "roi_mean_absolute_rgb_delta": round(roi_mean, 3),
        "outside_roi_mean_absolute_rgb_delta": round(outside_mean, 3),
        "roi_change_detected": roi_mean >= 10.0,
        "frame_pair_is_not_lip_sync_or_alignment_proof": True,
    }

def build_mouth_review_sheet(video_mp4: bytes, mouth_overlay: dict,
                             *, ffmpeg_binary: str | None = None) -> dict:
    """Return an actual-frame PNG contact sheet plus manual-review metadata.

    Review remains unapproved even when frame decoding succeeds. A sheet can
    show a misplaced sprite; it cannot infer the correct anatomical location.
    """
    if type(video_mp4) is not bytes or not 100 <= len(video_mp4) <= MAX_VIDEO_BYTES:
        raise AnimeVisualReviewError("Bounded encoded MP4 bytes required.")
    samples = _sample_times(mouth_overlay)
    ffmpeg = ffmpeg_binary or shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AnimeVisualReviewError("Local FFmpeg and ffprobe are required for visual review.")
    sheet = Image.new("RGB", (FRAME_WIDTH * 3, (FRAME_HEIGHT + 26) * 2), (12, 15, 24))
    draw = ImageDraw.Draw(sheet)
    decoded_frames = []
    try:
        with tempfile.TemporaryDirectory(prefix="hoshi-mouth-review-") as directory:
            path = Path(directory) / "draft.mp4"
            path.write_bytes(video_mp4)
            media_qc = _verify_review_media(path, ffprobe)
            for idx, sample in enumerate(samples):
                command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
                           "-i", str(path),
                           "-vf", f'select=eq(n\\,{sample["frame_index"]})',
                           "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
                proc = subprocess.run(command, capture_output=True, timeout=15, check=False)
                if (proc.returncode != 0 or not 100 <= len(proc.stdout) <= MAX_FRAME_BYTES):
                    raise AnimeVisualReviewError("Actual MP4 review frame extraction failed.")
                with Image.open(BytesIO(proc.stdout)) as decoded:
                    if decoded.format != "PNG" or decoded.size != (FRAME_WIDTH, FRAME_HEIGHT):
                        raise AnimeVisualReviewError("Unexpected decoded review frame format.")
                    frame = decoded.convert("RGB")
                decoded_frames.append(frame)
                sample["decoded_frame_rgb_sha256"] = hashlib.sha256(frame.tobytes()).hexdigest()
                col, row = idx // 2, idx % 2
                left, top = col * FRAME_WIDTH, row * (FRAME_HEIGHT + 26)
                sheet.paste(frame, (left, top + 26))
                draw.text((left + 8, top + 7),
                          f'{sample["shot_id"][:24]} {sample["sample_kind"]} '
                          f'{sample["time_ms"] / 1000:.3f}s', fill=(240, 240, 240))
                x, y = left + sample["x"], top + 26 + sample["y"]
                draw.rectangle((x, y, x + sample["width"] - 1,
                                y + sample["height"] - 1),
                               outline=(255, 220, 40), width=2)
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        if isinstance(exc, AnimeVisualReviewError):
            raise
        raise AnimeVisualReviewError("Could not generate bounded visual review sheet.") from None
    pixel_evidence = []
    for shot_index in range(3):
        active_sample, quiet_sample = samples[2 * shot_index:2 * shot_index + 2]
        if (active_sample["sample_kind"] != "active"
                or quiet_sample["sample_kind"] != "quiet"
                or not active_sample["expected_sprite_visible"]
                or quiet_sample["expected_sprite_visible"]):
            evidence = {
                "status": "not_comparable_no_active_and_quiet_encoded_frames",
                "frame_pair_is_not_lip_sync_or_alignment_proof": True,
            }
        else:
            evidence = _pair_pixel_evidence(
                decoded_frames[2 * shot_index], decoded_frames[2 * shot_index + 1],
                (active_sample["x"], active_sample["y"],
                 active_sample["width"], active_sample["height"]))
        pixel_evidence.append({"shot_id": active_sample["shot_id"], **evidence})
    stream = BytesIO()
    sheet.save(stream, format="PNG")
    png = stream.getvalue()
    return {
        "filename": "hoshi_mouth_review_DRAFT.png",
        "png_bytes": png,
        "png_sha256": hashlib.sha256(png).hexdigest(),
        "samples": [{k: v for k, v in s.items() if k not in
                     ("x", "y", "width", "height")} for s in samples],
        "source_video_sha256": hashlib.sha256(video_mp4).hexdigest(),
        "media_qc": media_qc,
        "decoded_frame_pair_pixel_evidence": pixel_evidence,
        "pixel_evidence_is_not_visual_alignment_proof": True,
        "frame_sampling_basis": "exact_decoded_frame_index_12fps",
        "expected_visibility_is_metadata_not_pixel_verified": True,
        "review_source": "decoded_mp4_frames_with_operator_sprite_position_guides",
        "visual_alignment_verified": False,
        "owner_approved": False,
        "manual_review_required": True,
    }
