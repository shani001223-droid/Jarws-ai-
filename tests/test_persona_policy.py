"""Personality continuity tests for fast voice and full Hoshi model routes.

Mocks prove that provider prompts contain boundaries, not that an external
model will always obey them; real voice/personality QA remains pending.
"""
import json
import os
import unittest
from unittest.mock import patch

from cloud_backend import main
from cloud_backend.persona_policy import personality_guardrails, _asks_for_less_affection


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class PersonaPolicyTests(unittest.TestCase):
    def test_boundaries_are_recognized_in_roman_urdu_and_english(self):
        for message in ("Mujhe jaan mat kaho", "Flirting band karo", "Don't flirt with me",
                        "Stop calling me baby", "Please avoid pet names"):
            with self.subTest(message=message):
                self.assertTrue(_asks_for_less_affection(message))
                prompt = personality_guardrails(message, "affectionate")
                self.assertIn("Honor this boundary now", prompt)
        self.assertFalse(_asks_for_less_affection("Main tumse pyar karta hoon"))
        self.assertFalse(_asks_for_less_affection("Kya tum mere sath masti karogi?"))

    def test_shared_policy_contains_nonmanipulative_rules_for_all_moods(self):
        for mood in ("sad", "anxious", "annoyed", "affectionate", "playful", "neutral"):
            for concise in (True, False):
                with self.subTest(mood=mood, concise=concise):
                    prompt = personality_guardrails("Hello", mood, concise=concise)
                    self.assertIn("Never threaten to cry", prompt)
                    self.assertIn("instead of real people", prompt)
                    self.assertIn("without evidence", prompt)
                    self.assertIn("fictional and age-appropriate", prompt)
                    self.assertLess(len(prompt), 1300)

    def test_fast_groq_voice_gets_mood_and_boundary_policy(self):
        raw = json.dumps({"reply": "Theek hai, main neutral rahungi.",
                          "speech_text": "ٹھیک ہے، میں نیوٹرل رہوں گی۔"})
        response = FakeResponse({"choices": [{"message": {"content": raw}}]})
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "", "GEMINI_API_KEY": "",
                                     "GROQ_API_KEY": "fixture", "ZAI_API_KEY": "",
                                     "MISTRAL_API_KEY": "", "NVIDIA_API_KEY": ""}):
            with patch("cloud_backend.main.urlopen", return_value=response) as mocked:
                answer = main.assistant(main.AssistantRequest(
                    message="Jaan mat kaho, main gussa hoon", personality="affectionate",
                    locale="ur-PK", fast=True))
        self.assertEqual(answer.mode, "groq")
        body = json.loads(mocked.call_args.args[0].data)
        system = body["messages"][0]["content"]
        self.assertIn("Likely user mood: annoyed", system)
        self.assertIn("Honor this boundary now", system)
        self.assertIn("Never threaten to cry", system)
        self.assertIn("fictional and age-appropriate", system)
        self.assertEqual(body["max_tokens"], 240)

    def test_gemini_full_prompt_keeps_boundary_and_task_accuracy(self):
        response = FakeResponse({"steps": [{"type": "model_output",
                                            "content": [{"type": "text", "text": "Understood."}]}]})
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "", "GROQ_API_KEY": "",
                                     "GEMINI_API_KEY": "fixture", "ZAI_API_KEY": "",
                                     "MISTRAL_API_KEY": "", "NVIDIA_API_KEY": ""}):
            with patch("cloud_backend.main.urlopen", return_value=response) as mocked:
                answer = main.assistant(main.AssistantRequest(
                    message="Please stop calling me baby.", personality="affectionate"))
        self.assertEqual(answer.mode, "gemini")
        body = json.loads(mocked.call_args.args[0].data)
        system = body["system_instruction"]
        self.assertIn("Honor this boundary now", system)
        self.assertIn("Never imply the user must rely on Hoshi", system)
        self.assertIn("without evidence", system)
        self.assertIn("Do not repeat greetings", system)


if __name__ == "__main__":
    unittest.main()
