import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICON_PATH = ROOT / "assets" / "hoshi-app-icon.svg"


class HoshiPwaManifestTests(unittest.TestCase):
    def test_manifest_declares_standard_install_icon_sizes(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("display"), "standalone")
        icons = manifest.get("icons", [])
        for size in ("192x192", "512x512"):
            matches = [
                icon for icon in icons
                if icon.get("src") == "./assets/hoshi-app-icon.svg"
                and icon.get("sizes") == size
                and icon.get("type") == "image/svg+xml"
                and "maskable" in icon.get("purpose", "").split()
            ]
            self.assertTrue(matches, f"manifest should include a maskable HOSHI SVG icon for {size}")
        self.assertTrue(ICON_PATH.is_file(), "referenced HOSHI app icon asset must exist")

    def test_app_icon_is_well_formed_svg(self):
        root = ET.parse(ICON_PATH).getroot()
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(root.attrib.get("viewBox"), "0 0 512 512")

    def test_document_references_manifest_and_favicon(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="manifest" href="./manifest.json">', html)
        self.assertIn('<link rel="icon" type="image/svg+xml" href="./assets/hoshi-app-icon.svg">', html)


if __name__ == "__main__":
    unittest.main()
