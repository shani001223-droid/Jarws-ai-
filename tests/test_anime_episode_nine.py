"""EP009: lawful library research costs, custody and tamper-resistant draft export."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloud_backend.anime_episode_nine import episode_nine_script, validate_episode_nine
from cloud_backend.anime_episode_eight import episode_eight_script
from cloud_backend.anime_series import series_manifest


def rehash(draft):
    raw = {k: v for k, v in draft.items() if k != "sha256"}
    draft["sha256"] = hashlib.sha256(json.dumps(
        raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


class EpisodeNineTests(unittest.TestCase):
    def test_public_library_beat_and_provenance(self):
        draft = episode_nine_script()
        outline = series_manifest()["episodes"][8]
        self.assertEqual(draft["episode_id"], "EP009")
        self.assertEqual(draft["episode_beat"], 4)
        self.assertEqual(draft["story_day"], 5)
        self.assertEqual(draft["source_event"], outline["event"])
        self.assertEqual(draft["source_handoff"], outline["handoff"])
        self.assertEqual(draft["previous_episode_sha256"], episode_eight_script()["sha256"])
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
        self.assertEqual(state["library_condition_history"], "not_accessed_staff_review_pending")
        self.assertEqual(state["catalog_dates"], "public_discrepancy_not_proof_of_tampering")
        self.assertEqual(state["records_request"], "submitted_receipt_not_permission")
        self.assertEqual(state["public_inventory_crosscheck"], "read_only_public_entries_logged_no_missing_page_found")
        self.assertEqual(state["private_borrower_data"], "not_collected_or_disclosed")
        self.assertEqual(state["library_staff_identity"], "not_recorded_for_publication")
        self.assertEqual(state["library_copy_review"], "independent_custodian_pending")
        self.assertEqual(state["volunteer_hours"], "limited_hours_logged_no_personal_data")
        self.assertEqual(state["library_public_access"], "supervised_only_not_restricted")
        self.assertEqual(draft["approval"], "editorial_draft_not_reviewed")
        for flag in ("human_reviewed", "spoken_duration_verified", "rendered"):
            self.assertIs(draft[flag], False)

    def test_determinism_and_copy_isolation(self):
        a, b = episode_nine_script(), episode_nine_script()
        self.assertEqual(a, b)
        digest = a.pop("sha256")
        self.assertEqual(digest, hashlib.sha256(json.dumps(
            a, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest())
        b["scenes"][0]["dialogue"][0]["text"] = "changed"
        b["carried_forward"]["signal_source"] = "known"
        self.assertNotEqual(episode_nine_script()["scenes"][0]["dialogue"][0]["text"], "changed")
        self.assertEqual(episode_nine_script()["carried_forward"]["signal_source"], "unknown")

    def test_reject_rehashed_mutations(self):
        mutations = {
            "prior_digest": lambda x: x.update(previous_episode_sha256="0" * 64),
            "outline": lambda x: x.update(source_outline_sha256="0" * 64),
            "story_day": lambda x: x.update(story_day=2),
            "beat": lambda x: x.update(episode_beat=1),
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
            "fake_condition_history": lambda x: x["carried_forward"].update(library_condition_history="accessed"),
            "false_ledger_match": lambda x: x["carried_forward"].update(catalog_dates="proof_of_sabotage"),
            "receipt_as_approval": lambda x: x["carried_forward"].update(records_request="permission_granted"),
            "source": lambda x: x["carried_forward"].update(signal_source="known"),
            "invented_inventory_find": lambda x: x["carried_forward"].update(public_inventory_crosscheck="missing_page_found"),
            "borrower_privacy": lambda x: x["carried_forward"].update(private_borrower_data="copied"),
            "staff_privacy": lambda x: x["carried_forward"].update(library_staff_identity="published"),
            "forged_review": lambda x: x["carried_forward"].update(library_copy_review="approved"),
            "fabricated_hours": lambda x: x["carried_forward"].update(volunteer_hours="unlimited"),
            "fake_access": lambda x: x["carried_forward"].update(library_public_access="restricted_access_granted"),
            "scene_count": lambda x: x["scenes"].pop(),
            "scene_order": lambda x: x["scenes"][1].update(number=1),
            "timing": lambda x: x["scenes"][1].update(start_second=1000),
            "cast": lambda x: x["scenes"][0]["dialogue"][0].update(speaker="stranger"),
            "dialogue": lambda x: x["scenes"][0]["dialogue"][0].update(text="Unapproved altered text"),
            "extra_field": lambda x: x.update(published=True),
        }
        for name, mutate in mutations.items():
            draft = copy.deepcopy(episode_nine_script())
            mutate(draft)
            rehash(draft)
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_episode_nine(draft)

    def test_original_cast_and_no_network(self):
        draft = episode_nine_script()
        speakers = {turn["speaker"] for scene in draft["scenes"] for turn in scene["dialogue"]}
        self.assertEqual(speakers, {"laila", "rayan", "meher", "aman", "zoya"})
        self.assertNotIn("https://", json.dumps(draft["scenes"]).lower())

    def test_create_only_private_export(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "ep008.json"
            cmd = [sys.executable, "-m", "scripts.export_hoshi_anime_episode_nine",
                   "--out", str(target)]
            first = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), episode_nine_script())
            original = target.read_bytes()
            second = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=15)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
