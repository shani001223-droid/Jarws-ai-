#!/usr/bin/env python3
"""Build and verify the standalone, offline Hoshi Star Trail web export.

No external modules, network, APK changes or deployment. Source files are a
strict allowlist: an unexpected import/export aborts instead of being bundled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game-studio"
OFFLINE_NAME = "Hoshi-Star-Trail-offline.html"
ARCHIVE_NAME = "Hoshi-Star-Trail-offline.zip"
README_NAME = "README.txt"
SUMS_NAME = "SHA256SUMS.txt"
MODULES = ("art.mjs", "animation.mjs", "gameplay.mjs", "engine.mjs")
ENGINE_IMPORT = 'import { drawOriginalTile } from "./art.mjs";'
PAGE_IMPORTS = (
    'import {validateManifest,paintPreview} from "./engine.mjs";',
    'import {createPreviewAnimation} from "./animation.mjs";',
    'import {DEFAULT_PROGRESS,createGameState,moveGame,undoGame,restartGame,unlockProgress,readSavedProgress,writeSavedProgress,clearSavedProgress} from "./gameplay.mjs";',
)
FETCH_BLOCK = (
    '  const response=await fetch("./levels.json",{cache:"no-store"});\n'
    '  if(!response.ok)throw new Error("local_manifest_unavailable");\n'
    '  levels=validateManifest(await response.json());'
)
README = (
    "Hoshi Star Trail - private offline web export\n"
    "Unzip and open Hoshi-Star-Trail-offline.html in a modern browser.\n"
    "It contains all six levels and original Canvas artwork; no server, account,\n"
    "network, paid assets or installation is required. No Android APK is included.\n"
    "Local progress saving is OFF until you opt in. Browser file:// storage\n"
    "support varies; the game remains playable if storage is unavailable.\n"
    "SHA256SUMS.txt verifies the HTML file. This is a review-only CI artifact,\n"
    "not a production deployment or physical Realme Note 50 acceptance.\n"
)
CSP = (
    '<meta http-equiv="Content-Security-Policy" '
    'content="default-src &#39;none&#39;; script-src &#39;unsafe-inline&#39;; '
    'style-src &#39;unsafe-inline&#39;; img-src data:; connect-src &#39;none&#39;; '
    'object-src &#39;none&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;">'
)


def _read_source(directory: Path, name: str, limit: int) -> str:
    path = directory / name
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("invalid_game_source_" + name)
    return path.read_text(encoding="utf-8")


def _without_exports(source: str, name: str) -> str:
    transformed = re.sub(r"(?m)^export (?=(?:function|const) )", "", source)
    if re.search(r"(?m)^\s*(?:import|export)\s", transformed):
        raise ValueError("unsupported_game_module_" + name)
    return transformed


def build_offline_html(directory: Path = GAME_DIR) -> bytes:
    html = _read_source(directory, "index.html", 100_000)
    if html.count('<script type="module">') != 1 or html.count("<script") != 1:
        raise ValueError("unexpected_game_script_layout")
    if html.count('<meta charset="utf-8">') != 1:
        raise ValueError("unexpected_game_head")
    manifest = json.loads(_read_source(directory, "levels.json", 16_000))
    if (not isinstance(manifest, dict) or manifest.get("version") != "gdd-v1"
            or manifest.get("status") != "playable_local_mvp"
            or not isinstance(manifest.get("levels"), list)
            or len(manifest["levels"]) != 6):
        raise ValueError("invalid_game_manifest")
    modules = []
    for name in MODULES:
        source = _read_source(directory, name, 35_000)
        if name == "engine.mjs":
            if source.count(ENGINE_IMPORT) != 1:
                raise ValueError("unexpected_game_engine_import")
            source = source.replace(ENGINE_IMPORT, "", 1)
        modules.append(_without_exports(source, name))
    match = re.search(r'<script type="module">\n([\s\S]*?)\n</script>', html)
    if not match:
        raise ValueError("missing_game_entrypoint")
    entry = match.group(1)
    for statement in PAGE_IMPORTS:
        if entry.count(statement) != 1:
            raise ValueError("unexpected_game_page_import")
        entry = entry.replace(statement, "", 1)
    if entry.count(FETCH_BLOCK) != 1:
        raise ValueError("unexpected_game_manifest_loader")
    entry = entry.replace(FETCH_BLOCK, "  levels=validateManifest(EMBEDDED_MANIFEST);", 1)
    if re.search(r"(?m)^\s*(?:import|export)\s", entry):
        raise ValueError("unsupported_game_entrypoint")
    manifest_js = json.dumps(manifest, ensure_ascii=True, separators=(",", ":"))
    js = ('"use strict";\nconst EMBEDDED_MANIFEST=' + manifest_js + ';\n'
          + "\n".join(modules) + "\n" + entry + "\n")
    if (re.search(r"</script", js, flags=re.IGNORECASE)
            or re.search(r"\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon)\s*\(", js)
            or re.search(r"\bawait\b", js)):
        raise ValueError("offline_game_contains_network_or_unsupported_script")
    offline = html[:match.start()] + "<script>\n" + js + "</script>" + html[match.end():]
    offline = offline.replace('<meta charset="utf-8">',
                              '<meta charset="utf-8">\n' + CSP, 1)
    if re.search(r"https?://", offline, flags=re.IGNORECASE):
        raise ValueError("offline_game_external_reference")
    result = offline.encode("utf-8")
    if len(result) > 150_000:
        raise ValueError("offline_game_too_large")
    return result


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info


def build_release(output: Path, directory: Path = GAME_DIR) -> Path:
    html = build_offline_html(directory)
    output.mkdir(parents=True, exist_ok=True)
    html_path = output / OFFLINE_NAME
    html_path.write_bytes(html)
    checksum = hashlib.sha256(html).hexdigest()
    files = (
        (OFFLINE_NAME, html),
        (README_NAME, README.encode("utf-8")),
        (SUMS_NAME, (checksum + "  " + OFFLINE_NAME + "\n").encode("ascii")),
    )
    archive = output / ARCHIVE_NAME
    with zipfile.ZipFile(archive, "w") as zipped:
        for name, data in files:
            zipped.writestr(_zip_info(name), data)
    verify_archive(archive)
    return archive


def verify_archive(archive: Path) -> str:
    if not archive.is_file() or archive.stat().st_size > 180_000:
        raise ValueError("invalid_game_archive")
    with zipfile.ZipFile(archive, "r") as zipped:
        infos = zipped.infolist()
        if [info.filename for info in infos] != [OFFLINE_NAME, README_NAME, SUMS_NAME]:
            raise ValueError("unexpected_game_archive_members")
        if any(info.file_size > 150_000 or info.flag_bits & 1 for info in infos):
            raise ValueError("invalid_game_archive_member")
        html = zipped.read(OFFLINE_NAME)
        sums = zipped.read(SUMS_NAME).decode("ascii")
        expected = hashlib.sha256(html).hexdigest() + "  " + OFFLINE_NAME + "\n"
        if sums != expected:
            raise ValueError("offline_game_checksum_mismatch")
        if (b'const EMBEDDED_MANIFEST=' not in html
                or b'<meta http-equiv="Content-Security-Policy"' not in html
                or b'<script type="module">' in html
                or b'fetch("./levels.json"' in html):
            raise ValueError("invalid_offline_game_payload")
        zipped.read(README_NAME).decode("utf-8")
        return hashlib.sha256(archive.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("game-release"))
    parser.add_argument("--verify", type=Path, help="Verify an existing offline ZIP instead")
    args = parser.parse_args()
    if args.verify:
        print("Verified offline game ZIP SHA-256:", verify_archive(args.verify))
    else:
        archive = build_release(args.out)
        print("Offline game ZIP:", archive)
        print("Verified archive SHA-256:", verify_archive(archive))


if __name__ == "__main__":
    main()
