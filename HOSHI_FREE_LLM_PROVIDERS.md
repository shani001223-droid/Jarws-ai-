# Hoshi optional AI providers from nejib1/Free-LLM

**Source directory:** https://github.com/nejib1/Free-LLM (MIT; listing only; it does not provide API credentials)

## What is integrated

The existing Hoshi model priority is preserved: real configured OpenJarvis for eligible complex tasks; quick Groq for short voice requests; then OpenRouter (free models), Gemini, and Groq as applicable. If those fail or are unconfigured, Hoshi tries the following **explicitly configured** extra providers, in fixed order:

| Hoshi mode | Secret environment variable | Free-only safeguard | Fixed model | Endpoint |
| --- | --- | --- | --- | --- |
| `zai` | `ZAI_API_KEY` | Free Flash model hard-coded | `glm-4.5-flash` | `https://api.z.ai/api/paas/v4/chat/completions` |
| `mistral` | `MISTRAL_API_KEY` | Also requires `MISTRAL_FREE_MODE=true` after confirming a **free-mode account** | `mistral-small-latest` | `https://api.mistral.ai/v1/chat/completions` |
| `nvidia` | `NVIDIA_API_KEY` | Also requires `NVIDIA_PROTOTYPE_MODE=true` for free permitted developer/prototyping access | `meta/llama-3.1-8b-instruct` | `https://integrate.api.nvidia.com/v1/chat/completions` |

**No credentials are copied from the directory, committed, created or inserted into the APK.** Only configure the above variables in the backend host's secret environment (Render Environment), never in GitHub files, code or public URLs. Hoshi's public `/health` may list names of configured extra providers but must never return keys or claim they are online without a real call.

**Provider notes:** Z.AI Flash free-tier eligibility can change. Mistral Free mode has limited usage and potential data-training/privacy terms; enable only when you accept those terms and are using a no-billing free workspace. NVIDIA developer API access is intended for prototyping, not production/commercial operations; leave disabled otherwise. Provider quotas or policies may change independently of this project.

## User setup

1. Generate an official key for a provider: https://z.ai/ ; https://console.mistral.ai/ ; https://build.nvidia.com/explore/discover
2. Set the matching environment variable (and the opt-in safeguard for Mistral or NVIDIA) in your Hoshi backend host. Never paste actual secrets into this repository.
3. Deploy a verified branch version only after CI and app tests pass; check `/health` for configured provider names, then perform a genuine no-cost test request.
4. If quota is exhausted, key rejected or a model is unavailable, the adapter fails safely; it does not buy credits or upgrade to a paid model.

All remote providers see the prompts Hoshi sends them during fallback. Do not send passwords or highly sensitive/private files. The adapter uses fixed HTTPS URLs, no redirects, bounded response sizes and timeouts, sanitized errors, and hard-coded model IDs to prevent unreviewed paid-model selection.

## Verified vs not verified

- Backend code and no-network mocked tests can verify request structure, fallback, routing, free-mode gates, fixed model IDs and absence of secrets in error messages.
- Only actual user-created provider keys can confirm *live* access. No live keys have been supplied or checked by this change.
- This integration improves possible fallback redundancy. It does not create new autonomous tools, game rendering, device control, or permanent unlimited quotas.
