"""Permission gates for safe Hoshi autonomous agent execution."""
import unittest

from fastapi import HTTPException
from starlette.requests import Request

from cloud_backend.permission_policy import check_agent_action
from cloud_backend.main import AgentTaskRequest, agent_execute


def _request():
    return Request({"type": "http", "method": "POST", "path": "/api/agent/execute",
        "headers": [], "client": ("127.0.0.18", 3218),
        "scheme": "https", "server": ("localhost", 443)})


class PermissionPolicyTests(unittest.TestCase):
    def test_only_existing_local_ads_are_auto_approved(self):
        allowed = check_agent_action("create_product_ads")
        self.assertTrue(allowed.known)
        self.assertTrue(allowed.allowed)
        self.assertFalse(allowed.approval_required)

    def test_account_actions_are_not_executable_by_a_plain_public_request(self):
        for name in ("publish_social", "send_email", "screen_control", "make_purchase",
                     "modify_external_files", "delete_user_data"):
            with self.subTest(name=name):
                decision = check_agent_action(name)
                self.assertTrue(decision.known)
                self.assertFalse(decision.allowed)
                self.assertTrue(decision.approval_required)
                with self.assertRaises(HTTPException) as ctx:
                    agent_execute(AgentTaskRequest(task=name, message="do it"), _request())
                self.assertEqual(ctx.exception.status_code, 403)

    def test_arbitrary_shell_and_live_money_stay_disabled_even_if_requested(self):
        for name in ("live_trade", "withdraw_funds", "execute_shell", "run_arbitrary_code"):
            decision = check_agent_action(name)
            self.assertFalse(decision.allowed)
            self.assertFalse(decision.approval_required)
            with self.assertRaises(HTTPException) as ctx:
                agent_execute(AgentTaskRequest(task=name, message="do it"), _request())
            self.assertEqual(ctx.exception.status_code, 403)

    def test_planned_game_anime_and_video_are_not_falsely_advertised_as_done(self):
        for name in ("build_game", "render_anime", "render_mp4", "autonomous_project"):
            with self.assertRaises(HTTPException) as ctx:
                agent_execute(AgentTaskRequest(task=name, message="do it"), _request())
            self.assertEqual(ctx.exception.status_code, 403)
            self.assertIn("not implemented", ctx.exception.detail)

    def test_unrecognized_tasks_still_fail_closed(self):
        self.assertFalse(check_agent_action("shell").known)
        with self.assertRaises(HTTPException) as ctx:
            agent_execute(AgentTaskRequest(task="shell", message="delete data"), _request())
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
