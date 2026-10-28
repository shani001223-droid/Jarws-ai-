"""Operator-only offline CLI for the private Hoshi Anime Studio animatic.

No network, public route, account login or uploader. Never overwrites outputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_pilot_animatic import (
    AnimePilotError, MAX_IMAGE_BYTES, render_private_animatic,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build private 30s anime storyboard animatic")
    parser.add_argument("--shot", action="append", required=True, help="Local PNG/JPEG (exactly 3)")
    parser.add_argument("--caption", action="append", required=True,
                        help="Hindi/Urdu/Roman Urdu single-line subtitle (exactly 3)")
    parser.add_argument("--out", required=True, help="New local directory; must not exist")
    parser.add_argument("--camera-move", action="append", choices=("static", "push_in", "pan_left", "pan_right"),
                        help="Optional 2D still camera move, once per shot (exactly 3)")
    parser.add_argument("--image-rights-attested", action="store_true",
                        help="Operator confirms rights to all supplied stills")
    args = parser.parse_args()
    if len(args.shot) != 3 or len(args.caption) != 3:
        parser.error("Exactly three --shot and three --caption values are required.")
    if args.camera_move is not None and len(args.camera_move) != 3:
        parser.error("Provide exactly three --camera-move values, or none.")
    if not args.image_rights_attested:
        parser.error("Explicit --image-rights-attested is required.")

    try:
        images = []
        for name in args.shot:
            path = Path(name)
            if not path.is_file() or not 100 <= path.stat().st_size <= MAX_IMAGE_BYTES:
                raise AnimePilotError("Local still missing or too large.")
            images.append(path.read_bytes())
        output = render_private_animatic(
            images, args.caption, image_rights_attested=True,
            camera_moves=args.camera_move)
        destination = Path(args.out)
        destination.mkdir(parents=False, exist_ok=False)
        try:
            (destination / output["filename"]).write_bytes(output["video_mp4"])
            (destination / "hoshi_anime_animatic_DRAFT.srt").write_bytes(
                output["subtitles_srt"])
            metadata = {k: v for k, v in output.items()
                        if k not in ("video_mp4", "subtitles_srt")}
            (destination / "manifest.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8")
        except OSError:
            for path in destination.iterdir():
                path.unlink()
            destination.rmdir()
            raise
        print(f"Private animatic created: {destination}")
        return 0
    except (AnimePilotError, OSError) as exc:
        print(f"Animatic not created: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
