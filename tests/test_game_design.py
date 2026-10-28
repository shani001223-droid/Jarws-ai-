"""Task 49: validate a real scoped design, not a claimed playable game."""
import unittest
from pathlib import Path
from cloud_backend.game_design import LEVELS, design_manifest, solve_level


class GameDesignTests(unittest.TestCase):
    def test_six_unique_bounded_solvable_levels(self):
        manifest = design_manifest()
        self.assertEqual(len(manifest["levels"]), 6)
        self.assertEqual(len(set(LEVELS)), 6)
        self.assertEqual([x["id"] for x in manifest["levels"]], list(range(1, 7)))
        for level in manifest["levels"]:
            self.assertEqual(len(level["rows"]), 7)
            self.assertLessEqual(level["minimum_moves"], 30)
            self.assertGreaterEqual(level["stars"], 1)
            self.assertLessEqual(level["stars"], 3)
            self.assertEqual(level["minimum_moves"], solve_level(tuple(level["rows"])))

    def test_rejects_unreachable_or_malformed_layouts(self):
        good = list(LEVELS[0])
        cases = [
            (".......", *good[1:]),
            ("#######", "#SXX.E#", *good[2:]),
            ("#######", "#S###E#", "#######", "###C###", "#######", "#######", "#######"),
            ("#######", "#S...E#", "#.....#", "#.....#", "#.....#", "#.....#", "#######"),
            ("#######", "#SS..E#", *good[2:]),
            tuple(good[:-1]),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                solve_level(case)

    def test_no_execution_or_approval_claim(self):
        manifest = design_manifest()
        self.assertEqual(manifest, design_manifest())
        self.assertEqual(len(manifest["sha256"]), 64)
        self.assertFalse(manifest["real_build_created"])
        self.assertFalse(manifest["network_required"])
        self.assertFalse(manifest["accounts_required"])
        self.assertFalse(manifest["paid_assets_required"])
        self.assertEqual(manifest["approval"], "proposed_not_owner_approved")

    def test_gdd_exists_and_describes_real_acceptance(self):
        text = (Path(__file__).resolve().parents[1] / "HOSHI_GAME_DESIGN.md").read_text(encoding="utf-8")
        for phrase in ("PROPOSED DESIGN ONLY", "Realme Note 50", "Roman Urdu",
                       "Task 50", "Task 51", "Task 52", "Task 53", "Task 54",
                       "breadth-first search", "not a playable game"):
            self.assertIn(phrase, text)
        for level in LEVELS:
            self.assertIn("\n".join(level), text)


if __name__ == "__main__":
    unittest.main()
