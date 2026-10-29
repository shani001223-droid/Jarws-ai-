"""Exact WAV/character/shot/caption timing handoff; no synthesized speech claims."""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

from PIL import Image

from cloud_backend.anime_pilot_animatic import AnimePilotError, render_private_animatic
from cloud_backend.anime_storyboard_handoff import bind_storyboard_handoff
from cloud_backend.anime_voice_timing import bind_voice_timing_handoff, VoiceTimingError


class VoiceTimingTests(unittest.TestCase):
    def setUp(self):
        self.stills = []
        for index in range(3):
            stream = BytesIO()
            Image.new("RGB", (640, 360), (20 + index * 20, 40, 100)).save(stream, "PNG")
            self.stills.append(stream.getvalue())
        stream = BytesIO()
        with wave.open(stream, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(bytes(16000 * 30 * 2))
        self.wav = stream.getvalue()
        self.captions = ["سلام", "नमस्ते", "Phir milenge"]
        self.moves = ["static", "static", "static"]
        self.storyboard = {
            "schema_version": 1, "project_id": "HoshiPilot", "language": "ur",
            "characters": [{"id": "hero", "design_sha256": "a" * 64, "rights_attested": True}],
            "shots": [
                {"shot_id": f"shot{i}", "still_sha256": hashlib.sha256(img).hexdigest(),
                 "caption": self.captions[i], "camera_move": "static",
                 "character_ids": ["hero"]}
                for i, img in enumerate(self.stills)
            ]
        }
        self.bound = bind_storyboard_handoff(self.storyboard, self.stills, self.captions, self.moves)
        self.cues = {
            "schema_version": 1, "language": "ur",
            "audio_sha256": hashlib.sha256(self.wav).hexdigest(),
            "cues": [
                {"shot_id": f"shot{i}", "speaker_id": "hero",
                 "start_ms": i * 10000 + 1000, "end_ms": i * 10000 + 9000,
                 "text": self.captions[i]}
                for i in range(3)
            ]
        }

    def test_exact_voice_timing_handoff(self):
        bound = bind_voice_timing_handoff(self.cues, self.bound, self.wav)
        self.assertEqual(bound["plan"]["cues"][2]["end_ms"], 29000)
        self.assertEqual(bound["plan"]["storyboard_sha256"], self.bound["plan_sha256"])
        self.assertFalse(bound["lip_sync_generated"])
        self.assertFalse(bound["voice_language_verified"])
        self.assertFalse(bound["owner_approved"])

    def test_rejects_mismatch_and_timing_spoofing(self):
        import copy
        mutations = [
            ("audio_sha256", "b" * 64),
            ("language", "hi"),
            ("schema_version", True),
        ]
        for field, value in mutations:
            with self.subTest(field=field):
                invalid = copy.deepcopy(self.cues)
                invalid[field] = value
                with self.assertRaises(VoiceTimingError):
                    bind_voice_timing_handoff(invalid, self.bound, self.wav)
        for field, value in [
            ("shot_id", "shot2"), ("speaker_id", "unknown"),
            ("text", "fake line"), ("start_ms", -1), ("start_ms", True),
            ("end_ms", 10001), ("end_ms", 1100), ("end_ms", 31000)
        ]:
            with self.subTest(field=field, value=value):
                invalid = copy.deepcopy(self.cues)
                invalid["cues"][0][field] = value
                with self.assertRaises(VoiceTimingError):
                    bind_voice_timing_handoff(invalid, self.bound, self.wav)
        with self.assertRaises(VoiceTimingError):
            bind_voice_timing_handoff(self.cues, self.bound, self.wav + b"x")
        with self.assertRaises(VoiceTimingError):
            bind_voice_timing_handoff(self.cues, None, self.wav)
        with self.assertRaises(VoiceTimingError):
            bind_voice_timing_handoff(self.cues, self.bound, None)

    def test_voice_cues_fail_closed_before_ffmpeg(self):
        invalid = dict(self.cues)
        invalid["audio_sha256"] = "0" * 64
        with self.assertRaises(AnimePilotError):
            render_private_animatic(
                self.stills, self.captions, image_rights_attested=True,
                audio_wav=self.wav, audio_rights_attested=True,
                storyboard_handoff=self.storyboard, voice_timing_plan=invalid)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and ffprobe required for real MP4 verification")
    def test_actual_mp4_manifest_contains_bound_voice_timing(self):
        result = render_private_animatic(
            self.stills, self.captions, image_rights_attested=True,
            audio_wav=self.wav, audio_rights_attested=True,
            storyboard_handoff=self.storyboard, voice_timing_plan=self.cues)
        self.assertIn(b"ftyp", result["video_mp4"][:32])
        self.assertEqual(result["voice_timing_handoff"]["plan"]["audio_sha256"],
                         result["source_audio_sha256"])
        self.assertEqual(result["voice_timing_handoff"]["plan"]["cues"][0]["text"], "سلام")
        self.assertFalse(result["hindi_urdu_voice_recorded"])
        self.assertFalse(result["uploaded"])
        self.assertEqual(result["subtitle_timing_source"],
                         "operator_supplied_voice_cues_not_audio_verified")
        subtitles = result["subtitles_srt"].decode("utf-8")
        self.assertIn("00:00:01,000 --> 00:00:09,000\nسلام", subtitles)
        self.assertIn("00:00:11,000 --> 00:00:19,000\nनमस्ते", subtitles)
        self.assertIn("00:00:21,000 --> 00:00:29,000\nPhir milenge", subtitles)
        self.assertNotIn("00:00:00,000 --> 00:00:10,000", subtitles)
        self.assertEqual(hashlib.sha256(result["subtitles_srt"]).hexdigest(),
                         result["subtitles_sha256"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and ffprobe required for CLI handoff")
    def test_private_cli_voice_cues_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
            for index, still in enumerate(self.stills):
                path = root / f"shot{index}.png"
                path.write_bytes(still)
                args += ["--shot", str(path)]
            for caption in self.captions:
                args += ["--caption", caption]
            storyboard_path = root / "storyboard.json"
            storyboard_path.write_text(json.dumps(self.storyboard, ensure_ascii=False),
                                       encoding="utf-8")
            wav_path = root / "audio.wav"
            wav_path.write_bytes(self.wav)
            cues_path = root / "cues.json"
            cues_path.write_text(json.dumps(self.cues, ensure_ascii=False), encoding="utf-8")
            output_dir = root / "private-review"
            args += [
                "--storyboard-json", str(storyboard_path),
                "--audio-wav", str(wav_path), "--audio-rights-attested",
                "--voice-cues-json", str(cues_path), "--image-rights-attested",
                "--out", str(output_dir)
            ]
            success = subprocess.run(args, capture_output=True, text=True, timeout=110)
            self.assertEqual(success.returncode, 0, success.stderr)
            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["voice_timing_handoff"]["plan"]["cues"][1]["text"],
                             "नमस्ते")
            self.assertFalse(manifest["voice_timing_handoff"]["lip_sync_generated"])
            self.assertEqual(manifest["subtitle_timing_source"],
                             "operator_supplied_voice_cues_not_audio_verified")
            exported_srt = (output_dir / "hoshi_anime_animatic_DRAFT.srt").read_text(encoding="utf-8")
            self.assertIn("00:00:11,000 --> 00:00:19,000", exported_srt)
            self.assertNotIn("00:00:10,000 --> 00:00:20,000", exported_srt)
            self.assertEqual(hashlib.sha256(exported_srt.encode("utf-8")).hexdigest(),
                             manifest["subtitles_sha256"])
            before = (output_dir / manifest["filename"]).read_bytes()
            repeat = subprocess.run(args, capture_output=True, text=True, timeout=110)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertEqual((output_dir / manifest["filename"]).read_bytes(), before)

    def test_cli_rejects_voice_cues_without_storyboard_and_wav(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
            for index, still in enumerate(self.stills):
                path = root / f"shot{index}.png"
                path.write_bytes(still)
                args += ["--shot", str(path)]
            for caption in self.captions:
                args += ["--caption", caption]
            cues_path = root / "cues.json"
            cues_path.write_text(json.dumps(self.cues), encoding="utf-8")
            dest = root / "should-not-exist"
            args += ["--voice-cues-json", str(cues_path), "--image-rights-attested",
                     "--out", str(dest)]
            result = subprocess.run(args, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("require both", result.stderr)
            self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
