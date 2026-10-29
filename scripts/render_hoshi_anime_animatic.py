"""Operator-only offline CLI for the private Hoshi Anime Studio animatic.

No network, public route, account login or uploader. Never overwrites outputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cloud_backend.anime_pilot_animatic import (
    AnimePilotError, MAX_IMAGE_BYTES, MAX_AUDIO_BYTES, render_private_animatic,
)
from cloud_backend.anime_mouth_overlay import MAX_SPRITE_BYTES
from cloud_backend.anime_visual_review import (build_mouth_review_sheet,
                                               AnimeVisualReviewError)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build private 30s anime storyboard animatic")
    parser.add_argument("--shot", action="append", required=True, help="Local PNG/JPEG (exactly 3)")
    parser.add_argument("--caption", action="append", required=True,
                        help="Hindi/Urdu/Roman Urdu single-line subtitle (exactly 3)")
    parser.add_argument("--out", required=True, help="New local directory; must not exist")
    parser.add_argument("--storyboard-json", help="Optional local 3-shot v1 plan; must match images, captions and moves")
    parser.add_argument("--camera-move", action="append", choices=("static", "push_in", "pan_left", "pan_right"),
                        help="Optional 2D still camera move, once per shot (exactly 3)")
    parser.add_argument("--audio-wav", help="Optional local 30s mono 16-bit PCM WAV, 16/24kHz")
    parser.add_argument("--voice-cues-json", help="Optional operator-supplied v1 per-shot voice timing; requires storyboard and WAV")
    parser.add_argument("--mouth-overlay-json",
                        help="Optional v1 original mouth sprite positions and exact SHA-256")
    parser.add_argument("--mouth-sprite", action="append",
                        help="Optional original transparent mouth-open RGBA PNG, exactly 3")
    parser.add_argument("--mouth-review-sheet", action="store_true",
                        help="Export a private decoded-frame PNG contact sheet for manual mouth placement review")
    parser.add_argument("--mouth-rights-attested", action="store_true",
                        help="Operator confirms rights to all mouth sprites; not phoneme lip-sync")
    parser.add_argument("--audio-rights-attested", action="store_true",
                        help="Operator confirms rights to the supplied WAV; does not verify dubbing")
    parser.add_argument("--image-rights-attested", action="store_true",
                        help="Operator confirms rights to all supplied stills")
    args = parser.parse_args()
    if len(args.shot) != 3 or len(args.caption) != 3:
        parser.error("Exactly three --shot and three --caption values are required.")
    if args.camera_move is not None and len(args.camera_move) != 3:
        parser.error("Provide exactly three --camera-move values, or none.")
    if not args.image_rights_attested:
        parser.error("Explicit --image-rights-attested is required.")
    if bool(args.audio_wav) != args.audio_rights_attested:
        parser.error("--audio-wav and --audio-rights-attested must be supplied together.")
    if args.mouth_review_sheet and not args.mouth_overlay_json:
        parser.error("--mouth-review-sheet requires the complete mouth-overlay input.")
    if (args.mouth_overlay_json is not None or args.mouth_sprite is not None
            or args.mouth_rights_attested):
        if (not args.mouth_overlay_json or args.mouth_sprite is None
                or len(args.mouth_sprite) != 3 or not args.mouth_rights_attested
                or not args.voice_cues_json):
            parser.error("Mouth overlays require --mouth-overlay-json, exactly three --mouth-sprite, --mouth-rights-attested and --voice-cues-json.")

    try:
        images = []
        for name in args.shot:
            path = Path(name)
            if not path.is_file() or not 100 <= path.stat().st_size <= MAX_IMAGE_BYTES:
                raise AnimePilotError("Local still missing or too large.")
            images.append(path.read_bytes())
        audio = None
        if args.audio_wav:
            audio_path = Path(args.audio_wav)
            if not audio_path.is_file() or not 44 <= audio_path.stat().st_size <= MAX_AUDIO_BYTES:
                raise AnimePilotError("Local audio WAV missing or too large.")
            audio = audio_path.read_bytes()
        storyboard = None
        if args.storyboard_json:
            plan_path = Path(args.storyboard_json)
            if not plan_path.is_file() or not 1 <= plan_path.stat().st_size <= 12000:
                raise AnimePilotError("Local storyboard JSON missing or too large.")
            try:
                storyboard = json.loads(plan_path.read_text(encoding="utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                raise AnimePilotError("Invalid UTF-8 storyboard JSON.") from None
        voice_cues = None
        if args.voice_cues_json:
            cue_path = Path(args.voice_cues_json)
            if not args.storyboard_json or not args.audio_wav:
                raise AnimePilotError("Voice cues require both --storyboard-json and --audio-wav.")
            if not cue_path.is_file() or not 1 <= cue_path.stat().st_size <= 5000:
                raise AnimePilotError("Local voice cues JSON missing or too large.")
            try:
                voice_cues = json.loads(cue_path.read_text(encoding="utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                raise AnimePilotError("Invalid UTF-8 voice cues JSON.") from None
        mouth_plan = None
        mouth_sprites = None
        if args.mouth_overlay_json:
            mouth_path = Path(args.mouth_overlay_json)
            if not mouth_path.is_file() or not 1 <= mouth_path.stat().st_size <= 5000:
                raise AnimePilotError("Local mouth overlay JSON missing or too large.")
            try:
                mouth_plan = json.loads(mouth_path.read_text(encoding="utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                raise AnimePilotError("Invalid UTF-8 mouth overlay JSON.") from None
            mouth_sprites = []
            for name in args.mouth_sprite:
                path = Path(name)
                if not path.is_file() or not 80 <= path.stat().st_size <= MAX_SPRITE_BYTES:
                    raise AnimePilotError("Mouth sprite PNG missing or too large.")
                mouth_sprites.append(path.read_bytes())
        output = render_private_animatic(
            images, args.caption, image_rights_attested=True,
            camera_moves=args.camera_move, storyboard_handoff=storyboard,
            audio_wav=audio, audio_rights_attested=args.audio_rights_attested,
            voice_timing_plan=voice_cues,
            mouth_overlay_plan=mouth_plan, mouth_sprites=mouth_sprites,
            mouth_rights_attested=args.mouth_rights_attested)
        review = None
        if args.mouth_review_sheet:
            try:
                review = build_mouth_review_sheet(
                    output["video_mp4"], output["mouth_overlay_handoff"])
            except AnimeVisualReviewError as exc:
                raise AnimePilotError(str(exc)) from None
        destination = Path(args.out)
        destination.mkdir(parents=False, exist_ok=False)
        try:
            (destination / output["filename"]).write_bytes(output["video_mp4"])
            (destination / "hoshi_anime_animatic_DRAFT.srt").write_bytes(
                output["subtitles_srt"])
            metadata = {k: v for k, v in output.items()
                        if k not in ("video_mp4", "subtitles_srt")}
            if review is not None:
                (destination / review["filename"]).write_bytes(review["png_bytes"])
                metadata["mouth_visual_review"] = {
                    k: v for k, v in review.items() if k != "png_bytes"}
            (destination / "manifest.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8")
        except OSError:
            for path in destination.iterdir():
                path.unlink()
            destination.rmdir()
            raise
        print(f"Private animatic created: {destination}")
        return 0
    except (AnimePilotError, OSError) as exc:
        print(f"Animatic not created: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
