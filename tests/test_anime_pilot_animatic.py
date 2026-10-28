"""Anime Studio real offline MP4 pilot and fail-closed rights/QC contracts."""
from __future__ import annotations

import copy
import hashlib
from io import BytesIO
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from cloud_backend import anime_pilot_animatic as pilot


def original_stills():
    """Synthetic shapes created here; no third-party anime artwork."""
    result = []
    for index in range(3):
        image = Image.new("RGB", (640, 360), (20 + index * 20, 30, 60))
        pen = ImageDraw.Draw(image)
        pen.ellipse((180, 35, 460, 320), fill=(90 + index * 30, 120, 170))
        pen.polygon(((320, 65), (250, 220), (390, 220)), fill=(15, 20, 35))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        result.append(buffer.getvalue())
    return result


CAPTIONS = ["Raat ka aasmaan abhi khamosh hai.",
            "Ek naya raaz hamare saamne hai.",
            "Kal sach ki talaash shuru hogi."]


class AnimePilotAnimaticTests(unittest.TestCase):
    def test_24_production_roles_and_30_second_srt(self):
        self.assertEqual(len(pilot.ROLES), 24)
        srt = pilot._captions_to_srt(CAPTIONS).decode("utf-8")
        self.assertIn("00:00:00,000 --> 00:00:10,000", srt)
        self.assertIn("00:00:20,000 --> 00:00:30,000", srt)
        self.assertIn(CAPTIONS[2], srt)
        self.assertNotIn("\\n", srt)

    def test_hindi_urdu_utf8_subtitles_are_not_transliterated(self):
        captions = ["یہ رات خاموش ہے۔", "आज एक नया राज़ सामने आया।",
                    "Kal hum sach dhoondenge."]
        encoded = pilot._captions_to_srt(captions)
        decoded = encoded.decode("utf-8")
        for line in captions:
            self.assertIn(line, decoded)
        self.assertEqual(decoded.count(" --> "), 3)

    def test_reject_rights_bypass_bad_assets_and_caption_injection(self):
        images = original_stills()
        for kwargs in (
            {},
            {"image_rights_attested": 1},
            {"image_rights_attested": True, "audio_rights_attested": True},
            {"image_rights_attested": True, "audio_wav": b"RIFFbad"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(pilot.AnimePilotError):
                pilot.render_private_animatic(images, CAPTIONS, **kwargs)
        for bad in (b"bad", b"0" * (pilot.MAX_IMAGE_BYTES + 1)):
            with self.subTest(bad=len(bad)), self.assertRaises(pilot.AnimePilotError):
                pilot.render_private_animatic([bad, *images[1:]], CAPTIONS,
                                              image_rights_attested=True)
        for bad in ("<script>evil</script>", "Hello\nworld", "safe\u202eunsafe",
                    "", "x" * 181):
            with self.subTest(bad=bad), self.assertRaises(pilot.AnimePilotError):
                pilot.render_private_animatic(images, [bad, *CAPTIONS[1:]],
                                              image_rights_attested=True)

    def test_missing_ffmpeg_fails_closed(self):
        with patch.object(pilot.shutil, "which", return_value=None):
            with self.assertRaisesRegex(pilot.AnimePilotError, "FFmpeg"):
                pilot.render_private_animatic(original_stills(), CAPTIONS,
                                              image_rights_attested=True)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real MP4 acceptance requires offline ffmpeg/ffprobe")
    def test_real_mp4_with_independent_probe_and_no_false_approval(self):
        originals = original_stills()
        output = pilot.render_private_animatic(originals, CAPTIONS,
                                               image_rights_attested=True)
        self.assertEqual(output["video_mp4"][4:8], b"ftyp")
        self.assertEqual(output["video_sha256"],
                         hashlib.sha256(output["video_mp4"]).hexdigest())
        self.assertEqual(output["source_image_sha256"],
                         [hashlib.sha256(x).hexdigest() for x in originals])
        self.assertEqual(output["duration_seconds"], 30)
        self.assertEqual(output["resolution"], [480, 270])
        self.assertEqual(output["frame_rate"], 12)
        self.assertTrue(output["actual_mp4_rendered"])
        self.assertEqual(output["stage"], "private_storyboard_animatic_only")
        self.assertEqual(output["audio_status"], "silent_no_music")
        self.assertIn("DRAFT", output["filename"])
        self.assertEqual(output["subtitles_srt"], pilot._captions_to_srt(CAPTIONS))
        for field in ("full_character_animation", "hindi_urdu_voice_recorded",
                      "subtitles_embedded", "source_rights_independently_verified",
                      "owner_approved", "published", "uploaded"):
            self.assertFalse(output[field], field)


    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "CLI integration requires real offline FFmpeg")
    def test_cli_creates_private_files_once_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index, data in enumerate(original_stills()):
                path = root / f"shot{index}.png"
                path.write_bytes(data)
                paths.append(path)
            out = root / "draft"
            cmd = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
            for path in paths:
                cmd += ["--shot", str(path)]
            for caption in CAPTIONS:
                cmd += ["--caption", caption]
            cmd += ["--image-rights-attested", "--out", str(out)]
            first = subprocess.run(cmd, text=True, capture_output=True, timeout=110)
            self.assertEqual(first.returncode, 0, first.stderr)
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["owner_approved"])
            self.assertTrue(manifest["actual_mp4_rendered"])
            mp4 = (out / manifest["filename"]).read_bytes()
            self.assertEqual(hashlib.sha256(mp4).hexdigest(), manifest["video_sha256"])
            self.assertEqual((out / "hoshi_anime_animatic_DRAFT.srt").read_bytes(),
                             pilot._captions_to_srt(CAPTIONS))
            second = subprocess.run(cmd, text=True, capture_output=True, timeout=110)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual((out / manifest["filename"]).read_bytes(), mp4)


if __name__ == "__main__":
    unittest.main()
