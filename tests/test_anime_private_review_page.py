"""Private HTML review handoff: no scripts, uploads or forged acceptance."""
from __future__ import annotations

import copy
import hashlib
import unittest

from cloud_backend.anime_private_review_page import (
    AnimePrivateReviewPageError, build_private_review_page,
)


def digest(text: bytes) -> str:
    return hashlib.sha256(text).hexdigest()


class PrivateReviewPageTests(unittest.TestCase):
    def setUp(self):
        self.windows = [
            (2000, 4000, "سلام"),
            (12000, 14000, "नमस्ते"),
            (22000, 24000, "Phir milenge"),
        ]
        self.result = {
            "filename": "hoshi_anime_subtitled_PRIVATE_DRAFT.mp4",
            "visual_evidence_filename": "hoshi_subtitle_encoded_comparison_PRIVATE.png",
            "status": "actual_shaped_srt_burned_into_private_mp4_unapproved",
            "owner_approved": False, "release_authorized": False,
            "publication_permitted": False,
            "spoken_words_independently_verified": False,
            "audio_sync_independently_verified": False,
            "human_readability_review_required": True,
            "subtitles_embedded_in_video": True,
            "video_sha256": digest(b"video"),
            "visual_evidence_sha256": digest(b"comparison"),
            "cue_windows_ms": [[start, end] for start, end, _ in self.windows],
            "media_qc": {"audio_codec": "aac"},
            "audio_review_decoded_from_actual_encoded_aac": True,
            "audio_waveform_filename": "hoshi_encoded_aac_waveform_PRIVATE.png",
            "audio_waveform_sha256": digest(b"waveform"),
            "audio_waveform_status": "actual_encoded_aac_waveform_human_review_only",
            "audio_review_samples": [
                {"filename": f"hoshi_cue_{i+1}_PRIVATE_REVIEW.wav",
                 "shot_index": i+1, "cue_start_ms": start,
                 "cue_end_ms": end, "wav_sha256": digest(str(i).encode()),
                 "decoded_from_actual_captioned_mp4_aac": True,
                 "spoken_words_independently_verified": False,
                 "phoneme_sync_verified": False}
                for i, (start, end, _) in enumerate(self.windows)
            ],
        }

    def test_real_local_media_links_csp_and_unapproved_language(self):
        html = build_private_review_page(self.result, self.windows).decode("utf-8")
        self.assertIn('script-src &#39;none&#39;', html.replace("'", "&#39;"))
        self.assertIn('src="hoshi_anime_subtitled_PRIVATE_DRAFT.mp4"', html)
        self.assertIn('src="hoshi_encoded_aac_waveform_PRIVATE.png"', html)
        self.assertIn('src="hoshi_cue_1_PRIVATE_REVIEW.wav"', html)
        self.assertIn("नमस्ते", html)
        self.assertIn("سلام", html)
        self.assertIn("UNAPPROVED / DO NOT PUBLISH", html)
        self.assertIn(self.result["video_sha256"], html)
        self.assertNotIn("<script", html)
        self.assertNotIn("<form", html)
        self.assertEqual(build_private_review_page(self.result, self.windows),
                         build_private_review_page(self.result, self.windows))

    def test_caption_is_escaped_not_executable(self):
        windows = list(self.windows)
        windows[1] = (12000, 14000, '<script>alert("x")</script>')
        result = copy.deepcopy(self.result)
        result["cue_windows_ms"] = [[a, b] for a, b, _ in windows]
        html = build_private_review_page(result, windows).decode("utf-8")
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_silent_source_never_claims_audio(self):
        result = copy.deepcopy(self.result)
        result.update({
            "media_qc": {"audio_codec": "none"},
            "audio_review_samples": [],
            "audio_review_decoded_from_actual_encoded_aac": False,
            "audio_waveform_filename": None,
            "audio_waveform_sha256": None,
            "audio_waveform_status": "no_encoded_aac_no_waveform",
        })
        html = build_private_review_page(result, self.windows).decode("utf-8")
        self.assertIn("No AAC soundtrack", html)
        self.assertNotIn("<audio", html)
        self.assertNotIn("hoshi_encoded_aac_waveform_PRIVATE.png", html)

    def test_tampered_rights_timestamps_hashes_and_local_paths_rejected(self):
        for key, value in (
            ("owner_approved", True),
            ("release_authorized", True),
            ("publication_permitted", True),
            ("spoken_words_independently_verified", True),
            ("filename", "https://evil.example/upload"),
            ("visual_evidence_filename", "../image.png"),
            ("video_sha256", "not-a-hash"),
            ("audio_waveform_sha256", "a" * 65),
            ("cue_windows_ms", [[0, 10000]] * 3),
            ("audio_review_decoded_from_actual_encoded_aac", False),
        ):
            with self.subTest(key=key):
                result = copy.deepcopy(self.result)
                result[key] = value
                with self.assertRaises(AnimePrivateReviewPageError):
                    build_private_review_page(result, self.windows)
        result = copy.deepcopy(self.result)
        result["audio_review_samples"][0]["filename"] = "../../wrong.wav"
        with self.assertRaises(AnimePrivateReviewPageError):
            build_private_review_page(result, self.windows)
        result = copy.deepcopy(self.result)
        result["audio_review_samples"][0]["phoneme_sync_verified"] = True
        with self.assertRaises(AnimePrivateReviewPageError):
            build_private_review_page(result, self.windows)
        with self.assertRaises(AnimePrivateReviewPageError):
            build_private_review_page(self.result, [
                (2000, 4000, "okay"), (12000, 14000, "bad\ncue"),
                (22000, 24000, "okay")])
        with self.assertRaises(AnimePrivateReviewPageError):
            build_private_review_page(self.result, [
                (2000, 4000, "okay"), (12000, 14000, "okay"),
                (11000, 24000, "overlap")])


if __name__ == "__main__":
    unittest.main()
