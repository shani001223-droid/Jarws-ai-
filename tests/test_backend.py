import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from cloud_backend import main


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


class AssistantApiTests(unittest.TestCase):
    def test_gemini_uses_interactions_api_and_extracts_model_output(self):
        payload = {
            "status": "completed",
            "steps": [
                {"type": "user_input", "content": [{"type": "text", "text": "Hello"}]},
                {"type": "model_output", "content": [{"type": "text", "text": "Hello from Gemini"}]},
            ],
        }
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-key", "GROQ_API_KEY": ""}):
            with patch("cloud_backend.main.urlopen", return_value=FakeResponse(payload)) as mocked:
                result = main.assistant(main.AssistantRequest(message="Hello"))

        self.assertEqual(result.reply, "Hello from Gemini")
        self.assertEqual(result.mode, "gemini")
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://generativelanguage.googleapis.com/v1beta/interactions")
        self.assertEqual(request.get_header("X-goog-api-key"), "test-gemini-key")
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], main.GEMINI_MODEL)
        self.assertEqual(body["input"], "Hello")
        self.assertFalse(body["store"])
        self.assertIn("Roman Urdu", body["system_instruction"])

    def test_gemini_http_404_falls_back_to_groq(self):
        error_body = io.BytesIO(json.dumps({"error": {"message": "test model error"}}).encode("utf-8"))
        gemini_error = HTTPError(
            "https://generativelanguage.googleapis.com/v1beta/interactions",
            404,
            "Not Found",
            {},
            error_body,
        )
        groq_payload = {
            "choices": [{"message": {"content": "Hello from Groq fallback"}}]
        }

        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test-gemini-key",
            "GROQ_API_KEY": "test-groq-key",
        }):
            with patch(
                "cloud_backend.main.urlopen",
                side_effect=[gemini_error, FakeResponse(groq_payload)],
            ) as mocked:
                result = main.assistant(main.AssistantRequest(message="Hello"))

        self.assertEqual(result.reply, "Hello from Groq fallback")
        self.assertEqual(result.mode, "groq")
        self.assertEqual(mocked.call_count, 2)
        fallback_request = mocked.call_args.args[0]
        self.assertEqual(fallback_request.full_url, "https://api.groq.com/openai/v1/chat/completions")


if __name__ == "__main__":
    unittest.main()
