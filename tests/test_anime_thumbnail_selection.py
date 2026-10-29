"""Real H.264 decoded-frame regressions for private thumbnail editorial selection."""
from __future__ import annotations

import copy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from cloud_backend.anime_pilot_animatic import render_private_animatic
from cloud_backend.anime_thumbnail import build_private_thumbnail_candidates
from cloud_backend.anime_thumbnail_selection import (
    AnimeThumbnailSelectionError, record_private_thumbnail_selection,
)


def original_stills():
    stills = []
    for index in range(3):
        image = Image.new("RGB", (640, 360), (35 + 35 * index, 65, 100))
        output = BytesIO()
        image.save(output, format="PNG")
        stills.append(output.getvalue())
    return stills


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Requires actual offline FFmpeg H.264 encoding and decoding")
class PrivateThumbnailSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = render_private_animatic(
            original_stills(), ["Raat ki kahani", "Aaj ka safar", "Nayi subah"],
            image_rights_attested=True)
        thumbnails = build_private_thumbnail_candidates(
            result["video_mp4"], title="نئی کہانی", rights_attested=True)
        cls.video = result["video_mp4"]
        cls.sheet = thumbnails["png_bytes"]
        cls.manifest = {k: v for k, v in result.items()
                        if k not in ("video_mp4", "subtitles_srt")}
        cls.manifest["thumbnail_candidates"] = {
            k: v for k, v in thumbnails.items() if k != "png_bytes"}

    def select(self, manifest=None, video=None, sheet=None, **kwargs):
        return record_private_thumbnail_selection(
            self.manifest if manifest is None else manifest,
            self.video if video is None else video,
            self.sheet if sheet is None else sheet,
            selected_shot=kwargs.get("selected_shot", 2),
            note=kwargs.get("note", "Shot two has the clearest original composition."),
            inspected=kwargs.get("inspected", True))

    def test_real_mp4_all_frames_match_and_never_grants_release(self):
        result = self.select()
        self.assertEqual(result["selected_frame_index"], 180)
        self.assertTrue(result["all_three_candidate_frames_independently_verified"])
        self.assertEqual(result["title_utf8_not_rendered"], "نئی کہانی")
        for key in ("owner_approved", "release_authorized",
                    "publication_permitted", "final_thumbnail_designed"):
            self.assertFalse(result[key])

    def test_reject_bad_selection_and_false_inspection(self):
        for kwargs in ({"selected_shot": 0}, {"selected_shot": True},
                       {"inspected": False}, {"note": "short"},
                       {"note": "Some note\nunsafe"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(AnimeThumbnailSelectionError):
                self.select(**kwargs)

    def test_reject_rehashed_forged_contact_pixels(self):
        with Image.open(BytesIO(self.sheet)) as image:
            edited = image.convert("RGB")
        edited.putpixel((10, 40), (255, 0, 0))
        output = BytesIO()
        edited.save(output, format="PNG")
        fake_sheet = output.getvalue()
        fake_manifest = copy.deepcopy(self.manifest)
        fake_manifest["thumbnail_candidates"]["png_sha256"] = hashlib.sha256(
            fake_sheet).hexdigest()
        with self.assertRaisesRegex(AnimeThumbnailSelectionError, "Contact pixels"):
            self.select(manifest=fake_manifest, sheet=fake_sheet)

    def test_reject_rehashed_forged_frame_metadata_and_media(self):
        fake = copy.deepcopy(self.manifest)
        fake["thumbnail_candidates"]["candidate_frames"][0][
            "decoded_frame_rgb_sha256"] = "0" * 64
        with self.assertRaises(AnimeThumbnailSelectionError):
            self.select(manifest=fake)
        fake = copy.deepcopy(self.manifest)
        fake["thumbnail_candidates"]["media_qc"]["duration_seconds"] = 99
        with self.assertRaises(AnimeThumbnailSelectionError):
            self.select(manifest=fake)
        with self.assertRaises(AnimeThumbnailSelectionError):
            self.select(video=b"not-an-mp4" * 100)

    def test_cli_create_only_and_no_owner_approval(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "draft"
            directory.mkdir()
            (directory / "manifest.json").write_text(
                json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            (directory / "hoshi_anime_animatic_DRAFT.mp4").write_bytes(self.video)
            (directory / "hoshi_thumbnail_candidates_DRAFT.png").write_bytes(self.sheet)
            command = [
                sys.executable, "-m", "scripts.select_hoshi_anime_thumbnail",
                "--draft-dir", str(directory), "--shot", "3",
                "--note", "Shot three is strongest for a private design draft.",
                "--inspected-contact-sheet",
            ]
            first = subprocess.run(command, capture_output=True, text=True, timeout=70)
            self.assertEqual(first.returncode, 0, first.stderr)
            path = directory / "hoshi_thumbnail_selection_PRIVATE.json"
            original = path.read_bytes()
            self.assertEqual(json.loads(original)["selected_frame_index"], 300)
            second = subprocess.run(command, capture_output=True, text=True, timeout=70)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
