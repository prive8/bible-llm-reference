# 2026-10-25 — Restoring the retrieval regression gate

Session by dad-h2 (Hermes agent, father's fleet). Steven asked for the CI cleanup on the bible-llm side.

## Done

1. **Diagnosed why `eval-regression` had not run since 2026-09-19.**
   The job was `cancelled` on every push from 2026-09-19 through 2026-10-08 — 7 consecutive runs, most recently `fdeee0f`. The last successful run of that job was `21f77eb` on 2026-09-19. The 8 matrix test jobs kept succeeding the whole time, which is why the repo read green while retrieval had not been checked for a month.

   Two independent causes, both confirmed by rebuilding the index and re-running the eval locally rather than by reading the CI logs.

2. **Cause 1 — the job timed out.** `timeout-minutes: 15`, and the index build no longer fits.

   The step comment said "~2 min on CPU at batch=64". That was true when the corpus was 43,483 passages. Multi-tradition support (`fdeee0f`) grew it to **66,689** — 37,247 Christianity + 6,236 Islam + 23,206 Judaism — and the build command has no `--no-quran`/`--no-torah`, so CI now indexes all three traditions.

   Measured: a full rebuild with the exact CI command took **12.0 min** on a 6-core box. The `ubuntu-latest` runner has 2 vCPU. **Later measured on the real runner: 835s (13.9 min).** I originally wrote "~36 min" by scaling linearly from the 6-core box; that was wrong by ~2.5×, because the embedding work does not scale linearly with core count. The conclusion is unchanged — setup+install (1.3 min) plus the build (14.1 min) is 15.4 min, already past the 15-min wall before the tests or eval could start. On the last cancelled run the build step consumed 13m41s of a 15-min budget and the job was killed with the test and eval steps `skipped`.

3. **Cause 2 — the gate would have failed even if it had finished.** The `semantic` threshold is 0.25 and the unscoped measurement is **0.234**. That is not a retrieval regression — it is the v1 benchmark being scored against a corpus it was never written for.

   The v1 benchmark's 204 expected citations are **all Bible**. With 29,442 non-Bible passages competing for the same top-10 slots, the number measures dilution rather than retrieval quality. Three pieces of evidence:

   - The old 43,483-entry index (2026-09-09, before the multi-tradition work) scores **0.272** on the current code. The code did not get worse.
   - Scoped to `--tradition christianity`, the new 66,689-entry index scores **0.282** semantic / **0.273** hybrid — at or above the v0.10.0 baseline (0.279 / 0.258).
   - The unscoped 0.234 is a benchmark-scope mismatch, not a quality drop. F0a (`d5bbfce`) also flipped the Judaism slice from pointed Hebrew to English `jps1917-modernized`, so English Tanakh text now competes for English-language queries too.

4. **Fixed the workflow** (`.github/workflows/ci.yml`, commit `38eb7f1`):
   - **Cache the built index**, keyed on a content hash of the corpus files plus the indexer code (`scripts/index_embeddings.py`, `bible/semantic.py`, `bible/lookup.py`, `bible/quran.py`, `bible/torah.py`, `bible/tanakh.py`). Only a corpus or embedder change pays the ~14 min build; every other push restores the cache and runs the eval in ~6.5 min total. This is the same trick the workflow already uses for the 80 MB sentence-transformers model, one level up.
   - **`timeout-minutes: 60`** as a backstop for a cold-cache run.
   - **Scope the gate to `--tradition christianity`**, matching the benchmark it scores. The thresholds are deliberately **not** lowered — moving semantic to 0.23 would encode a scope mismatch as the new normal and hide a genuine regression later.
   - **A verify step** so a missing index fails loudly instead of silently skipping the semantic and hybrid paths and letting the gate pass on BM25 alone.

5. **Verified locally** against a rebuilt 66,689-passage index, running the exact gate script from the workflow:

   ```
   bm25      recall@10=0.108  threshold=0.060  [PASS]
   semantic  recall@10=0.282  threshold=0.250  [PASS]
   hybrid    recall@10=0.273  threshold=0.220  [PASS]
   ```

   Injecting a synthetic 0.200 semantic row makes the gate fail, so it is a real gate and not a vacuous one. Sister-script suite: 147 passed, 0 failed.

6. **Verified on the real runner.** Run `40216038726` on `f873558` went **green** — the retrieval gate executed for the first time since 2026-09-19 and reported bm25 **0.108**, semantic **0.282**, hybrid **0.273**, matching the local measurement exactly. Cold run: 20.9 min total (setup+install 1.3, build 14.1, verify+tests 0.8, eval 4.5).

7. **Found and fixed a stale-cache bug in my own fix** (commit `aa7fd51`). The v1 workflow used an `actions/cache` `restore-keys` prefix *and* built without `--overwrite`. Those two combine badly: `actions/cache` restores the most recent prefix match when the exact key misses, but reports `cache-hit=false` for it — so on a corpus change a **stale** index is restored to disk, the build step runs, and `index_embeddings.py` exits 1 with "partial index exists… Pass --resume or --overwrite". The first push touching the corpus would have turned the gate red even though nothing was broken. Reproduced locally before it could fire.

   Fixes:
   - **Dropped `restore-keys` on the index cache.** An exact key match is the only case where the restored index is guaranteed to correspond to the current corpus. The sentence-transformers model cache keeps its `restore-keys` — that one is safe, because it is keyed by model name and a wrong restore is merely a cache miss.
   - **Added `--overwrite`** to the build, so the index is replaced rather than the build failing if anything is already on disk.
   - **Strengthened the verify step.** It previously only checked that the meta file existed. It now recomputes the expected passage count from the corpus itself (no embedder needed, ~0.4 s) and checks it against the index metadata, and checks the `.bin` size is exactly `count * dim * 4`. Tested against four cases: good index (exit 0), missing index (1), stale index with the old 43,483 count (1), truncated `.bin` (1).

   Run `40220328946` on `aa7fd51` then went **green again** with the build step `skipped` on a cache hit and the same three numbers. Warm run: **6.5 min** total.

   Worth knowing: `cache-hit` is `true` only on an **exact** key match. A `restore-keys` restore silently gives you files that do not correspond to the key you asked for.

## Decisions

- **Did not lower the semantic threshold.** The 0.234 measurement is an artifact of scoring a Bible-only benchmark against a three-tradition corpus. Scoping the query is the correct fix; re-baselining the threshold would hide future regressions.
- **Chose caching over simply raising the timeout.** A 60-minute timeout alone would make the gate run but burn ~14 min of runner time on every push to `main`. The cache reduces that to ~6.5 min on most pushes and keeps the ~14 min cost for the rare corpus change that actually needs it.
- **Cached on corpus content, not on the commit SHA.** The index is a pure function of the corpus files and the embedder, so a code-only push should reuse it. The hash covers both, and the path is included so a rename invalidates the cache too.
- **Used an exact cache key with no `restore-keys`.** A prefix restore is a footgun for a derived artifact that must match the corpus exactly: it hands back files from a different corpus while reporting a cache miss.
- **Left `bible/semantic.py` alone for now.** While measuring, a third problem showed up: `search_semantic()` reloads and re-decodes the 98 MB index on *every* query (`struct.unpack` into 66,689 Python lists, ~1.8 s per query) and then scores every vector in pure Python (~2.7 s per query). `array.array('f', raw)` decodes the same bytes in 0.048 s — 31× faster, and `array` is stdlib, so ADR-001's stdlib-only constraint holds. That is a real scaling problem but it is a separate change from the CI fix, and it needs its own test coverage.

## Blocked

- Nothing for the gate itself. It has now run green twice on `main` — cold (`40216038726`) and warm (`40220328946`).
- The licence decision for the five non-redistributable editions is still Steven's and is untouched here. This session changed no data files.

## Next Steps

1. **Switch the gate to `--benchmark v2 --split dev`.** Benchmark v2 (90 queries, 56 cross-tradition citations, dev/held_out splits) is the one that actually matches the multi-tradition corpus. The 2026-10-08 notes already ask for exactly this. The cache now makes it affordable.
2. **Fix the per-query index reload in `bible/semantic.py`** — `array.array` for the decode plus an in-process cache so the index is decoded once per run rather than once per query. Worth ~1.6× on eval wall time with no new dependency. A numpy fast path (one matvec instead of a Python loop) would be ~22× but needs a stdlib fallback and is a bigger change.
3. **Re-baseline the thresholds once benchmark v2 is in place.** The v0.10.0 baselines (semantic 0.279, hybrid 0.258) were measured on a Bible-only index.

---

# 2026-10-25 (later) — Benchmark v2 dev gate

The v2 dev split is now the second CI gate. This is the "switch the gate to
`--benchmark v2 --split dev`" step that the 2026-10-08 notes asked for, and
the "run the qwen3 eval" item from the vault TODO board.

## The v2 dev baseline (measured, not estimated)

Command, against the 66,689-passage multi-tradition index:

```
python scripts/run_eval.py --paths bm25,semantic,hybrid --benchmark v2 --split dev
```

| Path | Recall@10 | MRR | Primary@1 | nDCG@10 | Queries/s |
|---|---|---|---|---|---|
| bm25 | **0.119** | 0.172 | 0.125 | 0.167 | 2.6 |
| semantic | **0.189** | 0.300 | 0.229 | 0.257 | 0.2 |
| hybrid | **0.183** | 0.291 | 0.208 | 0.241 | 0.2 |

**These are lower than the v1 numbers (0.108 / 0.282 / 0.273), and that is
correct** — v2 is a harder benchmark, not a worse system. Two independent
checks confirm the gap is real difficulty rather than a scoring artifact:

1. **Retrieval is proportionally multi-tradition.** The tradition mix of the
   retrieved top-10 across all 48 dev queries is 53.6% Christianity / 31.4%
   Tanakh / 15.0% Quran, against a corpus mix of 55.8% / 34.8% / 9.3%. The
   system is returning all three traditions in proportion — it is not
   defaulting to KJV.
2. **Recall is uniform across traditions.** Of the expected citations that
   belong to each tradition, the fraction retrieved is 19.8% (Christianity),
   19.2% (Tanakh), 13.3% (Quran). No tradition is being systematically
   starved.

The v2 benchmark demands more per query (229 expected citations over 48
queries, vs v1's 204 over 39) and expects hits across all three canons at
once, so each individual citation is harder to land in a top-10.

### Split integrity

- v2 dev = 48 queries, v2 held_out = 42 queries, **no query appears in
  both** (checked; pinned by `t_eval_gate_benchmark_v2_dev_held_out_are_disjoint`).
- Only **1** of the 39 v1 queries appears in v2 dev, so v2 dev is a fresh
  measurement with no back-door to the v1 numbers.
- v2 dev expects 45 Quran citations and 73 Tanakh citations — it genuinely
  exercises cross-tradition retrieval (pinned by
  `t_eval_gate_benchmark_v2_dev_has_cross_tradition_citations`).

## The gate thresholds

| Path | Baseline | Threshold | Margin |
|---|---|---|---|
| bm25 | 0.119 | 0.08 | -33% |
| semantic | 0.189 | 0.15 | -21% |
| hybrid | 0.183 | 0.14 | -23% |

The margins are deliberately wider than the v1 gate's (~10%), because v2's
numbers are lower, so the same absolute tolerance would be a much larger
relative tolerance here.

**The v2 thresholds are NOT the v1 thresholds.** Reusing v1's semantic 0.25
against a v2 baseline of 0.189 would fail on current code — verified: the
gate exits 1 on the real v2 report at the v1 thresholds.

**The harness is deterministic.** Repeated runs of the same command against
the same index return identical numbers (bm25 0.119 twice; semantic 0.150
twice on an 8-query subset). So the baseline is a fixed value, not a sample,
and a threshold below it is a real regression detector rather than a
coin flip.

## What changed in the workflow

1. **The gate logic moved out of the workflow into `scripts/eval_gate.py`.**
   It was an inline Python heredoc, which meant it could not be unit-tested.
   Now it is importable and covered by seven sister-script tests.
2. **Two gate steps instead of one.** The v1 gate (scoped to Christianity,
   unchanged thresholds) still runs, and the v2 dev gate runs alongside it.
   v1 is the long-history single-domain signal; v2 is the cross-tradition
   signal that matches the corpus. Neither replaces the other.
3. **The gate fails on a missing row.** `run_eval.py` skips a path whose
   artifact is missing and emits no summary row for it. The old inline gate
   treated "no row" as "nothing to check" and passed on the paths that did
   run. The new gate fails loudly — that was the "gate that skips its own
   inputs passes vacuously" failure mode.

## Tests added

Seven new sister-script tests (`147 → 154`):

- `t_eval_threshold_gate_parses_real_report` — rewritten to exercise the
  real `eval_gate.py` parsing code instead of a copy of the regex.
- `t_eval_gate_ignores_per_persona_rows` — the report has a per-persona
  table whose rows also start with a path name; the gate must read the
  aggregate.
- `t_eval_gate_missing_row_is_a_failure_not_a_pass`
- `t_eval_gate_exits_nonzero_on_regression` — end-to-end, proves the gate
  can fail.
- `t_eval_gate_fails_when_path_row_missing`
- `t_eval_gate_rejects_malformed_threshold`
- `t_eval_gate_benchmark_v2_dev_has_cross_tradition_citations`
- `t_eval_gate_benchmark_v2_dev_held_out_are_disjoint`
- `t_eval_gate_benchmark_v2_dev_baseline_is_stable` — reads the workflow
  and asserts every threshold it passes is strictly below the measured
  baseline, so nobody can "fix" a red gate by raising the threshold.

## Notes

- The measurement index used here is `data/embeddings/ci-timing_*` (gitignored, derived data) and can be deleted.
- The gate thresholds were left at their existing values so this commit changes CI plumbing only. Anyone reading the new numbers should know the semantic/hybrid baselines were measured on the old Bible-only corpus.
