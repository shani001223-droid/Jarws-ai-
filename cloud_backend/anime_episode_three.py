"""Task 56 EP003: original Pakistani Roman Urdu editorial draft, not approved media.

Offline deterministic source. Planned scene seconds are not measured runtime.
"""
from __future__ import annotations
import hashlib
import json
from copy import deepcopy
from cloud_backend.anime_episode_two import episode_two_script
from cloud_backend.anime_series import series_manifest

EPISODE_ID = "EP003"
SCENE_SECONDS = 225
SPEAKERS = frozenset({"laila", "rayan", "meher", "aman", "zoya"})
CARRY_FORWARD = {
    "pulse_custody": "meher_archive_copy_and_laila_source",
    "clock_offset": "two_minutes_not_silently_corrected",
    "signal_source": "unknown",
    "clinic_priority": "patient_safety_before_receiver_test",
    "locked_corridor_access": "written_permission_pending",
    "missing_index_page": "not_reconstructed",
    "public_witness_consent": "required_before_disclosure",
}
SCENES = [
  [
    "Subah ka naya daftar",
    "Noorabad municipal public reading room",
    "Meher original packet aur do minute clock correction ko alag signed registers mein compare karti hai.",
    [
      [
        "laila",
        "Aaj hum purani file ko nahi badlenge. Nayi observation alag register mein likhenge."
      ],
      [
        "meher",
        "Mere paas sealed copy hai, magar missing page abhi bhi missing hai. Main usay khud nahi bharungi."
      ],
      [
        "zoya",
        "Public index ki sirf authorized copy dekho. Private witness data lene ki ijazat nahi hai."
      ],
      [
        "laila",
        "Jab tak clock verify nahi hoti, corrected waqt ko confirmed reading nahi kahenge."
      ]
    ]
  ],
  [
    "Clinic ka pehla haq",
    "Noorabad community clinic supply desk",
    "Aman clinic reserve battery ka load chart banata hai; radio test ke liye clinic ka power istemal nahi hota.",
    [
      [
        "aman",
        "Vaccine fridge aur emergency lights ki battery reserve hai. Is par radio experiment nahi hoga."
      ],
      [
        "rayan",
        "Mera portable receiver apni cell se chalega. Pehle us ki capacity naapna zaroori hai."
      ],
      [
        "laila",
        "Agar hamari battery kam hui to test cancel hoga. Mareezon ki safety pehle aayegi."
      ],
      [
        "aman",
        "Sirf zubani wada kaafi nahi. Battery load aur stop threshold likh kar mujhe dikhana."
      ]
    ]
  ],
  [
    "Ijaazat ki darkhwast",
    "Observatory authorized maintenance reception",
    "Zoya locked corridor ka seal number likh kar formal access request jama karti hai; koi approval nahi milta.",
    [
      [
        "zoya",
        "Seal number aur request ka waqt likho. Received stamp ko access permission mat samajhna."
      ],
      [
        "laila",
        "Humein service history chahiye. Jab tak written approval nahi aata, darwaza band rahega."
      ],
      [
        "zoya",
        "Agar request reject ho jaye to public records se alternate evidence dhoondhna hoga."
      ],
      [
        "laila",
        "Hum kisi lock ko nahi chherenge. Permission pending ko pending hi report mein likhenge."
      ]
    ]
  ],
  [
    "Do ghariyon ka naqsha",
    "Observatory isolated clock test bench",
    "Rayan do battery clocks ka offline comparison karta hai aur raw timestamp ko preserve karta hai.",
    [
      [
        "rayan",
        "Do minute ka farq clock mein tha, signal source mein nahi. Dono baaton ko alag rakho."
      ],
      [
        "meher",
        "Original timestamp ko chherna mana hai. Correction ke liye naya signed column banega."
      ],
      [
        "laila",
        "Har measurement ke saath device aur uncertainty likho. Hum andazay ko saboot nahi banayenge."
      ],
      [
        "rayan",
        "Isolated bench par clocks check karna safe hai. Public grid ko hum bilkul touch nahi karenge."
      ]
    ]
  ],
  [
    "Khali safhay ka record",
    "Noorabad public library reference counter",
    "Team missing maintenance page ke badlay public catalogue ka cross-reference dekhti hai; koi private borrower data nahi leti.",
    [
      [
        "meher",
        "Catalogue mein reference mil sakta hai, magar woh missing page ka asli replacement nahi."
      ],
      [
        "zoya",
        "Staff se public record poochna theek hai. Kisi reader ki private history lena mana hai."
      ],
      [
        "laila",
        "Agar number nahi milta to hum khali jagah ko khali hi chhorenge, kahani nahi banayenge."
      ],
      [
        "meher",
        "Nayi entry par source aur date dono likhungi. Purani sealed file apni jagah rahegi."
      ]
    ]
  ],
  [
    "Bazaar ka sawaal",
    "Noorabad bazaar public notice board",
    "Aman blackout ki afwah ko verified public information se alag karta hai; pulse aur outage ka link unknown rehta hai.",
    [
      [
        "aman",
        "Log pulse ko blackout ka sabab keh rahe hain, lekin humare paas is ka saboot nahi."
      ],
      [
        "laila",
        "Hum sirf itna kahenge ke passive signal record hua hai aur source abhi maloom nahi."
      ],
      [
        "zoya",
        "Kisi witness ka naam ya raw recording public na karo jab tak consent aur safety review na ho."
      ],
      [
        "aman",
        "Clinic ka emergency schedule main khud update karunga. Afwah se ilaaj mein deri nahi honi chahiye."
      ]
    ]
  ],
  [
    "Mehfooz dry run",
    "Observatory roof portable receive only station",
    "Team independent low-power receiver ke controls ko offline dry run mein check karti hai; naya signal source establish nahi hota.",
    [
      [
        "rayan",
        "Receiver ka transmit path disconnected hai. Yeh sirf procedure ka dry run hai, discovery nahi."
      ],
      [
        "laila",
        "Battery limit aur stop control dono test karo. Agar readings unclear hon to turant rukna."
      ],
      [
        "aman",
        "Clinic ki reserve battery yahan nahi hai. Inventory se bhi is baat ki tasdeeq karo."
      ],
      [
        "zoya",
        "Locked corridor ka permission abhi pending hai. Yeh portable test us approval ka badal nahi."
      ]
    ]
  ],
  [
    "Kal ka hawala",
    "Meher supervised archive desk at dusk",
    "Meher EP001 aur EP002 ke records ko naye proposed plan se link karti hai; next independent review pending rehta hai.",
    [
      [
        "meher",
        "EP001 aur EP002 ki asli copies waisi hi hain. Aaj ka plan ek alag revision ke saath hai."
      ],
      [
        "laila",
        "Humne safe checklist banayi hai, lekin signal ka source abhi bhi unknown hi hai."
      ],
      [
        "zoya",
        "Agli meeting mein pehle written permission aur independent clock review ka status dekhenge."
      ],
      [
        "aman",
        "Clinic ki supply kal dobara check hogi. Patient safety se pehle koi naya test nahi hoga."
      ]
    ]
  ]
]

