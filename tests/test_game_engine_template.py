"""Tasks 50-52: keep the playable offline Canvas levels identical to the GDD."""
import json
from pathlib import Path
import unittest
from cloud_backend.game_design import design_manifest

ROOT = Path(__file__).resolve().parents[1]
class GameEngineTemplateTests(unittest.TestCase):
    def test_static_levels_match_proven_design_exactly(self):
        template = json.loads((ROOT / "game-studio/levels.json").read_text(encoding="utf-8"))
        design = design_manifest()
        self.assertEqual(template["version"], design["version"])
        self.assertEqual(template["status"], "playable_local_mvp")
        self.assertEqual(template["levels"], design["levels"])

    def test_offline_free_playable_ui_has_explicit_save_consent(self):
        html = (ROOT / "game-studio/index.html").read_text(encoding="utf-8")
        js = (ROOT / "game-studio/engine.mjs").read_text(encoding="utf-8")
        self.assertIn('type="module"', html)
        self.assertIn("./engine.mjs", html)
        self.assertIn("./levels.json", html)
        self.assertIn("./gameplay.mjs", html)
        self.assertIn("readSavedProgress", html)
        self.assertIn("saveToggle.checked", html)
        self.assertIn("clearSavedProgress", html)
        self.assertIn("data-dir", html)
        self.assertIn("prefers-reduced-motion", html)
        self.assertNotIn("https://", html + js)
        self.assertNotIn("eval(", js)
        self.assertIn("localStorage", html)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("fetch(", js)

if __name__ == "__main__":
    unittest.main()
