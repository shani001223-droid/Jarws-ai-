"""Real encoded private Anime Studio music handoff, no publishing or rights inference."""
from __future__ import annotations

from array import array
from io import BytesIO
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

from PIL import Image

from cloud_backend.anime_pilot_animatic import (
    AnimePilotError, render_private_animatic,
)


def tone_wav(frequency: int, seconds: int = 30) -> bytes:
    rate = 16000
    samples = array("h", (
        int(6000 * math.sin(2 * math.pi * frequency * i / rate))
        for i in range(rate * seconds)
    ))
    stream = BytesIO()
    with wave.open(stream, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(samples.tobytes())
    return stream.getvalue()


def stills():
    result = []
    for i in range(3):
        stream = BytesIO()
        Image.new("RGB", (640, 360), (40 + i * 30, 60, 90)).save(stream, "PNG")
        result.append(stream.getvalue())
    return result


CAPTIONS = ["ایک رات", "एक कहानी", "Aakhri manzar"]


def frequency_power(samples, frequency: int, rate: int = 16000) -> float:
    """Simple narrowband Goertzel measurement, independent of manifest claims."""
    n = len(samples)
    k = round(n * frequency / rate)
    coefficient = 2 * math.cos(2 * math.pi * k / n)
    previous = previous2 = 0.0
    for value in samples:
        current = value + coefficient * previous - previous2
        previous2, previous = previous, current
    return previous2 ** 2 + previous ** 2 - coefficient * previous2 * previous


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Real encoded AAC requires local FFmpeg")
class MusicMixTests(unittest.TestCase):
    def test_music_rights_and_invalid_audio_fail_closed(self):
        images = stills()
        music = tone_wav(880)
        for kwargs in (
            {"music_wav": music},
            {"music_rights_attested": True},
            {"music_wav": music, "music_rights_attested": 1},
            {"music_wav": b"not a wave", "music_rights_attested": True},
            {"music_wav": tone_wav(880, 29), "music_rights_attested": True},
        ):
            with self.subTest(kwargs=list(kwargs)), self.assertRaises(AnimePilotError):
                render_private_animatic(images, CAPTIONS,
                                        image_rights_attested=True, **kwargs)

    def test_real_aac_mix_contains_both_distinct_tones(self):
        voice = tone_wav(440)
        music = tone_wav(880)
        result = render_private_animatic(
            stills(), CAPTIONS, image_rights_attested=True,
            audio_wav=voice, audio_rights_attested=True,
            music_wav=music, music_rights_attested=True,
        )
        self.assertEqual(result["source_audio_sha256"], hashlib.sha256(voice).hexdigest())
        self.assertEqual(result["source_music_sha256"], hashlib.sha256(music).hexdigest())
        self.assertEqual(result["music_gain"], 0.15)
        self.assertEqual(result["audio_status"], "caller_attested_voice_and_music_wavs_unverified")
        self.assertFalse(result["music_artistic_mix_verified"])
        self.assertFalse(result["hindi_urdu_voice_recorded"])
        self.assertFalse(result["owner_approved"])
        self.assertFalse(result["published"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.mp4"
            path.write_bytes(result["video_mp4"])
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "stream=codec_type,codec_name", "-of", "json", str(path)],
                capture_output=True, text=True, timeout=15, check=True)
            streams = json.loads(probe.stdout)["streams"]
            self.assertEqual(sum(s.get("codec_type") == "audio" for s in streams), 1)
            self.assertTrue(any(s.get("codec_name") == "aac" for s in streams))
            decoded = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-i", str(path), "-t", "1", "-vn", "-ac", "1", "-ar", "16000",
                 "-f", "s16le", "-"],
                capture_output=True, timeout=15, check=True)
            samples = array("h")
            samples.frombytes(decoded.stdout)
            self.assertGreater(len(samples), 15000)
            self.assertGreater(frequency_power(samples[:16000], 440), 1e12)
            self.assertGreater(frequency_power(samples[:16000], 880), 1e10)

    def test_music_only_cli_is_private_and_non_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = []
            for i, data in enumerate(stills()):
                path = root / f"shot{i}.png"
                path.write_bytes(data)
                images.append(path)
            music_path = root / "original.wav"
            music_path.write_bytes(tone_wav(880))
            output = root / "draft"
            cmd = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
            for path in images:
                cmd.extend(["--shot", str(path)])
            for caption in CAPTIONS:
                cmd.extend(["--caption", caption])
            cmd.extend(["--out", str(output), "--image-rights-attested",
                        "--music-wav", str(music_path), "--music-rights-attested"])
            first = subprocess.run(cmd, capture_output=True, text=True, timeout=110)
            self.assertEqual(first.returncode, 0, first.stderr)
            manifest = json.loads((output / "manifest.json").read_text("utf-8"))
            self.assertEqual(manifest["audio_status"], "caller_attested_music_wav_unverified")
            self.assertIsNone(manifest["source_audio_sha256"])
            self.assertEqual(manifest["source_music_sha256"],
                             hashlib.sha256(music_path.read_bytes()).hexdigest())
            self.assertFalse(manifest["owner_approved"])
            self.assertFalse(manifest["published"])
            movie = (output / manifest["filename"]).read_bytes()
            second = subprocess.run(cmd, capture_output=True, text=True, timeout=110)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual((output / manifest["filename"]).read_bytes(), movie)

    def test_music_cli_rights_pair_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = []
            for i, data in enumerate(stills()):
                path = root / f"shot{i}.png"
                path.write_bytes(data)
                images.append(path)
            music_path = root / "music.wav"
            music_path.write_bytes(tone_wav(880))
            for extra in (["--music-wav", str(music_path)],
                          ["--music-rights-attested"]):
                cmd = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
                for path in images:
                    cmd.extend(["--shot", str(path)])
                for caption in CAPTIONS:
                    cmd.extend(["--caption", caption])
                cmd.extend(["--out", str(root / "draft"), "--image-rights-attested"])
                cmd.extend(extra)
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("must be supplied together", proc.stderr)
                self.assertFalse((root / "draft").exists())


if __name__ == "__main__":
    unittest.main()
