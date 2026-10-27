"""Curriculum integrity, bounded retrieval and backend deployment parity."""
from hashlib import sha256
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from cloud_backend import brain

ROOT = Path(__file__).resolve().parents[1]


class TradingKnowledgeTests(unittest.TestCase):
    def tearDown(self):
        brain.load_knowledge.cache_clear()

    def test_all_11_canonical_files_and_prompt_match_runtime_bundle(self):
        knowledge = brain.load_knowledge()
        self.assertEqual(len(knowledge.lessons), 11)
        self.assertEqual(len({x.id for x in knowledge.lessons}), 11)
        for lesson in knowledge.lessons:
            canonical = (ROOT / "modules" / lesson.filename).read_text(encoding="utf-8")
            self.assertEqual(lesson.content, canonical)
            self.assertEqual(lesson.digest, sha256(canonical.encode()).hexdigest())
        self.assertEqual(knowledge.system_prompt, (ROOT / "HOSHI_SYSTEM_PROMPT_FINAL.txt").read_text())

    def test_ten_modules_have_three_explicitly_conditional_chart_exercises(self):
        for lesson in brain.load_knowledge().lessons[1:]:
            examples = lesson.content.split("## 3 Live Chart Examples\n\n")[1].split("## Sources")[0]
            self.assertEqual(len(re.findall(r"^[123]\. \*\*\[", examples, re.M)), 3)
            self.assertIn("not a verified live", lesson.content.replace("**", "").replace("\n", " "))
            for heading in ("Definition", "Application Zone", "Failure Zone"):
                self.assertIn("## " + heading, lesson.content)

    def test_history_corrects_1971_and_hft_timeline_shortcuts(self):
        text = brain.get_lesson("history")["content"]
        for date in ("1602", "1637", "1902", "1931", "1938", "1971", "1973", "1987", "2008", "2009", "2020–2025"):
            self.assertIn(date, text)
        self.assertIn("foreign exchange existed long before", text)
        self.assertIn("not HFT's invention", text)

    def test_unknown_ids_and_paths_cannot_load_files(self):
        for key in ("../main.py", "/etc/passwd", "https://example.com", "nonexistent"):
            with self.assertRaises(KeyError):
                brain.get_lesson(key)

    def test_retrieval_is_bounded_relevant_and_omits_nontrading_chat(self):
        text = brain.trading_context("ICT Silver Bullet aur FVG ka failure zone samjhao")
        self.assertIn("[ict;", text)
        self.assertIn("[fvg_imbalances;", text)
        self.assertIn("Failure Zone:", text)
        self.assertLessEqual(len(text), 4800)
        self.assertEqual(brain.trading_context("Flora shampoo ke ads banao"), "")
        self.assertEqual(brain.trading_context("Hi how are you?"), "")

    def test_index_returns_copies_and_never_claims_training(self):
        payload = brain.knowledge_index()
        payload["lessons"][0]["title"] = "changed"
        self.assertEqual(brain.knowledge_index()["lessons"][0]["title"], "Trading History")
        self.assertFalse(payload["training_enabled"])
        self.assertFalse(brain.get_lesson("ict")["live_examples_verified"])

    def test_tampered_missing_and_wrong_identity_bundles_fail_closed(self):
        original = json.loads((ROOT / "cloud_backend" / "knowledge_bundle.json").read_bytes())
        for kind in ("content", "identity", "missing", "prompt", "invalid_json"):
            candidate = json.loads(json.dumps(original))
            if kind == "content":
                candidate["lessons"][0]["content"] += "changed"
            elif kind == "identity":
                candidate["lessons"][0]["id"] = "other"
            elif kind == "missing":
                candidate["lessons"].pop()
            elif kind == "prompt":
                candidate["system_prompt"] += "changed"
            raw = b"not-json" if kind == "invalid_json" else json.dumps(candidate).encode()
            brain.load_knowledge.cache_clear()
            with patch.object(Path, "read_bytes", return_value=raw), self.assertRaises(brain.KnowledgeError):
                brain.load_knowledge()

    def test_missing_runtime_file_does_not_fall_back_to_random_paths(self):
        brain.load_knowledge.cache_clear()
        with patch.object(Path, "read_bytes", side_effect=OSError("private path")):
            with self.assertRaises(brain.KnowledgeError):
                brain.load_knowledge()


if __name__ == "__main__":
    unittest.main()
