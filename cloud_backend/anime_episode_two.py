"""Task 56: EP002 original Roman Urdu *editorial* draft, linked to EP001.

This is a planned scene allocation, not 30 minutes of recorded dialogue or an
approved screenplay. Deterministic, offline, with no publishing or media calls.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from cloud_backend.anime_scripts import pilot_script
from cloud_backend.anime_series import series_manifest

EPISODE_ID = "EP002"
SCENE_SECONDS = 225
ALLOWED_SPEAKERS = frozenset({"laila", "rayan", "meher", "aman", "zoya"})
CARRY_FORWARD = {
    "pulse_custody": "meher_archive_copy_and_laila_source",
    "clock_offset": "two_minutes_not_silently_corrected",
    "signal_source": "unknown",
    "clinic_priority": "patient_safety_before_receiver_test",
}

# Eight separately authored scene drafts. Every location/action and dialogue
# line is a narrative proposal; none is an actual filmed or voiced scene.
SCENES = (
    ("Subah ka record", "Meher ke shehri archive ka records room",
     "Meher do sealed evidence copies ko milati hai; kal ki clock correction alag register mein rakhti hai.", (
        ("meher", "Kal wali source file apni jagah hai. Clock ki do minute wali correction alag safhay par hai."),
        ("laila", "Main chahti hoon ke koi bhi nayi reading purani file ko badlay baghair likhi jaye."),
        ("zoya", "Mujhe inspection ke liye sirf register ki tasdeeq shuda copy chahiye, asal file nahi."),
        ("meher", "Copy par waqt aur sign dono honge; jisay dekhnay ki ijazat ho usi ko dungi."),
    )),
    ("Ruka hua darwaza", "Noorabad observatory ka locked equipment corridor",
     "Receiver room ke bahar safety seal lagi milti hai; team bina ijazat darwaza nahi kholti.", (
        ("rayan", "Equipment room par nayi seal hai. Isay torna test se zyada bara masla banay ga."),
        ("laila", "Hum permission ka record maangte hain, chup kar andar jana hamara tareeqa nahi."),
        ("zoya", "Seal ka number note karo. Main authorized custodian se likhi hui wajah mangungi."),
        ("rayan", "Tab tak portable receiver se sirf purani recording ka offline muqabla kar sakte hain."),
    )),
    ("Clinic ka pehla haq", "Noorabad community clinic ka battery storage room",
     "Aman backup battery ka load chart dikhata hai; observatory team apna test moakhar karti hai.", (
        ("aman", "Do emergency lamps aur vaccine fridge ko bijli chahiye; yeh pehla haq hai."),
        ("laila", "Humara radio tajriba ruk sakta hai. Kisi mareez ka ilaaj rukna nahi chahiye."),
        ("rayan", "Main apni spare cell ki capacity naap kar dunga, magar andazay se wada nahi karunga."),
        ("aman", "Shukriya. Measurement likh lena, phir clinic ki team khud faisla karegi."),
    )),
    ("Gumshuda daftar", "Noorabad municipal records counter ke samne waiting area",
     "Receiver ki maintenance entry maangi jati hai magar daftar mein index ka aik panna missing hai.", (
        ("laila", "Humein sirf receiver ki service history chahiye; kisi ka private record nahi."),
        ("meher", "Index ka aik safha nahi mil raha. Is ka matlab abhi saboot mitana nahi hota."),
        ("zoya", "Missing page ko missing hi likho. Kis ne kab dekha, us ki gawahi alag hogi."),
        ("laila", "Jab tak doosra record nahi milta, hum kisi par ilzam nahi lagayenge."),
    )),
    ("Do ghariyan", "Observatory ke portable receiver test bench par",
     "Rayan do battery clocks ka offline comparison karta hai; pehli reading ki uncertainty barqarar rehti hai.", (
        ("rayan", "Dono ghariyon ka farq naap liya hai, lekin kal ki recording ka asal waqt abhi final nahi."),
        ("laila", "Har observation ke saath clock ka naam likho, taake baad mein hisaab mil sake."),
        ("meher", "Main dono comparison sheets archive karungi, purani entry ko overwrite nahi karungi."),
        ("rayan", "Agla sample tab lenge jab safety clearance aur clinic ka load dono clear hon."),
    )),
    ("Afwah ka raasta", "Noorabad bazaar ke public notice board ke paas",
     "Ek afwah se log pulse ko blackout ka sabab samajhne lagte hain; team uncertainty saaf karti hai.", (
        ("aman", "Bazaar mein keh rahe hain radio pulse ne bijli band ki. Is ka koi saboot nahi."),
        ("laila", "Humne sirf ek signal suna hai. Blackout se us ka rishta abhi maloom nahi."),
        ("zoya", "Public note mein sirf verified observations hon; kisi shakhs ka naam bina razamandi nahi."),
        ("aman", "Main clinic ke notice par sirf emergency timings aur contact rakhunga."),
    )),
    ("Gawah ka ikhtiyar", "Meher ke archive ka supervised reading table",
     "Zoya custody log check karti hai; ek proposed public copy se private witness details hatai jati hain.", (
        ("zoya", "Jis ne observation di us ki ijazat ke baghair naam public packet mein nahi ja sakta."),
        ("meher", "Main public summary aur private custody record ko do alag folders mein rakhungi."),
        ("laila", "Data ka matlab logon ki privacy khatam karna nahi. Sirf zaroori cheez dikhayenge."),
        ("zoya", "Aaj ki inspection mein source relay ka faisla nahi, sirf record ka silsila verify hua."),
    )),
    ("Naya rasta", "Observatory ki chhat par dusk safety meeting",
     "Team authorized maintenance log ka intezar karti hai aur next passive test ke liye written checklist banati hai.", (
        ("laila", "Darwaza band hai to hum qanooni ijazat ka intezar karenge; raaz abhi khula hai."),
        ("rayan", "Main portable test ka diagram banaunga, live grid ya locked room ko nahi chherunga."),
        ("aman", "Clinic ki supply pehle check hogi. Us ke baad hi koi extra battery istemal hogi."),
        ("meher", "Kal ki file aur aaj ki rukawat dono archive mein hain; agla qadam isi record se niklay ga."),
    )),
)


def validate_episode_two(script: dict) -> None:
    """Reject continuity drift, invented approval, timing errors and early reveals."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    outline = series_manifest()
    episode = outline["episodes"][1]
    pilot = pilot_script()
    required = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP001",
        "previous_episode_sha256": pilot["sha256"],
        "source_outline_sha256": outline["sha256"],
        "story_day": episode["story_day"],
        "source_event": episode["event"],
        "source_handoff": episode["handoff"],
        "episode_beat": episode["beat"],
        "language": "Pakistani Roman Urdu",
        "approval": "editorial_draft_not_reviewed",
        "human_reviewed": False,
        "spoken_duration_verified": False,
        "rendered": False,
        "planned_seconds": SCENE_SECONDS * len(SCENES),
        "known_revelations": episode["revelations_known"],
        "carried_forward": CARRY_FORWARD,
    }
    if any(script.get(k) != v for k, v in required.items()):
        raise ValueError("provenance_or_false_completion")
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != len(SCENES):
        raise ValueError("scene_count")
    seen = set()
    for i, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or scene.get("number") != i:
            raise ValueError("scene_order")
        if scene.get("start_second") != (i - 1) * SCENE_SECONDS or scene.get("planned_seconds") != SCENE_SECONDS:
            raise ValueError("scene_timing")
        title = scene.get("title")
        if not isinstance(title, str) or len(title) < 5 or title in seen:
            raise ValueError("scene_title")
        seen.add(title)
        if any(not isinstance(scene.get(k), str) or len(scene[k]) < 25 for k in ("location", "action")):
            raise ValueError("scene_description")
        dialogue = scene.get("dialogue")
        if not isinstance(dialogue, list) or len(dialogue) < 4:
            raise ValueError("thin_dialogue")
        for turn in dialogue:
            if not isinstance(turn, dict) or set(turn) != {"speaker", "text"}:
                raise ValueError("dialogue_schema")
            if turn["speaker"] not in ALLOWED_SPEAKERS or not isinstance(turn["text"], str) or len(turn["text"]) < 35:
                raise ValueError("dialogue_cast_or_length")
    prose = json.dumps(scenes, ensure_ascii=False).lower()
    for premature in ("founder-built guardian", "energy diversion ka pattern",
                      "reset se evidence", "public oversight aur independent audit ka naya muahida"):
        if premature in prose:
            raise ValueError("premature_revelation")
    if "sha256" in script:
        digest_data = {k: v for k, v in script.items() if k != "sha256"}
        expected = hashlib.sha256(json.dumps(digest_data, ensure_ascii=False, sort_keys=True,
                                             separators=(",", ":")).encode("utf-8")).hexdigest()
        if script["sha256"] != expected:
            raise ValueError("revision_digest")


