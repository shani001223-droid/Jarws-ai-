"""Milestone planner verification: dependencies, scope and no fake execution."""
import unittest
from cloud_backend.milestone_planner import plan_milestones
from cloud_backend import main


class MilestonePlannerTests(unittest.TestCase):
    def test_large_anime_is_batched_without_rendering_or_enqueuing(self):
        result=plan_milestones("Create Hindi Urdu anime 300 episodes 30 min each")
        self.assertEqual(result["intent"],"render_anime")
        self.assertEqual(result["batching"]["batch_size"],10)
        self.assertEqual(result["batching"]["batch_count"],30)
        self.assertTrue(result["batching"]["requires_episode_level_qc"])
        self.assertTrue(result["plan_only"])
        self.assertFalse(result["job_created"])
        self.assertIsNone(result["next_milestone"])
        self.assertEqual(result["execution_status"],"not_started")
        self.assertTrue(all(m["status"]=="not_started" and not m["evidence"] for m in result["milestones"]))

    def test_dependencies_are_acyclic_and_ordered_for_game(self):
        result=plan_milestones("Mere liye ek puri game banaao")
        seen=set()
        for milestone in result["milestones"]:
            self.assertTrue(set(milestone["depends_on"]).issubset(seen))
            self.assertNotIn(milestone["id"],seen)
            self.assertIn("Inspect actual output",milestone["verification"])
            seen.add(milestone["id"])
        self.assertIn("playable_build",seen)
        self.assertIn("qa_report",seen)

    def test_ready_ad_tool_is_still_not_claimed_as_executed(self):
        result=plan_milestones("Flora shampoo ads bana do")
        self.assertEqual(result["intent"],"create_product_ads")
        self.assertEqual(result["next_milestone"],"feed_creative")
        self.assertFalse(result["job_created"])
        self.assertTrue(all(m["status"]=="not_started" for m in result["milestones"]))

    def test_chat_and_unknown_scope_do_not_fake_jobs(self):
        for message in ("Hoshi kaisi ho", "How to build a game?"):
            result=plan_milestones(message)
            self.assertEqual(result["mode"],"chat")
            self.assertFalse(result["job_created"])

    def test_api_returns_no_sensitive_prompt(self):
        secret="sk-proj-DO-NOT-RETURN-THIS"
        result=main.agent_milestones(main.GoalSpecRequest(message="Create a game "+secret))
        self.assertNotIn(secret,str(result))
        self.assertTrue(result["plan_only"])

    def test_no_unbounded_milestone_list_for_very_large_scope(self):
        result=plan_milestones("Create anime 99999 episodes 9999 minutes each")
        self.assertLessEqual(len(result["milestones"]),6)
        self.assertTrue(result["blockers"])
        self.assertEqual(result["batching"]["batch_count"],10000)


if __name__=="__main__":
    unittest.main()
