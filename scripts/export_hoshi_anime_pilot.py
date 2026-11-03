"""Export Task 56's unreviewed EP001 pilot table-read draft as a local JSON file.

Run: python -m scripts.export_hoshi_anime_pilot --out Hoshi-EP001-draft.json
Refuses to overwrite existing files. No network, audio, model or publication.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cloud_backend.anime_scripts import pilot_script


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export unreviewed Roman Urdu pilot draft (not media)")
    parser.add_argument("--out", help="New UTF-8 JSON file; refuses overwrite")
    args = parser.parse_args(argv)
    payload = json.dumps(pilot_script(), ensure_ascii=False, indent=2) + "\n"
    if args.out:
        target = Path(args.out)
        if target.is_dir():
            parser.error("output must be a new file")
        try:
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
        except FileExistsError:
            parser.error("refusing to overwrite existing pilot")
        except OSError as exc:
            parser.error(f"cannot create output: {type(exc).__name__}")
        print(f"Created unreviewed pilot draft: {target}", file=sys.stderr)
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
