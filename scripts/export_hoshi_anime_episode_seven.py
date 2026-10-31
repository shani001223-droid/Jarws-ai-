"""Private create-only EP007 JSON exporter; no network, media or publication."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cloud_backend.anime_episode_seven import episode_seven_script


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export unreviewed EP007 Roman Urdu draft")
    parser.add_argument("--out", help="New local JSON file; refuses overwrite")
    args = parser.parse_args(argv)
    payload = json.dumps(episode_seven_script(), ensure_ascii=False, indent=2) + "\n"
    if args.out:
        target = Path(args.out)
        if target.is_dir():
            parser.error("output must be a new file")
        try:
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
        except FileExistsError:
            parser.error("refusing to overwrite existing episode")
        except OSError as exc:
            parser.error(f"cannot create output: {type(exc).__name__}")
        print(f"Created unreviewed EP007 draft: {target}", file=sys.stderr)
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
