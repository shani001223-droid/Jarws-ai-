"""Export Task 55's *outline-only* 300-episode manifest; no network or render.

Run from repository root:
  python -m scripts.export_hoshi_anime_chronology --out Hoshi-anime-chronology.json

Output is deliberately create-only: it will never overwrite an existing file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cloud_backend.anime_series import series_manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export proposed anime beat chronology (not scripts)")
    parser.add_argument("--out", help="New UTF-8 JSON file; refuses overwrite")
    args = parser.parse_args(argv)
    payload = json.dumps(series_manifest(), ensure_ascii=False, indent=2) + "\n"
    if args.out:
        target = Path(args.out)
        if target.is_dir():
            parser.error("output must be a new file")
        try:
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
        except FileExistsError:
            parser.error("refusing to overwrite existing chronology")
        except OSError as exc:
            parser.error(f"cannot create output: {type(exc).__name__}")
        print(f"Created outline-only chronology: {target}", file=sys.stderr)
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
