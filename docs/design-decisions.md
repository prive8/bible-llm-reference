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

- **ADR-008 — RESOLVED 2026-09-09** → Cross-reference dataset source is
  openbible.info (CC-BY 4.0), not TSKe-from-scratch. See ADR-008 in this
  file.
- **ADR-009** — Dense embedding retrieval backend (local sentence-transformers
  vs. hosted NVIDIA NIM). Defer to Milestone 3B.
- **ADR-010** — Phase 2 base model (Llama / Mistral / Qwen / smaller).
  Defer to Phase 2.

---

## ADR-008 — openbible.info cross-references as Phase 1 cross-reference substrate

**Status:** Accepted (2026-09-09).
**Context:** HANDOFF §5 Milestone 4 called for ingesting a public-domain cross-reference dataset ("TSKe recommended, verify license"). Three candidates were considered:
1. **scrollmapper/bible_databases `cross_references.txt`** — TSV of openbible.info data, CC-BY 4.0, 344,800 edges. Hosted on GitHub; stable mirror.
2. **CrossReferences-org/bible-cross-references** — TSK with phrase-level anchors for English/French/Afrikaans, CC-BY 4.0 (not pure public domain — attribution required).
3. **Build from scratch** — infeasible at this scale (~300K edges); no precedent for a non-crowdsourced TSKe-quality graph.

**Decision:** Use the openbible.info dataset via the scrollmapper mirror, ingested by `scripts/ingest_cross_references.py` into `data/references/cross_references.json`. License is **CC-BY 4.0**, propagated via the data README and the project README. Raw TSV is committed alongside the JSON so the data is auditable without re-downloading.

