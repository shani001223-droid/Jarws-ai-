"""EP003 chronology, provenance, false completion, tamper and export tests."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from cloud_backend.anime_episode_three import episode_three_script, validate_episode_three
from cloud_backend.anime_episode_two import episode_two_script
from cloud_backend.anime_series import series_manifest

class EpisodeThreeTests(unittest.TestCase):
    def test_chronology_and_editorial_truth(self):
        draft = episode_three_script()
        outline = series_manifest()["episodes"][2]
        self.assertEqual(draft["episode_id"], "EP003")
        self.assertEqual(draft["previous_episode_sha256"], episode_two_script()["sha256"])
        self.assertEqual(draft["source_outline_sha256"], series_manifest()["sha256"])
        self.assertEqual(draft["episode_beat"], 3)
        self.assertEqual(draft["story_day"], 2)
        self.assertEqual(draft["source_event"], outline["event"])
        self.assertEqual(draft["source_handoff"], outline["handoff"])
        self.assertEqual(len(draft["scenes"]), 8)
        self.assertEqual(sum(len(scene["dialogue"]) for scene in draft["scenes"]), 32)
        self.assertEqual(sum(scene["planned_seconds"] for scene in draft["scenes"]), 1800)
        self.assertEqual(draft["known_revelations"], [])
        self.assertEqual(draft["carried_forward"]["locked_corridor_access"], "written_permission_pending")
        self.assertEqual(draft["carried_forward"]["signal_source"], "unknown")
        self.assertEqual(draft["approval"], "editorial_draft_not_reviewed")
        self.assertFalse(draft["human_reviewed"])
        self.assertFalse(draft["spoken_duration_verified"])
        self.assertFalse(draft["rendered"])

    def test_deterministic_revision_and_fresh_objects(self):
        first, second = episode_three_script(), episode_three_script()
        self.assertEqual(first, second)
        digest = first.pop("sha256")
        raw = json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(raw.encode("utf-8")).hexdigest(), digest)
        second["scenes"][0]["dialogue"][0]["text"] = "tampered"
        second["carried_forward"]["signal_source"] = "known"
        self.assertNotEqual(episode_three_script()["scenes"][0]["dialogue"][0]["text"], "tampered")
        self.assertEqual(episode_three_script()["carried_forward"]["signal_source"], "unknown")

    def test_fail_closed_on_mutation_even_with_rehashed_text(self):
        mutations = {
            "previous": lambda x: x.update(previous_episode_sha256="0" * 64),
            "outline": lambda x: x.update(source_outline_sha256="0" * 64),
            "wrong_day": lambda x: x.update(story_day=1),
            "false_review": lambda x: x.update(human_reviewed=True),
            "false_audio": lambda x: x.update(spoken_duration_verified=True),
            "false_render": lambda x: x.update(rendered=True),
            "false_approval": lambda x: x.update(approval="approved"),
            "early_reveal": lambda x: x.update(known_revelations=["future"]),
            "false_permission": lambda x: x["carried_forward"].update(locked_corridor_access="approved"),
            "false_source": lambda x: x["carried_forward"].update(signal_source="known"),
            "missing_scene": lambda x: x["scenes"].pop(),
            "scene_order": lambda x: x["scenes"][1].update(number=1),
            "scene_timing": lambda x: x["scenes"][1].update(start_second=999),
            "short_dialogue": lambda x: x["scenes"][0]["dialogue"].pop(),
            "wrong_speaker": lambda x: x["scenes"][0]["dialogue"][0].update(speaker="other"),
            "spoiler": lambda x: x["scenes"][0]["dialogue"][0].update(text="founder-built guardian"),
            "extra_field": lambda x: x.update(published=True),
        }
        for name, mutation in mutations.items():
            payload = copy.deepcopy(episode_three_script())
            mutation(payload)
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_episode_three(payload)
        payload = episode_three_script()
        payload["scenes"][0]["dialogue"][0]["text"] = "Unapproved edited dialogue with recomputed digest"
        data = {k: v for k, v in payload.items() if k != "sha256"}
        payload["sha256"] = hashlib.sha256(json.dumps(
            data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        with self.assertRaises(ValueError):
            validate_episode_three(payload)

    def test_offline_original_five_character_dialogue(self):
        draft = episode_three_script()
        text = json.dumps(draft["scenes"], ensure_ascii=False).lower()
        self.assertNotIn("https://", text)
        self.assertNotIn("founder-built guardian", text)
        self.assertEqual({turn["speaker"] for scene in draft["scenes"] for turn in scene["dialogue"]},
                         {"laila", "rayan", "meher", "aman", "zoya"})

    def test_create_only_export(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "ep003.json"
            cmd = [sys.executable, "-m", "scripts.export_hoshi_anime_episode_three", "--out", str(target)]
            first = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=12)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), episode_three_script())
            before = target.read_bytes()
            second = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=12)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(target.read_bytes(), before)

if __name__ == "__main__":
    unittest.main()
