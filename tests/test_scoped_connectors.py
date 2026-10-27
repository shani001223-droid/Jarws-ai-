"""Task 36: no-write GitHub connector, operator auth and fail-closed scope."""
import base64
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import Response

from cloud_backend import main
from cloud_backend.job_records import JobRecordStore
from cloud_backend.scoped_connectors import (
    InvalidConnectorPath, ScopedConnectorError,
    github_connector_ready, read_scoped_github_file,
)


class FakeRequest:
    def __init__(self, token=""):
        self.headers = {"authorization": token}


def github_item(path, data):
    return {
        "type": "file", "path": path, "encoding": "base64",
        "size": len(data),
        "content": base64.b64encode(data).decode("ascii"),
        "sha": hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest(),
    }


class ScopedConnectorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name) / "jobs.sqlite"
        JobRecordStore(self.db)
        self.operator = "operator-only-" + "X" * 36
        self.github = "github_pat_" + "a" * 60
        self.env = {
            "HOSHI_JOB_API_TOKEN": self.operator,
            "HOSHI_JOB_DB_PATH": str(self.db),
            "HOSHI_GITHUB_READ_TOKEN": self.github,
            "HOSHI_ARTIFACT_ROOT": "",
        }

    def test_exact_repo_branch_and_verified_utf8_content(self):
        path = "HOSHI_MASTER_PROJECT.md"
        body = b"# Hoshi project\n"
        with patch("cloud_backend.scoped_connectors._request_json",
                   return_value=github_item(path, body)) as request:
            result = read_scoped_github_file(path, self.github)
        self.assertEqual(result["content"], body.decode())
        self.assertEqual(result["sha256"], hashlib.sha256(body).hexdigest())
        self.assertTrue(result["read_only"])
        self.assertTrue(result["content_is_untrusted_data"])
        url, token = request.call_args.args
        self.assertEqual(token, self.github)
        self.assertIn("/repos/shani001223-droid/Jarws-ai-/contents/", url)
        self.assertIn("ref=hoshi%2Fdnd-foundation-20261026", url)
        self.assertNotIn(self.github, url)

    def test_paths_and_tokens_fail_before_network(self):
        bad = [
            "", "../README.md", "cloud_backend/.env", "cloud_backend/secrets.py/../x",
            "android/app/build.gradle", ".github/workflows/ci.yml",
            "https://evil.test/file", "HOSHI_MASTER_PROJECT.md?ref=main",
            "HOSHI_MASTER_PROJECT.md%2f..", "cloud_backend/__init__.py/secret",
        ]
        with patch("cloud_backend.scoped_connectors._request_json") as request:
            for path in bad:
                with self.subTest(path=path):
                    with self.assertRaises(InvalidConnectorPath):
                        read_scoped_github_file(path, self.github)
            for token in ("", "bad", "a\nBearer bad", " " * 40):
                with self.assertRaises(ScopedConnectorError):
                    read_scoped_github_file("README.md", token)
            request.assert_not_called()
        self.assertFalse(github_connector_ready(""))
        self.assertTrue(github_connector_ready(self.github))

    def test_forged_metadata_and_corruption_rejected(self):
        path = "README.md"
        valid = github_item(path, b"real bytes")
        mutations = [
            {"sha": "0" * 40},
            {"size": 999},
            {"path": "other.md"},
            {"type": "dir"},
            {"content": "%%%"},
            {"encoding": "utf-8"},
            {"content": base64.b64encode(b"\xff").decode("ascii"),
             "size": 1,
             "sha": hashlib.sha1(b"blob 1\0\xff").hexdigest()},
        ]
        for changes in mutations:
            with self.subTest(changes=changes):
                with patch("cloud_backend.scoped_connectors._request_json",
                           return_value={**valid, **changes}):
                    with self.assertRaises(ScopedConnectorError):
                        read_scoped_github_file(path, self.github)

    def test_large_file_and_upstream_failure_never_return_content(self):
        path = "README.md"
        with patch("cloud_backend.scoped_connectors._request_json",
                   return_value=github_item(path, b"x" * 32769)):
            with self.assertRaises(ScopedConnectorError):
                read_scoped_github_file(path, self.github)
        with patch("cloud_backend.scoped_connectors._request_json",
                   side_effect=ScopedConnectorError("github_read_unavailable")):
            with self.assertRaises(ScopedConnectorError) as exc:
                read_scoped_github_file(path, self.github)
            self.assertNotIn(self.github, str(exc.exception))

    def test_authenticated_api_only_get_and_no_browser_credentials(self):
        paths = {(route.path, method) for route in main.app.routes
                 for method in getattr(route, "methods", set())}
        endpoint = "/api/agent/connectors/github/file"
        self.assertIn((endpoint, "GET"), paths)
        self.assertNotIn((endpoint, "POST"), paths)
        with patch.dict(os.environ, self.env):
            for bad in (FakeRequest(), FakeRequest("Bearer wrong")):
                with patch.object(main, "read_scoped_github_file") as remote:
                    with self.assertRaises(main.HTTPException) as denied:
                        main.private_github_connector_file(
                            "README.md", bad, Response())
                    self.assertEqual(denied.exception.status_code, 401)
                    remote.assert_not_called()
            with patch.object(main, "read_scoped_github_file",
                              return_value={"read_only": True, "content": "hello"}) as remote:
                response = Response()
                result = main.private_github_connector_file(
                    "README.md", FakeRequest("Bearer " + self.operator), response)
                self.assertTrue(result["read_only"])
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(response.headers["x-content-type-options"], "nosniff")
                remote.assert_called_once_with("README.md", self.github)
            with self.assertRaises(main.HTTPException) as invalid:
                main.private_github_connector_file(
                    "../.env", FakeRequest("Bearer " + self.operator), Response())
            self.assertEqual(invalid.exception.status_code, 422)
            status = main.private_connector_status(
                FakeRequest("Bearer " + self.operator), Response())
            self.assertTrue(status["github"]["configured"])
            self.assertFalse(status["storage"]["configured"])
            self.assertFalse(status["writes_enabled"])
            self.assertNotIn(self.github, str(status))
            self.assertNotIn(self.operator, str(status))
        with patch.dict(os.environ, {"HOSHI_JOB_API_TOKEN": "",
                                     "HOSHI_JOB_DB_PATH": ""}):
            with self.assertRaises(main.HTTPException) as unavailable:
                main.private_connector_status(FakeRequest(), Response())
            self.assertEqual(unavailable.exception.status_code, 503)

    def test_missing_github_token_is_unavailable_even_if_operator_authorized(self):
        with patch.dict(os.environ, {**self.env, "HOSHI_GITHUB_READ_TOKEN": ""}):
            with self.assertRaises(main.HTTPException) as unavailable:
                main.private_github_connector_file(
                    "README.md", FakeRequest("Bearer " + self.operator), Response())
            self.assertEqual(unavailable.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
