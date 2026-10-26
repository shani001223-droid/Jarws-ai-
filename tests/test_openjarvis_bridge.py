"""Integration tests: real OpenJarvis-compatible HTTP contract, no real network."""
import json
import os
import unittest
from unittest.mock import patch

from cloud_backend import main
from cloud_backend import openjarvis_bridge as oj
from cloud_backend.agent_tools import try_calculate


class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, limit=200001):
        return self.data[:limit]


class FakeOpener:
    def __init__(self, data):
        self.data = data
        self.request = None
        self.timeout = None
    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return FakeResponse(self.data)


class OpenJarvisBridgeTests(unittest.TestCase):
    def env(self, **more):
        return patch.dict(os.environ, {
            "OPENJARVIS_URL": "", "OPENJARVIS_MODEL": "", "OPENJARVIS_API_KEY": "",
            "OPENROUTER_API_KEY": "", "GEMINI_API_KEY": "", "GROQ_API_KEY": "",
            **more,
        }, clear=False)

    def test_connector_requires_own_model_and_endpoint(self):
        with self.env(OPENJARVIS_URL="https://agent.example.org"):
            self.assertIsNone(oj.endpoint())
        with self.env(OPENJARVIS_MODEL="qwen3:4b"):
            self.assertIsNone(oj.endpoint())
        with self.env(OPENJARVIS_MODEL="qwen3:4b", OPENJARVIS_URL="https://agent.example.org/v1"):
            self.assertEqual(oj.endpoint(), ("https://agent.example.org/v1/chat/completions", "qwen3:4b"))

    def test_remote_must_be_https_and_safe_url(self):
        for unsafe in ("http://agent.example.org", "file:///etc/passwd",
                       "https://username:secret@agent.example.org",
                       "https://agent.example.org/v1/?token=x"):
            with self.env(OPENJARVIS_MODEL="qwen3:4b", OPENJARVIS_URL=unsafe):
                with self.assertRaises(oj.OpenJarvisUnavailable):
                    oj.endpoint()
        with self.env(OPENJARVIS_MODEL="qwen3:4b", OPENJARVIS_URL="http://127.0.0.1:8000"):
            self.assertEqual(oj.endpoint()[0], "http://127.0.0.1:8000/v1/chat/completions")

    def test_real_openjarvis_contract_and_private_key_header(self):
        fake = FakeOpener({"choices": [{"message": {"content": "Here are three steps."}}]})
        with self.env(OPENJARVIS_URL="https://agent.example.org", OPENJARVIS_MODEL="qwen3:4b", OPENJARVIS_API_KEY="private-test-only"):
            with patch("urllib.request.build_opener", return_value=fake):
                result = oj.ask_openjarvis("Please plan this", "System guidance", timeout=7)
        self.assertEqual(result, "Here are three steps.")
        self.assertEqual(fake.request.full_url, "https://agent.example.org/v1/chat/completions")
        body = json.loads(fake.request.data)
        self.assertEqual(body["model"], "qwen3:4b")
        self.assertEqual(body["messages"][-1]["content"], "Please plan this")
        self.assertFalse(body["stream"])
        self.assertEqual(fake.timeout, 7)
        self.assertEqual(fake.request.get_header("Authorization"), "Bearer private-test-only")

    def test_agent_mode_is_only_used_for_complex_nonfast_requests(self):
        self.assertTrue(oj.wants_agent("compare these strategies",fast=False))
        self.assertTrue(oj.wants_agent("explain this carefully",fast=False))
        self.assertFalse(oj.wants_agent("Hello!",fast=False))
        self.assertFalse(oj.wants_agent("compare these strategies",fast=True))

    def test_backend_selects_actual_openjarvis_agent_for_complex_request(self):
        with self.env(OPENJARVIS_URL="https://agent.example.org", OPENJARVIS_MODEL="qwen3:4b"):
            with patch.object(main, "ask_openjarvis", return_value="A verified plan.") as called:
                reply=main.assistant(main.AssistantRequest(message="Plan my week in detail",locale="en"))
                health=main.health()
        self.assertEqual(reply.mode,"openjarvis")
        self.assertEqual(reply.reply,"A verified plan.")
        self.assertEqual(called.call_args.kwargs["timeout"],7)
        self.assertTrue(health["openjarvis_configured"])

    def test_unavailable_agent_falls_back_without_retries(self):
        with self.env(OPENJARVIS_URL="https://agent.example.org",OPENJARVIS_MODEL="qwen3:4b",GROQ_API_KEY="test"):
            with patch.object(main,"ask_openjarvis",side_effect=oj.OpenJarvisUnavailable("offline")) as agent:
                with patch.object(main,"_groq_reply",return_value="Safe fallback") as backup:
                    answer=main.assistant(main.AssistantRequest(message="Explain gravity",locale="en"))
        self.assertEqual(answer.mode,"groq")
        self.assertEqual(agent.call_count,1)
        self.assertEqual(backup.call_count,1)

    def test_calculator_is_instant_and_requires_no_ai_key(self):
        self.assertEqual(try_calculate("calculate (23 + 7) * 4"), "120")
        self.assertEqual(try_calculate("what is 19/2?"), "9.5")
        self.assertEqual(try_calculate("2^3"), "8")
        self.assertIsNone(try_calculate("delete files"))
        self.assertIsNone(try_calculate("2**1000000"))
        with self.env():
            with patch.object(main,"urlopen") as network:
                response=main.assistant(main.AssistantRequest(message="23 * 7",locale="ur-PK"))
        self.assertEqual(response.mode,"calculator")
        self.assertEqual(response.reply,"Jawab: 161")
        self.assertIn("جواب",response.speech_text)
        network.assert_not_called()


if __name__=="__main__":
    unittest.main()
