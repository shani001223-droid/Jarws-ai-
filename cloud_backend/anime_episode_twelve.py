"""Task 56 EP012: original Roman Urdu lawful-access Rukawat editorial draft.

An incomplete equipment access request is not approval, denial, a live
calibration, measured bearing, or 30 minutes of verified performance.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache

from cloud_backend.anime_episode_eleven import episode_twelve_script
from cloud_backend.anime_series import series_manifest


@lru_cache(maxsize=1)
def _previous_episode_sha256() -> str:
    """Cache an immutable digest only, not mutable prior script objects."""
    return episode_twelve_script()["sha256"]


EPISODE_ID = "EP012"
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
    "next_sequence": "lawful_alternative_access_plan_pending",
    "library_handoff_packet": "two_numbered_internal_copies_independent_review_pending",
    "library_request_deadline": "no_authorized_response_yet",
    "antenna_calibration": "offline_reference_checklist_drafted_not_tested",
    "antenna_fixture": "visible_bend_unverified_cause_not_adjusted",
    "signal_direction": "not_measured_source_unknown",
    "power_authorization": "separate_power_and_safety_clearance_pending",
    "antenna_access_obstacle": "incomplete_annex_no_access_or_denial",
    "safety_review": "requested_not_authorized"
}
SCENES = [
    [
        "Band darwaza",
        "Observatory ka authorized reception desk",
        "Team ko equipment corridor ki application mein missing safety annex ka pata chalta hai; koi access nahi milta.",
        [
            [
                "zoya",
                "Reception par application incomplete mark hui hai. Is par approval ka stamp nahi, aur hum band corridor mein qadam nahi rakhenge."
            ],
            [
                "rayan",
                "EP011 ki paper checklist sirf proposal hai. Main antenna ko on karne ya fixture ko seedha karne ki koshish nahi karunga."
            ],
            [
                "laila",
                "Humein pata karna hai kaunsa annex chahiye, magar kisi staff ki private detail ya naam report mein nahi likhna."
            ],
            [
                "meher",
                "Main receipt number ko internal file mein rakhungi. Incomplete application ko final refusal ya ijazat dono nahi kahenge."
            ]
        ]
    ],
    [
        "Teen alag ijazatein",
        "Observatory ka public notice board",
        "Zoya equipment, corridor aur electrical safety ke separate forms ko compare karti hai.",
        [
            [
                "zoya",
                "Equipment authority, corridor entry aur separate power safety ke forms alag hain. Aik request doosri ki jagah nahi le sakti."
            ],
            [
                "aman",
                "Clinic ki oxygen aur emergency roshni ka budget yahan istemal nahi hoga. Hum bina bijli ke bhi saboot ki hifazat kar sakte hain."
            ],
            [
                "rayan",
                "Mount par bent nishan ab bhi unverified hai. Qualified inspection ke baghair koi screw ya cable touch nahi karna."
            ],
            [
                "laila",
                "Aaj ki rukawat paperwork aur safety ki hai, kisi sabit shuda saazish ki nahi. Hamara record isi had tak rahe."
            ]
        ]
    ],
    [
        "Ghalat nuskha",
        "Community library ka supervised desk",
        "Public inventory aur antenna annex ki milti-julti numbering ek ghalat shortcut paida karti hai.",
        [
            [
                "meher",
                "Library ke public catalog par milta julta reference number hai, lekin yeh antenna permission ka replacement nahi."
            ],
            [
                "rayan",
                "Raw pulse ke clock mein do minute ka offset hai. Catalog ki date ko is se jor kar signal ka rukh nahi nikaal sakte."
            ],
            [
                "zoya",
                "Restricted borrower record aur maintenance history dono ki alag written requests pending hain; hum unhein khol nahi sakte."
            ],
            [
                "laila",
                "Missing index page abhi missing hai. Kisi photocopy se uski asal ibarat bana kar saboot mein shamil mat karna."
            ]
        ]
    ],
    [
        "Bina rukh ki lakeer",
        "Observatory ka public map corner",
        "Team hypothetical sketch ko measurement se alag label karti hai.",
        [
            [
                "rayan",
                "Public map par nahr ki lakeer nazar aati hai, magar is se na antenna bearing milti hai na signal ka source."
            ],
            [
                "meher",
                "Main sketch par hypothetical aur unmeasured dono likhungi. Aaj koi receiver reading ya frequency log nahi bana."
            ],
            [
                "aman",
                "Agar safety annex poora na ho to hum test postpone karenge. Mareezon ki zaroorat kisi mystery se kam nahi."
            ],
            [
                "zoya",
                "Is naqshay ki wajah se tunnel ya corridor ka gate nahi khulta. Legal access ka jawab abhi baqi hai."
            ]
        ]
    ],
    [
        "Do lifafay",
        "Observatory ka sealed archive shelf",
        "Meher antenna forms ko do numbered library copies se alag rakhti hai.",
        [
            [
                "meher",
                "Do numbered library envelopes seal ke saath apni jagah hain. Naye antenna forms unke andar nahi jayenge."
            ],
            [
                "laila",
                "Independent custodian ne abhi review sign nahi kiya. Hum unki taraf se tasdeeq ya approval likh nahi sakte."
            ],
            [
                "zoya",
                "Witness consent aur staff privacy bhi pending hain. Kisi ko notice bhejna ya public post karna abhi mana hai."
            ],
            [
                "rayan",
                "Antenna ka visible bend sirf observation hai. Usay missing page, pulse ya sabotage ka saboot mat bana dena."
            ]
        ]
    ],
    [
        "Aman ka sawal",
        "Community clinic ka planning table",
        "Aman team ko proposed test ke practical human costs yaad dilata hai.",
        [
            [
                "aman",
                "Ward mein cooling, oxygen aur lights ke liye har unit zaroori hai. Separate authorized supply ke baghair test ka sawal hi nahi."
            ],
            [
                "laila",
                "Hum apne volunteer hours likhenge magar mareezon ya gawahon ka personal data ikattha nahi karenge."
            ],
            [
                "rayan",
                "Paper checklist mein emergency stop aur qualified engineer ka review bhi likha hai. Yeh sirf draft hai, performed test nahi."
            ],
            [
                "meher",
                "Main time estimate ko planned kahungi, measured nahi. Hum ne na calibration ki na kisi signal ki direction dekhi."
            ]
        ]
    ],
    [
        "Khali dastakhat",
        "Observatory ka authorized filing counter",
        "Team missing annex aur review request ko signed draft ke taur par jama karne ka plan banati hai.",
        [
            [
                "zoya",
                "Hum forms ki checklist tayyar kar sakte hain, lekin submission receipt se permission automatically nahi milti."
            ],
            [
                "meher",
                "Jab tak actual authorized jawab nahi aata, status pending rahega. Main blank signature box ko blank hi chhorungi."
            ],
            [
                "rayan",
                "Qualified inspection ka waqt bhi confirm nahi. Kisi unverified calendar entry ko completed safety clearance mat samajhna."
            ],
            [
                "laila",
                "Public notice aur independent library review dono alag approvals hain. Hum kisi deadline ko approval mein tabdeel nahi karenge."
            ]
        ]
    ],
    [
        "Agla raasta",
        "Noorabad ka community reading corner",
        "EP012 unresolved legal access obstacle ke saath EP013 ke lawful alternate plan ko handoff karta hai.",
        [
            [
                "laila",
                "Aaj humne band raaste ko shortcut se nahi khola. EP013 mein sirf qanooni aur kam-khatre wala alternate plan dekhenge."
            ],
            [
                "zoya",
                "Corridor, equipment aur power ki written clearances abhi pending hain. Koi restricted gate khola nahi gaya."
            ],
            [
                "meher",
                "Library copies sealed hain, missing index page nahi mila aur independent custodian ka jawab abhi nahi aaya."
            ],
            [
                "rayan",
                "Signal source unknown, direction unmeasured aur antenna disconnected hai. Yeh sach aglay episode ki bunyaad hai."
            ]
        ]
    ]
]

def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def validate_episode_twelve(script: dict) -> None:
    """Reject changed dialogue even if rehashed, fake approvals and spoilers."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][11]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP011",
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


def episode_twelve_script() -> dict:
    """Return a fresh EP012 draft linked to immutable EP011 and series outline."""
    manifest = series_manifest()
    episode = manifest["episodes"][10]
    draft = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP011",
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
    validate_episode_twelve(draft)
    return draft
