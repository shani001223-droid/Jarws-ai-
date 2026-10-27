# Hoshi Task 33 — Docker-only Python execution sandbox (development)

This adds `cloud_backend/sandbox_runner.py` to the **same** Hoshi project. It is a trusted-operator Python API, not a public code runner or a general agent that can run generated commands.

## Scope

`run_python(source, timeout_seconds=3)` accepts at most 8 KiB UTF-8 Python source and executes it only in an already installed local `python:3.12-alpine` Docker image. There is **no fallback to host Python**, shell, network, API, app/phone action, arbitrary image, external image pull, host mount, Docker socket mount, user-selected command, or HTTP endpoint. Source goes to the container over standard input and is never passed as a shell argument or logged. Output is bounded to 16 KiB combined; wall-clock to 1–5 seconds. Exit status, timeout and output-limit failures are distinguished without claiming success. A unique container name is used; timeout/output-limit cleanup requests daemon-side forced removal.

Container policy: no network, read-only root, dropped capabilities, no-new-privileges, default Docker seccomp required at preflight, unprivileged UID/GID 65534, no host mounts, no image pulls, private PID namespace, 32-process cap, 128 MiB memory/swap cap, 0.5 CPU cap, 64 file descriptor limit and 8 MiB noexec scratch tmpfs. Python runs in isolated mode (`-I -S`). This does not confer authority to edit repository files, publish ads, trade, send messages or touch Android apps.

## Operator-only example

```python
from cloud_backend.sandbox_runner import run_python, SandboxSafetyError

try:
    result = run_python("print(7 * 6)")
    assert result["ok"] and result["stdout"].strip() == "42"
except SandboxSafetyError:
    # Docker/image/seccomp unavailable: do not execute source on the host.
    pass
```

The operator must install and trust the exact local Docker image in advance. CI uses `docker pull python:3.12-alpine` **only in the isolated GitHub test runner**; the application never pulls an image. `HOSHI isolated sandbox smoke` runs actual container tests for arithmetic, network denial, root-filesystem write denial, output floods and timeout, in addition to no-Docker unit tests. The standard Python/Node/Playwright suite and backend Docker build/health remain separate checks.

## Hard limitations and pending acceptance

- This is **not a production multi-tenant hostile-code sandbox**. Docker container boundaries and the host Docker daemon have vulnerabilities and operational requirements; a dedicated rootless, restricted remote worker, image digest pinning, stronger policy, audit, quotas, operator authentication and separate infrastructure review are needed before public or arbitrary model-generated code execution.
- Ordinary Render Docker web services do **not** automatically provide a nested Docker daemon. Without a separately approved, secured worker, `run_python` fails closed; it is not an always-on remote code executor.
- `cloud_backend/document_tools.py` remains a trusted in-process PDF/image parser. This task does not automatically sandbox hostile documents; there is no untrusted file upload endpoint.
- There is no registered queue worker, auto-generated game, production deployment, Android device QA, remote OpenJarvis activation or user-facing UI. No purchases, account actions or real trading.
- Never mark Task 33 verified until full CI, Docker backend smoke and real isolated-sandbox workflow have passed for the relevant implementation commit. The **only** task completion scoreboard is `HOSHI_60_TASK_MASTER_ROADMAP.md`.
