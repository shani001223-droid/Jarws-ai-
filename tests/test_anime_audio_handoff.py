"""Private Anime Studio CLI: real audio handoff, rights gates and MP4 QC."""
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

from cloud_backend.anime_pilot_animatic import MAX_AUDIO_BYTES


def _wav(seconds: int = 30) -> bytes:
    stream = BytesIO()
    with wave.open(stream, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * (16000 * seconds))
    return stream.getvalue()


class AudioHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.images = []
        for i in range(3):
            image = Image.new("RGB", (640, 360), (25 + i * 30, 40, 100))
            path = self.root / f"original-{i}.png"
            image.save(path)
            self.images.append(path)
        self.audio_path = self.root / "owner-audio.wav"
        self.audio_path.write_bytes(_wav())
        self.destination = self.root / "private-output"

    def command(self, *extra):
        args = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
        for path in self.images:
            args += ["--shot", str(path)]
        for caption in ("سلام", "नमस्ते", "Phir milenge"):
            args += ["--caption", caption]
        args += ["--out", str(self.destination), "--image-rights-attested"]
        args += list(extra)
        return args

    def run_cli(self, *extra):
        return subprocess.run(self.command(*extra), capture_output=True,
                              text=True, timeout=110)

    def test_audio_and_rights_must_be_supplied_together(self):
        for flags in (
            ("--audio-wav", str(self.audio_path)),
            ("--audio-rights-attested",),
        ):
            with self.subTest(flags=flags):
                result = self.run_cli(*flags)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must be supplied together", result.stderr)
                self.assertFalse(self.destination.exists())

    def test_bad_or_oversized_audio_rejected_without_output(self):
        for name, content in (
            ("broken.wav", b"not a WAV file"),
            ("too-short.wav", _wav(29)),
            ("oversized.wav", b"x" * (MAX_AUDIO_BYTES + 1)),
        ):
            with self.subTest(name=name):
                path = self.root / name
                path.write_bytes(content)
                result = self.run_cli("--audio-wav", str(path),
                                      "--audio-rights-attested")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.destination.exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real AAC MP4 requires local FFmpeg and ffprobe")
    def test_real_private_mp4_aac_and_nonoverwrite(self):
        result = self.run_cli("--audio-wav", str(self.audio_path),
                              "--audio-rights-attested")
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((self.destination / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_audio_sha256"],
                         hashlib.sha256(self.audio_path.read_bytes()).hexdigest())
        self.assertEqual(manifest["audio_status"], "caller_attested_wav_unverified")
        self.assertFalse(manifest["hindi_urdu_voice_recorded"])
        self.assertFalse(manifest["owner_approved"])
        self.assertFalse(manifest["uploaded"])
        self.assertFalse(manifest["published"])
        video_path = self.destination / manifest["filename"]
        video = video_path.read_bytes()
        self.assertEqual(hashlib.sha256(video).hexdigest(), manifest["video_sha256"])
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,codec_type",
             "-of", "json", str(video_path)],
            capture_output=True, text=True, timeout=12, check=True)
        streams = json.loads(probe.stdout)["streams"]
        self.assertIn(("audio", "aac"),
                      [(s["codec_type"], s["codec_name"]) for s in streams])
        self.assertIn(("video", "h264"),
                      [(s["codec_type"], s["codec_name"]) for s in streams])
        again = self.run_cli("--audio-wav", str(self.audio_path),
                             "--audio-rights-attested")
        self.assertNotEqual(again.returncode, 0)
        self.assertEqual(video_path.read_bytes(), video)


if __name__ == "__main__":
    unittest.main()
