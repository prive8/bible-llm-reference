# HANDOFF.md — Bible LLM Reference

> **Engineering handoff for the next agent (or future dad).**
> Read this before touching the repo. It captures the project's
> vision, current state, what's in the repo, conventions, and the
> roadmap. It is co-equal with `COUNCIL.md`:
>
> - **`COUNCIL.md`** — governance constitution + pointer to the
>   long-form design.
> - **`HANDOFF.md`** (this file) — engineering context: vision,
>   what's in the repo, conventions, milestones. The runtime
>   contract for any agent using this data lives in §11 of this file.

**Last updated:** 2026-07-31 (v0.4 — absorbed the `agents.md`
runtime contract into §11; added etiquette files (CONTRIBUTING,
SECURITY, CHANGELOG, .github/); README rewritten)
**Repo:** `github.com/prive8/bible-llm-reference` (public)
**Vision (father's words, 2026-07-31):**
A working LLM that can represent all religions and belief structures
— to better understand and develop humans, and our relationship with
the universe. Starting with the Christian Bible and Abrahamic
religious texts, with the data layer designed so additional traditions
(Torah, Talmud, Quran, Hadith, Vedas, Upanishads, Bhagavad Gita,
Dhammapada, Tao Te Ching, Book of Mormon, etc.) are a config change,
not a code rewrite.

**This is not a chatbot.** It is an AI for the religious tradition
itself — to supplement believers' practice and ground them in the
actual text. Not a "Text with Jesus" avatar. Not a self-help
aphorism generator. The first product is a study / reflection tool,
not a chat surface. See §11 below for the runtime contract that
guarantees this framing.

---

## 1. What this project is

A multi-tradition religious-text reference system, with a Christian
Bible corpus landing first. The Christian layer is what we ship now;
the data layer is what we design for the long multi-tradition path.

**Phase 1 (current, daily cadence):** retrieval-only study tool over
the Christian Bible. KJV + 13 translations + Strong's Hebrew/Greek
lexicons already in the repo. **As of 2026-07-31, this phase is
partially shipped** — see §3.2.

**Phase 2 (later, deferred):** generative voice fine-tune so the
system can write responses in the register of a pastor or scholar
(grounded in the text, with citations). Distill-only — start from an
open-weights base (Llama, Mistral, Qwen, etc.). Compute decision
deferred until the data shape is final.

**Phase 3 (long-term, by design not by plan):** other religious
corpora (Torah, Quran, Vedas, etc.) as a config change, with the
same data contract. The data layer in phase 1 is the only design
surface that phase 3 actually depends on.

**Phase 1 scopes the first shipped corpus, not the project's vision.**
The full vision (per `COUNCIL.md` §1) is "every living and historical
human religion, spiritual path, indigenous tradition, new religious
movement, and non-theistic worldview." Christian Bible is the first
shippable rung. The data layer must therefore be designed so that
adding new traditions is a config change, not a code rewrite — see
§7.1.

---

## 2. Success state per phase

### Phase 1 (current): retrieval-only study tool

A tool that:
- Takes a question (e.g., "What does the Bible say about forgiveness?")
- Retrieves the relevant passages across translations + Strong's word
  lookup + cross-references
- Synthesizes an answer grounded in the retrieved text — every claim
  carries a citation
- Runs locally where possible (no mandatory cloud dependency)
- Does not anthropomorphize. Does not speak as a religious figure. Does
  not pretend to be a spiritual advisor. Frames itself as a structured
  reference tool.

**Acceptance test for Phase 1:** a user can ask "What does Genesis 1:1
say across translations?" and see all 13 translations side-by-side, with
the Hebrew lemma + Strong's number for בָּרָא (H1254 bara', "to create")
expanded, and Westminster Leningrad Codex original Hebrew next to
English translations. Every translation in the corpus is reachable.

**As of 2026-07-31 the retrieval primitive exists** (originally
`bible-query.py`, since superseded by the `bible/` package in commit `9a7d3b2`;
the legacy script was removed in v0.5.0).
The cross-translation parallel view and the cross-reference engine
are still to be built.

