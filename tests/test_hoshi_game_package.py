"""Task 54: deterministic, tamper-evident standalone offline web export."""
import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from package_hoshi_game import (  # noqa: E402
    ARCHIVE_NAME, OFFLINE_NAME, README_NAME, SUMS_NAME,
    GAME_DIR, build_offline_html, build_release, verify_archive,
)


class OfflineGamePackageTests(unittest.TestCase):
    def test_deterministic_real_zip_and_checksum(self):
        with tempfile.TemporaryDirectory() as temp:
            first = build_release(Path(temp) / "one")
            second = build_release(Path(temp) / "two")
            self.assertEqual(first.name, ARCHIVE_NAME)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(len(verify_archive(first)), 64)
            with zipfile.ZipFile(first) as zipped:
                self.assertEqual(zipped.namelist(), [OFFLINE_NAME, README_NAME, SUMS_NAME])
                html = zipped.read(OFFLINE_NAME)
                self.assertEqual(html, (Path(temp) / "one" / OFFLINE_NAME).read_bytes())
                self.assertIn(b'const EMBEDDED_MANIFEST=', html)
                self.assertIn(b'connect-src &#39;none&#39;', html)
                self.assertNotIn(b'<script src=', html)
                self.assertNotIn(b'<link rel="stylesheet"', html)
                self.assertNotIn(b'<script type="module">', html)
                self.assertNotIn(b'fetch("./levels.json"', html)
                self.assertNotIn(b'https://', html)
                self.assertLess(len(html), 150_000)
                self.assertEqual(
                    zipped.read(SUMS_NAME).decode("ascii"),
                    hashlib.sha256(html).hexdigest() + "  " + OFFLINE_NAME + "\n",
                )

    def test_tampered_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = build_release(Path(temp))
            with zipfile.ZipFile(archive, "r") as zipped:
                members = [(name, zipped.read(name)) for name in zipped.namelist()]
            with zipfile.ZipFile(archive, "w") as zipped:
                for name, data in members:
                    zipped.writestr(name, data + b"tampered" if name == OFFLINE_NAME else data)
            with self.assertRaisesRegex(ValueError, "checksum_mismatch"):
                verify_archive(archive)

    def test_unexpected_remote_import_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("index.html", "levels.json", "art.mjs", "animation.mjs",
                         "gameplay.mjs", "engine.mjs"):
                (root / name).write_bytes((GAME_DIR / name).read_bytes())
            with (root / "art.mjs").open("a", encoding="utf-8") as stream:
                stream.write('\nimport "https://example.invalid/untrusted.js";\n')
            with self.assertRaisesRegex(ValueError, "unsupported_game_module"):
                build_offline_html(root)


if __name__ == "__main__":
    unittest.main()
