"""Structural regression tests: screen control never silently bypasses Android consent.

These checks prove source wiring, not real-device OS dialog acceptance.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android/app/src/main"
BRIDGE = ANDROID / "java/com/valtron/jarvis/JarvisBridge.kt"
ACTIVITY = ANDROID / "java/com/valtron/jarvis/MainActivity.kt"
SERVICE = ANDROID / "java/com/valtron/jarvis/JarvisAccessibilityService.kt"
XML = ANDROID / "res/xml/jarvis_accessibility_service.xml"
MANIFEST = ANDROID / "AndroidManifest.xml"
WEB = ROOT / "index.html"


class ScreenConsentContractTests(unittest.TestCase):
    def test_android_requires_user_enabled_os_accessibility_settings(self):
        bridge = BRIDGE.read_text(encoding="utf-8")
        activity = ACTIVITY.read_text(encoding="utf-8")
        xml = XML.read_text(encoding="utf-8")
        manifest = MANIFEST.read_text(encoding="utf-8")
        self.assertIn("Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES", bridge)
        self.assertIn("Settings.Secure.ACCESSIBILITY_ENABLED", bridge)
        self.assertIn('if (action !in allowedActions || !isEnabled()) return false', bridge)
        self.assertIn("JarvisAccessibilityService.instance == null", bridge)
        self.assertIn("if (activity.isActionEpochCurrent(epoch) && isEnabled() && liveService != null)", bridge)
        self.assertIn("AlertDialog.Builder(this)", activity)
        self.assertIn("Enable basic screen controls?", activity)
        self.assertIn('.setNegativeButton("Cancel", null)', activity)
        self.assertIn("Settings.ACTION_ACCESSIBILITY_SETTINGS", activity)
        self.assertIn('android:canRetrieveWindowContent="false"', xml)
        self.assertIn('android.permission.BIND_ACCESSIBILITY_SERVICE', manifest)

    def test_only_allowlisted_actions_supported_and_no_private_screen_capture(self):
        bridge = BRIDGE.read_text(encoding="utf-8")
        service = SERVICE.read_text(encoding="utf-8")
        for action in ("back", "home", "swipe_up", "swipe_down", "screenshot"):
            with self.subTest(action=action):
                self.assertIn('"' + action + '"', bridge)
        for dangerous in ("tap_anywhere", "type_password", "read_screen_text", "send_message"):
            with self.subTest(action=dangerous):
                self.assertNotIn('"' + dangerous + '"', bridge)
        self.assertIn("Intentionally do not inspect events or screen contents", service)
        self.assertNotIn("rootInActiveWindow", service)
        self.assertNotIn("getRootInActiveWindow", service)

    def test_dashboard_asks_permission_only_after_explicit_user_interaction(self):
        html = WEB.read_text(encoding="utf-8")
        self.assertIn("id=\"screenPermissionBtn\"", html)
        self.assertIn("$('screenPermissionBtn').onclick=()=>window.JarvisBridge.requestSettings()", html)
        self.assertIn("window.JarvisBridge.isEnabled()", html)
        self.assertIn("if(!bridge.isEnabled())", html)
        self.assertIn("action could not be queued", html.lower())
        self.assertIn("android accessibility", html.lower())


if __name__ == "__main__":
    unittest.main()
