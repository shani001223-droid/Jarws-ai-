"""Task 43: catalogue integrity, provenance and image-safety regression."""
from io import BytesIO
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from cloud_backend import main
from cloud_backend import flora_catalog
from cloud_backend.ad_studio import CATALOG


class FloraCatalogueTests(unittest.TestCase):
    def test_catalogue_matches_existing_renderer_and_owner_prices(self):
        snapshot = flora_catalog.catalogue_snapshot()
        self.assertEqual(len(snapshot["products"]), 2)
        self.assertEqual({p["id"] for p in snapshot["products"]}, set(CATALOG))
        self.assertEqual({p["id"]: p["price"]["amount_pkr"] for p in snapshot["products"]},
                         {"gold_kit": 3500, "shampoo": 1500})
        for product in snapshot["products"]:
            self.assertFalse(product["price"]["current_price_independently_verified"])
            self.assertTrue(product["price"]["reconfirm_before_publication"])
            self.assertIsNone(product["photo"]["asset_path"])
            self.assertIsNone(product["photo"]["sha256"])
            self.assertFalse(product["photo"]["rights_verified"])
            self.assertEqual(product["creative_status"], "illustrated_template_only")

    def test_catalogue_is_detached_and_cannot_mutate_renderer(self):
        first = flora_catalog.catalogue_snapshot()
        first["products"][0]["details"].clear()
        first["products"][0]["price"]["amount_pkr"] = 1
        self.assertEqual(flora_catalog.catalogue_snapshot("gold_kit")["products"][0]["price"]["amount_pkr"], 3500)
        self.assertTrue(CATALOG["gold_kit"]["details"])

    def test_invalid_id_and_catalogue_price_drift_fail_closed(self):
        with self.assertRaises(flora_catalog.FloraCatalogError):
            flora_catalog.catalogue_snapshot("../secret")
        with patch.dict(CATALOG["shampoo"], {"price": "RS. 100"}):
            with self.assertRaises(flora_catalog.FloraCatalogError):
                flora_catalog.catalogue_snapshot()

    def test_public_read_only_route_and_no_store_headers(self):
        client = TestClient(main.app)
        response = client.get("/api/flora/catalog")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["products"]), 2)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertNotIn("zip_base64", response.text)
        single = client.get("/api/flora/catalog", params={"product_id": "shampoo"})
        self.assertEqual(single.status_code, 200)
        self.assertEqual(len(single.json()["products"]), 1)
        invalid = client.get("/api/flora/catalog", params={"product_id": "not-listed"})
        self.assertEqual(invalid.status_code, 422)
        self.assertNotIn("not-listed", invalid.text)

    def test_photo_inspection_does_not_claim_rights_or_save_image(self):
        image = Image.new("RGB", (640, 800), "white")
        data = BytesIO()
        image.save(data, format="PNG")
        report = flora_catalog.inspect_owner_photo(data.getvalue(), "image/png")
        self.assertEqual((report["width"], report["height"]), (640, 800))
        self.assertEqual(len(report["sha256"]), 64)
        self.assertFalse(report["saved"])
        self.assertFalse(report["approved_for_publication"])
        self.assertFalse(report["owner_rights_verified"])

    def test_rejects_corrupt_wrong_mime_tiny_and_oversized_images(self):
        with self.assertRaises(flora_catalog.FloraCatalogError):
            flora_catalog.inspect_owner_photo(b"not an image", "image/png")
        with self.assertRaises(flora_catalog.FloraCatalogError):
            flora_catalog.inspect_owner_photo(b"x" * 8_000_001, "image/png")
        with self.assertRaises(flora_catalog.FloraCatalogError):
            flora_catalog.inspect_owner_photo("not bytes", "image/png")
        image = Image.new("RGB", (640, 800))
        out = BytesIO()
        image.save(out, format="PNG")
        with self.assertRaises(flora_catalog.FloraCatalogError):
            flora_catalog.inspect_owner_photo(out.getvalue(), "image/jpeg")
        tiny = BytesIO()
        Image.new("RGB", (120, 120)).save(tiny, format="PNG")
        with self.assertRaises(flora_catalog.FloraCatalogError):
            flora_catalog.inspect_owner_photo(tiny.getvalue(), "image/png")


if __name__ == "__main__":
    unittest.main()
