"""Private waveform contact sheet from the *actual encoded AAC* listening WAVs.

This is a bounded visual handoff for a human to compare sound timing with
caption cue boundaries. Peaks do NOT establish words, language, or lip-sync.
No uploads, external services, playback or owner/publication authorization.
"""
from __future__ import annotations

from array import array
from io import BytesIO
import hashlib
import sys
import wave

from PIL import Image, ImageDraw


class AnimeAudioWaveformError(ValueError):
    """Invalid or mismatched private encoded-audio evidence."""


WIDTH, HEIGHT = 1440, 660
LEFT, RIGHT = 150, 1400
SAMPLE_RATE = 16000
MAX_WAV_BYTES = 750_000


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_encoded_audio_waveform(clips: list[dict], samples: list[dict]) -> dict:
    """Render three AAC-derived cue waveforms with exact SRT cue markers.

    The input WAV bytes must match the SHA-256 and timing/sample metadata
    returned by the encoded-MP4 extractor. Empty inputs mean no audio track;
    never manufacture a waveform for a silent source.
    """
    if clips == [] and samples == []:
        return {"png_bytes": None, "samples": [],
                "status": "no_encoded_aac_no_waveform"}
    if (type(clips) is not list or type(samples) is not list
            or len(clips) != 3 or len(samples) != 3):
        raise AnimeAudioWaveformError("Exactly three encoded AAC excerpts required.")
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (9, 14, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text((LEFT, 14),
              "ENCODED AAC CUE TIMING - HUMAN LISTENING REVIEW ONLY",
              fill=(234, 239, 248))
    draw.text((LEFT, 34),
              "Waveform energy is not speech, word accuracy or phoneme sync.",
              fill=(174, 188, 209))
    records = []
    for index, (clip, item) in enumerate(zip(clips, samples)):
        filename = f"hoshi_cue_{index + 1}_PRIVATE_REVIEW.wav"
        if (type(clip) is not dict or type(item) is not dict
                or clip.get("filename") != filename
                or item.get("filename") != filename
                or item.get("shot_index") != index + 1
                or item.get("decoded_from_actual_captioned_mp4_aac") is not True
                or item.get("spoken_words_independently_verified") is not False
                or item.get("phoneme_sync_verified") is not False):
            raise AnimeAudioWaveformError("Cue source provenance mismatch.")
        data = clip.get("wav_bytes")
        first = item.get("excerpt_start_ms")
        end_requested = item.get("excerpt_end_ms_requested")
        cue_start, cue_end = item.get("cue_start_ms"), item.get("cue_end_ms")
        count = item.get("decoded_pcm_sample_count")
        if (type(data) is not bytes or not 44 <= len(data) <= MAX_WAV_BYTES
                or type(item.get("wav_sha256")) is not str
                or _sha(data) != item["wav_sha256"]
                or item.get("sample_rate_hz") != SAMPLE_RATE
                or item.get("channels") != 1
                or item.get("sample_width_bytes") != 2
                or type(first) is not int or type(end_requested) is not int
                or type(cue_start) is not int or type(cue_end) is not int
                or type(count) is not int
                or not 0 <= first <= cue_start < cue_end <= end_requested <= 30000
                or not 1 <= count <= 175_000):
            raise AnimeAudioWaveformError("Invalid bounded cue WAV metadata.")
        try:
            with wave.open(BytesIO(data), "rb") as reader:
                if (reader.getnchannels() != 1 or reader.getsampwidth() != 2
                        or reader.getframerate() != SAMPLE_RATE
                        or reader.getcomptype() != "NONE"
                        or reader.getnframes() != count):
                    raise AnimeAudioWaveformError("WAV header differs from AAC provenance.")
                raw = reader.readframes(count)
        except (wave.Error, EOFError, OSError):
            raise AnimeAudioWaveformError("Invalid encoded-audio review WAV.") from None
        if len(raw) != count * 2:
            raise AnimeAudioWaveformError("Truncated encoded-audio WAV.")
        actual_end = first + count * 1000 / SAMPLE_RATE
        if (abs(actual_end - end_requested) > 105
                or cue_end > actual_end + 105):
            raise AnimeAudioWaveformError("AAC excerpt timing differs from cue.")
        pcm = array("h")
        pcm.frombytes(raw)
        if sys.byteorder != "little":
            pcm.byteswap()
        row_top = 76 + index * 190
        center = row_top + 82
        draw.text((20, row_top + 48), f"CUE {index + 1}",
                  fill=(237, 243, 251))
        draw.text((15, row_top + 69), f"{cue_start}-{cue_end} ms",
                  fill=(165, 183, 205))
        draw.rectangle((LEFT, row_top, RIGHT, row_top + 160),
                       outline=(65, 80, 104), width=1)
        def x_at(ms: float) -> int:
            return LEFT + round((ms - first) * (RIGHT - LEFT)
                                / (actual_end - first))
        x0 = max(LEFT, min(RIGHT, x_at(cue_start)))
        x1 = max(LEFT, min(RIGHT, x_at(cue_end)))
        if x1 <= x0:
            raise AnimeAudioWaveformError("Cue has no measurable waveform width.")
        draw.rectangle((x0, row_top + 1, x1, row_top + 159),
                       fill=(22, 44, 66))
        draw.line((LEFT, center, RIGHT, center), fill=(79, 94, 114))
        draw.line((x0, row_top, x0, row_top + 160),
                  fill=(255, 195, 94), width=2)
        draw.line((x1, row_top, x1, row_top + 160),
                  fill=(255, 195, 94), width=2)
        # Peak-envelope bins represent real decoded samples; never invent
        # interpolated dialogue activity between quiet samples.
        bins = 625
        peak_max = 0
        for bin_index in range(bins):
            a = bin_index * count // bins
            b = (bin_index + 1) * count // bins
            if b <= a:
                continue
            peak = max(abs(int(value)) for value in pcm[a:b])
            peak_max = max(peak_max, peak)
            height = round(peak * 69 / 32768)
            x = LEFT + bin_index * (RIGHT - LEFT) // bins
            draw.line((x, center - height, x, center + height),
                      fill=(97, 211, 212), width=2)
        draw.text((LEFT + 4, row_top + 140),
                  f"Excerpt {first}-{end_requested} ms | {count} samples",
                  fill=(181, 200, 219))
        records.append({
            "shot_index": index + 1,
            "wav_sha256": item["wav_sha256"],
            "cue_start_ms": cue_start, "cue_end_ms": cue_end,
            "excerpt_start_ms": first,
            "decoded_pcm_sample_count": count,
            "measured_peak_normalized": round(peak_max / 32768, 6),
            "cue_marker_x_px": [x0, x1],
            "spoken_words_independently_verified": False,
            "phoneme_sync_verified": False,
        })
    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    png = buffer.getvalue()
    if not 100 <= len(png) <= 4_000_000:
        raise AnimeAudioWaveformError("Private waveform PNG exceeds size limit.")
    return {"png_bytes": png, "samples": records,
            "status": "actual_encoded_aac_waveform_human_review_only",
            "resolution": [WIDTH, HEIGHT],
            "png_sha256": _sha(png),
            "human_listening_review_required": True,
            "spoken_words_independently_verified": False,
            "phoneme_sync_verified": False,
            "owner_approved": False, "publication_permitted": False}
