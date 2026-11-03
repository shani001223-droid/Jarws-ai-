"""EP006: public-library continuity, tamper resistance, draft truth and export."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloud_backend.anime_episode_six import episode_six_script, validate_episode_six
from cloud_backend.anime_episode_five import episode_five_script
from cloud_backend.anime_series import series_manifest


def rehash(draft):
    raw = {k: v for k, v in draft.items() if k != "sha256"}
    draft["sha256"] = hashlib.sha256(json.dumps(
        raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


class EpisodeSixTests(unittest.TestCase):
    def test_public_library_beat_and_provenance(self):
        draft = episode_six_script()
        outline = series_manifest()["episodes"][5]
        self.assertEqual(draft["episode_id"], "EP006")
        self.assertEqual(draft["episode_beat"], 1)
        self.assertEqual(draft["story_day"], 3)
        self.assertEqual(draft["source_event"], outline["event"])
        self.assertEqual(draft["source_handoff"], outline["handoff"])
        self.assertEqual(draft["previous_episode_sha256"], episode_five_script()["sha256"])
        self.assertEqual(draft["source_outline_sha256"], series_manifest()["sha256"])
        self.assertEqual(len(draft["scenes"]), 8)
        self.assertEqual(sum(len(s["dialogue"]) for s in draft["scenes"]), 32)
        self.assertEqual(sum(s["planned_seconds"] for s in draft["scenes"]), 1800)
        self.assertEqual(draft["known_revelations"], [])
        state = draft["carried_forward"]
        self.assertEqual(state["signal_source"], "unknown")
        self.assertEqual(state["locked_corridor_access"], "written_permission_pending")
        self.assertEqual(state["public_notice"], "draft_not_issued")
        self.assertEqual(state["handoff_receipt"], "internal_signed_independent_review_pending")
        self.assertEqual(state["missing_index_page"], "absent_logged_not_reconstructed")
        self.assertEqual(state["library_register"], "public_reference_catalog_and_bound_register_located")
        self.assertEqual(state["restricted_library_records"], "written_request_pending")
        self.assertEqual(draft["approval"], "editorial_draft_not_reviewed")
        for flag in ("human_reviewed", "spoken_duration_verified", "rendered"):
            self.assertIs(draft[flag], False)

    def test_determinism_and_copy_isolation(self):
        a, b = episode_six_script(), episode_six_script()
        self.assertEqual(a, b)
        digest = a.pop("sha256")
        self.assertEqual(digest, hashlib.sha256(json.dumps(
            a, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest())
        b["scenes"][0]["dialogue"][0]["text"] = "changed"
        b["carried_forward"]["signal_source"] = "known"
        self.assertNotEqual(episode_six_script()["scenes"][0]["dialogue"][0]["text"], "changed")
        self.assertEqual(episode_six_script()["carried_forward"]["signal_source"], "unknown")

    def test_reject_rehashed_mutations(self):
        mutations = {
            "prior_digest": lambda x: x.update(previous_episode_sha256="0" * 64),
            "outline": lambda x: x.update(source_outline_sha256="0" * 64),
            "story_day": lambda x: x.update(story_day=2),
            "beat": lambda x: x.update(episode_beat=2),
            "false_review": lambda x: x.update(human_reviewed=True),
            "false_duration": lambda x: x.update(spoken_duration_verified=True),
            "false_render": lambda x: x.update(rendered=True),
            "approval": lambda x: x.update(approval="approved"),
            "spoiler": lambda x: x.update(known_revelations=["relay_found"]),
            "corridor": lambda x: x["carried_forward"].update(locked_corridor_access="approved"),
            "notice": lambda x: x["carried_forward"].update(public_notice="issued"),
            "receipt": lambda x: x["carried_forward"].update(handoff_receipt="independently_approved"),
            "library": lambda x: x["carried_forward"].update(library_register="secret_frequency_discovered"),
            "missing_page": lambda x: x["carried_forward"].update(missing_index_page="reconstructed"),
            "private_access": lambda x: x["carried_forward"].update(restricted_library_records="approved"),
            "source": lambda x: x["carried_forward"].update(signal_source="known"),
            "scene_count": lambda x: x["scenes"].pop(),
            "scene_order": lambda x: x["scenes"][1].update(number=1),
            "timing": lambda x: x["scenes"][1].update(start_second=1000),
            "cast": lambda x: x["scenes"][0]["dialogue"][0].update(speaker="stranger"),
            "dialogue": lambda x: x["scenes"][0]["dialogue"][0].update(text="Unapproved altered text"),
            "extra_field": lambda x: x.update(published=True),
        }
        for name, mutate in mutations.items():
            draft = copy.deepcopy(episode_six_script())
            mutate(draft)
            rehash(draft)
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_episode_six(draft)

    def test_original_cast_and_no_network(self):
        draft = episode_six_script()
        speakers = {turn["speaker"] for scene in draft["scenes"] for turn in scene["dialogue"]}
        self.assertEqual(speakers, {"laila", "rayan", "meher", "aman", "zoya"})
        self.assertNotIn("https://", json.dumps(draft["scenes"]).lower())

    def test_create_only_private_export(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "ep006.json"
            cmd = [sys.executable, "-m", "scripts.export_hoshi_anime_episode_six",
                   "--out", str(target)]
            first = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), episode_six_script())
            original = target.read_bytes()
            second = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
