"""Static privacy/cancellation contracts for Task 24; device behavior needs real QA."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "index.html").read_text(encoding="utf-8")
CLIENT = (ROOT / "hoshi-local-ui-actions.js").read_text(encoding="utf-8")
BRIDGE = (ROOT / "android/app/src/main/java/com/valtron/jarvis/JarvisBridge.kt").read_text(encoding="utf-8")
ACTIVITY = (ROOT / "android/app/src/main/java/com/valtron/jarvis/MainActivity.kt").read_text(encoding="utf-8")


class EmergencyStopContracts(unittest.TestCase):
    def test_native_actions_are_invalidated_before_ui_thread_execution(self):
        self.assertIn("fun cancelQueuedActions(): Boolean = activity.cancelQueuedActions()", BRIDGE)
        self.assertIn("val epoch = activity.currentActionEpoch()", BRIDGE)
        self.assertIn("activity.isActionEpochCurrent(epoch)", BRIDGE)
        self.assertIn("private val nativeActionEpoch = AtomicInteger(0)", ACTIVITY)
        self.assertIn("nativeActionEpoch.incrementAndGet()", ACTIVITY)
        self.assertIn("if (isActionEpochCurrent(epoch)) dispatchKnownAppLaunch(action, requestId)", ACTIVITY)

    def test_local_dom_action_cannot_run_after_stop_or_with_stale_id(self):
        self.assertIn("window.hoshiExecuteLocalUiAction=(action,payload,id)", WEB)
        self.assertIn("actionSafety.isCurrent(id,action)", WEB)
        self.assertIn('JSONObject.quote(payload) + "," + requestId + ")"', ACTIVITY)
        self.assertIn("!actionSafety.finish(id,verified)", WEB)
        self.assertIn("actionSafety.cancel(id,'timeout')", WEB)

    def test_action_history_never_includes_draft_payload_or_persistent_storage(self):
        self.assertIn("function createSafety(maxEntries=20)", CLIENT)
        self.assertIn("entries.unshift(Object.freeze({action,outcome,at:Date.now()}))", CLIENT)
        self.assertNotIn("localStorage", CLIENT)
        self.assertNotIn("payload:", CLIENT)
        self.assertIn("row.textContent=new Date(item.at)", WEB)
        self.assertIn('id="actionEmergencyStopBtn"', WEB)
        self.assertIn("actionSafety.emergencyStop()", WEB)
        self.assertIn("interruptHoshi()", WEB)
        self.assertIn("invalidateQueuedActions()", WEB)
        self.assertIn("localOcrPending=false", WEB)


if __name__ == "__main__":
    unittest.main()
