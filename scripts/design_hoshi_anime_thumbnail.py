"""Offline, operator-only Hindi/Urdu/Roman Urdu thumbnail title draft.

Revalidates the original video and selection; never uploads or approves media.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_thumbnail_export import (
    AnimeThumbnailExportError, build_private_selected_thumbnail_preview,
)
from cloud_backend.anime_thumbnail_title import (
    AnimeThumbnailTitleError, render_private_titled_thumbnail,
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file() or not 1 <= path.stat().st_size <= maximum:
        raise AnimeThumbnailTitleError("Missing or oversized private input.")
    return path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a local review-only shaped thumbnail title")
    parser.add_argument("--draft-dir", required=True, help="Existing private Anime Studio pilot")
    parser.add_argument("--font", required=True, help="Local operator-owned/licensed TTF or OTF font")
    parser.add_argument("--font-rights-attested", action="store_true",
                        help="Explicitly attest permission to use this font")
    args = parser.parse_args()
    try:
        directory = Path(args.draft_dir)
        font_path = Path(args.font)
        if font_path.suffix.lower() not in (".ttf", ".otf"):
            raise AnimeThumbnailTitleError("A local TTF/OTF font is required.")
        if args.font_rights_attested is not True:
            raise AnimeThumbnailTitleError("Font rights attestation is required.")
        try:
            manifest = json.loads(_read(directory / "manifest.json", 120_000).decode("utf-8"))
            selection = json.loads(_read(
                directory / "hoshi_thumbnail_selection_PRIVATE.json", 20_000).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise AnimeThumbnailTitleError("Invalid private pilot JSON.") from None
        preview = build_private_selected_thumbnail_preview(
            manifest,
            _read(directory / "hoshi_anime_animatic_DRAFT.mp4", 15_000_000),
            _read(directory / "hoshi_thumbnail_candidates_DRAFT.png", 3_000_000),
            selection)
        result = render_private_titled_thumbnail(
            preview, _read(font_path, 8_000_000),
            font_rights_attested=args.font_rights_attested)
        image = result.pop("png_bytes")
        target = directory / "titled_thumbnail_PRIVATE_DRAFT"
        target.mkdir(mode=0o700, exist_ok=False)
        with (target / result["filename"]).open("xb") as output:
            output.write(image)
        with (target / "typography_provenance_PRIVATE.json").open(
                "x", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, sort_keys=True, indent=2)
            output.write("\n")
        print("Private title draft rendered with RAQM; manual font/glyph/rights review required.")
        return 0
    except (AnimeThumbnailTitleError, AnimeThumbnailExportError, OSError, ValueError) as exc:
        print(f"Private title draft not created: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
