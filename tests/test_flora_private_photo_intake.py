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

    def test_downscale_without_upscale_and_reject_extreme_aspect_ratio(self):
        large = BytesIO()
        Image.new("RGB", (3200, 1600), "white").save(large, format="PNG")
        prepared = prepare_private_flora_photo(large.getvalue(), "image/png")
        self.assertEqual(prepared["sanitized_canvas_px"], [2048, 1024])
        narrow = BytesIO()
        Image.new("RGB", (4096, 400), "white").save(narrow, format="PNG")
        with self.assertRaises(FloraPrivatePhotoError):
            prepare_private_flora_photo(narrow.getvalue(), "image/png")

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


    def test_private_cli_one_step_real_silent_mp4_with_hash_bound_photo(self):
        """Operator can produce an actual private MP4 without a second script."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "original_with_exif.jpg"
            original = _jpeg_with_exif()
            source.write_bytes(original)
            out = root / "private"
            out.mkdir()
            args = [
                sys.executable, "-m", "scripts.prepare_flora_private_photo",
                "--photo", str(source), "--mime", "image/jpeg",
                "--product-id", "gold_kit", "--output-dir", str(out),
                "--rights-attested", "--render-video", "--placement", "story",
            ]
            completed = subprocess.run(args, capture_output=True, text=True, timeout=90)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            self.assertFalse(summary["publication_permitted"])
            self.assertFalse(summary["owner_approved"])
            names = {
                "flora_gold_kit_PRIVATE_photo.png",
                "flora_gold_kit_PRIVATE_photo_provenance.json",
                "flora_gold_kit_story_DRAFT.png",
                "flora_gold_kit_story_DRAFT.mp4",
            }
            self.assertEqual({p.name for p in out.iterdir()}, names)
            provenance = json.loads(
                (out / "flora_gold_kit_PRIVATE_photo_provenance.json").read_text()
            )
            render = provenance["private_render"]
            self.assertEqual(render["audio_status"], "silent_no_music")
            self.assertFalse(render["publication_permitted"])
            self.assertFalse(render["owner_approved"])
            self.assertFalse(render["photo_rights_independently_verified"])
            self.assertFalse(render["current_price_independently_verified"])
            self.assertTrue(render["ffprobe_verified_locally"])
            self.assertEqual(
                provenance["sanitized_photo_sha256"],
                hashlib.sha256((out / "flora_gold_kit_PRIVATE_photo.png").read_bytes()).hexdigest(),
            )
            for kind, filename in (("poster", "flora_gold_kit_story_DRAFT.png"),
                                   ("video", "flora_gold_kit_story_DRAFT.mp4")):
                self.assertEqual(
                    render[kind + "_sha256"],
                    hashlib.sha256((out / filename).read_bytes()).hexdigest(),
                )
            self.assertEqual(summary["video_sha256"], render["video_sha256"])
            self.assertNotIn("original_with_exif.jpg",
                             (out / "flora_gold_kit_PRIVATE_photo_provenance.json").read_text())
            self.assertNotIn(b"PRIVATE CAMERA IDENTIFIER",
                             (out / "flora_gold_kit_PRIVATE_photo.png").read_bytes())
            probed = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries",
                "stream=codec_name,codec_type:format=duration",
                "-of", "json", str(out / "flora_gold_kit_story_DRAFT.mp4"),
            ], capture_output=True, text=True, timeout=15, check=True)
            streams = json.loads(probed.stdout)["streams"]
            self.assertEqual([(s["codec_type"], s["codec_name"]) for s in streams],
                             [("video", "h264")])
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            repeat = subprocess.run(args, capture_output=True, text=True, timeout=90)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})
            self.assertEqual(source.read_bytes(), original)

    def test_private_cli_invalid_photo_never_leaves_partial_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "broken.jpg"
            source.write_bytes(_jpeg_with_exif()[:250])
            out = root / "private"
            out.mkdir()
            result = subprocess.run([
                sys.executable, "-m", "scripts.prepare_flora_private_photo",
                "--photo", str(source), "--mime", "image/jpeg",
                "--product-id", "shampoo", "--output-dir", str(out),
                "--rights-attested", "--render-video",
            ], capture_output=True, text=True, timeout=25)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(out.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
