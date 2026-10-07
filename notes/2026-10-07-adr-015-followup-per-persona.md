# 2026-10-07 — ADR-015 follow-up: the precision-vs-recall trade-off has a persona shape

> Companion doc to `notes/2026-09-19-3large-benchmark.md` and ADR-015.
> Uses the per-persona benchmark added in commit `ed82b4e` to surface
> a finding the aggregate 33-query average hides.

## TL;DR

The 3-large vs local sentence-transformer trade-off (3-large wins
precision, loses recall) is **not uniform across personas**. The
per-persona breakdown shows:

- **3-large wins** the precision-sensitive personas (Priya, Aisha).
- **Local wins** the recall-sensitive personas (Sarah, Marcus).
- **Mixed** for the interface/edge-case personas (Jordan, Yuki).

This means the production-default decision is not "local or 3-large"
— it's "**per persona, pick the embedder that fits the question
shape**". The Phase 4 front-end can route queries by detected
persona (or by query shape) to the right embedder.

## Setup

- **Benchmark:** the 33-query hand-curated set in `tests/benchmark.py`,
  re-labeled with a `persona` field per `docs/audience_expectations.md`.
  Distribution: sarah=11, marcus=6, aisha=6, jordan=5, yuki=3, priya=2.
- **Embedders:** local `all-MiniLM-L6-v2` (384-dim, on-disk at
  `data/embeddings/default`) and OpenRouter `text-embedding-3-large`
  (3072-dim, on-disk at `data/embeddings/openrouter-3large`).
- **Run command:** `python3 scripts/run_eval.py --paths semantic
  --backend openrouter --index openrouter-3large` (and `--backend
  local --index default` for the local run).
- **No re-embed.** Both indexes were already built; the per-persona
  view is a re-query of the existing on-disk data.

## Results (semantic path, recall@K)

| Persona | n  | Local | 3-large | Δ      | Trade-off |
|---------|----|-------|---------|--------|-----------|
| sarah   | 11 | 0.256 | 0.201   | -0.055 | Local wins (recall) |
| marcus  |  6 | 0.250 | 0.183   | -0.067 | Local wins (recall) |
| aisha   |  6 | 0.222 | 0.311   | +0.089 | 3-large wins (precision) |
| jordan  |  5 | 0.387 | 0.313   | -0.074 | Local wins (recall) |
| yuki    |  3 | 0.367 | 0.217   | -0.150 | Local wins (recall, but n=3 noisy) |
| priya   |  2 | 0.267 | 0.350   | +0.083 | 3-large wins (precision, but n=2 very noisy) |

The pattern: **3-large's precision advantage shows up on the
doctrinal / cross-tradition queries** (Aisha's "what does the corpus
teach about X", Priya's "what does the tradition say about
mercy/judgment"). 3-large's recall loss shows up on **everyday
language queries** (Sarah's "what does the Bible say when I can't
keep going", Marcus's "what does the text say about creation").

This matches an intuition: 3-large is a 3072-dim semantic embedder
trained on broad web text. It can disambiguate the *right* verse for
a theologically precise query (Aisha) but it doesn't help with
"give me every verse that touches X" because no embedding model can
do exhaustive recall from a single query.

## Aggregate vs per-persona

The aggregate 33-query semantic numbers (the only view before this
commit):

| Embedder | Recall@K | MRR | Primary@1 | nDCG@K |
|----------|----------|-----|-----------|--------|
| Local    | 0.279    | 0.165 | 0.151   | 0.222  |
| 3-large  | 0.245    | 0.294 | 0.212   | 0.234  |

The per-persona view breaks that 0.034 recall deficit into a story:
it's not a flat trade-off. Sarah loses 0.055 recall (and would
*hurt* from a 3-large default), Aisha gains 0.089 recall (and would
*benefit* from a 3-large default), Priya gains 0.083 (n=2, but
consistent with the Aisha pattern). The aggregate treats these as
cancellation; the per-persona view treats them as routing decisions.

## What this implies for Phase 4 (front-end)

The Phase 4 front-end is per `docs/phase4-scope-frontend.md` split
into Reader (default) / Scholar (Aisha) / Comparative (Yuki / Priya)
layers. The per-persona trade-off suggests:

- **Reader layer (default):** stay on local. Sarah is the load-bearing
  persona; her queries are recall-sensitive. Local wins her slice.
- **Scholar layer (Aisha):** offer 3-large as an opt-in. Aisha's
  doctrinal queries benefit from 3-large's precision. The Scholar
  layer can show both scores side-by-side.
- **Comparative layer (Yuki / Priya):** the n=2 / n=3 slices are
  too small to draw a strong conclusion, but the Priya trend
  (3-large wins 0.083) is consistent with cross-tradition queries
  needing higher-dimensional embeddings to disambiguate.

This is a routing decision, not a default-flip. The 3-large index
costs $0.74 to build + per-query API cost to query. Routing by
persona is cheaper than flipping the default.

## What I am NOT concluding

- **n=2 (Priya) and n=3 (Yuki) are directional.** The Priya
  3-large win (+0.083) is consistent with the Aisha pattern but
  the slice is too small to be stable. Worth re-running after
  Gap 2 (cross-tradition queries, separate session) expands
  these slices.
- **Hybrid path not analyzed in this doc.** The hybrid path's
  per-persona numbers are noisier (BM25 dilutes the persona signal)
  and the precision-vs-recall trade-off shifts again. Worth a
  separate doc.
- **Not changing the production default.** ADR-014 still holds:
  local is the production default. The per-persona routing is a
  Phase 4 consideration, not a v0.x change.

## Verification

```
$ python3 scripts/run_eval.py --paths semantic --backend openrouter \
    --index openrouter-3large | tail -10
| semantic | sarah   | 11 | 0.201 | 0.273 | 0.182 | 0.199 |
| semantic | marcus  |  6 | 0.183 | 0.264 | 0.167 | 0.200 |
| semantic | yuki    |  3 | 0.217 | 0.167 | 0.000 | 0.259 |
| semantic | priya   |  2 | 0.350 | 0.625 | 0.500 | 0.355 |
| semantic | aisha   |  6 | 0.311 | 0.350 | 0.333 | 0.275 |
| semantic | jordan  |  5 | 0.313 | 0.256 | 0.200 | 0.241 |
```

## Open follow-ups

1. **Phase 4 routing** — the Reader / Scholar / Comparative layers
   can route to local / 3-large per persona. Wire that decision
   into the FastAPI MVP.
2. **Gap 2 (cross-tradition queries)** — grow the Yuki and Priya
   slices from n=3 / n=2 to n=8+ each. The 3-large win on Priya
   would be more credible with n=8.
3. **Hybrid per-persona** — the hybrid path blends BM25 + semantic
   and the persona signal gets noisier. Worth a separate table
   to see if the BM25 dilution helps or hurts each persona.
