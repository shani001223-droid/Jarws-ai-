"""Versioned local trading curriculum and bounded retrieval; no model training.

Canonical Markdown stays at repository /modules. A hash-checked JSON snapshot is
shipped in Render's cloud_backend-only Docker build. Never read user paths/URLs.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re

VERSION = "hoshi-trading-knowledge-v2"
MODULE_FILES = (
    ("history", "trading_history_complete.md", "Trading History", ("history", "timeline", "dow theory", "wyckoff", "elliott", "tareekh", "تاریخ")),
    ("market_structure", "01_market_structure.md", "Market Structure", ("market structure", "bos", "choch", "mss", "support", "resistance", "trend")),
    ("candlestick_psychology", "02_candlestick_psychology.md", "Candlestick Psychology", ("candlestick", "candle", "engulfing", "wick", "inside bar")),
    ("order_blocks", "03_order_blocks.md", "Order Blocks", ("order block", "order blocks", "ob", "displacement")),
    ("smc", "04_smc.md", "SMC", ("smc", "smart money", "institutional")),
    ("ict", "05_ict.md", "ICT", ("ict", "killzone", "kill zone", "silver bullet", "power of three", "power of 3", "po3")),
    ("liquidity", "06_liquidity.md", "Liquidity", ("liquidity", "inducement", "turtle soup", "bsl", "ssl", "sweep")),
    ("fvg_imbalances", "07_fvg_imbalances.md", "FVG and Imbalances", ("fvg", "fair value gap", "imbalance", "imbalances")),
    ("indicators_order_flow", "08_indicators_order_flow.md", "Indicators and Order Flow", ("indicator", "indicators", "order flow", "rsi", "ema", "atr", "vwap", "cvd", "delta")),
    ("global_money_flow", "09_global_money_flow.md", "Global Money Flow", ("dxy", "bonds", "cot", "intermarket", "money flow", "yields", "dollar")),
    ("risk_psychology", "10_risk_psychology.md", "Risk and Psychology", ("risk", "psychology", "stop loss", "take profit", "drawdown", "position size", "accuracy", "confluence")),
)


class KnowledgeError(ValueError):
    """Missing or mismatched trusted curriculum; never echo file paths."""


@dataclass(frozen=True)
class Lesson:
    id: str
    filename: str
    title: str
    keywords: tuple[str, ...]
    content: str
    digest: str


@dataclass(frozen=True)
class Knowledge:
    lessons: tuple[Lesson, ...]
    system_prompt: str


def _digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def load_knowledge() -> Knowledge:
    """Load ALL 11 lessons once; reject incomplete or corrupted bundles."""
    try:
        raw = Path(__file__).with_name("knowledge_bundle.json").read_bytes()
        if len(raw) > 200_000:
            raise KnowledgeError("oversized_bundle")
        payload = json.loads(raw)
        if payload["version"] != VERSION or len(payload["lessons"]) != len(MODULE_FILES):
            raise KnowledgeError("incomplete_bundle")
        lessons = []
        for entry, (key, filename, title, keywords) in zip(payload["lessons"], MODULE_FILES):
            content = entry["content"]
            if (entry["id"] != key or entry["filename"] != filename
                    or entry["title"] != title or entry["keywords"] != list(keywords)
                    or not isinstance(content, str) or not 500 <= len(content) <= 15_000
                    or _digest(content) != entry["sha256"]):
                raise KnowledgeError("invalid_lesson")
            if key != "history" and any(heading not in content for heading in (
                    "## Definition", "## Application Zone", "## Failure Zone", "## 3 Live Chart Examples")):
                raise KnowledgeError("incomplete_lesson")
            lessons.append(Lesson(key, filename, title, keywords, content, entry["sha256"]))
        prompt = payload["system_prompt"]
        if (not isinstance(prompt, str) or not 400 <= len(prompt) <= 5_000
                or _digest(prompt) != payload["system_prompt_sha256"]):
            raise KnowledgeError("invalid_system_prompt")
        return Knowledge(tuple(lessons), prompt)
    except KnowledgeError:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise KnowledgeError("knowledge_unavailable") from exc


def knowledge_index() -> dict:
    return {"version": VERSION, "mode": "educational-knowledge-only",
            "training_enabled": False, "orders_enabled": False,
            "lessons": [{"id": x.id, "title": x.title, "sha256": x.digest}
                        for x in load_knowledge().lessons]}


def get_lesson(module_id: str) -> dict:
    for x in load_knowledge().lessons:
        if module_id == x.id:
            return {"version": VERSION, "id": x.id, "title": x.title,
                    "content": x.content, "sha256": x.digest,
                    "mode": "educational-knowledge-only", "training_enabled": False,
                    "live_examples_verified": False, "orders_enabled": False}
    raise KeyError("unknown_lesson")


def _matches(term: str, text: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text))


def trading_context(message: str) -> str:
    """Retrieve two relevant lesson excerpts; don't bloat unrelated chat prompts."""
    text = message[:4000].casefold()
    gate = ("trading", "trade", "bitcoin", "btc", "eth", "forex", "stock",
            "market", "candlestick", "candle", "fvg", "order block", "smc", "ict",
            "liquidity", "bsl", "ssl", "rsi", "ema", "vwap", "atr", "dxy", "cot",
            "wyckoff", "elliott", "killzone", "kill zone", "silver bullet", "confluence",
            "stop loss", "take profit", "ٹریڈنگ", "مارکیٹ")
    if not any(_matches(word, text) for word in gate):
        return ""
    knowledge = load_knowledge()
    ranked = sorted(enumerate(knowledge.lessons), key=lambda ix: (
        -sum(_matches(word, text) for word in ix[1].keywords), ix[0]))
    selected = [x for _, x in ranked if any(_matches(w, text) for w in x.keywords)][:2]
    if not selected:
        selected = [next(x for x in knowledge.lessons if x.id == "risk_psychology")]
    chunks = ["Trusted versioned educational reference; not live market observations. "
              "Confluence is rule coverage, never win probability. No orders or guaranteed accuracy."]
    for lesson in selected:
        if lesson.id == "history":
            excerpt = lesson.content[:2400]
        else:
            parts = []
            for heading, bound in (("Definition", 550), ("Application Zone", 650), ("Failure Zone", 650)):
                section = lesson.content.split("## " + heading + "\n\n", 1)[1].split("\n## ", 1)[0]
                parts.append(heading + ": " + section.strip()[:bound])
            excerpt = "\n".join(parts)
        chunks.append(f"[{lesson.id}; {VERSION}; sha256={lesson.digest}]\n" + excerpt)
    return "\n\n".join(chunks)[:4800]
