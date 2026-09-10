# 2026-09-09 — Real local vector index + M3C hybrid fusion (v0.8.0)

## Done

- **Generated the first real semantic vector index** of the Bible + Quran corpus
  using `sentence-transformers/all-MiniLM-L6-v2` (CPU, local, $0):
  - 43,483 passages total (37,247 KJV Bible + 6,236 Quran Saheeh International)
  - 384 dimensions
  - Generated in 198.6 seconds (~219 vec/s on CPU)
  - Output: `data/embeddings/default_meta.json` (12 MB) +
    `data/embeddings/default_vectors.bin` (67 MB)
- **Milestone 3C: hybrid BM25 + semantic fusion shipped.** New module
  `bible/hybrid.py` with:
  - `hybrid_search(query, bm25_results, semantic_results, bm25_weight,
    solo_weight, top_k)` — citation-keyed join with per-source min-max
    normalization.
  - `run_hybrid()` — high-level runner with human-readable + JSON output.
  - CLI: `python -m bible hybrid "comfort in grief" [--bm25-weight 0.5]
    [--solo-weight 0.7] [--top-k 10] [--json] [--translation KJV]`
  - Wired into `bible/__main__.py` dispatcher.
- **Real semantic queries verified end-to-end** on natural-language prompts:
  - "comfort in times of grief" → Matthew 5:4 #1 ("Blessed are they that
    mourn: for they shall be comforted") + Sirach 7:34, Psalms 31:10, etc.
  - "mercy and compassion" → Matthew 5:7 #2 + Quran 31:3 ("guidance and
    mercy") at #3 — cross-tradition fusion working.
  - "forgiveness of enemies" → mixes Christianity (Sirach 25:14) and
    Islam (Quran 22:50, 7:153, 11:11) in the same ranked list.
  - "trust in God during hardship" → Proverbs 3:5 ("Trust in the LORD
    with all thine heart"), Psalms 62:8, Psalms 71:5.
  - "creation of the world" → Quran 55:3, 40:57, 56:59 lead (Quran is
    dense on creation).
- **13 new sister-script tests**, suite now at **75 passed, 0 failed**:
  - 12 for hybrid fusion (normalization, reciprocal vs solo, extreme
    weights, empty inputs, defaults, CLI dispatcher)
  - 1 conditional test for the real on-disk index
    (`t_semantic_real_index_loads_and_returns_results`) — skips when
    the index files don't exist (CI path), runs full check when they do
- **Decided to gitignore the index** (not commit 67 MB). Pattern: raw
  source committed, derived data gitignored (same as ADR-003 Strong's).
  Added `.gitignore` rules for `data/embeddings/*.bin` and
  `data/embeddings/*.json`. Added `data/embeddings/README.md` to
  document the directory and the regen procedure.
- **Docs refreshed:**
  - CHANGELOG v0.8.0
  - HANDOFF §5 M3C marked ✅ (was "defer to Phase 3.5") + test count 62→75
  - ADR-011 — hybrid fusion design
  - pyproject.toml 0.7.0 → 0.8.0
  - README quickstart: hybrid example + 75 tests

## Blocked

- Nothing. M3B + M3C are both fully landed.

## Decisions made

- **Gitignore the vector index** (not commit 67 MB). The index is
  derived data; per ADR-003-style discipline, raw is committed and
  derived is regenerated. Anyone cloning the repo runs `pip install -e
  ".[embeddings]" && python scripts/index_embeddings.py --backend local`
  once to get the index (~3 min on CPU).
- **Hybrid defaults: `bm25_weight=0.5`, `solo_weight=0.7`.** Equal
  weight is a safe default (callers can override); 0.7 solo weight means
  reciprocal hits naturally rank above solos but solos still compete.
- **Cross-tradition by default.** Hybrid queries don't filter by
  tradition; they surface both Bible and Quran results. `--tradition`
  filter is added if the user wants to constrain.
- **Default model = `nvidia/nv-embedqa-e5-v5` for NIM, `all-MiniLM-L6-v2`
  for local.** Two different embeddings means two different index files
  — local index is named `default` (384-dim); a future NIM index
  would be `nim` (1024-dim). The system doesn't try to merge across
  model spaces (which is fundamentally a bad idea anyway).

## Verification

```
$ python3 tests/run_all.py
  ... 75 ✓ ...
  75 passed, 0 failed (of 75)

$ python -m bible hybrid "comfort in grief" --top-k 3
  1. [CHRISTIANITY] Matthew 5:4 (combined: 0.732, source: both)
     "Blessed are they that mourn: for they shall be comforted."
  2. [CHRISTIANITY] Sirach 7:34 (combined: 0.624, source: bm25)
     "Fail not to be with them that weep, and mourn with them that mourn."
  3. [CHRISTIANITY] Psalms 31:10 (combined: 0.591, source: bm25)
     "For my life is spent with grief, and my years with sighing..."

$ python -m bible semantic "trust in God during hardship" --top-k 3
  1. [CHRISTIANITY] Psalms 62:8 (Similarity: 66.2%)
     "Trust in him at all times; ye people, pour out your heart before him: God is a refuge for us. Selah."
  2. [CHRISTIANITY] Sirach 1:28 (Similarity: 58.5%)
     "Distrust not the fear of the Lord when thou art poor: and come not unto him with a double heart."
  3. [CHRISTIANITY] Proverbs 3:5 (Similarity: 57.8%)
     "Trust in the LORD with all thine heart; and lean not unto thine own understanding."
```

## Commit shape

- `feat(hybrid): BM25 + semantic fusion engine (M3C, ADR-011)`
- `test(hybrid): 12 fusion tests + 1 real-index integration test (suite 75)`
- `chore: bump to v0.8.0 — gitignore derived index, ADR-011 docs, hybrid CLI`
