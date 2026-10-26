"""Routing regression tests: never confuse categorization with execution."""
import unittest

from cloud_backend.task_router import route_task
from cloud_backend import main


class TaskRouterTests(unittest.TestCase):
    def test_readonly_research_can_run_but_screen_marking_stays_unavailable(self):
        for prompt in ("BTC research karo", "ETH market analyse kro"):
            route = route_task(prompt)
            self.assertTrue(route.ready)
            self.assertEqual(route.executor, "trading_research")
            self.assertFalse(route.needs_device_permission)

    def test_existing_product_ad_tool_routes_to_real_executor(self):
        for phrase in ("mere products k ads bana kar do", "Flora shampoo poster create karo"):
            with self.subTest(phrase=phrase):
                result = route_task(phrase)
                self.assertEqual(result.mode, "backend_tool")
                self.assertEqual(result.intent, "create_product_ads")
                self.assertTrue(result.ready)
                self.assertEqual(result.executor, "create_product_ads")

    def test_btc_chart_analysis_requires_real_screen_integration(self):
        result = route_task("BTC k chart ko analyse kro support resistance mark kro indicators lagao")
        self.assertEqual(result.mode, "screen_agent")
        self.assertEqual(result.intent, "chart_analysis")
        self.assertFalse(result.ready)
        self.assertTrue(result.needs_device_permission)

    def test_large_games_are_backend_projects_but_not_falsely_executed(self):
        result = route_task("Mere liye ek puri game banaao")
        self.assertEqual(result.mode, "backend_project")
        self.assertEqual(result.intent, "build_game")
        self.assertFalse(result.ready)
        self.assertIsNone(result.executor)

    def test_300_episode_anime_request_is_recognized_but_not_faked(self):
        result = route_task("Hindi Urdu anime 300 episodes 30 min each banaao")
        self.assertEqual(result.mode, "backend_project")
        self.assertEqual(result.intent, "render_anime")
        self.assertFalse(result.ready)

    def test_ordinary_chat_and_howto_questions_do_not_launch_workers(self):
        for phrase in ("Hoshi tum kaisi ho?", "How to create a game?",
                       "BTC chart kaise analyse karte hain?"):
            with self.subTest(phrase=phrase):
                result = route_task(phrase)
                self.assertEqual(result.mode, "chat")
                self.assertEqual(result.executor, "assistant")

    def test_phone_actions_are_never_claimed_from_web_backend(self):
        route = route_task("Open WhatsApp on my phone")
        self.assertEqual(route.mode, "screen_agent")
        self.assertFalse(route.ready)
        self.assertTrue(route.needs_device_permission)

    def test_api_returns_immutable_route_data_without_user_text(self):
        response = main.agent_route(main.AgentRouteRequest(message="Mere liye anime banaao"))
        self.assertEqual(response["mode"], "backend_project")
        self.assertIsNone(response["executor"])
        self.assertFalse(response["ready"])
        self.assertNotIn("Mere liye anime banaao", str(response))


if __name__ == "__main__":
    unittest.main()
