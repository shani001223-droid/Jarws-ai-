"""Task 56 EP002 continuity, consent, revision and non-completion regression tests."""
import copy
import hashlib
import json
import unittest

from cloud_backend.anime_episode_two import episode_two_script, validate_episode_two
from cloud_backend.anime_scripts import pilot_script
from cloud_backend.anime_series import series_manifest


class EpisodeTwoTests(unittest.TestCase):
    def test_eight_authored_scenes_follow_pilot(self):
        script = episode_two_script()
        outline = series_manifest()["episodes"][1]
        self.assertEqual(script["episode_id"], "EP002")
        self.assertEqual(script["previous_episode_sha256"], pilot_script()["sha256"])
        self.assertEqual(script["source_event"], outline["event"])
        self.assertEqual(script["source_handoff"], outline["handoff"])
        self.assertEqual(script["episode_beat"], 2)
        self.assertEqual(script["story_day"], 1)
        self.assertEqual(len(script["scenes"]), 8)
        self.assertEqual(sum(len(scene["dialogue"]) for scene in script["scenes"]), 32)
        self.assertEqual(sum(scene["planned_seconds"] for scene in script["scenes"]), 1800)
        self.assertEqual(script["known_revelations"], [])
        self.assertEqual(script["carried_forward"]["signal_source"], "unknown")
        self.assertEqual(script["approval"], "editorial_draft_not_reviewed")
        self.assertFalse(script["human_reviewed"])
        self.assertFalse(script["spoken_duration_verified"])
        self.assertFalse(script["rendered"])

    def test_stable_digest_and_no_shared_mutable_objects(self):
        a, b = episode_two_script(), episode_two_script()
        self.assertEqual(a, b)
        digest = a.pop("sha256")
        raw = json.dumps(a, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(hashlib.sha256(raw.encode("utf-8")).hexdigest(), digest)
        b["scenes"][0]["dialogue"][0]["text"] = "edited"
        b["carried_forward"]["signal_source"] = "invented"
        self.assertNotEqual(episode_two_script()["scenes"][0]["dialogue"][0]["text"], "edited")
        self.assertEqual(episode_two_script()["carried_forward"]["signal_source"], "unknown")

    def test_fail_closed_on_provenance_timing_spoilers_and_claims(self):
        mutations = {
            "wrong_pilot": lambda x: x.update(previous_episode_sha256="0" * 64),
            "wrong_outline": lambda x: x.update(source_outline_sha256="0" * 64),
            "false_review": lambda x: x.update(human_reviewed=True),
            "false_audio": lambda x: x.update(spoken_duration_verified=True),
            "false_render": lambda x: x.update(rendered=True),
            "false_approval": lambda x: x.update(approval="approved"),
            "future_reveal": lambda x: x.update(known_revelations=["future"]),
            "invent_source": lambda x: x["carried_forward"].update(signal_source="known"),
            "missing_scene": lambda x: x["scenes"].pop(),
            "wrong_scene_number": lambda x: x["scenes"][1].update(number=1),
            "wrong_timing": lambda x: x["scenes"][1].update(start_second=999),
            "wrong_total": lambda x: x.update(planned_seconds=1700),
            "thin_scene": lambda x: x["scenes"][0].update(dialogue=[]),
            "bad_speaker": lambda x: x["scenes"][0]["dialogue"][0].update(speaker="unknown"),
            "short_line": lambda x: x["scenes"][0]["dialogue"][0].update(text="No"),
            "spoiler": lambda x: x["scenes"][0]["dialogue"][0].update(
                text="Ab energy diversion ka pattern humein yaqeenan mil gaya hai, sab ko bata do."),
            "tampered_digest": lambda x: x["scenes"][0]["dialogue"][0].update(
                text="Yeh ek lambi magar tampered line hai jis ka hash bilkul alag niklay ga."),
        }
        for name, change in mutations.items():
            script = copy.deepcopy(episode_two_script())
            change(script)
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_episode_two(script)

    def test_no_external_urls_or_unauthorized_actions(self):
        script = episode_two_script()
        text = json.dumps(script["scenes"], ensure_ascii=False).lower()
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)
        self.assertNotIn("founder-built guardian", text)
        self.assertEqual({turn["speaker"] for scene in script["scenes"] for turn in scene["dialogue"]},
                         {"laila", "rayan", "meher", "aman", "zoya"})


if __name__ == "__main__":
    unittest.main()
