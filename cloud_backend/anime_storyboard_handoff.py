"""Validated private storyboard-to-renderer handoff for Hoshi Anime Studio.

This binds a human-authored 3-shot plan to the *exact* still bytes, caption
text, camera movement, and stable character design-reference identifiers.
It does not generate artwork, prove that a face is consistent, or clear rights.
No network, accounts, filesystem writes, model calls or external execution.
"""
from __future__ import annotations

import hashlib
import json
import re


class StoryboardHandoffError(ValueError):
    """A private storyboard package is invalid or does not match its media."""


_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,39}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_LANGUAGES = frozenset(("hi", "ur", "roman-ur"))
_MOVES = frozenset(("static", "push_in", "pan_left", "pan_right"))


def _identifier(value: object) -> bool:
    return type(value) is str and _ID.fullmatch(value) is not None


def _digest(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def bind_storyboard_handoff(
    storyboard: object,
    stills: list[bytes] | tuple[bytes, ...],
    captions: list[str] | tuple[str, ...],
    camera_moves: list[str] | tuple[str, ...],
) -> dict:
    """Fail closed unless plan and actual 30s renderer inputs match exactly.

    The per-character design SHA is caller-supplied provenance metadata; it is
    not an independently inspected reference image or proof of visual fidelity.
    """
    if type(storyboard) is not dict or set(storyboard) != {
        "schema_version", "project_id", "language", "characters", "shots"
    }:
        raise StoryboardHandoffError("Storyboard must use the exact v1 schema.")
    if type(storyboard["schema_version"]) is not int or storyboard["schema_version"] != 1:
        raise StoryboardHandoffError("Unsupported storyboard schema version.")
    if not _identifier(storyboard["project_id"]):
        raise StoryboardHandoffError("Invalid project identifier.")
    if type(storyboard["language"]) is not str or storyboard["language"] not in _LANGUAGES:
        raise StoryboardHandoffError("Storyboard language must be hi, ur or roman-ur.")

    characters = storyboard["characters"]
    if type(characters) is not list or not 1 <= len(characters) <= 6:
        raise StoryboardHandoffError("Provide 1 to 6 character design references.")
    ids = set()
    for character in characters:
        if type(character) is not dict or set(character) != {
            "id", "design_sha256", "rights_attested"
        }:
            raise StoryboardHandoffError("Invalid character reference schema.")
        if (not _identifier(character["id"]) or character["id"] in ids
                or not _digest(character["design_sha256"])
                or character["rights_attested"] is not True):
            raise StoryboardHandoffError("Character reference requires unique ID, SHA and rights attestation.")
        ids.add(character["id"])

    shots = storyboard["shots"]
    if (type(shots) is not list or len(shots) != 3
            or type(stills) not in (list, tuple) or len(stills) != 3
            or type(captions) not in (list, tuple) or len(captions) != 3
            or type(camera_moves) not in (list, tuple) or len(camera_moves) != 3):
        raise StoryboardHandoffError("Storyboard must bind exactly three 10-second shots.")
    shot_ids = set()
    for index, shot in enumerate(shots):
        if type(shot) is not dict or set(shot) != {
            "shot_id", "still_sha256", "caption", "camera_move", "character_ids"
        }:
            raise StoryboardHandoffError("Invalid shot schema.")
        references = shot["character_ids"]
        if (not _identifier(shot["shot_id"]) or shot["shot_id"] in shot_ids
                or type(stills[index]) is not bytes
                or not _digest(shot["still_sha256"])
                or shot["still_sha256"] != hashlib.sha256(stills[index]).hexdigest()
                or type(shot["caption"]) is not str
                or shot["caption"] != captions[index]
                or type(shot["camera_move"]) is not str
                or shot["camera_move"] not in _MOVES
                or shot["camera_move"] != camera_moves[index]
                or type(references) is not list or len(references) > 4
                or any(not _identifier(r) for r in references)
                or len(set(references)) != len(references)
                or any(r not in ids for r in references)):
            raise StoryboardHandoffError("Shot identifiers, rights references or exact media binding failed.")
        shot_ids.add(shot["shot_id"])

    # Serialize a normalized, bounded schema, not arbitrary caller objects.
    bound = {
        "schema_version": 1,
        "project_id": storyboard["project_id"],
        "language": storyboard["language"],
        "characters": [
            {"id": c["id"], "design_sha256": c["design_sha256"],
             "rights_attested": True} for c in characters
        ],
        "shots": [
            {"shot_id": s["shot_id"], "still_sha256": s["still_sha256"],
             "caption": s["caption"], "camera_move": s["camera_move"],
             "character_ids": list(s["character_ids"])}
            for s in shots
        ],
    }
    serialized = json.dumps(bound, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":")).encode("utf-8")
    if len(serialized) > 12000:
        raise StoryboardHandoffError("Storyboard metadata exceeds private size limit.")
    return {
        "plan": bound,
        "plan_sha256": hashlib.sha256(serialized).hexdigest(),
        "shot_duration_seconds": 10,
        "character_design_consistency": "reference_ids_only_visuals_not_verified",
        "rights_independently_verified": False,
        "owner_approved": False,
    }
