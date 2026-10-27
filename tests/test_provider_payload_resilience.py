"""Regression coverage for successful HTTP responses with malformed provider JSON.

Provider-side API changes must never cause an unhandled AttributeError/500.
"""
import json
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from cloud_backend import main


class JsonReply:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self):
        return self.payload


class ProviderResponseResilienceTests(unittest.TestCase):
    def test_groq_unexpected_json_top_level_is_a_controlled_error(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-only"}):
            for bad_payload in ([], None, "unexpected", {"choices": {}}):
                with self.subTest(payload=repr(bad_payload)):
                    with patch("cloud_backend.main.urlopen", return_value=JsonReply(bad_payload)):
                        with self.assertRaisesRegex(RuntimeError, "invalid response"):
                            main._groq_reply("Hello", "Reply briefly.")

    def test_groq_invalid_choice_and_message_are_a_controlled_error(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "fixture-only"}):
            for bad_payload in ({"choices": [None]}, {"choices": ["wrong"]},
                                {"choices": [{"message": []}]},
                                {"choices": [{"message": {"content": ["invalid"]}}]}):
                with self.subTest(payload=repr(bad_payload)):
                    with patch("cloud_backend.main.urlopen", return_value=JsonReply(bad_payload)):
                        with self.assertRaisesRegex(RuntimeError, "invalid response"):
                            main._groq_reply("Hello", "Reply briefly.")

    def test_gemini_malformed_success_json_becomes_actionable_gateway_error(self):
        isolated = {"OPENROUTER_API_KEY": "", "GROQ_API_KEY": "", "GEMINI_API_KEY": "fixture-only",
                    "OPENJARVIS_URL": "", "OPENJARVIS_MODEL": ""}
        with patch.dict(os.environ, isolated):
            for bad_payload in ([], None, {"steps": ["not-a-step"]},
                                {"steps": [{"type": "model_output", "content": [None]}]}):
                with self.subTest(payload=repr(bad_payload)):
                    with patch("cloud_backend.main.urlopen", return_value=JsonReply(bad_payload)):
                        with self.assertRaises(HTTPException) as error:
                            main.assistant(main.AssistantRequest(message="Please describe a star."))
                        self.assertEqual(error.exception.status_code, 503)
                        self.assertIn("invalid response", error.exception.detail)
                        self.assertNotIn("fixture-only", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
