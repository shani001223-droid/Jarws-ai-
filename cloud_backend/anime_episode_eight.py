"""Task 56 EP008: original Roman Urdu Tadbeer editorial draft, unreviewed.

A supervised public inventory cross-check preserves the restricted-record
boundary, unresolved index page and patient-first power priority.
Planned 1,800 seconds are not measured speech or produced running time.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache

from cloud_backend.anime_episode_seven import episode_seven_script
from cloud_backend.anime_series import series_manifest

@lru_cache(maxsize=1)
def _previous_episode_sha256() -> str:
    """Cache only an immutable digest, never a mutable prior draft."""
    return episode_seven_script()["sha256"]


EPISODE_ID = "EP008"
SCENE_SECONDS = 225
SPEAKERS = frozenset({"laila", "rayan", "meher", "aman", "zoya"})
CARRY_FORWARD = {
  "pulse_custody": "meher_archive_copy_and_laila_source",
  "clock_offset": "two_minutes_not_silently_corrected",
  "signal_source": "unknown",
  "clinic_priority": "patient_safety_before_receiver_test",
  "locked_corridor_access": "written_permission_pending",
  "missing_index_page": "absent_logged_not_reconstructed",
  "public_witness_consent": "required_before_disclosure",
  "portable_test": "dry_run_only",
  "public_notice": "draft_not_issued",
  "handoff_receipt": "internal_signed_independent_review_pending",
  "library_register": "public_reference_catalog_and_bound_register_located",
  "restricted_library_records": "written_request_pending",
  "library_condition_history": "not_accessed_staff_review_pending",
  "catalog_dates": "public_discrepancy_not_proof_of_tampering",
  "records_request": "submitted_receipt_not_permission",
  "public_inventory_crosscheck": "read_only_public_entries_logged_no_missing_page_found",
  "private_borrower_data": "not_collected_or_disclosed",
  "library_staff_identity": "not_recorded_for_publication",
  "next_sequence": "public_copy_custody_review_pending"
}
SCENES = [
  [
    "Doosra raasta",
    "Noorabad public library ka enquiry desk",
    "Zoya restricted request pending rakh kar public inventory ka supervised cross-check propose karti hai.",
    [
      [
        "zoya",
        "Restricted ledger ka jawab abhi nahi aaya. Public inventory ki khuli entries staff ki hidayat se dekh sakte hain."
      ],
      [
        "laila",
        "Yeh Tadbeer hai, shortcut nahi. Koi private record kholna ya missing page khud banana hamara kaam nahi."
      ],
      [
        "meher",
        "Main public entries ka source, edition aur observation waqt alag likhungi. Receipt ko ijazat nahi samjhungi."
      ],
      [
        "aman",
        "Library staff ka naam afwah mein nahi aana chahiye. Hamara sawaal record se hai, kisi shakhs se nahi."
      ]
    ]
  ],
  [
    "Purana nuskha",
    "Library ka supervised reference shelf",
    "Team do public inventory editions compare karti hai; originals library mein hi rehte hain.",
    [
      [
        "meher",
        "Dono public editions par alag print dates hain. Main page numbers aur headings likh rahi hoon, tasveer nahi le rahi."
      ],
      [
        "rayan",
        "Print date aur signal timestamp aik jaisi cheez nahi. Inko mila kar frequency ka nateeja nikalna ghalat hoga."
      ],
      [
        "laila",
        "Original volumes yahin rahenge. Hamari copy mein sirf publicly visible differences aur uncertainty jayegi."
      ],
      [
        "zoya",
        "Staff ne supervised viewing ki had batayi hai; is se restricted maintenance ledger ki access nahi milti."
      ]
    ]
  ],
  [
    "Khali khana",
    "Library ka public catalog print table",
    "Public index serial range ka gap note hota hai; missing page ka matn infer nahi kiya jata.",
    [
      [
        "rayan",
        "Serial range mein aik khali jagah nazar aa rahi hai, magar is ka matlab transmitter ki frequency nahi hota."
      ],
      [
        "meher",
        "Gap ka reference aur public source likh diya. Missing index page ka matn ab bhi unknown hai."
      ],
      [
        "aman",
        "Agar hum andaazay ko haqeeqat bol den to library ke logon ka bharosa toot jayega."
      ],
      [
        "laila",
        "Is observation ko sawal ki surat mein rakho. Na sabotage sabit hua, na kisi shakhs ki ghalti."
      ]
    ]
  ],
  [
    "Naya sawal",
    "Library ka public information counter",
    "Zoya public print-cycle policy ka general sawal poochti hai; private borrower data nahi maangti.",
    [
      [
        "zoya",
        "Hum sirf public edition cycle aur catalog revision policy pooch rahe hain, borrower ki private file nahi."
      ],
      [
        "meher",
        "Jo general policy public hai us ka edition number record hoga. Personal history packet mein nahi jayegi."
      ],
      [
        "laila",
        "Agar jawab available na ho to pending likhenge. Khali jagah ko kahani se bharna mana hai."
      ],
      [
        "aman",
        "Logon ki izzat bhi evidence ka hissa hai. Bina consent kisi witness ki pehchan share nahi hogi."
      ]
    ]
  ],
  [
    "Ghadi ka farq",
    "Observatory ka offline evidence table",
    "Rayan library edition notes ko raw pulse timestamps se alag rakhta hai; live equipment untouched.",
    [
      [
        "rayan",
        "Instrument ki do minute correction ko library edition dates par lagana be-maani hai. Yeh clocks comparable nahi."
      ],
      [
        "meher",
        "Raw pulse recording aur library observations ke alag envelopes hain; dono ki chain of custody likhi hai."
      ],
      [
        "laila",
        "Koi signal source confirm nahi hua. Public catalog se sirf aglay sawal ki direction milti hai."
      ],
      [
        "zoya",
        "Independent technical review abhi pending hai. Draft hypothesis ko approved result kehna theek nahi."
      ]
    ]
  ],
  [
    "Bijli ka haq",
    "Noorabad community clinic ka staff room",
    "Aman ward priorities repeat karta hai; portable receiver unpowered paper exercise rehta hai.",
    [
      [
        "aman",
        "Emergency lights, dawa ki cooling aur mareez sab se pehle. Library inquiry ke liye clinic backup nahi milega."
      ],
      [
        "rayan",
        "Receiver ka sirf paper dry-run hai. Separate supply aur safety clearance ke baghair switch nahi dabega."
      ],
      [
        "laila",
        "Hum evidence ka kaam slow kar sakte hain, lekin kisi patient ki safety ko risk mein nahi dalenge."
      ],
      [
        "meher",
        "Is boundary ko har handoff note mein dobara likhungi, taake koi approval ka ghalat dawa na kare."
      ]
    ]
  ],
  [
    "Aam baat",
    "Library ka public community notice board",
    "Team neutral clarification draft banati hai lekin publish nahi karti.",
    [
      [
        "aman",
        "Afwah keh rahi hai ke index chori hua. Hamari observation missing page aur pending inquiry tak mehdood hai."
      ],
      [
        "zoya",
        "Draft notice abhi issue nahi hoga. Witness consent, library review aur authorized sign-off pehle chahiye."
      ],
      [
        "meher",
        "Public copy mein borrower details ya staff identities nahi hain. Sirf source labels aur unresolved points hain."
      ],
      [
        "laila",
        "Hum kisi par ilzam nahi lagayenge. Public inventory ka cross-check bhi missing page ka jawab nahi hai."
      ]
    ]
  ],
  [
    "Saaf hawala",
    "Library ka supervised exit register",
    "Public observations ka limited internal handoff hota hai; restricted records abhi pending hain.",
    [
      [
        "meher",
        "Public edition observations ki do numbered copies hain. Originals library mein hain aur missing page ab bhi absent hai."
      ],
      [
        "zoya",
        "Written request ka receipt permission nahi. Private ledger band rahega jab tak lawful jawab nahi milta."
      ],
      [
        "rayan",
        "Agla qadam copies ki independent custody review hai. Signal ka source abhi bhi unknown hai."
      ],
      [
        "laila",
        "Tadbeer ka matlab qanooni raasta aur saaf uncertainty hai. Hum aglay saboot ka intezar karenge."
      ]
    ]
  ]
]


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def validate_episode_eight(script: dict) -> None:
    """Reject rehashed tampering, false approvals, chronology drift and spoilers."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][7]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP007",
        "previous_episode_sha256": _previous_episode_sha256(),
        "source_outline_sha256": manifest["sha256"],
        "story_day": episode["story_day"],
        "source_event": episode["event"],
        "source_handoff": episode["handoff"],
        "episode_beat": episode["beat"],
        "language": "Pakistani Roman Urdu",
        "approval": "editorial_draft_not_reviewed",
        "human_reviewed": False,
        "spoken_duration_verified": False,
        "rendered": False,
        "planned_seconds": len(SCENES) * SCENE_SECONDS,
        "known_revelations": episode["revelations_known"],
        "carried_forward": CARRY_FORWARD,
    }
    if set(script) != set(expected) | {"scenes", "sha256"}:
        raise ValueError("invalid_schema")
    if any(type(script.get(key)) is not type(value) or script[key] != value
           for key, value in expected.items()):
        raise ValueError("false_completion_or_provenance")
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != len(SCENES):
        raise ValueError("scene_count")
    for number, (scene, authored) in enumerate(zip(scenes, SCENES), 1):
        title, location, action, dialogue = authored
        required = {
            "number": number, "title": title, "location": location, "action": action,
            "start_second": (number - 1) * SCENE_SECONDS,
            "planned_seconds": SCENE_SECONDS,
            "dialogue": [{"speaker": speaker, "text": line} for speaker, line in dialogue],
        }
        if not isinstance(scene, dict) or scene != required:
            raise ValueError("unreviewed_scene_change")
        if len(dialogue) != 4 or any(speaker not in SPEAKERS or len(line) < 35
                                     for speaker, line in dialogue):
            raise ValueError("authored_dialogue_invalid")
    if script["known_revelations"] != [] or script["carried_forward"]["signal_source"] != "unknown":
        raise ValueError("premature_revelation")
    raw = {key: value for key, value in script.items() if key != "sha256"}
    if script.get("sha256") != hashlib.sha256(_canonical(raw)).hexdigest():
        raise ValueError("revision_digest")


