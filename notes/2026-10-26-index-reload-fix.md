# Index reload fix — 2026-10-26

## The problem

`bible/semantic.py`'s `search_semantic()` called `load_vector_index()` on
**every query**. That function re-read the whole `.bin` file and decoded it
with `struct.unpack` into 66,689 nested Python lists — ~1.3 s per query for
the 66,689-passage corpus.

The index is derived data. It is written once by a build and then read many
times. Re-decoding it per query was pure waste, and it was the dominant cost
of a CI eval.

A second, smaller waste sat inside the scoring loop: `cosine_similarity()`
recomputed the L2 norm of the query **and of every candidate vector** on
every call — 66,689 × 2 norms per query, ~1.1 s.

## What changed

1. **The index is decoded once per process and cached.**
   `load_vector_index_cached()` keeps the decoded result in a module-level
   dict keyed by `(resolved dir, name)`. `load_vector_index()` remains as
   the compatibility wrapper returning the original nested
   `(entries, list[list[float]], dim)` shape, so nothing downstream breaks.

2. **Decoding uses `array('f')`, not `struct.unpack`.**
   A flat `array('f')` of `count * dim` float32s decodes in ~0.07 s versus
   ~1.3 s, and avoids allocating 66,689 separate list objects.

3. **Candidate norms are precomputed at load, not per query.**
   `cosine_similarity` needs each candidate's norm. Computing all 66,689
   norms once at load costs ~0.7 s and is amortized over every subsequent
   query. The score stays an **exact cosine similarity** — the fast path
   divides by the precomputed norm rather than assuming the stored vectors
   are unit length.

4. **`sum(map(mul, ...))` instead of a generator expression** in the dot
   product — measurably faster over 66,689 candidates.

5. **`clear_vector_index_cache()`** is the invalidation hook. A process that
   writes a new index and then searches it must call it, otherwise the cache
   serves the pre-build copy.

All of this is stdlib (`array`, `operator`, `math`) — ADR-001 still holds,
`bible/` still imports nothing outside the standard library.

## Measured

Same host, same index, same benchmark, old code vs new code:

| Benchmark | Before | After | Speedup |
|---|---|---|---|
| v2 dev (48 queries, 3 paths) | 8m09s | **1m55s** | **4.3×** |
| v1 scoped (all queries, 3 paths) | 5m44s | **56s** | **6.2×** |

Per-query cost, measured directly on the 66,689 × 384 index:

| Representation | Decode | Score | Per-query |
|---|---|---|---|
| `struct.unpack` → nested lists (old) | 1.334 s | 1.076 s | 2.41 s |
| flat `array('f')` + precomputed norms (new) | 0.000 s | 0.627 s | **0.63 s** |

The decode is 20× faster with `array('f')`, but the **score loop was the
floor**, not the decode — that was the finding that changed the design. A
cached decode alone would have left ~1.1 s/query on the table.

## Results are unchanged

Scores are **bit-identical**, not merely close:

- v1 scoped: bm25 `0.108`, semantic `0.282`, hybrid `0.273` — unchanged.
- v2 dev: bm25 `0.119`, semantic `0.189`, hybrid `0.183` — unchanged.
- Max score delta between old and new implementations across 8 queries
  across the real 66,689-entry index: **0.000e+00** (exact equality).
- Ordering identical on every query.
- Both CI gates pass on the new reports.

A separate benchmark showed the pure dot-product shortcut (relying on the
vectors being pre-normalized) scores `1.517e-10` away from full cosine —
float32 rounding. The shipped code divides by precomputed norms instead, so
it does not depend on that assumption at all.

## Why it was not done earlier

Three plausible approaches were measured and rejected:

- **NumPy** — 22× faster scoring, max score difference `8e-08`. Rejected:
  ADR-001 makes `bible/` stdlib-only. (NumPy is already an `embeddings`
  extra and is installed in the CI eval job, so an optional fast path is
  legitimate if it is ever worth the complexity.)
- **Pure dot product** — fastest, but silently wrong if an index is ever
  written unnormalized. `save_vector_index()` does *not* normalize; the
  *indexer* does, before calling it. Precomputed norms get the same speed
  without the assumption.
- **`memoryview` zero-copy** — decode is free, but the score loop is
  unchanged at ~1.2 s. No benefit over `array('f')` here.

## Tests

Seven new sister-script tests (155 → 162), all passing:

- `t_semantic_index_cache_returns_same_data_as_uncached` — the cached and
  uncached loaders return identical data, and the compatibility wrapper
  still produces the original nested shape.
- `t_semantic_index_cache_can_be_cleared` — a rebuilt index is visible
  after `clear_vector_index_cache()`, and the stale copy is served before
  the clear. This is the test that would catch a missing invalidation hook.
- `t_semantic_index_cache_missing_index_is_none` — a missing index loads as
  `None` and does not poison the cache when the file appears later.
- `t_semantic_index_truncated_file_is_truncated_not_wrong` — a `.bin`
  shorter than `count*dim` yields a truncated index, not a wrong-shaped one.
- `t_semantic_stored_vectors_are_normalized` — pins the indexer's
  normalization behavior and checks the precomputed norms match.
- `t_semantic_precomputed_norms_match_cosine_for_unnormalized_vectors` —
  the fast path is an exact cosine similarity for vectors that are
  *deliberately not* normalized. This is the test that fails if someone
  swaps the precomputed-norm division for a bare dot product.
- `t_semantic_dot_product_shortcut_matches_cosine` — dot product equals
  cosine for unit vectors.

## CI impact

The `eval-regression` job on a cache hit was ~17 min before this change
(5m12s v1 + 8m57s v2 locally, measured on the 2-vCPU runner). With the
per-query decode gone, both gates should drop to a few minutes. The job's
`timeout-minutes: 60` is unchanged — this fix buys headroom, it does not
depend on it.

## Files

- `bible/semantic.py` — cached loader, flat `array('f')` decode,
  precomputed norms, fast scoring loop, `_search_with_vector_lists()` for
  the caller-supplied `custom_index` path.
- `tests/run_all.py` — seven new tests.
- `README.md` — test count 155 → 162.
- `.github/workflows/ci.yml` — step name no longer cites a stale test count.