def episode_two_script() -> dict:
    """Return a fresh offline EP002 table-read draft; timing remains unverified."""
    outline = series_manifest()
    episode = outline["episodes"][1]
    result = {
        "episode_id": EPISODE_ID,
        "previous_episode_id": "EP001",
        "previous_episode_sha256": pilot_script()["sha256"],
        "source_outline_sha256": outline["sha256"],
        "story_day": episode["story_day"],
        "source_event": episode["event"],
        "source_handoff": episode["handoff"],
        "episode_beat": episode["beat"],
        "language": "Pakistani Roman Urdu",
        "approval": "editorial_draft_not_reviewed",
        "human_reviewed": False,
        "spoken_duration_verified": False,
        "rendered": False,
        "planned_seconds": SCENE_SECONDS * len(SCENES),
        "known_revelations": deepcopy(episode["revelations_known"]),
        "carried_forward": deepcopy(CARRY_FORWARD),
        "scenes": [
            {"number": i, "title": title, "location": location, "action": action,
             "start_second": (i - 1) * SCENE_SECONDS, "planned_seconds": SCENE_SECONDS,
             "dialogue": [{"speaker": speaker, "text": line} for speaker, line in dialogue]}
            for i, (title, location, action, dialogue) in enumerate(SCENES, 1)
        ],
    }
    validate_episode_two(result)
    canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    result["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    validate_episode_two(result)
    return result
