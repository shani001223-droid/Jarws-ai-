"""Task 33: opt-in, Docker-only execution of small Python snippets.

Trusted Python operator API. There is deliberately no HTTP route, agent tool,
worker registration, host interpreter fallback, Docker socket mount, network,
host bind mount or image pull. Do not expose this to arbitrary public users:
container isolation is defense in depth, not a multi-tenant security guarantee.
"""
from __future__ import annotations

import json
import math
import os
import secrets
import selectors
import shutil
import subprocess
import time

IMAGE = "python:3.12-alpine"
MAX_SOURCE_BYTES = 8192
MAX_OUTPUT_BYTES = 16384
MAX_WALL_SECONDS = 5.0


class SandboxSafetyError(ValueError):
    """Sanitized rejection; never includes source or Docker stderr."""


class _TimedOut(Exception):
    pass


class _OutputExceeded(Exception):
    pass


def _validate(source: str, timeout_seconds: float) -> bytes:
    if not isinstance(source, str) or not source.strip() or "\x00" in source:
        raise SandboxSafetyError("Invalid Python source.")
    data = source.encode("utf-8")
    if len(data) > MAX_SOURCE_BYTES:
        raise SandboxSafetyError("Python source exceeds sandbox limit.")
    if (isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or not 1 <= timeout_seconds <= MAX_WALL_SECONDS):
        raise SandboxSafetyError("Invalid sandbox time limit.")
    return data


def _preflight() -> str:
    docker = shutil.which("docker")
    if not docker:
        raise SandboxSafetyError("Sandbox unavailable: Docker is required.")
    try:
        security = subprocess.run(
            [docker, "info", "--format", "{{json .SecurityOptions}}"],
            capture_output=True, text=True, timeout=4, check=False)
        if security.returncode or not any("seccomp" in str(option)\n                                          for option in json.loads(security.stdout)):
            # Docker security options contain e.g. name=seccomp,profile=builtin.
            # Explicitly refuse daemons without the default seccomp boundary.
            raise SandboxSafetyError("Sandbox unavailable: seccomp required.")
        image = subprocess.run(
            [docker, "image", "inspect", IMAGE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=4, check=False)
        if image.returncode:
            raise SandboxSafetyError("Sandbox unavailable: trusted image not installed.")
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
        raise SandboxSafetyError("Sandbox unavailable: Docker preflight failed.") from None
    return docker


def _command(docker: str, name: str) -> list[str]:
    return [
        docker, "run", "--rm", "--pull=never", "--name", name, "-i",
        "--network=none", "--read-only", "--cap-drop=ALL",
        "--security-opt=no-new-privileges", "--pids-limit=32",
        "--memory=128m", "--memory-swap=128m", "--cpus=0.5",
        "--ulimit=nofile=64:64", "--user=65534:65534",
        "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=8m",
        "--workdir=/tmp", "--env=HOME=/tmp",
        "--env=PYTHONDONTWRITEBYTECODE=1", "--env=PYTHONNOUSERSITE=1",
        "--entrypoint=python", IMAGE, "-I", "-S", "-",
    ]


def _collect(proc: subprocess.Popen, payload: bytes, timeout: float) -> tuple[int, bytes, bytes]:
    """Nonblocking bounded pipes: a noisy child cannot fill host memory."""
    out, err = bytearray(), bytearray()
    deadline = time.monotonic() + timeout
    selector = selectors.DefaultSelector()
    streams = (proc.stdin, proc.stdout, proc.stderr)
    try:
        for stream in streams:
            os.set_blocking(stream.fileno(), False)
        selector.register(proc.stdin, selectors.EVENT_WRITE, "stdin")
        selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
        selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
        offset = 0
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise _TimedOut()
            for key, _ in selector.select(timeout=min(remaining, 0.1)):
                stream, kind = key.fileobj, key.data
                if kind == "stdin":
                    try:
                        count = os.write(stream.fileno(), payload[offset:offset + 4096])
                    except BrokenPipeError:
                        count = len(payload) - offset
                    offset += count
                    if offset >= len(payload):
                        selector.unregister(stream)
                        stream.close()
                    continue
                chunk = os.read(stream.fileno(), 4096)
                if not chunk:
                    selector.unregister(stream)
                    stream.close()
                    continue
                if len(out) + len(err) + len(chunk) > MAX_OUTPUT_BYTES:
                    raise _OutputExceeded()
                (out if kind == "stdout" else err).extend(chunk)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _TimedOut()
        try:
            return proc.wait(timeout=remaining), bytes(out), bytes(err)
        except subprocess.TimeoutExpired:
            raise _TimedOut() from None
    finally:
        selector.close()
        for stream in streams:
            if stream is not None and not stream.closed:
                stream.close()


def _cleanup(docker: str, name: str, proc: subprocess.Popen) -> None:
    # Explicit daemon-side cleanup matters: killing the Docker CLI alone may
    # leave the detached container running after a timeout/output flood.
    try:
        subprocess.run([docker, "rm", "-f", name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        pass
    if proc.poll() is None:
        proc.kill()
    try:
        proc.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        pass


def run_python(source: str, *, timeout_seconds: float = 3.0) -> dict:
    """Run UTF-8 Python via a locally installed Docker image, never on host.

    Returns bounded text and a verified exit status. Nonzero, timeout, output
    flood or unavailable Docker are never represented as success.
    """
    payload = _validate(source, timeout_seconds)
    docker = _preflight()
    name = "hoshi-sandbox-" + secrets.token_hex(10)
    try:
        proc = subprocess.Popen(
            _command(docker, name), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
            close_fds=True, start_new_session=True)
    except OSError:
        raise SandboxSafetyError("Sandbox unavailable: container did not start.") from None
    try:
        code, out, err = _collect(proc, payload, float(timeout_seconds))
        return {
            "ok": code == 0, "status": "completed" if code == 0 else "failed",
            "exit_code": code, "stdout": out.decode("utf-8", "replace"),
            "stderr": err.decode("utf-8", "replace"),
        }
    except (_TimedOut, _OutputExceeded) as exc:
        return {"ok": False, "status": "timed_out" if isinstance(exc, _TimedOut)
                else "output_limit", "exit_code": None, "stdout": "", "stderr": ""}
    except OSError:
        raise SandboxSafetyError("Sandbox failed closed.") from None
    finally:
        _cleanup(docker, name, proc)