def _canonical(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def validate_episode_three(script: dict) -> None:
    """Reject false approval, unauthorized edits, chronology drift and invalid hashes."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][2]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP002",
        "previous_episode_sha256": episode_two_script()["sha256"],
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
        raise ValueError("provenance_or_false_completion")
    if not isinstance(script.get("scenes"), list) or len(script["scenes"]) != len(SCENES):
        raise ValueError("scene_count")
    for number, (scene, authored) in enumerate(zip(script["scenes"], SCENES), 1):
        title, location, action, dialogue = authored
        required = {
            "number": number, "title": title, "location": location, "action": action,
            "start_second": (number - 1) * SCENE_SECONDS,
            "planned_seconds": SCENE_SECONDS,
            "dialogue": [{"speaker": speaker, "text": line} for speaker, line in dialogue],
        }
        if not isinstance(scene, dict) or scene != required:
            raise ValueError("unreviewed_scene_change")
        if len(dialogue) < 4 or any(speaker not in SPEAKERS or len(line) < 35
                                   for speaker, line in dialogue):
            raise ValueError("authored_dialogue_invalid")
    payload = {key: value for key, value in script.items() if key != "sha256"}
    digest = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
    if script.get("sha256") != digest:
        raise ValueError("revision_digest")

def episode_three_script() -> dict:
    """Fresh EP003 private table-read draft with EP002 hash-chain linkage."""
    manifest = series_manifest()
    episode = manifest["episodes"][2]
    result = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP002",
        "previous_episode_sha256": episode_two_script()["sha256"],
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
    result["sha256"] = hashlib.sha256(_canonical(result).encode("utf-8")).hexdigest()
    validate_episode_three(result)
    return result
