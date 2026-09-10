# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the Python package (per `pyproject.toml`).

## [Unreleased]

## [0.11.0] — 2026-09-10

### Added
- **Phase 3.2 — Torah (Five Books of Moses) adapter.** New `bible/torah.py`
  module with the same surface as `bible/quran.py`: `parse_torah_ref`,
  `list_torah_translations`, `load_torah_edition`, `get_torah_verses_scoped`,
  `run_torah`. Supports canonical names (`Genesis 1:1`), short Latin aliases
  (`Gen 1:1`), transliterations (`Bereshit 1:1`), and Hebrew-with-nikkud
  (`בְּרֵאשִׁית 1:1`). Ranges accept hyphen / en-dash / em-dash. CLI:
  `python -m bible torah "Genesis 1:1"`.
- **`scripts/ingest_torah.py`** — pulls Modernized JPS 1917 (English, CC-BY)
  and תנ״ך עם ניקוד (Hebrew, Public Domain) from the Sefaria API, with
  polite 1.05s delay between requests (Sefaria robots.txt asks for ≤ 1 req/sec),
  3× exponential-backoff retry, and HTML-markup stripping (footnote markers,
  `<big>`/`<small>`/`<span>` cantillation, NBSP/THINSP, paragraph markers).
- **9 Torah sister-script tests** (`t_torah_resolve_book_aliases`,
  `t_torah_parse_canonical_ref`, `t_torah_parse_alias_and_hebrew`,
  `t_torah_parse_range`, `t_torah_parse_garbage_returns_none`,
  `t_torah_data_files_present`, `t_torah_verses_chapter_scoped`,
  `t_torah_cli_json`, `t_torah_cli_hebrew_alias`). Test suite now **94 tests**.
- **`docs/phase3-scope-torah.md`** — scope doc covering source selection
  rationale, license attribution, acceptance criteria, and out-of-scope
  items (full Tanakh, Targum, Talmud are Phase 3.3+).

### Fixed
- **Semantic search tradition filter was a silent substring bug.**
  v0.8.0–v0.10.0 used `if filter_tradition not in entry_trad`, which
  silently returned 0 results for `--tradition bible` (because stored
  entries use `tradition="christianity"`, not `"bible"`). Replaced with
  an explicit alias map (`bible → christianity`, `muslim → islam`,
  `jewish → judaism`) and exact-match comparison. The CLI is unchanged
  (`--tradition bible` still works), but now actually returns results.
  Regression test: `t_semantic_tradition_filter_aliases`.
- **Semantic search `--tradition all` returned 0 entries** — the substring
  filter matched `"all"` against entries' tradition field (never equal),
  skipping everything. Fixed by explicitly treating `all` (and `None`)
  as "no filter". Same regression test covers both cases.

### Changed
- `bible/semantic.py` `--tradition` choices expanded from
  `all|bible|islam` to `all|bible|islam|judaism`.
- `bible/__main__.py`: `bible torah` command wired; `--bm25-weight`
  default-doc fixed (0.5 → 0.1) per HANDOFF §8 #7.

## [0.10.0] — 2026-09-10

### Added
- **`RUNTIME_CONTRACT.md`** — extracted from `HANDOFF.md` §11. Five
  rules binding any agent that consumes this dataset (cite + translation,
  Strong's lemma + gloss, no invented verses, internal diversity, no
  Scripture impersonation). Includes an "Evolution" section for proposing
  contract changes. Consumers no longer have to scroll past project
  archaeology to find the rules they must follow.
- **CI `eval-regression` job** in `.github/workflows/ci.yml`. Runs only on
  push to main (not on PRs). Builds the local semantic index, runs
  `scripts/run_eval.py`, and gates CI on recall@10 thresholds:
  bm25 ≥ 0.06, semantic ≥ 0.25, hybrid ≥ 0.22. Catches future
  regressions before they ship. Model + index are cached between runs.
- 1 sister-script test (`t_eval_threshold_gate_parses_real_report`)
  that locks the CI regex against harness output format drift.

