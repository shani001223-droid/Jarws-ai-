"""Provider routing guarantees: configured-only, no duplicates, no phantom agent."""
import os
import unittest
from unittest.mock import patch

from cloud_backend.provider_policy import choose_providers
from cloud_backend import main


class ProviderPolicyTests(unittest.TestCase):
    def test_fast_voice_uses_configured_groq_before_others_without_duplicate_fallback(self):
        plan = choose_providers(
            "Kya haal hai", fast=True, groq=True, openrouter=True,
            gemini=True, openjarvis=True,
        )
        self.assertEqual(plan.order, ("groq", "openrouter", "gemini"))
        self.assertTrue(plan.fast_voice_first)
        self.assertFalse(plan.agent_first)

    def test_complex_nonvoice_can_use_real_configured_agent_first(self):
        plan = choose_providers(
            "Compare BTC strategies", fast=False, groq=True,
            gemini=True, openrouter=True, openjarvis=True,
        )
        self.assertEqual(plan.order, ("openjarvis", "openrouter", "gemini", "groq"))
        self.assertTrue(plan.agent_first)

    def test_normal_chat_does_not_call_agent_and_missing_providers_not_added(self):
        plan = choose_providers(
            "Hello Hoshi", fast=False, groq=False, gemini=False,
            openrouter=True, openjarvis=True,
        )
        self.assertEqual(plan.order, ("openrouter",))
        self.assertFalse(plan.agent_first)
        missing = choose_providers(
            "Plan game project", fast=False, groq=False,
            gemini=False, openrouter=False, openjarvis=False,
        )
        self.assertEqual(missing.order, ())
        self.assertIsNone(missing.priority)

    def test_actual_assistant_routes_fast_voice_to_groq_and_avoids_other_network_calls(self):
        env = {"OPENROUTER_API_KEY": "fixture-not-real", "GROQ_API_KEY": "fixture-not-real",
               "GEMINI_API_KEY": "fixture-not-real", "OPENJARVIS_URL": "", "OPENJARVIS_MODEL": ""}
        with patch.dict(os.environ, env):
            with patch.object(main, "_groq_reply", return_value="I'm Hoshi.") as groq:
                with patch.object(main, "_openrouter_reply") as router:
                    with patch.object(main, "urlopen") as network:
                        answer=main.assistant(main.AssistantRequest(message="Hello Hoshi",fast=True))
        self.assertEqual(answer.mode, "groq")
        self.assertEqual(groq.call_count, 1)
        router.assert_not_called()
        network.assert_not_called()

    def test_actual_assistant_normal_text_uses_configured_openrouter(self):
        env={"OPENROUTER_API_KEY":"fixture-only","GROQ_API_KEY":"fixture-only",
             "GEMINI_API_KEY":"","OPENJARVIS_URL":"","OPENJARVIS_MODEL":""}
        with patch.dict(os.environ,env):
            with patch.object(main,"_openrouter_reply",return_value="A clear reply.") as route:
                with patch.object(main,"_groq_reply") as backup:
                    answer=main.assistant(main.AssistantRequest(message="Tell me a story"))
        self.assertEqual(answer.mode,"openrouter")
        route.assert_called_once()
        backup.assert_not_called()


if __name__=="__main__":
    unittest.main()
