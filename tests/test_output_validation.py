"""Task 35: real generated format checks and malicious metadata regressions."""
import ast
import base64
import hashlib
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from zipfile import ZIP_STORED, ZipFile

from cloud_backend.output_validation import (
    OutputFormatError, validate_campaign_zip, validate_json_document,
    validate_png_media, validate_python_source,
)
from cloud_backend.specialist_orchestrator import orchestrate_flora_campaign


def rewrite_zip(original, changes, *, duplicate=None):
    target = BytesIO()
    with ZipFile(BytesIO(original)) as src, ZipFile(target, "w", ZIP_STORED) as dst:
        for item in src.infolist():
            data = changes.get(item.filename, src.read(item.filename))
            dst.writestr(item.filename, data)
        if duplicate:
            dst.writestr(duplicate, b"forged")
    return target.getvalue()


class OutputValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = orchestrate_flora_campaign(["shampoo"])
        assert result["ok"], result.get("error_code")
        cls.payload = base64.b64decode(result["artifact"]["zip_base64"], validate=True)

    def test_python_syntax_only_never_executes(self):
        source = b"raise RuntimeError('MUST_NOT_RUN')\n"
        result = validate_python_source(source)
        self.assertEqual(result["sha256"], hashlib.sha256(source).hexdigest())
        self.assertTrue(result["syntax_only"])
        self.assertFalse(result["executed"])
        for invalid in (b"def broken(:\n", b"\x00", b"\xff", b"x" * 64001, "", b""):
            with self.subTest(invalid=repr(invalid)[:50]):
                with self.assertRaises(OutputFormatError):
                    validate_python_source(invalid)

    def test_json_duplicate_keys_and_non_finite_rejected(self):
        self.assertTrue(validate_json_document(b'{"a":[1,true,null]}')["parsed"])
        for invalid in (b'{"a":1,"a":2}', b'{"x":NaN}', b'null',
                        b'{"broken":', b"\xff", b" " * 64001):
            with self.subTest(invalid=repr(invalid)[:50]):
                with self.assertRaises(OutputFormatError):
                    validate_json_document(invalid)

    def test_actual_campaign_and_png_dimensions(self):
        result = validate_campaign_zip(self.payload)
        self.assertEqual(result["products"], ["shampoo"])
        self.assertFalse(result["rendered_video"])
        self.assertEqual(result["sha256"], hashlib.sha256(self.payload).hexdigest())
        with ZipFile(BytesIO(self.payload)) as outer:
            inner_data = outer.read("shampoo.zip")
        with ZipFile(BytesIO(inner_data)) as inner:
            png = inner.read("shampoo_feed_1080x1350.png")
        image = validate_png_media(png, expected_size=(1080, 1350))
        self.assertEqual(image["width"], 1080)
        for invalid in (png[:40], b"not a png", b"", b"x" * 3_000_001):
            with self.subTest(length=len(invalid)):
                with self.assertRaises(OutputFormatError):
                    validate_png_media(invalid, expected_size=(1080, 1350))
        with self.assertRaises(OutputFormatError):
            validate_png_media(png, expected_size=(500, 500))

    def test_specialist_does_not_return_success_when_format_gate_fails(self):
        with patch("cloud_backend.specialist_orchestrator.validate_campaign_zip",
                   side_effect=OutputFormatError("invalid_png_media")):
            result = orchestrate_flora_campaign(["shampoo"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["failed_specialist"], "campaign_packager")
        self.assertEqual(result["error_code"], "campaign_verification_failed")
        self.assertIsNone(result["artifact"])
        self.assertFalse(result["queued_job_completed"])
        self.assertFalse(result["published"])

    def test_outer_manifest_digest_and_archive_tampering(self):
        with ZipFile(BytesIO(self.payload)) as outer:
            original_manifest = json.loads(outer.read("manifest.json"))
            inner_data = outer.read("shampoo.zip")
        bad_digest = json.loads(json.dumps(original_manifest))
        bad_digest["products"][0]["sha256"] = "0" * 64
        bad_mp4 = json.loads(json.dumps(original_manifest))
        bad_mp4["rendered_video"] = True
        bad_filename = json.loads(json.dumps(original_manifest))
        bad_filename["products"][0]["filename"] = "../shampoo.zip"
        for altered in (bad_digest, bad_mp4, bad_filename):
            payload = rewrite_zip(self.payload, {
                "manifest.json": json.dumps(altered).encode()
            })
            with self.subTest(altered=altered):
                with self.assertRaises(OutputFormatError):
                    validate_campaign_zip(payload)
        with self.assertRaises(OutputFormatError):
            validate_campaign_zip(rewrite_zip(self.payload, {}, duplicate="manifest.json"))
        with self.assertRaises(OutputFormatError):
            validate_campaign_zip(rewrite_zip(self.payload, {"shampoo.zip": b"fake zip"}))
        with self.assertRaises(OutputFormatError):
            validate_campaign_zip(b"not zip")

    def test_nested_corruption_even_with_recomputed_outer_digest(self):
        with ZipFile(BytesIO(self.payload)) as outer:
            manifest = json.loads(outer.read("manifest.json"))
            inner = outer.read("shampoo.zip")
        broken_inner = rewrite_zip(inner, {"shampoo_feed_1080x1350.png": b"fake"})
        manifest["products"][0]["sha256"] = hashlib.sha256(broken_inner).hexdigest()
        manifest["products"][0]["bytes"] = len(broken_inner)
        forged = rewrite_zip(self.payload, {
            "manifest.json": json.dumps(manifest).encode(),
            "shampoo.zip": broken_inner,
        })
        with self.assertRaises(OutputFormatError):
            validate_campaign_zip(forged)


if __name__ == "__main__":
    unittest.main()
