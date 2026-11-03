"""Task 56 pilot EP001 editorial draft, NOT a reviewed 30-minute production script.

Original Roman Urdu dialogue and a scene timing *plan*. No model calls, audio,
external accounts, render, or write side effects. No user artwork is reused.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from cloud_backend.anime_series import REVEALS, series_manifest

PILOT_ID = "EP001"
SCENE_SECONDS = 180
SPEAKERS = frozenset({"laila", "rayan", "meher", "aman", "zoya"})
SCENES = (
    ("Subah ka sannata", "Noorabad hilltop observatory room", "Laila register par aakhri reading likhti hai; door shehar ki roshni kam hoti hai.", (
        ("laila", "Aaj bhi bijli teen martaba gayi. Agar reading ghalat hai to main dobara napungi."),
        ("rayan", "Receiver ko chherne se pehle us ka purana calibration record dekh lete hain."),
        ("laila", "Bilkul. Hum sirf sun rahe hain, kisi public line ko control nahi kar rahe."),
        ("rayan", "Main battery ka meter note karta hoon; yeh bhi hamesha ke liye nahi chalegi."),
    )),
    ("Pehli dhun", "Noorabad observatory listening desk", "Receiver par barabar waqfay se halki pulse sunai deti hai; Laila waqt likhti hai.", (
        ("laila", "Rayan, yeh awaaz phir aayi. Waqt 06:14:20 likh lo, andaza nahi."),
        ("rayan", "Teen pulses mein faasla qareeban barabar hai, magar source abhi maloom nahi."),
        ("laila", "Main recording ka asli file naam aur receiver settings bhi saath rakhungi."),
        ("rayan", "Aur doosra sample lene tak hum isay kisi ka paigham nahi kahenge."),
    )),
    ("Kaghaz ki gawahi", "Noorabad observatory archive shelf", "Laila purani duty diary se receiver ki serial plate milati hai.", (
        ("laila", "Is diary mein receiver ka number mukhtalif hai. Shayad kisi ne part badla tha."),
        ("meher", "Purani entry ko mitaana mat. Nayi correction alag tareekh ke saath likho."),
        ("laila", "Theek hai, pehle asal safhay ki tasveer aur phir apna note."),
        ("meher", "Saboot tabhi kaam aata hai jab agla shakhs bhi hamara raasta samajh sake."),
    )),
    ("Band hoti roshni", "Noorabad observatory corridor", "Aman phone par clinic ke outage ki khabar deta hai; team bijli ka kharch ginti hai.", (
        ("aman", "Clinic ki backup light kamzor hai. Mareezon ko pehle dekhna zaroori hai."),
        ("laila", "Hum receiver ka doosra test chhota rakhenge; battery tumhare kaam aa sakti hai."),
        ("aman", "Mujhe sirf tasdeeq shuda halat batao, kisi afwah se log pareshan honge."),
        ("rayan", "Test ke baad battery level dobara note karunga, phir faisla karenge."),
    )),
    ("Doosra sample", "Noorabad observatory listening desk", "Rayan bina signal bheje passive recording karta hai; Laila timestamp milati hai.", (
        ("rayan", "Antenna ko sirf receive par rakha hai. Hum koi transmission nahi bhej rahe."),
        ("laila", "Pehle sample ke muqable mein pulse zara dair se aayi hai."),
        ("meher", "Dono files ki copies aur waqt alag register mein likh do."),
        ("rayan", "Ek pattern ho sakta hai, lekin do samples se faisla nahi hota."),
    )),
    ("Gawah ka sawal", "Noorabad observatory entrance", "Zoya safety inspection par aati hai aur data ki chain-of-custody poochti hai.", (
        ("zoya", "Agar yeh public report banegi to asli file aur recording ki custody kaun rakhega?"),
        ("laila", "Main source file rakhungi, Meher copy aur register ka zimma le sakti hai."),
        ("meher", "Har transfer par waqt, naam aur ijazat likhenge. Koi chhupa edit nahi."),
        ("zoya", "Acha. Aur jab tak saboot na ho, is pulse ka asal source mat batana."),
    )),
    ("Aik chhoti ghalti", "Noorabad observatory clock wall", "Team ko maloom hota hai desk clock do minute aage hai; woh raw timestamps bachati hai.", (
        ("rayan", "Desk clock do minute aage hai. Pehli reading ko khamoshi se badalna ghalat hoga."),
        ("laila", "Asal timestamp rehne do; correction ka naya column banao."),
        ("meher", "Yeh farq report mein saaf likhenge, warna baad mein hum par shak hoga."),
        ("zoya", "Ghalti maan lena saboot ko kamzor nahi, behtar banata hai."),
    )),
    ("Bahar ki awaaz", "Noorabad observatory courtyard", "Door se blackout ke dauran logon ki baat sunai deti hai; Aman ehtiyat samjhata hai.", (
        ("aman", "Log pareshan hain. Kisi ko yeh mat kaho ke humne wajah dhoond li."),
        ("laila", "Hum itna keh sakte hain ke ek ajeeb radio pulse record hui hai."),
        ("aman", "Aur yeh bhi ke is ka bijli ke maslay se taalluq abhi sabit nahi."),
        ("rayan", "Agle test se pehle clinic ki battery zaroorat poori karte hain."),
    )),
    ("Saboot ki do copies", "Meher's city archive records desk", "Meher source recording ko read-only media par copy karti hai aur register seal karti hai.", (
        ("meher", "Ek copy mere paas, doosri Laila ke paas. Dono ka hash yahan likha hai."),
        ("laila", "Kisi ko sunane se pehle gawahon ki ijazat aur context zaroor dena."),
        ("zoya", "Mujhe sirf inspection record chahiye, main asli file le kar nahi jaungi."),
        ("meher", "Aaj ka packet abhi sirf preliminary hai; hum kal dobara verify karenge."),
    )),
    ("Agla qadam", "Noorabad observatory roof at dusk", "Laila evidence packet band karti hai; team next observation aur safety check tay karti hai.", (
        ("laila", "Aaj humne sirf pulse record ki. Is ke peeche ki kahani abhi baqi hai."),
        ("rayan", "Kal passive receiver ko alag clock se milayenge, bina live grid chheray."),
        ("aman", "Aur pehle clinic ki zaroorat ka hisaab. Kisi ki sehat tajribe se bari hai."),
        ("meher", "Time-stamped recording mere archive mein hai; har agla qadam isi se shuru hoga."),
    )),
)


def validate_pilot(script: dict) -> None:
    """Fail closed on fabricated approval, broken timing, spoilers or cast drift."""
    if not isinstance(script, dict):
        raise ValueError("invalid_script")
    episode = series_manifest()["episodes"][0]
    for key, value in (
        ("episode_id", PILOT_ID), ("source_outline_sha256", series_manifest()["sha256"]),
        ("story_day", episode["story_day"]), ("source_event", episode["event"]),
        ("source_handoff", episode["handoff"]), ("approval", "editorial_draft_not_reviewed"),
        ("language", "Pakistani Roman Urdu"), ("rendered", False),
        ("human_reviewed", False), ("spoken_duration_verified", False),
    ):
        if script.get(key) != value:
            raise ValueError("script_provenance_or_claim")
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != len(SCENES):
        raise ValueError("scene_count")
    if script.get("planned_seconds") != SCENE_SECONDS * len(SCENES):
        raise ValueError("timing_claim")
    seen = set()
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or scene.get("number") != index:
            raise ValueError("scene_order")
        if scene.get("planned_seconds") != SCENE_SECONDS or scene.get("start_second") != (index - 1) * SCENE_SECONDS:
            raise ValueError("scene_timing")
        if not isinstance(scene.get("title"), str) or len(scene["title"]) < 5 or scene["title"] in seen:
            raise ValueError("scene_title")
        seen.add(scene["title"])
        for field in ("location", "action"):
            if not isinstance(scene.get(field), str) or len(scene[field]) < 25:
                raise ValueError("scene_description")
        dialogue = scene.get("dialogue")
        if not isinstance(dialogue, list) or len(dialogue) < 4:
            raise ValueError("thin_dialogue")
        for line in dialogue:
            if not isinstance(line, dict) or set(line) != {"speaker", "text"}:
                raise ValueError("dialogue_schema")
            if line["speaker"] not in SPEAKERS or not isinstance(line["text"], str) or len(line["text"]) < 35:
                raise ValueError("dialogue_cast_or_length")
    text = json.dumps(scenes, ensure_ascii=False).lower()
    # Future plot revelations are prohibited in this first-episode draft.
    for spoiler in ("founder-built guardian", "energy diversion ka pattern", "reset se evidence",
                    "public oversight aur independent audit ka naya muahida"):
        if spoiler in text:
            raise ValueError("premature_revelation")
    if script.get("known_revelations") != episode["revelations_known"]:
        raise ValueError("reveal_gate")


def pilot_script() -> dict:
    """Fresh, original pilot table-read draft with estimated, not verified, runtime."""
    episode = series_manifest()["episodes"][0]
    scenes = [
        {
            "number": index, "title": title, "location": location, "action": action,
            "start_second": (index - 1) * SCENE_SECONDS,
            "planned_seconds": SCENE_SECONDS,
            "dialogue": [{"speaker": speaker, "text": line} for speaker, line in dialogue],
        }
        for index, (title, location, action, dialogue) in enumerate(SCENES, 1)
    ]
    script = {
        "episode_id": PILOT_ID,
        "source_outline_sha256": series_manifest()["sha256"],
        "story_day": episode["story_day"],
        "source_event": episode["event"],
        "source_handoff": episode["handoff"],
        "language": "Pakistani Roman Urdu",
        "approval": "editorial_draft_not_reviewed",
        "human_reviewed": False,
        "rendered": False,
        "spoken_duration_verified": False,
        "planned_seconds": SCENE_SECONDS * len(scenes),
        "known_revelations": deepcopy(episode["revelations_known"]),
        "scenes": scenes,
    }
    validate_pilot(script)
    canonical = json.dumps(script, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    script["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return script
