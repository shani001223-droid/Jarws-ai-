"""Create-only private EP003 editorial draft export; no network or media."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from cloud_backend.anime_episode_three import episode_three_script

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export unreviewed EP003 Roman Urdu JSON")
    parser.add_argument("--out", help="New local JSON file; existing paths are never overwritten")
    args = parser.parse_args(argv)
    payload = json.dumps(episode_three_script(), ensure_ascii=False, indent=2) + "\n"
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
        print(f"Created unreviewed EP003 draft: {target}", file=sys.stderr)
    else:
        sys.stdout.write(payload)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
