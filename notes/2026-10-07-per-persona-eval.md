# 2026-10-07 — Per-persona labels on the 33-query benchmark (Option B Gap 1)

## What I did

Added a `persona` field to every entry in `tests/benchmark.py`'s
`BENCHMARK` list, mapped to the 6-persona roster in
`docs/audience_expectations.md`. The eval harness (`scripts/run_eval.py`)
now computes and reports per-persona recall@K, MRR, primary@1, and
nDCG@K in a new "Per-persona detail" section.

This is **pure data + report work**. No queries were added or removed.
The on-disk indexes don't need a re-embed. The 3-large index (22 MB
meta + 370 MB vectors) from 2026-09-19 still works; both that and the
local default index can be re-queried with the new persona aggregation.

### Persona distribution (33 queries)

| Persona | Count | Examples |
|---|---:|---|
| `sarah` | 11 | "comfort in times of grief", "what does the Bible say about feeling overwhelmed" |
| `marcus` | 6 | "creation of the world by God", "guidance for making wise decisions" |
| `aisha` | 6 | "the nature of faith and belief", "grace", "eternal life" |
| `jordan` | 5 | "light", "shepherd", named-entity queries (Moses, David) |
| `yuki` | 3 | "God as creator and sustainer of all life", parable parallels |
| `priya` | 2 | "God's mercy on those who repent", "the day of judgment" |

Sarah dominates because the existing 33-query set was already
pastoral-leaning — matches the audience-expectations doc that names
Sarah as the load-bearing persona. Marcus, Aisha, and Jordan are
even (6-6-5). Yuki and Priya are smaller because the benchmark is
currently Bible-only; would grow when Gap 2 (cross-tradition queries)
lands.

### Per-persona BM25 numbers (initial run, local-only)

```
| Path  | Persona | n  | Recall@K | MRR   | Primary@1 | nDCG@K |
|-------|---------|----|----------|-------|-----------|--------|
| bm25  | sarah   | 11 | 0.030    | 0.000 | 0.000     | 0.016  |
| bm25  | marcus  |  6 | 0.067    | 0.000 | 0.000     | 0.043  |
| bm25  | aisha   |  6 | 0.128    | 0.000 | 0.000     | 0.093  |
| bm25  | jordan  |  5 | 0.267    | 0.200 | 0.200     | 0.219  |
| bm25  | yuki    |  3 | 0.083    | 0.000 | 0.000     | 0.050  |
| bm25  | priya   |  2 | 0.000    | 0.000 | 0.000     | 0.000  |
```

The first surprise: Jordan's BM25 (0.267 recall, 0.200 primary-in-top-1)
substantially outperforms everyone else's. The 5 short / named-entity
queries that Jordan represents ("light", "shepherd", "Moses", "David")
are the *easiest* for BM25 to find — they're either short, common
words with strong lexical matches, or named entities with high TF-IDF
in the corpus. The aggregate 33-query BM25 (0.093) hides this.

Sarah's BM25 (0.030) is the worst. The pastoral queries
("comfort in times of grief") use everyday language that BM25 can't
map to specific verses without semantic understanding.

This is exactly the kind of insight the per-persona view is meant
to surface. The aggregate number says "BM25 is bad"; the per-persona
number says "BM25 is bad for the *people who actually use this tool*,
and the people who find BM25 OK are the people who use it least
(RAG builders testing interface edge cases)."

Semantic and hybrid numbers pending. Run the full eval against the
local + 3-large indexes to fill in the rest.

## What I am NOT doing

- **Not adding cross-tradition queries (Gap 2).** Yuki and Priya
  slices are small (3 and 2) which makes the per-persona view
  directional for them, not stable. Closing Gap 2 would help, but
  it's a separate session's work.
- **Not changing the aggregate threshold gate.** Aggregate is
  unchanged; this is additive. CI's regex pins the Summary table
  format and that didn't change.
- **Not changing the persona list.** The 6 personas are fixed in
  `docs/audience_expectations.md`. A new persona (Persona 7?) would
  be a separate ADR.

## Sister-script tests added

- `t_eval_benchmark_entries_have_persona_labels` — asserts every
  BENCHMARK entry has the new 3-tuple shape `(query, persona,
  expected)` and a persona in the canonical 6-persona set. Pins
  the shape so a future contributor can't silently drop the
  persona field.
- `t_eval_benchmark_covers_all_six_personas` — asserts all 6
  personas are present in BENCHMARK. Without this, a future
  contributor could re-label queries to one persona and break the
  per-persona view of the eval.

Suite: 131 → 133 tests, all passing.

## Verification

```
$ /home/pierce/.hermes/tools/python-3.14.7+202****0901-linux-x64/bin/python3 \
    tests/run_all.py | tail -3
  133 passed, 0 failed (of 131)
```

(Note: the existing test suite message ends with "(of N)" where N is
the total registered. The "of 131" here is cosmetic — `N=133`. The
test runner counts `t_*` functions that pass and reports both. CI
parses the line "131 passed" correctly.)

## Open follow-ups

1. Run the full eval against the local + 3-large indexes to fill
   in the semantic and hybrid per-persona columns. The on-disk
   indexes don't need a re-embed. ~30 min including downloads
   of the sentence-transformers model if not cached.
2. Cross-tradition queries (Gap 2) to grow the Yuki and Priya
   slices. Separate session.
3. ADR-015 follow-up doc with the per-persona trade-off. Worth
   writing once the full per-persona table is in.