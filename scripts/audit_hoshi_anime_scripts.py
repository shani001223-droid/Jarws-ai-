"""Private, create-only Task 56 QA report; no network or media output."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from cloud_backend.anime_script_readiness import build_readiness_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Audit Hoshi EP001-EP003 draft readiness")
    parser.add_argument("--out", help="New local JSON path; never overwrite")
    args = parser.parse_args(argv)
    payload = json.dumps(build_readiness_report(), ensure_ascii=False, indent=2) + "\n"
    if not args.out:
        sys.stdout.write(payload)
        return 0
    path = Path(args.out)
    if path.is_dir():
        parser.error("output must be a new file")
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
    except FileExistsError:
        parser.error("refusing to overwrite existing report")
    except OSError as exc:
        parser.error(f"cannot create output: {type(exc).__name__}")
    print(f"Created private editorial QA report: {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
