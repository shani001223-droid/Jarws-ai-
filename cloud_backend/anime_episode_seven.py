"""Task 56 EP007: original Roman Urdu Rukawat editorial draft, unreviewed.

Missing index page history is restricted; the team records conflicting public
dates and files a narrow lawful records request. No approvals or publication.
Planned 1,800 seconds are not measured speech or produced running time.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache

from cloud_backend.anime_episode_six import episode_six_script
from cloud_backend.anime_series import series_manifest

@lru_cache(maxsize=1)
def _previous_episode_sha256() -> str:
    """Cache only an immutable digest, never a mutable prior draft."""
    return episode_six_script()["sha256"]


EPISODE_ID = "EP007"
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
  "next_sequence": "lawful_public_inventory_crosscheck_pending"
}
SCENES = [
  [
    "Band daftar",
    "Noorabad public library ka reference desk",
    "Staff missing index ki condition history ko restricted maintenance ledger mein batata hai; team formal request ka raasta poochti hai.",
    [
      [
        "laila",
        "Hum missing page ki history poochh rahe hain, kisi par ilzam nahi laga rahe. Kya formal request ka raasta hai?"
      ],
      [
        "zoya",
        "Public register dekhna aur restricted condition ledger mangna do alag kaam hain. Written permission ka intezar hoga."
      ],
      [
        "meher",
        "EP006 ka condition note original shelf record se alag hai. Main dono ki provenance saaf rakhungi."
      ],
      [
        "rayan",
        "Ledger band hai to main technical conclusion nahi nikalunga. Sirf pending sawalat ki list banaunga."
      ]
    ]
  ],
  [
    "Do tareekhein",
    "Library ka public notice board",
    "Public catalog aur printed inventory ki edition dates mukhtalif hain; team discrepancy note karti hai, sabotage nahi.",
    [
      [
        "meher",
        "Public catalog aur printed inventory ki tareekh alag hain. Yeh mismatch hai, missing page ka sabab nahi."
      ],
      [
        "laila",
        "Kisi ek tareekh ko chupke se sahi maan lena ghalti hogi. Dono raw entries alag note karo."
      ],
      [
        "aman",
        "Library staff ko bina saboot zimmedar thehrana logon ka aitbaar tor sakta hai. Alfaaz ehtiyat se chuno."
      ],
      [
        "zoya",
        "Agar correction ka official record hai to poochhenge; private register kholne ka pressure nahi dalenge."
      ]
    ]
  ],
  [
    "Kamzor jild",
    "Library ka supervised reading table",
    "Staff damaged binding ki wajah se handling rokta hai; team visible condition hi record karti hai.",
    [
      [
        "zoya",
        "Binding kamzor hai aur staff ne mazeed handling roki hai. Investigation ke liye kitab ko nuksan nahi pohanchayenge."
      ],
      [
        "rayan",
        "Main missing safhay ko tasavvur se fill nahi karunga. Bina original record koi frequency confirm nahi hoti."
      ],
      [
        "laila",
        "Rukawat ka matlab yeh nahi ke kisi ne raaz chhupaya. Pehle conservation report ka public status poochho."
      ],
      [
        "meher",
        "Original register library mein hi rahega. Hamare paas supervised observation ka signed note hai."
      ]
    ]
  ],
  [
    "Darkhwast",
    "Library administration ka public enquiry counter",
    "Zoya narrow records request taiyar karti hai, borrower names aur private data exclude karti hai.",
    [
      [
        "zoya",
        "Darkhwast mein sirf condition-history dates aur missing page ka status mangenge, borrower names bilkul nahi."
      ],
      [
        "laila",
        "Request bhejne se approval nahi mil jata. Jawab aane tak restricted records untouched rahenge."
      ],
      [
        "meher",
        "Internal handoff receipt attach kar sakti hoon, magar usay independent technical clearance nahi kahungi."
      ],
      [
        "aman",
        "Jawab der se aaye to bhi clinic ka backup is inquiry ke liye istemal nahi hoga."
      ]
    ]
  ],
  [
    "Ghalat qiyas",
    "Observatory ka offline review table",
    "Rayan public dates aur pulse notes compare karta hai; clocks non-comparable hain, hypothesis untested rehti hai.",
    [
      [
        "rayan",
        "Catalog ki tareekh ko radio pulse ke waqt se jorna abhi mumkin nahi. Dono records ki clocks alag hain."
      ],
      [
        "meher",
        "Do minute ka correction sirf hamare instrument ke liye documented hai, library record par apply nahi hota."
      ],
      [
        "laila",
        "Agar hypothesis fail ho rahi hai to usay fail likho. Sahi jawab dhoondhna hai, kahani banana nahi."
      ],
      [
        "zoya",
        "Independent reviewer ko mismatch aur uncertainty dono dena. Similarity transmitter ki pehchan nahi hai."
      ]
    ]
  ],
  [
    "Ward ki awaaz",
    "Noorabad community clinic ka corridor",
    "Aman emergency load ka priority note banata hai; receive-only test bhi safety approval tak pending hai.",
    [
      [
        "aman",
        "Ward mein dawa ki cooling aur emergency lights pehle hain. Experimental receiver ko backup supply nahi milegi."
      ],
      [
        "rayan",
        "Portable test abhi paper dry-run hai. Safety sign-off aur alag power ke baghair switch on nahi karunga."
      ],
      [
        "laila",
        "Library ki rukawat ka jawab chahiye, magar mareezon ki qeemat par nahi. Yeh report mein saaf likho."
      ],
      [
        "meher",
        "Clinic-first boundary ko next handoff mein repeat karungi, taake koi isay optional na samjhe."
      ]
    ]
  ],
  [
    "Afwah",
    "Library ka community information corner",
    "Missing page par afwah phailti hai; team witness privacy ke saath neutral draft clarification banati hai.",
    [
      [
        "aman",
        "Log keh rahe hain safha jaan boojh kar hataya gaya. Hamare paas is daaway ka saboot nahi."
      ],
      [
        "laila",
        "Public note mein sirf verified missing page aur pending records request likhenge, kisi par shak nahi."
      ],
      [
        "zoya",
        "Notice abhi draft hai, issued nahi. Consent aur authorized review ke baghair kuch share nahi hoga."
      ],
      [
        "meher",
        "Private borrower details ya staff names ko public copy mein bilkul nahi laungi."
      ]
    ]
  ],
  [
    "Intezaar ka saboot",
    "Library ka supervised exit counter",
    "Team request receipt ko permission se alag rakhti hai; missing page history aur signal source unresolved hain.",
    [
      [
        "meher",
        "Public catalog aur condition observation ki copy alag envelopes mein hain. Restricted ledger abhi nahi mila."
      ],
      [
        "zoya",
        "Written request ka receipt approval nahi hota. Jawab aane tak kisi band record ko nahi chhooenge."
      ],
      [
        "rayan",
        "Agla qadam public inventory ka lawful cross-check hai. Signal ka source abhi unknown hai."
      ],
      [
        "laila",
        "Rukawat ko shortcut se nahi, saaf evidence se paar karenge. Agla qanooni raasta dhoondna hoga."
      ]
    ]
  ]
]


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def validate_episode_seven(script: dict) -> None:
    """Reject rehashed tampering, false approvals, chronology drift and spoilers."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][6]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP006",
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


def episode_seven_script() -> dict:
    """Return a fresh EP007 draft linked to the immutable EP006 revision."""
    manifest = series_manifest()
    episode = manifest["episodes"][6]
    draft = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP006",
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
    validate_episode_seven(draft)
    return draft
