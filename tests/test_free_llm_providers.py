"""No-network tests for Free-LLM-directory provider adapters and Hoshi routing."""
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO

from cloud_backend import main
from cloud_backend.free_llm_providers import (
    OptionalProviderError, available_free_providers, ask_free_provider,
)
from cloud_backend.provider_policy import choose_providers


class FakeHTTPResponse:
    def __init__(self, payload):
        self.raw = json.dumps(payload).encode("utf-8") if not isinstance(payload, bytes) else payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, n=128001):
        return self.raw[:n]


class FakeOpener:
    def __init__(self, result):
        self.result = result
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return FakeHTTPResponse(self.result)


class FreeLLMProviderTests(unittest.TestCase):
    def env(self, **extras):
        defaults = {
            "OPENROUTER_API_KEY": "", "GEMINI_API_KEY": "", "GROQ_API_KEY": "",
            "OPENJARVIS_URL": "", "OPENJARVIS_MODEL": "",
            "ZAI_API_KEY": "", "MISTRAL_API_KEY": "", "NVIDIA_API_KEY": "",
            "MISTRAL_FREE_MODE": "", "NVIDIA_PROTOTYPE_MODE": "",
        }
        defaults.update(extras)
        return patch.dict(os.environ, defaults)

    def test_keys_are_optional_and_opt_in_guards_block_paid_or_production_modes(self):
        with self.env(ZAI_API_KEY="fake-z", MISTRAL_API_KEY="fake-m",
                      NVIDIA_API_KEY="fake-n"):
            self.assertEqual(available_free_providers(), ("zai",))
        with self.env(ZAI_API_KEY="fake-z", MISTRAL_API_KEY="fake-m",
                      NVIDIA_API_KEY="fake-n", MISTRAL_FREE_MODE="true",
                      NVIDIA_PROTOTYPE_MODE="true"):
            self.assertEqual(available_free_providers(), ("zai", "mistral", "nvidia"))

    def test_provider_requests_use_only_fixed_https_hosts_and_free_catalog_model(self):
        cases = [
            ("zai", "ZAI_API_KEY", "https://api.z.ai/api/paas/v4/chat/completions", "glm-4.5-flash", {}),
            ("mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1/chat/completions", "mistral-small-latest", {"MISTRAL_FREE_MODE": "true"}),
            ("nvidia", "NVIDIA_API_KEY", "https://integrate.api.nvidia.com/v1/chat/completions", "meta/llama-3.1-8b-instruct", {"NVIDIA_PROTOTYPE_MODE": "true"}),
        ]
        for name, key, url, model, flags in cases:
            fake = FakeOpener({"choices": [{"message": {"content": "Tested answer"}}]})
            with self.subTest(provider=name):
                with self.env(**{key: "test-only-key", **flags, "ZAI_MODEL": "paid-model",
                                 "MISTRAL_MODEL": "paid-model", "NVIDIA_MODEL": "paid-model"}):
                    with patch("urllib.request.build_opener", return_value=fake):
                        result = ask_free_provider(name, "hello", "Answer in Roman Urdu")
                self.assertEqual(result, "Tested answer")
                self.assertEqual(fake.request.full_url, url)
                self.assertEqual(json.loads(fake.request.data)["model"], model)
                self.assertEqual(fake.request.get_header("Authorization"), "Bearer test-only-key")
                self.assertEqual(fake.timeout, 8)

    def test_invalid_or_truncated_reply_has_sanitized_error(self):
        for result in ({}, {"choices": [{"message": {"content": ""}}]},
                       {"choices": [{"message": {"content": "partial"}, "finish_reason": "length"}]}):
            fake = FakeOpener(result)
            with self.env(ZAI_API_KEY="secret-DO-NOT-LOG"):
                with patch("urllib.request.build_opener", return_value=fake):
                    with self.assertRaises(OptionalProviderError) as error:
                        ask_free_provider("zai", "PRIVATE INPUT", "PRIVATE INSTRUCTION")
            self.assertNotIn("secret-DO-NOT-LOG", str(error.exception))
            self.assertNotIn("PRIVATE INPUT", str(error.exception))

    def test_fixed_provider_priority_never_duplicates(self):
        plan = choose_providers(
            "hello", fast=True, openrouter=True, gemini=True, groq=True,
            openjarvis=True, zai=True, mistral=True, nvidia=True)
        self.assertEqual(plan.order, ("groq", "openrouter", "gemini", "zai", "mistral", "nvidia"))

    def test_zai_can_act_as_only_available_ai_provider(self):
        with self.env(ZAI_API_KEY="fake-only"):
            with patch.object(main, "ask_free_provider", return_value="Main Hoshi hoon.") as ask:
                output = main.assistant(main.AssistantRequest(message="Tell me about science"))
                health = main.health()
        self.assertEqual(output.mode, "zai")
        self.assertEqual(output.reply, "Main Hoshi hoon.")
        ask.assert_called_once()
        self.assertEqual(health["extra_free_providers_configured"], ["zai"])

    def test_openrouter_failure_then_zai_fallback(self):
        with self.env(ZAI_API_KEY="fake-z", OPENROUTER_API_KEY="fake-or"):
            with patch.object(main, "_openrouter_reply", side_effect=RuntimeError("rate limit")):
                with patch.object(main, "ask_free_provider", return_value="Backup answer") as backup:
                    output = main.assistant(main.AssistantRequest(message="Explain a planet"))
        self.assertEqual(output.mode, "zai")
        backup.assert_called_once()

    def test_failure_of_first_optional_provider_falls_back_once_to_next(self):
        with self.env(ZAI_API_KEY="fake-z", MISTRAL_API_KEY="fake-m",
                      MISTRAL_FREE_MODE="true"):
            with patch.object(main, "ask_free_provider", side_effect=[
                OptionalProviderError("zai HTTP 429"), "Mistral answer"
            ]) as called:
                output = main.assistant(main.AssistantRequest(message="Explain gravity"))
        self.assertEqual(output.mode, "mistral")
        self.assertEqual(called.call_count, 2)

    def test_user_urdu_mode_preserves_speech_contract(self):
        valid = '{"reply":"Main Hoshi hoon.","speech_text":"میں ہوشی ہوں۔"}'
        with self.env(ZAI_API_KEY="fake-z"):
            with patch.object(main, "ask_free_provider", return_value=valid):
                output = main.assistant(main.AssistantRequest(message="salam", locale="ur-PK"))
        self.assertEqual(output.mode, "zai")
        self.assertIn("میں", output.speech_text)

    def test_disallowed_provider_never_sends_network_request(self):
        with self.env(NVIDIA_API_KEY="fake-secret", NVIDIA_PROTOTYPE_MODE="false"):
            with patch("urllib.request.build_opener") as network:
                with self.assertRaises(OptionalProviderError):
                    ask_free_provider("nvidia", "test", "instruction")
                network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
