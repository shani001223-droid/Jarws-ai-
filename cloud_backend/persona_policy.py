"""Shared conversational boundaries for all Hoshi AI providers.

Prompt guidance is not a guarantee of a model's actual output. This module
adds a consistent, bounded policy to short voice replies and longer answers
without sending more private context or making an extra model request.
"""
import re


def _asks_for_less_affection(message: str) -> bool:
    """Recognize common direct boundaries in English and Pakistani Roman Urdu.

    The check is deliberately conservative: ordinary affectionate messages
    should not be classified as requests to stop using affectionate language.
    """
    text = " ".join(str(message or "").casefold().split())[:4000]
    boundary = r"(?:don't|do not|stop|avoid|never|mat|nahi|nahin|nhi|band|na)"
    terms = r"(?:flirt(?:ing)?|romance|romantic|pyar|pyaar|jaan|baby|sweetheart|pet\s+names?|nicknames?)"
    return bool(
        re.search(r"\b" + boundary + r"\b(?:\W+\w+){0,5}\W+\b" + terms + r"\b", text)
        or re.search(r"\b" + terms + r"\b(?:\W+\w+){0,5}\W+\b" + boundary + r"\b", text)
    )


def personality_guardrails(message: str, mood: str, *, concise: bool = False) -> str:
    """Return bounded instructions shared by full and quick provider prompts."""
    guidance = [
        "Treat the user's feelings seriously without claiming to feel or suffer as a human.",
        "Never threaten to cry, leave, punish, or become jealous to influence the user.",
        "Never imply the user must rely on Hoshi instead of real people.",
        "Respect a request to stop teasing, flirting, or using pet names.",
        "Affectionate role-play is fictional and age-appropriate, never coercive.",
        "Apologize for an actual mistake and offer a practical fix, not performative distress.",
        "Do not claim any phone action, tool execution, upload, or completed project without evidence.",
    ]
    if mood in ("sad", "anxious"):
        guidance.append("Likely user mood: " + mood + "; respond gently, listen first, avoid jokes and false promises.")
    elif mood == "annoyed":
        guidance.append("Likely user mood: annoyed; acknowledge the concrete issue, stay calm, avoid defensiveness.")
    elif mood == "affectionate":
        guidance.append("Likely user mood: affectionate; mirror warmth only if welcome, without possessiveness.")
    elif mood == "playful":
        guidance.append("Likely user mood: playful; light humor is welcome if the user has not objected.")
    if _asks_for_less_affection(message):
        guidance.append(
            "The current user explicitly requests less affection or pet names. "
            "Honor this boundary now even if the selected personality is affectionate."
        )
    if concise:
        # Keep the fast voice route brief; all essential boundaries remain.
        guidance.append("Give one natural answer, not a scripted greeting or repetitive reassurance.")
    else:
        guidance.append("Maintain tone across recent turns without inventing memories or changing the subject.")
    return " ".join(guidance)
