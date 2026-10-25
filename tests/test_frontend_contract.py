"""Static regression checks for the HOSHI dashboard contract."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SERVICE_WORKER = (ROOT / "sw.js").read_text(encoding="utf-8")
SPRITE_PATH = ROOT / "assets" / "hoshi-expressions.webp"


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for key, value in attrs if key == "id" and value)


class FrontendContractTests(unittest.TestCase):
    def test_html_ids_are_unique_and_script_references_exist(self):
        parser = IdCollector()
        parser.feed(HTML)
        self.assertEqual(len(parser.ids), len(set(parser.ids)), "Duplicate HTML id found")
        known_ids = set(parser.ids)
        scripts = re.findall(r"<script>([\s\S]*?)</script>", HTML, re.IGNORECASE)
        self.assertTrue(scripts, "Dashboard inline script is missing")
        refs = set(re.findall(r"\$\(['\"]([^'\"]+)['\"]\)", scripts[0]))
        self.assertTrue(refs, "Dashboard ID references were not detected")
        self.assertEqual(refs - known_ids, set(), "Script references missing HTML IDs")

    def test_character_expression_sprite_is_a_valid_webp_asset(self):
        self.assertTrue(SPRITE_PATH.is_file(), "HOSHI expression sprite is missing")
        image = SPRITE_PATH.read_bytes()
        self.assertGreater(len(image), 5000, "Expression sprite is unexpectedly small")
        self.assertEqual(image[:4], b"RIFF", "Sprite is not a RIFF image")
        self.assertEqual(image[8:12], b"WEBP", "Sprite is not a WebP image")
        self.assertIn("./assets/hoshi-expressions.webp", SERVICE_WORKER)
        self.assertIn("./memory-privacy.js", SERVICE_WORKER)
        self.assertIn('<script src="./memory-privacy.js"></script>', HTML)
        self.assertIn('CACHE_NAME = "hoshi-shell-v9"', SERVICE_WORKER)

    def test_each_ui_emotion_selects_a_character_expression(self):
        emotions = (
            "happy", "sad", "affectionate", "excited", "shy",
            "concerned", "annoyed", "playful", "thinking", "caring",
        )
        for emotion in emotions:
            selector = rf'\.orb\[data-emotion="{emotion}"\] \.companion-avatar\{{background-position:'
            self.assertRegex(HTML, selector, f"No sprite position for {emotion}")

    def test_memory_controls_and_local_preferences_are_present(self):
        for element_id in ("chatHistory", "memoryToggle", "clearMemoryBtn", "voiceSelect",
                           "languageToggle", "speakToggle", "wakeToggle"):
            self.assertIn(f'id="{element_id}"', HTML)
        for feature in ("Delete saved ", "Edit saved ", "hoshiLanguage",
                        "hoshiVoiceReplies", "hoshiWakeWord"):
            self.assertIn(feature, HTML)


if __name__ == "__main__":
    unittest.main()
