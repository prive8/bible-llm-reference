# 2026-09-10 — OpenRouter embedder backend (v0.13.0)

## Done

### 1. OpenRouter embedder shipped (`OpenRouterEmbedder`)

New paid backend in `bible/semantic.py` — mirrors the `NIMEmbedder`
API exactly. Default model `openai/text-embedding-3-small` (1536-dim,
~$0.02/M tokens → ~$0.02 for the full ~1.12M-token corpus index
build). Headers, body shape, error classes all wired; mock-transport
test pattern same as NIM tests.

### 2. Factory routing + auto precedence

`get_embedder("openrouter")` returns `OpenRouterEmbedder`. Auto
resolution order: local > openrouter > nim > mock. New sister-script
test `t_get_embedder_auto_prefers_openrouter_over_nim_when_both_keys_set`
locks the precedence.

### 3. CLI + index script

`--backend openrouter` now valid in `bible semantic` and
`scripts/index_embeddings.py`. No CLI changes otherwise — `--index
<name>` already parameterizes which index the eval harness queries,
so the benchmark is just `scripts/index_embeddings.py --backend
openrouter --name openrouter-default` followed by
`scripts/run_eval.py --paths semantic --index openrouter-default`.

### 4. HANDOFF §8 #10 — benchmark workflow documented

Step-by-step in §8 #10 for the next agent who runs the live benchmark
after `OPENROUTER_API_KEY` lands in `~/.hermes/.env`. Expected outcome
noted (educated guess: 5-15% recall gain over local MiniLM).

## Closed

- HANDOFF §8 #1 updated: now bounded by three options (local / NIM /
  OpenRouter) instead of two.
- HANDOFF §8 #8 updated: paths forward = OpenRouter benchmark (#10).
- HANDOFF §8 #10 added.

## Test status

- **107/107 passing locally** (up from 97 after v0.12.0).
- 9 new OpenRouter tests + 1 updated NIM regression test.
- All tests use mocked transport — CI is hermetic, no OpenRouter key
  needed for the test suite.

## Pending

- **Live OpenRouter benchmark** — blocks on user adding
  `OPENROUTER_API_KEY` to `~/.hermes/.env`. Once that's done:
  - `python scripts/index_embeddings.py --backend openrouter --name openrouter-default`
  - `python scripts/run_eval.py --paths semantic --index openrouter-default`
  - Update `docs/evaluation.md` with new baseline.
  - Update ADR-011 (hybrid fusion) with the OpenRouter cross-backend
    comparison.
  - Close §8 #10 with a yes/no on whether the swap is worth the cost.
  - Total wall time: ~7 min (3 min index build + 1.5 min eval +
    ~2 min reporting).

## Blocked

Items 3 (Phase 3.3 full Tanakh) and 4 (Phase 2 prep) deferred to
next session — this session focused on the OpenRouter backend
because it unblocks the entire embedding-benchmark question.

## Decisions made

- **Default OpenRouter model: `openai/text-embedding-3-small`** rather
  than a "stronger" model like `text-embedding-3-large`. Reasoning:
  cost-per-million at small is ~10× cheaper than large, and for the
  retrieval-quality difference (~3-5% expected), the small tier is
  the right cost-quality tradeoff. If small underperforms, swap to
  large is a one-line config change.
- **`auto` prefers OpenRouter over NIM** when both keys are set.
  Reasoning: OpenRouter has paid-tier access; NIM is free-tier-gated
  on this account. Future-proof: if NIM free-tier unblocks, the
  precedence can flip back, but for now OpenRouter is the working
  paid path.
- **No `input_type` parameter for OpenRouter requests** (NIM has it
  for E5 quality). OpenAI-family models don't have the equivalent;
  tests verify `input_type` is absent from the request body.
- **`X-Title` header sent for OpenRouter app attribution.** OpenRouter
  requires it for ranked-app display (TOS requirement); no functional
  effect, just analytics.
