import io
import json
import os
import tempfile
import unittest
import uuid
from unittest.mock import patch

from fastapi import HTTPException
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

    def test_health_reports_interactions_api_and_provider_flags(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test-gemini-key",
            "GROQ_API_KEY": "test-groq-key",
        }):
            health = main.health()

        self.assertEqual(health["version"], "0.9.0")
        self.assertEqual(health["gemini_api"], "interactions")
        self.assertTrue(health["gemini_configured"])
        self.assertTrue(health["groq_configured"])
        self.assertEqual(health["gemini_model"], "gemini-3.8-flash")
        self.assertEqual(health["groq_model"], "openai/gpt-oss-20b")
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
        self.assertEqual(request.get_header("User-agent"), "JARVIS-Cloud-Assistant/0.9.0 (+https://jarws-ai-1.onrender.com)")
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], main.GEMINI_MODEL)
        self.assertEqual(body["input"], "Hello")
        self.assertFalse(body["store"])
        self.assertIn("Roman Urdu", body["system_instruction"])

    def test_groq_403_error_is_diagnosable(self):
        error_body = io.BytesIO(json.dumps({"error": "Project does not have permission to use this model."}).encode("utf-8"))
        groq_error = HTTPError(
            "https://api.groq.com/openai/v1/chat/completions",
            403,
            "Forbidden",
            {},
            error_body,
        )
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-groq-key"}):
            with patch("cloud_backend.main.GROQ_MODEL", "test-model"):
                with patch("cloud_backend.main.urlopen", side_effect=groq_error):
                    with self.assertRaisesRegex(RuntimeError, "permission/model access") as caught:
                        main._groq_reply("Hello", "Reply in English.")
        self.assertIn("test-model", str(caught.exception))
        self.assertIn("does not have permission", str(caught.exception))

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
        self.assertEqual(fallback_request.get_header("User-agent"), "JARVIS-Cloud-Assistant/0.9.0 (+https://jarws-ai-1.onrender.com)")


    def test_conversation_memory_is_used_for_followup_and_persisted(self):
        first_reply = {
            "steps": [{"type": "model_output", "content": [
                {"type": "text", "text": "Nice to meet you, Ali."}
            ]}]
        }
        second_reply = {
            "steps": [{"type": "model_output", "content": [
                {"type": "text", "text": "Your name is Ali."}
            ]}]
        }
        conversation_id = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as memory_dir:
            with patch.dict(os.environ, {
                "GEMINI_API_KEY": "test-gemini-key",
                "GROQ_API_KEY": "",
                "JARVIS_DB_PATH": os.path.join(memory_dir, "memory.sqlite3"),
            }):
                with patch(
                    "cloud_backend.main.urlopen",
                    side_effect=[FakeResponse(first_reply), FakeResponse(second_reply)],
                ) as mocked:
                    main.assistant(main.AssistantRequest(
                        message="My name is Ali.", conversation_id=conversation_id
                    ))
                    result = main.assistant(main.AssistantRequest(
                        message="What is my name?", conversation_id=conversation_id
                    ))

                self.assertEqual(result.reply, "Your name is Ali.")
                second_request = json.loads(mocked.call_args_list[1].args[0].data.decode("utf-8"))
                self.assertIn("My name is Ali.", second_request["input"])
                self.assertIn("Current user message:", second_request["input"])
                history = main.get_recent_history(conversation_id)
                self.assertEqual([turn["role"] for turn in history], [
                    "user", "assistant", "user", "assistant"
                ])
                self.assertEqual(history[-1]["content"], "Your name is Ali.")

    def test_invalid_conversation_id_is_rejected(self):
        with self.assertRaises(HTTPException):
            main.assistant(main.AssistantRequest(
                message="Hello", conversation_id="x" * 36
            ))



if __name__ == "__main__":
    unittest.main()
