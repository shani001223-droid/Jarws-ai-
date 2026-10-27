"""Static privacy/race contracts for Task 20 on-device selected-image OCR.

These checks are not a substitute for Android compilation or real-device OCR QA.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "android/app/src/main/java/com/valtron/jarvis"
ACTIVITY = NATIVE / "MainActivity.kt"
OCR = NATIVE / "LocalScreenshotOcr.kt"
BRIDGE = NATIVE / "JarvisBridge.kt"
WEB = ROOT / "index.html"


class ScreenshotOcrContractTests(unittest.TestCase):
    def test_user_selected_image_only_with_atomic_picker_gate(self):
        activity = ACTIVITY.read_text(encoding="utf-8")
        bridge = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("Intent.ACTION_OPEN_DOCUMENT", activity)
        self.assertIn("Intent.CATEGORY_OPENABLE", activity)
        self.assertIn('type = "image/*"', activity)
        self.assertIn("AtomicBoolean(false)", activity)
        self.assertIn("!localOcrBusy.compareAndSet(false, true)", activity)
        self.assertIn("if (isFinishing || isDestroyed", activity)
        self.assertIn("fun chooseScreenshotForLocalOcr(): Boolean", bridge)
        self.assertNotIn("MediaProjectionManager", activity)
        self.assertNotIn("getRootInActiveWindow", bridge)

    def test_offline_latin_model_and_bounded_image_output(self):
        code = OCR.read_text(encoding="utf-8")
        self.assertIn("TextRecognizerOptions.DEFAULT_OPTIONS", code)
        self.assertIn('setOf("image/png", "image/jpeg", "image/webp")', code)
        self.assertIn("1L..8_000_000L", code)
        self.assertIn("2048", code)
        self.assertIn("4_500_000L", code)
        self.assertIn("remaining = 2400", code)
        self.assertIn("blocks.length() >= 35", code)
        self.assertIn("recognizer.close()", code)
        self.assertNotIn("http://", code)
        self.assertNotIn("https://", code)

    def test_private_display_never_forwards_text(self):
        html = WEB.read_text(encoding="utf-8")
        self.assertIn("settingsPanel.append(document.querySelector('.controls'),document.querySelector('.bottom-workspace'))", html)
        self.assertIn("window.hoshiLocalOcrResult=raw=>", html)
        self.assertIn("if(!localOcrPending)return;", html)
        self.assertIn("$('screenOcrOutput').textContent=lines.join", html)
        self.assertIn("localOcrPending=false;", html)
        self.assertIn("No upload.", html)


if __name__ == "__main__":
    unittest.main()
