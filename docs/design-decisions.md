# Design Decisions (ADRs)

> Architecture Decision Records. One per significant choice. Append-only.
> When a decision is reversed, add a new ADR that supersedes the old one
> and link both.

---

## ADR-001 — Stdlib-only dependencies for Phase 1

**Status:** Accepted (2026-07-31, Grok upgrade).
**Context:** The Phase 1 substrate is a deterministic reference tool — it loads committed JSON, parses references, looks up Strong's entries. None of that needs numpy, requests, or anything outside stdlib. Adding dependencies costs startup latency, supply-chain risk, and a `pip install` barrier for downstream consumers who just want to clone and run.
**Decision:** `dependencies = []` in `pyproject.toml`. Stdlib only. Any model/embedding dependency is deferred to Milestone 3 (semantic search) where it's a *requirement*, not a default.
**Consequences:** Sister-script tests run without pytest. Ingestion scripts use `urllib` instead of `requests`. Future contributors can't `import numpy` without a milestone-level justification in HANDOFF.md.

---

## ADR-002 — Multi-tradition data layer constraint (Phase 3 design now)

**Status:** Accepted (2026-07-31, Grok upgrade).
**Context:** The project is the Christian slice of a larger Religion & Spirituality AI. Adding Torah/Quran/Vedas/etc. in Phase 3 must be a config change, not a code rewrite — otherwise the data layer is the thing we'll regret first.
**Decision:** The Phase 1 data layer accepts a generic `divisions` abstraction (1-to-4 levels deep) alongside the existing Christian book/chapter/verse shape. Lexicon surface is plugin-based (Strong's, Lane's, Monier-Williams, etc.). Citation format is per-tradition. Documented in `docs/data-schema.md` with parallel-structure examples for five tradition families.
**Consequences:** The Phase 1 schema is *not* the simplest possible schema for Christian Bible. It's the simplest schema that scales to traditions with different canonical structures (Quran surah/ayah, Gita chapter.verse with period, Tao single-level chapter, etc.). The "extra generality" is the cost of Phase 3 being cheap.

---

## ADR-003 — Strong's data ships as JS source, not pre-aggregated JSON

