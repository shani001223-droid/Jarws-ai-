"""Task 56 EP011: original Roman Urdu antenna Ishara editorial draft, unreviewed.

A disconnected visual inspection and paper calibration plan are NOT a live
calibration, a measured signal direction, an approval or 30 minutes of speech.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache

from cloud_backend.anime_episode_ten import episode_ten_script
from cloud_backend.anime_series import series_manifest


@lru_cache(maxsize=1)
def _previous_episode_sha256() -> str:
    """Cache an immutable digest only, not mutable prior script objects."""
    return episode_ten_script()["sha256"]


EPISODE_ID = "EP011"
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
    "next_sequence": "antenna_calibration_access_obstacle_pending",
    "library_handoff_packet": "two_numbered_internal_copies_independent_review_pending",
    "library_request_deadline": "no_authorized_response_yet",
    "antenna_calibration": "offline_reference_checklist_drafted_not_tested",
    "antenna_fixture": "visible_bend_unverified_cause_not_adjusted",
    "signal_direction": "not_measured_source_unknown",
    "power_authorization": "separate_power_and_safety_clearance_pending"
}
SCENES = [
    [
        "Khamosh antenna",
        "Observatory ka band equipment room",
        "Rayan aur Laila bina power diye purane antenna ki mounting ko dekhte hain.",
        [
            [
                "rayan",
                "Yeh purana antenna filhal disconnected hai. Main sirf bracket ki visible halat aur label note karunga, isay chalaunga nahi."
            ],
            [
                "laila",
                "EP010 ka library packet alag sealed hai; is hardware ko us packet ka proof ya source samajhna abhi jaldi hogi."
            ],
            [
                "meher",
                "Main inspection ko observational draft likhungi. Kisi engineer ki clearance ya independent sign hamare paas nahi."
            ],
            [
                "zoya",
                "Band corridor ki written ijazat pending hai, is liye hum sirf is authorized equipment room tak mehdood rahenge."
            ]
        ]
    ],
    [
        "Tedha nishan",
        "Observatory ka disconnected workbench",
        "Antenna ke purane fixture par bent alignment mark milta hai, magar sabab unknown hai.",
        [
            [
                "rayan",
                "Mount par tedha nishan nazar aa raha hai, lekin yeh damage kab hua aur kis wajah se hua, hum nahi jaante."
            ],
            [
                "aman",
                "Is nishan ko sabotage kehna theek nahi. Agar loose metal ho to kisi ko haath lagane se pehle safety check chahiye."
            ],
            [
                "laila",
                "Photo bhi sirf internal draft mein rahegi; bina permission kisi ki identity ya equipment history publish nahi hogi."
            ],
            [
                "meher",
                "Original bracket ko hilaaye baghair observed position likh rahi hoon; replacement part abhi order nahi hua."
            ]
        ]
    ],
    [
        "Do daftar",
        "Observatory ka private archive table",
        "Meher library packet aur antenna inspection ko do alag provenance records mein rakhti hai.",
        [
            [
                "meher",
                "Do numbered library copies apne seal ke saath rahengi. Antenna inspection ka naya note unki custody chain mein ghusega nahi."
            ],
            [
                "zoya",
                "Restricted library record request ka receipt ab bhi permission nahi. Independent custodian ki tasdeeq abhi baqi hai."
            ],
            [
                "rayan",
                "Library ki edition date aur raw pulse ke do minute clock offset alag observations hain; unko jor kar rukh nahi nikaal sakte."
            ],
            [
                "laila",
                "Missing index page abhi nahi mila. Antenna ka visible bend us page ki kahani ko na sabit karta hai na jhutlata hai."
            ]
        ]
    ],
    [
        "Bina bijli ka naqsha",
        "Community clinic ka safe planning corner",
        "Aman aur Rayan ek paper-only calibration checklist par patient-safety boundary likhte hain.",
        [
            [
                "aman",
                "Ward ki cooling, oxygen aur emergency roshni pehla haq rakhti hain. Clinic backup se antenna ko aik watt bhi nahi milega."
            ],
            [
                "rayan",
                "Checklist mein pehle separate power approval, qualified inspection aur disconnected reference check likha hai; live test nahi."
            ],
            [
                "zoya",
                "Written corridor access, equipment authority aur risk review teen alag approvals hain. Aaj un mein se koi hasil nahi hui."
            ],
            [
                "laila",
                "Hum checklist ko action report nahi kahenge. Plan ka hona calibration ho jana nahi hota, yeh saaf likho."
            ]
        ]
    ],
    [
        "Purani lakeer",
        "Observatory ka public floor plan board",
        "Team approved public plan par antenna ki purani orientation ka sirf hypothetical sketch banati hai.",
        [
            [
                "rayan",
                "Public floor plan par purani orientation ka aik mark hai, magar is se aaj ke signal ki direction measure nahi hoti."
            ],
            [
                "meher",
                "Sketch ke kone par hypothetical likh rahi hoon; raw receiver data aur independent comparison dono unavailable hain."
            ],
            [
                "aman",
                "Nahr ka zikr purane naqshay mein hai, lekin hum bina measurement usay signal ka rukh announce nahi karenge."
            ],
            [
                "zoya",
                "Koi restricted maintenance passage is plan ki wajah se khul nahi jata. Us ki written request abhi pending hai."
            ]
        ]
    ],
    [
        "Gawahon ka sukoon",
        "Noorabad ka community reading corner",
        "Aman afwahon ke darmiyan neutral update ka draft banata hai, share nahi karta.",
        [
            [
                "aman",
                "Log pooch rahe hain ke antenna chal gaya kya. Main keh raha hoon sirf offline planning hui hai, koi live test nahi."
            ],
            [
                "laila",
                "Public notice abhi issue nahi hoga. Gawahon ki razamandi aur authorized review ke baghair koi naam bahar nahi jayega."
            ],
            [
                "zoya",
                "Staff aur borrower ki private maloomat humne collect nahi ki. Unki khamoshi ko approval ya evidence mat samjho."
            ],
            [
                "meher",
                "Main is update ko private draft folder mein rakhungi, public announcement ya published report mein nahi."
            ]
        ]
    ],
    [
        "Chaar shartein",
        "Observatory ka equipment safety board",
        "Rayan proposed calibration ko authorization aur observation ke separate stages mein baantta hai.",
        [
            [
                "rayan",
                "Pehli shart safe mechanical inspection, doosri separate power, teesri written access aur chauthi qualified review hai."
            ],
            [
                "aman",
                "Agar in mein se aik bhi na mile to hum receiver on nahi karenge. Clinic ki zaroorat hamesha pehle rahegi."
            ],
            [
                "zoya",
                "Independent custodian ko library copies dikhana bhi uski razamandi aur proper receipt ke baad hoga, aaj nahi."
            ],
            [
                "laila",
                "Abhi koi bearing, frequency ya source direction verified nahi. Checklist par pending ka lafz saaf nazar aana chahiye."
            ]
        ]
    ],
    [
        "Agla imtehan",
        "Observatory ka sealed handoff shelf",
        "EP011 paper calibration plan ko pending gates ke saath band karta hai aur EP012 ke access obstacle ka raasta banata hai.",
        [
            [
                "meher",
                "Library packet ke dono numbered envelopes sealed hain; antenna notes un se alag hain aur independent review pending hai."
            ],
            [
                "rayan",
                "Bent fixture aur reference sketch ko verify karne ke liye approved inspection chahiye. Aaj koi calibration run nahi hua."
            ],
            [
                "zoya",
                "Written corridor access aur equipment clearance ke jawab abhi nahi aaye; agla qadam inhi rukawaton ko qanooni tareeqe se suljhana hai."
            ],
            [
                "laila",
                "Signal ka source unknown hai, nahr ki direction abhi unmeasured hai. Hum sirf sachay pending notes aglay din le ja rahe hain."
            ]
        ]
    ]
]


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def validate_episode_eleven(script: dict) -> None:
    """Reject changed dialogue even if rehashed, fake approvals and spoilers."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][10]
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


def episode_eleven_script() -> dict:
    """Return a fresh EP011 draft linked to immutable EP010 and series outline."""
    manifest = series_manifest()
    episode = manifest["episodes"][10]
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
    validate_episode_eleven(draft)
    return draft
