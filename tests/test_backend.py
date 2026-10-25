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

    def test_health_reports_interactions_api_and_provider_flags(self):
        with patch.dict(os.environ, {
            "GEMINI_API_KEY": "test-gemini-key",
            "GROQ_API_KEY": "test-groq-key",
        }):
            health = main.health()

        self.assertEqual(health["version"], "0.7.0")
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
        self.assertEqual(request.get_header("User-agent"), "JARVIS-Cloud-Assistant/0.7.0 (+https://jarws-ai-1.onrender.com)")
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], main.GEMINI_MODEL)
        self.assertEqual(body["input"], "Hello")
        self.assertFalse(body["store"])
        self.assertIn("Roman Urdu", body["system_instruction"])

    def test_btc_market_snapshot_combines_public_ticker_and_stats(self):
        ticker = {
            "price": "100.0",
            "bid": "99.8",
            "ask": "100.2",
            "volume": "1400",
            "time": "2026-10-25T10:00:00Z",
        }
        stats = {
            "open": "80.0",
            "high": "112.0",
            "low": "72.0",
            "last": "99.9",
            "volume": "1200.5",
            "volume_30day": "10000",
        }
        with patch.object(main, "_market_cache", {"payload": None, "fetched_at": 0.0}):
            with patch("cloud_backend.main.time.monotonic", return_value=1000.0):
                with patch(
                    "cloud_backend.main.urlopen",
                    side_effect=[FakeResponse(ticker), FakeResponse(stats)],
                ) as mocked:
                    result = main.btc_market()

        self.assertEqual(result["source"], "Coinbase Exchange")
        self.assertEqual(result["symbol"], "BTC-USD")
        self.assertEqual(result["market_type"], "spot")
        self.assertEqual(result["price_usd"], 100.0)
        self.assertAlmostEqual(result["change_24h_pct"], 25.0)
        self.assertEqual(result["high_24h_usd"], 112.0)
        self.assertEqual(result["low_24h_usd"], 72.0)
        self.assertEqual(result["volume_24h_btc"], 1200.5)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(
            mocked.call_args_list[0].args[0].full_url,
            "https://api.exchange.coinbase.com/products/BTC-USD/ticker",
        )
        self.assertEqual(
            mocked.call_args_list[1].args[0].full_url,
            "https://api.exchange.coinbase.com/products/BTC-USD/stats",
        )
        self.assertEqual(
            mocked.call_args_list[0].args[0].get_header("User-agent"),
            "JARVIS-Cloud-Assistant/0.8.0 (+https://jarws-ai-1.onrender.com)",
        )

    def test_btc_market_snapshot_uses_short_cache(self):
        cached = {
            "source": "Coinbase Exchange",
            "symbol": "BTC-USD",
            "price_usd": 123.0,
        }
        with patch.object(main, "_market_cache", {"payload": cached, "fetched_at": 1000.0}):
            with patch("cloud_backend.main.time.monotonic", return_value=1010.0):
                with patch("cloud_backend.main.urlopen") as mocked:
                    result = main.btc_market()
        self.assertEqual(result["price_usd"], 123.0)
        mocked.assert_not_called()

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
        self.assertEqual(fallback_request.get_header("User-agent"), "JARVIS-Cloud-Assistant/0.7.0 (+https://jarws-ai-1.onrender.com)")


if __name__ == "__main__":
    unittest.main()
