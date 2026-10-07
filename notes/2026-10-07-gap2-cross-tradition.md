# 2026-10-07 — Gap 2 (cross-tradition queries) + qwen3-8b full index build (in progress)

## What I did

### Gap 2 data (committed in this session)

Added 6 new cross-tradition queries to `tests/benchmark.py` to grow
the Yuki and Priya slices from n=3 and n=2 (directional-only) to
n=6 and n=5 (stable / directional-but-stronger).

Benchmark now 33 → 39 queries:

| Persona | Before | After | Δ |
|---------|--------|-------|---|
| sarah   | 11 | 11 | 0 |
| marcus  |  6 |  6 | 0 |
| aisha   |  6 |  6 | 0 |
| jordan  |  5 |  5 | 0 |
| yuki    |  3 |  6 | +3 |
| priya   |  2 |  5 | +3 |

The 6 new queries and their primary citations:

1. **"creation account across the Bible and the Quran"** (yuki) —
   Genesis 1:1-2, John 1:1-3, Quran 2:30 (khalifa), Quran 32:4-5,
   Quran 7:54
2. **"monotheism in the Shema and the Quran"** (yuki) —
   Deuteronomy 6:4, Quran 112:1-4 (al-Ikhlas), Isaiah 43:10-11,
   Quran 2:163
3. **"mercy and compassion in the Hebrew Bible and the Quran"**
   (yuki) — Exodus 34:6-7, Quran 1:1-3 (al-Fatiha), Psalms 103:8-14,
   Quran 2:64
4. **"shared stories of prophets in Jewish and Muslim traditions"**
   (priya) — Genesis 12:1-3, Quran 21:51-73, Quran 6:83-86,
   Genesis 22:1-19
5. **"law and mercy in the Hebrew Bible and the Quran"** (priya) —
   Hosea 6:6, Quran 2:177, Micah 6:8, Quran 5:32
6. **"hospitality to strangers across Jewish and Islamic tradition"**
   (priya) — Genesis 18:1-8, Quran 51:24-27, Quran 11:69-77,
   Hebrews 13:2

All citations verified against the on-disk corpus before commit.
The Hosea + Micah + Isaiah references are in the `translations/*.json`
files (the ones that `bible parallel` can serve), not the Strong's-
augmented `kjv.json`. The `bible parallel` CLI has a single-verse
parser bug (returns empty for `Hosea 6:6` but works for
`Hosea 6:6-7`) — noted for later.

### New sister-script tests

- `t_eval_benchmark_per_persona_slices_meet_minimum` — asserts each
  persona slice meets the documented minimums (sarah=6, marcus=6,
  aisha=6, jordan=5, yuki=6, priya=5). Pins the slice sizes from
  the Gap 2 work so a future contributor can't silently shrink
  them by removing queries.
- `t_eval_benchmark_cross_tradition_queries_exist` — asserts at
  least 4 BENCHMARK queries have expected citations spanning
  multiple traditions (Bible+Quran or Torah+Quran). Without
  this, a future contributor could delete all cross-tradition
  queries and the eval would silently become Bible-only again.

Suite: 133 → 135 tests, all passing.

### qwen3-8b full index build (in progress, background)

Launched a full-corpus build of `qwen/qwen3-embedding-8b` (4096-dim)
on the OpenRouter side. The 2026-09-19 attempt at this model
failed at batch 2 of 2K due to OpenRouter endpoint unreliability
(see `notes/2026-09-19-3large-benchmark.md`). Trying again at full
66K scale; if it succeeds, this gives a third embedder to compare
against local + 3-large.

Why bother: the per-persona finding (3-large wins Aisha/Priya,
loses Sarah/Marcus) is currently a single data point per persona.
If qwen3-8b (4096-dim) *also* wins the doctrinal/cross-tradition
personas, the finding becomes "more dimensions = better for
doctrinal precision" — a structural claim about embedding
geometry, not a 3-large-specific quirk. If it doesn't, the finding
is more interesting and worth a different writeup.

**Status at session-end:** background process running, ~8% complete
(5,184 / 66,689 passages). ETA: 20-25 min from session start.
Build log: `/tmp/qwen3-build.log`. Final log will be archived
to `notes/eval-runs/` if the build succeeds.

## What I am NOT doing

- **Not changing the 3-large vs local finding yet.** The new
  queries will shift the per-persona numbers slightly (Yuki +3
  queries might lose its 3-large loss; Priya +3 might confirm
  the 3-large win). Re-eval against the new 39-query benchmark
  is a separate step, after the qwen3-8b build completes.
- **Not changing the production default.** ADR-014 still holds.
- **Not adding non-Abrahamic corpora (Vedas, Tao Te Ching).** Out
  of scope for the 66K Abrahamic + early-Jewish corpus.

## Verification

```
$ python3 tests/run_all.py | tail -3
  135 passed, 0 failed (of 135)
```

```
$ python3 -c "from tests.benchmark import BENCHMARK; print(len(BENCHMARK))"
39
```

## Open follow-ups (in priority order)

1. **Wait for qwen3-8b build to complete** (~20-25 min ETA).
   Re-run the eval against the new `openrouter-qwen3-8b` index
   with the 39-query benchmark. Per-persona table for qwen3 vs
   local vs 3-large.
2. **Re-eval all three embedders against the 39-query benchmark**
   (local, 3-large, qwen3-8b). New per-persona table with 3
   data points per persona. The cross-tradition queries (Yuki +
   Priya) will exercise the Quran side for the first time.
3. **ADR-015 follow-up v2**: the precision-vs-recall trade-off
   has a persona shape *and* a model shape. Worth a doc.
4. **Hybrid per-persona table** (already noted in the earlier
   follow-up doc, still pending a doc of its own).
5. **Close the loop on Priya** to n=6 (one more query). Quick
   follow-up if time permits.
