"""Fail-closed original storyboard handoff and real renderer integration tests."""
from __future__ import annotations

import copy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

from cloud_backend.anime_storyboard_handoff import (
    StoryboardHandoffError, bind_storyboard_handoff,
)
from cloud_backend.anime_pilot_animatic import AnimePilotError, render_private_animatic


CAPTIONS = ("یہ ایک نیا سفر ہے۔", "आज कहानी शुरू होती है।", "Kal milenge.")
MOVES = ("push_in", "pan_left", "static")


def originals():
    output = []
    for i in range(3):
        picture = Image.new("RGB", (640, 360), (20 + 20 * i, 30, 70))
        painter = ImageDraw.Draw(picture)
        painter.rectangle((120, 60, 530, 300), fill=(60 + 30 * i, 90, 150))
        painter.ellipse((240, 90, 400, 250), fill=(180, 140, 120))
        buffer = BytesIO()
        picture.save(buffer, "PNG")
        output.append(buffer.getvalue())
    return output


def plan_for(stills):
    return {
        "schema_version": 1,
        "project_id": "OriginalFantasyPilot",
        "language": "ur",
        "characters": [
            {"id": "hero", "design_sha256": hashlib.sha256(b"original-design-sheet").hexdigest(),
             "rights_attested": True},
        ],
        "shots": [
            {"shot_id": f"scene_{i+1}", "still_sha256": hashlib.sha256(still).hexdigest(),
             "caption": CAPTIONS[i], "camera_move": MOVES[i],
             "character_ids": ["hero"]} for i, still in enumerate(stills)
        ],
    }


class StoryboardHandoffTests(unittest.TestCase):
    def setUp(self):
        self.stills = originals()
        self.plan = plan_for(self.stills)

    def test_exact_media_binding_and_stable_canonical_digest(self):
        result = bind_storyboard_handoff(self.plan, self.stills, CAPTIONS, MOVES)
        self.assertEqual(result["plan"]["language"], "ur")
        self.assertEqual(result["shot_duration_seconds"], 10)
        self.assertFalse(result["owner_approved"])
        self.assertFalse(result["rights_independently_verified"])
        self.assertEqual(result["character_design_consistency"],
                         "reference_ids_only_visuals_not_verified")
        self.assertEqual(result["plan_sha256"],
                         bind_storyboard_handoff(copy.deepcopy(self.plan),
                                                 list(self.stills), list(CAPTIONS),
                                                 list(MOVES))["plan_sha256"])
        self.assertEqual(len(result["plan_sha256"]), 64)

    def test_fail_closed_on_tampering_and_unknown_character(self):
        for mutate in (
            lambda p: p["shots"][0].update({"still_sha256": "0" * 64}),
            lambda p: p["shots"][1].update({"caption": "Different line"}),
            lambda p: p["shots"][0].update({"camera_move": "static"}),
            lambda p: p["shots"][2].update({"character_ids": ["unknown"]}),
            lambda p: p["shots"][0].update({"shot_id": "scene_2"}),
            lambda p: p["characters"][0].update({"rights_attested": False}),
            lambda p: p["characters"][0].update({"design_sha256": "invalid"}),
            lambda p: p.update({"schema_version": True}),
            lambda p: p.update({"language": "en"}),
            lambda p: p.update({"secret": "not allowed"}),
            lambda p: p["shots"][0].update({"character_ids": ["hero", "hero"]}),
        ):
            changed = copy.deepcopy(self.plan)
            mutate(changed)
            with self.subTest(changed=changed), self.assertRaises(StoryboardHandoffError):
                bind_storyboard_handoff(changed, self.stills, CAPTIONS, MOVES)
        with self.assertRaises(StoryboardHandoffError):
            bind_storyboard_handoff(self.plan, self.stills[::-1], CAPTIONS, MOVES)
        with self.assertRaises(StoryboardHandoffError):
            bind_storyboard_handoff(self.plan, self.stills, CAPTIONS[::-1], MOVES)
        with self.assertRaises(StoryboardHandoffError):
            bind_storyboard_handoff(self.plan, self.stills, CAPTIONS, MOVES[::-1])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real storyboard MP4 requires local FFmpeg")
    def test_real_private_mp4_manifest_binds_storyboard_and_remains_draft(self):
        result = render_private_animatic(
            self.stills, CAPTIONS, image_rights_attested=True,
            camera_moves=MOVES, storyboard_handoff=self.plan)
        self.assertEqual(result["storyboard_handoff"]["plan_sha256"],
                         bind_storyboard_handoff(self.plan, self.stills,
                                                 CAPTIONS, MOVES)["plan_sha256"])
        self.assertEqual(result["source_image_sha256"],
                         [s["still_sha256"] for s in self.plan["shots"]])
        self.assertEqual(result["camera_moves"], list(MOVES))
        self.assertTrue(result["actual_mp4_rendered"])
        self.assertFalse(result["full_character_animation"])
        self.assertFalse(result["owner_approved"])
        self.assertFalse(result["published"])

    def test_bad_storyboard_rejected_before_encoder(self):
        broken = copy.deepcopy(self.plan)
        broken["shots"][0]["still_sha256"] = "0" * 64
        with self.assertRaises(AnimePilotError):
            render_private_animatic(self.stills, CAPTIONS, image_rights_attested=True,
                                    camera_moves=MOVES, storyboard_handoff=broken)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "CLI storyboard integration requires local FFmpeg")
    def test_operator_cli_handoff_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = []
            for i, still in enumerate(self.stills):
                path = root / f"original{i}.png"
                path.write_bytes(still)
                paths.append(path)
            plan_path = root / "storyboard.json"
            plan_path.write_text(json.dumps(self.plan, ensure_ascii=False), encoding="utf-8")
            out = root / "private-draft"
            command = [sys.executable, "-m", "scripts.render_hoshi_anime_animatic"]
            for path in paths:
                command.extend(["--shot", str(path)])
            for caption in CAPTIONS:
                command.extend(["--caption", caption])
            for move in MOVES:
                command.extend(["--camera-move", move])
            command.extend(["--image-rights-attested", "--storyboard-json",
                            str(plan_path), "--out", str(out)])
            first = subprocess.run(command, capture_output=True, text=True, timeout=110)
            self.assertEqual(first.returncode, 0, first.stderr)
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["storyboard_handoff"]["plan_sha256"],
                             bind_storyboard_handoff(self.plan, self.stills,
                                                     CAPTIONS, MOVES)["plan_sha256"])
            self.assertFalse(manifest["owner_approved"])
            movie = (out / manifest["filename"]).read_bytes()
            self.assertEqual(hashlib.sha256(movie).hexdigest(), manifest["video_sha256"])
            second = subprocess.run(command, capture_output=True, text=True, timeout=110)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual((out / manifest["filename"]).read_bytes(), movie)


if __name__ == "__main__":
    unittest.main()
