"""Private offline Hoshi Anime Studio: 30-second *animatic*, not full animation.

Three rights-attested stills + original captions -> real H.264 MP4 and SRT.
No internet, public API, background worker, external upload, AI voice or account use.
This is a review-only pilot for a future multi-agent Hindi/Urdu production system.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave

from PIL import Image, ImageOps, UnidentifiedImageError

from .anime_storyboard_handoff import bind_storyboard_handoff, StoryboardHandoffError
from .anime_voice_timing import bind_voice_timing_handoff, VoiceTimingError


class AnimePilotError(ValueError):
    """Invalid or unverifiable private anime animatic input/output."""


WIDTH, HEIGHT, FPS, SHOT_SECONDS = 480, 270, 12, 10
DURATION_SECONDS = 30
CAMERA_MOVES = ("static", "push_in", "pan_left", "pan_right")
MAX_IMAGE_BYTES = 4_000_000
MAX_MP4_BYTES = 15_000_000
MAX_AUDIO_BYTES = 3_000_000
ROLES = (
    "production_manager", "story_architect", "script_writer",
    "character_designer", "character_consistency", "background_artist",
    "storyboard_artist", "action_choreographer", "animation_director",
    "vfx_artist", "voice_casting", "voice_artist", "lip_sync",
    "original_music", "sound_design", "video_editor", "subtitles",
    "thumbnail_designer", "seo", "quality_inspector", "rights_checker",
    "render_export", "approval_gated_uploader", "production_auditor",
)


def _image_to_frame(source: bytes) -> tuple[Image.Image, str]:
    if type(source) is not bytes or not (100 <= len(source) <= MAX_IMAGE_BYTES):
        raise AnimePilotError("Each still must be a bounded PNG or JPEG.")
    try:
        with Image.open(BytesIO(source)) as picture:
            if picture.format not in ("PNG", "JPEG") or getattr(picture, "n_frames", 1) != 1:
                raise AnimePilotError("Only single-frame PNG/JPEG stills are supported.")
            if not (64 <= picture.width <= 4096 and 64 <= picture.height <= 4096):
                raise AnimePilotError("Still image dimensions are out of bounds.")
            picture.load()
            normalized = ImageOps.exif_transpose(picture).convert("RGB")
            normalized.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            frame = Image.new("RGB", (WIDTH, HEIGHT), (8, 12, 24))
            frame.paste(normalized, ((WIDTH - normalized.width) // 2,
                                     (HEIGHT - normalized.height) // 2))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise AnimePilotError("Still image could not be decoded safely.") from None
    return frame, hashlib.sha256(source).hexdigest()


def _captions_to_srt(captions: tuple[str, ...] | list[str]) -> bytes:
    if type(captions) not in (tuple, list) or len(captions) != 3:
        raise AnimePilotError("Exactly three timed captions are required.")
    blocks = []
    for index, caption in enumerate(captions):
        if (type(caption) is not str or not 1 <= len(caption) <= 180
                or caption != caption.strip() or any(
                    ord(ch) < 32 or ch in "<>\u202e\u202d\u2066\u2067\u2068\u2069"
                    for ch in caption)):
            raise AnimePilotError("Caption must be a safe single line.")
        start, end = index * SHOT_SECONDS, (index + 1) * SHOT_SECONDS
        blocks.append(f"{index + 1}\n00:00:{start:02d},000 --> 00:00:{end:02d},000\n{caption}\n")
    return ("\n".join(blocks) + "\n").encode("utf-8")


def _voice_cues_to_srt(voice_timing: dict) -> bytes:
    """Export operator-validated speech intervals, not inferred lip-sync.

    The exact original caption is displayed only during its supplied cue window.
    Silent gaps are intentionally left without subtitles. All intervals and
    captions were validated by bind_voice_timing_handoff before this call.
    """
    blocks = []
    for index, cue in enumerate(voice_timing["plan"]["cues"], 1):
        def timestamp(ms: int) -> str:
            hours, remainder = divmod(ms, 3_600_000)
            minutes, remainder = divmod(remainder, 60_000)
            seconds, millis = divmod(remainder, 1000)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

        blocks.append(
            f'{index}\n{timestamp(cue["start_ms"])} --> '
            f'{timestamp(cue["end_ms"])}\n{cue["text"]}\n'
        )
    return ("\n".join(blocks) + "\n").encode("utf-8")


def _validate_audio(audio: bytes) -> None:
    if type(audio) is not bytes or not 44 <= len(audio) <= MAX_AUDIO_BYTES:
        raise AnimePilotError("Optional audio must be a bounded PCM WAV.")
    try:
        with wave.open(BytesIO(audio), "rb") as stream:
            rate, frames = stream.getframerate(), stream.getnframes()
            if (stream.getcomptype() != "NONE" or stream.getnchannels() != 1
                    or stream.getsampwidth() != 2 or rate not in (16000, 24000)
                    or not 30 <= frames / rate <= 30.2
                    or len(stream.readframes(frames)) != frames * 2):
                raise AnimePilotError("Audio must be 30s mono 16-bit PCM WAV.")
    except (wave.Error, OSError, EOFError, ValueError, ZeroDivisionError):
        raise AnimePilotError("Invalid or truncated WAV.") from None


def _probe(path: Path, ffprobe: str, with_audio: bool) -> None:
    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries",
             "stream=codec_type,codec_name,width,height:format=duration,format_name",
             "-of", "json", str(path)],
            capture_output=True, timeout=12, check=False,
        )
        if result.returncode or len(result.stdout) > 16000:
            raise AnimePilotError("Video probe failed.")
        info = json.loads(result.stdout)
        videos = [s for s in info["streams"] if s.get("codec_type") == "video"]
        audios = [s for s in info["streams"] if s.get("codec_type") == "audio"]
        duration = float(info["format"]["duration"])
        if (len(videos) != 1 or videos[0].get("codec_name") != "h264"
                or (videos[0].get("width"), videos[0].get("height")) != (WIDTH, HEIGHT)
                or len(audios) != int(with_audio)
                or (with_audio and audios[0].get("codec_name") != "aac")
                or "mp4" not in info["format"].get("format_name", "")
                or not 29.8 <= duration <= 30.3):
            raise AnimePilotError("Video stream or duration failed independent QC.")
    except (OSError, subprocess.TimeoutExpired, KeyError, TypeError, ValueError, IndexError):
        raise AnimePilotError("Could not independently verify MP4.") from None


def _camera_filter(moves: tuple[str, ...]) -> str:
    """Allowlisted FFmpeg 2D still reframing; never interpolate character motion."""
    segments = []
    for index, move in enumerate(moves):
        source, target = f"[{index}:v]", f"[shot{index}]"
        if move == "static":
            effect = "setpts=PTS-STARTPTS"
        elif move == "push_in":
            effect = ("zoompan=z='min(1+on*0.001,1.12)':"
                      "x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
                      f"d=1:s={WIDTH}x{HEIGHT}:fps={FPS},setpts=PTS-STARTPTS")
        else:
            horizontal = ("(iw-iw/zoom)*(1-on/119)" if move == "pan_left"
                          else "(iw-iw/zoom)*on/119")
            effect = (f"zoompan=z=1.12:x='{horizontal}':"
                      f"y='(ih-ih/zoom)/2':d=1:s={WIDTH}x{HEIGHT}:"
                      f"fps={FPS},setpts=PTS-STARTPTS")
        segments.append(f"{source}{effect}{target}")
    segments.append("[shot0][shot1][shot2]concat=n=3:v=1:a=0,format=yuv420p[v]")
    return ";".join(segments)


def render_private_animatic(stills: list[bytes] | tuple[bytes, ...],
                            captions: list[str] | tuple[str, ...], *,
                            image_rights_attested: bool = False,
                            audio_wav: bytes | None = None,
                            audio_rights_attested: bool = False,
                            camera_moves: list[str] | tuple[str, ...] | None = None,
                            storyboard_handoff: dict | None = None,
                            voice_timing_plan: dict | None = None) -> dict:
    """Encode a private 30-second storyboard preview; never approve/publish it.

    Caller must attest rights to every still and optional soundtrack. No claim
    of independent copyright verification, Hindi/Urdu TTS or full animation.
    Captions are exported as a UTF-8 SRT sidecar, not burned into frames.
    """
    if type(image_rights_attested) is not bool or not image_rights_attested:
        raise AnimePilotError("Explicit rights attestation for all stills is required.")
    if type(audio_rights_attested) is not bool:
        raise AnimePilotError("Audio rights attestation must be boolean.")
    if (audio_wav is None) != (not audio_rights_attested):
        raise AnimePilotError("Audio and its explicit rights attestation must match.")
    if audio_wav is not None:
        _validate_audio(audio_wav)
    if type(stills) not in (list, tuple) or len(stills) != 3:
        raise AnimePilotError("Exactly three original stills are required.")
    if camera_moves is None:
        camera_moves = ("static",) * 3
    if (type(camera_moves) not in (list, tuple) or len(camera_moves) != 3
            or any(type(move) is not str or move not in CAMERA_MOVES
                   for move in camera_moves)):
        raise AnimePilotError("Camera moves must be three allowlisted 2D moves.")
    camera_moves = tuple(camera_moves)
    srt = _captions_to_srt(captions)
    images = [_image_to_frame(still) for still in stills]
    handoff = None
    if storyboard_handoff is not None:
        try:
            handoff = bind_storyboard_handoff(
                storyboard_handoff, stills, captions, camera_moves)
        except StoryboardHandoffError as exc:
            raise AnimePilotError(str(exc)) from None
    voice_timing = None
    if voice_timing_plan is not None:
        try:
            voice_timing = bind_voice_timing_handoff(voice_timing_plan, handoff, audio_wav)
        except VoiceTimingError as exc:
            raise AnimePilotError(str(exc)) from None
        # Match the actual SRT sidecar to validated operator cue intervals.
        # This does not certify that the WAV contains the spoken words.
        srt = _voice_cues_to_srt(voice_timing)
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AnimePilotError("Offline FFmpeg and ffprobe are required.")

    try:
        with tempfile.TemporaryDirectory(prefix="hoshi-anime-animatic-") as directory:
            root = Path(directory)
            cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
            for index, (frame, _) in enumerate(images):
                path = root / f"shot{index}.png"
                frame.save(path, format="PNG")
                cmd += ["-loop", "1", "-framerate", str(FPS),
                        "-t", str(SHOT_SECONDS), "-i", str(path)]
            if audio_wav is not None:
                wav_path = root / "audio.wav"
                wav_path.write_bytes(audio_wav)
                cmd += ["-i", str(wav_path)]
            cmd += ["-filter_complex", _camera_filter(camera_moves),
                    "-map", "[v]"]
            if audio_wav is not None:
                cmd += ["-map", "3:a:0"]
            cmd += ["-frames:v", str(DURATION_SECONDS * FPS), "-r", str(FPS),
                    "-c:v", "libx264", "-threads", "2", "-preset", "ultrafast",
                    "-crf", "32", "-pix_fmt", "yuv420p"]
            if audio_wav is None:
                cmd += ["-an"]
            else:
                cmd += ["-c:a", "aac", "-b:a", "64k"]
            output = root / "hoshi_anime_animatic_DRAFT.mp4"
            cmd += ["-movflags", "+faststart", "-f", "mp4", str(output)]
            completed = subprocess.run(cmd, capture_output=True, timeout=90, check=False)
            if completed.returncode != 0 or not output.is_file():
                raise AnimePilotError("Offline animatic encoding failed.")
            if not 0 < output.stat().st_size <= MAX_MP4_BYTES:
                raise AnimePilotError("Encoded MP4 exceeds the size limit.")
            _probe(output, ffprobe, audio_wav is not None)
            mp4 = output.read_bytes()
    except (OSError, subprocess.TimeoutExpired):
        raise AnimePilotError("Offline encoding failed or timed out.") from None

    return {
        "filename": "hoshi_anime_animatic_DRAFT.mp4",
        "video_mp4": mp4,
        "subtitles_srt": srt,
        "video_sha256": hashlib.sha256(mp4).hexdigest(),
        "subtitles_sha256": hashlib.sha256(srt).hexdigest(),
        "source_image_sha256": [digest for _, digest in images],
        "source_audio_sha256": (hashlib.sha256(audio_wav).hexdigest()
                                if audio_wav is not None else None),
        "duration_seconds": DURATION_SECONDS,
        "resolution": [WIDTH, HEIGHT],
        "frame_rate": FPS,
        "camera_moves": list(camera_moves),
        "storyboard_handoff": handoff,
        "voice_timing_handoff": voice_timing,
        "subtitle_timing_source": ("operator_supplied_voice_cues_not_audio_verified"
                                   if voice_timing is not None else "fixed_ten_second_shots"),
        "camera_motion_is_2d_still_reframing": any(m != "static" for m in camera_moves),
        "production_roles": list(ROLES),
        "stage": "private_storyboard_animatic_only",
        "actual_mp4_rendered": True,
        "full_character_animation": False,
        "hindi_urdu_voice_recorded": False,
        "subtitles_embedded": False,
        "audio_status": ("caller_attested_wav_unverified" if audio_wav is not None
                         else "silent_no_music"),
        "source_rights_independently_verified": False,
        "owner_approved": False,
        "published": False,
        "uploaded": False,
        "requires_owner_review": True,
    }
