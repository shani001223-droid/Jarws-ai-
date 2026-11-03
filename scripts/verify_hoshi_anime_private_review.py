"""Read-only offline integrity check for the PRIVATE Hoshi anime review bundle.

Never approves, uploads, edits or publishes media. Use before human review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_private_review_verify import (
    AnimePrivateBundleError, verify_private_review_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify private Hoshi subtitle review media without changing it")
    parser.add_argument("--draft-dir", required=True,
                        help="Original local draft directory containing private bundle")
    args = parser.parse_args()
    try:
        result = verify_private_review_bundle(
            Path(args.draft_dir) / "subtitle_burnin_PRIVATE_DRAFT")
    except AnimePrivateBundleError as exc:
        print(f"Private review bundle NOT verified: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
