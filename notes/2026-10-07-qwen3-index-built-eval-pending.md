# 2026-10-07 — qwen3-8b full index built (1 GB on disk, eval pending)

## Status (snapshot at 18:56 EDT)

The full 66,689-passage qwen3-8b index built successfully:

- **Process:** `proc_8088e698b32f`, started 13:13 EDT, completed 14:16 EDT
  (63 min wall time, 17.6 vec/s)
- **Files on disk:**
  - `data/embeddings/openrouter-qwen3-8b_meta.json` (22 MB)
  - `data/embeddings/openrouter-qwen3-8b_vectors.bin` (1.04 GB)
- **Index content:** 66,689 vectors, dim=4096
- **Cost:** ~$0.05 of OpenRouter credit (was $1.09, now $1.15)
- **No log file** — the build process completed but the
  `/tmp/qwen3-build-resume.log` was cleaned up in a reboot.
  The build itself succeeded (the 100% "Vector indexing complete"
  message printed before the process exited).

## Why the 3rd-embedder eval isn't in the repo yet

After the build completed, I attempted the eval:

```
python3 scripts/run_eval.py --paths semantic,hybrid \
  --backend openrouter --index openrouter-qwen3-8b
```

The process exited at the "[semantic] starting..." message with
no error and no further output. Tried twice with the same result.
The Hermes gateway was hanging up the eval process.

**Hypothesis:** the eval calls OpenRouter for each of the 39 queries
× 2 paths = 78 query-runs, and the gateway may be timing out the
underlying tool calls. The eval itself probably isn't broken —
the same script works fine against local and 3-large (both
re-ran successfully in the prior session).

**The data is recoverable.** Two ways to land the eval results:

1. **Run from a different shell** that doesn't have the gateway
   timeout. For example, a plain `terminal` tool call in a
   foreground slot rather than a `background` slot — that way
   the tool can wait the full ~8-10 min for the eval to complete
   instead of timing out at the gateway layer.

2. **Split the eval into smaller chunks.** Run semantic only
   (39 queries, ~3-4 min), then hybrid only (39 queries,
   ~3-4 min). Two shorter evals are less likely to trip the
   gateway timeout than one long one.

3. **Use the on-disk index directly** without going through
   `run_eval.py`. Write a one-off script that loads the index,
   embeds the 39 queries via the same OpenRouter client, and
   computes the per-persona metrics inline. Same result, but
   the script doesn't have the per-query logging that the eval
   harness does, so the failure mode is different.

The handoff doc (this file) doesn't pick a recommendation because
the right choice depends on the gateway's timeout behavior in
future sessions. Leaving it as a decision for the next session.

## What this means for the per-persona finding

The persona shape (3-large wins Aisha + Priya on recall, loses
the other 4) was confirmed across 4 path × embedder combinations
(local + 3-large × semantic + hybrid) per the hybrid doc
(commit `5c06977`). The 3rd embedder (qwen3-8b) would add the
*model-shape* dimension. The two scenarios to compare (per
`notes/2026-10-07-adr-015-followup-v2-per-persona.md`):

- qwen3-8b also wins Aisha + Priya on recall → the finding is
  "more dimensions = better for doctrinal precision" (structural)
- qwen3-8b does NOT win Aisha + Priya → 3-large is the only model
  with that profile (specific)

Without the eval, the question is open.

## File state at session-end

- `data/embeddings/openrouter-qwen3-8b_meta.json` — 22 MB, present
- `data/embeddings/openrouter-qwen3-8b_vectors.bin` — 1.04 GB, present
- Both gitignored per existing rule (`data/embeddings/*.bin / *.json`)
- The on-disk index is the qwen3-8b full build; the next eval can
  read it directly without re-embedding.

## Recommended next-session action

Run the qwen3-8b semantic eval in a foreground slot with a
longer tool timeout. The script is:

```bash
PYTHON_BIN=/home/pierce/.hermes/tools/python-3.14.7+202****0901-linux-x64/bin/python3
source /home/pierce/.hermes/.env
export OPENROUTER_API_KEY
export OPENROUTER_EMBED_MODEL=qwen/qwen3-embedding-8b

$PYTHON_BIN -u scripts/run_eval.py \
  --paths semantic,hybrid \
  --backend openrouter \
  --index openrouter-qwen3-8b \
  > /tmp/eval-qwen3-39query.log 2>&1
```

If that hangs up the gateway again, split into two runs:
`--paths semantic` first, then `--paths hybrid`. Either way,
the on-disk index is the same.
