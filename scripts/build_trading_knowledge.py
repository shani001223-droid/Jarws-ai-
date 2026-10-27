"""Rebuild the backend-only deployment bundle from canonical root knowledge."""
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cloud_backend.brain import MODULE_FILES, VERSION  # noqa: E402


def build():
    lessons = []
    for key, filename, title, keywords in MODULE_FILES:
        text = (ROOT / "modules" / filename).read_text(encoding="utf-8")
        lessons.append({"id": key, "filename": filename, "title": title,
                        "keywords": list(keywords), "content": text,
                        "sha256": sha256(text.encode("utf-8")).hexdigest()})
    prompt = (ROOT / "HOSHI_SYSTEM_PROMPT_FINAL.txt").read_text(encoding="utf-8")
    return {"version": VERSION, "lessons": lessons, "system_prompt": prompt,
            "system_prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest()}


if __name__ == "__main__":
    result = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    target = ROOT / "cloud_backend" / "knowledge_bundle.json"
    if sys.argv[1:] == ["--check"]:
        if target.read_text(encoding="utf-8") != result:
            raise SystemExit("Knowledge bundle differs; run python scripts/build_trading_knowledge.py")
        print("All 11 lessons and final prompt match the deployment bundle")
    elif not sys.argv[1:]:
        target.write_text(result, encoding="utf-8")
        print("Built 11-lesson backend knowledge bundle")
    else:
        raise SystemExit("Usage: build_trading_knowledge.py [--check]")
