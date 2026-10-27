# HOSHI Task 34 — scoped specialist orchestration

Development-only module: cloud_backend/specialist_orchestrator.py.

## Actual supported workflow

A trusted Python caller invokes orchestrate_flora_campaign(("gold_kit", "shampoo")).

This runs four **fixed, offline** specialist scopes, in order:

1. catalog_planner: reject unknown products, duplicate keys, unbounded batches and arbitrary tool names before execution.
2. creative_specialist: run the existing Task 27 planner/designer/coder/tester renderer for each approved Flora product.
3. artifact_auditor: independently re-check role receipts, SHA-256, exact bytes and the existing PNG/ZIP/catalogue verifier for each product.
4. campaign_packager: assemble and re-open one flora_campaign.zip containing each verified per-product ZIP and a JSON manifest with product keys, exact byte sizes and SHA-256 digests.

The result is a real, bounded, base64-encoded **in-memory ZIP** of existing offline PNG, caption and storyboard deliverables. It is **not** an MP4, original product photography, a remote multi-model agent team, or an autonomous overnight job. The combined package is not written to disk or published.

## Security and limits

- Only gold_kit and shampoo, at most two distinct keys, and only built-in trusted Python specialist functions.
- No arbitrary user prompts, model-generated Python, external URLs, shell, device actions, posting, purchases, secrets, trading or HTTP endpoints.
- Independent verification refuses a delegate's unverified success flag, forged role receipts, mismatched digest, invalid ZIP or wrong catalogue data.
- Inner ZIPs capped at 5 MB each; combined ZIP capped at 10.1 MB. No filesystem writes or stored raw prompts.
- Optional trusted stop_requested callback is checked **between** specialist stages; it cannot preempt a synchronous renderer already running. Canceled or failed results contain **no partial ZIP**.
- Optional delegate injection is for trusted Python tests only. Never expose this callable or arbitrary tools to a browser or user/model payload.
- No queue handler registration, worker start, persistent volume, artifact-store integration or status mutation. Persisted, published and queued_job_completed remain false.
- This is bounded deterministic orchestration, **not** a general-purpose autonomous multi-agent platform. General task execution requires separately audited scopes, permission gates, worker isolation, persistence and live verification.

## Verification

tests/test_specialist_orchestrator.py covers real two-product output, manifest/hash/inner ZIP integrity, scope and duplicate rejection, fake evidence and tampering, stop/cancel behavior, secret-safe errors and absence of queued-job side effects. Full CI, Docker backend import/health and phone acceptance must be recorded **after** passing runs, not assumed.

Task 06 (production release/rollback/Realme QA) and Task 11 (real OpenJarvis service) remain blocked by external configuration and explicit release authorization. No merge/deployment or paid action is part of this task.
