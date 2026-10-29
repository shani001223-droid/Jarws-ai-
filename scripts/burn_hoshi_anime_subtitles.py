"""Operator-only, create-only offline subtitle burn-in for an existing Hoshi pilot.

No upload, network, owner approval, automatic publishing or modification of
the original draft. Use an original/licensed local TTF/OTF font.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_subtitle_burnin import (
    AnimeSubtitleBurninError, render_private_subtitled_pilot,
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file() or not 1 <= path.stat().st_size <= maximum:
        raise AnimeSubtitleBurninError("Missing or oversized private local input.")
    return path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Burn validated Hindi/Urdu SRT into a PRIVATE 30s MP4 draft")
    parser.add_argument("--draft-dir", required=True)
    parser.add_argument("--font", required=True, help="Original/licensed local TTF/OTF")
    parser.add_argument("--font-rights-attested", action="store_true")
    args = parser.parse_args()
    try:
        root, font = Path(args.draft_dir), Path(args.font)
        if (not args.font_rights_attested
                or font.suffix.lower() not in (".ttf", ".otf")):
            raise AnimeSubtitleBurninError(
                "Explicit font rights and a local TTF/OTF required.")
        try:
            manifest = json.loads(
                _read(root / "manifest.json", 120_000).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise AnimeSubtitleBurninError("Invalid private manifest JSON.") from None
        result = render_private_subtitled_pilot(
            manifest,
            _read(root / "hoshi_anime_animatic_DRAFT.mp4", 15_000_000),
            _read(root / "hoshi_anime_animatic_DRAFT.srt", 20_000),
            _read(font, 8_000_000),
            font_rights_attested=True)
        encoded = result.pop("video_mp4")
        target = root / "subtitle_burnin_PRIVATE_DRAFT"
        target.mkdir(mode=0o700, exist_ok=False)
        with (target / result["filename"]).open("xb") as stream:
            stream.write(encoded)
        with (target / "subtitle_burnin_provenance_PRIVATE.json").open(
                "x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False,
                      sort_keys=True, indent=2)
            stream.write("\n")
        print("Private captioned MP4 created; human speech/readability review still required.")
        return 0
    except (AnimeSubtitleBurninError, OSError, ValueError) as exc:
        print(f"Private subtitle MP4 not created: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
