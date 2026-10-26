"""Authenticated planned-job API tests; no workers or secrets in the client."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cloud_backend import main


class FakeRequest:
    def __init__(self, bearer=""):
        self.headers = {"authorization": bearer}


class PrivateJobApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.token = "test-only-job-token-" + "x" * 48
        self.db = str(Path(self.temp.name) / "private.sqlite")
        self.env = patch.dict(os.environ, {
            "HOSHI_JOB_API_TOKEN": self.token,
            "HOSHI_JOB_DB_PATH": self.db,
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.auth = FakeRequest("Bearer " + self.token)

    def test_fail_closed_without_explicit_backend_configuration(self):
        with patch.dict(os.environ, {"HOSHI_JOB_API_TOKEN": "", "HOSHI_JOB_DB_PATH": ""}):
            with self.assertRaises(main.HTTPException) as error:
                main.create_job_record(main.JobRecordRequest(kind="build_game"), self.auth)
            self.assertEqual(error.exception.status_code, 503)
        self.assertFalse(Path(self.db).exists())

    def test_private_create_and_lookup_do_not_execute(self):
        payload = main.JobRecordRequest(kind="render_anime", request_key="client-1")
        response = main.create_job_record(payload, self.auth)
        self.assertFalse(response["executed"])
        self.assertFalse(response["worker_available"])
        self.assertEqual(response["job"]["status"], "planned")
        self.assertEqual(main.create_job_record(payload, self.auth)["job"]["id"], response["job"]["id"])
        fetched = main.get_job_record(response["job"]["id"], self.auth)
        self.assertEqual(fetched["job"]["id"], response["job"]["id"])
        self.assertFalse(fetched["executed"])
        self.assertNotIn(self.token, str(response))
        self.assertNotIn("client-1", str(fetched))

    def test_auth_required_for_both_operations(self):
        for req in (FakeRequest(), FakeRequest("Bearer wrong"), FakeRequest("Basic " + self.token)):
            with self.assertRaises(main.HTTPException) as create_error:
                main.create_job_record(main.JobRecordRequest(kind="build_game"), req)
            self.assertEqual(create_error.exception.status_code, 401)
            with self.assertRaises(main.HTTPException) as read_error:
                main.get_job_record("hjob_" + "A" * 24, req)
            self.assertEqual(read_error.exception.status_code, 401)
        self.assertFalse(Path(self.db).exists())

    def test_invalid_kind_or_id_never_exposes_store(self):
        with self.assertRaises(main.HTTPException) as error:
            main.create_job_record(main.JobRecordRequest(kind="execute_shell"), self.auth)
        self.assertEqual(error.exception.status_code, 422)
        with self.assertRaises(main.HTTPException) as missing:
            main.get_job_record("../etc/passwd", self.auth)
        self.assertEqual(missing.exception.status_code, 404)

    def test_sqlite_open_error_is_sanitized(self):
        # SQLite cannot use an existing directory as a database file.
        with patch.dict(os.environ, {"HOSHI_JOB_DB_PATH": self.temp.name}):
            with self.assertRaises(main.HTTPException) as error:
                main.create_job_record(main.JobRecordRequest(kind="build_game"), self.auth)
        self.assertEqual(error.exception.status_code, 503)
        self.assertNotIn(self.temp.name, error.exception.detail)

    def test_unavailable_storage_is_not_reported_as_success(self):
        with patch.dict(os.environ, {"HOSHI_JOB_DB_PATH": str(Path(self.temp.name) / "missing" / "x.sqlite")}):
            with self.assertRaises(main.HTTPException) as error:
                main.create_job_record(main.JobRecordRequest(kind="build_game"), self.auth)
        self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
