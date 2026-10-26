# Hoshi Room Life v1 — implementation / acceptance notes

Created on 26 October 2026 as incremental work on top of the latest main branch. This is **a 2D room activity and expression-sprite animation**, not a Live2D, skeletal or per-phoneme rig.

## Implemented in source
- Reuses existing approved Hoshi bedroom and `assets/hoshi-expressions.webp` (eight expression cells); never swaps the original character for new/generic art.
- Separate animated room props: gaming monitor, phone/reels icon, music glow and ambient illumination (CSS, no new image downloads).
- Small approved Hoshi expression portrait animates breathing, occasional approximate blink, speaking mouth, happy/shy/sad/playful/angry moods. It is a distinct animated portrait, **not an actual face replacement on the full bedroom photograph**.
- Scenes: Relax, Gaming, Reels, Dance, Rest through a single Room menu, or direct commands: `game khelo`, `reels dekho`, `dance karo`, `so jao`, `normal ho jao`. Changes are scene simulations; they do not launch or consume real games, reels or streaming music.
- Dance tap optionally starts a quiet original sine-wave melody synthesized with Web Audio locally; network not used. Voice-command dance gives visual mode only because browser autoplay policy may block sound.
- Assistant `listening`, `thinking`, `speaking`, `idle` state events now update a separate scene state. Speaking mouth loop starts on real speech playback callback, but is **approximate rhythmic motion**, not energy- or phoneme-based lip sync.
- Lightweight CSS animations respect reduced-motion, Settings animation toggle, low mobile GPU budget and background lifecycle.
- Optional in-app suggestions are **OFF by default**, limited to Hoshi's own Trading and AI Influencer tabs, dismissible and throttled to once per 10 minutes. No outside-app awareness, hidden screen capture, continuous uploads, microphone monitoring or auto-trading.
- All existing Chat, Trading, AI Influencer, Outfit, Settings tabs, memory, reminders, native shortcuts and backend services remain in source.
- CI adds Node unit and real-browser Playwright regression checks.

## Remaining artwork (cannot faithfully fake)
The bedroom photo `assets/hoshi-nightroom.webp` is a flattened image. For Hoshi to walk to her real gaming PC, sit, hold a phone, dance with movable arms, blink **on her actual room face**, cry and do accurate audio-energy lip-sync, an artist must separate that **same approved Hoshi** and room into spatially aligned transparent layers / poses. Required: clean room-only base; cut-out full-body Hoshi, head/arms/hair; aligned eyebrow/eye closed/open and 4 mouth shapes; pose frame sequences for gaming, mobile, dance; outfit layers sharing identical pivots. No generic replacement/face redesign.

## Device and testing acceptance
Check PR browser CI and Android WebView manually on Realme Note 50 for phone layout, reduced motion, CPU/battery, actual voice interruptions and audio permissions. Mocked and CI tests do not prove device voice or full animated character. Do not promise 24/7 screen monitoring. The current version adds no paid API or framework dependency. The app can continue running via existing hosting, subject to provider quotas.
