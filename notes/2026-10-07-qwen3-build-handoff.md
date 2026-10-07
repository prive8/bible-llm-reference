# 2026-10-07 — qwen3-8b build in progress (handoff)

## Status (final, session-end 12:27 EDT)

- **Full 66K build** was attempted but killed at 75% (50,000 / 66,689
  passages processed) around 12:19 EDT. No output files written —
  the script only writes the index at the very end (line 224 of
  `scripts/index_embeddings.py`), so the ~$0.02 of OpenRouter
  embedding work done was lost. The previous 2026-09-19 attempt
  had the same problem (see `notes/2026-09-19-3large-benchmark.md`).
  This is a known fragility of the current index script.
- **5K probe build** completed successfully (12:26 EDT, 5 min 27s
  wall time, 15.3 vec/s). Two files written:
  - `data/embeddings/openrouter-qwen3-8b-5k_meta.json` (1.4 MB)
  - `data/embeddings/openrouter-qwen3-8b-5k_vectors.bin` (81 MB)
- **256-passage probe** also completed (14.21s, 18 vec/s). Smoke
  test on "creation account in the Quran" → Genesis 1:1 ranked
  first. Endpoint works correctly at all sizes tested.

## Throughput observed

| Build | Throughput | Total time (66K equiv) |
|-------|-----------|------------------------|
| 256 passages | 18 vec/s | 61 min |
| 5,000 passages | 15.3 vec/s | 72 min |
| 50,000 passages (incomplete) | ~22 vec/s* | 50 min |
| 3-large (prior session, 66K) | 42 vec/s | 26 min |

*The 50K was a partial run, so the throughput is averaged over a
mixed workload including ramp-up. Treat the 5K number (15.3
vec/s) as the canonical "qwen3 is 3x slower than 3-large" number.

**The full 66K qwen3 build is estimated at ~70 min wall time.**
That's longer than my available session windows (30-60 min).
Strategy: do it overnight or in a dedicated window.

## When it finishes

The full 66K build (if re-attempted) will write two files to
`data/embeddings/`:
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

## Alternative: do the full build overnight

The full 66K build is ~70 min. If you have a dedicated overnight
window, kick it off before bed:

```bash
# Start as a background process
nohup bash -c '
  PYTHON_BIN=/home/pierce/.hermes/tools/python-3.14.7+202****0901-linux-x64/bin/python3
  source /home/pierce/.hermes/.env
  export OPENROUTER_API_KEY
  export OPENROUTER_EMBED_MODEL=qwen/qwen3-embedding-8b
  $PYTHON_BIN -u scripts/index_embeddings.py --backend openrouter \
    --name openrouter-qwen3-8b 2>&1 > /tmp/qwen3-build.log
' >/dev/null 2>&1 &

# Check on it
sleep 1800 && ls -la data/embeddings/openrouter-qwen3-8b_*
```

The 5K probe shows the endpoint is reliable at small scale; the
issue with the full build is *only* that the script doesn't
checkpoint, so any process death before the final write loses
the work. Adding checkpointing to `scripts/index_embeddings.py`
is a separate fix (one line per batch range would do it).

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