"""Real image and private CLI regression for Flora Task 43 photo intake."""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from cloud_backend.flora_catalog import FloraCatalogError, inspect_owner_photo
from cloud_backend.flora_private_photo_intake import (
    FloraPrivatePhotoError, prepare_private_flora_photo,
)
from cloud_backend.flora_photo_posters import render_flora_photo_preview
from cloud_backend.flora_video_ads import render_flora_video_draft


def _jpeg_with_exif() -> bytes:
    image = Image.new("RGB", (640, 800), (70, 120, 160))
    exif = Image.Exif()
    exif[274] = 6  # EXIF rotation: display width and height swapped
    exif[271] = "PRIVATE CAMERA IDENTIFIER"
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


class FloraPrivatePhotoIntakeTests(unittest.TestCase):
    def test_exif_orientation_and_private_metadata_scrub(self):
        original = _jpeg_with_exif()
        self.assertEqual(inspect_owner_photo(original, "image/jpeg")["width"], 640)
        result = prepare_private_flora_photo(original, "image/jpeg")
        self.assertEqual(result["source_photo_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(result["sanitized_canvas_px"], [800, 640])
        self.assertTrue(result["metadata_removed"])
        self.assertFalse(result["approved_for_publication"])
        self.assertFalse(result["owner_rights_independently_verified"])
        self.assertFalse(result["publication_permitted"])
        cleaned = result["sanitized_png_bytes"]
        self.assertEqual(result["sanitized_photo_sha256"], hashlib.sha256(cleaned).hexdigest())
        self.assertNotIn(b"PRIVATE CAMERA IDENTIFIER", cleaned)
        with Image.open(BytesIO(cleaned)) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.mode, "RGB")
            self.assertFalse(image.info)
            self.assertEqual(image.size, (800, 640))

    def test_private_photo_reaches_real_poster_and_mp4_without_approval(self):
        prepared = prepare_private_flora_photo(_jpeg_with_exif(), "image/jpeg")
        photo = prepared["sanitized_png_bytes"]
        poster = render_flora_photo_preview("shampoo", photo, "image/png")
        self.assertEqual(poster["source_photo_sha256"],
                         prepared["sanitized_photo_sha256"])
        self.assertFalse(poster["approved_for_publication"])
        video = render_flora_video_draft("shampoo", photo, "image/png", "feed")
        self.assertEqual(video["codec"], "h264")
        self.assertEqual(video["audio_status"], "silent_no_music")
        self.assertEqual(video["source_photo_sha256"],
                         prepared["sanitized_photo_sha256"])
        self.assertFalse(video["approved_for_publication"])
        self.assertFalse(video["published"])
        self.assertTrue(video["video_mp4"].startswith(b"\x00\x00"))

    def test_animated_apng_and_truncated_jpeg_fail_closed(self):
        a = Image.new("RGB", (640, 640), "red")
        b = Image.new("RGB", (640, 640), "blue")
        buffer = BytesIO()
        a.save(buffer, format="PNG", save_all=True, append_images=[b],
               duration=100, loop=0)
        animated = buffer.getvalue()
        with self.assertRaises(FloraCatalogError):
            inspect_owner_photo(animated, "image/png")
        with self.assertRaises(FloraPrivatePhotoError):
            prepare_private_flora_photo(animated, "image/png")
        truncated = _jpeg_with_exif()[:250]
        with self.assertRaises(FloraCatalogError):
            inspect_owner_photo(truncated, "image/jpeg")

    def test_private_cli_create_only_and_no_rights_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "owner.jpg"
            source.write_bytes(_jpeg_with_exif())
            out = root / "private"
            out.mkdir()
            args = [sys.executable, "-m", "scripts.prepare_flora_private_photo",
                    "--photo", str(source), "--mime", "image/jpeg",
                    "--product-id", "gold_kit", "--output-dir", str(out)]
            denied = subprocess.run(args, capture_output=True, text=True, timeout=25)
            self.assertNotEqual(denied.returncode, 0)
            self.assertEqual(list(out.iterdir()), [])
            accepted = subprocess.run(args + ["--rights-attested"],
                                      capture_output=True, text=True, timeout=25)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            report = json.loads(accepted.stdout)
            self.assertFalse(report["publication_permitted"])
            self.assertEqual(len(list(out.iterdir())), 2)
            meta = json.loads((out / "flora_gold_kit_PRIVATE_photo_provenance.json").read_text())
            self.assertTrue(meta["caller_rights_attested_not_independently_verified"])
            self.assertFalse(meta["owner_approved"])
            self.assertNotIn("sanitized_png_bytes", meta)
            self.assertEqual(source.read_bytes(), _jpeg_with_exif())
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            repeated = subprocess.run(args + ["--rights-attested"],
                                      capture_output=True, text=True, timeout=25)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})


if __name__ == "__main__":
    unittest.main()
