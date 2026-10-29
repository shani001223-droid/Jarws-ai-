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
            result["video_mp4"], title="نئی کتاب", rights_attested=True)
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
        self.assertEqual(result["title_utf8_not_rendered"], "نئی کتاب")
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

    def test_reject_rehashed_forged_shot_label(self):
        # A misleading header could trick a reviewer even if the image crop is genuine.
        with Image.open(BytesIO(self.sheet)) as image:
            edited = image.convert("RGB")
        edited.putpixel((12, 10), (255, 0, 0))
        output = BytesIO()
        edited.save(output, format="PNG")
        fake_sheet = output.getvalue()
        fake_manifest = copy.deepcopy(self.manifest)
        fake_manifest["thumbnail_candidates"]["png_sha256"] = hashlib.sha256(
            fake_sheet).hexdigest()
        with self.assertRaisesRegex(AnimeThumbnailSelectionError, "shot labels"):
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


    def test_selected_frame_preview_is_actual_verified_video_crop(self):
        from cloud_backend.anime_thumbnail_export import build_private_selected_thumbnail_preview
        selection = self.select(selected_shot=2)
        result = build_private_selected_thumbnail_preview(
            self.manifest, self.video, self.sheet, selection)
        self.assertEqual(result["preview_resolution"], [1280, 720])
        self.assertEqual(result["source_frame_resolution"], [480, 270])
        self.assertTrue(result["upscaled_from_low_resolution"])
        self.assertEqual(result["selected_frame_index"], 180)
        self.assertEqual(result["title_utf8_not_rendered"], "نئی کتاب")
        with Image.open(BytesIO(self.sheet)) as sheet:
            expected = sheet.convert("RGB").crop((480, 30, 960, 300)).resize(
                (1280, 720), Image.Resampling.LANCZOS)
        with Image.open(BytesIO(result["png_bytes"])) as actual:
            self.assertEqual(actual.format, "PNG")
            self.assertEqual(actual.size, (1280, 720))
            self.assertEqual(actual.convert("RGB").tobytes(), expected.tobytes())
        self.assertEqual(hashlib.sha256(result["png_bytes"]).hexdigest(),
                         result["png_sha256"])
        for flag in ("typography_added", "final_thumbnail_designed",
                     "owner_approved", "release_authorized", "publication_permitted"):
            self.assertFalse(result[flag])

    def test_preview_rejects_forged_or_mismatched_selection(self):
        from cloud_backend.anime_thumbnail_export import (
            AnimeThumbnailExportError, build_private_selected_thumbnail_preview)
        original = self.select()
        for field, replacement in (
            ("selected_frame_index", 60),
            ("source_video_sha256", "0" * 64),
            ("owner_approved", True),
            ("publication_permitted", True),
        ):
            forged = copy.deepcopy(original)
            forged[field] = replacement
            with self.subTest(field=field), self.assertRaises(AnimeThumbnailExportError):
                build_private_selected_thumbnail_preview(
                    self.manifest, self.video, self.sheet, forged)
        with self.assertRaises(AnimeThumbnailExportError):
            build_private_selected_thumbnail_preview(
                self.manifest, self.video, self.sheet, {"selected_shot": 1})
        with self.assertRaises(AnimeThumbnailExportError):
            build_private_selected_thumbnail_preview(
                self.manifest, self.video, b"fake-png" * 100, original)

    def test_preview_cli_create_only_no_final_or_upload(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "pilot"
            directory.mkdir()
            (directory / "manifest.json").write_text(
                json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            (directory / "hoshi_anime_animatic_DRAFT.mp4").write_bytes(self.video)
            (directory / "hoshi_thumbnail_candidates_DRAFT.png").write_bytes(self.sheet)
            (directory / "hoshi_thumbnail_selection_PRIVATE.json").write_text(
                json.dumps(self.select(selected_shot=1), ensure_ascii=False),
                encoding="utf-8")
            command = [sys.executable, "-m", "scripts.export_hoshi_anime_thumbnail",
                       "--draft-dir", str(directory)]
            first = subprocess.run(command, capture_output=True, text=True, timeout=90)
            self.assertEqual(first.returncode, 0, first.stderr)
            target = directory / "selected_thumbnail_PRIVATE_DRAFT"
            preview = target / "hoshi_selected_thumbnail_DRAFT.png"
            provenance = json.loads(
                (target / "preview_provenance_PRIVATE.json").read_text(encoding="utf-8"))
            original_bytes = preview.read_bytes()
            self.assertEqual(provenance["selected_shot"], 1)
            self.assertEqual(provenance["png_sha256"],
                             hashlib.sha256(original_bytes).hexdigest())
            self.assertFalse(provenance["publication_permitted"])
            second = subprocess.run(command, capture_output=True, text=True, timeout=90)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(preview.read_bytes(), original_bytes)


    def _local_font_bytes(self):
        from PIL import ImageFont
        font = ImageFont.truetype("DejaVuSans.ttf", 24)
        return Path(font.path).read_bytes()

    def test_private_titled_draft_renders_real_pixels_and_retains_release_denial(self):
        from PIL import features
        from cloud_backend.anime_thumbnail_export import build_private_selected_thumbnail_preview
        from cloud_backend.anime_thumbnail_title import render_private_titled_thumbnail
        if not features.check("raqm"):
            self.skipTest("RAQM unavailable: must fail closed in production")
        preview = build_private_selected_thumbnail_preview(
            self.manifest, self.video, self.sheet, self.select())
        result = render_private_titled_thumbnail(
            preview, self._local_font_bytes(), font_rights_attested=True)
        self.assertEqual(result["title_utf8_rendered"], "نئی کتاب")
        self.assertEqual(result["title_direction"], "rtl")
        self.assertEqual(result["font_shaping_engine"], "libraqm")
        self.assertTrue(result["font_unicode_cmap_coverage_verified"])
        self.assertTrue(result["typography_added"])
        self.assertFalse(result["glyph_coverage_independently_verified"])
        self.assertFalse(result["owner_approved"])
        self.assertFalse(result["publication_permitted"])
        self.assertEqual(hashlib.sha256(result["png_bytes"]).hexdigest(),
                         result["png_sha256"])
        with Image.open(BytesIO(result["png_bytes"])) as rendered:
            self.assertEqual(rendered.size, (1280, 720))
            self.assertNotEqual(rendered.convert("RGB").tobytes(),
                                Image.open(BytesIO(preview["png_bytes"])).convert("RGB").tobytes())
        for text, direction in (("می\u200cخواهم", "rtl"), ("Raat Ki Kahani", "ltr")):
            # Rendering exercise only: real CLI always derives title from verified manifest.
            sample = dict(preview, title_utf8_not_rendered=text)
            draft = render_private_titled_thumbnail(
                sample, self._local_font_bytes(), font_rights_attested=True)
            self.assertEqual(draft["title_direction"], direction)
            self.assertFalse(draft["glyph_coverage_independently_verified"])

    def test_missing_urdu_and_devanagari_font_glyphs_fail_closed(self):
        from cloud_backend.anime_thumbnail_export import build_private_selected_thumbnail_preview
        from cloud_backend.anime_thumbnail_title import (
            AnimeThumbnailTitleError, render_private_titled_thumbnail)
        preview = build_private_selected_thumbnail_preview(
            self.manifest, self.video, self.sheet, self.select())
        # DejaVu Sans has Arabic coverage but not Urdu U+06C1 or Devanagari.
        for title in ("نئی کہانی", "नई कहानी"):
            with self.subTest(title=title), self.assertRaisesRegex(
                    AnimeThumbnailTitleError, "Font lacks required"):
                render_private_titled_thumbnail(
                    dict(preview, title_utf8_not_rendered=title),
                    self._local_font_bytes(), font_rights_attested=True)

    def test_titled_draft_fails_closed_on_invalid_font_preview_or_rights(self):
        from PIL import features
        from cloud_backend.anime_thumbnail_export import build_private_selected_thumbnail_preview
        from cloud_backend.anime_thumbnail_title import (
            AnimeThumbnailTitleError, render_private_titled_thumbnail)
        if not features.check("raqm"):
            self.skipTest("RAQM unavailable: must fail closed in production")
        preview = build_private_selected_thumbnail_preview(
            self.manifest, self.video, self.sheet, self.select())
        font = self._local_font_bytes()
        for data, rights in ((b"not-a-font" * 200, True), (font, False),
                             (b"x" * 8_000_001, True)):
            with self.subTest(rights=rights, size=len(data)), self.assertRaises(
                    AnimeThumbnailTitleError):
                render_private_titled_thumbnail(
                    preview, data, font_rights_attested=rights)
        for changes in ({"owner_approved": True},
                        {"png_sha256": "0" * 64},
                        {"title_utf8_not_rendered": "Unsafe\\nTitle"},
                        {"title_utf8_not_rendered": "हिंदी اردو"}):
            forged = dict(preview, **changes)
            with self.subTest(changes=changes), self.assertRaises(AnimeThumbnailTitleError):
                render_private_titled_thumbnail(
                    forged, font, font_rights_attested=True)

    def test_title_metadata_rejects_spoofing_but_preserves_urdu_hindi_joiners(self):
        from cloud_backend.anime_thumbnail import AnimeThumbnailError, _validate_title
        for unsafe in ("Unsafe\\nTitle", "Unsafe\nTitle", "Unsafe\u2028Title",
                       "Unsafe\u2029Title", "Unsafe\u202aTitle",
                       "Unsafe\u2060Title", "Unsafe\ud800Title",
                       "Cafe\u0301", "Bad\x7fTitle"):
            with self.subTest(unsafe=repr(unsafe)), self.assertRaises(AnimeThumbnailError):
                _validate_title(unsafe)
        for safe in ("نئی کہانی", "नई कहानी", "Raat Ki Kahani",
                     "می\u200cخواهم", "क्\u200dष"):
            with self.subTest(safe=safe):
                _validate_title(safe)

    def test_titled_cli_real_mp4_create_only_and_no_upload(self):
        from PIL import features, ImageFont
        if not features.check("raqm"):
            self.skipTest("RAQM unavailable: must fail closed in production")
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "pilot"
            directory.mkdir()
            (directory / "manifest.json").write_text(
                json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            (directory / "hoshi_anime_animatic_DRAFT.mp4").write_bytes(self.video)
            (directory / "hoshi_thumbnail_candidates_DRAFT.png").write_bytes(self.sheet)
            (directory / "hoshi_thumbnail_selection_PRIVATE.json").write_text(
                json.dumps(self.select(), ensure_ascii=False), encoding="utf-8")
            font = Path(root) / "local-operator-font.ttf"
            font.write_bytes(self._local_font_bytes())
            command = [sys.executable, "-m", "scripts.design_hoshi_anime_thumbnail",
                       "--draft-dir", str(directory), "--font", str(font)]
            without_rights = subprocess.run(command, capture_output=True, text=True, timeout=90)
            self.assertNotEqual(without_rights.returncode, 0)
            self.assertFalse((directory / "titled_thumbnail_PRIVATE_DRAFT").exists())
            command.append("--font-rights-attested")
            first = subprocess.run(command, capture_output=True, text=True, timeout=90)
            self.assertEqual(first.returncode, 0, first.stderr)
            target = directory / "titled_thumbnail_PRIVATE_DRAFT"
            provenance = json.loads(
                (target / "typography_provenance_PRIVATE.json").read_text(encoding="utf-8"))
            png = target / provenance["filename"]
            original_bytes = png.read_bytes()
            self.assertEqual(hashlib.sha256(original_bytes).hexdigest(),
                             provenance["png_sha256"])
            self.assertFalse(provenance["publication_permitted"])
            second = subprocess.run(command, capture_output=True, text=True, timeout=90)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(png.read_bytes(), original_bytes)



if __name__ == "__main__":
    unittest.main()