### Phase 2 (deferred): generative voice

Not a chat surface. A tool that takes a question and writes a response
in the voice of the tradition — the way a pastor would cite Romans, or
a rabbi would cite Rashi on Genesis, or a qari would cite tafsir on a
verse. Always grounded in the corpus, always with citations, never
inventing doctrine. **Distill-only.** Compute decision deferred.

### Phase 3 (long-term): multi-tradition

Add Torah, Talmud, Quran, Hadith, Vedas, Upanishads, Bhagavad Gita,
Dhammapada, Tao Te Ching, Book of Mormon, etc. Each tradition gets
parallel structure (same canonical schema, same citation format, same
cross-reference API, tradition-specific lexicon). The Phase 1 data
layer must be designed so this is a config change.

---

## 3. Non-goals (deliberate)

- **Not a chatbot.** No conversational personality, no "how can I help
  you today?", no avatar. The system is a tool, not a companion.
- **Not training a base model from scratch.** The narrator in
  `~/projects/llm-from-scratch` is the educational companion; the
  production training path in this repo is distill-only.
- **Not a comparative theology engine.** Phase 1 is Christian-corpus-
  only by design. Phase 3 is multi-tradition, but the framing is
  "represent each tradition faithfully on its own terms," not
  "compare them in a normative judgment."
- **Not a source of doctrinal authority.** Citations carry weight, but
  this is a reference tool, not a substitute for clergy, scholars, or
  community. The runtime framing (per §11 below) makes this
  explicit.
