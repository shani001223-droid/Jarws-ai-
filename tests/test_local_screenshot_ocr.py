"""Task 20 local screenshot OCR privacy contract; CI Android + browser checks are separate."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "android/app/src/main"
ACTIVITY = ANDROID / "java/com/valtron/jarvis/MainActivity.kt"
BRIDGE = ANDROID / "java/com/valtron/jarvis/JarvisBridge.kt"
OCR = ANDROID / "java/com/valtron/jarvis/LocalScreenshotOcr.kt"
GRADLE = ROOT / "android/app/build.gradle.kts"
WEB = ROOT / "index.html"


class LocalScreenshotOcrContractTests(unittest.TestCase):
    def test_explicit_picker_and_offline_model(self):
        activity = ACTIVITY.read_text(encoding="utf-8")
        bridge = BRIDGE.read_text(encoding="utf-8")
        ocr = OCR.read_text(encoding="utf-8")
        gradle = GRADLE.read_text(encoding="utf-8")
        self.assertIn("Intent.ACTION_OPEN_DOCUMENT", activity)
        self.assertIn("Intent.CATEGORY_OPENABLE", activity)
        self.assertIn("REQUEST_LOCAL_SCREENSHOT_OCR", activity)
        self.assertIn("chooseScreenshotForLocalOcr", bridge)
        self.assertIn("onActivityResult", activity)
        self.assertIn("TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)", ocr)
        self.assertIn('implementation("com.google.mlkit:text-recognition:16.0.1")', gradle)
        self.assertNotIn("http://", ocr)
        self.assertNotIn("https://", ocr)

    def test_bounded_ephemeral_data(self):
        ocr = OCR.read_text(encoding="utf-8")
        html = WEB.read_text(encoding="utf-8")
        for requirement in ("8_000_000", "2048", "4_500_000", "blocks.length() >= 35",
                            "remaining = 2400", "bitmap.recycle()", "recognizer.close()"):
            self.assertIn(requirement, ocr)
        for requirement in ("screenOcrBtn", "screenOcrClearBtn", "window.hoshiLocalOcrResult",
                            "screenOcrOutput').textContent", "Urdu script is not supported"):
            self.assertIn(requirement, html)
        self.assertNotIn("rootInActiveWindow", ocr)
        self.assertNotIn("MediaProjection", ocr)


if __name__ == "__main__":
    unittest.main()
