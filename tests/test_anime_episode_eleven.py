"""EP011: offline antenna planning, provenance, privacy and tamper regression."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloud_backend.anime_episode_eleven import episode_eleven_script, validate_episode_eleven
from cloud_backend.anime_episode_ten import episode_ten_script
from cloud_backend.anime_series import series_manifest


def rehash(draft):
    raw = {k: v for k, v in draft.items() if k != "sha256"}
    draft["sha256"] = hashlib.sha256(json.dumps(
        raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


class EpisodeElevenTests(unittest.TestCase):
    def test_ishara_outline_and_prior_revision(self):
        draft = episode_eleven_script()
        outline = series_manifest()["episodes"][10]
        self.assertEqual(draft["episode_id"], "EP011")
        self.assertEqual(draft["previous_episode_id"], "EP010")
        self.assertEqual(draft["previous_episode_sha256"], episode_ten_script()["sha256"])
        self.assertEqual(draft["source_outline_sha256"], series_manifest()["sha256"])
        self.assertEqual(draft["episode_beat"], 1)
        self.assertEqual(draft["story_day"], outline["story_day"])
        self.assertEqual(draft["source_event"], outline["event"])
        self.assertEqual(draft["source_handoff"], outline["handoff"])
        self.assertEqual(draft["known_revelations"], [])
        self.assertEqual(len(draft["scenes"]), 8)
        self.assertEqual(sum(len(s["dialogue"]) for s in draft["scenes"]), 32)
        self.assertEqual(sum(s["planned_seconds"] for s in draft["scenes"]), 1800)
        self.assertEqual(
            {t["speaker"] for s in draft["scenes"] for t in s["dialogue"]},
            {"laila", "rayan", "meher", "aman", "zoya"},
        )
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
            "restricted_library_records": "written_request_pending",
            "records_request": "submitted_receipt_not_permission",
            "missing_index_page": "absent_logged_not_reconstructed",
            "library_copy_review": "independent_custodian_pending",
            "private_borrower_data": "not_collected_or_disclosed",
            "library_staff_identity": "not_recorded_for_publication",
            "library_handoff_packet": "two_numbered_internal_copies_independent_review_pending",
            "library_request_deadline": "no_authorized_response_yet",
            "antenna_calibration": "offline_reference_checklist_drafted_not_tested",
            "antenna_fixture": "visible_bend_unverified_cause_not_adjusted",
            "signal_direction": "not_measured_source_unknown",
            "power_authorization": "separate_power_and_safety_clearance_pending",
            "next_sequence": "antenna_calibration_access_obstacle_pending",
        }.items():
            self.assertEqual(state[key], expected, key)

    def test_digest_and_mutable_copy_isolation(self):
        a, b = episode_eleven_script(), episode_eleven_script()
        self.assertEqual(a, b)
        digest = a.pop("sha256")
        self.assertEqual(digest, hashlib.sha256(json.dumps(
            a, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest())
        b["scenes"][0]["dialogue"][0]["text"] = "Unauthorized changed text"
        b["carried_forward"]["signal_source"] = "known"
        self.assertNotEqual(episode_eleven_script()["scenes"][0]["dialogue"][0]["text"], "Unauthorized changed text")
        self.assertEqual(episode_eleven_script()["carried_forward"]["signal_source"], "unknown")

    def test_reject_rehashed_fabricated_evidence(self):
        mutations = {
            "previous_digest": lambda d: d.update(previous_episode_sha256="0" * 64),
            "outline_digest": lambda d: d.update(source_outline_sha256="0" * 64),
            "wrong_beat": lambda d: d.update(episode_beat=2),
            "false_review": lambda d: d.update(human_reviewed=True),
            "false_runtime": lambda d: d.update(spoken_duration_verified=True),
            "false_render": lambda d: d.update(rendered=True),
            "fake_approval": lambda d: d.update(approval="approved"),
            "spoiler": lambda d: d.update(known_revelations=["signal_source_found"]),
            "forged_custodian": lambda d: d["carried_forward"].update(library_copy_review="approved"),
            "fake_access": lambda d: d["carried_forward"].update(locked_corridor_access="granted"),
            "receipt_not_permission": lambda d: d["carried_forward"].update(records_request="permission_granted"),
            "invented_page": lambda d: d["carried_forward"].update(missing_index_page="reconstructed"),
            "invented_source": lambda d: d["carried_forward"].update(signal_source="known"),
            "false_calibration": lambda d: d["carried_forward"].update(antenna_calibration="live_test_completed"),
            "false_direction": lambda d: d["carried_forward"].update(signal_direction="canal_confirmed"),
            "fake_power": lambda d: d["carried_forward"].update(power_authorization="granted"),
            "fake_packet_review": lambda d: d["carried_forward"].update(library_handoff_packet="approved"),
            "false_notice": lambda d: d["carried_forward"].update(public_notice="issued"),
            "clinic_power": lambda d: d["carried_forward"].update(clinic_priority="receiver_first"),
            "wrong_predecessor": lambda d: d.update(previous_episode_id="EP009"),
            "changed_line": lambda d: d["scenes"][0]["dialogue"][0].update(text="Edited dialogue"),
            "scene_timing": lambda d: d["scenes"][1].update(start_second=10),
            "scene_count": lambda d: d["scenes"].pop(),
            "extra_field": lambda d: d.update(published=True),
        }
        for name, change in mutations.items():
            draft = copy.deepcopy(episode_eleven_script())
            change(draft)
            rehash(draft)
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_episode_eleven(draft)

    def test_private_create_only_export(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "ep011.json"
            command = [sys.executable, "-m", "scripts.export_hoshi_anime_episode_eleven",
                       "--out", str(target)]
            first = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), episode_eleven_script())
            original = target.read_bytes()
            second = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
