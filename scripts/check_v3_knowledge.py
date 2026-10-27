"""Check the V3 curriculum's declared scope, content floor and file receipts.

Mechanical checks cannot certify historical truth or runtime integration.
Run this before each chapter commit; never count pending files as delivered.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path, PurePosixPath
import re

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


def check():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["schema_version"] == "hoshi-v3-curriculum-1"
    assert manifest["minimum_body_words"] >= 1000
    seen, folders, done = set(), set(), []
    for doc in manifest["documents"]:
        rel = PurePosixPath(doc["path"])
        assert (not rel.is_absolute() and ".." not in rel.parts and len(rel.parts) == 3
                and rel.parts[0] == "knowledge_base" and rel.parts[1] in FOLDERS
                and rel.suffix == ".md"), rel
        assert str(rel) not in seen, rel
        seen.add(str(rel)); folders.add(rel.parts[1])
        path = ROOT / str(rel)
        if doc["status"] == "pending":
            assert not path.exists(), f"Unreviewed chapter must not be counted/pushed as complete: {rel}"
            continue
        assert doc["status"] == "source_checked", (rel, doc["status"])
        raw = path.read_bytes()
        assert len(raw) <= 1000000, rel
        text = raw.decode("utf-8")
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
        done.append({"path": str(rel), "body_words": count})
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
        for item in payload["observations"]:
            assert item["status"] in ("fetched", "unavailable")
            if item["status"] == "unavailable":
                assert "return_pct" not in item, "Missing data cannot become a zero return"
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
            "curriculum_percent": round(len(done)/total*100, 2),
            "scope": "declared curriculum files only; not all trading knowledge or runtime completion",
            "documents": done, "integration_gates": manifest["integration_gates"]}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
