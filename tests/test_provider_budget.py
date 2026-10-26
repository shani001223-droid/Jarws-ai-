"""Provider latency safety: no 60-second serial fallback after client timeout."""
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from cloud_backend import main
from cloud_backend.free_llm_providers import ask_free_provider


class ProviderBudgetTests(unittest.TestCase):
    def env(self):
        return patch.dict(os.environ,{
            "OPENROUTER_API_KEY":"","GEMINI_API_KEY":"","GROQ_API_KEY":"",
            "OPENJARVIS_URL":"","OPENJARVIS_MODEL":"",
            "ZAI_API_KEY":"test-fixture","MISTRAL_API_KEY":"","NVIDIA_API_KEY":"",
        })

    def test_free_provider_receives_bounded_timeout_when_budget_is_available(self):
        with self.env():
            with patch.object(main.time,"monotonic",side_effect=[100.0,101.0]):
                with patch.object(main,"ask_free_provider",return_value="Fast answer.") as called:
                    answer=main.assistant(main.AssistantRequest(message="Describe the stars"))
        self.assertEqual(answer.mode,"zai")
        self.assertEqual(called.call_count,1)
        self.assertLessEqual(called.call_args.kwargs["timeout"],5.0)

    def test_no_optional_request_starts_after_latency_budget_is_exhausted(self):
        with self.env():
            with patch.object(main.time,"monotonic",side_effect=[100.0,129.0]):
                with patch.object(main,"ask_free_provider") as called:
                    with self.assertRaises(HTTPException) as raised:
                        main.assistant(main.AssistantRequest(message="Describe the stars"))
        called.assert_not_called()
        self.assertEqual(raised.exception.status_code,503)

    def test_openrouter_fast_timeout_and_groq_preserve_single_attempt(self):
        # The full backend suite separately asserts the actual network-request
        # timeout values, while this test checks routing stays idempotent.
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":"fixture",
                                    "GROQ_API_KEY":"fixture",
                                    "GEMINI_API_KEY":"",
                                    "ZAI_API_KEY":""}):
            with patch.object(main,"_groq_reply",return_value="Hi Hoshi") as called:
                answer=main.assistant(main.AssistantRequest(message="Hello Hoshi",fast=True))
        self.assertEqual(answer.mode,"groq")
        called.assert_called_once()


if __name__=="__main__":
    unittest.main()
