"""Real encoded-MP4 regression for private Hindi/Urdu SRT visual review."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageFont

from cloud_backend.anime_subtitle_preview import (
    AnimeSubtitlePreviewError, build_private_subtitle_contact_sheet,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SubtitleVisualReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="hoshi-subtitle-preview-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        path = Path(cls.temp.name) / "real.mp4"
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
             "-f", "lavfi", "-i", "color=c=navy:s=480x270:r=12:d=30",
             "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000:duration=30",
             "-t", "30", "-c:v", "libx264", "-preset", "ultrafast",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "32k",
             "-shortest", "-y", str(path)],
            capture_output=True, timeout=60, check=False)
        if result.returncode:
            raise AssertionError(result.stderr[:500])
        cls.video = path.read_bytes()
        cls.font_path = Path(ImageFont.truetype("DejaVuSans.ttf", 18).path)
        cls.font = cls.font_path.read_bytes()

    def setUp(self):
        self.captions = ["سلام", "Kya haal hai", "Theek hun"]
        self.srt = "".join(
            f"{i+1}\n00:00:{i*10:02d},000 --> 00:00:{(i+1)*10:02d},000\n"
            f"{caption}\n\n"
            for i, caption in enumerate(self.captions)).encode("utf-8")
        storyboard = {
            "schema_version": 1, "language": "ur",
            "shots": [{"shot_id": f"shot{i}", "caption": caption}
                      for i, caption in enumerate(self.captions)],
        }
        plan_bytes = json.dumps(storyboard, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":")).encode("utf-8")
        self.manifest = {
            "stage": "private_storyboard_animatic_only",
            "actual_mp4_rendered": True, "owner_approved": False,
            "published": False, "uploaded": False,
            "video_sha256": digest(self.video),
            "subtitles_sha256": digest(self.srt),
            "subtitle_timing_source": "fixed_ten_second_shots",
            "storyboard_handoff": {
                "plan": storyboard, "plan_sha256": digest(plan_bytes),
            },
        }

    def render(self, **overrides):
        values = dict(manifest=self.manifest, video=self.video,
                      subtitles=self.srt, font_bytes=self.font,
                      font_rights_attested=True)
        values.update(overrides)
        return build_private_subtitle_contact_sheet(**values)

    def test_real_mp4_urdu_and_roman_urdu_caption_pixels(self):
        result = self.render()
        self.assertEqual(result["status"],
                         "actual_mp4_frames_with_shaped_srt_private_review_only")
        self.assertEqual(result["source_video_sha256"], digest(self.video))
        self.assertEqual(result["source_subtitles_sha256"], digest(self.srt))
        self.assertEqual(result["png_sha256"], digest(result["png_bytes"]))
        self.assertEqual(result["resolution"], [1440, 300])
        self.assertEqual([s["decoded_frame_index"] for s in result["samples"]],
                         [60, 180, 300])
        self.assertEqual(result["samples"][0]["caption_direction"], "rtl")
        self.assertEqual(result["samples"][1]["caption_direction"], "ltr")
        self.assertTrue(all(s["text_ink_bbox_px"][2] > s["text_ink_bbox_px"][0]
                            for s in result["samples"]))
        with Image.open(__import__("io").BytesIO(result["png_bytes"])) as image:
            self.assertEqual(image.size, (1440, 300))
            self.assertEqual(image.format, "PNG")
        self.assertFalse(result["subtitles_embedded_in_video"])
        self.assertFalse(result["spoken_words_independently_verified"])
        self.assertFalse(result["owner_approved"])
        self.assertFalse(result["publication_permitted"])

    def test_tamper_rights_and_missing_glyphs_fail_closed(self):
        with self.assertRaises(AnimeSubtitlePreviewError):
            self.render(font_rights_attested=False)
        with self.assertRaises(AnimeSubtitlePreviewError):
            self.render(video=self.video + b"forged")
        with self.assertRaises(AnimeSubtitlePreviewError):
            self.render(font_bytes=b"fake")
        altered = self.srt.replace(b"Kya haal hai", b"fake caption")
        forged = copy.deepcopy(self.manifest)
        forged["subtitles_sha256"] = digest(altered)
        with self.assertRaisesRegex(AnimeSubtitlePreviewError, "storyboard"):
            self.render(manifest=forged, subtitles=altered)
        # Default DejaVu font does not map Devanagari. Do not output tofu boxes.
        hindi = "नमस्ते"
        hindi_srt = self.srt.replace(b"Kya haal hai", hindi.encode("utf-8"))
        hindi_manifest = copy.deepcopy(self.manifest)
        hindi_manifest["subtitles_sha256"] = digest(hindi_srt)
        hindi_manifest["storyboard_handoff"]["plan"]["shots"][1]["caption"] = hindi
        plan = hindi_manifest["storyboard_handoff"]["plan"]
        hindi_manifest["storyboard_handoff"]["plan_sha256"] = digest(json.dumps(
            plan, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8"))
        with self.assertRaisesRegex(AnimeSubtitlePreviewError, "validation failed"):
            self.render(manifest=hindi_manifest, subtitles=hindi_srt)

    def test_create_only_cli_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(
                json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            (root / "hoshi_anime_animatic_DRAFT.mp4").write_bytes(self.video)
            (root / "hoshi_anime_animatic_DRAFT.srt").write_bytes(self.srt)
            args = [sys.executable, "-m", "scripts.review_hoshi_anime_subtitles",
                    "--draft-dir", str(root), "--font", str(self.font_path),
                    "--font-rights-attested"]
            first = subprocess.run(args, capture_output=True, timeout=60)
            self.assertEqual(first.returncode, 0, first.stderr[:500])
            target = root / "subtitle_review_PRIVATE_DRAFT"
            provenance = json.loads((target / "subtitle_review_provenance_PRIVATE.json")
                                    .read_text(encoding="utf-8"))
            self.assertFalse(provenance["owner_approved"])
            second = subprocess.run(args, capture_output=True, timeout=60)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(provenance["png_sha256"], digest(
                (target / "hoshi_subtitle_review_PRIVATE_DRAFT.png").read_bytes()))


    def test_real_encoded_private_burnin_cue_gaps_and_fail_closed(self):
        from io import BytesIO
        from PIL import ImageStat
        from cloud_backend.anime_subtitle_burnin import (
            AnimeSubtitleBurninError, render_private_subtitled_pilot,
        )
        cues = []
        for i, caption in enumerate(self.captions):
            cues.append({"shot_id": f"shot{i}", "text": caption,
                         "start_ms": i * 10000 + 2000,
                         "end_ms": i * 10000 + 4000})
        plan = {
            "schema_version": 1,
            "storyboard_sha256": self.manifest["storyboard_handoff"]["plan_sha256"],
            "audio_sha256": "a" * 64,
            "cues": cues,
        }
        manifest = copy.deepcopy(self.manifest)
        manifest["source_audio_sha256"] = "a" * 64
        manifest["subtitle_timing_source"] = "operator_supplied_voice_cues_not_audio_verified"
        manifest["voice_timing_handoff"] = {
            "plan": plan,
            "plan_sha256": digest(json.dumps(
                plan, ensure_ascii=False, sort_keys=True,
                separators=(",", ":")).encode("utf-8")),
        }
        srt = "".join(
            f"{i+1}\n00:00:{i*10+2:02d},000 --> 00:00:{i*10+4:02d},000\n"
            f"{caption}\n\n"
            for i, caption in enumerate(self.captions)).encode("utf-8")
        manifest["subtitles_sha256"] = digest(srt)
        kwargs = dict(manifest=manifest, video=self.video, subtitles=srt,
                      font_bytes=self.font, font_rights_attested=True)
        result = render_private_subtitled_pilot(**kwargs)
        self.assertEqual(result["video_sha256"], digest(result["video_mp4"]))
        self.assertEqual(result["cue_windows_ms"],
                         [[2000, 4000], [12000, 14000], [22000, 24000]])
        self.assertTrue(result["subtitles_embedded_in_video"])
        self.assertEqual(result["media_qc"]["frame_count"], 360)
        self.assertEqual(result["media_qc"]["audio_codec"], "aac")
        self.assertFalse(result["spoken_words_independently_verified"])
        self.assertFalse(result["owner_approved"])
        self.assertFalse(result["publication_permitted"])
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "captioned.mp4"
            video.write_bytes(result["video_mp4"])
            def decoded_frame(index):
                command = ["ffmpeg", "-hide_banner", "-loglevel", "error",
                           "-nostdin", "-i", str(video),
                           "-vf", f"select=eq(n\\,{index})", "-frames:v", "1",
                           "-f", "image2pipe", "-vcodec", "png", "-"]
                output = subprocess.run(command, capture_output=True,
                                        timeout=20, check=False)
                self.assertEqual(output.returncode, 0, output.stderr[:300])
                with Image.open(BytesIO(output.stdout)) as picture:
                    return picture.convert("RGB").copy()
            # One second is outside all cues; three seconds is inside shot 1.
            quiet, spoken = decoded_frame(12), decoded_frame(36)
            self.assertLess(max(ImageStat.Stat(quiet.crop((30, 220, 450, 260))).extrema[0]), 90)
            self.assertGreater(max(ImageStat.Stat(spoken.crop((30, 220, 450, 260))).extrema[0]), 150)
        with self.assertRaises(AnimeSubtitleBurninError):
            render_private_subtitled_pilot(**(kwargs | {"font_rights_attested": False}))
        with self.assertRaises(AnimeSubtitleBurninError):
            render_private_subtitled_pilot(**(kwargs | {"video": self.video + b"fake"}))

    def test_private_burnin_cli_create_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(
                json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")
            (root / "hoshi_anime_animatic_DRAFT.mp4").write_bytes(self.video)
            (root / "hoshi_anime_animatic_DRAFT.srt").write_bytes(self.srt)
            command = [sys.executable, "-m", "scripts.burn_hoshi_anime_subtitles",
                       "--draft-dir", str(root), "--font", str(self.font_path),
                       "--font-rights-attested"]
            first = subprocess.run(command, capture_output=True, timeout=160)
            self.assertEqual(first.returncode, 0, first.stderr[:500])
            target = root / "subtitle_burnin_PRIVATE_DRAFT"
            meta = json.loads((target / "subtitle_burnin_provenance_PRIVATE.json")
                              .read_text(encoding="utf-8"))
            self.assertEqual(meta["video_sha256"], digest(
                (target / meta["filename"]).read_bytes()))
            self.assertFalse(meta["release_authorized"])
            second = subprocess.run(command, capture_output=True, timeout=160)
            self.assertNotEqual(second.returncode, 0)
            self.assertFalse((root / "manifest.json").read_text(
                encoding="utf-8").find('"owner_approved": true') >= 0)


if __name__ == "__main__":
    unittest.main()
