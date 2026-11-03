"""Task 48: privacy-minimal, offline Flora sales/campaign evidence summaries.

Only trusted Python callers may supply bounded, already-redacted records. This
module does not fetch sales, infer sales from impressions, verify external
receipts, read customer details, or publish anything. No HTTP/write route.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date

try:
    from .flora_catalog import FloraCatalogError, catalogue_snapshot
    from .flora_campaign import PLATFORMS
except ImportError:  # direct Python import from cloud_backend/
    from flora_catalog import FloraCatalogError, catalogue_snapshot
    from flora_campaign import PLATFORMS


class FloraReportingError(ValueError):
    """The proposed offline report cannot be grounded safely."""


_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z", re.ASCII)
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z", re.ASCII)
_DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_MAX_ROWS = 250
_MAX_MONEY = 10_000_000
_MAX_METRIC = 10_000_000
_SOURCES_SALES = frozenset(("owner_manual_export", "private_shop_export"))
_SOURCES_CAMPAIGN = frozenset(("owner_manual_export", "platform_export"))
_SALE_FIELDS = frozenset((
    "record_id", "date", "product_id", "units", "received_pkr",
    "refunded_pkr", "source", "campaign_revision_sha256",
))
_CAMPAIGN_FIELDS = frozenset((
    "record_id", "date", "platform", "campaign_revision_sha256",
    "impressions", "clicks", "inquiries", "spend_pkr", "source",
))


def _day(value: str) -> date:
    if type(value) is not str or _DATE_RE.fullmatch(value) is None:
        raise FloraReportingError("Dates must use YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise FloraReportingError("Invalid calendar date.") from None


def _bounded_int(value: object, *, minimum: int = 0, maximum: int = _MAX_METRIC) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise FloraReportingError("Invalid bounded non-negative integer.")
    return value


def _row(value: object, fields: frozenset[str], optional: frozenset[str] = frozenset()) -> dict:
    if type(value) is not dict or not (fields - optional) <= value.keys() or not value.keys() <= fields:
        raise FloraReportingError("Record schema invalid; remove personal or extra fields.")
    identifier = value["record_id"]
    if type(identifier) is not str or _ID_RE.fullmatch(identifier) is None:
        raise FloraReportingError("Invalid opaque record ID.")
    return value


def _digest(value: object, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise FloraReportingError("Invalid campaign revision digest.")
    return value


def _records(value: object) -> list:
    if type(value) is not list or len(value) > _MAX_ROWS:
        raise FloraReportingError("Too many or invalid report records.")
    return value


def _snapshot_products() -> set[str]:
    try:
        snapshot = catalogue_snapshot()
        products = snapshot["products"]
        if (snapshot["read_only"] is not True or
                snapshot["no_actual_product_photos_available"] is not True or
                not isinstance(products, list)):
            raise FloraReportingError("Catalogue approval state inconsistent.")
        ids = set()
        for item in products:
            if (item["price"]["current_price_independently_verified"] is not False
                    or item["photo"]["approved_for_publication"] is not False):
                raise FloraReportingError("Catalogue approval state inconsistent.")
            ids.add(item["id"])
        if ids != {"gold_kit", "shampoo"}:
            raise FloraReportingError("Unexpected Flora catalogue.")
        return ids
    except (FloraCatalogError, KeyError, TypeError):
        raise FloraReportingError("Flora catalogue could not be verified.") from None


def build_flora_evidence_report(
    start_date: str,
    end_date: str,
    sales_records: list,
    campaign_records: list,
) -> dict:
    """Summarize only caller-supplied redacted evidence for a 31-day window.

    All amounts/metrics are *reported*, not audited. A missing source is null,
    not a fabricated zero. No revenue is derived from catalogue list prices.
    """
    start, end = _day(start_date), _day(end_date)
    if end < start or (end - start).days > 30:
        raise FloraReportingError("Report window must be 1 to 31 calendar days.")
    sales_rows, campaign_rows = _records(sales_records), _records(campaign_records)
    product_ids = _snapshot_products()
    seen_sales, seen_campaigns = set(), set()
    sales, campaigns = [], []

    for original in sales_rows:
        item = _row(original, _SALE_FIELDS, frozenset(("campaign_revision_sha256",)))
        identifier = item["record_id"]
        if identifier in seen_sales:
            raise FloraReportingError("Duplicate sales record ID.")
        seen_sales.add(identifier)
        day = _day(item["date"])
        if (not start <= day <= end or type(item["product_id"]) is not str
                or item["product_id"] not in product_ids):
            raise FloraReportingError("Sales record outside allowed scope.")
        if type(item["source"]) is not str or item["source"] not in _SOURCES_SALES:
            raise FloraReportingError("Unsupported sales evidence source.")
        units = _bounded_int(item["units"], minimum=1, maximum=1000)
        received = _bounded_int(item["received_pkr"], maximum=_MAX_MONEY)
        refunded = _bounded_int(item["refunded_pkr"], maximum=_MAX_MONEY)
        if refunded > received:
            raise FloraReportingError("Refund exceeds reported receipts.")
        sales.append({
            "record_id": identifier, "date": day.isoformat(),
            "product_id": item["product_id"], "units": units,
            "received_pkr": received, "refunded_pkr": refunded,
            "source": item["source"],
            "campaign_revision_sha256": _digest(
                item.get("campaign_revision_sha256"), optional=True
            ),
        })

    for original in campaign_rows:
        item = _row(original, _CAMPAIGN_FIELDS, frozenset(("spend_pkr",)))
        identifier = item["record_id"]
        if identifier in seen_campaigns:
            raise FloraReportingError("Duplicate campaign record ID.")
        seen_campaigns.add(identifier)
        day = _day(item["date"])
        if (not start <= day <= end or type(item["platform"]) is not str
                or item["platform"] not in PLATFORMS):
            raise FloraReportingError("Campaign record outside allowed scope.")
        if type(item["source"]) is not str or item["source"] not in _SOURCES_CAMPAIGN:
            raise FloraReportingError("Unsupported campaign evidence source.")
        impressions = _bounded_int(item["impressions"])
        clicks = _bounded_int(item["clicks"])
        inquiries = _bounded_int(item["inquiries"])
        if clicks > impressions:
            raise FloraReportingError("Reported clicks exceed impressions.")
        spend = item.get("spend_pkr")
        if spend is not None:
            spend = _bounded_int(spend, maximum=_MAX_MONEY)
        campaigns.append({
            "record_id": identifier, "date": day.isoformat(),
            "platform": item["platform"],
            "campaign_revision_sha256": _digest(item["campaign_revision_sha256"]),
            "impressions": impressions, "clicks": clicks,
            "inquiries": inquiries, "spend_pkr": spend,
            "source": item["source"],
        })

    by_product = {}
    for item in sales:
        row = by_product.setdefault(item["product_id"], {
            "record_count": 0, "units": 0, "received_pkr": 0,
            "refunded_pkr": 0, "net_pkr": 0,
        })
        row["record_count"] += 1
        row["units"] += item["units"]
        row["received_pkr"] += item["received_pkr"]
        row["refunded_pkr"] += item["refunded_pkr"]
        row["net_pkr"] += item["received_pkr"] - item["refunded_pkr"]

    by_platform = {}
    for item in campaigns:
        row = by_platform.setdefault(item["platform"], {
            "record_count": 0, "impressions": 0, "clicks": 0,
            "inquiries": 0, "spend_pkr": 0, "spend_coverage_complete": True,
        })
        row["record_count"] += 1
        for field in ("impressions", "clicks", "inquiries"):
            row[field] += item[field]
        if item["spend_pkr"] is None:
            row["spend_coverage_complete"] = False
        else:
            row["spend_pkr"] += item["spend_pkr"]
    for row in by_platform.values():
        if not row["spend_coverage_complete"]:
            row["spend_pkr"] = None

    # A campaign revision tag is a caller-provided label, not proof of causality.
    # Never calculate conversion, ROAS, profit, or ROI from unmatched exports.
    payload = {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "sales": sorted(sales, key=lambda row: row["record_id"]),
        "campaigns": sorted(campaigns, key=lambda row: row["record_id"]),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "version": "flora-evidence-report-v1",
        "status": "draft_requires_source_reconciliation" if sales or campaigns else "no_source_records",
        "period": payload["period"],
        "source_status": "operator_supplied_unverified",
        "source_revision_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "sales": None if not sales else {
            "record_count": len(sales),
            "units": sum(row["units"] for row in sales),
            "received_pkr": sum(row["received_pkr"] for row in sales),
            "refunded_pkr": sum(row["refunded_pkr"] for row in sales),
            "net_pkr": sum(row["received_pkr"] - row["refunded_pkr"] for row in sales),
            "by_product": {key: by_product[key] for key in sorted(by_product)},
        },
        "campaigns": None if not campaigns else {
            "record_count": len(campaigns),
            "impressions": sum(row["impressions"] for row in campaigns),
            "clicks": sum(row["clicks"] for row in campaigns),
            "inquiries": sum(row["inquiries"] for row in campaigns),
            "spend_coverage_complete": all(row["spend_pkr"] is not None for row in campaigns),
            "spend_pkr": sum(row["spend_pkr"] for row in campaigns)
                         if all(row["spend_pkr"] is not None for row in campaigns) else None,
            "by_platform": {key: by_platform[key] for key in sorted(by_platform)},
        },
        "attribution_verified": False,
        "conversion_rate": None,
        "return_on_ad_spend": None,
        "profit_pkr": None,
        "independently_reconciled": False,
        "publishable": False,
        "persisted": False,
        "external_accounts_accessed": False,
        "orders_created": False,
        "limitations": [
            "No external sales or platform records were fetched or verified.",
            "Missing records are unknown, not zero sales or zero impressions.",
            "Campaign revision tags do not prove sales attribution.",
            "List prices, ad spend, profit and ROI are never inferred.",
        ],
    }
