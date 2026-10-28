"""Completion-state safety checks; integrity is not historical truth certification."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_v3_knowledge as curriculum


class CurriculumStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "chapter.md"
        self.path.write_text("# INCOMPLETE DRAFT\nSynthetic state fixture, not a curriculum chapter.\n")
        self.draft = {"status": "draft", "completion_blockers": ["Verified dated endpoint pairs are missing."],
                      "runtime_eligible": False}

    def test_draft_requires_explicit_blockers_and_runtime_exclusion(self):
        self.assertEqual(curriculum.document_state(self.draft, self.path), "draft")
        for changes in ({"completion_blockers": []}, {"completion_blockers": None},
                        {"completion_blockers": [""]}, {"completion_blockers": "missing"},
                        {"runtime_eligible": True}, {"runtime_eligible": None}):
            with self.subTest(changes=changes), self.assertRaises(AssertionError):
                curriculum.document_state({**self.draft, **changes}, self.path)

    def test_changing_only_draft_status_cannot_manufacture_completion(self):
        with self.assertRaisesRegex(AssertionError, "Unresolved completion blockers"):
            curriculum.document_state({**self.draft, "status": "source_checked"}, self.path)
        with self.assertRaises(AssertionError):
            curriculum.document_state({**self.draft, "status": "source_checked",
                                       "completion_blockers": []}, self.path)
        self.assertEqual(curriculum.document_state({"status": "source_checked"}, self.path),
                         "source_checked")  # Human source review is a separate requirement.

    def test_pending_cannot_hide_a_written_file_or_unknown_state(self):
        with self.assertRaises(AssertionError):
            curriculum.document_state({"status": "pending"}, self.path)
        for state in ("complete", "trained", "loaded"):
            with self.subTest(state=state), self.assertRaises(AssertionError):
                curriculum.document_state({"status": state}, self.path)
        absent = self.path.with_name("absent.md")
        self.assertEqual(curriculum.document_state({"status": "pending"}, absent), "pending")
        with self.assertRaises(AssertionError):
            curriculum.document_state(self.draft, absent)

    def test_current_manifest_counts_only_source_checked_chapters(self):
        manifest = json.loads(curriculum.MANIFEST.read_text())
        result = curriculum.check()
        complete = sum(d["status"] == "source_checked" for d in manifest["documents"])
        drafts = sum(d["status"] == "draft" for d in manifest["documents"])
        self.assertEqual(result["completed_documents"], complete)
        self.assertEqual(result["planned_documents"], len(manifest["documents"]))
        self.assertEqual(result["draft_documents"], drafts)
        self.assertEqual(len(result["drafts"]), drafts)
        self.assertEqual(result["curriculum_percent"], round(100 * complete / len(manifest["documents"]), 2))
        self.assertEqual(result["curriculum_source_complete"], complete == len(manifest["documents"]))

    def test_current_draft_cannot_be_promoted_with_unresolved_receipts(self):
        manifest = json.loads(curriculum.MANIFEST.read_text())
        draft = next((d for d in manifest["documents"] if d["status"] == "draft"), None)
        if draft is None:
            self.skipTest("No current draft remains; synthetic promotion guards still run.")
        changed = copy.deepcopy(manifest)
        target = next(d for d in changed["documents"] if d["path"] == draft["path"])
        target["status"] = "source_checked"
        file = Path(self.directory.name) / "manifest.json"
        file.write_text(json.dumps(changed))
        with patch.object(curriculum, "MANIFEST", file), self.assertRaises(AssertionError):
            curriculum.check()

    def test_removing_metadata_blockers_still_cannot_complete_a_visible_draft(self):
        manifest = json.loads(curriculum.MANIFEST.read_text())
        target = next((d for d in manifest["documents"] if d["status"] == "draft"), None)
        if target is None:
            self.skipTest("No current draft remains; synthetic promotion guards still run.")
        target.update(status="source_checked", completion_blockers=[], runtime_eligible=True)
        file = Path(self.directory.name) / "manifest.json"
        file.write_text(json.dumps(manifest))
        with patch.object(curriculum, "MANIFEST", file), self.assertRaisesRegex(AssertionError, "visible draft cannot be completed"):
            curriculum.check()


if __name__ == "__main__":
    unittest.main()
