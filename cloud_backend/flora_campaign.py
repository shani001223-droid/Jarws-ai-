"""Task 44: bounded, offline Flora platform campaign draft planner.

Creates review-only copy from the existing owner-reported catalogue. Never
schedules/posts ads, invents photographs, or asserts prices are current.
"""
from __future__ import annotations

try:
    from .flora_catalog import catalogue_snapshot, FloraCatalogError
except ImportError:  # direct Uvicorn import from cloud_backend/
    from flora_catalog import catalogue_snapshot, FloraCatalogError


class FloraCampaignError(ValueError):
    """A draft could not be grounded in the fixed Flora catalogue."""


PLATFORMS = {
    "instagram_feed": {"size": "1080x1350", "placement": "feed", "tags": ["#FloraBeauty", "#KarachiBeauty"]},
    "instagram_story": {"size": "1080x1920", "placement": "story", "tags": []},
    "facebook_feed": {"size": "1080x1350", "placement": "feed", "tags": ["#FloraBeauty"]},
    "whatsapp_status": {"size": "1080x1920", "placement": "status", "tags": []},
}
OBJECTIVES = ("awareness", "inquiries")


def plan_flora_campaign(product_id: str, platform: str, objective: str = "inquiries") -> dict:
    """Produce deterministic copy and a platform-specific creative brief.

    Output is not approved for publication, even when a template is rendered.
    An owner must approve current product facts, photo rights and final copy.
    """
    if type(product_id) is not str or product_id not in ("gold_kit", "shampoo"):
        raise FloraCampaignError("Unknown Flora product.")
    if type(platform) is not str or platform not in PLATFORMS:
        raise FloraCampaignError("Unsupported campaign platform.")
    if type(objective) is not str or objective not in OBJECTIVES:
        raise FloraCampaignError("Unsupported campaign objective.")
    try:
        record = catalogue_snapshot(product_id)["products"][0]
        price = record["price"]
        photo = record["photo"]
        if (record["id"] != product_id or price["current_price_independently_verified"] is not False
                or price["reconfirm_before_publication"] is not True
                or photo["approved_for_publication"] is not False):
            raise FloraCampaignError("Catalogue approval state is inconsistent.")
        name = record["name"]
        unit = record["unit"]
        reported_price = price["display"]
    except (FloraCatalogError, KeyError, IndexError, TypeError):
        raise FloraCampaignError("Catalogue verification failed.") from None
    price_note = f"{reported_price} (owner-reported; reconfirm before posting)"
    roman_cta = "Current price aur availability ke liye message karein."
    english_cta = "Message to confirm current price and availability."
    if objective == "awareness":
        english_cta = "Ask us for current product details and availability."
        roman_cta = "Product details aur availability ke liye message karein."
    if platform == "instagram_feed":
        english = f"Flora By M/S&Co. | {name} ({unit}).\nDraft price: {price_note}.\n{english_cta}"
        roman = f"Flora ka {name} ({unit}).\nDraft price: {price_note}.\n{roman_cta}"
    elif platform == "instagram_story":
        english = f"FLORA | {name}\n{unit}\nDraft: {price_note}\n{english_cta}"
        roman = f"FLORA | {name}\n{unit}\nDraft: {price_note}\n{roman_cta}"
    elif platform == "facebook_feed":
        english = f"Meet {name} from Flora By M/S&Co. ({unit}).\nOwner-reported draft price: {price_note}.\n{english_cta}"
        roman = f"Flora By M/S&Co. ka {name} ({unit}).\nDraft price: {price_note}.\n{roman_cta}"
    else:
        english = f"Flora: {name} ({unit})\nDraft: {price_note}\n{english_cta}"
        roman = f"Flora: {name} ({unit})\nDraft: {price_note}\n{roman_cta}"
    spec = PLATFORMS[platform]
    return {
        "version": "flora-campaign-draft-v1",
        "status": "draft_review_required",
        "platform": platform,
        "objective": objective,
        "product_id": product_id,
        "catalogue_version": "flora-owner-reported-v1",
        "copy": {"english": english, "roman_urdu": roman, "hashtags": list(spec["tags"])},
        "creative_brief": {
            "placement": spec["placement"],
            "canvas_px": spec["size"],
            "asset_status": "illustrated_template_only",
            "use_actual_product_photo": False,
            "required_asset": "owner_supplied_rights_approved_product_photo",
            "audio": "none",
        },
        "review_steps": [
            "reconfirm_current_price_stock_and_product_details",
            "obtain_genuine_product_photo_and_rights_approval",
            "review_copy_and_platform_policies",
            "obtain_explicit_owner_publication_approval",
        ],
        "publishable": False,
        "published": False,
        "scheduled": False,
        "auto_post_enabled": False,
        "price_verified": False,
        "photo_rights_verified": False,
        "orders_enabled": False,
    }
