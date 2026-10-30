"""Operator-only offline Flora photo intake; no network or publication.

Usage:
  python -m scripts.prepare_flora_private_photo --photo ./my-photo.jpg \
    --mime image/jpeg --product-id shampoo --output-dir ./private \
    --rights-attested

Only a sanitized PNG and an explicitly unapproved provenance JSON are written.
The original image is never copied. Output names are fixed and create-only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat

from cloud_backend.flora_catalog import catalogue_snapshot
from cloud_backend.flora_private_photo_intake import prepare_private_flora_photo


def _read_local_photo(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 8_000_000:
            raise ValueError("Source must be a bounded regular photo file.")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read(8_000_001)
        if len(data) != info.st_size:
            raise ValueError("Source photo changed or exceeds size limit.")
        return data
    finally:
        os.close(fd)


def _create_private_files(directory: Path, files: dict[str, bytes]) -> None:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Output must be an existing non-symlink private directory.")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    dirfd = os.open(directory, flags)
    created: list[str] = []
    try:
        for name, data in files.items():
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=dirfd)
            created.append(name)
            with os.fdopen(fd, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
    except Exception:
        # Roll back only files newly created by this invocation; never replace
        # or remove any pre-existing operator asset.
        for name in created:
            os.unlink(name, dir_fd=dirfd)
        raise
    finally:
        os.close(dirfd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare private Flora photo (never publish)")
    parser.add_argument("--photo", type=Path, required=True)
    parser.add_argument("--mime", choices=["image/png", "image/jpeg", "image/webp"],
                        required=True)
    parser.add_argument("--product-id", choices=["gold_kit", "shampoo"], required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rights-attested", action="store_true")
    args = parser.parse_args(argv)
    if not args.rights_attested:
        parser.error("Explicit operator photo-rights attestation is required.")
    catalogue_snapshot(args.product_id)  # fail on stale/changed product prices
    photo = prepare_private_flora_photo(_read_local_photo(args.photo), args.mime)
    png = photo.pop("sanitized_png_bytes")
    photo.update({
        "product_id": args.product_id,
        "caller_rights_attested_not_independently_verified": True,
        "owner_approved": False,
        "published": False,
        "uploaded": False,
        "next_step": "Private draft poster/MP4 only; confirm photo, price and rights.",
    })
    stem = "flora_" + args.product_id + "_PRIVATE_photo"
    names = {
        stem + ".png": png,
        stem + "_provenance.json": (json.dumps(photo, sort_keys=True, ensure_ascii=False,
                                               indent=2) + "\n").encode("utf-8"),
    }
    _create_private_files(args.output_dir, names)
    print(json.dumps({
        "status": photo["status"], "product_id": args.product_id,
        "sanitized_photo_sha256": photo["sanitized_photo_sha256"],
        "owner_approved": False, "publication_permitted": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
