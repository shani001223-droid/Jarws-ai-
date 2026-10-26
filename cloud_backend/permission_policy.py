"""Server-side HOSHI agent action permission policy.

Every newly added agent tool must be explicitly added here and wired to a
verified execution handler. A boolean sent from a browser cannot confer
permission to post, purchase, delete files, control a device, or trade.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDecision:
    known: bool
    allowed: bool
    approval_required: bool
    reason: str


# Backend-only allowlist. The sole existing executor makes local
# illustration-based ads and returns downloadable files; no external writes.
_AUTO_ALLOWED = frozenset({"create_product_ads"})

# These high-impact tasks are recognized for *denial*, not executable handlers.
# A future authenticated, reviewed workflow must register them separately.
_APPROVAL_REQUIRED = frozenset({
    "publish_social", "send_message", "send_email", "change_account_settings",
    "modify_external_files", "screen_control", "make_purchase", "delete_user_data",
})

# Never expose real-money trading or raw system execution as an agent endpoint.
_FORBIDDEN = frozenset({"live_trade", "withdraw_funds", "execute_shell", "run_arbitrary_code"})

# Future creative project types are not executable merely because user requests.
_NOT_IMPLEMENTED = frozenset({"build_game", "render_anime", "render_mp4", "autonomous_project"})


def check_agent_action(task: str) -> PermissionDecision:
    name = str(task or "").strip().lower()
    if name in _AUTO_ALLOWED:
        return PermissionDecision(True, True, False, "Approved local artifact generator.")
    if name in _FORBIDDEN:
        return PermissionDecision(True, False, False, "High-risk action is disabled.")
    if name in _APPROVAL_REQUIRED:
        return PermissionDecision(True, False, True,
            "Requires a separate authenticated, explicit approval workflow.")
    if name in _NOT_IMPLEMENTED:
        return PermissionDecision(True, False, False,
            "Project worker is not implemented or verified.")
    return PermissionDecision(False, False, False, "Unknown agent action.")
