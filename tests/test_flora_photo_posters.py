"""Task 45: offline real-PNG preview and fail-closed provenance tests."""
import hashlib
from io import BytesIO
import unittest
from unittest.mock import patch

from PIL import Image

from cloud_backend import flora_photo_posters as posters
from cloud_backend.ad_studio import CATALOG


def synthetic_photo():
    """Only a synthetic test fixture; never a genuine product photograph."""
    image = Image.new("RGB", (800, 1000), (22, 99, 157))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class FloraPhotoPosterTests(unittest.TestCase):
    def test_real_png_previews_for_both_products_and_placements(self):
        photo = synthetic_photo()
        for product in ("gold_kit", "shampoo"):
            for placement, expected_size in (("feed", (1080, 1350)), ("story", (1080, 1920))):
                with self.subTest(product=product, placement=placement):
                    result = posters.render_flora_photo_preview(product, photo, "image/png", placement)
                    self.assertEqual(result["canvas_px"], list(expected_size))
                    self.assertEqual(result["source_photo_sha256"], hashlib.sha256(photo).hexdigest())
                    self.assertEqual(result["preview_sha256"], hashlib.sha256(result["preview_png"]).hexdigest())
                    with Image.open(BytesIO(result["preview_png"])) as rendered:
                        self.assertEqual(rendered.format, "PNG")
                        self.assertEqual(rendered.size, expected_size)
                        self.assertEqual(rendered.getpixel((540, 600)), (22, 99, 157))
                    self.assertFalse(result["approved_for_publication"])
                    self.assertFalse(result["published"])
                    self.assertFalse(result["saved"])
                    self.assertTrue(result["requires_owner_review"])
                    self.assertIn("DRAFT", result["preview_filename"])

    def test_attestation_is_not_independent_approval(self):
        result = posters.render_flora_photo_preview(
            "shampoo", synthetic_photo(), "image/png", rights_attested=True, price_reviewed=True)
        self.assertTrue(result["caller_rights_attested"])
        self.assertTrue(result["caller_price_reviewed"])
        self.assertFalse(result["rights_independently_verified"])
        self.assertFalse(result["current_price_independently_verified"])
        self.assertFalse(result["approved_for_publication"])

    def test_rejects_unknown_product_placement_and_invalid_attestations(self):
        photo = synthetic_photo()
        for product, placement, rights in (("other", "feed", False),
                                           ("gold_kit", "../../story", False),
                                           ("shampoo", "feed", 1)):
            with self.subTest(product=product, placement=placement, rights=rights):
                with self.assertRaises(posters.FloraPosterError):
                    posters.render_flora_photo_preview(product, photo, "image/png", placement,
                                                       rights_attested=rights)

    def test_rejects_invalid_photo_and_catalogue_drift(self):
        with self.assertRaises(posters.FloraPosterError):
            posters.render_flora_photo_preview("gold_kit", b"not a photo", "image/png")
        with self.assertRaises(posters.FloraPosterError):
            posters.render_flora_photo_preview("gold_kit", synthetic_photo(), "image/jpeg")
        with patch.dict(CATALOG["shampoo"], {"price": "RS. 1"}):
            with self.assertRaises(posters.FloraPosterError):
                posters.render_flora_photo_preview("shampoo", synthetic_photo(), "image/png")


if __name__ == "__main__":
    unittest.main()