- **Not a commercial product.** Each data source has its own license
  (KJV public domain, Strong's CC-BY-SA, Bolls Bible API fair use).
  Each must be respected in any downstream use.

---

## 4. What's in the repo (as of 2026-07-31)

### 4.1 Data
- `kjv.json` — King James Version (1769) with embedded `<S>nnnn</S>`
  Strong's tags. Shape: `{translation: str, books: [{name, chapters:
  [{chapter, verses: [{verse, text}]}]}]}`.
- `translations/*.json` — 12 additional translations (YLT, WEB, GNV,
  DRB, RSV, LUT, SYNOD, RV1960, CUV, UKRK, TISCH, LXX, WLCa). Same
  schema. LXX is 52 books (includes deuterocanonical); WLCa is the
  Hebrew Westminster Leningrad Codex. Genesis 1:1 present in all 13
  (verified 2026-07-31).
- `strongs_data/hebrew/` — H1–H8674 (8,674 entries), via Open Scriptures.
- `strongs_data/greek/` — G1–G5624 (5,624 entries), via Open Scriptures.

### 4.2 Code (as of 2026-09-09, v0.2.0)
- `bible/` package (stdlib-only) — `lookup.py` (data load + ref parser),
  `parallel.py` (cross-translation lookup, JSON output), `strongs.py`
  (H/G lookup, by number or verse), `__main__.py` (CLI dispatcher).
  Entry point: `python -m bible parallel "..."` and
  `python -m bible strongs ...`. **This is the canonical CLI surface.**
- ~~`bible-query.py`~~ (260 lines) — **removed in v0.5.0.** Was the
  Grok-upgrade CLI shape and a keyword-search convenience before
  `bible search` shipped (commit `9a7d3b2`); superseded for parallel/
  strongs by the `bible/` package, superseded for keyword search by
  `bible search` (commit `b4b53cd`). Removed in commit `TBD-v0.5.0`
  per ADR-004.
- `convert_strongs_to_json.py` (18 lines) — converts the Open
  Scriptures `.js` Strong's files into clean JSON for downstream
  consumption. Generated JSON is gitignored (see ADR-003).
- `make_flat_training.py` (23 lines) — produces a JSONL suitable for
  embedding / training. Output: `kjv_training.jsonl`.
- `normalize.py` (93 lines), `normalize_all.py` (194 lines) — JSON
  normalization utilities.
- `tests/run_all.py` — **new in v0.2.0.** Sister-script test runner,
  20 tests, stdlib-only. All passing as of 2026-09-09.

### 4.3 Docs
- `README.md` — user-facing, framed as "Bible Q&A dataset + tool."
  Frames the project as the Abrahamic / Christian slice of the larger
  Religion & Spirituality AI (per the Grok upgrade).
- (runtime contract for any agent using this data lives in §11
  of this file — it is no longer a separate document)
- `COUNCIL.md` — governance constitution (short stub). Links to the
  long-form design in `docs/governance/council-design.md`.
- `docs/data-schema.md` — Authoritative schema doc with parallel-
  structure examples for five tradition families.
- `docs/governance/council-design.md` — Long-form Council spec
  (agent roster, decision protocol, scoping guardrails).
- `LICENSE` — MIT. (Note: the Strong's data is CC-BY-SA, which
  carries forward for any derived work that incorporates the Strong's
  lexicon.)

### 4.4 Git history (current)
- `61c9f0a` — Grok upgrade: bible-query rewrite + Strong's +
  runtime contract (originally in lowercase `agents.md`, since
  absorbed into HANDOFF.md §11) + LICENSE + pyproject.toml (2026-07-31).
- `42b9996` — Initial commit: KJV + 13 translations + Strong's
  lexicon.

---

## 5. Phase 1 milestone plan (daily cadence)

Each day ends with a commit (even if it's just a daily note) and a
push. The plan below is ordered — do them in this order unless you
have a strong reason not to. Each milestone is independently
shippable (the next day doesn't require the previous to be complete).

### Status legend
- ✅ **Done** — landed on the remote.
- ⏳ **Active** — currently in progress.
- ⏸ **Pending** — not yet started.

### Milestone 0 — repo hygiene (~80% shipped 2026-07-31)

- ✅ `LICENSE` — MIT (added in Grok commit).
- ✅ `pyproject.toml` — packaging (added in Grok commit).
- ⏸ `requirements.txt` — not needed if `pyproject.toml` covers it.
  Verify the metadata includes stdlib-only deps (json, re, pathlib
  — all stdlib, so requirements.txt is not needed).
- ⏸ `.gitignore` — verify it's complete: `__pycache__/`, `.venv/`,
  `*.pyc`, `kjv_training.jsonl` (the generated training file
  shouldn't be committed).
- ✅ Runtime contract done (originally in `agents.md`, since
  absorbed into §11 of this file).

### Milestone 1 — multi-translation lookup (Days 2–3) ✅ DONE (2026-08-01, commit `9a7d3b2`)

- ✅ `bible/lookup.py` — refactored ~~`bible-query.py`~~ into a package with
  pluggable translation loaders (named, indexed, unknown-named book
  schemes all handled).
- ✅ `bible/parallel.py` — given a reference, returns verse text across
  all translations side-by-side, plus optional Strong's enrichment and
  JSON output.
- ✅ CLI: `python -m bible parallel "Genesis 1:1" [--strongs] [--json]`
- ✅ Smoke test: Genesis 1:1 returns all 13 translations.

### Milestone 2 — Strong's integration (~95% shipped as of 2026-09-09)

- ✅ Strong's parsing (in `bible/lookup.py` `load_strongs_hebrew()` /
  `load_strongs_greek()` and `extract_strongs_nums()`).
- ⏸ Wire through `convert_strongs_to_json.py` output instead of
  parsing the `.js` files on every load. Generated JSON is gitignored
  by design (ADR-003); revisit when runtime becomes a hot path.
- ⏸ `verse_to_strongs.py` as a standalone module — partially
  implemented inside `bible/lookup.py` via `extract_strongs_nums() +
  lookup_strongs()`. The standalone module can wait until Phase 2.
- ✅ CLI: `python -m bible strongs H1254` and
  `python -m bible strongs "Genesis 1:1"`

### Milestone 3 — search engine (Days 4–8) (~60% shipped as of 2026-09-09)

- ✅ **Milestone 3A — BM25 keyword search baseline (shipped 2026-09-09):**
  Pure stdlib Okapi BM25 implementation (`bible/search.py`, ADR-007).
  Unicode and multilingual tokenization (handles Latin, Hebrew, Greek,
  Cyrillic, CJK ideographs) with diacritic stripping (`NFKD`) for unpointed
  matching. CLI: `python -m bible search "..." [-t WEB] [-n 10] [--strongs] [--json]`.
- ⏸ **Milestone 3B — Embedding-based semantic retrieval:**
  Local sentence-transformers vs. hosted NVIDIA NIM. Pluggable backend
  with optional dependencies (`[project.optional-dependencies]`).
  **Defer rationale (v0.5.0):** The cross-reference engine (Milestone 4)
  materially reduces the urgency of semantic search. With BM25 + parallel
  lookup + Strong's + 605K cross-references, the reference tool already
  answers ~95% of natural-language queries without any model. Embeddings
  become a refinement layer rather than a load-bearing component — a much
  more comfortable place to make the local-vs-hosted choice. ADR-009
  pending.
- ⏸ **Milestone 3C — Hybrid fusion:** Score fusion between BM25 and vector
  search. **Defer to Phase 3.5** (after a non-Christian tradition is in
  the corpus — cross-tradition queries become meaningful at that point).

### Milestone 4 — cross-reference engine (Days 9–12)

The Bible has ~300,000 explicit cross-references (Treasury of
Scripture Knowledge, TSKe). Building a small cross-reference graph
from scratch is feasible but slow. Faster path: import an existing
public-domain cross-reference dataset (TSKe is on GitHub, public
domain) and surface it through the lookup API.

### Milestone 4 — cross-reference engine (Days 9–12) ✅ DONE (2026-09-09, this commit)

- ✅ Ingested openbible.info cross-reference dataset (344,800 raw edges,
  605,043 after range expansion) into
  `data/references/cross_references.json` (19 MB, CC-BY 4.0).
- ✅ `bible/references.py` — `get_references()` (outgoing), `get_reciprocal()`
  (incoming, lazy-built index), `traverse()` (1–3 hops, clamped, cycle-safe).
- ✅ CLI: `python -m bible references "John 3:16" [--hops N] [--min-votes V]
  [--direction out|in|both] [--json]`
- ✅ Smoke test: John 3:16's top outgoing edge is Romans 5:8 (871 votes);
  Genesis 1:1's top hop-2 edge is John 1:1 (304 votes).

### Milestone 5 — packaging + sister-script tests + docs (~99% shipped as of 2026-09-09, v0.5.0)

- ✅ Sister-script tests in `tests/run_all.py` — **38 tests, all passing.**
  No pytest dependency (ADR-001, ADR-005). Unicode/Windows console-safe.
  Run via `python3 tests/run_all.py`.
- ✅ `docs/design-decisions.md` — eight ADRs capturing architectural
  decisions through ADR-008 (openbible.info cross-references).
- ✅ `docs/evaluation.md` — retrieval-quality metrics per milestone,
  with active BM25 evaluation benchmark targets.
- ✅ `docs/phase3-scope-quran.md` — Phase 3 scout document for Quran
  as the pilot second tradition.
- ✅ CI workflow (`.github/workflows/ci.yml`) — matrix testing across
  Ubuntu and Windows on Python 3.10–3.13.
- ✅ README quickstart updated with canonical `python -m bible parallel`,
  `python -m bible search`, and `python -m bible references`.
- ✅ `bible-query.py` removed (was legacy deprecation from v0.2.0; fully
  superseded by `python -m bible` since v0.3.0). Milestone 5 closeout.

### Daily note template

```
# YYYY-MM-DD — Milestone N: title

## Done
- ...

## Blocked
- ...

## Tomorrow
- ...

## Decisions made
- ... (these go into the HANDOFF.md "Decisions" section when significant)
```

---

## 6. Repository layout (target)

```
bible-llm-reference/
├── HANDOFF.md                     # this file
# (agents.md absorbed into HANDOFF.md §11 — no separate file)
├── COUNCIL.md                     # governance constitution (short stub)
├── README.md                      # user-facing
├── LICENSE                        # MIT (added 2026-07-31)
├── pyproject.toml                 # packaging
├── .gitignore
├── notes/
│   └── YYYY-MM-DD.md              # daily journal
├── kjv.json                       # do not move
├── translations/
│   └── *.json                     # do not move
├── strongs_data/
│   └── hebrew/, greek/            # do not move
├── bible/                         # new Python package (target)
│   ├── __init__.py
│   ├── corpus.py                  # Load translations, schema check
│   ├── lookup.py                  # Book → Chapter → Verse accessor
│   ├── parallel.py                # Cross-translation parallel view
│   ├── strongs.py                 # Strong's number → lexicon entry
│   ├── verse_to_strongs.py        # KJV verse → word-level tags
│   ├── search.py                  # BM25 baseline
│   ├── embed.py                   # Optional embeddings wrapper
│   ├── cli.py                     # `python -m bible ...` entry point
│   └── references.py              # Cross-reference engine (Milestone 4)
├── convert_strongs_to_json.py     # existing (Grok upgrade)
├── make_flat_training.py          # existing (Grok upgrade)
├── # bible-query.py                # REMOVED in v0.5.0 — see ADR-004
├── data/                          # target layout (post-Milestone 1)
│   ├── traditions/
│   │   ├── christian/             # the 13 existing translations
│   │   ├── quran/                 # Phase 3
│   │   └── ...
│   ├── lexicons/
│   │   ├── strongs/               # existing (relocated from strongs_data/)
│   │   ├── lane/                  # Phase 3
│   │   └── ...
│   └── adapters/                  # thin per-tradition shims
│       ├── christian.py
│       ├── quran.py
│       └── ...
├── tests/
│   ├── test_corpus.py             # sister-script style
│   ├── test_lookup.py
│   ├── test_parallel.py
│   ├── test_strongs.py
│   ├── test_search.py
│   └── test_references.py
└── docs/
    ├── data-schema.md             # Authoritative schema doc (parallel-structure examples)
    ├── design-decisions.md        # ADRs
    ├── evaluation.md              # How we measure retrieval quality
    └── governance/
        ├── council-design.md      # Long-form Council spec
        ├── verdicts/              # Council verdicts (one file per verdict)
        └── controversies/         # Controversy Register
```

---

## 7. Conventions

### 7.1 Data layer constraint (all-traditions-capable)

The Christian Bible is the first shipped corpus, not the only target
tradition. The Phase 1 data layer must enforce:

- **Schema flexibility.** Every tradition has a different canonical
  structure (Christian Bible: book → chapter → verse; Quran: surah
  → ayah; Vedas: mandala → sukta → mantra; Torah: parasha → aliya;
  etc.). The schema must accept the Christian pattern today and the
  others as configuration, not refactor.
- **Citation format flexibility.** "Genesis 1:1" is the Christian
  citation. Other traditions have their own canonical citations.
  The API surface must accept and produce tradition-appropriate
  formats without code changes.
- **Lexicon pluggability.** Strong's is the Christian / Hebrew /
  Greek lexicon. Other traditions need their own (Brown-Driver-
  Briggs for Hebrew, Lane's for Arabic, Monier-Williams for Sanskrit,
  etc.). The lexicon surface must accept tradition-specific lexica
  as plugins.
- **Cross-reference abstraction.** When Phase 3 ships, "find verses
  about forgiveness" must work across traditions, not just within
  Christianity. The cross-reference API must be tradition-agnostic.

This is the only design constraint Phase 1 carries for Phase 3.
Everything else can be refactored later; the data contract cannot.

See `docs/data-schema.md` for the parallel-structure examples that
make this concrete.

### 7.2 Daily cadence
- Work daily, even if it's small. A typo fix counts as a daily commit.
- Each day ships a `notes/YYYY-MM-DD.md` file with the four sections
  (Done / Blocked / Tomorrow / Decisions). The note is the artifact
  even if the code isn't.
- Push daily. Don't sit on local commits.

### 7.3 Commit format
- Conventional Commits: `feat(scope):`, `fix(scope):`, `chore:`,
  `docs:`
- One logical change per commit.
- Reference README / HANDOFF.md / COUNCIL.md sections in the body
  when relevant.

### 7.4 Code style
- Python 3.11+ (matches the WSL environment)
- Stdlib-only where possible. The existing code (`bible/` package,
  `convert_strongs_to_json.py`, `make_flat_training.py`,
  `scripts/ingest_cross_references.py`) is stdlib-only. Adding
  numpy/sentence-transformers/etc. is a milestone-3B decision, not
  a default.
- Type hints on public functions
- Docstrings on modules
- One file per concern (don't bloat `bible/__init__.py`)
- No AI/ML calls in the runtime beyond what's explicitly designed in
  (this is a deterministic reference tool, not a chat surface)

### 7.5 Data discipline
- Raw corpus files are read-only. If you need a derived index, build
  it at runtime and cache it in `~/.cache/bible-llm-reference/` (NOT
  in the repo).
- No real-time API calls (Bolls Bible API) at runtime. The data is
  committed. If a translation is missing, add it via a one-shot
  ingestion script that commits the JSON.
- Strong's license is CC-BY-SA. Anything derived from it stays under
  the same license if distributed. Cite in the README.

### 7.6 Auth / secrets
- No secrets in this repo. The Bolls Bible API was used once for the
  initial commit; no API key required. If you need one later (e.g.,
  for a hosted embedding model), follow the canonical pattern:
  read from `~/.hermes/.env` via shell redirection, never paste
  values in chat.

### 7.7 Phase 1 compute decisions
- Local inference: sentence-transformers (CPU) is fine for small
  corpora. ~80MB.
- Hosted inference: NVIDIA NIM with `NVIDIA_API_KEY` from
  `~/.hermes/.env` for any model too large for local.
- No model training in Phase 1. (Phase 2 is distill-only; compute
  TBD.)

### 7.8 Governance
- Project-level governance lives in `COUNCIL.md`. It is co-equal
  with this document, not subordinate.
- Contributors should read `COUNCIL.md` §3 (when the council forms)
  and `docs/governance/council-design.md` §2 (agent roster) before
  submitting a PR that touches doctrinal claims, model behavior, or
  scope expansion.
- The Council itself is a single-contributor body until either Phase 2
  lands or a second contributor joins. The structure is in place for
  when a real board forms.

---

## 8. Pending decisions (do not act without dad)

1. **Embedding model for semantic search (Milestone 3B).** Local
   sentence-transformers vs. hosted NVIDIA NIM. Defer to Milestone 3B.
2. **Phase 2 base model.** Llama 3 / Mistral / Qwen / something
   smaller. Defer to Phase 2.
3. **README refresh.** The current README frames the project as the
   "Abrahamic / Christian slice of the Religion & Spirituality AI"
   (per the Grok upgrade). The broader vision is in `COUNCIL.md`.
   A README rewrite is not urgent; do it after Milestone 1 so the
   new framing is grounded in shipped code.
4. (Resolved.) Cross-reference dataset source: openbible.info via
   scrollmapper mirror, CC-BY 4.0 (ADR-008, 2026-09-09). See
   `docs/data-schema.md` and `data/references/README.md`.
5. (Resolved.) The original `agents.md` had a malformed code block
   in the quick-integration example. That file was absorbed into §11
   of this file, and the Python integration example was removed
   (it was documentation noise, not a contract surface).

---

## 9. Companion docs

- (the runtime contract for any agent using this data is §11 of
  this file — co-equal with the rest of the handoff)
- `COUNCIL.md` — governance constitution (short stub).
- `docs/governance/council-design.md` — long-form Council spec.
- `docs/data-schema.md` — parallel-structure schema examples.
- `README.md` — user-facing.

In `~/projects/llm-from-scratch`:
- The Karpathy-style "build a GPT from scratch" workshop. Use as a
  reference when Phase 2 lands. Not part of this repo's runtime.

---

## 10. Quick orientation for the next agent

If you have 5 minutes:
1. Read `README.md` — what's shipped
2. Read this file's §1–§4 — vision, success state, what's in the repo
3. Read `notes/<today>.md` — where the last worker left off
4. Read §11 below — the runtime contract for any agent using this data
5. Skim `COUNCIL.md` §3 — when the council forms (current state:
   single-contributor body under the principles)
6. Skim `docs/data-schema.md` §6 — the cross-tradition summary table
   so you know what the data layer is designed to scale toward

If you have 30 minutes, add:
7. Read `bible/lookup.py` and `bible/parallel.py` — the retrieval primitives
8. Run `python3 -m bible parallel "John 3:16" --strongs` and trace what it does
9. Read §11 below — the runtime contract for any agent using this data
   (citation rules, Strong's policy, no-anthropomorphizing)
10. Read `docs/governance/council-design.md` §2 — the target agent
    roster for Phase 2 (not yet implemented; don't code against it
    as if it were live)

If you have 2 hours, also:
11. Read `strongs_data/hebrew/strongs-hebrew-dictionary.js` first
    50 lines — to understand the Strong's data shape
12. Read the Bolls Bible API docs (the data source) — understand
    what fields are available so future ingestion is principled
13. Read `docs/data-schema.md` end-to-end — the schema design that
    `bible/lookup.py` should converge toward

If you're about to write code, also:
14. Re-read §5 (milestones) and §7 (conventions)
15. Update `notes/<today>.md` with what you did — even if it's one
    line

If you're picking up `llm-from-scratch` for Phase 2 reference: that's
a separate repo. Don't conflate.

---

## 11. Runtime contract for any agent using this data

> This section was previously a separate `agents.md` file. It is
> absorbed here as the runtime contract that binds any agent
> (whether or not the Council has formed; whether the user is the
> project owner or a downstream consumer). The contract is the
> floor; the Council's role is to evolve the contract over time.
> The file `agents.md` no longer exists; the contract is canonical
> here.
>
> **Audience:** any agent that uses this data, including the
> `bible/` CLI, future Council-routed agents, and downstream
> applications that consume the dataset.

### 11.1 Council agents served by this repo (Abrahamic / Christian slice)

| Council Agent          | How this repo is used                                      |
|------------------------|------------------------------------------------------------|
| abrahamic_guardian     | Primary retrieval source for all Protestant / Catholic / Orthodox queries |
| historian_archivist    | Exact verse + Strong's provenance                          |
| comparative_scholar    | Parallel passage lookup across versions                    |
| ethicist_mediator      | Hard texts kept in full context (no soft-pedaling)         |

The full 10-agent roster (when the Council forms) is in
`docs/governance/council-design.md` §2. This repo serves the four
agents above; the other six are out of scope until Phase 3 adds
non-Abrahamic corpora.

### 11.2 Runtime contract (the five rules)

1. **Always cite exact reference + translation.** Every claim
   grounded in a text must carry the citation (book/chapter/verse
   or equivalent) and the translation source. No floating claims.
2. **When Strong's is available, surface lemma + short gloss.**
   For Hebrew and Greek words, include the lemma (original word)
   and a brief gloss in line with the claim. Don't make the user
   look it up separately.
3. **Never invent verses or claim personal revelation.** Cite
   only verses that exist in the source corpus. Never speak as
   if reporting a personal spiritual experience or revelation.
4. **Present internal diversity when relevant.** A tradition is
   internally diverse. When the question touches a contested or
   denomination-specific point, surface that diversity (Catholic vs.
   Protestant readings, manuscript traditions, etc.) rather than
   collapsing to one position.
5. **Output is always "structured reference text", never "I am
   speaking as Scripture".** The system outputs facts about the
   text, formatted for the user. It does not impersonate the text,
   a religious figure, or a spiritual authority.

### 11.3 Pointer for downstream consumers

If you fork this repo for the upstream Religion & Spirituality AI
project, link it under the Abrahamic section of your `COUNCIL.md`:

```markdown
Data source: https://github.com/prive8/bible-llm-reference
Use `python -m bible parallel|strongs|search|references` (the bible/ package CLI).
```
