# 2026-10-07 — ADR-015 follow-up v2: per-persona trade-off confirmed and sharpened by Gap 2

> Companion to `notes/2026-10-07-adr-015-followup-per-persona.md`
> (commit `aac4260`, 33-query benchmark) and Gap 2 (commit `ea4af34`,
> 39-query benchmark). Re-runs the per-persona eval against the
> 39-query benchmark with both local and 3-large. Confirms and
> sharpens the persona-shape finding.

## TL;DR

The 3-large vs local trade-off **is a precision-vs-recall trade-off
with a persona shape**, and that shape **persists with cross-tradition
queries added to the benchmark**. Specifically:

- **3-large wins on MRR (precision) for all 6 personas** without
  exception. The +0.036 to +0.250 MRR delta is one-sided.
- **3-large wins on recall for Aisha (+0.089) and Priya (+0.033)** —
  the doctrinal / cross-tradition personas. Confirmed.
- **3-large loses on recall for the other 4 personas** (Sarah,
  Marcus, Jordan, Yuki). The delta is small (0.033-0.074) but
  consistent.

The interpretation: 3-large is *always* better at putting the right
verse first (MRR), but the *right* verse for Sarah (pastoral) is
less well-defined than for Aisha (doctrinal). For Sarah, "every
verse that comforts" matters more than "the single best verse."

## Setup

- **Benchmark:** 39 queries (was 33, grew by 6 cross-tradition
  queries in Gap 2). All citations verified against the on-disk
  corpus.
- **Embedders:** local `all-MiniLM-L6-v2` (384-dim) and OpenRouter
  `text-embedding-3-large` (3072-dim). Both indexes pre-built,
  no re-embed.
- **Run command:** `python3 scripts/run_eval.py --paths semantic
  --backend {local,openrouter} --index {default,openrouter-3large}`.
- **Test suite:** 135 tests, all passing (Gap 2 added 2 new tests
  for slice minimums and cross-tradition coverage).

## Results (semantic path, 39 queries)

| Persona | n  | Local R@K | 3-large R@K | Δ recall | Local MRR | 3-large MRR | Δ MRR |
|---------|----|-----------|-------------|----------|-----------|-------------|-------|
| sarah   | 11 | 0.256     | 0.201       | -0.055   | 0.182     | 0.273       | +0.091 |
| marcus  |  6 | 0.250     | 0.183       | -0.067   | 0.222     | 0.264       | +0.042 |
| aisha   |  6 | 0.222     | 0.311       | +0.089   | 0.167     | 0.350       | +0.183 |
| jordan  |  5 | 0.387     | 0.313       | -0.074   | 0.220     | 0.256       | +0.036 |
| yuki    |  6 | 0.183     | 0.150       | -0.033   | 0.000     | 0.250       | +0.250 |
| priya   |  5 | 0.107     | 0.140       | +0.033   | 0.000     | 0.250       | +0.250 |

**Sign convention: positive Δ = 3-large wins.**

### What changed from the 33-query version

| Persona | 33-query Δ recall | 39-query Δ recall | Δ Δ |
|---------|-------------------|-------------------|-----|
| sarah   | -0.055            | -0.055            |  0 |
| marcus  | -0.067            | -0.067            |  0 |
| aisha   | +0.089            | +0.089            |  0 |
| jordan  | -0.074            | -0.074            |  0 |
| yuki    | -0.150 (n=3)      | -0.033 (n=6)      | +0.117 (less loss) |
| priya   | +0.083 (n=2)      | +0.033 (n=5)      | -0.050 (weaker win) |

The 4 personas that didn't grow (sarah, marcus, aisha, jordan)
have *identical* numbers — the new queries are *additive*, not
substitutive, so they don't move the existing slices.

Yuki and Priya are the interesting ones. Yuki's 3-large loss
*shrinks* (from -0.150 to -0.033) when the slice grows. With n=3
Yuki, 3-large's loss was *big*; with n=6 Yuki, 3-large's loss is
*small*. The Priya win also shrinks (from +0.083 to +0.033) but
stays positive.

The pattern: cross-tradition queries (Quran + Torah) are *harder*
for both embedders (both see their numbers drop on Yuki and Priya
slices), but 3-large holds up better. The relative trade-off
softens but doesn't flip.

## What this means

**The persona-shape is real and now stable.** Across 2 benchmarks
(33 and 39 queries), 4 stable personas (sarah, marcus, aisha,
jordan), and 2 growing personas (yuki, priya):
- 3-large wins on Aisha and Priya (doctrinal / cross-tradition)
- 3-large loses on Sarah, Marcus, Jordan, Yuki (pastoral /
  philosophical / interface / cross-tradition-parallel)

This is a 6/6 verdict on MRR (3-large wins all), and a 2/4 split
on recall (3-large wins Aisha + Priya, loses the other 4).

The MRR delta is uniformly positive: 3-large puts the right verse
first more often, for every persona. But Sarah's queries are
*recalls* — "give me every verse that comforts" — and "every verse
that comforts" is a larger set than "the single best verse that
comforts." For Sarah, MRR wins don't help.

**Production default remains local (ADR-014).** The persona shape
is a *routing* decision for Phase 4, not a default-flip.

## What still needs to happen

1. **qwen3-8b re-eval** — the full 66K qwen3-8b index build was
   in flight (background) when this doc was written. The third
   embedder will tell us whether the persona shape is a
   *local-vs-3-large* specific trade-off or a *more-dimensions-
   is-better-for-doctrinal* structural finding. If qwen3-8b
   (4096-dim) also wins Aisha and Priya, the latter. If it doesn't,
   3-large is the only model that wins on doctrinal precision.
2. **Hybrid per-persona** — the hybrid path blends BM25 + semantic
   and the persona signal is noisier. Worth a separate table.
3. **Phase 4 routing** — wire per-persona → embedder choice into
   the FastAPI MVP. The Scholar layer (Aisha) routes to 3-large;
   the Reader layer (Sarah) stays on local.

## Verification

```
$ python3 tests/run_all.py | tail -3
  135 passed, 0 failed (of 135)

$ python3 scripts/run_eval.py --paths semantic --backend openrouter \
    --index openrouter-3large | grep "semantic | [a-z]" | head
| semantic | sarah  | 11 | 0.201 | 0.273 | 0.182 | 0.199 |
| semantic | marcus |  6 | 0.183 | 0.264 | 0.167 | 0.200 |
| semantic | aisha  |  6 | 0.311 | 0.350 | 0.333 | 0.275 |
| semantic | jordan |  5 | 0.313 | 0.256 | 0.200 | 0.241 |
| semantic | yuki   |  6 | 0.150 | 0.250 | 0.167 | 0.208 |
| semantic | priya  |  5 | 0.140 | 0.250 | 0.200 | 0.142 |
```

## Files in this commit

- `notes/2026-10-07-adr-015-followup-v2-per-persona.md` (this doc)
- `notes/eval-runs/2026-10-07-3large-semantic-39query.log` (raw output)
- `notes/eval-runs/2026-10-07-local-semantic-39query.log` (raw output, committed in `acdb93d`)