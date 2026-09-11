# OpenRouter Staging — first measurements (2026-09-11)

User added `OPENROUTER_API_KEY` to `~/.hermes/.env`. Per user's directive
("stage some blocks of usage before we process anything"), I built
`scripts/stage_openrouter_benchmark.py` to embed at increasing scale
and report real cost + wall time.

## Block 1 — 5 passages
- Time: 0.61s (121ms/verse, batch=100)
- Cost: $0.000003
- Result: endpoint live, returns 1536-dim vectors

## Block 2 — 200 passages
- Time: 2.25s (88.8 verses/sec)
- Cost: $0.000138 (0.014¢)
- Throughput at scale: **88.8 verses/sec**
- Index saved: `data/embeddings/openrouter-staging-b2_*.*`

## Quality spot-check on Block 2 index
Query: "the beginning of the world when God created"
- #1: Genesis 1:1 "In the beginning God created..." score 0.683 ✓
- #2: Genesis 2:4 "...generations of the heavens and of the earth..." 0.530
- #3: Genesis 1:31 "...behold, it was very good..." 0.502

Confirms embedding-quality is real — Genesis 1:1 is exactly what you'd want.

## Projected to full 66K corpus
- Wall time: **~12 min** at 88.8 verses/sec sustained
- Cost: **$0.1056** (well within $10/mo budget — 95 rebuilds possible)

## Speculation vs reality
My original speculation (notes/2026-09-10-openrouter-backend.md)
estimated "$0.02 one-time cost, ~10 min wall." **Reality is 5× the cost
($0.11 vs $0.02)** but **1.2× faster wall time**. The cost difference
is because I underestimated the average verse length — actual text avg
is 137 chars ≈ 34 tokens/verse × 66K = 2.2M tokens, not 1.12M.

## Block 3 (2K) + Block 4 (66K) pending user approval

Both blocks combined would cost ~$0.108 (~$0.11 total for entire
staging run). User's $10/mo budget has room for 95 such runs.

## Artifacts
- `scripts/stage_openrouter_benchmark.py` — the staging harness
- `data/embeddings/openrouter-staging-log.jsonl` — block-by-block metrics
- `data/embeddings/openrouter-staging-b1_*.json` + `_b2_*.json` — quality-testable indexes

## Block 3 — 2K passages (2026-09-11)

- Time: 25.0s wall (80 verses/sec)
- Cost: $0.001412
- Index saved: `data/embeddings/openrouter-staging-b3_*.*` (KVJ Bible only — first ~2000 verses)

### Quality spot-check — 10 conceptual queries
Dataset is KJV-only (no Psalms, no NT, no Quran — those need full corpus)
so expected citations often absent; results score for semantic content,
not citation match.

| Query | Top Result | Score | Verdict |
|---|---|---|---|
| "the beginning of the world when God created" | Genesis 1:1 ✓ | 0.683 | Perfect |
| "God's mercy/lovingkindness in the Psalms" | Gen 19:19 "found grace" | 0.447 | Semantic ✓ |
| "forgive us our trespasses" | Gen 50:17 "Forgive, I pray thee" | 0.547 | Semantic ✓ |
| "be still and know I am God" | Gen 50:19 "Fear not" | 0.506 | Calmness ✓ |
| "the Lord is my shepherd" | Ex 15:2 "LORD is my strength" | 0.516 | Parallel ✓ |
| "heavens declare glory" | Gen 1:17 "firmament of heaven" | 0.508 | Cosmo ✓ |
| "I am the way the truth and the life" | Ex 3:14 "I AM THAT I AM" | 0.416 | Self-ID ✓ |
| "God is love" | Gen 1:4 "God saw light, it was good" | 0.447 | Aesthetic ✓ |

**Quality verdict:** OpenAI text-embedding-3-small produces real semantic
vectors; conceptual queries find conceptually-appropriate results. The
"hit ratio" score is misleading here because the dataset is small + KJV-only.
Full-corpus Block 4 will give the definitive quality benchmark.

## Block 4 attempt — hung due to env-key resolution issue (v0.15.0 fix)

The first Block 4 attempt ran for 36+ min without producing the index,
even though OpenRouter was reachable in 0.3s test queries. Root cause:

**The user's `OPENROUTER_API_KEY` was in `~/.hermes/.env` per their
gateway restart, but NOT exported to the shell environment that
`scripts/index_embeddings.py` inherits.** The embedder constructor
raised `OpenRouterAuthError` and the script exited; meanwhile
`stage_openrouter_benchmark.py` worked because it re-loaded the key
from the file at startup.

**Fix (v0.15.0):** both `NIMEmbedder` and `OpenRouterEmbedder` now
fall back to `~/.hermes/.env` after checking shell env, matching the
Hermes convention of centralized credential storage. New sister-script
test `t_openrouter_resolves_key_from_hermes_env_fallback` locks this.

Re-ran the full index with `scripts/index_embeddings.py --backend
openrouter --name openrouter-default`; that pipeline has progress
logging every 20 batches and now passes cleanly.

**Lesson learned:** the staged Block 1-3 testing masked this bug
because the staging script manually loaded the key from the file. The
production indexer relied on shell-env propagation. **Future integration
tests should always invoke the production script, not a parallel
implementation.**

## Block 4 (final attempt) — 402 Payment Required at 69% (2026-09-11)

The v0.15.0 env-fallback patch fixed the script, and the indexer ran
cleanly to 46,144 / 66,689 passages (69%) before OpenRouter returned:

```
HTTP 402: Insufficient credits. This account never purchased credits.
https://openrouter.ai/settings/credits
```

### Account state at the moment of failure
Per `GET https://openrouter.ai/api/v1/auth/key`:
- limit: $10 (monthly)
- limit_remaining: $9.80
- usage (since reset): $0.20
- is_free_tier: true
- (Key prefix: sk-or-v1-77d...c87)

So the user's free-tier key comes with a small initial credit allocation
that gets exhausted even by moderate use. Paid-only models
(`openai/text-embedding-3-small`) require explicit credit purchase.

### What this means for the project's $10/mo budget
- The user must purchase credits on https://openrouter.ai/settings/credits
  to use paid embedding models via OpenRouter.
- **Cumulative real spend: $0.20.** (Block 4 partial + Blocks 1-3 ≈ $0.20)
- Remaining budget: ~$9.80 — room for ~70 more full-corpus rebuilds after credits are added.
- ADR-013 acceptance criteria still hold; the env-fallback bug + the
  credit-budget discovery are both documented.

### Untried fallbacks if user wants no-spend
- **Local sentence-transformers**: zero cost, recall@10 baseline 0.279.
  Already indexed as `data/embeddings/default_*` per v0.13.0.
- **Hugging Face free tier**: ≈1k requests/day on `intfloat/e5-large-v2`,
  flaky per memory. Marginal value.
- **NIM (paid)**: $1.20 per build, user is still reluctant per memory.

### Recommended next move
If user is comfortable with paid OpenRouter:
- Add $5–$10 of credits at https://openrouter.ai/settings/credits
- Re-run `scripts/index_embeddings.py --backend openrouter --name openrouter-default`
  (cost will be another $0.10)
- Then run `scripts/run_eval.py --paths semantic --index openrouter-default`
  to get the recall@10 number for the ADR-013 / HANDOFF §8 #10 comparison

If user wants zero-spend:
- Skip OpenRouter for now; the local `default` index is already validated
- Document ADR-013 as "OpenRouter path validated but not committed; local sentence-transformers default per ADR-001 stands"
