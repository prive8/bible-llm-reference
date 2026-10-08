# 2026-10-08 — Foundation F0–F4, Benchmark V2, and Passage Chunking

## Done

1. **Step 0 — F0a verification and regression test.**
   - Confirmed `scripts/index_embeddings.py` defaults Judaism slice to English (`jps1917-modernized`).
   - Added unit test `t_index_embeddings_judaism_defaults_to_english` in `tests/run_all.py` validating that collected passages contain English characters and the `--judaism-edition` flag correctly routes between JPS English and Hebrew.

2. **Step 1 — Licence-as-data catalog (`data/editions.json`).**
   - Transformed the narrative findings of `LICENCE-AUDIT.md` into a structured, machine-readable catalog of 25 scriptural editions across Christian Bible, Quran, Tanakh, Strong's, and cross-references.
   - Captured explicit metadata per edition: `id`, `tradition`, `name`, `language`, `year`, `license`, `source`, `path`, `redistributable` (bool), `commercial_ok` (bool), and `notes`.
   - Identified and flagged redistributable vs. local-only editions (e.g. RSV, RV1960, Saheeh International marked `redistributable: false`).

3. **Step 2 — Foundation F1–F4 (Unified Passage Model, TraditionRegistry, Canonical IDs, Versification Alignment).**
   - Created `data/versification_map.json`: documented canonical book name mappings (e.g. `1 Samuel` ↔ `Samuel I`) and chapter/verse alignment offsets between Christian versification and the Masoretic Text (Malachi 3:19–24 ↔ Malachi 4:1–6, Joel 3:1–5 ↔ Joel 2:28–32, etc.).
   - Created `bible/registry.py`:
     - Unified `Passage` dataclass (`tradition`, `canonical_id`, `citation`, `text`, `edition_id`, `language`, `translation_name`, `strongs_tags`).
     - Canonical ID constructor `make_canonical_id` and parser `parse_canonical_id` (e.g. `bible:Matthew.5.4`, `quran:2.255`, `tanakh:Genesis.1.1`).
     - `TraditionRegistry`: central catalog loading `data/editions.json` and `data/versification_map.json`, providing `get_edition`, `list_editions`, `align_canonical_id`, `parse_reference`, and cross-tradition `get_passages`.
   - Routed core commands:
     - `bible/search.py`: BM25 index and search accept `tradition` (`all`, `islam`, `judaism`, `christianity`). Added `--tradition` to CLI.
     - `bible/parallel.py`: accepts `--tradition`, parses cross-tradition references and canonical IDs, and queries all matching editions across traditions.

4. **Step 3 — Eval Benchmark V2 & Range/Passage Scoring.**
   - Researched and authored `tests/benchmark_v2.py`: 90 curated queries with 15 queries each for all 6 canonical personas (Sarah, Marcus, Yuki, Priya, Aisha, Jordan), partitioned into `dev` (48 queries) and `held_out` (42 queries) splits, with graded relevance weights (3/2/1) and cross-tradition expected citations.
   - Updated `scripts/run_eval.py`:
     - Added `--benchmark {v1,v2}`, `--split {all,dev,held_out}`, and `--tradition`.
     - Implemented `citation_matches`: supports range matching (e.g. `2 Corinthians 1:3-4` matched by `2 Corinthians 1:3`), multi-verse chunk containment (e.g. `Matthew 5:4` matched by chunk `Matthew 5:3-5`), parenthetical Quran titles (`Quran 70 (Al-Ma'arij) 70:19`), and cross-tradition versification alignment (`Malachi 4:1` matched by `tanakh:Malachi.3.19`).
     - Updated `_metrics_for_query` to compute range-aware `recall@k`, `mrr`, `primary_in_top1`, and graded `ndcg@k`.

5. **Step 4 — Passage Chunking & Constituent Verse Resolution.**
   - Updated `scripts/index_embeddings.py`:
     - Added `_chunk_verses` sliding-window helper.
     - Added `--chunk-size` (default 1) and `--chunk-step` (default: `max(1, chunk_size - 1)` for overlapping windows).
     - Windows respect chapter boundaries across Bible, Quran surahs, and Tanakh/Torah divisions.
   - Updated `bible/semantic.py`:
     - `search_semantic` attaches `constituent_verses` to results when querying a chunked index.
     - Added `expand_passage_chunks` and `resolve_verses=True` parameter to unpack multi-verse passage hits into constituent verse citations with inherited scores.
     - Added `--resolve-verses` flag to semantic CLI.

6. **Test Suite Verification.**
   - Added 9 new unit tests to `tests/run_all.py` covering registry, canonical IDs, versification alignments, multi-tradition parallel, BM25 search across traditions, benchmark V2 structure, citation matching, passage chunking, and verse resolution.
   - Verified that all 147 sister-script tests pass (0 failures).

## Decisions

- **Range / Chunk Matching Semantics:** In retrieval evaluation, an exact string match is an ideal case, but passage retrieval retrieves windows. `citation_matches` treats an expected range as satisfied if the retrieved verse intersects the range (`max(r_s, e_s) <= min(r_e, e_e)`), and vice versa for chunk retrievals.
- **Cross-Tradition Versification Mapping in Scoring:** When querying cross-tradition concepts (e.g. comparing Malachi in Christian vs Jewish Bibles), `citation_matches` leverages `TraditionRegistry.align_canonical_id` so that MT verse numbering matches Christian numbering.
- **Passage Chunking Windowing:** Windows default to single verses for full backwards-compatibility. When `--chunk-size > 1`, windows slide within chapter boundaries rather than straddling book/chapter boundaries, ensuring coherent pericope units.

## Next Steps

- Rebuild production embeddings on host with chunking enabled (e.g., `--chunk-size 3 --chunk-step 2`) using `sentence-transformers` or OpenRouter.
- Run `python scripts/run_eval.py --benchmark v2 --split dev` against neural index to establish baseline retrieval scores across all 6 personas.
