"""Regression tests for modular JARVIS API and service."""
import os, tempfile, unittest
from unittest.mock import patch
from fastapi import HTTPException
from cloud_backend import main
from cloud_backend.jarvis_app import memory, service
from cloud_backend.jarvis_app.providers import gemini_input, trim_history

class ModularBackendTests(unittest.TestCase):
    def test_health_contract_preserves_dashboard_fields(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY":"g", "GROQ_API_KEY":"q"}): result = main.health()
        self.assertTrue(result["ok"]); self.assertEqual(result["gemini_api"], "interactions")
        self.assertTrue(result["gemini_configured"]); self.assertTrue(result["groq_configured"])
        self.assertEqual(main.root()["assistant"], "/api/assistant")
    def test_api_payload_and_response_contract(self):
        payload = main.AssistantRequest(message="Hello", locale="en")
        with patch("cloud_backend.jarvis_app.api.answer_message", return_value=("Hi there", "gemini")): result = main.assistant(payload)
        self.assertEqual(result.reply, "Hi there"); self.assertEqual(result.mode, "gemini")
    def test_history_is_bounded_and_ordered(self):
        history = [{"role":"user", "content":f"message {i}"} for i in range(20)]; result = trim_history(history)
        self.assertLessEqual(len(result), 12); self.assertEqual(result[-1]["content"], "message 19")
    def test_gemini_input_has_context_and_current_message(self):
        prompt = gemini_input("current", [{"role":"user", "content":"previous"}])
        self.assertIn("User: previous", prompt); self.assertIn("Current user message:", prompt); self.assertIn("current", prompt)
    def test_invalid_conversation_id_returns_400(self):
        with self.assertRaises(HTTPException) as ctx: service.canonical_conversation_id("not-a-uuid")
        self.assertEqual(ctx.exception.status_code, 400)
    def test_blank_message_returns_400(self):
        with self.assertRaises(HTTPException) as ctx: service.answer_message(" ")
        self.assertEqual(ctx.exception.status_code, 400)
    def test_memory_save_and_retrieve_isolated_by_conversation(self):
        with tempfile.TemporaryDirectory() as temp, patch("cloud_backend.jarvis_app.memory.get_settings") as settings:
            settings.return_value = type("Settings", (), {"db_path":os.path.join(temp,"memory.db"), "memory_retention_days":30})()
            memory.save_turn("conversation-A", "Hello", "Hi"); memory.save_turn("conversation-B", "Other", "Answer")
            self.assertEqual(memory.get_recent_history("conversation-A"), [{"role":"user","content":"Hello"},{"role":"assistant","content":"Hi"}])
    def test_gemini_success(self):
        fake = type("Settings", (), {"gemini_api_key":"test", "groq_api_key":"", "gemini_model":"model", "groq_model":"fallback"})()
        with patch("cloud_backend.jarvis_app.service.get_settings", return_value=fake), patch("cloud_backend.jarvis_app.service._history", return_value=[]), patch("cloud_backend.jarvis_app.service._save"), patch("cloud_backend.jarvis_app.service.gemini_reply", return_value="Hello"):
            self.assertEqual(service.answer_message("Hello"), ("Hello", "gemini"))

if __name__ == "__main__": unittest.main()
