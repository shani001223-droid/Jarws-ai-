"""Task 55: original 300-episode anime continuity plan, NOT scripts or rendered media.

Deterministic, offline and read-only. No model calls, accounts, files or workers.
Every five-episode sequence has an authored event and consequence. The generator
expands those into individually numbered causal beats for script review.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy

TITLE = "Aasmaan Ka Daira"
EPISODES_PER_ARC = 30
TARGET_EPISODES = 300
MINUTES_PER_EPISODE = 30
BEATS = (
    ("Ishara", "Laila aur team is suraagh ko verify karte hain"),
    ("Rukawat", "Mukhalif quwwat saboot tak rasai rokne ki koshish karti hai"),
    ("Tadbeer", "Team aik naya, qanooni aur kam-khatre wala raasta chunti hai"),
    ("Qeemat", "Faislay ka waqt, trust aur energy par asli asar samne aata hai"),
    ("Hawala", "Saboot ki copy aur aglay qadam ki zimmedari record hoti hai"),
)

# Each pair is an authored five-episode story unit: concrete event, causal handoff.
# Ten arcs x six units x five beats = 300 distinct chronological episode entries.
ARCS = (
    ("Band Awaaz", "Laila ka pehla signal aur doston ka ittihad", (
        ("purani observatory mein ajnabi radio pulse milna", "pulse ki time-stamped recording Meher ko milti hai"),
        ("shehri library mein kho gaya frequency register milna", "register ka missing page sab ko shak mein dalta hai"),
        ("Rayan ka toota antenna dobara calibrate karna", "signal ka rukh purani nahr ki taraf nikalta hai"),
        ("nahr ke gate par band maintenance tunnel dekhna", "tunnel ka legal access permit darkhwast hota hai"),
        ("Aman ka blackout ward ke mareezon ko sambhalna", "team ko bijli ki kami ka insani asar samajh aata hai"),
        ("Meher ka pehla evidence packet archive karna", "team encrypted nahi, signed paper copies bhi banati hai"),
    )),
    ("Zameen Ka Naqsha", "Signal ke raste aur shehar ki purani planning", (
        ("municipal map mein nahr ke neeche cable milna", "cable route ki photo public record se milti hai"),
        ("bridge ke neeche relay box ka serial number parhna", "serial number supply ledger se milaya jata hai"),
        ("Zoya ka team se evidence provenance mangna", "team independent witness ke samne record kholti hai"),
        ("barish se archive ke kaghaz bachana", "duplicate records safe library tak pohnchte hain"),
        ("Rayan ka passive receiver banana", "bina network chheray pulse ka interval map hota hai"),
        ("nahr ke relay ka source shehar ke andar sabit karna", "pehla raaz public hearing ke liye taiyar hota hai"),
    )),
    ("Roshan Qeemat", "Bijli ki taqseem aur awam ke sawaal", (
        ("hospital aur bazaar ke outage logs milana", "energy shortage ka naqsha samne aata hai"),
        ("Meher ka purana meter audit parhna", "audit ki tareekh aur signatures verify hote hain"),
        ("Laila ka basti ke logon se razamandi lena", "gawahon ke naam unki ijazat se record hote hain"),
        ("Aman ka emergency light ka free repair camp chalana", "basti team ki niyyat ko test karti hai"),
        ("Zoya ka council hearing ka notice dena", "saboot ko naya legal deadline milta hai"),
        ("public grid ka pehla mismatch establish karna", "team aglay arc mein rural meters check karti hai"),
    )),
    ("Do Shehr", "Markaz aur dehat ke darmiyan energy ka farq", (
        ("dehati clinic ke voltage logs collect karna", "do ilaqon ke measured readings milti hain"),
        ("Rayan ka tampered meter seal pehchanna", "seal ki chain-of-custody banai jati hai"),
        ("Meher ka purchase contract compare karna", "contract ki clauses public debate mein aati hain"),
        ("Laila ka rural committee se mashwara karna", "committee apna witness nominate karti hai"),
        ("Aman ka battery ration plan banana", "medical needs ko grid politics se alag rakha jata hai"),
        ("energy diversion ka documented pattern dikhana", "public inquiry mein rural haqooq ka sawal uthta hai"),
    )),
    ("Aaina Council", "Hearing, zimmedari aur pehla bada nuqsan", (
        ("council ke khulay session mein data pesh karna", "sawal-jawab ka official transcript banta hai"),
        ("Zoya ka forged timestamp pakarna", "ek kamzor gawahi record se hat jati hai"),
        ("Meher ka asli maintenance log dhoondhna", "alternate corroboration mil jati hai"),
        ("Rayan ka damaged substation inspect karna", "technical report safety authority ko di jati hai"),
        ("Laila ka team ki ghalti khul kar tasleem karna", "public trust ko sach se dobara banana parta hai"),
        ("hearing ka interim order hasil karna", "council ko independent inspection qabool karni parti hai"),
    )),
    ("Bunyad Ka Code", "Purane founders aur safety protocol ki kahani", (
        ("observatory ke founders ke interview notes milna", "purane faislon ki chronology banti hai"),
        ("Meher ka protocol manual ka missing appendix dhoondhna", "manual ki asal version identify hoti hai"),
        ("Rayan ka simulation mein grid failsafe test karna", "sirf offline model ka result milta hai"),
        ("Zoya ka purane board minutes verify karna", "zimmedari kisi aik shakhs par nahi thopti"),
        ("Laila ka protocol ki human-cost report banana", "team safety aur accountability ko jorti hai"),
        ("founder-built guardian protocol ka saboot dena", "naya masla: isay band karna kitna mehfooz hai"),
    )),
    ("Sheesha Dar", "System ki hifazat aur saboot ki jang", (
        ("guardian relay ke safety interlocks samajhna", "team live grid ko touch na karne ka faisla karti hai"),
        ("Aman ka blackout drill organize karna", "basti mein emergency preparedness barhti hai"),
        ("Meher ka record-copy custody audit karna", "saboot ka second independent custodian milta hai"),
        ("Rayan ka offline patch proposal likhna", "patch ko production mein laganay se roka jata hai"),
        ("Zoya ka conflict-of-interest declaration lena", "investigation ki impartiality test hoti hai"),
        ("public review board ki temporary nigrani lena", "team ko restricted evidence access milta hai"),
    )),
    ("Aakhri Reset", "Evidence ko bachanay ka faisla", (
        ("council ke reset notice ka matn parhna", "reset ka scope abhi ghair-wazeh rehta hai"),
        ("Rayan ka isolated test rig mein reset rehearse karna", "test aur asli system ka farq record hota hai"),
        ("Meher ka audit archive ka backup verify karna", "multiple physical copies maujood hoti hain"),
        ("Laila ka logon ko reset risks samjhana", "public consultation mein mukhtalif rai aati hai"),
        ("Zoya ka retention clause par legal sawal uthana", "reset par interim stay ki darkhwast hoti hai"),
        ("reset se evidence mitne ka proof pesh karna", "stay milta hai aur transparent alternative zaroori hota hai"),
    )),
    ("Naya Muahida", "Shared governance aur trust ki azmaish", (
        ("dehat aur shehar ke delegates ka joint forum banana", "representation rules likhe jate hain"),
        ("Aman ka health-first allocation model rakhna", "emergency loads ke priority criteria bante hain"),
        ("Rayan ka open meter dashboard ka offline prototype dikhana", "privacy aur tampering risks note hote hain"),
        ("Meher ka public archive access policy draft karna", "sensitive gawahon ki hifazat shamil hoti hai"),
        ("Zoya ka independent audit mandate propose karna", "council apne ikhtiyarat share karne par behas karti hai"),
        ("naye muahiday ka public vote karwana", "final oversight mechanism ke liye raasta khulta hai"),
    )),
    ("Subah Ka Daira", "Accountability, marammat aur khula mustaqbil", (
        ("damaged grid ki phased repair report banana", "har repair ki verification schedule hoti hai"),
        ("Laila ka apni team ka conflict disclose karna", "team ki leadership ko public scrutiny milti hai"),
        ("Meher ka 300-day archive index taiyar karna", "future generations ke liye provenance bachta hai"),
        ("Rayan ka failsafe ke independent test results dena", "safety team se bahar verify hoti hai"),
        ("Aman ka restored clinics ka follow-up lena", "logon ki zindagi mein farq ko measure kiya jata hai"),
        ("public oversight ko final authority dena", "daira band nahi hota: nayi zimmedari shuru hoti hai"),
    )),
)

REVEALS = {
    60: "Radio pulse ka asal source shehar ka purana terrestrial relay hai.",
    120: "Grid ke records rural ilaqon se energy diversion ka pattern dikhate hain.",
    180: "Guardian protocol shehar ke founders ne khud design kiya tha.",
    240: "Proposed reset se zaroori audit evidence mit sakta tha.",
    300: "Grid par public oversight aur independent audit ka naya muahida lagu hota hai.",
}

CHARACTERS = (
    {"id": "laila", "role": "young observatory technician", "boundary": "cannot override live grid"},
    {"id": "rayan", "role": "repair engineer", "boundary": "tests patches offline first"},
    {"id": "meher", "role": "archivist", "boundary": "preserves source and custody"},
    {"id": "aman", "role": "community medic", "boundary": "patient safety first"},
    {"id": "zoya", "role": "independent inspector", "boundary": "requires corroboration"},
)

WORLD_RULES = (
    "Signals travel through physical relays; no supernatural foresight or time travel.",
    "Grid energy is finite; every reroute has a measurable cost.",
    "No one can remotely control a person or erase memories.",
    "Evidence requires source, timestamp and independent custody.",
    "No reset, hack or repair occurs on a live public grid without authorized safety review.",
)


def validate_series(manifest: dict) -> None:
    """Reject inconsistent chronology, unearned reveals and fabricated completion."""
    if not isinstance(manifest, dict):
        raise ValueError("invalid_manifest")
    episodes = manifest.get("episodes")
    if not isinstance(episodes, list) or len(episodes) != TARGET_EPISODES:
        raise ValueError("invalid_episode_count")
    if manifest.get("target_total_minutes") != 9000 or manifest.get("rendered_episodes") != 0:
        raise ValueError("false_completion_or_duration")
    if manifest.get("approval") != "proposed_not_owner_approved":
        raise ValueError("false_approval")
    seen = set()
    for expected, episode in enumerate(episodes, 1):
        if not isinstance(episode, dict) or episode.get("number") != expected:
            raise ValueError("nonsequential_episode")
        if episode.get("arc") != (expected - 1) // EPISODES_PER_ARC + 1:
            raise ValueError("arc_drift")
        if episode.get("sequence") != ((expected - 1) % 30) // 5 + 1:
            raise ValueError("sequence_drift")
        if episode.get("beat") != ((expected - 1) % 5) + 1:
            raise ValueError("beat_drift")
        if episode.get("story_day") != (expected + 1) // 2:
            raise ValueError("day_drift")
        if episode.get("previous_episode") != (expected - 1 or None):
            raise ValueError("causality_drift")
        if not isinstance(episode.get("event"), str) or len(episode["event"]) < 20:
            raise ValueError("empty_event")
        if not isinstance(episode.get("handoff"), str) or len(episode["handoff"]) < 20:
            raise ValueError("empty_handoff")
        key = (episode["event"], episode["beat"])
        if key in seen:
            raise ValueError("duplicate_beat")
        seen.add(key)
        if episode.get("revelations_known") != [REVEALS[n] for n in sorted(REVEALS) if n <= expected]:
            raise ValueError("reveal_leak")
    if len(manifest.get("arcs", [])) != 10 or len(manifest.get("characters", [])) != 5:
        raise ValueError("invalid_bible")


def series_manifest() -> dict:
    """Return a fresh deterministic 300-beat chronology with no external effects."""
    if len(ARCS) != 10 or any(len(arc[2]) != 6 for arc in ARCS):
        raise ValueError("invalid_arc_source")
    episodes = []
    for arc_index, (name, focus, sequences) in enumerate(ARCS, 1):
        for sequence_index, (event, handoff) in enumerate(sequences, 1):
            for beat_index, (beat_name, beat_action) in enumerate(BEATS, 1):
                number = (arc_index - 1) * 30 + (sequence_index - 1) * 5 + beat_index
                episodes.append({
                    "number": number,
                    "id": f"EP{number:03d}",
                    "arc": arc_index,
                    "arc_title": name,
                    "arc_focus": focus,
                    "sequence": sequence_index,
                    "beat": beat_index,
                    "title": f"{name}: {beat_name} {sequence_index}",
                    "story_day": (number + 1) // 2,
                    "previous_episode": number - 1 or None,
                    "event": event,
                    "action": beat_action,
                    "handoff": handoff,
                    "revelations_known": [REVEALS[n] for n in sorted(REVEALS) if n <= number],
                    "status": "outline_only",
                })
    manifest = {
        "title": TITLE,
        "version": 1,
        "approval": "proposed_not_owner_approved",
        "language": "Pakistani Roman Urdu / Urdu (scripts to be reviewed separately)",
        "target_episodes": TARGET_EPISODES,
        "target_minutes_per_episode": MINUTES_PER_EPISODE,
        "target_total_minutes": TARGET_EPISODES * MINUTES_PER_EPISODE,
        "rendered_episodes": 0,
        "reviewed_scripts": 0,
        "arcs": [{"number": i, "title": arc[0], "focus": arc[1], "sequences": len(arc[2])}
                 for i, arc in enumerate(ARCS, 1)],
        "characters": deepcopy(list(CHARACTERS)),
        "world_rules": list(WORLD_RULES),
        "episodes": episodes,
    }
    validate_series(manifest)
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return manifest
