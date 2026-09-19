# 2026-09-19 — text-embedding-3-large benchmark (full 66K + 33-query eval)

## What I did

After the v0.15.0 / ADR-015 comparison settled local as the measurable
default (0.279 recall@K vs 0.189 for `text-embedding-3-small`), the
question was whether a *bigger* OpenAI embedder would shift the picture.
`text-embedding-3-large` is the natural next step — same family as
3-small but 3072-dim (vs 1536), $0.13/M tokens (vs $0.02), and known
to be a meaningful quality step on OpenAI's internal benchmarks.

Also tested `qwen/qwen3-embedding-8b` (4096-dim, ~free) but the
OpenRouter free endpoint hit `urllib.TimeoutError` on batch 2 of a 2K
test — same connection-state pathology that bit the Tanakh ingest on
2026-09-11. Doc'd here for the record; not pursued further.

## Full 66K index build

```
$ OPENROUTER_EMBED_MODEL=openai/text-embedding-3-large \
  python3 scripts/index_embeddings.py --backend openrouter \
  --name openrouter-3large
```

- Wall time: 1576.36s (26 min)
- Throughput: 42.3 vec/s
- Dim: 3072
- Index files: `data/embeddings/openrouter-3large_{meta.json, vectors.bin}` (22 MB + 370 MB)
- Cost: ~$0.74 (OpenRouter account went from $0.32 → $1.06 since reset)

Note on exit code: process supervisor returned 137 (SIGKILL) during the
final save step. The vectors + metadata were already written to disk
before the kill; `load_vector_index` confirms all 66,689 entries are
readable. Treated as cosmetic.

## 33-query eval (semantic path)

Same `tests/benchmark.py` queries used for ADR-015, top-k=10, single
batch per query:

| Embedder | dim | Recall@K | MRR | Primary@1 | nDCG@K | q/s |
|----------|-----|----------|-----|-----------|--------|-----|
| Local `all-MiniLM-L6-v2` | 384 | **0.279** | 0.165 | 0.151 | 0.222 | **0.3** |
| OpenRouter `text-embedding-3-small` | 1536 | 0.189 | 0.199 | 0.121 | 0.184 | 0.1 |
| OpenRouter `text-embedding-3-large` | 3072 | 0.245 | **0.294** | **0.212** | **0.234** | 0.1 |

### Read

`text-embedding-3-large` is a **meaningful step up from 3-small** on
every quality metric:
- Recall@K: +30% (0.189 → 0.245)
- MRR: +48% (0.199 → 0.294)
- Primary@1: +75% (0.121 → 0.212)
- nDCG: +27% (0.184 → 0.234)

But local `all-MiniLM-L6-v2` still wins on Recall@K (+14% over
3-large), and at 3× the query throughput. The trade-off is now:

- **Local:** better raw recall, free, fast. Best for "find me every
  verse related to X" (Sarah persona).
- **3-large:** better ranking when it hits, costs $0.74 per full
  rebuild, 3× slower at query time. Best for "which single verse is
  THE answer" (Yuki / Marcus persona).

### Spot-check on the 8 conceptual queries (qwen3 vs 3-small)

Before pivoting to 3-large I tested `qwen/qwen3-embedding-8b` on a
200-passage slice. Same query → same Genesis 1:1 hit but at score
0.805 vs 3-small's 0.683. Interesting signal, but the endpoint
unreliability blocked the full corpus build.

## Decision

**Local stays the production default.** ADR-014 unchanged.
ADR-015 is amended to record the 3-large numbers and the precision-
vs-recall framing so future contributors don't get confused by
"OpenRouter wins on 3/5 metrics" out of context.

3-large is wired and available as a precision-focused alternate for
any future feature that needs Primary@1 over Recall@K. Not the default
because:
- Sarah (Persona 4, lay-faithful) is the load-bearing persona per the
  Council design — comprehensive results matter more than precise ones.
- The runtime contract exists for Sarah.
- 3× query latency is a real UX hit at the front-end layer.

## Artifacts

- `data/embeddings/openrouter-3large_*` — full 3072-dim 66K index
- `data/embeddings/openrouter-staging-qwen3-embedding-8b-b2_*` — 200-passage qwen3 slice (proof of endpoint reachability, not a full corpus)
- `scripts/stage_openrouter_model.py` — generalized Stage 1 harness
  that accepts `--model` (the existing `stage_openrouter_benchmark.py`
  hardcodes the default model)

## OpenRouter account state (end of session)

- usage since reset: $1.06
- remaining: $8.94
- cost of this session: $0.74 (3-large full build) + $0.001 (qwen3
  200-passage) + ~$0.005 (eval queries) ≈ **$0.75**
