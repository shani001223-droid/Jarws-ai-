"""Task 56 EP001 pilot continuity, timing, rights and truth-in-status tests."""
import copy
import hashlib
import json
import unittest

from cloud_backend.anime_series import series_manifest
from cloud_backend.anime_scripts import PILOT_ID, pilot_script, validate_pilot


class PilotScriptTests(unittest.TestCase):
    def test_pilot_has_ten_authored_scenes_and_planned_30_minutes(self):
        script = pilot_script()
        self.assertEqual(script["episode_id"], PILOT_ID)
        self.assertEqual(len(script["scenes"]), 10)
        self.assertEqual(script["planned_seconds"], 1800)
        self.assertEqual(sum(s["planned_seconds"] for s in script["scenes"]), 1800)
        self.assertGreaterEqual(sum(len(s["dialogue"]) for s in script["scenes"]), 40)
        self.assertEqual(script["source_outline_sha256"], series_manifest()["sha256"])
        self.assertEqual(script["source_event"], series_manifest()["episodes"][0]["event"])
        self.assertEqual(script["source_handoff"], series_manifest()["episodes"][0]["handoff"])
        self.assertEqual(script["known_revelations"], [])
        self.assertFalse(script["human_reviewed"])
        self.assertFalse(script["rendered"])
        self.assertFalse(script["spoken_duration_verified"])

    def test_stable_revision_digest_and_fresh_objects(self):
        a, b = pilot_script(), pilot_script()
        self.assertEqual(a, b)
        digest = a.pop("sha256")
        canonical = json.dumps(a, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(canonical.encode("utf-8")).hexdigest(), digest)
        b["scenes"][0]["dialogue"][0]["text"] = "tampered"
        self.assertNotEqual(pilot_script()["scenes"][0]["dialogue"][0]["text"], "tampered")

    def test_rejects_broken_story_cast_time_and_false_review(self):
        base = pilot_script()
        changes = {
            "fake_review": lambda x: x.update(human_reviewed=True),
            "fake_render": lambda x: x.update(rendered=True),
            "fake_spoken_duration": lambda x: x.update(spoken_duration_verified=True),
            "fake_approval": lambda x: x.update(approval="approved"),
            "wrong_outline": lambda x: x.update(source_outline_sha256="0" * 64),
            "wrong_handoff": lambda x: x.update(source_handoff="unearned reveal"),
            "missing_scene": lambda x: x["scenes"].pop(),
            "scene_order": lambda x: x["scenes"][1].update(number=1),
            "timing_gap": lambda x: x["scenes"][1].update(start_second=999),
            "timing_overrun": lambda x: x["scenes"][0].update(planned_seconds=999),
            "wrong_total": lambda x: x.update(planned_seconds=999),
            "unknown_cast": lambda x: x["scenes"][0]["dialogue"][0].update(speaker="unknown"),
            "short_dialogue": lambda x: x["scenes"][0]["dialogue"][0].update(text="Hi"),
            "thin_scene": lambda x: x["scenes"][0].update(dialogue=[]),
            "early_reveal": lambda x: x["scenes"][0]["dialogue"][0].update(
                text="Yahan energy diversion ka pattern sabit ho chuka hai, isay foran announce kar do."),
            "reveal_gate": lambda x: x.update(known_revelations=["future"]),
        }
        for name, mutation in changes.items():
            candidate = copy.deepcopy(base)
            mutation(candidate)
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_pilot(candidate)

    def test_no_production_claims_or_unlicensed_cast(self):
        script = pilot_script()
        self.assertEqual(script["approval"], "editorial_draft_not_reviewed")
        self.assertEqual(script["language"], "Pakistani Roman Urdu")
        self.assertEqual({line["speaker"] for scene in script["scenes"] for line in scene["dialogue"]},
                         {"laila", "rayan", "meher", "aman", "zoya"})
        self.assertFalse(any("http://" in line["text"] or "https://" in line["text"]
                             for scene in script["scenes"] for line in scene["dialogue"]))


if __name__ == "__main__":
    unittest.main()
