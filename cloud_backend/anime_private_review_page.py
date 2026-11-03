"""Offline, read-only HTML handoff for the PRIVATE Hoshi subtitle pilot.

No JavaScript, external assets, upload, persistent approval or publishing.
All references are fixed local filenames and all subtitle text is HTML-escaped.
This is a human listening/visual review aid, NOT speech or lip-sync QA.
"""
from __future__ import annotations

from html import escape
import hashlib
import re


class AnimePrivateReviewPageError(ValueError):
    """Unsafe or mismatched private media-review evidence."""


VIDEO = "hoshi_anime_subtitled_PRIVATE_DRAFT.mp4"
VISUAL = "hoshi_subtitle_encoded_comparison_PRIVATE.png"
WAVEFORM = "hoshi_encoded_aac_waveform_PRIVATE.png"
HEX = re.compile(r"[0-9a-f]{64}\Z")


def _digest(value: object) -> str:
    if type(value) is not str or HEX.fullmatch(value) is None:
        raise AnimePrivateReviewPageError("Invalid SHA-256 evidence.")
    return value


def _safe_caption(value: object) -> str:
    if (type(value) is not str or not 1 <= len(value) <= 180
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise AnimePrivateReviewPageError("Invalid private caption.")
    return escape(value, quote=True)


def _milliseconds(value: int) -> str:
    return f"{value // 60000:02d}:{(value // 1000) % 60:02d}.{value % 1000:03d}"


def build_private_review_page(result: dict, windows: list[tuple[int, int, str]]) -> bytes:
    """Create a bounded self-contained *markup* page for existing local evidence.

    Caller has already validated and decoded the actual H.264/AAC and SRT.
    This re-checks file names, digests, cues and non-approval flags before
    linking only the files written in the same create-only output directory.
    """
    if type(result) is not dict or type(windows) is not list or len(windows) != 3:
        raise AnimePrivateReviewPageError("Three validated review cues required.")
    if (result.get("filename") != VIDEO
            or result.get("visual_evidence_filename") != VISUAL
            or result.get("status") != "actual_shaped_srt_burned_into_private_mp4_unapproved"
            or result.get("owner_approved") is not False
            or result.get("release_authorized") is not False
            or result.get("publication_permitted") is not False
            or result.get("spoken_words_independently_verified") is not False
            or result.get("audio_sync_independently_verified") is not False
            or result.get("human_readability_review_required") is not True
            or result.get("subtitles_embedded_in_video") is not True):
        raise AnimePrivateReviewPageError("Unapproved private review evidence required.")
    video_hash = _digest(result.get("video_sha256"))
    visual_hash = _digest(result.get("visual_evidence_sha256"))
    audio_records = result.get("audio_review_samples")
    if type(audio_records) is not list or len(audio_records) not in (0, 3):
        raise AnimePrivateReviewPageError("Invalid AAC review record count.")
    if (bool(audio_records) != (result.get("media_qc", {}).get("audio_codec") == "aac")
            or result.get("audio_review_decoded_from_actual_encoded_aac") is not bool(audio_records)):
        raise AnimePrivateReviewPageError("Encoded AAC review provenance mismatch.")
    if audio_records:
        if (result.get("audio_waveform_filename") != WAVEFORM
                or result.get("audio_waveform_status") !=
                "actual_encoded_aac_waveform_human_review_only"):
            raise AnimePrivateReviewPageError("Missing encoded AAC waveform evidence.")
        waveform_hash = _digest(result.get("audio_waveform_sha256"))
    else:
        if (result.get("audio_waveform_filename") is not None
                or result.get("audio_waveform_sha256") is not None
                or result.get("audio_waveform_status") != "no_encoded_aac_no_waveform"):
            raise AnimePrivateReviewPageError("Silent MP4 cannot claim AAC evidence.")
        waveform_hash = None
    if result.get("cue_windows_ms") != [[start, end] for start, end, _ in windows]:
        raise AnimePrivateReviewPageError("Caption timestamps differ from MP4 provenance.")

    cards = []
    previous_end = 0
    for index, cue in enumerate(windows):
        if (type(cue) is not tuple or len(cue) != 3
                or type(cue[0]) is not int or type(cue[1]) is not int
                or not previous_end <= cue[0] < cue[1] <= 30000):
            raise AnimePrivateReviewPageError("Invalid ordered cue window.")
        start, end, caption = cue
        previous_end = end
        safe = _safe_caption(caption)
        audio = '<p>No encoded AAC audio track: voice cannot be reviewed.</p>'
        if audio_records:
            record = audio_records[index]
            filename = f"hoshi_cue_{index + 1}_PRIVATE_REVIEW.wav"
            if (type(record) is not dict
                    or record.get("filename") != filename
                    or record.get("shot_index") != index + 1
                    or record.get("cue_start_ms") != start
                    or record.get("cue_end_ms") != end
                    or record.get("decoded_from_actual_captioned_mp4_aac") is not True
                    or record.get("spoken_words_independently_verified") is not False
                    or record.get("phoneme_sync_verified") is not False):
                raise AnimePrivateReviewPageError("AAC cue provenance mismatch.")
            audio_hash = _digest(record.get("wav_sha256"))
            audio = (f'<audio controls preload="none" src="{filename}"></audio>'
                     f'<p class="hash">AAC-derived WAV SHA-256: {audio_hash}</p>')
        cards.append(
            f'<section class="cue"><h3>Cue {index + 1} '
            f'({_milliseconds(start)}–{_milliseconds(end)})</h3>'
            f'<p class="caption" dir="auto">{safe}</p>{audio}</section>')
    waveform = (
        f'<h2>Actual encoded-AAC waveform</h2>'
        f'<img src="{WAVEFORM}" alt="Decoded AAC peak waveform and cue markers">'
        f'<p class="hash">Waveform SHA-256: {waveform_hash}</p>'
        if waveform_hash else
        '<p>No AAC soundtrack; do not infer any spoken dialogue.</p>')
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; media-src 'self' file:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; object-src 'none'; script-src 'none'">
<title>Hoshi PRIVATE Anime Studio pilot review</title>
<style>
body{{font:16px system-ui,sans-serif;background:#0b1220;color:#eaf1fb;margin:auto;max-width:960px;padding:20px;line-height:1.55}}
h1,h2{{color:#c7e4ff}}.warning{{border:2px solid #efc77c;padding:12px}}
video,img{{display:block;width:100%;max-width:100%;height:auto;margin:12px 0}}
.cue{{border:1px solid #40536b;border-radius:8px;padding:14px;margin:12px 0}}
.caption{{font-size:1.35rem;white-space:pre-wrap;overflow-wrap:anywhere}}
audio{{width:100%}}.hash{{font-size:.75rem;overflow-wrap:anywhere;color:#b6c7dd}}
</style></head><body>
<h1>Hoshi Anime Studio — PRIVATE 30-second pilot</h1>
<p class="warning"><strong>UNAPPROVED / DO NOT PUBLISH.</strong>
This local page does not certify Hindi/Urdu speech, words, pronunciation,
lip-sync, source/font/voice rights, artistic quality or owner acceptance.</p>
<h2>Actual subtitle-burned MP4</h2>
<video controls preload="metadata" src="{VIDEO}"></video>
<p class="hash">Encoded MP4 SHA-256: {video_hash}</p>
<h2>Decoded original vs captioned frames</h2>
<img src="{VISUAL}" alt="Three original versus encoded captioned MP4 frames">
<p class="hash">Comparison SHA-256: {visual_hash}</p>
<h2>Listen and inspect each subtitle cue</h2>
{''.join(cards)}
{waveform}
<p>Manually play the complete video, listen to each cue, compare caption timing,
visual readability, original character motion, voice rights and any sound defects.
Record acceptance or revisions separately in the existing private review workflow.
No approval, upload or account action occurs from opening this page.</p>
</body></html>
"""
    data = document.encode("utf-8")
    if len(data) > 32_000:
        raise AnimePrivateReviewPageError("Private review HTML exceeds size limit.")
    return data
