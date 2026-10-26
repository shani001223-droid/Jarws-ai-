"""Regression tests for structured companion metadata without relying on AI providers."""
import json
import math
import unittest

from cloud_backend.emotions import companion_state
from cloud_backend.main import make_assistant_response


class HoshiEmotionMetadataTests(unittest.TestCase):
    def test_full_valid_metadata_is_retained(self):
        answer = json.dumps({
            "reply": "Tum mujhse naraz ho?",
            "speech_text": "تم مجھ سے ناراض ہو؟",
            "emotion": "sad",
            "emotion_intensity": 0.7,
            "animation": "sad_eyes",
            "gesture": "look_down",
            "voice_style": "gentle",
        })
        result = make_assistant_response(answer, "test", "Main naraz hoon", "ur-PK")
        self.assertEqual(result.reply, "Tum mujhse naraz ho?")
        self.assertEqual(result.speech_text, "تم مجھ سے ناراض ہو؟")
        self.assertEqual(result.emotion, "sad")
        self.assertEqual(result.emotion_intensity, 0.7)
        self.assertEqual(result.animation, "sad_eyes")
        self.assertEqual(result.gesture, "look_down")
        self.assertEqual(result.voice_style, "gentle")

    def test_invalid_provider_states_reset_to_safe_defaults(self):
        state = companion_state({
            "emotion": "controlling",
            "emotion_intensity": 999,
            "animation": "replace_character_with_generic_avatar",
            "gesture": "capture_screen",
            "voice_style": "paid_voice",
        }, "worried")
        self.assertEqual(state, {
            "emotion": "neutral",
            "emotion_intensity": 0.45,
            "animation": "idle",
            "gesture": "none",
            "voice_style": "soft",
        })

    def test_bad_intensity_types_and_nan_do_not_bypass_validation(self):
        for invalid in (-1, 2, True, "0.7", float("nan"), float("inf")):
            with self.subTest(value=repr(invalid)):
                self.assertEqual(companion_state({"emotion_intensity": invalid})["emotion_intensity"], 0.45)

    def test_missing_metadata_retains_existing_classifier_and_voice(self):
        response = make_assistant_response(
            json.dumps({"reply": "Main tumhari baat sun rahi hoon.",
                        "speech_text": "میں تمہاری بات سن رہی ہوں۔"}),
            "openrouter", "Main naraz hoon", "ur-PK",
        )
        self.assertIn(response.emotion, {"caring", "concerned", "annoyed", "neutral"})
        self.assertEqual(response.animation, "idle")
        self.assertEqual(response.gesture, "none")
        self.assertEqual(response.voice_style, "soft")


if __name__ == "__main__":
    unittest.main()
