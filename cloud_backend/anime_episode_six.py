"""Task 56 EP006: original Roman Urdu editorial draft, not a reviewed screenplay.

The first Ishara beat of the public-library sequence locates the public frequency
register while keeping its missing index page and the pulse source unresolved.
Offline and deterministic: no network, media, approvals or publishing.
Planned scene slots do not measure spoken or produced running time.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from cloud_backend.anime_episode_five import episode_five_script
from cloud_backend.anime_series import series_manifest

EPISODE_ID = "EP006"
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
  "next_sequence": "missing_page_history_inquiry_pending"
}
SCENES = [
  [
    "Kitab ka darwaza",
    "Noorabad public library ka information desk",
    "Laila public catalog mein frequency register ka reference dhoondti hai; private borrower records ki darkhwast nahi karti.",
    [
      [
        "laila",
        "Hum sirf public catalog aur reference register dekhna chahte hain. Kisi borrower ka naam ya private history nahi chahiye."
      ],
      [
        "zoya",
        "Library ka aam reference section sab ke liye hai, lekin staff ke qawaid phir bhi follow karne honge."
      ],
      [
        "meher",
        "EP005 ka internal handoff mere paas hai. Yeh signed hai, magar independent technical review abhi pending hai."
      ],
      [
        "rayan",
        "Register mil bhi gaya to pulse ka source sabit nahi hoga. Pehle catalog number aur edition note karenge."
      ]
    ]
  ],
  [
    "Ek purana number",
    "Library ka public reference counter",
    "Team public catalog se bound frequency register ka catalog number aur edition verify karti hai; naya source claim nahi karti.",
    [
      [
        "meher",
        "Catalog mein register ka number aur edition maujood hai. Main dono ko bilkul waise hi likhungi jaise record par hain."
      ],
      [
        "laila",
        "Humein ek reference mila hai, signal bhejne wala nahi. Yeh farq hamari report ki pehli line mein rahe."
      ],
      [
        "zoya",
        "Sirf public shelf ki kitab dekhna theek hai; restricted archive tak jana abhi bhi written approval mangta hai."
      ],
      [
        "rayan",
        "Main register ke labels ko apne offline notes se compare karunga, kisi receiver ko live nahi chalaunga."
      ]
    ]
  ],
  [
    "Gumshuda safha",
    "Public library ka supervised reading table",
    "Bound register milta hai lekin index ka aik safha gayab hai; team khali jagah ko saboot ke taur par record karti hai.",
    [
      [
        "laila",
        "Register yahin hai, lekin index ka aik safha missing hai. Hum andazay se us ka matn nahi bharenge."
      ],
      [
        "meher",
        "Main page sequence aur catalog condition note karungi. Bina tasdeeq kisi shakhs par safha hatane ka ilzam nahi."
      ],
      [
        "zoya",
        "Staff ki ijazat se sirf visible page numbers likho. Kitab ko nuksan ya kisi seal ko chhoona mana hai."
      ],
      [
        "rayan",
        "Missing safha ek evidence gap hai. Is se na frequency confirm hoti hai na hamara pehla model sahi sabit hota hai."
      ]
    ]
  ],
  [
    "Do waqt, ek sawal",
    "City archive ka supervised comparison desk",
    "Meher library reference aur pulse timestamps ko side-by-side rakhti hai, raw data mein do-minute correction merge nahi karti.",
    [
      [
        "meher",
        "Raw pulse waqt aur correction note alag columns mein rahenge. Library ki tareekh ko un se zabardasti match nahi karenge."
      ],
      [
        "rayan",
        "Do minute ka clock offset hamare purane instrument ka hai; register par wahi offset laga dena ghalat hoga."
      ],
      [
        "laila",
        "Agar matching sirf adjustment se banti hai, to usay finding nahi balkay untested hypothesis likhenge."
      ],
      [
        "zoya",
        "Independent reviewer ko asal records, correction ki wajah aur uncertainty sab nazar aani chahiye."
      ]
    ]
  ],
  [
    "Mareez ka pehla haq",
    "Noorabad community clinic ka backup supply room ke bahar",
    "Aman ko register ki khabar milti hai lekin clinic ki emergency power boundary badalne se inkar karta hai.",
    [
      [
        "aman",
        "Naya register milna achi baat hai, magar fridge aur emergency lights ki reserve supply investigation ke liye nahi milegi."
      ],
      [
        "rayan",
        "Main sirf kagaz par comparison kar raha hoon. Portable cell ka receive-only trial bhi written safety sign-off ke baghair nahi."
      ],
      [
        "laila",
        "Kisi clue ke liye mareezon ka risk qabool nahi. Handoff mein clinic-first boundary phir se likhenge."
      ],
      [
        "meher",
        "Yeh safety note independent review ke saath jayega, taake koi agla reader shortcut ko approval na samjhe."
      ]
    ]
  ],
  [
    "Naqshay ki hadd",
    "Observatory ka offline analysis table",
    "Rayan register ke public labels ka offline comparison karta hai; matching ya signal-source discovery ka daawa nahi karta.",
    [
      [
        "rayan",
        "Public register ke labels aur hamare receiver ke notes mein kuch alfaaz milte hain, magar measurements comparable nahi hain."
      ],
      [
        "laila",
        "Har similarity ke saath alternative explanation bhi likho. Ek lafz ka milna transmitter ki pehchan nahi."
      ],
      [
        "meher",
        "Dry-run worksheet ko raw pulse recording se alag folder mein rakho, warna baad mein evidence mix ho jayega."
      ],
      [
        "zoya",
        "Locked corridor ki request abhi pending hai. Offline comparison ko hardware access ka replacement bhi mat kehna."
      ]
    ]
  ],
  [
    "Gawah ki hifazat",
    "Library ka public community reading corner",
    "Team library inquiry ka neutral draft summary banati hai aur gawahon ki private pehchan share nahi karti.",
    [
      [
        "aman",
        "Bazaar ke log poochhenge ke kya mila. Hum kitab ka public reference bata sakte hain, kisi gawah ka naam nahi."
      ],
      [
        "meher",
        "Public note abhi draft hai. Consent ke baghair testimony, borrower details ya kisi ki tasveer is mein nahi aayegi."
      ],
      [
        "laila",
        "Hum sirf register milne aur missing page ka verified observation batayenge, blackout ka sabab nahi ghadenge."
      ],
      [
        "zoya",
        "Kisi notice ko issued mat likho. Review aur authorized publication ke baghair yeh sirf internal draft hai."
      ]
    ]
  ],
  [
    "Rukawat ka pehla nishan",
    "Noorabad public library ka exit register desk",
    "Team register ki condition aur missing page ka supervised note banati hai; next obstacle ke liye lawful records request taiyar karti hai.",
    [
      [
        "meher",
        "Catalog reference aur missing page ka condition note mere archive copy mein jayega. Original kitab library mein hi rahegi."
      ],
      [
        "rayan",
        "Agla sawal yeh hai ke missing page ki official history kahan hai; abhi hamare paas us ka jawab nahi."
      ],
      [
        "zoya",
        "Restricted maintenance ya borrower records ke liye alag written request chahiye. Koi private file khud se nahi kholega."
      ],
      [
        "laila",
        "Aaj humne register dhoonda hai, source nahi. Kal missing safhay ki rukawat ko qanooni tareeqay se samjhenge."
      ]
    ]
  ]
]


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def validate_episode_six(script: dict) -> None:
    """Reject rehashed tampering, false approvals, chronology drift and spoilers."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][5]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP005",
        "previous_episode_sha256": episode_five_script()["sha256"],
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


def episode_six_script() -> dict:
    """Return a fresh EP006 draft linked to the immutable EP005 revision."""
    manifest = series_manifest()
    episode = manifest["episodes"][5]
    draft = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP005",
        "previous_episode_sha256": episode_five_script()["sha256"],
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
    validate_episode_six(draft)
    return draft
