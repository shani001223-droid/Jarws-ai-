"""Operator-only, read-only verifier for an existing private Flora MP4 draft.

Example:
  python -m scripts.verify_flora_private_bundle --draft-dir ./private \
    --product-id shampoo --placement story

Never approves, uploads, modifies, publishes or purchases anything.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cloud_backend.flora_private_bundle_verify import verify_private_flora_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify an offline Flora DRAFT bundle")
    parser.add_argument("--draft-dir", type=Path, required=True)
    parser.add_argument("--product-id", choices=["gold_kit", "shampoo"], required=True)
    parser.add_argument("--placement", choices=["story", "feed"], default="story")
    args = parser.parse_args(argv)
    result = verify_private_flora_bundle(args.draft_dir, args.product_id, args.placement)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
