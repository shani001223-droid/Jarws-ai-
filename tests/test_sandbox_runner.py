"""Task 33: fail-closed Docker isolation contracts and bounded I/O."""
import subprocess
import sys
import unittest
from unittest.mock import patch

from cloud_backend import sandbox_runner as sandbox
from cloud_backend import main


class SandboxRunnerTests(unittest.TestCase):
    def test_input_limits_and_no_shell(self):
        for source in ("", "  ", "print('a')\x00", "a" * (sandbox.MAX_SOURCE_BYTES + 1), 4):
            with self.subTest(source=repr(source)[:20]):
                with self.assertRaises(sandbox.SandboxSafetyError):
                    sandbox.run_python(source)
        for timeout in (0, 0.5, 5.1, float("nan"), True, "2"):
            with self.subTest(timeout=timeout):
                with self.assertRaises(sandbox.SandboxSafetyError):
                    sandbox.run_python("print(1)", timeout_seconds=timeout)
        command = sandbox._command("/usr/bin/docker", "hoshi-sandbox-safe")
        self.assertEqual(command[:2], ["/usr/bin/docker", "run"])
        for flag in ("--network=none", "--read-only", "--cap-drop=ALL",
                     "--security-opt=no-new-privileges", "--pull=never",
                     "--memory=128m", "--memory-swap=128m", "--cpus=0.5",
                     "--user=65534:65534", "--pids-limit=32"):
            self.assertIn(flag, command)
        self.assertNotIn("--privileged", command)
        self.assertNotIn("-v", command)
        self.assertNotIn("--mount", command)
        self.assertEqual(command[-4:], [sandbox.IMAGE, "-I", "-S", "-"])
        self.assertNotIn("sh", command)
        self.assertNotIn("bash", command)

    def test_missing_docker_fails_without_host_execution(self):
        with patch.object(sandbox.shutil, "which", return_value=None):
            with patch.object(sandbox.subprocess, "Popen") as popen:
                with self.assertRaisesRegex(sandbox.SandboxSafetyError, "Docker is required"):
                    sandbox.run_python("print('hello')")
                popen.assert_not_called()

    def test_seccomp_and_local_image_are_mandatory(self):
        good = subprocess.CompletedProcess([], 0,
                                           '["name=seccomp,profile=builtin","name=apparmor"]', "")
        bad = subprocess.CompletedProcess([], 0, '["name=apparmor"]', "")
        image_ok = subprocess.CompletedProcess([], 0, "", "")
        image_missing = subprocess.CompletedProcess([], 1, "", "")
        with patch.object(sandbox.shutil, "which", return_value="/usr/bin/docker"):
            with patch.object(sandbox.subprocess, "run", side_effect=[bad]):
                with self.assertRaisesRegex(sandbox.SandboxSafetyError, "seccomp"):
                    sandbox._preflight()
            with patch.object(sandbox.subprocess, "run", side_effect=[good, image_missing]):
                with self.assertRaisesRegex(sandbox.SandboxSafetyError, "trusted image"):
                    sandbox._preflight()
            with patch.object(sandbox.subprocess, "run", side_effect=[good, image_ok]) as run:
                self.assertEqual(sandbox._preflight(), "/usr/bin/docker")
                self.assertEqual(run.call_args_list[1].args[0][-2:], ["inspect", sandbox.IMAGE])

    def _local_child(self, script):
        # Fixed test fixture executed on host only to test the bounded pipe
        # collector; run_python never uses the host Python interpreter.
        return subprocess.Popen(
            [sys.executable, "-c", script],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0, start_new_session=True)

    def test_collector_reads_output_and_exit_code(self):
        proc = self._local_child("import sys; print(sys.stdin.read().upper())")
        try:
            code, out, err = sandbox._collect(proc, b"hello", 2.0)
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), b"HELLO")
            self.assertEqual(err, b"")
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def test_collector_limits_output_flood(self):
        proc = self._local_child("import sys; sys.stdout.write('x' * 200000); sys.stdout.flush()")
        try:
            with self.assertRaises(sandbox._OutputExceeded):
                sandbox._collect(proc, b"x", 2.0)
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def test_collector_wall_clock_timeout(self):
        proc = self._local_child("import time; time.sleep(4)")
        try:
            with self.assertRaises(sandbox._TimedOut):
                sandbox._collect(proc, b"x", 0.15)
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def test_no_public_sandbox_execution_route(self):
        routes = {route.path for route in main.app.routes}
        self.assertFalse(any("sandbox" in route or "execute-code" in route
                             for route in routes))


if __name__ == "__main__":
    unittest.main()
