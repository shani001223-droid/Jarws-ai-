"""EP012: legal-access obstacle, provenance, privacy and negative mutation tests."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloud_backend.anime_episode_twelve import episode_twelve_script, validate_episode_twelve
from cloud_backend.anime_episode_eleven import episode_eleven_script
from cloud_backend.anime_series import series_manifest


def rehash(draft):
    data = {key: value for key, value in draft.items() if key != "sha256"}
    draft["sha256"] = hashlib.sha256(json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


class EpisodeTwelveTests(unittest.TestCase):
    def test_rukawat_outline_provenance_and_scene_counts(self):
        draft = episode_twelve_script()
        outline = series_manifest()["episodes"][11]
        self.assertEqual(draft["episode_id"], "EP012")
        self.assertEqual(draft["previous_episode_id"], "EP011")
        self.assertEqual(draft["previous_episode_sha256"], episode_eleven_script()["sha256"])
        self.assertEqual(draft["source_outline_sha256"], series_manifest()["sha256"])
        self.assertEqual(draft["episode_beat"], 2)
        self.assertEqual(draft["story_day"], outline["story_day"])
        self.assertEqual(draft["source_event"], outline["event"])
        self.assertEqual(draft["source_handoff"], outline["handoff"])
        self.assertEqual(draft["known_revelations"], [])
        self.assertEqual(len(draft["scenes"]), 8)
        self.assertEqual(sum(len(s["dialogue"]) for s in draft["scenes"]), 32)
        self.assertEqual(sum(s["planned_seconds"] for s in draft["scenes"]), 1800)
        self.assertEqual({t["speaker"] for s in draft["scenes"] for t in s["dialogue"]},
                         {"laila", "rayan", "meher", "aman", "zoya"})
        self.assertEqual(draft["approval"], "editorial_draft_not_reviewed")
        for key in ("human_reviewed", "spoken_duration_verified", "rendered"):
            self.assertIs(draft[key], False)
        state = draft["carried_forward"]
        for key, expected in {
            "signal_source": "unknown",
            "clock_offset": "two_minutes_not_silently_corrected",
            "locked_corridor_access": "written_permission_pending",
            "clinic_priority": "patient_safety_before_receiver_test",
            "public_notice": "draft_not_issued",
            "missing_index_page": "absent_logged_not_reconstructed",
            "library_copy_review": "independent_custodian_pending",
            "private_borrower_data": "not_collected_or_disclosed",
            "library_handoff_packet": "two_numbered_internal_copies_independent_review_pending",
            "antenna_calibration": "offline_reference_checklist_drafted_not_tested",
            "signal_direction": "not_measured_source_unknown",
            "power_authorization": "separate_power_and_safety_clearance_pending",
            "antenna_access_obstacle": "incomplete_annex_no_access_or_denial",
            "safety_review": "requested_not_authorized",
            "next_sequence": "lawful_alternative_access_plan_pending",
        }.items():
            self.assertEqual(state[key], expected, key)

    def test_digest_and_mutable_copy_isolation(self):
        first, second = episode_twelve_script(), episode_twelve_script()
        self.assertEqual(first, second)
        digest = first.pop("sha256")
        self.assertEqual(digest, hashlib.sha256(json.dumps(
            first, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest())
        second["scenes"][0]["dialogue"][0]["text"] = "Unauthorized change"
        second["carried_forward"]["signal_source"] = "known"
        self.assertNotEqual(episode_twelve_script()["scenes"][0]["dialogue"][0]["text"],
                            "Unauthorized change")
        self.assertEqual(episode_twelve_script()["carried_forward"]["signal_source"], "unknown")

    def test_reject_rehashed_forgery_and_changed_dialogue(self):
        changes = {
            "wrong_predecessor": lambda d: d.update(previous_episode_sha256="0" * 64),
            "wrong_outline": lambda d: d.update(source_outline_sha256="0" * 64),
            "wrong_beat": lambda d: d.update(episode_beat=3),
            "fake_review": lambda d: d.update(human_reviewed=True),
            "fake_runtime": lambda d: d.update(spoken_duration_verified=True),
            "fake_approval": lambda d: d.update(approval="approved"),
            "false_render": lambda d: d.update(rendered=True),
            "spoiler": lambda d: d.update(known_revelations=["signal_source_known"]),
            "fake_corridor": lambda d: d["carried_forward"].update(locked_corridor_access="granted"),
            "fake_power": lambda d: d["carried_forward"].update(power_authorization="granted"),
            "fake_safety": lambda d: d["carried_forward"].update(safety_review="approved"),
            "fake_antenna": lambda d: d["carried_forward"].update(antenna_calibration="completed"),
            "fake_direction": lambda d: d["carried_forward"].update(signal_direction="canal_measured"),
            "false_denial": lambda d: d["carried_forward"].update(antenna_access_obstacle="denied"),
            "false_notice": lambda d: d["carried_forward"].update(public_notice="issued"),
            "fake_library_review": lambda d: d["carried_forward"].update(library_copy_review="approved"),
            "missing_page_found": lambda d: d["carried_forward"].update(missing_index_page="found"),
            "clinic_diversion": lambda d: d["carried_forward"].update(clinic_priority="receiver_first"),
            "changed_line": lambda d: d["scenes"][0]["dialogue"][0].update(text="Edited line"),
            "scene_timing": lambda d: d["scenes"][2].update(start_second=100),
            "missing_scene": lambda d: d["scenes"].pop(),
            "extra_field": lambda d: d.update(published=True),
        }
        for name, change in changes.items():
            draft = copy.deepcopy(episode_twelve_script())
            change(draft)
            rehash(draft)
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_episode_twelve(draft)

    def test_private_create_only_export(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "ep012.json"
            cmd = [sys.executable, "-m", "scripts.export_hoshi_anime_episode_twelve",
                   "--out", str(target)]
            first = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")),
                             episode_twelve_script())
            original = target.read_bytes()
            second = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
