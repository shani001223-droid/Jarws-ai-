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
import wave

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
        self.assertEqual(result["visual_evidence_sha256"],
                         digest(result["visual_evidence_png"]))
        self.assertEqual(result["visual_evidence_resolution"], [960, 900])
        self.assertTrue(result["visual_evidence_decoded_from_both_mp4s"])
        self.assertFalse(result["caption_ink_independently_machine_verified"])
        self.assertEqual(len(result["visual_evidence_samples"]), 3)
        # Listen to the actual encoded AAC cue excerpts, not the source WAV.
        self.assertTrue(result["audio_review_decoded_from_actual_encoded_aac"])
        self.assertTrue(result["audio_review_human_listening_required"])
        self.assertEqual(len(result["audio_review_wavs"]), 3)
        self.assertEqual(len(result["audio_review_samples"]), 3)
        self.assertEqual(result["audio_waveform_status"],
                         "actual_encoded_aac_waveform_human_review_only")
        self.assertEqual(result["audio_waveform_sha256"],
                         digest(result["audio_waveform_png"]))
        self.assertEqual(result["audio_waveform_resolution"], [1440, 660])
        self.assertEqual(len(result["audio_waveform_samples"]), 3)
        with Image.open(BytesIO(result["audio_waveform_png"])) as waveform:
            self.assertEqual(waveform.size, (1440, 660))
        self.assertTrue(result["audio_waveform_human_review_required"])
        for index, clip in enumerate(result["audio_review_wavs"]):
            record = result["audio_review_samples"][index]
            self.assertEqual(record["filename"], clip["filename"])
            self.assertEqual(record["wav_sha256"], digest(clip["wav_bytes"]))
            self.assertFalse(record["spoken_words_independently_verified"])
            self.assertFalse(record["phoneme_sync_verified"])
            with wave.open(BytesIO(clip["wav_bytes"]), "rb") as audio:
                self.assertEqual((audio.getnchannels(), audio.getsampwidth(),
                                  audio.getframerate()), (1, 2, 16000))
                self.assertLessEqual(abs(audio.getnframes() -
                                         (record["excerpt_end_ms_requested"] -
                                          record["excerpt_start_ms"]) * 16), 1600)
                self.assertTrue(any(audio.readframes(800)))
        from cloud_backend.anime_subtitle_burnin import _encoded_cue_audio_evidence
        self.assertEqual(_encoded_cue_audio_evidence(
            "ffmpeg", Path("unused.mp4"), [(0, 10000, "a")] * 3, "none"), ([], []))
        with Image.open(BytesIO(result["visual_evidence_png"])) as evidence:
            self.assertEqual(evidence.size, (960, 900))
            original_band = evidence.crop((20, 250, 460, 290))
            captioned_band = evidence.crop((500, 250, 940, 290))
            self.assertLess(max(ImageStat.Stat(original_band).extrema[0]), 90)
            self.assertGreater(max(ImageStat.Stat(captioned_band).extrema[0]), 150)
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
            self.assertEqual(meta["review_page_filename"],
                             "hoshi_private_review_OFFLINE.html")
            review_html = (target / meta["review_page_filename"]).read_bytes()
            self.assertEqual(meta["review_page_sha256"], digest(review_html))
            self.assertIn(b"UNAPPROVED / DO NOT PUBLISH", review_html)
            self.assertIn(b"<video controls", review_html)
            self.assertIn(b"<audio controls", review_html)
            self.assertNotIn(b"<script", review_html)
            self.assertTrue(meta["review_page_human_review_required"])
            self.assertEqual(meta["visual_evidence_sha256"], digest(
                (target / meta["visual_evidence_filename"]).read_bytes()))
            self.assertEqual(len(meta["visual_evidence_samples"]), 3)
            self.assertEqual(len(meta["audio_review_samples"]), 3)
            self.assertNotIn("audio_review_wavs", meta)
            self.assertNotIn("audio_waveform_png", meta)
            self.assertEqual(meta["audio_waveform_sha256"], digest(
                (target / meta["audio_waveform_filename"]).read_bytes()))
            for record in meta["audio_review_samples"]:
                self.assertEqual(record["wav_sha256"], digest(
                    (target / record["filename"]).read_bytes()))
            # Verify the actual saved media, captions, HTML and AAC-derived
            # evidence before human review; never infer speech/owner approval.
            verify = [sys.executable, "-m",
                      "scripts.verify_hoshi_anime_private_review",
                      "--draft-dir", str(root)]
            checked = subprocess.run(verify, capture_output=True, timeout=70)
            self.assertEqual(checked.returncode, 0, checked.stderr[:500])
            report = json.loads(checked.stdout)
            self.assertEqual(report["status"],
                             "private_bundle_bytes_and_mp4_verified_human_review_pending")
            self.assertFalse(report["owner_approved"])
            self.assertFalse(report["speech_or_lip_sync_verified"])
            self.assertEqual(report["file_count"], 8)
            page = target / meta["review_page_filename"]
            page_bytes = page.read_bytes()
            page.write_bytes(page_bytes + b"<!-- forged -->")
            rejected = subprocess.run(verify, capture_output=True, timeout=20)
            self.assertNotEqual(rejected.returncode, 0)
            page.write_bytes(page_bytes)
            clip = target / meta["audio_review_samples"][0]["filename"]
            clip_bytes = clip.read_bytes()
            clip.write_bytes(clip_bytes + b"tamper")
            rejected = subprocess.run(verify, capture_output=True, timeout=20)
            self.assertNotEqual(rejected.returncode, 0)
            clip.write_bytes(clip_bytes)
            # A forged but still well-formed WAV can be re-hashed in local
            # provenance. It must not pass as the actual encoded AAC samples.
            provenance = target / "subtitle_burnin_provenance_PRIVATE.json"
            provenance_bytes = provenance.read_bytes()
            forged_wav = bytearray(clip_bytes)
            forged_wav[50] ^= 1  # Flip a PCM byte, leaving the WAV header valid.
            clip.write_bytes(forged_wav)
            forged_meta = copy.deepcopy(meta)
            forged_meta["audio_review_samples"][0]["wav_sha256"] = digest(
                bytes(forged_wav))
            provenance.write_text(json.dumps(forged_meta, ensure_ascii=False),
                                  encoding="utf-8")
            rejected = subprocess.run(verify, capture_output=True, timeout=70)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn(b"AAC listening clips differ", rejected.stderr)
            clip.write_bytes(clip_bytes)
            provenance.write_bytes(provenance_bytes)
            # An attacker can re-hash a different valid PNG in the JSON.
            # The verifier must compare decoded source/encoded MP4 pixels,
            # not merely trust a self-consistent metadata hash.
            from io import BytesIO
            visual = target / meta["visual_evidence_filename"]
            visual_bytes = visual.read_bytes()
            provenance = target / "subtitle_burnin_provenance_PRIVATE.json"
            provenance_bytes = provenance.read_bytes()
            with Image.open(BytesIO(visual_bytes)) as original:
                changed = original.convert("RGB")
                changed.putpixel((1, 1), (255, 0, 0))
                changed.save(visual, format="PNG")
            forged = dict(meta)
            forged["visual_evidence_sha256"] = digest(visual.read_bytes())
            provenance.write_text(json.dumps(forged, ensure_ascii=False),
                                  encoding="utf-8")
            rejected = subprocess.run(verify, capture_output=True, timeout=70)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn(b"Comparison pixels", rejected.stderr)
            visual.write_bytes(visual_bytes)
            provenance.write_bytes(provenance_bytes)

            forged = copy.deepcopy(meta)
            forged["visual_evidence_samples"][0]["decoded_frame_index"] = 13
            provenance.write_text(json.dumps(forged, ensure_ascii=False),
                                  encoding="utf-8")
            rejected = subprocess.run(verify, capture_output=True, timeout=70)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn(b"Invalid encoded comparison cue", rejected.stderr)
            provenance.write_bytes(provenance_bytes)
            (target / "unexpected.txt").write_text("not an approved review asset")
            rejected = subprocess.run(verify, capture_output=True, timeout=70)
            self.assertNotEqual(rejected.returncode, 0)
            (target / "unexpected.txt").unlink()
            checked_again = subprocess.run(verify, capture_output=True, timeout=70)
            self.assertEqual(checked_again.returncode, 0, checked_again.stderr[:500])
            second = subprocess.run(command, capture_output=True, timeout=160)
            self.assertNotEqual(second.returncode, 0)
            self.assertFalse((root / "manifest.json").read_text(
                encoding="utf-8").find('"owner_approved": true') >= 0)


if __name__ == "__main__":
    unittest.main()
