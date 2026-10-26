"""Goal-to-deliverables contract: specification is not execution."""
import unittest
from pydantic import ValidationError
from cloud_backend.goal_spec import goal_to_deliverables
from cloud_backend import main


class GoalSpecTests(unittest.TestCase):
    def test_large_anime_goal_has_exact_requested_scope_and_real_formats(self):
        result=goal_to_deliverables("Hindi Urdu anime 300 episodes 30 min each banaao")
        self.assertEqual(result["intent"],"render_anime")
        self.assertEqual(result["mode"],"backend_project")
        self.assertFalse(result["executor_ready"])
        self.assertEqual(result["execution_status"],"not_started")
        self.assertEqual(result["scope"],{"episode_count":300,"minutes_per_episode":30,"total_requested_minutes":9000})
        self.assertIn("rendered_episodes",[d["id"] for d in result["deliverables"]])
        self.assertIn("MP4",[d["format"] for d in result["deliverables"]])
        self.assertTrue(all(d["status"]=="planned" for d in result["deliverables"]))
        self.assertTrue(result["blockers"])

    def test_game_spec_requires_playable_export_and_real_qa(self):
        result=goal_to_deliverables("Mere liye ek puri game banaao")
        self.assertEqual(result["intent"],"build_game")
        self.assertFalse(result["executor_ready"])
        self.assertEqual(result["execution_status"],"not_started")
        self.assertEqual([d["id"] for d in result["deliverables"]][-2:],
                         ["playable_build","qa_report"])

    def test_ad_spec_describes_real_existing_output_without_fake_mp4(self):
        result=goal_to_deliverables("Flora shampoo ads banao")
        self.assertEqual(result["intent"],"create_product_ads")
        self.assertTrue(result["executor_ready"])
        self.assertEqual(result["execution_status"],"not_started")
        self.assertIn("ad_pack",[d["id"] for d in result["deliverables"]])
        self.assertNotIn("MP4",[d["format"] for d in result["deliverables"]])

    def test_chart_spec_is_paper_only_and_not_device_execution(self):
        result=goal_to_deliverables("BTC chart analyse kro support resistance mark kro")
        self.assertEqual(result["intent"],"chart_analysis")
        self.assertEqual(result["mode"],"screen_agent")
        self.assertFalse(result["executor_ready"])
        self.assertIn("annotated_chart",[d["id"] for d in result["deliverables"]])
        self.assertTrue(result["blockers"])

    def test_explanation_remains_chat(self):
        result=goal_to_deliverables("How to create a game?")
        self.assertEqual(result["mode"],"chat")
        self.assertEqual([d["id"] for d in result["deliverables"]],["answer"])

    def test_scope_guardrails_are_explicit_not_silent(self):
        result=goal_to_deliverables("Create anime 3000 episodes 240 minutes each")
        self.assertTrue(any("guardrails" in b for b in result["blockers"]))
        self.assertEqual(result["scope"]["total_requested_minutes"],720000)

    def test_user_secrets_are_not_reflected_in_spec(self):
        result=goal_to_deliverables("Create a game with password SECRET-DONT-LOG-123")
        self.assertNotIn("SECRET-DONT-LOG-123",str(result))

    def test_api_is_pure_and_rejects_empty_or_oversized_requests(self):
        result=main.agent_spec(main.GoalSpecRequest(message="Mere liye game banao"))
        self.assertEqual(result["intent"],"build_game")
        self.assertIn("No background job",result["notes"])
        for value in ("","x"*4001):
            with self.assertRaises(ValidationError):
                main.GoalSpecRequest(message=value)


if __name__=="__main__":
    unittest.main()
