"""Task 46: actual offline MP4 encoding, safety and provenance gates."""
import hashlib
from io import BytesIO
import math
import shutil
import struct
import unittest
from unittest.mock import patch
import wave

from PIL import Image

from cloud_backend import flora_video_ads as video


def synthetic_photo():
    image = Image.new("RGB", (800, 1000), (45, 95, 145))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def original_test_tone():
    """Synthesized by this test; no third-party copyrighted recording."""
    rate = 16000
    frames = bytearray()
    for index in range(rate * 3):
        value = int(500 * math.sin(2 * math.pi * 220 * index / rate))
        frames.extend(struct.pack("<h", value))
    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(bytes(frames))
    return output.getvalue()


class FloraVideoTests(unittest.TestCase):
    def test_fail_closed_on_unapproved_audio_or_bad_inputs(self):
        photo = synthetic_photo()
        tone = original_test_tone()
        for kwargs in (
            {"placement": "../story"},
            {"audio_wav": tone},
            {"audio_wav": b"bad", "audio_rights_attested": True},
            {"audio_rights_attested": True},
            {"audio_rights_attested": 1},
        ):
            with self.subTest(kwargs=tuple(kwargs)):
                with self.assertRaises(video.FloraVideoError):
                    video.render_flora_video_draft("shampoo", photo, "image/png", **kwargs)
        with self.assertRaises(video.FloraVideoError):
            video.render_flora_video_draft("not_a_product", photo, "image/png")
        with self.assertRaises(video.FloraVideoError):
            video.render_flora_video_draft("gold_kit", b"bad", "image/png")

    def test_missing_ffmpeg_fails_closed(self):
        with patch.object(video.shutil, "which", return_value=None):
            with self.assertRaisesRegex(video.FloraVideoError, "FFmpeg"):
                video.render_flora_video_draft("shampoo", synthetic_photo(), "image/png")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Offline FFmpeg not installed; actual MP4 acceptance pending")
    def test_real_silent_mp4_and_metadata(self):
        result = video.render_flora_video_draft("gold_kit", synthetic_photo(), "image/png")
        self.assertTrue(result["video_mp4"][4:8] == b"ftyp")
        self.assertEqual(result["video_sha256"], hashlib.sha256(result["video_mp4"]).hexdigest())
        self.assertEqual(result["canvas_px"], [360, 640])
        self.assertEqual(result["duration_seconds"], 3)
        self.assertEqual(result["audio_status"], "silent_no_music")
        self.assertIn("DRAFT", result["filename"])
        for flag in ("approved_for_publication", "published", "scheduled", "saved",
                     "photo_rights_independently_verified", "audio_rights_independently_verified",
                     "current_price_independently_verified"):
            self.assertFalse(result[flag], flag)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Offline FFmpeg not installed; actual audio acceptance pending")
    def test_original_test_audio_is_aac_but_not_rights_approved(self):
        result = video.render_flora_video_draft(
            "shampoo", synthetic_photo(), "image/png", "feed",
            audio_wav=original_test_tone(), audio_rights_attested=True)
        self.assertEqual(result["canvas_px"], [360, 450])
        self.assertEqual(result["audio_status"], "caller_supplied_wav_rights_unverified")
        self.assertFalse(result["audio_rights_independently_verified"])
        self.assertFalse(result["approved_for_publication"])


if __name__ == "__main__":
    unittest.main()
