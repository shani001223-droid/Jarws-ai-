"""EP004: continuity, tamper resistance, draft truth and offline export."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloud_backend.anime_episode_four import episode_four_script, validate_episode_four
from cloud_backend.anime_episode_three import episode_three_script
from cloud_backend.anime_series import series_manifest

class EpisodeFourTests(unittest.TestCase):
    def test_beat_cost_and_provenance(self):
        draft = episode_four_script()
        outline = series_manifest()["episodes"][3]
        self.assertEqual(draft["episode_id"], "EP004")
        self.assertEqual(draft["episode_beat"], 4)
        self.assertEqual(draft["story_day"], 2)
        self.assertEqual(draft["source_event"], outline["event"])
        self.assertEqual(draft["source_handoff"], outline["handoff"])
        self.assertEqual(draft["previous_episode_sha256"], episode_three_script()["sha256"])
        self.assertEqual(draft["source_outline_sha256"], series_manifest()["sha256"])
        self.assertEqual(len(draft["scenes"]), 8)
        self.assertEqual(sum(len(s["dialogue"]) for s in draft["scenes"]), 32)
        self.assertEqual(sum(s["planned_seconds"] for s in draft["scenes"]), 1800)
        self.assertEqual(draft["known_revelations"], [])
        self.assertEqual(draft["carried_forward"]["signal_source"], "unknown")
        self.assertEqual(draft["carried_forward"]["locked_corridor_access"], "written_permission_pending")
        self.assertEqual(draft["carried_forward"]["public_notice"], "draft_not_issued")
        self.assertEqual(draft["approval"], "editorial_draft_not_reviewed")
        for flag in ("human_reviewed", "spoken_duration_verified", "rendered"):
            self.assertIs(draft[flag], False)

    def test_deterministic_and_fresh(self):
        first, second = episode_four_script(), episode_four_script()
        self.assertEqual(first, second)
        digest = first.pop("sha256")
        self.assertEqual(digest, hashlib.sha256(json.dumps(
            first, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest())
        second["scenes"][0]["dialogue"][0]["text"] = "changed"
        second["carried_forward"]["signal_source"] = "known"
        self.assertNotEqual(episode_four_script()["scenes"][0]["dialogue"][0]["text"], "changed")
        self.assertEqual(episode_four_script()["carried_forward"]["signal_source"], "unknown")

    def test_fail_closed_on_rehashed_mutations(self):
        mutations = {
            "prior_digest": lambda x: x.update(previous_episode_sha256="0" * 64),
            "outline": lambda x: x.update(source_outline_sha256="0" * 64),
            "story_day": lambda x: x.update(story_day=1),
            "false_review": lambda x: x.update(human_reviewed=True),
            "false_duration": lambda x: x.update(spoken_duration_verified=True),
            "false_render": lambda x: x.update(rendered=True),
            "approval": lambda x: x.update(approval="approved"),
            "spoiler": lambda x: x.update(known_revelations=["future"]),
            "permission": lambda x: x["carried_forward"].update(locked_corridor_access="approved"),
            "notice": lambda x: x["carried_forward"].update(public_notice="issued"),
            "source": lambda x: x["carried_forward"].update(signal_source="known"),
            "scene_count": lambda x: x["scenes"].pop(),
            "scene_order": lambda x: x["scenes"][1].update(number=1),
            "timing": lambda x: x["scenes"][1].update(start_second=1000),
            "cast": lambda x: x["scenes"][0]["dialogue"][0].update(speaker="stranger"),
            "dialogue": lambda x: x["scenes"][0]["dialogue"][0].update(text="Unapproved altered text"),
            "extra_field": lambda x: x.update(published=True),
        }
        for name, mutate in mutations.items():
            draft = copy.deepcopy(episode_four_script())
            mutate(draft)
            raw = {k: v for k, v in draft.items() if k != "sha256"}
            draft["sha256"] = hashlib.sha256(json.dumps(
                raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_episode_four(draft)

    def test_original_cast_and_no_network(self):
        draft = episode_four_script()
        speakers = {turn["speaker"] for scene in draft["scenes"] for turn in scene["dialogue"]}
        self.assertEqual(speakers, {"laila", "rayan", "meher", "aman", "zoya"})
        self.assertNotIn("https://", json.dumps(draft["scenes"]).lower())

    def test_create_only_private_export(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "ep004.json"
            cmd = [sys.executable, "-m", "scripts.export_hoshi_anime_episode_four",
                   "--out", str(target)]
            first = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), episode_four_script())
            original = target.read_bytes()
            second = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(target.read_bytes(), original)

if __name__ == "__main__":
    unittest.main()
