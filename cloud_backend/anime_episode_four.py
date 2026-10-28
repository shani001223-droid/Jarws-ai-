"""Task 56 EP004: original Roman Urdu editorial draft, not a reviewed screenplay.

The Qeemat beat explores time, trust and finite power costs. Offline only:
no model, device, network, media, approval or publishing side effects.
Planned scene slots are not measured dialogue or actual running time.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from cloud_backend.anime_episode_three import episode_three_script
from cloud_backend.anime_series import series_manifest

EPISODE_ID = "EP004"
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
  "public_notice": "draft_not_issued"
}
SCENES = [
  [
    "Ruki hui subah",
    "Noorabad observatory ke bahar public bench",
    "Laila pichlay din ke pending kaamon ko likhti hai aur batati hai ke har delay ki aik insani qeemat hai.",
    [
      [
        "laila",
        "Do din ki mehnat ke baad bhi source unknown hai. Ab humein har ghante ka hisaab dena hoga."
      ],
      [
        "rayan",
        "Receiver ka dry run hua tha, live observation nahi. Main report mein yeh farq saaf likhunga."
      ],
      [
        "meher",
        "Archive ki do copies mehfooz hain, lekin missing index page ko hum abhi bhi nahi dhoond paye."
      ],
      [
        "laila",
        "Agar hum jaldi mein natija nikalen to shehar ka bharosa aur waqt dono zaya honge."
      ]
    ]
  ],
  [
    "Clinic ka hisaab",
    "Noorabad community clinic ka morning supply counter",
    "Aman emergency supply ka naya load chart dikhata hai aur team apni portable cell ki limit ko dobara janchti hai.",
    [
      [
        "aman",
        "Kal vaccine fridge ki battery kam thi. Aaj bhi clinic ki reserve supply par pehla haq mareezon ka hai."
      ],
      [
        "rayan",
        "Meri portable cell alag hai. Usay clinic se charge nahi kiya, aur us ki capacity abhi limited hai."
      ],
      [
        "laila",
        "Hum is cell ko bhi sirf approved passive check ke liye sochenge, kisi emergency ka risk nahi lenge."
      ],
      [
        "aman",
        "Mujhe likha hua stop threshold chahiye. Zubani yaqeen se emergency planning nahi chalti."
      ]
    ]
  ],
  [
    "Seal ki qeemat",
    "Observatory maintenance reception ka waiting hall",
    "Zoya received-stamp wali access request aur asli written permission ke darmiyan farq samjhati hai.",
    [
      [
        "zoya",
        "Request receive hui hai, magar corridor kholne ki written permission abhi tak nahi mili."
      ],
      [
        "laila",
        "Is intezar se test late ho raha hai, lekin bina ijazat seal torna saboot ko nuqsan dega."
      ],
      [
        "rayan",
        "Main apna offline model update kar sakta hoon. Locked equipment ko chhoona zaroori nahi."
      ],
      [
        "zoya",
        "Main pending status ko pending hi likhungi. Kisi stamp ko approval ka naam nahi denge."
      ]
    ]
  ],
  [
    "Bazaar ka bharosa",
    "Noorabad bazaar ki chhoti community meeting",
    "Aman ko blackout ke bare mein sawaal milte hain; team afwah aur tasdeeq shuda baat alag rakhti hai.",
    [
      [
        "aman",
        "Logon ko jawab chahiye, magar hum pulse ko bijli band honay ka sabab sabit nahi kar sakte."
      ],
      [
        "meher",
        "Agar summary banayenge to witness ke naam aur private details bina razamandi nahi aayengi."
      ],
      [
        "laila",
        "Main sirf recorded observation aur uncertainty bataungi. Koi final source claim nahi hoga."
      ],
      [
        "zoya",
        "Public note abhi draft hai. Independent review se pehle isay official notice mat kehna."
      ]
    ]
  ],
  [
    "Ghari ka farq",
    "Meher ke supervised city archive reading table",
    "Meher raw timestamps, corrected column aur do independent clock readings ko saath rakhti hai.",
    [
      [
        "meher",
        "Asal timestamp ko humne nahi badla. Do minute ki correction apni alag signed entry mein hai."
      ],
      [
        "rayan",
        "Dono ghariyon ka muqabla abhi bhi uncertainty rakhta hai; is se signal ka source nahi milta."
      ],
      [
        "laila",
        "Har nayi calculation mein raw aur corrected waqt dono nazar aane chahiye, warna ghalat fehmi hogi."
      ],
      [
        "zoya",
        "Aaj ka audit sirf record ke tareeqe ka hai. Main kisi technical discovery ki tasdeeq nahi kar rahi."
      ]
    ]
  ],
  [
    "Waqt ki kami",
    "Observatory ke isolated planning room",
    "Rayan limited hours aur portable battery budget ki list banata hai; team risky shortcuts ko rad karti hai.",
    [
      [
        "rayan",
        "Hamare paas chaar ghante aur ek portable cell hai. Yeh poori grid investigation ka budget nahi."
      ],
      [
        "laila",
        "To phir chhota sa lawful test plan banate hain, aur unclear result par foran ruk jayenge."
      ],
      [
        "aman",
        "Clinic ka emergency schedule pehle se tay hai. Team us ke kaam mein rukawat nahi banegi."
      ],
      [
        "meher",
        "Har proposed step ka source aur zimmedar shakhs likh do, taake kal koi andaza na lagaye."
      ]
    ]
  ],
  [
    "Gawah ka intezar",
    "Noorabad municipal public records corridor",
    "Zoya missing page ke bare mein public index request ki progress batati hai, magar kisi par ilzam nahi lagati.",
    [
      [
        "zoya",
        "Public index ka jawab abhi pending hai. Missing page ko chori ka saboot kehna ghalat hoga."
      ],
      [
        "meher",
        "Main original packet aur nayi request ko alag rakhti hoon. Koi private borrower history nahi lungi."
      ],
      [
        "laila",
        "Agar jawab na aaye to hum alternate public source dhoondhenge, lekin khali jagah khud nahi bharenge."
      ],
      [
        "zoya",
        "Aur jab gawah mile to us ki razamandi aur custody note karna zaroori hoga."
      ]
    ]
  ],
  [
    "Aaj ki qeemat",
    "Noorabad observatory courtyard at dusk",
    "Team delay, community trust aur energy ki qeemat ko evidence handoff mein likh kar aglay din ka lawful raasta tay karti hai.",
    [
      [
        "laila",
        "Aaj humne signal ka raaz nahi khola. Humne bas samjha ke sahi tareeqe ki bhi qeemat hoti hai."
      ],
      [
        "aman",
        "Mareez mehfooz rahe, yeh sab se zaroori natija hai. Clinic ki battery ka record mere paas hai."
      ],
      [
        "meher",
        "Raw recording, clock correction aur pending requests ki alag copies archive mein rehengi."
      ],
      [
        "zoya",
        "Kal independent review aur written permission ka status dekhenge. Tab tak koi public discovery claim nahi."
      ]
    ]
  ]
]

def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def validate_episode_four(script: dict) -> None:
    """Fail closed on rewritten source, false approval, spoilers and hash drift."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    manifest = series_manifest()
    episode = manifest["episodes"][3]
    expected = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP003",
        "previous_episode_sha256": episode_three_script()["sha256"],
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

def episode_four_script() -> dict:
    """Fresh deterministic EP004 draft, linked to the unmodified EP003 digest."""
    manifest = series_manifest()
    episode = manifest["episodes"][3]
    draft = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP003",
        "previous_episode_sha256": episode_three_script()["sha256"],
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
    validate_episode_four(draft)
    return draft
