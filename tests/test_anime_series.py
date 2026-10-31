"""Task 55: deterministic continuity, spoiler and false-completion regression."""
import copy
import hashlib
import json
import unittest
from pathlib import Path

from cloud_backend.anime_series import (
    ARCS, BEATS, REVEALS, TARGET_EPISODES, series_manifest, validate_series,
)


class AnimeSeriesTests(unittest.TestCase):
    def test_exact_300_unique_episodes_and_9000_target_minutes(self):
        m = series_manifest()
        self.assertEqual(m["target_episodes"], 300)
        self.assertEqual(m["target_minutes_per_episode"], 30)
        self.assertEqual(m["target_total_minutes"], 9000)
        self.assertEqual(len(m["episodes"]), TARGET_EPISODES)
        self.assertEqual([e["id"] for e in m["episodes"]],
                         [f"EP{i:03d}" for i in range(1, 301)])
        self.assertEqual(len(ARCS), 10)
        self.assertEqual(sum(len(arc[2]) for arc in ARCS), 60)
        self.assertEqual(len(BEATS), 5)
        self.assertEqual(len({(e["event"], e["beat"]) for e in m["episodes"]}), 300)
        self.assertEqual([e["story_day"] for e in m["episodes"]][::2],
                         list(range(1, 151)))
        self.assertEqual(m["episodes"][0]["previous_episode"], None)
        self.assertEqual(m["episodes"][-1]["previous_episode"], 299)
        self.assertTrue(all(e["status"] == "outline_only" for e in m["episodes"]))

    def test_reveal_gates_and_causal_arc_boundaries(self):
        m = series_manifest()
        for episode_number, reveal in REVEALS.items():
            before = m["episodes"][episode_number - 2]
            after = m["episodes"][episode_number - 1]
            self.assertNotIn(reveal, before["revelations_known"])
            self.assertIn(reveal, after["revelations_known"])
        for index in range(30, 300, 30):
            self.assertEqual(m["episodes"][index]["previous_episode"], index)
            self.assertEqual(m["episodes"][index]["arc"], index // 30 + 1)

    def test_stable_hash_and_fresh_no_shared_mutable_state(self):
        a, b = series_manifest(), series_manifest()
        self.assertEqual(a, b)
        self.assertEqual(len(a["sha256"]), 64)
        digest = a.pop("sha256")
        payload = json.dumps(a, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(digest, hashlib.sha256(payload.encode("utf-8")).hexdigest())
        b["episodes"][0]["title"] = "tampered"
        self.assertNotEqual(series_manifest()["episodes"][0]["title"], "tampered")

    def test_rejects_spoiler_and_chronology_drift(self):
        base = series_manifest()
        for change in ("missing", "out_of_order", "wrong_arc", "wrong_day",
                       "wrong_previous", "early_reveal", "fake_render",
                       "fake_approval", "duplicate", "empty_handoff"):
            m = copy.deepcopy(base)
            if change == "missing":
                m["episodes"].pop()
            elif change == "out_of_order":
                m["episodes"][5]["number"] = 8
            elif change == "wrong_arc":
                m["episodes"][0]["arc"] = 3
            elif change == "wrong_day":
                m["episodes"][2]["story_day"] = 42
            elif change == "wrong_previous":
                m["episodes"][10]["previous_episode"] = None
            elif change == "early_reveal":
                m["episodes"][0]["revelations_known"].append(REVEALS[60])
            elif change == "fake_render":
                m["rendered_episodes"] = 1
            elif change == "fake_approval":
                m["approval"] = "approved"
            elif change == "duplicate":
                m["episodes"][1]["event"] = m["episodes"][0]["event"]
                m["episodes"][1]["beat"] = m["episodes"][0]["beat"]
            elif change == "empty_handoff":
                m["episodes"][0]["handoff"] = ""
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_series(m)

    def test_design_does_not_claim_scripts_media_or_owner_signoff(self):
        m = series_manifest()
        self.assertEqual(m["rendered_episodes"], 0)
        self.assertEqual(m["reviewed_scripts"], 0)
        self.assertEqual(m["approval"], "proposed_not_owner_approved")
        self.assertTrue(all("30" not in e["status"] for e in m["episodes"]))
        self.assertFalse(any("password" in str(e).lower() for e in m["episodes"]))

    def test_cli_exports_real_300_entry_json_without_overwrite(self):
        import subprocess
        import sys
        import tempfile
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "chronology.json"
            cmd = [sys.executable, "-m", "scripts.export_hoshi_anime_chronology", "--out", str(out)]
            first = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=12)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["episodes"]), 300)
            self.assertEqual(payload["sha256"], series_manifest()["sha256"])
            before = out.read_bytes()
            second = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=12)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(out.read_bytes(), before)

    def test_series_bible_has_consistency_and_future_task_gates(self):
        doc = (Path(__file__).resolve().parents[1] / "HOSHI_ANIME_SERIES_BIBLE.md").read_text(encoding="utf-8")
        for phrase in ("PROPOSED DESIGN ONLY", "300", "9,000", "Roman Urdu",
                       "Task 56", "Task 57", "Task 58", "Task 59", "Task 60",
                       "Realme Note 50", "not scripts", "not rendered episodes",
                       "Deewar Mein Dafan"):
            self.assertIn(phrase, doc)
        for title, _, _ in ARCS:
            self.assertIn(title, doc)


if __name__ == "__main__":
    unittest.main()
