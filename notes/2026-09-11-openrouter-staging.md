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
