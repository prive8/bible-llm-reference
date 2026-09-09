# Evaluation — Measuring Retrieval Quality

> **Status:** Shell document. Define the metrics when Milestone 3 (semantic
> search) lands; the reference-only path (Milestones 1–2) doesn't need
> numeric scoring, just correctness assertions.
>
> **Last updated:** 2026-09-09

---

## 1. What we're evaluating

The bible-llm-reference project is a **retrieval substrate**, not a generative model. So evaluation is about:

- **Exact-reference recall** — does `lookup("John 3:16")` return exactly John 3:16?
- **Translation coverage** — does `parallel("Genesis 1:1")` return all 13 (or 14, with KJV) translations?
- **Strong's linkage** — does a Strong's number on a KJV verse resolve to the correct lexicon entry?
- **Keyword search relevance** (Milestone 3+) — does `search("faith without works")` put James 2:14–26 at the top?
- **Semantic search relevance** (Milestone 3+) — does `embed("verses about forgiveness")` return Matthew 6:14–15, Ephesians 4:32, etc.?

## 2. What we explicitly do NOT evaluate

- **Generative quality.** This project does not generate text in Phase 1. Phase 2 evaluation (when it lands) lives in a separate doc.
- **Theological accuracy.** The system reports what the texts say; it does not adjudicate doctrine.
- **Translation "correctness."** Each translation is what its source says it is; we don't rank translations against each other.

## 3. Reference-path metrics (Milestone 1–2, current)

These are pass/fail, not scored. Implemented in `tests/run_all.py`:

| Metric                      | Test                                         | Pass criterion |
|-----------------------------|----------------------------------------------|----------------|
| Reference parser correctness | `t_parse_*` (8 tests)                        | All known reference forms parse to canonical (book, ch, vs, ve) |
| Translation coverage        | `t_list_translations_count`, `t_required_*`  | All 13 expected translations present |
| Parallel lookup             | `t_parallel_*` (2 tests)                     | Genesis 1:1 returns ≥13 rows; John 3:16 includes KJV + Strong's |
| Strong's linkage            | `t_strongs_hebrew_h1254`, `t_strongs_greek_g25` | Known numbers resolve to non-empty entries |
| Legacy-script regression    | `t_legacy_bible_query_does_not_inline_strongs_into_text` | English text is clean, Strong's refs are on separate lines |

**Running:** `python3 tests/run_all.py` — should print `N passed, 0 failed` and exit 0.

## 4. Keyword search metrics (Milestone 3A, shipped)

BM25 Okapi search engine (`bible/search.py`, ADR-007) is evaluated in `tests/run_all.py`:

| Metric | Test | Pass criterion |
|--------|------|----------------|
| Phrase relevance / Top-1 accuracy | `t_search_faith_without_works` | Top-1 result is James 2:20 or James 2:26 |
| No-false-positive baseline | `t_search_no_results` | Nonsense tokens return 0 results |
| Multi-translation support | `t_search_translation_web` | Querying WEB surfaces Genesis 1:3 in top 3 |
| Pipeline serialization | `t_search_cli_json` | JSON output parses with `reference`, `text`, `score` |
| Ancient language diacritic handling | `t_search_multilingual_wlca_hebrew` | Unpointed Hebrew `ברא` surfaces Genesis 1:1/1:27 in WLCa |

- **Top-1 accuracy:** Evaluated on reference phrases. Target: ≥80%.
- **Phrase boost:** Exact phrase occurrence receives scoring priority over scattered occurrences.
- **Multi-tradition & multilingual readiness:** Diacritic-insensitive Unicode tokenization handles unpointed Hebrew, Greek accents, and non-ASCII scripts.

## 5. Semantic search metrics (Milestone 3+, draft)

When embeddings ship, define:

- **Recall@10:** For 50 (natural-language question, relevant-verse-list) pairs, what fraction of the relevant verses appear in the top 10 nearest neighbors? Target: ≥70%.
- **Cross-tradition sanity:** For multi-tradition corpora (Phase 3+), a query like "verses about mercy" should surface Christian (Matthew 5:7, Psalm 103:8), Quran (2:64, 2:218), and rabbinic parallels when those corpora are present. This is a Phase 3 evaluation problem.

## 6. Human-in-the-loop evaluation

For all of the above, **a small set of hand-curated reference queries** is the most reliable signal. The HANDOFF.md daily cadence (notes/YYYY-MM-DD.md) should include one "evaluation query of the day" with expected output, and the test suite should grow as those queries accumulate.

---

## Pending definitions (to write when the milestone lands)

- [ ] Top-1 accuracy for BM25 (50 queries, hand-curated)
- [ ] Recall@10 for embeddings (50 queries, hand-curated)
- [ ] Cross-reference engine: percentage of TSKe cross-references the engine resolves correctly
- [ ] Phase 2: citation-groundedness rate (every generated claim carries a citation?)