### Changed
- **`DEFAULT_BM25_WEIGHT` lowered from 0.5 → 0.1** (the v0.10.0 hybrid-fusion
  tuning sweep). Sweep results on the local `all-MiniLM-L6-v2`:
  - bm25_weight=0.0 → hybrid recall 0.268 (pure semantic ceiling)
  - **bm25_weight=0.1 → hybrid recall 0.258** (chosen default)
  - bm25_weight=0.2 → hybrid recall 0.241
  - bm25_weight=0.3 → hybrid recall 0.241
  - bm25_weight=0.5 → hybrid recall 0.233 (v0.9.0 default; closed HANDOFF §8 #7)
  - **Closed HANDOFF §8 #7** ("hybrid fusion defaults deferred from v0.8.0")
  - Tuned default pinned by `t_hybrid_default_weights` so future regressions are loud
  - CI `eval-regression` threshold updated to 0.22 to match the new baseline
- README "How good is the search?" table now shows v0.10.0 numbers
  (hybrid 0.258 at the new 0.1 default), with the unchanged
  methodological caveat about benchmark expansion vs. model improvement.
- `docs/evaluation.md` baseline section updated to v0.10.0 numbers +
  full tuning rationale documented inline.
- HANDOFF §8 #7 marked RESOLVED with the full tuning rationale and
  pointer to `bible/hybrid.py` for the tuning history comment.

## [0.9.0] — 2026-09-09

### Added
- **`scripts/run_eval.py` — retrieval evaluation harness.** Runs the
  hand-curated benchmark against BM25, semantic, and hybrid retrieval
  paths; reports recall@10, MRR, primary-in-top-1, and nDCG@10.
  Outputs a markdown report. Supports `--paths`, `--top-k`, `--csv`
  for per-query analysis.
- **`tests/benchmark.py` — 33-query retrieval benchmark.** 179 expected
  verses across Bible + Quran Saheeh with graded relevance weights
  (1=related, 2=strong, 3=primary). Covers emotional / theological /
  doctrinal / adversarial / cross-tradition themes.
- **`docs/evaluation.md` — real numbers + baseline + future work.**
  Documents the v0.9.0-pre baseline (Semantic 3× better than BM25 on
  recall@10), identifies that hybrid is currently *worse* than
  semantic alone due to BM25 noise, and lists 5 follow-on evaluation
  tasks.
- **Process-local embedder caching.** `get_embedder("local")` now caches
  the `LocalSentenceTransformerEmbedder` instance per process — first
  call pays the model-load cost (~3s on warm disk), subsequent calls
  are free. Reduces the eval harness's 33-query semantic run from
  ~5min to ~100s.
- 8 sister-script tests for the harness's pure-logic functions (DCG,
  nDCG, per-query metrics). Suite now at **83 passed, 0 failed**.
- **CI badge** in README header.

### Found (and documented) — important

- **Hybrid fusion is currently *worse* than semantic-only** at the
  default 50/50 weight. BM25's recall is so low (0.093) that its
  noise gets 50% of the weight in the hybrid score, suppressing
  semantic-only hits. Documented as decision #7 in HANDOFF §8.

### Changed
- `get_embedder("local")` is now process-local cached; first call is
  slow, subsequent calls are O(microseconds).
- HANDOFF §8 — added explicit "Revisit when" guidance for each
  pending decision; resolved items #3 (README refresh) and #6
  (bible-query.py removal) explicitly closed.
- README — added CI badge + retrieval evaluation quickstart lines.

## [0.8.0] — 2026-09-09

### Added
- **First real semantic vector index of the Bible + Quran corpus.**
  43,483 passages embedded locally with `sentence-transformers/all-MiniLM-L6-v2`
  (384-dim, CPU). Index files committed to `data/embeddings/`:
  - `default_meta.json` (12 MB)
  - `default_vectors.bin` (67 MB, float32 binary)
  - Generated in 198s on CPU (~220 vec/s). Cost: $0.
- `bible/hybrid.py` — **Milestone 3C hybrid fusion engine (ADR-011).**
  Citation-keyed join of BM25 results + semantic results with per-source
  min-max normalization. Reciprocal hits (verse in BOTH sources) naturally
  outrank solos. CLI: `python -m bible hybrid "comfort in grief"
  [--bm25-weight 0.5] [--solo-weight 0.7] [--top-k 10] [--json]`.
