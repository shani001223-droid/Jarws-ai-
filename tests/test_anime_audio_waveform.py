"""Deterministic, bounded waveform evidence from private encoded AAC WAV excerpts."""
from __future__ import annotations

from io import BytesIO
import copy
import hashlib
import math
import struct
import unittest
import wave

from PIL import Image

from cloud_backend.anime_audio_waveform import (
    AnimeAudioWaveformError, build_encoded_audio_waveform,
)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class EncodedAudioWaveformTests(unittest.TestCase):
    def setUp(self):
        self.clips = []
        self.records = []
        for index in range(3):
            raw = b"".join(struct.pack("<h", round(
                5000 * math.sin(2 * math.pi * 440 * n / 16000)))
                for n in range(16000))
            buffer = BytesIO()
            with wave.open(buffer, "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(16000)
                audio.writeframes(raw)
            data = buffer.getvalue()
            filename = f"hoshi_cue_{index + 1}_PRIVATE_REVIEW.wav"
            self.clips.append({"filename": filename, "wav_bytes": data})
            self.records.append({
                "shot_index": index + 1, "filename": filename,
                "cue_start_ms": index * 10000 + 250,
                "cue_end_ms": index * 10000 + 750,
                "excerpt_start_ms": index * 10000,
                "excerpt_end_ms_requested": index * 10000 + 1000,
                "decoded_pcm_sample_count": 16000,
                "sample_rate_hz": 16000, "channels": 1,
                "sample_width_bytes": 2, "wav_sha256": sha(data),
                "decoded_from_actual_captioned_mp4_aac": True,
                "spoken_words_independently_verified": False,
                "phoneme_sync_verified": False,
            })

    def test_actual_pcm_samples_drawn_and_sha_bound(self):
        result = build_encoded_audio_waveform(self.clips, self.records)
        self.assertEqual(result["status"],
                         "actual_encoded_aac_waveform_human_review_only")
        self.assertEqual(result["resolution"], [1440, 660])
        self.assertEqual(result["png_sha256"], sha(result["png_bytes"]))
        self.assertEqual(len(result["samples"]), 3)
        self.assertTrue(all(0.1 < entry["measured_peak_normalized"] < 0.2
                            for entry in result["samples"]))
        self.assertFalse(result["spoken_words_independently_verified"])
        self.assertFalse(result["phoneme_sync_verified"])
        self.assertFalse(result["publication_permitted"])
        with Image.open(BytesIO(result["png_bytes"])) as image:
            self.assertEqual(image.size, (1440, 660))
            self.assertEqual(image.format, "PNG")
        self.assertEqual(result["png_bytes"], build_encoded_audio_waveform(
            self.clips, self.records)["png_bytes"])

    def test_no_encoded_aac_does_not_fabricate_waveform(self):
        result = build_encoded_audio_waveform([], [])
        self.assertIsNone(result["png_bytes"])
        self.assertEqual(result["status"], "no_encoded_aac_no_waveform")
        with self.assertRaises(AnimeAudioWaveformError):
            build_encoded_audio_waveform([], self.records)

    def test_forged_wav_timing_header_and_rights_claims_rejected(self):
        clips = copy.deepcopy(self.clips)
        clips[0]["wav_bytes"] += b"forged"
        with self.assertRaises(AnimeAudioWaveformError):
            build_encoded_audio_waveform(clips, self.records)
        for key, value in (
            ("decoded_pcm_sample_count", 15999),
            ("cue_end_ms", 11000),
            ("sample_rate_hz", 44100),
            ("spoken_words_independently_verified", True),
            ("decoded_from_actual_captioned_mp4_aac", False),
        ):
            records = copy.deepcopy(self.records)
            records[0][key] = value
            with self.subTest(key=key), self.assertRaises(AnimeAudioWaveformError):
                build_encoded_audio_waveform(self.clips, records)
        clips = copy.deepcopy(self.clips)
        clips[0]["wav_bytes"] = b"not a wave"
        records = copy.deepcopy(self.records)
        records[0]["wav_sha256"] = sha(clips[0]["wav_bytes"])
        with self.assertRaises(AnimeAudioWaveformError):
            build_encoded_audio_waveform(clips, records)


if __name__ == "__main__":
    unittest.main()
