"""Operator-only private thumbnail candidate selection. No publishing or upload."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_thumbnail_selection import (
    AnimeThumbnailSelectionError, record_private_thumbnail_selection,
)


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file() or not 1 <= path.stat().st_size <= limit:
        raise AnimeThumbnailSelectionError("Missing or oversized private draft artifact.")
    return path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description="Choose an inspected private anime thumbnail candidate")
    parser.add_argument("--draft-dir", required=True, help="Existing offline pilot output directory")
    parser.add_argument("--shot", required=True, type=int, choices=(1, 2, 3),
                        help="Which of the three actual decoded candidate frames")
    parser.add_argument("--note", required=True, help="Editorial reason for this choice (8–500 characters)")
    parser.add_argument("--inspected-contact-sheet", action="store_true",
                        help="Attest actual manual inspection; not owner approval")
    args = parser.parse_args()
    try:
        directory = Path(args.draft_dir)
        try:
            manifest = json.loads(_read(directory / "manifest.json", 120_000).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise AnimeThumbnailSelectionError("Invalid UTF-8 private draft manifest.") from None
        selection = record_private_thumbnail_selection(
            manifest,
            _read(directory / "hoshi_anime_animatic_DRAFT.mp4", 15_000_000),
            _read(directory / "hoshi_thumbnail_candidates_DRAFT.png", 3_000_000),
            selected_shot=args.shot, note=args.note,
            inspected=args.inspected_contact_sheet)
        # Exclusive create: preserve previous editorial choice and original artifacts.
        with (directory / "hoshi_thumbnail_selection_PRIVATE.json").open(
                "x", encoding="utf-8") as output:
            json.dump(selection, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")
        print("Private candidate selected; no final design, approval, upload or release.")
        return 0
    except (AnimeThumbnailSelectionError, OSError, ValueError) as exc:
        print(f"Private thumbnail selection not recorded: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