**Rationale:**
- openbible.info is the de-facto modern cross-reference source for Bible software (Logos, Olive Tree, TheWord all use derived datasets).
- CC-BY 4.0 is acceptable per HANDOFF §7.5 (the Strong's CC-BY-SA is already in the same license family; attribution to openbible.info is straightforward).
- 605K+ post-range-expansion edges is enough signal for a useful traversal; building a graph from scratch would take weeks of research.

**Consequences:**
- The cross-reference engine (`bible/references.py`) is stdlib-only (ADR-001 consistent) — pure JSON load + dict traversal.
- Votes are an interpretive signal (crowd-sourced quality scores), not authoritative. CLI surfaces the votes so consumers can filter.
- Negative-vote edges are dropped at ingest (1,166 of 344,800 rows). Consumer can re-enable by editing the ingest script.
- Self-loops are dropped at ingest (already-excluded in the openbible data, but the script filters defensively).
- Future migration: if a better public-domain cross-reference dataset appears, the JSON shape is decoupled from the source — re-ingest only.
- **Phase 3 implication:** non-Christian traditions have no openbible equivalent. The cross-reference engine will need to be either omitted for those traditions or sourced separately (e.g., Quran tafsir cross-references, rabbinic cross-references for Tanakh).

---

## ADR-009 — Quran as Phase 3 Pilot Tradition and Multi-Tradition Adapter Pattern

**Status:** Accepted (2026-09-09).
**Context:** The project's long-term vision requires extending beyond the Christian Bible to multiple religious traditions (`COUNCIL.md` §1). The Quran was chosen as the pilot second tradition (`docs/phase3-scope-quran.md`) because of its structural clarity (114 surahs, 6,236 ayahs), rich public-domain ecosystem (Tanzil.net, King Fahd Quran Complex via `fawazahmed0/quran-api`), and monotheistic Abrahamic thematic overlap.

**Decision:**
1. **Ingestion:** Pure stdlib script `scripts/ingest_quran.py` transforms 5 public-domain English translations (Saheeh International, Yusuf Ali, Pickthall, Mufti Taqi Usmani, Arberry) + Uthmani Hafs Arabic text into `data/quran/{edition}.json` matching `docs/data-schema.md` §2 (`tradition: "islam"`, `structure: "surah_ayah"`, `divisions` with surah metadata).
2. **Adapter Pattern:** `bible/quran.py` mirrors the public contract of `bible/lookup.py`. It parses Quran citations (`"Quran 2:255"`, `"Al-Baqarah 2:255"`, `"2:255"`, `"Ayat al-Kursi"`, ranges `"112:1-4"`), caches loaded editions, and returns structured verse objects.
3. **CLI Integration:** `python -m bible quran "Al-Baqarah 2:255"` presents Arabic Uthmani text alongside English translation, supports multi-translation views (`-t`), and outputs JSON (`--json`).

**Consequences:**
- The adapter pattern proves that non-Christian scripture structures (`surah/ayah` vs `book/chapter/verse`) can be seamlessly added without modifying core Bible lookup code.
- Zero external dependencies: stdlib-only throughout (ADR-001 preserved).
- Cross-platform UTF-8 handling verified for Arabic script on Windows and Linux consoles.
- Total test suite expanded from 38 to 48 sister-script tests with 0 failures.

---

## ADR-010 — Milestone 3B Semantic Search Architecture & Pluggable Backend

**Status:** Accepted (2026-09-09). **Implementation complete in v0.7.0** (NIM `NIMEmbedder` class added; the architecture Gemini shipped in v0.6.0 had the contract documented but no actual NIM implementation).

**Context:** Milestone 3B requires semantic / conceptual retrieval across scriptures (e.g. "finding peace in suffering"). Adding neural libraries (torch, sentence-transformers, numpy) directly into base dependencies would violate ADR-001 (stdlib-only baseline). Hosted inference introduces credentials and costs.

**Decision:**
1. **Stdlib-First Vector Engine:** `bible/semantic.py` implements vector mathematics (dot product, Euclidean norm, cosine similarity, top-$k$ ranking) in pure Python standard library (`math`, `struct`, `heapq`).
2. **Binary Flat Vector Index:** Serialized float32 binary format (`.bin`) paired with JSON metadata (`.json`) enables sub-millisecond in-memory vector cosine similarity search with zero external vector database dependencies.
3. **Pluggable Embedders:**
   - `local`: Local CPU/GPU sentence-transformers (`all-MiniLM-L6-v2`, ~80MB) configured via `[project.optional-dependencies] embeddings = ["sentence-transformers>=2.2.0", "numpy>=1.20.0"]`.
   - `mock`: Deterministic stdlib hash-projection embedder for zero-dependency test suites and offline verification.
   - `nim`: Hosted NVIDIA NIM via `NIMEmbedder` (v0.7.0+) — reads `NVIDIA_API_KEY` from env, defaults to `nvidia/nv-embedqa-e5-v5` (1024-dim E5 retriever), uses `input_type="query"` vs `"passage"` correctly for E5 family models.
4. **Offline Indexing Script:** `scripts/index_embeddings.py` generates multi-tradition vector indices offline across Christian Bible and Quran. Supports `--backend nim` for hosted generation.
5. **CLI:** `python -m bible semantic "query" [--top-k 10] [--tradition all|bible|islam] [--backend auto|local|mock|nim] [--json]`.

**`NIMEmbedder` implementation details (v0.7.0):**
- Stdlib `urllib.request` POST to `{NIM_BASE_URL}/embeddings`, defaults to `https://integrate.api.nvidia.com/v1`.
- Bearer-token auth header (`Authorization: Bearer ${NVIDIA_API_KEY}`).
- OpenAI-compatible request body: `{"input": [...], "model": "nvidia/nv-embedqa-e5-v5", "encoding_format": "float", "input_type": "passage"|"query"}`.
- Six distinct error classes (`NIMAuthError`, `NIMRateLimitError`, `NIMServerError`, `NIMResponseError`, `NIMConnectionError`, base `NIMError`) so callers can distinguish retry-with-backoff from abort without parsing strings.
- `embed_query()` sets `input_type="query"` automatically; `embed_texts()` defaults to `"passage"`.
- Out-of-order `index` sorting defends against buggy NIM responses.
- `_http_post` is a monkey-patch hook for test injection.

**Consequences:**
- Base runtime remains 100% zero-dependency stdlib (ADR-001 preserved).
- Development and test suites remain $0.00 compute cost (mock + stdlib-only).
- Hermes or local environments can generate full neural embeddings offline whenever ready.
- Operational compute decision (NIM vs. local) is decoupled from the architecture.
- Test suite expanded to **62 passing tests** with 0 failures.

---

## ADR-011 — Milestone 3C Hybrid BM25 + Semantic Fusion

**Status:** Accepted (2026-09-09).

**Context:** With Milestone 3B (semantic search) shipped in v0.6.0 and v0.7.0, the project had two complementary retrieval paths but no way to combine them. BM25 (M3A) is exact-keyword-strong; semantic (M3B) is meaning-strong. Neither alone answers "verses about comfort in grief" with both keyword matches (e.g. "comfort") and thematic matches (e.g. "blessed are those who mourn") in one ranked list.

**Decision:**
1. **`bible/hybrid.py` — citation-keyed join.** Take the top-K candidates from BM25 (`bible.search`) and top-K from semantic (`bible.semantic`), join on citation string (e.g. "John 3:16"), and produce a single fused ranking.
2. **Per-source min-max normalization.** BM25 raw scores are unbounded and query-length-dependent; cosine similarities are in [-1, 1]. Without normalization, BM25 always dominates. Min-max each source's results to [0, 1] within a single query, then compute `combined = α * bm25_norm + (1-α) * sem_norm`.
3. **Reciprocal hits outrank solos via weighted-sum structure.** A verse appearing in both BM25 and semantic gets the full weighted sum; a verse in only one source gets its single score multiplied by `solo_weight` (default 0.7). This naturally elevates consensus without filtering any source.
4. **CLI integration.** `python -m bible hybrid "comfort in grief" [--bm25-weight 0.5] [--solo-weight 0.7] [--top-k 10] [--json]`. Wired into `bible/__main__.py`.
5. **Defaults.** `DEFAULT_BM25_WEIGHT = 0.5` (equal weight), `DEFAULT_SOLO_WEIGHT = 0.7` (solos get 70% of their normalized score). Both are public API constants; if they change silently every downstream user gets different rankings.

**Consequences:**
- Pure stdlib (`math`, no numpy needed for fusion — min-max is trivial Python).
- Cross-tradition capable: BM25 leg is Bible-only; semantic leg includes Quran. Hybrid results naturally include both.
- 12 new sister-script tests covering: normalization (basic, constant, empty), reciprocal vs solo ranking, extreme weight values (0.0 and 1.0), empty input sets, default constants sanity, top_k limiting, CLI dispatcher wiring.
- Test suite now at **75 passed, 0 failed**.
- The hybrid fusion closes the Milestone 3B/C loop: M3A (BM25) + M3B (semantic) + M3C (fusion) all landed. With a real local index in `data/embeddings/` (43,483 vectors across Bible + Quran Saheeh International), all three retrieval paths now produce useful results on natural-language queries.

---

## Pending ADRs (to be drafted when the decision is made)

- **ADR-011 — RESOLVED 2026-09-09** → Hybrid BM25 + semantic fusion engine shipped in v0.8.0 (this ADR). Replaces the previous placeholder.
- **ADR-012 — RESOLVED 2026-09-10** → Phase 2 base model family pick (this ADR).

---

## ADR-012 — Phase 2 base model family pick (Llama-3.1-8B-Instruct)

**Status:** Accepted (2026-09-10). Defers the operational "which specific
checkpoint + how to fine-tune" decision to when Phase 2 work actually
starts; locks the *family* and the *criteria* so the operational pick
has a clear framework when it lands.

**Context:**
Phase 2 is "generative voice fine-tune" per HANDOFF §1 — a tool that
takes a question and writes a response in the voice of the tradition
(pastor citing Romans, rabbi citing Rashi, qari citing tafsir), grounded
in the corpus with citations, never inventing doctrine. **Distill-only**
by HANDOFF §1 constraint.

Data shape (now stable, after Phase 3.1 + 3.2 shipped in v0.6.0–v0.11.0):
- **~55K passages** across Christianity (37K Bible, KJV), Islam (6K
  Quran Saheeh International), Judaism (6K Torah + 6K Hebrew nikkud).
- **Multilingual** — primary target is English output, but citations
  must surface Hebrew/Arabic/Greek/Latin originals accurately.
- **High citation density** — every claim is grounded; model must not
  paraphrase citations away.
- **Compact retrieval substrate** — `bible.search` (BM25) + `bible.semantic`
  (sentence-transformers) + `bible.hybrid` (fused) + `bible.references`
  (openbible.info cross-references, 605K edges) provide the
  context the model needs. Model is the synthesizer, not the retriever.

Constraints (from HANDOFF §1, §8 #1, ADR-001):
- **Distill-only** — no training from scratch; LoRA / QLoRA fine-tune
  of an existing open base.
- **Local-first / free-tier-friendly** — the user's cost posture is
  "free-tier endpoints only until you're comfortable with spend"
  (memory, 2026-09-09). A 7B-class model must run on a single consumer
  GPU (24 GB VRAM) or be hosted on a free-tier inference API.
- **Citation fidelity is non-negotiable** — Runtime Contract rules 1, 2,
  4 in `RUNTIME_CONTRACT.md`. A model that hallucinates citations is
  unusable.
- **Council principles bind** — neutral across traditions, primary-
  source-first, no impersonation (RUNTIME_CONTRACT rule 5).

**Decision — family pick:**

**Llama-3.1-8B-Instruct** (or its successors at the same parameter
count) is the chosen Phase 2 base family. Reasoning:

1. **License: Llama 3 Community License.** Permits distillation and
   fine-tuning, requires attribution + acceptable-use policy
   compliance. Compatible with the project's MIT-license code,
   CC-BY data, and Council's neutral-across-traditions stance.
   Compared to Mistral 7B (Apache 2.0 — also fine) and Qwen2.5-7B
   (Apache 2.0 — also fine), Llama 3.1 has the largest community
   fine-tuning ecosystem (largest pool of LoRA adapters, instruction
   templates, eval harnesses to learn from). Ecosystem beats license
   marginal differences here.
2. **Vocabulary size + tokenizer.** Llama 3.1's tokenizer handles
   Latin-script languages well; **Hebrew and Arabic fall back to
   byte-level BPE**, which is slower but functional. For the
   citation-originals requirement (where the model needs to *see*
   Hebrew/Arabic and either reproduce or summarize), byte-level BPE
   is acceptable. (Qwen2.5 has a larger tokenizer with explicit
   CJK + Arabic coverage but its training data is more Chinese-leaning,
   which is *worse* for our Abrahamic corpus — Hebrew/Arabic vocab
   doesn't matter if the model's prior is wrong.) Llama wins on
   training-data distribution even if its tokenizer is weaker on
   Hebrew/Arabic chars.
3. **Context window.** Llama 3.1 ships 8K context out of the box;
   128K with rope-scaling hacks. Long context matters because
   cross-reference traversal (RUNTIME_CONTRACT rule 4) can chain
   3-hop expansions through `bible.references.traverse(hops=3)`.
   8K native is sufficient for "single verse + commentary +
   cross-references"; 128K if we ever do "entire book context" mode.
4. **Citation-fidelity track record.** Llama 3.1 8B Instruct scores
   ~75% on TruthfulQA, ~50% on HaluEval (per Meta's model card).
   That's not "no hallucinations ever" but it's the right baseline
   to distill from. Smaller models (Phi-3-mini, Gemma-2-2B) score
   much worse on HaluEval; larger models (Llama 3.1 70B) score
   better but fail the "single 24GB GPU" constraint.
5. **Distill-friendly fine-tuning ecosystem.** Llama 3.1 has
   well-documented QLoRA configs (4-bit, rank-16 LoRA on attention
   + MLP layers) that fit in 24 GB VRAM with full gradient
   checkpointing. Qwen2.5 has similar but smaller ecosystem;
   Mistral 7B is fine but the 7B-vs-8B split is marginal.

**What this decision does NOT pick:**
- Specific checkpoint (Llama 3.1 8B Instruct has ~5 variants —
  base, instruct, chat, codellama-instruct, etc.). Picked at Phase 2
  start based on the distillation pipeline's specific needs.
- Quantization scheme (Q4_K_M, Q5_K_M, Q8_0, GPTQ, AWQ). Picked
  at Phase 2 start based on target hardware.
- Fine-tuning recipe (LoRA rank, target modules, dataset format).
  Drafted separately when Phase 2 work actually starts.
- Training data shape. The current schema (corpus + retrieval
  substrate) is stable; the *training dataset* that teaches the model
  "when user asks X, retrieve Y, write Z in voice V" is designed
  in Phase 2, not now.

**Consequences:**
- Closes HANDOFF §8 #2.
- Phase 2 starting checklist now has a clear first step: "download
  Llama-3.1-8B-Instruct.Q4_K_M.gguf, verify it runs on the target
  hardware, evaluate against a held-out religion-Q&A set."
- The pick is **a family pick**, not a commitment. If by Phase 2
  start a Llama 4 / 3.2 / Mistral 8B / Qwen3 8B has materially
  improved on Hebrew/Arabic tokenization or HaluEval, this ADR is
  superseded by an ADR-013 that re-runs the comparison.
- **Reject Phi-3-mini (3.8B), Gemma-2-2B:** too small for
  citation-fidelity at our standards.
- **Reject Llama-3.1-70B:** fails single-GPU constraint. If free-tier
  NIM ever allows embedding inference (HANDOFF §8 #1), hosting the
  base model on NIM is a separate decision; not pre-decided here.
- **Reject Mistral-7B / Qwen2.5-7B:** both viable, both would be picked
  over Llama if Llama 3.1 wasn't available. Recorded here as fallbacks
  so the next ADR author doesn't re-litigate from scratch.

