"""Task 56 EP005: original Roman Urdu editorial draft, not a reviewed screenplay.

The Hawala beat records bounded evidence handoff and lawful next steps. Offline only:
no model, device, network, media, approval or publishing side effects.
Planned scene slots are not measured dialogue or actual running time.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache

from cloud_backend.anime_episode_four import episode_four_script
from cloud_backend.anime_series import series_manifest

@lru_cache(maxsize=1)
def _previous_episode_sha256() -> str:
    """Cache only an immutable digest, never a mutable prior draft."""
    return episode_four_script()["sha256"]


EPISODE_ID = "EP005"
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
  "portable_test": "dry_run_only",
  "public_notice": "draft_not_issued",
  "handoff_receipt": "internal_signed_independent_review_pending",
  "next_sequence": "public_library_register_inquiry_pending"
}
SCENES = [
  [
    "Hawala ka pehla qadam",
    "Noorabad observatory ka records desk",
    "Laila pehli sequence ke observations ko ek handoff register mein rakhti hai; source ka daawa nahi karti.",
    [
      [
        "laila",
        "Aaj ka kaam signal ka raaz hal karna nahi, jo dekha hai usay doosray logon ke liye samajhne layak banana hai."
      ],
      [
        "meher",
        "Mere paas raw pulse ki copy hai aur Laila ke paas original record. Dono ka hash aur waqt alag likhenge."
      ],
      [
        "rayan",
        "Dry run ki worksheet ko observation ke saath mix nahi karunga; woh sirf hamara offline plan tha."
      ],
      [
        "zoya",
        "Main is register ko dekh sakti hoon, magar meri nazar approval ya independent technical tasdeeq nahi hai."
      ]
    ]
  ],
  [
    "Do ghariyan, do columns",
    "City archive ka supervised catalog table",
    "Meher correction aur asal timestamps ko separate columns mein rakhti hai aur unki limitations batati hai.",
    [
      [
        "meher",
        "Asal clock ki reading ko badalna mana hai. Do minute ka farq ek signed correction note mein alag rahega."
      ],
      [
        "rayan",
        "Agar kal koi is data ko dobara calculate kare, usey raw aur adjusted dono waqt milne chahiye."
      ],
      [
        "laila",
        "Hum uncertainty ka column bhi khali nahi chhorenge, warna log ek andazay ko exact time samajh lenge."
      ],
      [
        "zoya",
        "Yeh paperwork ek audit trail hai, kisi ajnabi source ki pehchan ka certificate nahi."
      ]
    ]
  ],
  [
    "Clinic pehle",
    "Noorabad community clinic ka emergency entrance",
    "Aman written safety note deta hai; investigation clinic supply se bilkul alag rehti hai.",
    [
      [
        "aman",
        "Fridge aur emergency lights ka load aaj bhi pehle hai. Investigation ko clinic ki backup supply se kuch nahi milega."
      ],
      [
        "rayan",
        "Meri portable cell ki charge limit record hai, lekin receive-only trial abhi approved bhi nahi hua."
      ],
      [
        "laila",
        "Hum bina written stop threshold aur permission ke koi receiver on nahi karenge, chahe delay kitna ho."
      ],
      [
        "aman",
        "Yeh baat handoff note mein saaf likho, taake agla reader risk ko chhota samajh kar shortcut na le."
      ]
    ]
  ],
  [
    "Band darwaza",
    "Observatory maintenance reception",
    "Zoya corridor ki request ki status dikhati hai aur received stamp ko permission banne se rokti hai.",
    [
      [
        "zoya",
        "Mere register mein darkhwast receive hui hai, lekin locked corridor ki written access permission abhi pending hai."
      ],
      [
        "laila",
        "Hum seal ko nahi chhooenge. Agli team ko bhi yahi boundary handoff mein likh kar deni hai."
      ],
      [
        "rayan",
        "Public records aur offline calculations se kaam chal sakta hai; restricted hardware par test ka koi order nahi."
      ],
      [
        "meher",
        "Pending ko approved likhne se poori chain of custody kamzor ho jayegi, is liye lafz bilkul saaf rakho."
      ]
    ]
  ],
  [
    "Gawah ki awaaz",
    "Noorabad bazaar community notice board",
    "Team proposed public note mein consent aur verified observations ka farq samajhti hai.",
    [
      [
        "aman",
        "Bazaar ke log sawal kar rahe hain, lekin kisi gawah ka naam us ki razamandi ke baghair share nahi hoga."
      ],
      [
        "meher",
        "Public notice abhi draft hai; is mein sirf non-identifying observations aur missing evidence ki baat hogi."
      ],
      [
        "laila",
        "Blackout aur pulse ka sabab ek hona sabit nahi hua. Humein yeh uncertainty khul kar batani hai."
      ],
      [
        "zoya",
        "Jab tak independent review na ho, is kagaz ko official finding ya issue hua notice nahi kehna."
      ]
    ]
  ],
  [
    "Do copies ka safar",
    "Meher ka secure city archive counter",
    "Meher aur Laila copies ke labels, hashes aur proposed custody receipt compare karti hain.",
    [
      [
        "meher",
        "Copy A mere archive mein rahegi aur source record Laila ke paas. Har transfer ke liye waqt aur sign chahiye."
      ],
      [
        "laila",
        "Main apni original file ka digest dobara likh rahi hoon, magar hash sirf file ki pehchan hai, sach ki guarantee nahi."
      ],
      [
        "rayan",
        "Dry-run calculations ko alag folder mein rakho. Unhen recorded pulse ki asli measurement mat samajhna."
      ],
      [
        "zoya",
        "Receipt ka draft theek hai, magar independent custodian ka signature milne tak review complete nahi hoga."
      ]
    ]
  ],
  [
    "Agla suraagh",
    "Noorabad public library ka front information desk",
    "Team next sequence ke public frequency register ke liye lawful inquiry tay karti hai.",
    [
      [
        "laila",
        "Observatory ke baad agla raasta public library ka frequency register hai; hum sirf accessible index poochhenge."
      ],
      [
        "meher",
        "Missing index page ko khud se reconstruct nahi karenge. Jo milay ga us ka catalog number note hoga."
      ],
      [
        "rayan",
        "Main naya signal source claim nahi karunga; register sirf hamari hypothesis ko test karne ka agla zariya hai."
      ],
      [
        "zoya",
        "Agar koi record restricted hua to written request bhejna, kisi private borrower ki history nikalna nahi."
      ]
    ]
  ],
  [
    "Hawala, faisla nahi",
    "Noorabad observatory courtyard at night",
    "Team handoff note sign karti hai, unknown source aur pending permissions ko next episode tak mehfooz rakhti hai.",
    [
      [
        "laila",
        "Pehla hawala tayyar hai: humne observation aur andazay ko alag rakha, raaz abhi baqi hai."
      ],
      [
        "meher",
        "Main do copies ki list aur correction note sambhalungi; independent review abhi pending likha rahega."
      ],
      [
        "aman",
        "Clinic ki safety boundary isi tarah rahegi. Kisi tajrube ke liye mareezon ka hissa nahi diya jayega."
      ],
      [
        "zoya",
        "Kal library inquiry ka record dekhte hain. Aaj ki signed handoff ko final approval ya discovery mat kehna."
      ]
    ]
  ]
]

def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def validate_episode_five(script: dict) -> None:
    """Fail closed on rewritten source, false approval, spoilers and hash drift."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][4]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP004",
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

def episode_five_script() -> dict:
    """Fresh deterministic EP005 draft, linked to the unmodified EP004 digest."""
    manifest = series_manifest()
    episode = manifest["episodes"][4]
    draft = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP004",
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
    validate_episode_five(draft)
    return draft