**Status:** Accepted (2026-07-31), revisited 2026-09-09.
**Context:** Strong's Hebrew and Greek ship from Open Scriptures as `.js` files (`strongs-hebrew-dictionary.js`, ~2 MB each) wrapped in a `var x = ...; module.exports = x;` pattern. They're committed as-is. Loading parses the JS at startup (~2s).
**Decision:** Ship the JS files as committed source-of-truth. `convert_strongs_to_json.py` exists to materialize clean JSON, but the generated JSON is gitignored. Every load pays the JS-parse tax.
**Rationale (2026-09-09 revisit):** This keeps the repo lean and makes upstream sync simpler (just pull Open Scriptures' latest JS). The startup cost is acceptable for a CLI. When the runtime becomes a hot-path API, switch to committed JSON.
**Consequences:** Every `bible.strongs` or `bible.parallel --strongs` call takes ~2s on first load (then `lru_cache` makes subsequent calls instant). A future change should commit `strongs-hebrew.json` and `strongs-greek.json` when the runtime justifies the ~6 MB repo growth.

---

## ADR-004 — `bible-query.py` is legacy, `python -m bible` is canonical

**Status:** Accepted (2026-09-09).
**Context:** The original `bible-query.py` was the only CLI in the Grok upgrade. The `bible/` package was added in commit `9a7d3b2` (2026-08-01) as the proper surface, but `bible-query.py` was kept around for backwards compat. Its `--strongs` path was also broken (inlined lemma+gloss into the English text — see HANDOFF §5 note 2026-09-09).
**Decision:**
- `python -m bible parallel ...` and `python -m bible strongs ...` are the canonical CLI surface going forward.
- `bible-query.py` remains in the repo as a deprecated convenience for keyword search (its main remaining feature), with `--strongs` fixed to print clean English + separate Strong's reference block.
- `pyproject.toml` `[project.scripts]` exposes `bible` (not `bible-query`).
- New contributors should be pointed at `python -m bible` first. `bible-query.py` gets removed once the keyword search (`bible search`) command lands in Milestone 3.
**Consequences:** Two CLIs temporarily. Document this in README and CONTRIBUTING.

---

## ADR-005 — Sister-script tests, not pytest

**Status:** Accepted (2026-07-31, implicit), formalized 2026-09-09.
**Context:** The project is stdlib-only by ADR-001. Adding pytest is a dependency. Tests at this scale (~20 cases, all end-to-end against real data) don't need pytest fixtures, parametrize, or plugins — they need: load data, run code, assert.
**Decision:** `tests/run_all.py` is a single stdlib Python file with one function per test (named `t_*`). Decorator registers, runner iterates and counts pass/fail. Exit code 0 = pass. No CI yet — when CI lands, it runs `python3 tests/run_all.py`.
**Rationale:** Sister-script style means each test is independently runnable (you can copy-paste one into a REPL), the runner has zero dependencies, and adding a test is "drop a new `t_*` function in the file." The downside (no fixtures, no parametrize, no pretty output) doesn't matter at this scale.
**Consequences:** Tests load the full KJV + Strong's at startup (~2s). Future: a `tests/unit/` subdirectory can hold pure-logic tests without the data load, if startup latency becomes a problem.

---

## ADR-006 — Remove fuzzy substring matching in book resolution

**Status:** Accepted (2026-09-09).
**Context:** `bible/lookup.py::resolve_book_name` had a third fallback step: for any unresolved input, find an alias whose key is a substring of (or contained in) the input. This was over-permissive — it turned `1jn 4:8` into "John" (because the alias `"jn"` matched the substring `"1jn"`) when the user clearly meant 1 John.
**Decision:** Remove the fuzzy substring fallback. Resolution is now: exact alias match (with and without spaces), then exact canonical name match (case-insensitive). Anything else returns None.
**Consequences:** Some edge inputs that *used to* work via fuzzy matching now return None (and surface a clearer error to the user). Added `"1jn"` / `"2jn"` / `"3jn"` no-space aliases for the common abbreviated form.
**Test:** `tests/run_all.py::t_parse_alias_1jn` now passes; `1jn 4:8` → `1 John`, not `John`.

## ADR-007 — Stdlib Okapi BM25 as canonical search baseline

**Status:** Accepted (2026-09-09).
**Context:** Milestone 3 requires search capabilities. Adding an embedding model or vector database immediately would introduce heavy external dependencies (sentence-transformers, torch, numpy) violating ADR-001 before establishing a deterministic baseline. Additionally, the project's long-term vision requires supporting multiple religious texts and ancient languages (Hebrew, Greek, Arabic, Sanskrit, CJK, etc.).
**Decision:** Implement an in-memory Okapi BM25 search engine (`bible/search.py`) using Python standard library only (`math`, `re`, `unicodedata`, `collections`).
- Tokenizer is Unicode-aware (`\w+` across multilingual scripts, individual CJK character segmentation) with diacritic stripping (`unicodedata.normalize('NFD')`) so unpointed/unaccented queries match pointed ancient texts (e.g. WLCa Hebrew, LXX Greek).
- Ranking uses Okapi BM25 ($k_1=1.5, b=0.75$) with Lucene non-negative IDF, coverage bonus for multi-word queries, and exact phrase boosts.
- Translation-pluggable: searches KJV by default, or any loaded translation (`-t WEB`, `-t YLT`, `-t WLCa`, etc.).
- Search is exposed via `python -m bible search "..."`. `bible-query.py` keyword search is superseded.
**Consequences:** Fast (<0.5s cold, <5ms warm) deterministic keyword search across all translations without any `pip install` dependencies. Embedding-based search (Milestone 3B) will build on top of this as an optional enhancement.

---

## Pending ADRs (to be drafted when the decision is made)

- **ADR-008** — Dense embedding retrieval backend (local sentence-transformers vs. hosted NVIDIA NIM). Defer to Milestone 3B.
- **ADR-009** — Cross-reference dataset source (TSKe vs. build from scratch). Defer to Milestone 4.
- **ADR-010** — Phase 2 base model (Llama / Mistral / Qwen / smaller). Defer to Phase 2.
