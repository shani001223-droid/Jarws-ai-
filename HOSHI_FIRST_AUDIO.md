# First useful reply / audio latency

27 October 2026. This release changes the existing production frontend; it does not merge the unrelated foundation PR or claim a new streaming model endpoint.

- First online Urdu phrase is at most 70 characters, followed by phrases at most 150 characters, preserving the full reply.
- Only the first synthesis request starts initially. After its bytes are ready, one following clip is prefetched while playback starts. Later clips cannot occupy the backend's two synthesis slots ahead of the first clip.
- Cancellation invalidates future requests and aborts the active fetch. Each clip has its own 22-second network deadline; a long spoken reply no longer expires merely because total playback exceeds 22 seconds.
- Installed Urdu browser speech can use the existing fast-device option, in addition to the existing Android bridge. No Hindi/English substitution is introduced. Synthesis errors retain online Urdu fallback.
- Timing display reports separately measured AI and audio delay plus their sum; it does not display a fabricated instant response. Device/browser voice start records actual callback timing.

## Validation and limits

Five new Node regressions cover first-phrase length/full text, first-request priority, no duplicate synthesis, cancellation and failure fallback. Existing Python and Node suites were run locally. Browser regression runs remain necessary before release.

Before deployment, sequential external HTTP probes returned health in 6.396 s, 65-character Urdu audio in 11.387 s, 127-character Urdu audio in 9.458 s, and one short fast Urdu assistant response in 11.425 s. Both audio requests returned nonempty MPEG data. These are single samples with different network/cache/warmup conditions, not an A/B benchmark, p95, or proof that shortening clips alone reduces production latency. In this sample the shorter clip was slower. The model/host/network path still prevents claiming the desired fast-first-answer target is achieved.

No SSE/token streaming, always-on paid host, API/model change, credentials, phone installation or user audio measurement is included. The expected optimization is reduced synthesis contention and avoiding cloud audio when real device Urdu TTS exists. Realme Note 50 audible first-reply latency remains unverified.

Quick simple replies on configured GPT-OSS 20B/120B request reasoning_effort=low rather than the provider default medium; detailed tasks and other models keep their settings. Reference: https://console.groq.com/docs/api-reference . No model/key/hosting replacement. A second baseline fast request used OpenRouter fallback and took 31.409 s; fallback latency remains unresolved.
