"""Source contracts for user-triggered, Hoshi-only Android tap/type/scroll.

CI proves policy wiring and compilation separately; real phone interaction is untested.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "android/app/src/main/java/com/valtron/jarvis/JarvisBridge.kt").read_text(encoding="utf-8")
ACTIVITY = (ROOT / "android/app/src/main/java/com/valtron/jarvis/MainActivity.kt").read_text(encoding="utf-8")
WEB = (ROOT / "index.html").read_text(encoding="utf-8")
CLIENT = (ROOT / "hoshi-local-ui-actions.js").read_text(encoding="utf-8")
SW = (ROOT / "sw.js").read_text(encoding="utf-8")


class LocalUiActionContracts(unittest.TestCase):
    def test_native_permission_and_service_gate(self):
        self.assertIn("fun performLocalUiAction(action: String, payload: String): Boolean", BRIDGE)
        self.assertIn("action !in localUiActions || !isEnabled()", BRIDGE)
        self.assertIn("JarvisAccessibilityService.instance == null", BRIDGE)
        self.assertIn("if (isEnabled() && JarvisAccessibilityService.instance != null)", BRIDGE)
        self.assertIn("payload.length !in 1..240", BRIDGE)
        self.assertIn("payload.any { it.code < 32 || it.code == 127 }", BRIDGE)

    def test_webview_executes_only_on_trusted_dashboard(self):
        self.assertIn('page.scheme != "https" || page.host != "jarws-ai-1.onrender.com"', ACTIVITY)
        self.assertIn("JSONObject.quote(action)", ACTIVITY)
        self.assertIn("JSONObject.quote(payload)", ACTIVITY)
        self.assertIn("fun dispatchLocalUiAction(action: String, payload: String)", ACTIVITY)
        self.assertNotIn("rootInActiveWindow", ACTIVITY)
        self.assertNotIn("dispatchGesture", ACTIVITY)

    def test_draft_only_no_cross_app_actions_or_submission(self):
        for action in ("tap_chat", "tap_settings", "type_draft", "scroll_up", "scroll_down"):
            self.assertIn('"' + action + '"', CLIENT)
        for prohibited in ("requestSubmit(", "fetch(", "startActivity(", "performGlobalAction("):
            self.assertNotIn(prohibited, CLIENT.replace("// Draft only. Never call requestSubmit(), click Send, or fetch().", ""))
        self.assertIn("input.value=payload", CLIENT)
        self.assertIn("sheet.scrollTop=", CLIENT)
        self.assertIn("window.hoshiExecuteLocalUiAction=", WEB)
        self.assertIn("bridge.performLocalUiAction(action,payload)", WEB)
        self.assertIn("id=\"localUiDraft\"", WEB)
        self.assertIn("hoshi-local-ui-actions.js", SW)
        self.assertIn('<script src="./hoshi-local-ui-actions.js"></script>', WEB)


if __name__ == "__main__":
    unittest.main()
