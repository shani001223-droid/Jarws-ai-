"""Task 56: private script-readiness QA, no fictional approvals."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloud_backend.anime_script_readiness import (
    BLOCKERS, _episode_row, build_readiness_report, validate_readiness_report,
)
from cloud_backend.anime_series import series_manifest
from cloud_backend.anime_episode_three import episode_three_script
from cloud_backend.anime_episode_six import episode_six_script
from cloud_backend.anime_episode_seven import episode_seven_script


class AnimeReadinessTests(unittest.TestCase):
    def test_all_authored_drafts_and_actual_word_counts(self):
        report = build_readiness_report()
        self.assertEqual([x["episode_id"] for x in report["episodes"]],
                         ["EP001", "EP002", "EP003", "EP004", "EP005", "EP006", "EP007"])
        self.assertEqual(report["remaining_individual_scripts"], 293)
        self.assertEqual(report["reviewed_scripts"], 0)
        self.assertEqual(report["production_ready_scripts"], 0)
        self.assertFalse(report["reference_is_measured"])
        self.assertFalse(report["published"])
        for row in report["episodes"]:
            self.assertEqual(row["planned_scene_seconds"], 1800)
            self.assertGreater(row["dialogue_words"], 0)
            self.assertGreater(row["dialogue_turns"], 0)
            self.assertIsNone(row["measured_runtime_seconds"])
            self.assertEqual(row["illustrative_spoken_seconds_at_120_wpm"],
                             row["dialogue_words"] // 2)
            self.assertFalse(row["verified_30_minute_screenplay"])
            self.assertFalse(row["production_ready"])
            self.assertEqual(row["blockers"], list(BLOCKERS))

    def test_determinism_and_digest(self):
        a = build_readiness_report()
        self.assertEqual(a, build_readiness_report())
        sha = a.pop("sha256")
        raw = json.dumps(a, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(sha, hashlib.sha256(raw.encode("utf-8")).hexdigest())

    def test_reject_rehashed_false_approvals_and_counts(self):
        mutations = [
            lambda x: x.update(reviewed_scripts=3),
            lambda x: x.update(remaining_individual_scripts=0),
            lambda x: x.update(published=True),
            lambda x: x["episodes"][0].update(approved=True),
            lambda x: x["episodes"][1].update(measured_runtime_seconds=1800),
            lambda x: x["episodes"][2].update(dialogue_words=99999),
            lambda x: x["episodes"][0]["blockers"].clear(),
            lambda x: x.update(reference_is_measured=True),
            lambda x: x.update(extra_field="approved"),
        ]
        for mutate in mutations:
            report = build_readiness_report()
            mutate(report)
            data = {k: v for k, v in report.items() if k != "sha256"}
            report["sha256"] = hashlib.sha256(json.dumps(
                data, ensure_ascii=False, sort_keys=True,
                separators=(",", ":")).encode("utf-8")).hexdigest()
            with self.assertRaises(ValueError):
                validate_readiness_report(report)

    def test_reject_modified_draft_even_with_new_hash(self):
        draft = episode_three_script()
        draft["scenes"][0]["dialogue"][0]["text"] = "Unauthorized new dialogue"
        data = {k: v for k, v in draft.items() if k != "sha256"}
        draft["sha256"] = hashlib.sha256(json.dumps(
            data, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        with self.assertRaises(ValueError):
            _episode_row(draft, 3, series_manifest()["sha256"])

    def test_reject_modified_sixth_draft_even_if_rehashed(self):
        draft = episode_six_script()
        draft["scenes"][2]["dialogue"][0]["text"] = "Fabricated register page content"
        data = {k: v for k, v in draft.items() if k != "sha256"}
        draft["sha256"] = hashlib.sha256(json.dumps(
            data, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        with self.assertRaises(ValueError):
            _episode_row(draft, 6, series_manifest()["sha256"])

    def test_reject_modified_seventh_draft_even_if_rehashed(self):
        draft = episode_seven_script()
        draft["carried_forward"]["records_request"] = "approved"
        data = {k: v for k, v in draft.items() if k != "sha256"}
        draft["sha256"] = hashlib.sha256(json.dumps(
            data, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        with self.assertRaises(ValueError):
            _episode_row(draft, 7, series_manifest()["sha256"])

    def test_private_create_only_export(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "readiness.json"
            cmd = [sys.executable, "-m", "scripts.audit_hoshi_anime_scripts",
                   "--out", str(target)]
            first = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")),
                             build_readiness_report())
            original = target.read_bytes()
            second = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
