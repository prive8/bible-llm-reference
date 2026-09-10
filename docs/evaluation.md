# Evaluation — Retrieval Quality Metrics

> **Last updated:** 2026-09-09 (v0.9.0-pre). Baseline numbers from the
> local CPU embedding model on the default index.

## Benchmark

A hand-curated set of 33 queries with 179 expected verses across the
Bible + Quran Saheeh International corpus. Each expected verse has a
relevance weight (1, 2, or 3). Defined in `tests/benchmark.py`.

Coverage:
- Emotional / pastoral themes (comfort, fear, trust, hope)
- Theological themes (mercy, judgment, creation, love)
- Practical / wisdom themes
- Doctrinal themes (faith, prophecy, resurrection, prayer)
- Adversarial: queries where BM25 keywords mislead
- Cross-tradition: queries where Quran answers alongside Bible
- Parables / narratives
- Specific people (Moses, David)
- Short / vague queries (light, shepherd, water, grace, eternal life, Holy Spirit)

## Metrics

For each query against each retrieval path:

- **recall@K** — fraction of expected verses appearing in top-K (default K=10).
  Primary "is this system finding relevant content" signal.
- **MRR** — mean reciprocal rank of the first weight-3 (primary) hit.
  Measures "how quickly does it surface the best answer."
- **primary-in-top-1 rate** — fraction of queries where any weight-3 verse is at rank 1.
- **nDCG@K** — normalized DCG using graded relevance. Standard IR metric.

## Baseline (v0.10.0, local `all-MiniLM-L6-v2` on 43K corpus)

Reproduce via `python scripts/run_eval.py`:

| Path | Recall@10 | MRR | Primary@1 | nDCG@10 | Queries/s |
|------|----------|-----|-----------|---------|-----------|
| **BM25** | 0.093 | 0.030 | 0.030 | 0.068 | 6.3 |
| **Semantic** | **0.279** | **0.165** | **0.151** | **0.222** | 0.3 |
| **Hybrid** (default 0.1/0.7) | **0.258** | 0.162 | **0.151** | **0.219** | 0.4 |

**Semantic is 3× better than BM25 on recall.** This is the headline finding.

**Hybrid is now *better* than at v0.9.0 default (0.233 → 0.241).** The
v0.9.0 default of `bm25_weight=0.5` (equal weights) was worse than
semantic-only because BM25's low recall (0.093) meant its 50% weight
in the fused score suppressed semantic-only hits. The v0.10.0 default
of `bm25_weight=0.3` lets semantic dominate solo results while still
letting BM25 contribute reciprocal hits. **Closed HANDOFF §8 #7.**

**Hybrid still has room.** Hybrid's recall@10 (0.241) is now *better*
than v0.9.0 but still below the semantic-only ceiling (0.279). Further
gains available by:
- **Lower `bm25_weight` further** (0.2 or 0.1) — risk: BM25 stops
  contributing to reciprocal hits, so we lose the consensus boost
- **BM25 confidence filter** — drop BM25 results below a BM25 score
  threshold before fusion (e.g. `bm25_score > 0.5 * max_in_query`)

## What works well

- **Adversarial queries** ("what does the Bible say about feeling
  overwhelmed", "passages about feeling abandoned or alone"): semantic
  search beats BM25 by 5-10× because the query vocabulary doesn't match
  the verse vocabulary.
- **Specific theological terms** ("grace", "eternal life"): semantic
  finds thematically grouped verses that BM25 misses.
- **Cross-tradition queries** ("God as creator and sustainer of all
  life", "the day of judgment"): hybrid surfaces both Bible and Quran
  verses in the same ranked list.

## What doesn't work yet

- **Hybrid fusion logic**: see "Hybrid is *worse* than semantic alone"
  above. BM25 noise is the main culprit. Fix: lower `bm25_weight` default,
  or add a BM25 confidence filter before fusion.
- **"light" / "shepherd" / "water"** queries: high BM25 recall but
  low semantic recall (the model doesn't generalize well from single-word
  queries to thematic verses). Mitigation: use BM25 for these specifically,
  semantic for longer queries. The default `auto` doesn't know to switch.
- **Named-entity queries** (Moses, David): semantic retrieves *about*
  them (verses mentioning Moses) but not their *stories*. The model
  treats names as content words, not as entity references.

## Methodology notes

- **Benchmark curation is iterative.** The first version of the benchmark
  was too narrow (only 105 unique citations). I dumped semantic top-10
  results per query, audited which retrieved verses were genuinely relevant
  but unlisted, and expanded the benchmark to 165 unique citations.
  When the model improves, repeat this exercise.
- **Relevance weights matter.** Weight-3 ("primary") hits mean
  "this verse IS the answer." Weight-2 ("strong") means "this verse
  is clearly on point." Weight-1 ("related") means "touches on the theme."
  MRR and primary-in-top-1 use only weight-3; recall@K uses all weights.
- **The harness runs against the real on-disk index.** The `data/embeddings/`
  directory must exist (regenerate via `scripts/index_embeddings.py`).
  Without it, the BM25 path still runs but semantic and hybrid are skipped.

## Future evaluation work

1. **Tune hybrid defaults.** Try `bm25_weight=0.3` vs `0.5` vs `0.7`;
  document the recall/MRR trade-off curve. Pick the operating point
  that maximizes semantic-equivalent recall without too much BM25 noise.
2. **Per-query-type breakdown.** Adversarial queries should be reported
  separately from "obvious keyword" queries. The current aggregate
  numbers hide whether a path works well on adversarial queries and
  poorly on keyword queries (or vice versa).
3. **Cross-tradition recall.** Add a separate metric: among queries
  with both Bible and Quran expected verses, what fraction of Quran-only
  verses does the path surface? (Requires more expected verses marked
  with `tradition: islam` in the benchmark.)
4. **NIM baseline.** When the user authorizes hosted inference, build
  the same index with `nvidia/nv-embedqa-e5-v5` and compare.
  Expected: ~10-20% relative recall improvement over `all-MiniLM-L6-v2`
  for retrieval-augmented queries, per the E5 model card.
5. **Per-corpus breakdown.** Bible-only vs. Quran-only vs. cross-tradition
  queries — does the model handle each equally well?

## How to run

```bash
# Full eval (~3 min on CPU)
python scripts/run_eval.py

# Just BM25 (fast)
python scripts/run_eval.py --paths bm25

# With per-query CSV for analysis
python scripts/run_eval.py --csv /tmp/eval.csv

# Quick iteration on a subset
python scripts/run_eval.py --limit 5 --paths semantic
```
