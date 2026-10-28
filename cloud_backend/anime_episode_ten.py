"""Task 56 EP010: original Roman Urdu Hawala editorial draft, unreviewed.

Private library-copy custody handoff precedes offline antenna calibration planning.
Proposed 1,800 seconds are not measured speech or produced running time.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache

from cloud_backend.anime_episode_nine import episode_nine_script
from cloud_backend.anime_series import series_manifest

@lru_cache(maxsize=1)
def _previous_episode_sha256() -> str:
    """Cache only an immutable digest, never a mutable prior draft."""
    return episode_nine_script()["sha256"]


EPISODE_ID = "EP010"
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
  "library_copy_review": "independent_custodian_pending",
  "volunteer_hours": "limited_hours_logged_no_personal_data",
  "library_public_access": "supervised_only_not_restricted",
  "next_sequence": "offline_antenna_calibration_planning_only",
  "library_handoff_packet": "two_numbered_internal_copies_independent_review_pending",
  "library_request_deadline": "no_authorized_response_yet",
  "antenna_calibration": "offline_plan_only_not_started"
}
SCENES = [
  [
    "Band lifafa",
    "Observatory ka internal archive desk",
    "Meher public-library copies aur raw pulse ke alag envelopes ka inventory banati hai.",
    [
      [
        "meher",
        "Library ki do numbered public copies is packet mein hain; raw pulse ka asli source alag sealed envelope mein rahega."
      ],
      [
        "laila",
        "Har copy ke saath public edition aur observation waqt likho. Missing index page ka matn hamare paas nahi."
      ],
      [
        "zoya",
        "Internal receipt par sign hone ka matlab independent custody review nahi. Khali review box ko khali rehne do."
      ],
      [
        "rayan",
        "Do minute ki instrument correction sirf raw pulse par note hai; library ki print date ko is se mat badlo."
      ]
    ]
  ],
  [
    "Aik aur dastak",
    "Library ka public information counter",
    "Zoya restricted-records request ka sirf status poochti hai; kisi private file tak rasai nahi hoti.",
    [
      [
        "zoya",
        "Hum request ka status poochne aaye hain, borrower records dekhne nahi. Receipt approval letter nahi hota."
      ],
      [
        "meher",
        "Main sirf request reference aur pending status likhungi. Staff ka naam public notes mein nahi aayega."
      ],
      [
        "aman",
        "Log jawab ka intezar kar sakte hain; bina ijazat file kholna kisi be-gunah ko mushkil mein daal sakta hai."
      ],
      [
        "laila",
        "Agar written jawab nahi aaya to packet mein pending likhenge. Koi shortcut ya andaza saboot nahi banega."
      ]
    ]
  ],
  [
    "Hifazat ka safha",
    "Community clinic ka emergency planning board",
    "Aman investigation aur ward backup ke darmiyan boundary dobara record karta hai.",
    [
      [
        "aman",
        "Mareezon ki cooling, oxygen support aur emergency roshni sab se pehle hain; clinic backup test ko nahi milega."
      ],
      [
        "rayan",
        "Antenna calibration ka agla plan sirf disconnected bench par likhenge; live receiver aur network ko nahi chhoenge."
      ],
      [
        "laila",
        "Separate power aur safety clearance ke baghair koi switch nahi dabega. Corridor ki written permission bhi pending hai."
      ],
      [
        "meher",
        "Yeh hifazati shart handoff mein likh di hai; aglay episode mein bhi isay approval samajh kar badla nahi jayega."
      ]
    ]
  ],
  [
    "Do ghariyon ka raaz nahi",
    "Observatory ka disconnected clock bench",
    "Rayan do alag time references ko label karta hai, unko mila kar source ka dawa nahi karta.",
    [
      [
        "rayan",
        "Instrument clock ka raw offset do minute hai, magar library edition ki tareekh alag provenance rakhti hai."
      ],
      [
        "zoya",
        "In dono ko mila kar transmitter, shakhs ya sabotage ka nateeja nikalna abhi ghair-zimmedarana hoga."
      ],
      [
        "meher",
        "Har observation ki asal ghari aur correction note alag columns mein hain; source record replace nahi hua."
      ],
      [
        "laila",
        "Hamara agla sawal calibration ke tareeqe par hai, signal ke source par final faisla abhi mumkin nahi."
      ]
    ]
  ],
  [
    "Awaz aur afwah",
    "Noorabad community reading corner",
    "Aman unissued public notice ke bare mein neutral guftagu karta hai.",
    [
      [
        "aman",
        "Mohallay mein log missing page ki kahani bana rahe hain; humne chori ya kisi ka jurm sabit nahi kiya."
      ],
      [
        "laila",
        "Gawahon ki razamandi aur authorized review ke baghair public notice draft hi rahega, share nahi hoga."
      ],
      [
        "zoya",
        "Public edition copies se kisi borrower ya staff member ki pehchan nikalna bhi ghalat hoga."
      ],
      [
        "meher",
        "Main private packet par unreviewed likh rahi hoon, taake kisi ko yeh final report na lage."
      ]
    ]
  ],
  [
    "Darmiyani nishan",
    "Library ka supervised public catalog table",
    "Public edition cross-check ka gap unanswered rehta hai; original register wahi rehta hai.",
    [
      [
        "meher",
        "Do public editions ke serial gap ka reference hai, lekin missing page ki koi verified copy nahi mili."
      ],
      [
        "rayan",
        "Gap ka antenna frequency se taalluq sabit nahi. Calibration ko alag, offline sawal samajhna hoga."
      ],
      [
        "zoya",
        "Restricted condition history abhi staff review ke baghair band hai. Hum kisi private shelf ko nahi kholenge."
      ],
      [
        "laila",
        "Original register library mein hi rehna chahiye; hamari numbered copies independent check ki muntazir hain."
      ]
    ]
  ],
  [
    "Zimmedari ka naam",
    "Observatory ka private custody review board",
    "Team review ke liye zimmedariyan likhti hai, lekin kisi ghair-hazir reviewer ka sign nahi banati.",
    [
      [
        "zoya",
        "Main request follow-up ki zimmedari leti hoon, magar independent reviewer ki tasdeeq abhi hasil nahi hui."
      ],
      [
        "meher",
        "Mere paas archive copy ki custody hai; Laila ke source envelope ko is packet se mix nahi karungi."
      ],
      [
        "aman",
        "Volunteer duty hours mehdood rahenge. Kisi gawah ki private pehchan review sheet par nahi likhenge."
      ],
      [
        "rayan",
        "Main antenna ke liye paper calibration checklist banaunga; koi live test, power draw ya access claim nahi."
      ]
    ]
  ],
  [
    "Agla hawala",
    "Observatory ka sealed handoff shelf",
    "EP010 library sequence ko pending review ke saath close karta hai aur EP011 ke offline antenna planning beat ko handoff deta hai.",
    [
      [
        "laila",
        "Library ka suraagh abhi adhoora hai. Hum sirf numbered copies aur unanswered requests aglay zimmedar logon ko de rahe hain."
      ],
      [
        "meher",
        "Internal packet sealed hai; independent custody sign, missing index page aur restricted ledger ka jawab abhi baqi hai."
      ],
      [
        "zoya",
        "Public notice unissued, witness consent pending aur corridor access unapproved rahegi; yeh handoff permission nahi."
      ],
      [
        "rayan",
        "Agla kaam toote antenna ki offline calibration planning hai, na signal source ka dawa aur na live receiver test."
      ]
    ]
  ]
]


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def validate_episode_ten(script: dict) -> None:
    """Reject rehashed tampering, false approvals, chronology drift and spoilers."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][9]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP010",
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


def episode_ten_script() -> dict:
    """Return a fresh EP010 draft linked to the immutable EP009 revision."""
    manifest = series_manifest()
    episode = manifest["episodes"][9]
    draft = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP010",
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
    validate_episode_ten(draft)
    return draft
