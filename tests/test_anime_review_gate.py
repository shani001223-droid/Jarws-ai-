"""Fail-closed private human QC; hashes and review never authorize publication."""
from __future__ import annotations

import copy
from array import array
import hashlib
import math
import wave
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

from PIL import Image

from cloud_backend.anime_review_gate import AnimeReviewGateError, record_private_review
from cloud_backend.anime_visual_review import _verify_review_media


def sha(data):
    return hashlib.sha256(data).hexdigest()


class PrivateReviewGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Real, local H.264/AAC media is necessary: the review gate must not
        # accept an arbitrary byte string merely because its manifest hashes match.
        cls.media_dir = tempfile.TemporaryDirectory(prefix="hoshi-qc-test-")
        cls.addClassCleanup(cls.media_dir.cleanup)
        target = Path(cls.media_dir.name) / "real_private_draft.mp4"
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
             "-f", "lavfi", "-i", "color=c=navy:s=480x270:r=12:d=30",
             "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000:duration=30",
             "-t", "30", "-c:v", "libx264", "-preset", "ultrafast",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "32k",
             "-shortest", "-y", str(target)],
            capture_output=True, timeout=60, check=False)
        if result.returncode:
            raise AssertionError(f"Local real-media fixture failed: {result.stderr[:400]!r}")
        cls.encoded_video = target.read_bytes()

    def setUp(self):
        self.video = self.encoded_video
        self.captions = ["سلام", "नमस्ते", "Phir milenge"]
        self.srt = ("1\n00:00:00,000 --> 00:00:10,000\nسلام\n\n"
                    "2\n00:00:10,000 --> 00:00:20,000\nनमस्ते\n\n"
                    "3\n00:00:20,000 --> 00:00:30,000\nPhir milenge\n\n").encode("utf-8")
        out = BytesIO()
        Image.new("RGB", (1440, 592), "navy").save(out, "PNG")
        self.sheet = out.getvalue()
        samples = []
        evidence = []
        for i in range(3):
            for offset, kind in ((12, "active"), (24, "quiet")):
                samples.append({"shot_id": f"shot{i}", "frame_index": i * 120 + offset,
                                "sample_kind": kind,
                                "expected_sprite_visible": kind == "active",
                                "decoded_frame_rgb_sha256": "a" * 64})
            evidence.append({"shot_id": f"shot{i}",
                             "status": "sampled_pair_pixel_delta_not_alignment_proof",
                             "roi_change_detected": True})
        self.manifest = {
            "stage": "private_storyboard_animatic_only", "actual_mp4_rendered": True,
            "owner_approved": False, "published": False, "uploaded": False,
            "video_sha256": sha(self.video), "subtitles_sha256": sha(self.srt),
            "mouth_visual_review": {
                "source_video_sha256": sha(self.video), "png_sha256": sha(self.sheet),
                "owner_approved": False, "visual_alignment_verified": False,
                "manual_review_required": True,
                "media_qc": {"status": "independently_probed_media_not_visual_approval",
                             "codec": "h264", "audio_codec": "aac",
                             "decoded_video_frames": 360, "width": 480, "height": 270,
                             "frame_rate": 12, "duration_seconds": 30.0},
                "samples": samples, "decoded_frame_pair_pixel_evidence": evidence,
            },
        }
        # Real renderer manifests carry a canonical storyboard digest; SRT
        # bytes must match its captions, not merely a caller-edited SHA.
        storyboard = {"schema_version": 1, "language": "ur",
                      "shots": [{"shot_id": f"shot{i}", "caption": caption}
                                for i, caption in enumerate(self.captions)]}
        self.manifest["storyboard_handoff"] = {
            "plan": storyboard, "plan_sha256": sha(json.dumps(
                storyboard, ensure_ascii=False, sort_keys=True,
                separators=(",", ":")).encode("utf-8"))}
        self.manifest["subtitle_timing_source"] = "fixed_ten_second_shots"
        self.notes = ["Checked original mouth placement visually"] * 3

    def record(self, **overrides):
        data = dict(manifest=self.manifest, video=self.video, subtitles=self.srt,
                    sheet=self.sheet, verdict="private_qc_pass",
                    shot_notes=self.notes, inspected=True)
        data.update(overrides)
        return record_private_review(**data)

    def test_explicit_private_review_never_authorizes_release(self):
        result = self.record()
        self.assertEqual(result["verdict"], "private_qc_pass")
        self.assertEqual(len(result["shot_notes"]), 3)
        self.assertEqual(result["source_video_sha256"], sha(self.video))
        self.assertFalse(result["owner_approved"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["publication_permitted"])
        self.assertFalse(result["lip_sync_independently_verified"])
        self.assertFalse(result["physical_phone_qa_verified"])
        self.assertEqual(self.record(verdict="needs_revision")["verdict"], "needs_revision")

    def test_music_backing_cannot_be_mistaken_for_verified_dialogue(self):
        # A continuous music track passes energy/occupancy checks, but is
        # not independent evidence of any Urdu/Hindi words being spoken.
        manifest = copy.deepcopy(self.manifest)
        manifest["source_music_sha256"] = "b" * 64
        with self.assertRaisesRegex(AnimeReviewGateError, "Music-backed audio"):
            self.record(manifest=manifest)
        review = self.record(manifest=manifest, verdict="needs_revision")
        self.assertEqual(review["verdict"], "needs_revision")
        self.assertFalse(review["publication_permitted"])

    def test_encoded_caption_energy_is_measured_not_speech_verified(self):
        result = self.record()
        qc = result["encoded_audio_subtitle_qc"]
        self.assertEqual(qc["status"], "encoded_audio_energy_measured_not_speech_recognition")
        self.assertEqual(len(qc["caption_windows"]), 3)
        self.assertTrue(qc["all_caption_windows_have_audio_energy"])
        self.assertTrue(qc["all_caption_windows_have_sustained_audio"])
        self.assertTrue(all(w["sustained_audio_detected"] for w in qc["caption_windows"]))
        self.assertFalse(qc["spoken_words_independently_verified"])
        self.assertFalse(qc["speech_language_independently_verified"])
        self.assertTrue(qc["music_or_noise_can_trigger"])
        self.assertTrue(qc["all_caption_windows_clear_of_possible_hard_clipping"])
        self.assertTrue(qc["hard_clipping_detection_is_conservative_not_proof"])
        self.assertTrue(all(not w["possible_hard_clipping_detected"]
                            for w in qc["caption_windows"]))

    def test_heavily_saturated_encoded_aac_requires_private_revision(self):
        # A full-scale square wave survives real AAC encoding with long
        # near-rail plateaus. It has ample sustained energy but is unsuitable
        # to approve as a clean dialogue mix. This does NOT recognize speech.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wav_path = root / "hard_limited.wav"
            video_path = root / "hard_limited.mp4"
            pcm = array("h", [
                32767 if math.sin(2 * math.pi * 440 * i / 16000) >= 0 else -32768
                for i in range(30 * 16000)])
            with wave.open(str(wav_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(pcm.tobytes())
            process = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-i", str(Path(self.media_dir.name) / "real_private_draft.mp4"),
                 "-i", str(wav_path), "-map", "0:v:0", "-map", "1:a:0",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "32k",
                 "-t", "30", "-y", str(video_path)],
                capture_output=True, timeout=30, check=False)
            self.assertEqual(process.returncode, 0, process.stderr[:300])
            encoded_video = video_path.read_bytes()
            media_qc = _verify_review_media(video_path, shutil.which("ffprobe"))
        manifest = copy.deepcopy(self.manifest)
        manifest["video_sha256"] = sha(encoded_video)
        manifest["mouth_visual_review"]["source_video_sha256"] = sha(encoded_video)
        manifest["mouth_visual_review"]["media_qc"] = media_qc
        with self.assertRaisesRegex(AnimeReviewGateError, "Possible hard-clipped AAC"):
            self.record(manifest=manifest, video=encoded_video)
        review = self.record(manifest=manifest, video=encoded_video,
                             verdict="needs_revision")
        audio = review["encoded_audio_subtitle_qc"]
        self.assertTrue(audio["all_caption_windows_have_sustained_audio"])
        self.assertFalse(audio["all_caption_windows_clear_of_possible_hard_clipping"])
        for window in audio["caption_windows"]:
            self.assertTrue(window["possible_hard_clipping_detected"])
            self.assertGreater(window["near_full_scale_sample_fraction"], 0.10)
            self.assertGreater(window["decoded_rms"], 0.75)
        self.assertFalse(review["publication_permitted"])

    def test_brief_encoded_beeps_cannot_pass_as_sustained_caption_audio(self):
        # Three 80 ms tones raise each 10-second RMS well above the old
        # energy-only threshold. They are not credible sustained dialogue.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wav_path = root / "brief_beeps.wav"
            sparse_path = root / "sparse.mp4"
            pcm = array("h", [0]) * (30 * 16000)
            for second in (1, 11, 21):
                for i in range(1280):
                    pcm[second * 16000 + i] = int(
                        11000 * math.sin(2 * math.pi * 440 * i / 16000))
            with wave.open(str(wav_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(pcm.tobytes())
            process = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-i", str(Path(self.media_dir.name) / "real_private_draft.mp4"),
                 "-i", str(wav_path), "-map", "0:v:0", "-map", "1:a:0",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "32k",
                 "-t", "30", "-y", str(sparse_path)],
                capture_output=True, timeout=30, check=False)
            self.assertEqual(process.returncode, 0, process.stderr[:300])
            sparse_video = sparse_path.read_bytes()
            sparse_media_qc = _verify_review_media(
                sparse_path, shutil.which("ffprobe"))
        manifest = copy.deepcopy(self.manifest)
        manifest["video_sha256"] = sha(sparse_video)
        manifest["mouth_visual_review"]["source_video_sha256"] = sha(sparse_video)
        manifest["mouth_visual_review"]["media_qc"] = sparse_media_qc
        with self.assertRaisesRegex(AnimeReviewGateError, "insufficient sustained audio"):
            self.record(manifest=manifest, video=sparse_video)
        result = self.record(manifest=manifest, video=sparse_video,
                             verdict="needs_revision")
        qc = result["encoded_audio_subtitle_qc"]
        self.assertTrue(qc["all_caption_windows_have_audio_energy"])
        self.assertFalse(qc["all_caption_windows_have_sustained_audio"])
        self.assertTrue(all(not w["sustained_audio_detected"]
                            for w in qc["caption_windows"]))
        self.assertFalse(result["publication_permitted"])

    def test_repeated_encoded_beeps_cannot_pass_as_dialogue_like_audio(self):
        # Fifteen separated 80ms tones per caption exceed the 5% occupancy
        # floor, but none lasts 150ms. Energy and occupancy alone must not
        # manufacture a private pass. This is not actual speech recognition.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wav_path = root / "repeated_beeps.wav"
            video_path = root / "repeated_beeps.mp4"
            pcm = array("h", [0]) * (30 * 16000)
            for shot in range(3):
                for pulse in range(15):
                    start = int((shot * 10 + 0.5 + pulse * 0.6) * 16000)
                    for i in range(1280):
                        pcm[start + i] = int(
                            11000 * math.sin(2 * math.pi * 440 * i / 16000))
            with wave.open(str(wav_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(pcm.tobytes())
            process = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-i", str(Path(self.media_dir.name) / "real_private_draft.mp4"),
                 "-i", str(wav_path), "-map", "0:v:0", "-map", "1:a:0",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "32k",
                 "-t", "30", "-y", str(video_path)],
                capture_output=True, timeout=30, check=False)
            self.assertEqual(process.returncode, 0, process.stderr[:300])
            video = video_path.read_bytes()
            qc_media = _verify_review_media(video_path, shutil.which("ffprobe"))
        manifest = copy.deepcopy(self.manifest)
        manifest["video_sha256"] = sha(video)
        manifest["mouth_visual_review"]["source_video_sha256"] = sha(video)
        manifest["mouth_visual_review"]["media_qc"] = qc_media
        with self.assertRaisesRegex(AnimeReviewGateError, "insufficient sustained audio"):
            self.record(manifest=manifest, video=video)
        review = self.record(manifest=manifest, video=video, verdict="needs_revision")
        audio = review["encoded_audio_subtitle_qc"]
        self.assertFalse(audio["all_caption_windows_have_sustained_audio"])
        self.assertEqual(audio["minimum_longest_contiguous_active_audio_ms"], 150)
        for window in audio["caption_windows"]:
            self.assertGreater(window["active_audio_frame_fraction"], 0.05)
            self.assertLess(window["longest_contiguous_active_audio_ms"], 150)
            self.assertTrue(window["audible_energy_detected"])
            self.assertFalse(window["sustained_audio_detected"])

    def test_silent_encoded_audio_blocks_private_pass_but_allows_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            silent_path = Path(directory) / "silent.mp4"
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-i", str(Path(self.media_dir.name) / "real_private_draft.mp4"),
                 "-af", "volume=0", "-c:v", "copy", "-c:a", "aac",
                 "-b:a", "32k", "-y", str(silent_path)],
                capture_output=True, timeout=30, check=False)
            self.assertEqual(result.returncode, 0, result.stderr[:300])
            silent_video = silent_path.read_bytes()
            silent_media_qc = _verify_review_media(silent_path, shutil.which("ffprobe"))
        manifest = copy.deepcopy(self.manifest)
        manifest["video_sha256"] = sha(silent_video)
        manifest["mouth_visual_review"]["source_video_sha256"] = sha(silent_video)
        manifest["mouth_visual_review"]["media_qc"] = silent_media_qc
        with self.assertRaisesRegex(AnimeReviewGateError, "Silent caption interval"):
            self.record(manifest=manifest, video=silent_video)
        result = self.record(manifest=manifest, video=silent_video,
                             verdict="needs_revision")
        self.assertFalse(result["encoded_audio_subtitle_qc"][
            "all_caption_windows_have_audio_energy"])
        self.assertFalse(result["publication_permitted"])

    def test_rejects_uninspected_or_unbounded_review(self):
        for overrides in (dict(inspected=False), dict(inspected=1),
                          dict(verdict="publish"), dict(shot_notes=["short"] * 3),
                          dict(shot_notes=["ok"] * 3),
                          dict(shot_notes=["x" * 501] * 3),
                          dict(shot_notes=["note one", "note two"])):
            with self.subTest(overrides=overrides), self.assertRaises(AnimeReviewGateError):
                self.record(**overrides)

    def test_rejects_hash_tamper_and_false_owner_approval(self):
        for key, value in (("video_sha256", "0" * 64),
                           ("subtitles_sha256", "0" * 64),
                           ("owner_approved", True), ("published", True)):
            bad = copy.deepcopy(self.manifest)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(AnimeReviewGateError):
                self.record(manifest=bad)
        for key, value in (("png_sha256", "0" * 64),
                           ("source_video_sha256", "0" * 64),
                           ("visual_alignment_verified", True)):
            bad = copy.deepcopy(self.manifest)
            bad["mouth_visual_review"][key] = value
            with self.subTest(key=key), self.assertRaises(AnimeReviewGateError):
                self.record(manifest=bad)
        with self.assertRaises(AnimeReviewGateError):
            self.record(video=self.video + b"tampered")
        with self.assertRaises(AnimeReviewGateError):
            self.record(sheet=b"invalid PNG")

    def test_rejects_fake_mp4_even_with_matching_sha_and_claimed_qc(self):
        fake = b"this is not encoded MP4 data" * 30
        forged = copy.deepcopy(self.manifest)
        forged["video_sha256"] = sha(fake)
        forged["mouth_visual_review"]["source_video_sha256"] = sha(fake)
        with self.assertRaisesRegex(AnimeReviewGateError, "independent media verification"):
            self.record(manifest=forged, video=fake)

    def test_rejects_manifest_media_qc_spoof(self):
        forged = copy.deepcopy(self.manifest)
        forged["mouth_visual_review"]["media_qc"]["duration_seconds"] = 29.999
        with self.assertRaisesRegex(AnimeReviewGateError, "metadata differs"):
            self.record(manifest=forged)

    def test_comparison_gaps_are_explicit_and_missing_movement_blocks_pass(self):
        bad = copy.deepcopy(self.manifest)
        bad["mouth_visual_review"]["decoded_frame_pair_pixel_evidence"][0]["roi_change_detected"] = False
        with self.assertRaises(AnimeReviewGateError):
            self.record(manifest=bad)
        self.assertEqual(self.record(manifest=bad, verdict="needs_revision")["verdict"],
                         "needs_revision")
        bad = copy.deepcopy(self.manifest)
        bad["mouth_visual_review"]["samples"][0]["sample_kind"] = "no_activity"
        bad["mouth_visual_review"]["samples"][0]["expected_sprite_visible"] = False
        bad["mouth_visual_review"]["decoded_frame_pair_pixel_evidence"][0]["status"] = (
            "not_comparable_no_active_and_quiet_encoded_frames")
        self.assertEqual(self.record(manifest=bad)["verdict"], "private_qc_pass")
        bad["mouth_visual_review"]["decoded_frame_pair_pixel_evidence"][0]["status"] = (
            "sampled_pair_pixel_delta_not_alignment_proof")
        with self.assertRaises(AnimeReviewGateError):
            self.record(manifest=bad)

    def test_subtitle_integrity_rejects_rehashed_forgery_and_bad_timing(self):
        # An attacker can edit both the SRT and its manifest hashes; that is
        # still not proof the captions match the bound source storyboard.
        bad_variants = [
            self.srt.replace("سلام".encode("utf-8"), b"forged"),
            self.srt.replace(b"00:00:10,000", b"00:00:09,000"),
            self.srt.replace(b"00:00:30,000", b"00:00:31,000"),
            self.srt.replace(b"3\n", b"4\n"),
            self.srt + b"4\n00:00:30,000 --> 00:00:31,000\nextra\n\n",
            b"\\xff" + self.srt,
        ]
        for srt in bad_variants:
            with self.subTest(srt=srt[:60]):
                manifest = copy.deepcopy(self.manifest)
                manifest["subtitles_sha256"] = sha(srt)
                with self.assertRaisesRegex(AnimeReviewGateError, "SRT"):
                    self.record(manifest=manifest, subtitles=srt)
        forged = copy.deepcopy(self.manifest)
        forged["storyboard_handoff"]["plan"]["shots"][0]["caption"] = "forged"
        with self.assertRaisesRegex(AnimeReviewGateError, "SRT"):
            self.record(manifest=forged)

    def test_operator_cue_srt_is_exactly_bound_to_audio_and_storyboard(self):
        manifest = copy.deepcopy(self.manifest)
        cues = [{"shot_id": f"shot{i}", "speaker_id": "actor",
                 "start_ms": i * 10000 + 1000,
                 "end_ms": i * 10000 + 9000, "text": caption}
                for i, caption in enumerate(self.captions)]
        plan = {"schema_version": 1, "language": "ur",
                "audio_sha256": "a" * 64,
                "storyboard_sha256": manifest["storyboard_handoff"]["plan_sha256"],
                "cues": cues}
        manifest["source_audio_sha256"] = "a" * 64
        manifest["voice_timing_handoff"] = {
            "plan": plan, "plan_sha256": sha(json.dumps(
                plan, ensure_ascii=False, sort_keys=True,
                separators=(",", ":")).encode("utf-8"))}
        manifest["subtitle_timing_source"] = "operator_supplied_voice_cues_not_audio_verified"
        srt = ("1\n00:00:01,000 --> 00:00:09,000\nسلام\n\n"
               "2\n00:00:11,000 --> 00:00:19,000\nनमस्ते\n\n"
               "3\n00:00:21,000 --> 00:00:29,000\nPhir milenge\n\n").encode("utf-8")
        manifest["subtitles_sha256"] = sha(srt)
        record = self.record(manifest=manifest, subtitles=srt)
        self.assertEqual(record["subtitle_qc"]["subtitle_blocks"], 3)
        self.assertFalse(record["subtitle_qc"]["spoken_words_independently_verified"])
        for mutation in ("audio_sha256", "storyboard_sha256", "plan_sha256"):
            forged = copy.deepcopy(manifest)
            if mutation == "plan_sha256":
                forged["voice_timing_handoff"]["plan_sha256"] = "0" * 64
            else:
                forged["voice_timing_handoff"]["plan"][mutation] = "0" * 64
            with self.subTest(mutation=mutation), self.assertRaisesRegex(
                    AnimeReviewGateError, "SRT"):
                self.record(manifest=forged, subtitles=srt)

    def test_cli_writes_only_create_only_private_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")
            (root / "hoshi_anime_animatic_DRAFT.mp4").write_bytes(self.video)
            (root / "hoshi_anime_animatic_DRAFT.srt").write_bytes(self.srt)
            (root / "hoshi_mouth_review_DRAFT.png").write_bytes(self.sheet)
            cmd = [sys.executable, "-m", "scripts.review_hoshi_anime_pilot",
                   "--draft-dir", str(root), "--verdict", "needs_revision",
                   "--inspected-video-and-sheet"]
            for note in self.notes:
                cmd += ["--shot-note", note]
            env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
            first = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(first.returncode, 0, first.stderr)
            record = root / "hoshi_private_qc_review.json"
            original = record.read_bytes()
            self.assertFalse(json.loads(original)["publication_permitted"])
            second = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(record.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
