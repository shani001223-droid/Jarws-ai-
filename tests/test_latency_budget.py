"""Fast voice/casual answers must not stack unbounded provider timeouts."""
import unittest
from unittest.mock import patch
from cloud_backend.latency_budget import provider_timeout
from cloud_backend import main


class LatencyBudgetTests(unittest.TestCase):
    def test_quick_budget_shrinks_as_providers_fail(self):
        self.assertEqual(provider_timeout(100, 100, fast=True), 7.0)
        self.assertAlmostEqual(provider_timeout(100, 105, fast=True), 7.0)
        self.assertAlmostEqual(provider_timeout(100, 110, fast=True), 2.25)
        self.assertEqual(provider_timeout(100, 113, fast=True), 0.0)

    def test_detailed_has_longer_budget(self):
        self.assertEqual(provider_timeout(100, 115, fast=False), 7.0)
        self.assertGreater(provider_timeout(100, 121, fast=False), 0)
        self.assertEqual(provider_timeout(100, 129, fast=False), 0.0)

    def test_invalid_inputs_fail_closed(self):
        for value in (float("inf"), float("nan"), -1):
            self.assertEqual(provider_timeout(1, 2, fast=True, cap=value), 0.0)
        self.assertEqual(provider_timeout(0, 0, fast=True, cap=0), 0.0)

    def test_openrouter_can_use_shortened_timeout(self):
        import os
        from tests.test_backend import FakeResponse
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-only"}):
            with patch("cloud_backend.main.urlopen", return_value=FakeResponse({
                "choices": [{"message": {"content": "Short answer"}}]
            })) as requested:
                answer = main._openrouter_reply("Salam", "system", timeout=2.5)
        self.assertEqual(answer, "Short answer")
        self.assertEqual(requested.call_args.kwargs["timeout"], 2.5)


if __name__ == "__main__":
    unittest.main()
