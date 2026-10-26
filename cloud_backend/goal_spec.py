"""Deterministic goal -> deliverables contract for HOSHI.

This is a planning/specification function, not an executor. It never stores
raw prompts, starts jobs, purchases services, or fabricates generated files.
"""
import re

try:
    from .task_router import route_task
except ImportError:  # uvicorn main:app launched from cloud_backend/ directly
    from task_router import route_task


_DELIVERABLES = {
    "create_product_ads": (
        ("feed_creative", "1080x1350 PNG", "Original illustrative feed creative"),
        ("story_creative", "1080x1920 PNG", "Original illustrative story creative"),
        ("captions", "UTF-8 text", "Product-specific caption copy"),
        ("storyboard", "UTF-8 text", "Video storyboard; not a rendered MP4"),
        ("ad_pack", "ZIP", "Downloadable package of generated assets"),
    ),
    "build_game": (
        ("game_design", "Markdown", "Game design document and scope"),
        ("game_project", "Source project", "Editable game engine project"),
        ("art_audio", "Asset directory", "Original or licensed art and audio"),
        ("playable_build", "Web or APK", "Actual playable export, not screenshots"),
        ("qa_report", "JSON/Markdown", "Gameplay, crash and performance test results"),
    ),
    "render_anime": (
        ("series_bible", "Markdown", "Characters, story rules and continuity bible"),
        ("episode_scripts", "UTF-8 text", "Individually reviewed Hindi/Urdu episode scripts"),
        ("storyboards", "Image sequence", "Episode shots and visual continuity plans"),
        ("audio_tracks", "Audio files", "Synchronized voice and legally usable audio"),
        ("rendered_episodes", "MP4", "Actually rendered episodes, not prompts or stills"),
        ("episode_qc", "JSON/Markdown", "Per-episode audiovisual QC and archive manifest"),
    ),
    "chart_analysis": (
        ("market_snapshot", "JSON", "Timestamped source-identified OHLCV data"),
        ("technical_analysis", "JSON", "Reproducible indicator and support/resistance values"),
        ("annotated_chart", "PNG", "Actual annotated chart with timeframe"),
        ("risk_notes", "Markdown", "Paper-only scenarios with assumptions and risk"),
    ),
    "device_action": (
        ("permission_check", "JSON", "Explicit Android permission and allowed-action check"),
        ("action_receipt", "JSON", "Verified device action result, not just an intent"),
    ),
    "ask_explanation": (("answer", "Text", "Clear explanation of the user's question"),),
    "conversation": (("answer", "Text", "Answer matched to user's language and context"),),
    "empty": (),
}


def _scope(message: str, intent: str) -> dict:
    """Capture only numeric scope, not private free-form user text."""
    if intent != "render_anime":
        return {}
    count = re.search(r"\b(\d{1,5})\s*(?:episodes?|ep)\b", message, re.I)
    if not count:
        count = re.search(r"\b(?:episodes?|ep)\s*(?:of|:)?\s*(\d{1,5})\b", message, re.I)
    duration = re.search(r"\b(\d{1,4})\s*(?:minutes?|mins?)\b", message, re.I)
    scope = {}
    if count:
        scope["episode_count"] = int(count.group(1))
    if duration:
        scope["minutes_per_episode"] = int(duration.group(1))
    if "episode_count" in scope and "minutes_per_episode" in scope:
        scope["total_requested_minutes"] = scope["episode_count"] * scope["minutes_per_episode"]
    return scope


def goal_to_deliverables(message: str) -> dict:
    """Describe what success requires; never imply deliverables were produced."""
    route = route_task(message)
    intent = route.intent
    specs = _DELIVERABLES.get(intent, _DELIVERABLES["conversation"])
    scope = _scope(str(message or ""), intent)
    blockers = []
    if not route.ready:
        blockers.append(route.reason)
    if intent == "render_anime" and (scope.get("episode_count", 1) > 1000 or scope.get("minutes_per_episode", 1) > 180):
        blockers.append("Requested scope exceeds current planning guardrails; requires a staged feasibility review.")
    return {
        "intent": intent,
        "mode": route.mode,
        "executor_ready": route.ready,
        "execution_status": "not_started",
        "deliverables": [
            {"id": key, "format": fmt, "acceptance": description, "status": "planned"}
            for key, fmt, description in specs
        ],
        "scope": scope,
        "blockers": blockers,
        "cost_policy": "free_first_no_paid_services_without_explicit_approval",
        "notes": "A specification is not a completed project. No background job or external action was started.",
    }
