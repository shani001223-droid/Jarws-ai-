"""Create-only, offline Hindi/Urdu subtitle readability sheet for a private pilot.

No upload, external provider, owner approval or subtitle burn-in to the MP4.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_subtitle_preview import (
    AnimeSubtitlePreviewError, build_private_subtitle_contact_sheet,
)


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file() or not 1 <= path.stat().st_size <= limit:
        raise AnimeSubtitlePreviewError("Missing or oversized local input.")
    return path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build private actual-frame Hindi/Urdu SRT readability sheet")
    parser.add_argument("--draft-dir", required=True)
    parser.add_argument("--font", required=True, help="Locally owned/licensed TTF/OTF")
    parser.add_argument("--font-rights-attested", action="store_true")
    args = parser.parse_args()
    try:
        directory, font_path = Path(args.draft_dir), Path(args.font)
        if (not args.font_rights_attested
                or font_path.suffix.lower() not in (".ttf", ".otf")):
            raise AnimeSubtitlePreviewError("Explicit local font rights and TTF/OTF required.")
        try:
            manifest = json.loads(_read(directory / "manifest.json", 120_000).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise AnimeSubtitlePreviewError("Invalid private manifest JSON.") from None
        result = build_private_subtitle_contact_sheet(
            manifest,
            _read(directory / "hoshi_anime_animatic_DRAFT.mp4", 15_000_000),
            _read(directory / "hoshi_anime_animatic_DRAFT.srt", 20_000),
            _read(font_path, 8_000_000),
            font_rights_attested=True)
        png = result.pop("png_bytes")
        target = directory / "subtitle_review_PRIVATE_DRAFT"
        target.mkdir(mode=0o700, exist_ok=False)
        with (target / result["filename"]).open("xb") as output:
            output.write(png)
        with (target / "subtitle_review_provenance_PRIVATE.json").open(
                "x", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, sort_keys=True, indent=2)
            output.write("\n")
        print("Private shaped SRT contact sheet created; manual readability and voice review required.")
        return 0
    except (AnimeSubtitlePreviewError, OSError, ValueError) as exc:
        print(f"Private subtitle preview not created: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
