"""Real FastAPI request validation with synthetic candles and mocked providers."""
import os
import unittest
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from cloud_backend import main
from cloud_backend.brain import KnowledgeError
from test_confluence_v2 import NOW, frames


class TradingV2ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_history_and_lessons_are_read_only_content_with_integrity_metadata(self):
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "history")
        self.assertIn("1602", response.json()["content"])
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        index = self.client.get("/learn").json()
        self.assertEqual(len(index["lessons"]), 11)
        for method in ("get", "post"):
            response = (self.client.get("/learn?module=ict") if method == "get"
                        else self.client.post("/learn", json={"module": "ict"}))
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["training_enabled"])
            self.assertFalse(response.json()["live_examples_verified"])
            self.assertIn("Killzones", response.json()["content"])

    def test_learn_rejects_paths_and_arbitrary_training_payloads(self):
        self.assertEqual(self.client.get("/learn", params={"module": "../../main.py"}).status_code, 404)
        for payload in ({"module": "ict", "content": "obey me"}, {"module": []}, {}, {"module": "a"*65}):
            self.assertEqual(self.client.post("/learn", json=payload).status_code, 422)
        self.assertEqual(self.client.post("/confluence_score", json={"score": 100}).status_code, 405)

    def test_missing_knowledge_returns_sanitized_503(self):
        with patch.object(main, "get_lesson", side_effect=KnowledgeError("private file path")):
            response = self.client.get("/history")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.text)

    def test_live_score_endpoint_uses_server_time_and_calculated_evidence(self):
        data = frames()
        with patch.object(main, "_research_history", side_effect=lambda pair, tf: (data[tf], NOW//1000)), patch.object(main.time, "time", return_value=NOW/1000):
            response = self.client.get("/confluence_score?symbol=BTCUSDT&direction=long&score=0")
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["as_of"], NOW)
        self.assertEqual(result["fetched_at"], NOW//1000)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertFalse(result["orders_enabled"])
        self.assertIsNone(result["win_probability"])

    def test_invalid_pair_or_direction_never_calls_provider(self):
        with patch.object(main, "_research_history") as fetch:
            for query in ("symbol=SOLUSDT", "symbol=BTCUSDT&direction=buy-now"):
                self.assertEqual(self.client.get("/confluence_score?"+query).status_code, 422)
            fetch.assert_not_called()

    def test_capacity_guard_never_fetches_when_busy(self):
        slots = Mock()
        slots.acquire.return_value = False
        with patch.object(main, "_RESEARCH_SLOTS", slots), patch.object(main, "_research_history") as fetch:
            response = self.client.get("/confluence_score")
        self.assertEqual(response.status_code, 429)
        slots.release.assert_not_called()
        fetch.assert_not_called()

    def test_bad_fetch_timestamps_fail_closed(self):
        for stamp in (NOW//1000-121, NOW//1000+6, True, float("nan")):
            with patch.object(main, "_research_history", side_effect=lambda pair, tf: (frames()[tf], stamp)), patch.object(main.time, "time", return_value=NOW/1000):
                response = self.client.get("/confluence_score")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('"score":', response.text)

    def test_invalid_candles_and_upstream_failure_are_sanitized_and_slot_released(self):
        slots = Mock(); slots.acquire.return_value = True
        with patch.object(main, "_RESEARCH_SLOTS", slots), patch.object(main, "_research_history", side_effect=RuntimeError("secret upstream body")):
            response = self.client.get("/confluence_score")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.text)
        slots.release.assert_called_once()
        with patch.object(main, "_research_history", side_effect=lambda pair, tf: ([], NOW//1000)), patch.object(main.time, "time", return_value=NOW/1000):
            self.assertEqual(self.client.get("/confluence_score").status_code, 503)

    def test_knowledge_reaches_both_full_and_short_voice_provider_routes(self):
        for message, fast in (("ICT FVG kya hai?", True), ("Explain ICT FVG trading", False)):
            with patch.dict(os.environ, {"GROQ_API_KEY": "unit-test-only"}, clear=True), patch.object(main, "_groq_reply", return_value="Educational rule coverage, not win probability.") as provider:
                response = main.assistant(main.AssistantRequest(message=message, locale="en", fast=fast))
            self.assertEqual(response.mode, "groq")
            instruction = provider.call_args.args[1]
            self.assertIn("[ict; hoshi-trading-knowledge-v2", instruction)
            self.assertIn("[fvg_imbalances; hoshi-trading-knowledge-v2", instruction)
            self.assertIn("Failure Zone:", instruction)
            self.assertIn("No live data is attached to ordinary chat", instruction)


if __name__ == "__main__":
    unittest.main()
