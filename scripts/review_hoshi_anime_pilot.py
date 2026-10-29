"""Record a human's offline private QC decision; never upload or authorize release."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_review_gate import AnimeReviewGateError, record_private_review


def _read(path: Path, limit: int) -> bytes:
    if not path.is_file() or not 1 <= path.stat().st_size <= limit:
        raise AnimeReviewGateError("Missing or oversized private draft artifact.")
    return path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline Hoshi private animatic human QC")
    parser.add_argument("--draft-dir", required=True, help="Existing private pilot directory")
    parser.add_argument("--verdict", required=True, choices=("private_qc_pass", "needs_revision"))
    parser.add_argument("--shot-note", action="append", required=True, help="One inspected shot note, in order; exactly 3")
    parser.add_argument("--inspected-video-and-sheet", action="store_true",
                        help="Confirm actual personal inspection; not automatic validation")
    args = parser.parse_args()
    try:
        directory = Path(args.draft_dir)
        manifest_bytes = _read(directory / "manifest.json", 120_000)
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise AnimeReviewGateError("Invalid draft manifest JSON.") from None
        result = record_private_review(
            manifest,
            _read(directory / "hoshi_anime_animatic_DRAFT.mp4", 15_000_000),
            _read(directory / "hoshi_anime_animatic_DRAFT.srt", 20_000),
            _read(directory / "hoshi_mouth_review_DRAFT.png", 3_000_000),
            verdict=args.verdict, shot_notes=args.shot_note,
            inspected=args.inspected_video_and_sheet)
        # Exclusive creation: no silent alteration of any previous QC record.
        with (directory / "hoshi_private_qc_review.json").open("x", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, indent=2, sort_keys=True)
            out.write("\n")
        print("Private QC recorded locally; NO release or upload authorized.")
        return 0
    except (AnimeReviewGateError, OSError, ValueError) as exc:
        print(f"Private QC not recorded: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
