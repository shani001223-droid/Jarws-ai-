"""Offline energy handoff tests; activity is not speech or lip-sync."""
from __future__ import annotations

import hashlib
from io import BytesIO
import math
import struct
import unittest
import wave

from cloud_backend.anime_audio_energy import AudioEnergyError, build_audio_energy_handoff


class AudioEnergyTests(unittest.TestCase):
    def _wav(self, audible=False):
        rate = 16000
        output = BytesIO()
        with wave.open(output, "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            if audible:
                samples = (
                    int(12000 * math.sin(2 * math.pi * 440 * index / rate))
                    if rate <= index < rate * 3 else 0
                    for index in range(rate * 30)
                )
                stream.writeframes(b"".join(struct.pack("<h", value) for value in samples))
            else:
                stream.writeframes(bytes(rate * 30 * 2))
        return output.getvalue()

    def _plan(self, wav):
        return {
            "plan_sha256": "f" * 64,
            "plan": {
                "audio_sha256": hashlib.sha256(wav).hexdigest(),
                "cues": [
                    {"shot_id": f"shot{i}", "speaker_id": "hero",
                     "start_ms": i * 10000 + 500,
                     "end_ms": i * 10000 + 9500}
                    for i in range(3)
                ]
            }
        }

    def test_silent_audio_does_not_fake_mouth_motion(self):
        wav = self._wav()
        result = build_audio_energy_handoff(wav, self._plan(wav))
        self.assertEqual(result["frames_analyzed"], 360)
        self.assertEqual(result["active_frames"], 0)
        self.assertEqual([s["energy_windows_ms"] for s in result["shots"]], [[], [], []])
        self.assertFalse(result["lip_sync_generated"])
        self.assertFalse(result["character_animation_generated"])

    def test_audio_energy_is_clamped_to_speaker_cue(self):
        wav = self._wav(audible=True)
        result = build_audio_energy_handoff(wav, self._plan(wav))
        self.assertEqual(result["shots"][0]["energy_windows_ms"], [[1000, 3000]])
        self.assertEqual(result["shots"][1]["energy_windows_ms"], [])
        self.assertEqual(result["shots"][2]["energy_windows_ms"], [])
        self.assertEqual(result["active_frames"], 24)
        self.assertEqual(result["audio_sha256"], hashlib.sha256(wav).hexdigest())
        self.assertEqual(result["voice_timing_sha256"], "f" * 64)
        self.assertIn("not_speech", result["source"])

    def test_wrong_wav_or_bad_cue_fails_closed(self):
        wav = self._wav()
        plan = self._plan(wav)
        with self.assertRaises(AudioEnergyError):
            build_audio_energy_handoff(wav + b"x", plan)
        with self.assertRaises(AudioEnergyError):
            build_audio_energy_handoff(wav, {"plan": {"cues": []}})
        plan["plan"]["cues"][0]["start_ms"] = True
        with self.assertRaises(AudioEnergyError):
            build_audio_energy_handoff(wav, plan)

    def test_invalid_wav_rejected(self):
        wav = self._wav()
        with self.assertRaises(AudioEnergyError):
            build_audio_energy_handoff(b"not a wav", self._plan(wav))


if __name__ == "__main__":
    unittest.main()
