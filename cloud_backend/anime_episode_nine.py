"""Task 56 EP009: original Roman Urdu Qeemat editorial draft, unreviewed.

Time, trust and clinic-first priorities are costed without fabricated approvals.
Planned 1,800 seconds are not measured speech or produced running time.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache

from cloud_backend.anime_episode_eight import episode_eight_script
from cloud_backend.anime_series import series_manifest

@lru_cache(maxsize=1)
def _previous_episode_sha256() -> str:
    """Cache only an immutable digest, never a mutable prior draft."""
    return episode_eight_script()["sha256"]


EPISODE_ID = "EP009"
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
  "next_sequence": "custody_and_cost_handoff_pending"
}
SCENES = [
  [
    "Der ka hisaab",
    "Observatory ka offline planning table",
    "Team public inventory inquiry ke baad waqt aur volunteer shifts ka kharcha likhti hai.",
    [
      [
        "laila",
        "Kal ki library visit ne poora din le liya. Ab har aglay qadam ki qeemat waqt aur zimmedari se naapni hogi."
      ],
      [
        "meher",
        "Maine sirf public edition numbers likhe hain. Missing index page ka matn hamare paas nahi, aur main kuch gadhungi nahi."
      ],
      [
        "rayan",
        "Do minute ki instrument correction ko catalog print dates se milana ghalat hoga. Hamein dono clocks alag rakhni hain."
      ],
      [
        "zoya",
        "Independent review aur restricted request abhi pending hain. Is der ko bhi case notes mein wazeh darj karo."
      ]
    ]
  ],
  [
    "Do nuskhe",
    "Library ka supervised reference table",
    "Public entries ki numbered copies banti hain; original register library mein rehta hai.",
    [
      [
        "meher",
        "Har public entry ke saath edition, page aur observation waqt likh diya. Original register library se bahar nahi jayega."
      ],
      [
        "zoya",
        "Do copies ka hona independent approval nahi. Jab tak doosra custodian check na kare, yeh internal drafts hi rahenge."
      ],
      [
        "laila",
        "Staff ki supervised access sirf khuli shelves tak thi. Restricted ledger ke liye written jawab ka intezar rahega."
      ],
      [
        "aman",
        "Volunteer ki mehnat bhi amanat hai. Be-wajah unhein phir library bula kar afwah ko hawa nahi denge."
      ]
    ]
  ],
  [
    "Band jawab",
    "Library ka public information counter",
    "Formal request ka receipt maujood hai magar access decision abhi pending hai.",
    [
      [
        "zoya",
        "Request ka receipt mere paas hai, magar approval ka letter nahi. Hum private borrower record ya maintenance ledger nahi kholenge."
      ],
      [
        "rayan",
        "Agar jawab dair se aata hai to instrument ki calibration alag offline rakhenge; live network ko chhoona zaroori nahi."
      ],
      [
        "meher",
        "Main pending date aur request reference likhungi. Kisi staff member ka naam public draft mein nahi aayega."
      ],
      [
        "laila",
        "Rukawat ki qeemat der hai, lekin bina ijazat record lena hamare saboot ko aur kamzor karega."
      ]
    ]
  ],
  [
    "Aitbar ki qeemat",
    "Noorabad community reading corner",
    "Afwah ke darmiyan team neutral public note ko unissued draft hi rakhti hai.",
    [
      [
        "aman",
        "Mohallay mein log missing page ko chori keh rahe hain. Humne aisa kuch sabit nahi kiya, is liye ilzam nahi dena."
      ],
      [
        "laila",
        "Public notice abhi draft hai. Gawahon ki razamandi, library review aur authorized sign-off ke baghair kuch issue nahi hoga."
      ],
      [
        "meher",
        "Public copy se borrower data aur staff identities nikaal di hain. Ab bhi review pending hai, isay publish mat karo."
      ],
      [
        "zoya",
        "Aitbar ko jaldbaazi se nahi bachaya ja sakta. Jo unknown hai, woh unknown hi batana hoga."
      ]
    ]
  ],
  [
    "Ward ki shift",
    "Community clinic ka handover desk",
    "Aman volunteer hours aur patient-first emergency power priority record karta hai.",
    [
      [
        "aman",
        "Ward mein dawa ki cooling aur emergency lights ko pehli priority milegi. Investigation ke liye clinic backup kabhi nahi denge."
      ],
      [
        "rayan",
        "Portable receiver abhi paper dry-run hai. Separate supply, safety clearance aur written corridor access sab pending hain."
      ],
      [
        "laila",
        "Aman ki shift khatam hone tak hum intezar kar sakte hain. Kisi mareez ki safety hamari deadline se kam nahi."
      ],
      [
        "meher",
        "Main volunteer hours aur clinic boundary ko internal handoff mein likh rahi hoon, taake reviewer ghalat na samjhe."
      ]
    ]
  ],
  [
    "Alag ghariyan",
    "Observatory ka disconnected archive bench",
    "Raw pulse aur public records alag envelopes mein rehte hain; time mismatch source nahi batata.",
    [
      [
        "rayan",
        "Raw pulse mein instrument ki do minute correction note hai. Library print date par woh correction apply nahi hoti."
      ],
      [
        "meher",
        "Archive copy aur source recording ki custody alag log mein hai. Public inventory notes unka replacement nahi."
      ],
      [
        "zoya",
        "Technical corroboration abhi nahi aayi. Do alag dates ko mila kar kisi relay ya shakhs ko zimmedar nahi keh sakte."
      ],
      [
        "laila",
        "Signal ka source abhi unknown hai. Hum sirf next lawful question likh sakte hain, final jawab nahi."
      ]
    ]
  ],
  [
    "Khali kursi",
    "Library ka internal review appointment board",
    "Independent custody review abhi pending hai; koi jhooti signature add nahi hoti.",
    [
      [
        "meher",
        "Numbered copies ready hain, lekin independent custodian ka signed review abhi nahi mila. Main blank jagah blank rakhungi."
      ],
      [
        "zoya",
        "Public inventory ka gap missing page ki recovery nahi. Review mein source labels aur custody chain hi dekhi jayegi."
      ],
      [
        "aman",
        "Volunteer log mein sirf duty hours hain, private gawahon ke naam nahi. Kisi ko afwah ki wajah se nuksan na ho."
      ],
      [
        "rayan",
        "Jab tak review na ho, calibration ke results bhi sirf offline working notes rahenge, public conclusion nahi."
      ]
    ]
  ],
  [
    "Hawala ki tayyari",
    "Observatory ka sealed internal handoff table",
    "Unreviewed copies aur limited-hours log aglay Hawala beat ke liye private custody mein rehte hain.",
    [
      [
        "laila",
        "Aaj humne waqt, bharosa aur energy ki qeemat dekhi. Magar saboot ko jaldi mein final nahi keh sakte."
      ],
      [
        "meher",
        "Public copy ke labels aur volunteer-hours log ko alag internal packets mein rakha hai; independent review pending hai."
      ],
      [
        "zoya",
        "Restricted ledger ka jawab, corridor ki written permission aur notice ka sign-off teeno abhi baqi hain."
      ],
      [
        "rayan",
        "Agla qadam sirf safe custody handoff hai. Na live receiver test hua, na missing page mila, na signal ka source pata chala."
      ]
    ]
  ]
]


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def validate_episode_nine(script: dict) -> None:
    """Reject rehashed tampering, false approvals, chronology drift and spoilers."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][8]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP008",
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


def episode_nine_script() -> dict:
    """Return a fresh EP009 draft linked to the immutable EP008 revision."""
    manifest = series_manifest()
    episode = manifest["episodes"][8]
    draft = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP008",
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
    validate_episode_nine(draft)
    return draft