def episode_eight_script() -> dict:
    """Return a fresh EP008 draft linked to the immutable EP007 revision."""
    manifest = series_manifest()
    episode = manifest["episodes"][7]
    draft = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP007",
        "previous_episode_sha256": _previous_episode_sha256(),
        "source_outline_sha256": manifest["sha256"],
        "story_day": episode["story_day"],
        "source_event": episode["event"],
        "source_handoff": episode["handoff"],
        "episode_beat": episode["beat"],
        "language": "Pakistani Roman Urdu",
        "approval": "editorial_draft_not_reviewed",
        "human_reviewed": False,
        "spoken_duration_verified": False,
        "rendered": False,
        "planned_seconds": len(SCENES) * SCENE_SECONDS,
        "known_revelations": deepcopy(episode["revelations_known"]),
        "carried_forward": deepcopy(CARRY_FORWARD),
        "scenes": [
            {"number": i, "title": title, "location": location, "action": action,
             "start_second": (i - 1) * SCENE_SECONDS, "planned_seconds": SCENE_SECONDS,
             "dialogue": [{"speaker": speaker, "text": line} for speaker, line in turns]}
            for i, (title, location, action, turns) in enumerate(SCENES, 1)
        ],
    }
    draft["sha256"] = hashlib.sha256(_canonical(draft)).hexdigest()
    validate_episode_eight(draft)
    return draft
