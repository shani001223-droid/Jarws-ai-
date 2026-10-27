"""Task 32: real offline document read/edit operations, with fail-closed limits."""
from hashlib import sha256
from io import BytesIO
import json
import unittest

from PIL import Image, PngImagePlugin
from pypdf import PdfReader, PdfWriter

from cloud_backend import document_tools as doc
from cloud_backend import main


def sample_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=400, height=600)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def sample_png():
    im = Image.new("RGB", (1000, 600), "blue")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("private-note", "DO-NOT-RETAIN")
    buffer = BytesIO()
    im.save(buffer, format="PNG", pnginfo=meta)
    return buffer.getvalue()


class DocumentToolsTests(unittest.TestCase):
    def test_pdf_inspect_and_rotate_only_selected_page(self):
        source = sample_pdf()
        inspected = doc.inspect_document("report.pdf", source)
        self.assertEqual(inspected["kind"], "pdf")
        self.assertEqual(inspected["pages"], 2)
        self.assertEqual(inspected["sha256"], sha256(source).hexdigest())
        self.assertEqual(inspected["preview"], "")
        edited = doc.rotate_pdf("report.pdf", source, 90, [2])
        self.assertEqual(edited["rotated_pages"], [2])
        self.assertEqual(edited["mime_type"], "application/pdf")
        reader = PdfReader(BytesIO(edited["data"]))
        self.assertEqual(len(reader.pages), 2)
        self.assertEqual(reader.pages[0].get("/Rotate", 0), 0)
        self.assertEqual(reader.pages[1].get("/Rotate", 0), 90)
        self.assertEqual(PdfReader(BytesIO(source)).pages[1].get("/Rotate", 0), 0)

    def test_pdf_rejects_invalid_header_page_limit_and_selection(self):
        pdf = sample_pdf()
        for bad in (b"not pdf", b"%PDF- fake"):
            with self.subTest(bad=bad):
                with self.assertRaises(doc.DocumentSafetyError):
                    doc.inspect_document("a.pdf", bad)
        for degrees, pages in ((0, [1]), (True, [1]), (90, []),
                               (90, [0]), (90, [3]), (90, [1, 1]),
                               (90, [True]), (90, "1")):
            with self.subTest(degrees=degrees, pages=pages):
                with self.assertRaises(doc.DocumentSafetyError):
                    doc.rotate_pdf("a.pdf", pdf, degrees, pages)
        writer = PdfWriter()
        for _ in range(doc.MAX_PAGES + 1):
            writer.add_blank_page(width=200, height=200)
        output = BytesIO()
        writer.write(output)
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("too-many.pdf", output.getvalue())

    def test_image_inspect_resize_preserves_aspect_strips_metadata(self):
        original = sample_png()
        inspected = doc.inspect_document("Flora.png", original)
        self.assertEqual((inspected["width"], inspected["height"]), (1000, 600))
        edited = doc.resize_image("Flora.png", original, 500)
        self.assertEqual((edited["width"], edited["height"]), (500, 300))
        self.assertEqual(edited["mime_type"], "image/png")
        self.assertTrue(edited["metadata_stripped"])
        with Image.open(BytesIO(edited["data"])) as image:
            self.assertEqual(image.size, (500, 300))
            self.assertNotIn("private-note", image.info)
        self.assertIn(b"DO-NOT-RETAIN", original)
        self.assertNotIn(b"DO-NOT-RETAIN", edited["data"])

    def test_image_rejects_fake_extension_oversize_and_invalid_size(self):
        original = sample_png()
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("wrong.jpg", original)
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("image.png", b"broken image")
        for size in (0, 127, 2049, True, 1.5):
            with self.subTest(size=size):
                with self.assertRaises(doc.DocumentSafetyError):
                    doc.resize_image("image.png", original, size)
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("image.png", b"x" * (doc.MAX_INPUT + 1))
        image = Image.new("RGB", (3000, 3000), "red")
        output = BytesIO()
        image.save(output, format="PNG")
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("huge.png", output.getvalue())

    def test_project_text_inspect_and_exact_edit_with_digest(self):
        original = b'{"brand":"Flora","price":3500}'
        inspected = doc.inspect_document("catalog.json", original)
        self.assertEqual(inspected["kind"], "project_text")
        edited = doc.replace_project_text(
            "catalog.json", original, "3500", "3600", inspected["sha256"])
        self.assertEqual(json.loads(edited["data"])["price"], 3600)
        self.assertEqual(edited["sha256"], sha256(edited["data"]).hexdigest())
        self.assertEqual(original, b'{"brand":"Flora","price":3500}')
        self.assertEqual(doc.inspect_document("notes.md", b"Roman Urdu")["preview"],
                         "Roman Urdu")

    def test_project_edit_fails_closed_on_stale_ambiguous_or_invalid_json(self):
        original = b'{"a":1,"b":1}'
        digest = sha256(original).hexdigest()
        for old, new, expected in (
            ("1", "2", digest),  # ambiguous
            ("missing", "2", digest),
            ("a", "b", "0" * 64),  # stale
            ("1", "NaN", digest),  # JSON parser rejects NaN
            ("1", "", digest),  # makes invalid JSON
        ):
            with self.subTest(old=old, new=new, expected=expected):
                with self.assertRaises(doc.DocumentSafetyError):
                    doc.replace_project_text("catalog.json", original, old, new,
                                             expected)
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("broken.json", b'{"a":NaN}')
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("invalid.txt", b"abc\x00def")
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("invalid.txt", b"\xff")

    def test_no_paths_executables_or_arbitrary_filesystem_access(self):
        for name in ("../secret.md", "folder\\secret.txt", "/tmp/a.pdf",
                     "private.env", "script.py", "archive.zip", "..json",
                     "foo..md", "bad name .txt/"):
            with self.subTest(name=name):
                with self.assertRaises(doc.DocumentSafetyError):
                    doc.inspect_document(name, b"safe")
        with self.assertRaises(doc.DocumentSafetyError):
            doc.inspect_document("safe.txt", "not bytes")
        with self.assertRaises(doc.DocumentSafetyError):
            doc.replace_project_text("safe.pdf", sample_pdf(), "a", "b", "0" * 64)

    def test_no_public_document_upload_or_mutation_endpoint(self):
        routes = {(route.path, method) for route in main.app.routes
                  for method in getattr(route, "methods", set())}
        self.assertFalse(any("/documents" in path for path, _ in routes))
        self.assertFalse(any("/files/upload" in path for path, _ in routes))


if __name__ == "__main__":
    unittest.main()
