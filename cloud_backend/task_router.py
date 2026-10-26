"""Honest, deterministic first-stage Hoshi task router.

Routing does not itself execute screen actions, generate a game, or render anime.
It dispatches only registered existing tools and labels all unimplemented
capabilities clearly. No network/model calls are required to route.
"""
import re
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class TaskRoute:
    mode: str
    intent: str
    ready: bool
    executor: str | None
    needs_device_permission: bool
    reason: str

    def as_payload(self):
        return asdict(self)


_CREATE = re.compile(r"\b(?:bana\w*|make|build|create|generate|design|develop|tayyar|produce|render|likh\w*)\b", re.I)
_EXPLAIN = re.compile(r"\b(?:kaise|how to|how do|tutorial|explain|samjhao|seekha\w*|guide|meaning|kya hai|what is)\b", re.I)
_AD = re.compile(r"\b(?:ads?|advertisements?|posters?|promos?|creatives?)\b|اشتہار|ایڈ", re.I)
_PRODUCT = re.compile(r"\b(?:product\w*|flora|facial|shampoo|gold|mere|mara|meri)\b", re.I)
_TRADING = re.compile(r"\b(?:btc|bitcoin|eth|ethereum|crypto|trading|chart|candles?)\b", re.I)
_TA = re.compile(r"\b(?:analy[sz]\w*|mark\w*|support|resistance|indicator\w*|strateg\w*|entry|stop.?loss|signals?|lagao|lagado|dikhao)\b", re.I)
_GAME = re.compile(r"\b(?:games?|gameplay|playable|mobile game|apk game)\b", re.I)
_ANIME = re.compile(r"\b(?:anime|episodes?|animated series|cartoon series)\b", re.I)
_SCREEN = re.compile(r"\b(?:screen|tap|scroll|phone|mobile|browser|whatsapp|youtube|open app)\b", re.I)
_MOBILE_ACTION = re.compile(r"\b(?:open|launch|start|tap|scroll|type|click|khol\w*|chalao)\b", re.I)


def route_task(message: str) -> TaskRoute:
    """Choose workflow type; do not promise execution if worker is absent."""
    normalized = " ".join(str(message or "").strip().split())
    if not normalized:
        return TaskRoute("chat", "empty", False, None, False, "Message cannot be empty.")
    if _EXPLAIN.search(normalized):
        return TaskRoute("chat", "ask_explanation", True, "assistant", False,
                         "Question should be answered as conversation, not silently executed.")
    if _AD.search(normalized) and _CREATE.search(normalized) and _PRODUCT.search(normalized):
        return TaskRoute("backend_tool", "create_product_ads", True, "create_product_ads", False,
                         "Existing product-ad tool can produce real PNG/ZIP assets, not video.")
    if _ANIME.search(normalized) and _CREATE.search(normalized):
        return TaskRoute("backend_project", "render_anime", False, None, False,
                         "Multi-episode animation worker, durable queue and render infrastructure are not ready.")
    if _GAME.search(normalized) and _CREATE.search(normalized):
        return TaskRoute("backend_project", "build_game", False, None, False,
                         "Game project worker is not yet implemented.")
    if _TRADING.search(normalized) and _TA.search(normalized):
        return TaskRoute("screen_agent", "chart_analysis", False, None, True,
                         "Current market APIs exist, but automatic chart marking is not verified.")
    if _SCREEN.search(normalized) and _MOBILE_ACTION.search(normalized):
        return TaskRoute("screen_agent", "device_action", False, None, True,
                         "A user-approved Android bridge is required; web backend cannot control a device.")
    return TaskRoute("chat", "conversation", True, "assistant", False,
                     "Use the existing assistant route and configured model providers.")
