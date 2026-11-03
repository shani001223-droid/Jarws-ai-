"""Task 47: offline Flora post draft and proposed-slot review, never a scheduler.

A proposed time is not a queued or scheduled post. No account tokens, uploads,
external platform clients, persistence, approvals or publication are performed.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

try:
    from .flora_campaign import FloraCampaignError, plan_flora_campaign
except ImportError:  # direct Uvicorn import from cloud_backend/
    from flora_campaign import FloraCampaignError, plan_flora_campaign


class FloraPostPlanError(ValueError):
    """Invalid post preview request or ungrounded catalogue/campaign data."""


_PKT = timezone(timedelta(hours=5))
_SLOT_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+05:00\Z", re.ASCII)
_MIN_NOTICE = timedelta(hours=2)
_MAX_HORIZON = timedelta(days=30)
_GATES = (
    "reconfirm_current_price_stock_and_product_details",
    "verify_owner_photo_audio_rights_and_final_assets",
    "approve_final_copy_and_platform_policy_compliance",
    "obtain_explicit_owner_publication_approval",
    "authorize_target_social_account_and_exact_post",
)


def preview_flora_post(
    product_id: str,
    platform: str,
    objective: str = "inquiries",
    proposed_local_time: str | None = None,
    *,
    now: datetime | None = None,
) -> dict:
    """Return a reproducible review-only post and optional Karachi time slot.

    The clock override is for trusted offline tests; it is never exposed by
    the HTTP route. Even a valid proposed slot is NOT persisted or scheduled.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise FloraPostPlanError("A timezone-aware clock is required.")
    if proposed_local_time is not None and (
        type(proposed_local_time) is not str or not _SLOT_RE.fullmatch(proposed_local_time)
    ):
        raise FloraPostPlanError("Proposed time must be Karachi ISO 8601 (+05:00) with seconds.")
    try:
        campaign = plan_flora_campaign(product_id, platform, objective)
    except (FloraCampaignError, KeyError, TypeError):
        raise FloraPostPlanError("Flora campaign could not be verified.") from None
    if (campaign.get("status") != "draft_review_required"
            or campaign.get("publishable") is not False
            or campaign.get("scheduled") is not False
            or campaign.get("published") is not False
            or campaign.get("price_verified") is not False
            or campaign.get("photo_rights_verified") is not False):
        raise FloraPostPlanError("Campaign safety state is inconsistent.")
    slot = None
    if proposed_local_time is not None:
        try:
            candidate = datetime.fromisoformat(proposed_local_time)
            if candidate.utcoffset() != timedelta(hours=5):
                raise ValueError("invalid offset")
            delta = candidate.astimezone(timezone.utc) - now.astimezone(timezone.utc)
            if not (_MIN_NOTICE <= delta <= _MAX_HORIZON):
                raise ValueError("outside permitted preview window")
        except ValueError:
            raise FloraPostPlanError("Proposed time must be 2 hours to 30 days in the future.") from None
        slot = {
            "timezone": "Asia/Karachi",
            "local": candidate.astimezone(_PKT).isoformat(timespec="seconds"),
            "utc": candidate.astimezone(timezone.utc).isoformat(timespec="seconds"),
            "review_by_utc": (candidate.astimezone(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds"),
            "status": "proposal_only_not_scheduled",
        }
    revision = {
        "product_id": campaign["product_id"],
        "platform": campaign["platform"],
        "objective": campaign["objective"],
        "catalogue_version": campaign["catalogue_version"],
        "copy": campaign["copy"],
        "creative_brief": campaign["creative_brief"],
        "slot": slot,
    }
    digest = hashlib.sha256(json.dumps(revision, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "version": "flora-post-preview-v1",
        "status": "draft_review_required",
        "revision_sha256": digest,
        "product_id": campaign["product_id"],
        "platform": campaign["platform"],
        "objective": campaign["objective"],
        "copy": campaign["copy"],
        "creative_brief": campaign["creative_brief"],
        "proposed_slot": slot,
        "approval_gates": [{"code": code, "approved": False} for code in _GATES],
        "publishable": False,
        "approved": False,
        "persisted": False,
        "queued": False,
        "scheduled": False,
        "published": False,
        "external_account_connected": False,
        "auto_post_enabled": False,
        "dry_run_only": True,
        "next_step": "owner_review_required_before_any_future_account_action",
    }
