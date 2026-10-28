"""Check the V3 curriculum's declared scope, content floor and file receipts.

Mechanical checks cannot certify historical truth or runtime integration.
Run this before each chapter commit; pending and draft files are not delivered.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path, PurePosixPath
import re

from v3_structure_evidence import check_window
from v3_pattern_evidence import check_receipt as check_pattern_receipt
from v3_zone_evidence import check_receipt as check_zone_receipt
from v3_smc_evidence import check_receipt as check_smc_receipt
from v3_ict_evidence import check_receipt as check_ict_receipt
from v3_liquidity_evidence import check_receipt as check_liquidity_receipt
from v3_fvg_evidence import check_receipt as check_fvg_receipt
from v3_indicator_evidence import check_receipt as check_indicator_receipt
from v3_macro_evidence import check_receipt as check_macro_receipt
from v3_risk_evidence import check_receipt as check_risk_receipt
from v3_news_evidence import check_receipt as check_news_receipt
from v3_session_evidence import check_receipt as check_session_source_receipt

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge_base/manifest.json"
FOLDERS = {
    "00_HISTORY_OF_EVERYTHING", "01_MARKET_STRUCTURE",
    "02_CANDLESTICK_AND_CHART_PATTERNS", "03_SUPPLY_DEMAND_ORDERBLOCKS",
    "04_SMC_COMPLETE", "05_ICT_COMPLETE", "06_LIQUIDITY_GOD",
    "07_FVG_IMBALANCE", "08_INDICATORS_AND_ORDERFLOW", "09_GLOBAL_MONEY_FLOW",
    "10_TRADING_PSYCHOLOGY_AND_RISK", "11_NEWS_TRADING",
}


def content_words(text):
    body = text.split("## Sources", 1)[0]
    body = re.sub(r"https?://\S+", "", body)
    return len(re.findall(r"\b\w+(?:['’\-]\w+)*\b", body))


def document_state(doc, path):
    """A written draft may be reviewed, but cannot become completion by relabelling."""
    state = doc["status"]
    if state == "pending":
        assert not path.exists(), f"Existing incomplete files must be explicitly declared draft: {path.name}"
        return state
    assert state in ("draft", "source_checked"), state
    assert path.is_file() and not path.is_symlink(), path.name
    if state == "draft":
        blockers = doc.get("completion_blockers")
        assert (isinstance(blockers, list) and blockers
                and all(isinstance(x, str) and 1 <= len(x) <= 2000 for x in blockers)), path.name
        assert doc.get("runtime_eligible") is False, path.name
    else:
        assert not doc.get("completion_blockers"), f"Unresolved completion blockers: {path.name}"
        assert "runtime_eligible" not in doc or doc["runtime_eligible"] is True, path.name
    return state


def check():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["schema_version"] == "hoshi-v3-curriculum-2"
    policy = manifest["document_status_policy"]
    assert (policy["version"] == 2 and policy["drafts_count_as_complete"] is False
            and policy["drafts_runtime_eligible"] is False)
    assert manifest["minimum_body_words"] >= 1000
    seen, folders, done, drafts = set(), set(), [], []
    for doc in manifest["documents"]:
        rel = PurePosixPath(doc["path"])
        assert (not rel.is_absolute() and ".." not in rel.parts and len(rel.parts) == 3
                and rel.parts[0] == "knowledge_base" and rel.parts[1] in FOLDERS
                and rel.suffix == ".md"), rel
        assert str(rel) not in seen, rel
        seen.add(str(rel)); folders.add(rel.parts[1])
        path = ROOT / str(rel)
        state = document_state(doc, path)
        if state == "pending":
            continue
        raw = path.read_bytes()
        assert len(raw) <= 1000000, rel
        text = raw.decode("utf-8")
        if state == "draft":
            assert "INCOMPLETE DRAFT" in text[:1500], (rel, "missing visible draft warning")
        else:
            assert "INCOMPLETE DRAFT" not in text[:1500], (rel, "visible draft cannot be completed")
        count = content_words(text)
        assert count >= manifest["minimum_body_words"], (rel, count)
        assert count == doc["body_word_count"], (rel, "word-count receipt drift")
        assert hashlib.sha256(raw).hexdigest() == doc["sha256"], (rel, "digest drift")
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", doc["reviewed_on"]), rel
        lowered = text.lower()
        for section in ("## what is it?", "## why does it form?", "## application zone",
                        "## failure zones", "## three real historical examples with dates",
                        "## how to use it to hunt a trade", "## sources"):
            assert section in lowered, (rel, "missing required section", section)
        examples = re.findall(r"^### Example [123] .+$", text, re.MULTILINE)
        assert len(examples) == 3 and all(re.search(r"\b\d{4}\b", x) for x in examples), rel
        assert len(re.findall(r"\]\(https://[^)]+\)", text)) >= 3, (rel, "missing source links")
        record = {"path": str(rel), "body_words": count}
        if state == "draft":
            drafts.append(record)
        else:
            done.append(record)
    assert folders == FOLDERS, "Every requested folder family must remain in the declared scope"
    actual = {str(p.relative_to(ROOT)) for p in (ROOT / "knowledge_base").rglob("*.md")}
    assert actual <= seen, "Unmanifested curriculum files: " + str(actual-seen)
    for receipt in manifest.get("data_receipts", []):
        rel = PurePosixPath(receipt["path"])
        assert (len(rel.parts) == 3 and rel.parts[0] == "knowledge_base"
                and rel.parts[1] in FOLDERS and ".." not in rel.parts
                and rel.suffix == ".json"), rel
        raw = (ROOT / str(rel)).read_bytes()
        assert len(raw) <= 1000000 and hashlib.sha256(raw).hexdigest() == receipt["sha256"], rel
        payload = json.loads(raw)
        kind = receipt.get("kind", "crash_windows")
        assert kind in ("crash_windows", "event_windows", "ohlcv_windows", "pattern_cases", "zone_cases", "smc_cases", "ict_intraday", "liquidity_cases", "fvg_cases", "indicator_cases", "macro_cases", "synthetic_risk", "news_events", "session_source_audit"), kind
        if kind == "session_source_audit":
            check_session_source_receipt(payload, ROOT)
            continue
        if kind == "news_events":
            check_news_receipt(payload, ROOT)
            continue
        if kind == "synthetic_risk":
            check_risk_receipt(payload, ROOT)
            continue
        if kind == "macro_cases":
            check_macro_receipt(payload, ROOT)
            continue
        if kind == "indicator_cases":
            check_indicator_receipt(payload, ROOT)
            continue
        if kind == "fvg_cases":
            check_fvg_receipt(payload, ROOT)
            continue
        if kind == "liquidity_cases":
            check_liquidity_receipt(payload, ROOT)
            continue
        if kind == "ict_intraday":
            check_ict_receipt(payload, ROOT)
            continue
        if kind == "smc_cases":
            check_smc_receipt(payload, ROOT)
            continue
        if kind == "zone_cases":
            check_zone_receipt(payload, ROOT)
            continue
        if kind == "pattern_cases":
            check_pattern_receipt(payload, ROOT)
            continue
        if kind == "ohlcv_windows":
            assert payload["schema_version"] == "hoshi-v3-ohlcv-evidence-1"
            assert payload["data_license"] == "CC BY-NC-SA 4.0"
            assert len(payload["observations"]) == 3
            for item in payload["observations"]:
                check_window(item)
            continue
        for item in payload["observations"]:
            assert item["status"] in ("fetched", "unavailable")
            if item["status"] == "unavailable":
                assert "return_pct" not in item, "Missing data cannot become a zero return"
                continue
            if kind == "event_windows":
                assert item["series"] == "NASDAQCOM"
                assert item["request_url"].startswith("https://fred.stlouisfed.org/graph/fredgraph.csv?")
                assert re.fullmatch(r"[0-9a-f]{64}", item["source_sha256"])
                event = date.fromisoformat(item["event_date"])
                before = item["pre_event_close"]
                assert date.fromisoformat(before["date"]) < event
                assert type(before["close"]) in (int, float) and before["close"] > 0 and math.isfinite(before["close"])
                sessions = item["post_event_trading_sessions"]
                assert set(sessions) <= {"1", "5", "20"} and "1" in sessions
                previous = None
                for n in sorted(sessions, key=int):
                    observation = sessions[n]
                    stamp = date.fromisoformat(observation["date"])
                    value = observation["close"]
                    assert stamp >= event and (previous is None or stamp > previous)
                    assert type(value) in (int, float) and value > 0 and math.isfinite(value)
                    assert math.isclose(observation["return_from_pre_event_close_pct"], (value/before["close"]-1)*100, abs_tol=1e-9)
                    previous = stamp
                continue
            assert item["series"] in ("NASDAQCOM", "SP500")
            assert item["url"].startswith("https://fred.stlouisfed.org/graph/fredgraph.csv?")
            peak_date, peak = item["peak"]
            trough_date, trough = item["later_window_low"]
            assert all(type(x) in (int, float) and math.isfinite(x) and x > 0 for x in (peak, trough))
            assert peak_date <= trough_date and trough <= peak
            assert math.isclose(item["return_pct"], (trough/peak-1)*100, abs_tol=1e-9)
            assert item["peak_to_window_low_calendar_days"] == (date.fromisoformat(trough_date)-date.fromisoformat(peak_date)).days
    total = len(manifest["documents"])
    assert total and len(done) <= total
    return {"completed_documents": len(done), "planned_documents": total,
            "draft_documents": len(drafts), "drafts": drafts,
            "curriculum_source_complete": len(done) == total,
            "curriculum_percent": round(len(done)/total*100, 2),
            "scope": "declared curriculum files only; not all trading knowledge or runtime completion",
            "documents": done, "integration_gates": manifest["integration_gates"]}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
