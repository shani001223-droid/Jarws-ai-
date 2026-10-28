"""Task 50: keep the free Canvas template identical to Task 49's GDD."""
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
        self.assertEqual(template["status"], "design_only_not_playable")
        self.assertEqual(template["levels"], design["levels"])

    def test_offline_free_preview_not_falsely_playable(self):
        html = (ROOT / "game-studio/index.html").read_text(encoding="utf-8")
        js = (ROOT / "game-studio/engine.mjs").read_text(encoding="utf-8")
        self.assertIn('type="module"', html)
        self.assertIn("./engine.mjs", html)
        self.assertIn("./levels.json", html)
        self.assertIn("preview only", html.lower())
        self.assertIn("prefers-reduced-motion", html)
        self.assertNotIn("https://", html + js)
        self.assertNotIn("eval(", js)
        self.assertNotIn("localStorage", html + js)
        self.assertNotIn("fetch(", js)

if __name__ == "__main__":
    unittest.main()
