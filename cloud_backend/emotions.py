"""Validated Hoshi companion states. No network calls or hidden emotion inference.

These are *animation requests*, not proof that sprite layers exist.
Unsupported poses must stay neutral until matching approved artwork is supplied.
"""
from __future__ import annotations

EMOTIONS = frozenset({
    "neutral", "happy", "excited", "playful", "shy", "affectionate",
    "curious", "thinking", "confused", "worried", "sad", "crying",
    "annoyed", "angry", "apologetic", "sleepy", "caring",
})
ANIMATIONS = frozenset({"idle", "smile", "sad_eyes", "thinking", "blush", "excited"})
GESTURES = frozenset({"none", "look_down", "head_tilt", "small_wave"})
VOICE_STYLES = frozenset({"soft", "warm", "playful", "gentle"})

def companion_state(proposed: object, fallback_emotion: str = "neutral") -> dict:
    """Validate untrusted provider metadata; unknown values get safe defaults."""
    candidate = proposed if isinstance(proposed, dict) else {}
    fallback_emotion = {"concerned": "worried"}.get(fallback_emotion, fallback_emotion)
    fallback = fallback_emotion if fallback_emotion in EMOTIONS else "neutral"
    raw_emotion = candidate.get("emotion")
    emotion = fallback if raw_emotion is None else (
        raw_emotion if isinstance(raw_emotion, str) and raw_emotion in EMOTIONS else "neutral"
    )
    intensity = candidate.get("emotion_intensity", 0.45)
    if isinstance(intensity, bool) or not isinstance(intensity, (int, float)) or not (0 <= intensity <= 1):
        intensity = 0.45
    animation = candidate.get("animation", "idle")
    if not isinstance(animation, str) or animation not in ANIMATIONS:
        animation = "idle"
    gesture = candidate.get("gesture", "none")
    if not isinstance(gesture, str) or gesture not in GESTURES:
        gesture = "none"
    voice_style = candidate.get("voice_style", "soft")
    if not isinstance(voice_style, str) or voice_style not in VOICE_STYLES:
        voice_style = "soft"
    return {
        "emotion": emotion,
        "emotion_intensity": float(intensity),
        "animation": animation,
        "gesture": gesture,
        "voice_style": voice_style,
    }
