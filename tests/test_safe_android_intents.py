"""Task 23 safe Android app intents: source/permission contracts.

CI also compiles the real Android APK; no physical phone success is claimed.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVITY = (ROOT / "android/app/src/main/java/com/valtron/jarvis/MainActivity.kt").read_text(encoding="utf-8")
BRIDGE = (ROOT / "android/app/src/main/java/com/valtron/jarvis/JarvisBridge.kt").read_text(encoding="utf-8")
MANIFEST = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class SafeAppIntentContracts(unittest.TestCase):
    def test_fixed_allowlist_and_origin_recheck(self):
        self.assertIn('action !in setOf("youtube", "whatsapp", "telegram", "browser", "settings", "tradingview")', ACTIVITY)
        self.assertIn('requestId !in 0..1_000_000_000', ACTIVITY)
        self.assertIn('page.scheme != "https" || page.host != "jarws-ai-1.onrender.com"', ACTIVITY)
        self.assertIn("safeIntentHandler.post { dispatchKnownAppLaunch(action, requestId) }", ACTIVITY)
        self.assertIn("dashboardWebView !== view || view.url != originalUrl", ACTIVITY)

    def test_no_arbitrary_url_or_send_or_accessibility_for_launch(self):
        start = ACTIVITY.index("fun openKnownApp(action: String, requestId: Int = 0)")
        end = ACTIVITY.index("/** Save only validated Hoshi-generated ZIP bytes", start)
        section = ACTIVITY[start:end]
        for host in ("www.youtube.com", "www.whatsapp.com", "web.telegram.org",
                     "www.tradingview.com", "www.google.com"):
            self.assertIn('Uri.parse("https://' + host + '/")', section)
        for forbidden in ("Intent.parseUri(", "Intent.ACTION_SEND", "EXTRA_TEXT",
                          "JarvisAccessibilityService", "Settings.ACTION_ACCESSIBILITY_SETTINGS",
                          "requestCode", "ACTION_CALL", "ACTION_DIAL"):
            self.assertNotIn(forbidden, section)
        self.assertIn("getLaunchIntentForPackage(it)", section)
        self.assertIn("startActivity(intent)", section)
        self.assertIn("catch (_: Exception)", section)
        self.assertIn("Intent(Settings.ACTION_SETTINGS)", section)

    def test_package_visibility_and_bounded_async_result(self):
        for package in ("com.google.android.youtube", "com.whatsapp",
                        "org.telegram.messenger", "com.tradingview.tradingviewapp"):
            self.assertIn('android:name="' + package + '"', MANIFEST)
        self.assertIn("fun openKnownAppVerified(action: String, requestId: Int): Boolean", BRIDGE)
        self.assertIn("if (requestId !in 1..1_000_000_000) return false", BRIDGE)
        self.assertIn("activity.openKnownApp(action, requestId)", BRIDGE)
        self.assertIn("window.hoshiKnownAppLaunchResult", ACTIVITY)
        self.assertIn("JSONObject.quote(action)", ACTIVITY)
        self.assertIn("window.hoshiKnownAppLaunchResult=(id,action,accepted)=>", HTML)
        self.assertIn("bridge.openKnownAppVerified(kind,id)", HTML)
        self.assertIn("action!==appLaunchPending.action", HTML)
        self.assertIn("typeof accepted!=='boolean'", HTML)
        self.assertIn("No verified Android app launch result.", HTML)
        self.assertIn("bridge.openKnownApp(kind)", HTML)  # backward-compatible APKs


if __name__ == "__main__":
    unittest.main()
