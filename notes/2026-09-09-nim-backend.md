# 2026-09-09 — NIM backend fill-in for Milestone 3B (v0.7.0)

## Done

- **Implemented `NIMEmbedder` in `bible/semantic.py`.** Gemini's v0.6.0
  commit (`ef61976`) shipped the architecture — the docstring and ADR-010
  referenced a "nim" backend, the `get_embedder` factory was updated
  to mention it, and the `--backend` argparse choices listed it — but
  no actual class implemented the contract. This is the gap I filled.
- **The shape:**
  - Stdlib `urllib.request` POST to `https://integrate.api.nvidia.com/v1/embeddings`
    (configurable via `NIM_BASE_URL` env var for self-hosted NIM containers).
  - Bearer-token auth (`Authorization: Bearer ${NVIDIA_API_KEY}`).
  - OpenAI-compatible body: `{"input": [...], "model": "...", "encoding_format": "float", "input_type": "passage"|"query"}`.
  - Default model: `nvidia/nv-embedqa-e5-v5` (1024-dim, E5-Large-Unsupervised
    finetuned for QA retrieval — right shape for our use case vs. the
    larger `llama-3.2-nemotron-embed-1b`).
  - Six distinct error classes: `NIMAuthError`, `NIMRateLimitError`,
    `NIMServerError`, `NIMResponseError`, `NIMConnectionError`, base
    `NIMError`. Callers can `except NIMRateLimitError:` and retry-with-backoff
    without parsing strings.
  - `embed_query()` sets `input_type="query"` automatically; `embed_texts()`
    defaults to `"passage"`. **This is the single biggest E5 retrieval
    quality lever, and the easiest thing to get wrong silently.** Worth
    calling out specifically in the docstring + a test.
  - Out-of-order `index` sorting defends against buggy NIM responses
    (paranoid but cheap; NIM docs guarantee order but bugs happen).
  - `_http_post` is a monkey-patch hook so tests can inject a fake
    transport without monkey-patching `urllib` globally.
- **Wired into `get_embedder()` factory.** Resolution order for `auto`:
  1. local (if `sentence_transformers` importable)
  2. NIM (if `NVIDIA_API_KEY` in env)
  3. mock fallback
- **CLI integration:** `--backend nim` now accepted in
  `python -m bible semantic ...` and `scripts/index_embeddings.py`.
- **9 new sister-script tests.** Suite now at **62 passed, 0 failed**.
  Tests use the `_http_post` monkey-patch hook — CI never hits the real
  NIM API. Tests cover:
  - Missing `NVIDIA_API_KEY` → `NIMAuthError` with a clear message
  - Full roundtrip with mock transport (verifies request body shape)
  - `embed_query()` uses `input_type="query"` automatically
  - Out-of-order indexes are sorted correctly
  - HTTP 429 maps to `NIMRateLimitError`
  - HTTP 401 maps to `NIMAuthError`
  - Malformed JSON response maps to `NIMResponseError`
  - Default model + base URL sanity
  - Factory routing (`get_embedder("nim")` returns `NIMEmbedder`)
- **Docs refreshed:** CHANGELOG v0.7.0, HANDOFF §5 M3B marked ✅ (architecture
  complete), HANDOFF §8 item 1 (embeddings decision) reframed as
  "operational choice deferred, not architecture deferred", ADR-010
  implementation details added, pyproject.toml bumped to 0.7.0, README
  quickstart updated with `--backend nim` example and 62-test count.

## Blocked

- Nothing. The architecture is fully complete; the only "blocker" is
  the user's call on whether to actually spend on NIM to index the
  corpus (still pending per memory — not a code issue).

## Decisions made

- **Default model is `nv-embedqa-e5-v5`, not `llama-3.2-nemotron-embed-1b`.**
  Rationale: E5 QA-tuned is the right shape for retrieval-augmented
  queries against scripture text. Nemotron is a generalist LLM-based
  embedder that's larger and less specialized for our use case.
- **Single NIM endpoint, multi-config via env vars.** `NIM_BASE_URL` and
  `NIM_EMBED_MODEL` both overridable. Keeps the constructor simple
  while supporting self-hosted NIM containers (the typical pattern for
  on-prem deployments).
- **`_http_post` test hook, not full `urllib` mocking.** Tests stay
  simple; future contributors can swap transports without breaking
  existing tests.
- **Per-batch index sort.** NIM docs guarantee order; we sort anyway
  because contract violations in production APIs are real and the cost
  is negligible.

## Verification

```
$ python3 tests/run_all.py
  ... 62 ✓ ...
  62 passed, 0 failed (of 62)

$ python3 -c "from bible.semantic import NIMEmbedder; \
  os.environ['NVIDIA_API_KEY'] = 'x'; \
  e = NIMEmbedder(); \
  print(f'model={e.model}, base_url={e.base_url}')"
  model=nvidia/nv-embedqa-e5-v5, base_url=https://integrate.api.nvidia.com/v1

$ python3 -c "from bible.semantic import NIMEmbedder, NIMAuthError; \
  import os; os.environ.pop('NVIDIA_API_KEY', None); \
  NIMEmbedder()"
  NIMAuthError: NVIDIA_API_KEY is not set. Either export it in your shell...
```

## Commit shape

- `feat(semantic): NIMEmbedder — fill in the M3B backend Gemini stubbed`
- `test(semantic): 9 NIM backend tests (suite now 62 passing)`
- `docs: CHANGELOG v0.7.0 + HANDOFF M3B ✅ + ADR-010 implementation notes + README quickstart + daily note`
