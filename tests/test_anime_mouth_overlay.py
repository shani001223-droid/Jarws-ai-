"""Actual private two-state mouth sprite video preview, never phoneme lip-sync."""
from __future__ import annotations

import copy
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

from PIL import Image, ImageDraw

from cloud_backend.anime_audio_energy import build_audio_energy_handoff
from cloud_backend.anime_mouth_overlay import (
    MouthOverlayError, bind_mouth_overlay, sprite_enable_expression,
)
from cloud_backend.anime_pilot_animatic import AnimePilotError, render_private_animatic
from cloud_backend.anime_visual_review import (AnimeVisualReviewError,
                                               build_mouth_review_sheet)
from cloud_backend.anime_storyboard_handoff import bind_storyboard_handoff
from cloud_backend.anime_voice_timing import bind_voice_timing_handoff


class MouthSpritePreviewTests(unittest.TestCase):
    def setUp(self):
        self.stills = []
        for index in range(3):
            stream = BytesIO()
            Image.new("RGB", (480, 270), (20, 40 + 10 * index, 100)).save(stream, "PNG")
            self.stills.append(stream.getvalue())
        self.captions = ["سلام", "नमस्ते", "Phir milenge"]
        self.storyboard = {
            "schema_version": 1, "project_id": "MouthPilot", "language": "ur",
            "characters": [{"id": "hero", "design_sha256": "a" * 64, "rights_attested": True}],
            "shots": [
                {"shot_id": f"shot{i}", "still_sha256": hashlib.sha256(still).hexdigest(),
                 "caption": self.captions[i], "camera_move": "static",
                 "character_ids": ["hero"]}
                for i, still in enumerate(self.stills)
            ]
        }
        self.wav = self._wav()
        self.cues = {
            "schema_version": 1, "language": "ur",
            "audio_sha256": hashlib.sha256(self.wav).hexdigest(),
            "cues": [
                {"shot_id": f"shot{i}", "speaker_id": "hero",
                 "start_ms": i * 10000 + 500, "end_ms": i * 10000 + 9500,
                 "text": self.captions[i]}
                for i in range(3)
            ]
        }
        image = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
        ImageDraw.Draw(image).ellipse((4, 3, 27, 12), fill=(255, 15, 15, 255))
        output = BytesIO()
        image.save(output, format="PNG")
        self.sprites = [output.getvalue()] * 3
        self.plan = {
            "schema_version": 1,
            "sprites": [
                {"shot_id": f"shot{i}", "speaker_id": "hero",
                 "png_sha256": hashlib.sha256(self.sprites[i]).hexdigest(),
                 "x": 200, "y": 130}
                for i in range(3)
            ]
        }

    @staticmethod
    def _wav(audible=True):
        rate = 16000
        stream = BytesIO()
        with wave.open(stream, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            samples = bytearray(rate * 30 * 2)
            if audible:
                for i in range(rate, rate * 3):
                    struct.pack_into("<h", samples, i * 2,
                                     int(12000 * math.sin(2 * math.pi * 440 * i / rate)))
            wav.writeframes(samples)
        return stream.getvalue()

    def _bound(self):
        storyboard = bind_storyboard_handoff(
            self.storyboard, self.stills, self.captions, ["static"] * 3)
        voice = bind_voice_timing_handoff(self.cues, storyboard, self.wav)
        energy = build_audio_energy_handoff(self.wav, voice)
        return voice, energy

    def test_exact_asset_and_speaker_binding(self):
        voice, energy = self._bound()
        bound = bind_mouth_overlay(self.plan, self.sprites, voice, energy,
                                   rights_attested=True)
        self.assertEqual(bound["audio_sha256"], hashlib.sha256(self.wav).hexdigest())
        self.assertEqual(bound["sprites"][0]["energy_windows_ms"], [[1000, 3000]])
        self.assertEqual(bound["sprites"][1]["energy_windows_ms"], [])
        self.assertTrue(bound["two_state_sprite_animation_generated"])
        self.assertFalse(bound["phoneme_lip_sync_generated"])
        self.assertFalse(bound["face_tracking_performed"])
        self.assertEqual(sprite_enable_expression(0, [[1000, 3000]]),
                         "gte(t,1.000)*lt(t,3.000)")
        self.assertEqual(sprite_enable_expression(1, []), "0")

    def test_rejects_missing_rights_tampering_and_wrong_assets(self):
        voice, energy = self._bound()
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, self.sprites, voice, energy)
        for key, value in [
            ("shot_id", "shot2"), ("speaker_id", "intruder"),
            ("png_sha256", "f" * 64), ("x", True), ("x", -1), ("x", 470),
            ("y", 260)
        ]:
            with self.subTest(key=key):
                invalid = copy.deepcopy(self.plan)
                invalid["sprites"][0][key] = value
                with self.assertRaises(MouthOverlayError):
                    bind_mouth_overlay(invalid, self.sprites, voice, energy,
                                       rights_attested=True)
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, [b"not a png"] * 3, voice, energy,
                               rights_attested=True)
        altered = copy.deepcopy(energy)
        altered["voice_timing_sha256"] = "0" * 64
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, self.sprites, voice, altered,
                               rights_attested=True)
        with self.assertRaises(AnimePilotError):
            render_private_animatic(
                self.stills, self.captions, image_rights_attested=True,
                audio_wav=self.wav, audio_rights_attested=True,
                storyboard_handoff=self.storyboard, voice_timing_plan=self.cues,
                mouth_overlay_plan=self.plan, mouth_sprites=self.sprites)

    def test_rejects_cross_audio_binding_and_out_of_cue_activity(self):
        """No mouth animation may be attributed to a different WAV or silent gap."""
        voice, energy = self._bound()
        altered = copy.deepcopy(energy)
        altered["audio_sha256"] = "f" * 64
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, self.sprites, voice, altered,
                               rights_attested=True)
        altered = copy.deepcopy(energy)
        altered["shots"][0]["energy_windows_ms"] = [[0, 100]]
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, self.sprites, voice, altered,
                               rights_attested=True)
        altered = copy.deepcopy(energy)
        altered["shots"][0]["energy_windows_ms"] = [[9500, 9700]]
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, self.sprites, voice, altered,
                               rights_attested=True)
        altered = copy.deepcopy(energy)
        altered["shots"][0] = None
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, self.sprites, voice, altered,
                               rights_attested=True)
        altered_voice = copy.deepcopy(voice)
        altered_voice["plan"]["cues"][0] = None
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, self.sprites, altered_voice, energy,
                               rights_attested=True)
        altered = copy.deepcopy(energy)
        altered["frame_rate"] = True
        with self.assertRaises(MouthOverlayError):
            bind_mouth_overlay(self.plan, self.sprites, voice, altered,
                               rights_attested=True)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/ffprobe required")
    def test_real_mp4_has_visible_energy_gated_sprite_not_permanent_overlay(self):
        result = render_private_animatic(
            self.stills, self.captions, image_rights_attested=True,
            audio_wav=self.wav, audio_rights_attested=True,
            storyboard_handoff=self.storyboard, voice_timing_plan=self.cues,
            mouth_overlay_plan=self.plan, mouth_sprites=self.sprites,
            mouth_rights_attested=True)
        self.assertIn(b"ftyp", result["video_mp4"][:32])
        self.assertTrue(result["mouth_overlay_handoff"]["two_state_sprite_animation_generated"])
        self.assertFalse(result["mouth_overlay_handoff"]["phoneme_lip_sync_generated"])
        self.assertFalse(result["full_character_animation"])
        self.assertFalse(result["published"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.mp4"
            path.write_bytes(result["video_mp4"])
            def frame_at(seconds):
                completed = subprocess.run(
                    [shutil.which("ffmpeg"), "-v", "error", "-ss", str(seconds),
                     "-i", str(path), "-frames:v", "1", "-f", "image2pipe",
                     "-vcodec", "png", "-"],
                    capture_output=True, timeout=15)
                self.assertEqual(completed.returncode, 0, completed.stderr.decode()[:200])
                return Image.open(BytesIO(completed.stdout)).convert("RGB")
            active = frame_at(2.0).getpixel((216, 138))
            inactive = frame_at(4.0).getpixel((216, 138))
            self.assertGreater(active[0], inactive[0] + 80)
            self.assertGreater(inactive[2], active[2] + 30)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/ffprobe required")
    def test_silent_wav_produces_no_visible_sprite(self):
        self.wav = self._wav(audible=False)
        self.cues["audio_sha256"] = hashlib.sha256(self.wav).hexdigest()
        result = render_private_animatic(
            self.stills, self.captions, image_rights_attested=True,
            audio_wav=self.wav, audio_rights_attested=True,
            storyboard_handoff=self.storyboard, voice_timing_plan=self.cues,
            mouth_overlay_plan=self.plan, mouth_sprites=self.sprites,
            mouth_rights_attested=True)
        self.assertFalse(result["mouth_overlay_handoff"]["two_state_sprite_animation_generated"])
        self.assertEqual(result["audio_energy_handoff"]["active_frames"], 0)

    def test_cli_requires_complete_rights_attested_sprite_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
            for index, still in enumerate(self.stills):
                path = root / f"shot{index}.png"
                path.write_bytes(still)
                args += ["--shot", str(path)]
            for caption in self.captions:
                args += ["--caption", caption]
            args += ["--mouth-overlay-json", str(root / "missing.json"),
                     "--image-rights-attested", "--out", str(root / "not-created")]
            completed = subprocess.run(args, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Mouth overlays require", completed.stderr)
            self.assertFalse((root / "not-created").exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/ffprobe required")
    def test_private_review_sheet_decodes_mp4_and_remains_unapproved(self):
        rendered = render_private_animatic(
            self.stills, self.captions, image_rights_attested=True,
            audio_wav=self.wav, audio_rights_attested=True,
            storyboard_handoff=self.storyboard, voice_timing_plan=self.cues,
            mouth_overlay_plan=self.plan, mouth_sprites=self.sprites,
            mouth_rights_attested=True)
        review = build_mouth_review_sheet(
            rendered["video_mp4"], rendered["mouth_overlay_handoff"])
        self.assertEqual(review["source_video_sha256"], rendered["video_sha256"])
        self.assertEqual(hashlib.sha256(review["png_bytes"]).hexdigest(),
                         review["png_sha256"])
        self.assertEqual(len(review["samples"]), 6)
        self.assertEqual(review["media_qc"]["decoded_video_frames"], 360)
        self.assertEqual(review["media_qc"]["audio_codec"], "aac")
        self.assertEqual(review["media_qc"]["status"],
                         "independently_probed_media_not_visual_approval")
        self.assertEqual(review["samples"][0]["sample_kind"], "active")
        self.assertEqual(review["samples"][1]["sample_kind"], "quiet")
        self.assertEqual(review["samples"][2]["sample_kind"], "no_activity")
        self.assertFalse(review["visual_alignment_verified"])
        self.assertFalse(review["owner_approved"])
        self.assertTrue(review["manual_review_required"])
        with Image.open(BytesIO(review["png_bytes"])) as contact:
            self.assertEqual(contact.size, (1440, 592))
            self.assertEqual(contact.format, "PNG")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/ffprobe required")
    def test_review_rejects_truncated_and_audio_free_real_mp4(self):
        """Decoded sample frames do not make an arbitrary clip an approved pilot."""
        voice, energy = self._bound()
        bound = bind_mouth_overlay(self.plan, self.sprites, voice, energy,
                                   rights_attested=True)
        silent_video = render_private_animatic(
            self.stills, self.captions, image_rights_attested=True)
        with self.assertRaises(AnimeVisualReviewError):
            build_mouth_review_sheet(silent_video["video_mp4"], bound)
        with tempfile.TemporaryDirectory() as directory:
            short = Path(directory) / "short.mp4"
            completed = subprocess.run(
                [shutil.which("ffmpeg"), "-v", "error", "-f", "lavfi",
                 "-i", "color=c=blue:s=480x270:r=12:d=3",
                 "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
                 "-t", "3", "-c:v", "libx264", "-threads", "2",
                 "-preset", "ultrafast", "-c:a", "aac", "-y", str(short)],
                capture_output=True, timeout=30, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr[:200])
            with self.assertRaises(AnimeVisualReviewError):
                build_mouth_review_sheet(short.read_bytes(), bound)

    def test_review_rejects_bad_video_and_spoofed_coordinates(self):
        voice, energy = self._bound()
        bound = bind_mouth_overlay(self.plan, self.sprites, voice, energy,
                                   rights_attested=True)
        with self.assertRaises(AnimeVisualReviewError):
            build_mouth_review_sheet(b"bad", bound)
        for key, value in (("x", True), ("x", -1), ("width", 1000)):
            bad = copy.deepcopy(bound)
            bad["sprites"][0][key] = value
            with self.subTest(key=key), self.assertRaises(AnimeVisualReviewError):
                build_mouth_review_sheet(b"x" * 200, bad)
        bad = copy.deepcopy(bound)
        bad["sprites"][0]["energy_windows_ms"] = [[-1, 200]]
        with self.assertRaises(AnimeVisualReviewError):
            build_mouth_review_sheet(b"x" * 200, bad)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/ffprobe required")
    def test_cli_review_sheet_is_private_and_create_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
            for index, still in enumerate(self.stills):
                path = root / f"shot{index}.png"
                path.write_bytes(still)
                args.extend(["--shot", str(path)])
            for caption in self.captions:
                args.extend(["--caption", caption])
            wav_path = root / "voice.wav"
            wav_path.write_bytes(self.wav)
            storyboard_path = root / "storyboard.json"
            storyboard_path.write_text(json.dumps(self.storyboard), encoding="utf-8")
            cues_path = root / "cues.json"
            cues_path.write_text(json.dumps(self.cues), encoding="utf-8")
            mouth_path = root / "mouth.json"
            mouth_path.write_text(json.dumps(self.plan), encoding="utf-8")
            args.extend(["--audio-wav", str(wav_path), "--audio-rights-attested",
                         "--storyboard-json", str(storyboard_path),
                         "--voice-cues-json", str(cues_path),
                         "--mouth-overlay-json", str(mouth_path),
                         "--mouth-rights-attested", "--image-rights-attested",
                         "--mouth-review-sheet"])
            for index, sprite in enumerate(self.sprites):
                path = root / f"mouth{index}.png"
                path.write_bytes(sprite)
                args.extend(["--mouth-sprite", str(path)])
            destination = root / "private-draft"
            args.extend(["--out", str(destination)])
            completed = subprocess.run(args, capture_output=True, text=True, timeout=110)
            self.assertEqual(completed.returncode, 0, completed.stderr[:400])
            png = (destination / "hoshi_mouth_review_DRAFT.png").read_bytes()
            manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["mouth_visual_review"]["png_sha256"],
                             hashlib.sha256(png).hexdigest())
            self.assertFalse(manifest["mouth_visual_review"]["owner_approved"])
            self.assertFalse(manifest["mouth_visual_review"]["visual_alignment_verified"])
            self.assertEqual(manifest["mouth_visual_review"]["media_qc"]["decoded_video_frames"], 360)
            second = subprocess.run(args, capture_output=True, text=True, timeout=110)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual((destination / "hoshi_mouth_review_DRAFT.png").read_bytes(), png)


if __name__ == "__main__":
    unittest.main()
