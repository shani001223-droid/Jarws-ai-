"""Deterministic free-first model routing for HOSHI's existing assistant.

This module *selects* usable configured providers, but does not create model
accounts, override quotas, silently purchase services or claim availability.
The caller still validates output and performs bounded fallback.
"""
from dataclasses import dataclass

try:
    from .openjarvis_bridge import wants_agent
except ImportError:
    from openjarvis_bridge import wants_agent


@dataclass(frozen=True)
class ProviderPlan:
    order: tuple[str, ...]
    priority: str | None
    fast_voice_first: bool
    agent_first: bool


def choose_providers(
    message: str,
    *,
    fast: bool,
    openrouter: bool,
    gemini: bool,
    groq: bool,
    openjarvis: bool,
) -> ProviderPlan:
    """Build a nonduplicated failover order using only explicitly configured services."""
    agent_first = bool(openjarvis and wants_agent(message, fast=fast))
    fast_voice_first = bool(fast and groq)
    priority = (
        (["openjarvis"] if agent_first else [])
        + (["groq"] if fast_voice_first else [])
        + (["openrouter"] if openrouter else [])
        + (["gemini"] if gemini else [])
        + (["groq"] if groq else [])
    )
    order = tuple(dict.fromkeys(priority))
    return ProviderPlan(order, order[0] if order else None, fast_voice_first, agent_first)
