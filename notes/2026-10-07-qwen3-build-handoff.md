# 2026-10-07 — qwen3-8b build in progress (handoff)

## Status (snapshot at 11:53 EDT)

- **Background process** `proc_336e89275438` running the full 66K
  passage build of `qwen/qwen3-embedding-8b` (4096-dim) on
  OpenRouter.
- **Progress:** 23,104 / 66,689 passages (34.6%) at 11:53 EDT.
- **ETA:** ~22-25 more minutes (build started 11:35, full build
  expected ~12:15-12:20 EDT).
- **Cost:** open-ended; will land in OpenRouter credit usage when
  complete. Started this hour at $1.06 used, $8.94 remaining
  of the $10 budget.
- **Log:** `/tmp/qwen3-build.log`

## When it finishes

The process will write two files to `data/embeddings/`:
- `openrouter-qwen3-8b_meta.json` (entries array)
- `openrouter-qwen3-8b_vectors.bin` (4096-dim float32 vectors, ~1GB)

After the files land, **re-run the per-persona eval**:

```bash
PYTHON_BIN=/home/pierce/.hermes/tools/python-3.14.7+202****0901-linux-x64/bin/python3
OPENROUTER_EMBED_MODEL=qwen/qwen3-embedding-8b \
  $PYTHON_BIN scripts/run_eval.py \
    --paths semantic \
    --backend openrouter \
    --index openrouter-qwen3-8b \
    > /tmp/eval-qwen3-39query.log 2>&1
```

(Use the Hermes Python 3.14 — it has sentence-transformers 6.1.0;
system python3.12 doesn't.)

## What to do with the results

Build the 3-embedder per-persona table:

| Persona | n  | Local R@K | 3-large R@K | qwen3 R@K |
|---------|----|-----------|-------------|-----------|
| sarah   | 11 | 0.256     | 0.201       | ? |
| marcus  |  6 | 0.250     | 0.183       | ? |
| aisha   |  6 | 0.222     | 0.311       | ? |
| jordan  |  5 | 0.387     | 0.313       | ? |
| yuki    |  6 | 0.183     | 0.150       | ? |
| priya   |  5 | 0.107     | 0.140       | ? |

**Two scenarios to watch for:**

1. **qwen3 also wins Aisha + Priya on recall** → the finding is
   "more dimensions = better for doctrinal precision" (structural).
   The persona shape is model-shape-independent. Write up as a
   follow-up to ADR-015.

2. **qwen3 does NOT win Aisha + Priya** → 3-large is the only
   model with that profile. The finding is "3-large specifically
   has doctrinal-precision benefits" (specific to OpenAI's
   model). Worth a different writeup.

The MRR direction (3-large wins all 6) is expected to hold for
qwen3 too. The interesting data point is whether qwen3 wins Aisha
+ Priya on *recall* — the precision dimension is already 3-large
across the board.

## Open follow-ups (in priority order)

1. **Wait for qwen3-8b build to complete** — re-run the eval with
   the 39-query benchmark, build the 3-embedder per-persona
   table.
2. **Hybrid per-persona table** — the hybrid path blends BM25 +
   semantic and the persona signal is noisier. BM25 Priya is
   0.000 (no Quran / Torah in BM25 corpus), so the hybrid's
   Priya number is mostly semantic. Worth documenting.
3. **Phase 4 routing** — wire per-persona → embedder choice into
   the FastAPI MVP. Reader (Sarah) stays on local; Scholar
   (Aisha) routes to 3-large; Comparative (Yuki / Priya) gets
   a per-query choice.
4. **CI threshold gate** — currently gates at the aggregate
   level (semantic ≥ 0.25, hybrid ≥ 0.22, bm25 ≥ 0.06). Should
   the gate also enforce per-persona minimums? Probably not for
   the aggregate threshold, but worth a per-persona regression
   check (e.g., "3-large semantic on Aisha must not drop below
   0.30 recall@K").