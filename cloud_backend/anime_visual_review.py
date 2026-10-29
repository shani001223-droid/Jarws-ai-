"""Private, operator-reviewed frame contact sheet for a rendered Hoshi mouth animatic.

Extracts actual decoded MP4 frames with a fixed FFmpeg argv (never shell).
The rectangle is a location guide, NOT automatic face/mouth alignment proof.
No uploads, external models, approval or production side effects.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw

MAX_VIDEO_BYTES = 15_000_000
MAX_FRAME_BYTES = 3_000_000
FRAME_WIDTH, FRAME_HEIGHT = 480, 270


class AnimeVisualReviewError(ValueError):
    """Unsafe video, invalid overlay or unavailable decoded review frame."""


def _sample_times(overlay: dict) -> list[dict]:
    if (type(overlay) is not dict or type(overlay.get("sprites")) is not list
            or len(overlay["sprites"]) != 3):
        raise AnimeVisualReviewError("Three validated mouth-overlay shots required.")
    samples = []
    for index, sprite in enumerate(overlay["sprites"]):
        if (type(sprite) is not dict
                or type(sprite.get("shot_id")) is not str
                or type(sprite.get("speaker_id")) is not str
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
        active = (sum(windows[0]) // 2 if windows else index * 10000 + 5000)
        quiet = next((index * 10000 + offset for offset in range(250, 10000, 250)
                      if not any(start <= index * 10000 + offset < end
                                 for start, end in windows)), None)
        for kind, ms in (("active" if windows else "no_activity", active),
                         ("quiet" if quiet is not None else "no_quiet_interval",
                          quiet if quiet is not None else index * 10000 + 9750)):
            samples.append({"shot_id": sprite["shot_id"], "speaker_id": sprite["speaker_id"],
                            "sample_kind": kind, "time_ms": ms,
                            "x": sprite["x"], "y": sprite["y"],
                            "width": sprite["width"], "height": sprite["height"]})
    return samples


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
    if not ffmpeg:
        raise AnimeVisualReviewError("Local FFmpeg is required for visual review.")
    sheet = Image.new("RGB", (FRAME_WIDTH * 3, (FRAME_HEIGHT + 26) * 2), (12, 15, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        with tempfile.TemporaryDirectory(prefix="hoshi-mouth-review-") as directory:
            path = Path(directory) / "draft.mp4"
            path.write_bytes(video_mp4)
            for idx, sample in enumerate(samples):
                command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
                           "-ss", f'{sample["time_ms"] / 1000:.3f}', "-i", str(path),
                           "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
                proc = subprocess.run(command, capture_output=True, timeout=15, check=False)
                if (proc.returncode != 0 or not 100 <= len(proc.stdout) <= MAX_FRAME_BYTES):
                    raise AnimeVisualReviewError("Actual MP4 review frame extraction failed.")
                with Image.open(BytesIO(proc.stdout)) as decoded:
                    if decoded.format != "PNG" or decoded.size != (FRAME_WIDTH, FRAME_HEIGHT):
                        raise AnimeVisualReviewError("Unexpected decoded review frame format.")
                    frame = decoded.convert("RGB")
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
        "review_source": "decoded_mp4_frames_with_operator_sprite_position_guides",
        "visual_alignment_verified": False,
        "owner_approved": False,
        "manual_review_required": True,
    }
