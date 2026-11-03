"""Operator-only, create-only private selected-frame thumbnail preview export.

Requires an existing inspected editorial selection. No final design or upload.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_thumbnail_export import (
    AnimeThumbnailExportError, build_private_selected_thumbnail_preview,
)


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file() or not 1 <= path.stat().st_size <= maximum:
        raise AnimeThumbnailExportError("Missing or oversized private draft input.")
    return path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a private selected-frame thumbnail draft")
    parser.add_argument("--draft-dir", required=True, help="Existing local anime pilot directory")
    args = parser.parse_args()
    try:
        directory = Path(args.draft_dir)
        try:
            manifest = json.loads(_read(directory / "manifest.json", 120_000).decode("utf-8"))
            selection = json.loads(_read(
                directory / "hoshi_thumbnail_selection_PRIVATE.json", 20_000).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise AnimeThumbnailExportError("Invalid private JSON input.") from None
        export = build_private_selected_thumbnail_preview(
            manifest,
            _read(directory / "hoshi_anime_animatic_DRAFT.mp4", 15_000_000),
            _read(directory / "hoshi_thumbnail_candidates_DRAFT.png", 3_000_000),
            selection)
        preview_bytes = export.pop("png_bytes")
        # A fresh directory avoids overwriting either media or provenance.
        target = directory / "selected_thumbnail_PRIVATE_DRAFT"
        target.mkdir(mode=0o700, exist_ok=False)
        with (target / export["filename"]).open("xb") as output:
            output.write(preview_bytes)
        with (target / "preview_provenance_PRIVATE.json").open(
                "x", encoding="utf-8") as output:
            json.dump(export, output, ensure_ascii=False, sort_keys=True, indent=2)
            output.write("\n")
        print("Private 1280x720 upscaled frame draft saved; no typography, approval or publishing.")
        return 0
    except (AnimeThumbnailExportError, OSError, ValueError) as exc:
        print(f"Private thumbnail preview not exported: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