- Real-index integration test: `t_semantic_real_index_loads_and_returns_results`
  loads the on-disk index and runs a real query end-to-end. Skipped
  automatically when the index doesn't exist (CI path).
- 13 new sister-script tests (12 hybrid fusion + 1 real-index). Suite
  now at **75 passed, 0 failed**.

### Changed
- `bible/__main__.py` — `hybrid` subcommand wired into the CLI dispatcher.
- HANDOFF §5 M3C — marked ✅ (was "defer to Phase 3.5"). With the real
  index in hand, hybrid fusion is no longer blocked.
- HANDOFF §5 M3B — index workflow now concrete: `pip install sentence-transformers numpy`
  → `python scripts/index_embeddings.py --backend local --name default`.

## [0.7.0] — 2026-09-09

### Added
- `bible/semantic.py` — `NIMEmbedder` class. Real implementation of the
  NIM backend (Gemini's commit `ef61976` documented it but stubbed it).
  Talks to `https://integrate.api.nvidia.com/v1/embeddings` via
  `urllib.request` (stdlib-only). Reads `NVIDIA_API_KEY` from env
  (`~/.hermes/.env` per HANDOFF §7.6). Defaults to
  `nvidia/nv-embedqa-e5-v5` (1024-dim E5 retriever).
- Six distinct error classes (`NIMAuthError`, `NIMRateLimitError`,
  `NIMServerError`, `NIMResponseError`, `NIMConnectionError`, base
  `NIMError`) so callers can distinguish retry-with-backoff from
  abort without parsing strings.
- `embed_query()` sets `input_type="query"` automatically for E5 models
  — the single biggest quality lever for retrieval, and easy to get
  wrong silently.
- Out-of-order `index` sorting defends against buggy NIM responses.
- `NIMEmbedder._http_post` is a monkey-patch hook so tests can inject
  a fake transport without monkey-patching `urllib` globally.
- 9 new sister-script tests (suite at **62 passing**): missing-key
  guard, full roundtrip with mock transport, `input_type=query` for
  ad-hoc queries, out-of-order index sort, HTTP 429/401/5xx mapping,
  malformed JSON, default-model sanity, factory routing.

### Changed
- `get_embedder()` factory now supports `"nim"` explicitly and routes
  `auto` mode through: local (if `sentence-transformers` importable)
  → NIM (if `NVIDIA_API_KEY` set) → mock fallback.
- `python -m bible semantic ...` and `scripts/index_embeddings.py`
  both accept `--backend nim` in their CLI choices.
- HANDOFF §5 M3B status: marked ✅ (was "embeddings are refinement,
  not load-bearing" — that rationale stands, but the architecture
  itself is now actually built, not just scoped).

## [0.6.0] — 2026-09-09

### Added
- **Phase 3.1 — Quran as the second tradition shipped (ADR-009).**
- `scripts/ingest_quran.py` — stdlib ingestion script fetching 6 editions from `fawazahmed0/quran-api` (Unlicense) and repacking into the canonical multi-tradition JSON schema (`docs/data-schema.md` §2).
- `data/quran/` — 6 public-domain Quran editions (~8.2 MB): Saheeh International (1996), Abdullah Yusuf Ali (1934), Marmaduke Pickthall (1930), Mufti Taqi Usmani, A. J. Arberry (1955), and Arabic Quran Uthmani Hafs recitation from King Fahd Quran Complex.
- `data/quran/README.md` — dataset documentation, Tanzil/Unlicense provenance, and schema documentation.
- `bible/quran.py` — Quran adapter module mirroring `bible.lookup`. Features comprehensive surah alias normalization (all 114 surahs, prefixes, transliterations, and named verses like Ayat al-Kursi), citation parsing (`parse_quran_ref`), lazy JSON loading with `@lru_cache`, and parallel multi-edition retrieval.
- `python -m bible quran "Al-Baqarah 2:255"` CLI subcommand — displays Arabic Uthmani script alongside English translation, supports multi-translation comparison (`-t`), and outputs structured JSON (`--json`). Safe UTF-8 console output across Linux and Windows.
- 10 new sister-script tests in `tests/run_all.py` — suite expanded from 38 → 48 passing tests (0 failed).
- ADR-009 recorded in `docs/design-decisions.md`.
- **Milestone 3B — Dense semantic retrieval architecture (ADR-010).**
- `bible/semantic.py` — stdlib-first vector search engine with dot product, Euclidean norm, and cosine similarity. Features flat binary float32 index storage (`.bin` + `.json`), pluggable backends (`local`, `mock`, `nim`), and multi-tradition cross-corpus filtering.
- `scripts/index_embeddings.py` — offline embedding generation script for Bible + Quran corpora.
- `python -m bible semantic "..."` CLI subcommand with `--top-k`, `--tradition`, and `--json` support.
- `pyproject.toml` — declared `[project.optional-dependencies] embeddings = ["sentence-transformers>=2.2.0", "numpy>=1.20.0"]`. Base install remains pure zero-dependency stdlib.
- 5 new sister-script tests in `tests/run_all.py` — total suite expanded to **53 passed tests (0 failed)**.
- ADR-010 recorded in `docs/design-decisions.md`.

## [0.5.0] — 2026-09-09

### Added
- `docs/phase3-scope-quran.md` — Phase 3 scope doc for Quran as the pilot
  second tradition. Identifies `fawazahmed0/quran-api` (Unlicense, 492
  editions) as the canonical source, the adapter pattern as the
  scaling strategy, and the 5-translation shortlist for Phase 3.1. ~600
  lines of estimated work; stdlib throughout.

### Removed
- `bible-query.py` (260 lines) — legacy CLI from the Grok upgrade. Was
  deprecated in v0.2.0 and superseded for parallel/strongs by the
  `bible/` package, and for keyword search by `bible search` (BM25) in
  v0.3.0. Per ADR-004.
- `tests/run_all.py::t_legacy_bible_query_does_not_inline_strongs_into_text`
  — regression test for the now-deleted script. Sister-script suite
  now at 38 passing tests.

### Changed
- README.md, HANDOFF.md (§4.2, §6, §7.4, §10), CONTRIBUTING.md,
  SECURITY.md, docs/data-schema.md, .github/ISSUE_TEMPLATE/bug_report.md,
  .github/PULL_REQUEST_TEMPLATE.md — all references to `bible-query.py`
  removed or rewritten to point at the `bible/` package or
  `python -m bible <subcommand>`.

## [0.4.0] — 2026-09-09

### Added
- `bible/references.py` — cross-reference engine backed by 605K+ openbible.info edges across 29K+ source verses. Public surface: `get_references(ref)`, `get_reciprocal(ref)`, `traverse(ref, hops)`, `load_xrefs()`, `metadata()`.
- `python -m bible references "John 3:16"` CLI subcommand with `--hops` (1–3), `--min-votes` (default 3), `--direction out|in|both`, and `--json` output.
- `data/references/cross_references.json` — normalized JSON keyed by canonical verse ref (19 MB). Derived from openbible.info (CC-BY 4.0).
- `data/references/cross_references.txt` — raw 8 MB TSV snapshot (commit 2024-11-04).
- `data/references/README.md` — license provenance + schema + refresh instructions.
- `scripts/ingest_cross_references.py` — one-shot ingestion script. Idempotent; re-run to refresh.
- 13 new sister-script tests for the cross-reference engine. Suite now at 39 passing tests.
- ADR-008 (`docs/design-decisions.md`) — openbible.info cross-references as Phase 1 cross-reference substrate.

### Changed
- `bible/__main__.py` — added `references` to the CLI dispatcher + USAGE string.
- `pyproject.toml` version bumped to `0.4.0`.

## [0.3.0] — 2026-09-09

### Added
- `bible/search.py` — pure-stdlib Okapi BM25 search engine (ADR-007) with $k_1=1.5, b=0.75$, Unicode/multilingual tokenization (handles Latin, Hebrew, Greek, Cyrillic, and CJK characters), diacritic-insensitive normalization (`NFKD`), phrase boost, and coverage multiplier.
- `python -m bible search "..."` CLI command with flags `-t/--translation`, `-n/--limit`, `--strongs`, and `--json`.
- `.github/workflows/ci.yml` — continuous integration workflow matrix testing across Ubuntu and Windows on Python 3.10–3.13.
- `docs/design-decisions.md` ADR-007: Stdlib Okapi BM25 as Canonical Search Baseline.
- 5 new search test cases in `tests/run_all.py` (`t_search_faith_without_works`, `t_search_no_results`, `t_search_translation_web`, `t_search_cli_json`, `t_search_multilingual_wlca_hebrew`), bringing test suite to 25 passing tests.

### Fixed
- UTF-8 console output on Windows in `tests/run_all.py`, `bible/__main__.py`, and `bible-query.py` avoiding `UnicodeEncodeError` when printing non-ASCII / ancient language texts and checkmarks.

## [0.2.0] — 2026-09-09

### Added
- `tests/run_all.py` — sister-script test runner (stdlib-only, no pytest). 20 tests covering reference parser, KJV loading, translation enumeration, parallel lookup, Strong's CLI, and legacy-script regression. Run via `python3 tests/run_all.py`.
- `docs/design-decisions.md` — six ADRs capturing the architectural decisions made since the Grok upgrade: stdlib-only, multi-tradition constraint, Strong's-as-JS, legacy CLI deprecation, sister-script tests, and the book-resolution fuzzy-match removal.
- `docs/evaluation.md` — shell document defining what we measure (and explicitly what we don't) at each milestone.
- `notes/2026-09-09.md` — daily journal entry (see HANDOFF.md §7.2).

### Changed
- `bible/lookup.py::resolve_book_name` — removed fuzzy substring fallback that incorrectly resolved `1jn` to `John` instead of `1 John`. Added `1jn`/`2jn`/`3jn` no-space aliases.
- `pyproject.toml` version bumped to `0.2.0`. `[project.scripts]` exposes `bible` (the new package CLI), not `bible-query`.

### Fixed
- `bible-query.py --strongs` — previously inlined lemma + gloss into the English text, producing unreadable output ("Forבִּכּוּרָה…Godחֲדַר…"). Now strips Strong's tags from the English line and prints Strong's references as a separate block. `python -m bible parallel --strongs` remains the canonical output path.
- `tests/run_all.py` — exposes the regression test for the `--strongs` bug above so it can't silently come back.

### Deprecated
- `bible-query.py` is now legacy. Use `python -m bible parallel ...` / `python -m bible strongs ...`. Will be removed when Milestone 3 (semantic search) lands the `bible search` command.

## [0.1.0] — 2026-07-31

### Added
- `bible-query.py` upgraded with exact reference parsing (book, chapter, verse, ranges), keyword search with multi-word scoring, Strong's enrichment on demand, JSON output, and an LLM-ready context block.
- `convert_strongs_to_json.py` — converts Open Scriptures Strong's `.js` files to clean JSON.
- `make_flat_training.py` — produces a JSONL for embedding / training.
- `LICENSE` (MIT).
- `pyproject.toml` — packaging metadata.
- `agents.md` — runtime contract for any agent using this data (later absorbed into `HANDOFF.md` §11).

### Notes
- This is the "Grok upgrade" commit (`61c9f0a`). Distinguished from the prior initial commit by the addition of the `bible-query` rewrite and the supporting tooling.

## [0.0.1] — 2026-07-31

### Added
- Initial commit (`42b9996`).
- `kjv.json` — King James Version (1769) with embedded Strong's tags.
- `translations/*.json` — 12 additional translations (YLT, WEB, GNV, DRB, RSV, LUT, SYNOD, RV1960, CUV, UKRK, TISCH, LXX, WLCa).
- `strongs_data/hebrew/` — H1–H8674 (8,674 entries).
- `strongs_data/greek/` — G1–G5624 (5,624 entries).
- `bible-query.py` (v0) — basic keyword search.
- `normalize.py`, `normalize_all.py` — JSON normalization utilities.
- `README.md` — initial framing.

---

## Versioning notes

- **Pre-1.0 versions** are pre-stabilization. Breaking changes are possible between minor versions.
- **1.0** ships when Milestone 1 (multi-translation lookup, `HANDOFF.md` §5) lands.
- **The data schema** is versioned independently in `docs/data-schema.md`. Schema changes go through the field-map bump process and require Council review.
- **The governance documents** (`COUNCIL.md`, `docs/governance/council-design.md`) version per their own embedded version history, not the Python package version.
