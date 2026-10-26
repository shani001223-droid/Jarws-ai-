"""Guard one canonical Hoshi project instead of diverging project documents.

This is a structural, no-network check. It does not claim to run live tools or
verify services on the user's phone.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "HOSHI_MASTER_PROJECT.md"
ROADMAP = ROOT / "HOSHI_60_TASK_MASTER_ROADMAP.md"
README = ROOT / "README.md"


class HoshiMasterProjectTests(unittest.TestCase):
    def test_project_master_and_readme_refer_to_same_canonical_repo(self):
        master = MASTER.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# HOSHI AI — One Unified Project"))
        self.assertIn("HOSHI_MASTER_PROJECT.md", readme[:1500])
        self.assertIn("HOSHI_60_TASK_MASTER_ROADMAP.md", readme[:1500])
        self.assertIn("https://github.com/shani001223-droid/Jarws-ai-", master)
        self.assertIn("hoshi/dnd-foundation-20261026", master)
        self.assertIn("Do not make a second Hoshi source repository", master)

    def test_all_documented_project_modules_and_supporting_docs_exist(self):
        expected = [
            "index.html", "trading.css", "sw.js", "manifest.json",
            "hoshi-speech-input.js", "hoshi-task-router.js", "hoshi-product-ads.js",
            "hoshi-memory-store.js", "memory-privacy.js", "reminder-parser.js",
            "assistant-commands.js", "cloud_backend/main.py",
            "cloud_backend/openjarvis_bridge.py", "cloud_backend/provider_policy.py",
            "cloud_backend/free_llm_providers.py", "cloud_backend/urdu_tts_text.py",
            "cloud_backend/task_router.py", "cloud_backend/goal_spec.py",
            "cloud_backend/milestone_planner.py", "cloud_backend/permission_policy.py",
            "cloud_backend/ad_studio.py", "cloud_backend/artifact_verifier.py",
            "android/app/src/main/java/com/valtron/jarvis/MainActivity.kt",
            "assets/hoshi-expressions.webp",
            ".github/workflows/ci.yml", ".github/workflows/android-apk.yml",
            "HOSHI_TASK_LIST.md", "HOSHI_PHASE1_AUDIT.md",
            "HOSHI_OPENJARVIS_INTEGRATION.md", "HOSHI_FREE_LLM_PROVIDERS.md",
            "HOSHI_AGENT_PRODUCT_ADS.md", "DEPLOYMENT_ROLLBACK.md",
        ]
        for relpath in expected:
            with self.subTest(path=relpath):
                self.assertTrue((ROOT / relpath).is_file(), relpath)

    def test_60_task_roadmap_is_unique_authoritative_status(self):
        roadmap = ROADMAP.read_text(encoding="utf-8")
        matches = re.findall(r"^- \[[ x]\] \*\*(\d{2})\*\*", roadmap, re.MULTILINE)
        self.assertEqual(matches, [f"{n:02d}" for n in range(1, 61)])
        master = MASTER.read_text(encoding="utf-8")
        self.assertIn("Only task-status scoreboard", master)
        self.assertIn("Current verified roadmap snapshot", master)
        self.assertIn("Never place", master)

    def test_single_handoff_includes_key_nondeceptive_boundaries(self):
        master = MASTER.read_text(encoding="utf-8")
        required = [
            "Realme Note 50", "Roman Urdu", "OpenJarvis", "Mistral",
            "Flora By M/S&Co.", "BTC", "24K Gold", "Rs 3,500",
            "main", "draft PR", "memory", "MP4", "never",
        ]
        for term in required:
            with self.subTest(term=term):
                self.assertIn(term.lower(), master.lower())


if __name__ == "__main__":
    unittest.main()
