"""Secret-safe diagnostic and backend error boundary regression tests."""
import asyncio
import os
import unittest
from unittest.mock import patch, AsyncMock

from fastapi import HTTPException
from starlette.requests import Request
from cloud_backend import main


class SafeErrorBoundaryTests(unittest.TestCase):
    def test_diagnostic_logs_error_kind_without_untrusted_message(self):
        private_text = "PRIVATE_API_KEY_and_user_prompt_must_not_be_logged"
        with self.assertLogs("hoshi.backend", level="WARNING") as cap:
            main._safe_log_failure("test.component", RuntimeError(private_text))
        self.assertIn("component=test.component", cap.output[0])
        self.assertIn("kind=RuntimeError", cap.output[0])
        self.assertNotIn(private_text, "\n".join(cap.output))

    def test_ad_render_failure_is_sanitized_and_releases_slot(self):
        main._AD_RECENT.clear()
        scope = {"type": "http", "method": "POST", "path": "/api/agent/execute",
                 "headers": [], "client": ("127.0.0.12", 5012),
                 "scheme": "https", "server": ("localhost", 443)}
        request = Request(scope)
        with patch("cloud_backend.main.create_ad_pack", side_effect=RuntimeError("PRIVATE_render_debug")):
            with self.assertLogs("hoshi.backend", level="WARNING") as cap:
                with self.assertRaises(HTTPException) as ctx:
                    main.agent_execute(main.AgentTaskRequest(task="create_product_ads", message="poster banao"), request)
            self.assertEqual(ctx.exception.status_code, 502)
            self.assertNotIn("PRIVATE_render_debug", ctx.exception.detail)
            self.assertNotIn("PRIVATE_render_debug", "\n".join(cap.output))
        # If an exception leaves the BoundedSemaphore locked, a following real call fails.
        main._AD_RECENT.clear()
        self.assertTrue(main.agent_execute(main.AgentTaskRequest(task="create_product_ads",
                                 message="gold facial kit ka ad banao"), request)["completed"])
        main._AD_RECENT.clear()

    def test_urdu_speech_failure_never_logs_private_text(self):
        with patch("cloud_backend.main.synthesize_urdu", new=AsyncMock(
            side_effect=RuntimeError("PRIVATE_user_spoken_text")
        )):
            with self.assertLogs("hoshi.backend", level="WARNING") as cap:
                with self.assertRaises(HTTPException) as ctx:
                    asyncio.run(main.speech(main.SpeechRequest(text="یہ آواز ایک ٹیسٹ ہے۔")))
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertNotIn("PRIVATE_user_spoken_text", ctx.exception.detail)
        self.assertNotIn("PRIVATE_user_spoken_text", "\n".join(cap.output))


if __name__ == "__main__":
    unittest.main()
