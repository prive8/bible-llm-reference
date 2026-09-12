# Bible LLM Reference

[![CI](https://github.com/prive8/bible-llm-reference/actions/workflows/ci.yml/badge.svg)](https://github.com/prive8/bible-llm-reference/actions)

A public-domain Bible dataset and reference tool for LLM training, retrieval, and research. This repository is the **canonical data + retrieval substrate** for the Abrahamic / Christian slice of the larger Religion & Spirituality AI project.

> **Read first:** if you're an AI agent or new contributor, start with
> [`HANDOFF.md`](./HANDOFF.md). It captures the project's vision,
> current state, conventions, and the milestone roadmap.
> [`COUNCIL.md`](./COUNCIL.md) is the constituted governance
> constitution (v0.4 — active single-contributor body, project owner
> as acting chair).
> [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) is the contract any
> downstream agent must follow.

---

## What this is

A structured reference tool over the **Abrahamic scriptural canon** —
13 Bible translations + Strong's Hebrew/Greek lexicon, 6 Quran editions,
the full Tanakh (Torah + Nevi'im + Ketuvim) in Hebrew-with-nikkud and
modernized JPS 1917 English — paired with BM25/semantic/hybrid
retrieval, 605K cross-references, and a strict runtime contract for any
downstream agent.

Built for:

- **LLM training pipelines** — corpus prep, JSONL export
- **RAG / retrieval workflows** — exact-reference lookup, keyword search, semantic parallels across **three traditions** (Christianity, Islam, Judaism)
- **Scholarly research** — parallel passage lookup across translations and traditions, original-language gloss, citation-graph traversal
- **Local-first inference** — base runtime is 100% stdlib; OpenRouter/NIM are available but optional
- **Front-end substrate** — the same CLI is the substrate for the planned Reader / Scholar / Comparative web UIs (see `docs/audience-similarities.md`)

**Not a chatbot.** This is a structured reference tool. Every output is grounded in a citation. See [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) for the contract that governs any agent using this data — five rules including *never impersonate Scripture* and *never paraphrase citations*.

---

## Highlights

- **66K indexed passages** across three traditions:
  - **Bible (Christianity)** — 37K verses in 13 translations: KJV (with Strong's tags inline), YLT, WEB, GNV, DRB, RSV, LUT, SYNOD, RV1960, CUV, UKRK, TISCH, LXX, WLCa
  - **Quran (Islam)** — 6K verses in 6 editions: Saheeh International, Yusuf Ali, Pickthall, Mufti Taqi Usmani, Arberry, Uthmani Arabic Hafs
  - **Tanakh (Judaism)** — 23K verses across all 39 books (Torah + Nevi'im + Ketuvim), 2 editions: Modernized JPS 1917 (English, CC-BY) and Hebrew-with-nikkud (Public Domain via Sefaria)
- **Strong's Concordance** for Hebrew (H1–H8674) and Greek (G1–G5624), via Open Scriptures
- **Exact reference parsing** across all three traditions — `John 3:16`, ranges (`John 3:16-18`), abbreviations (`1 Cor`, `Ps`, `jn`), Hebrew-with-nikkud aliases (`בְּרֵאשִׁית 1:1`), Roman-numeral prefixes (`I Samuel`)
- **Parallel view** across translations and editions, with optional Strong's enrichment and JSON output
- **Okapi BM25 keyword search** — multilingual (Latin, Hebrew, Arabic, Greek, Cyrillic, CJK), diacritic-insensitive, translation-pluggable
- **Semantic search** — local `sentence-transformers/all-MiniLM-L6-v2` by default (free, offline); OpenRouter and NIM backends available with API keys
- **Hybrid search** — BM25 + semantic fusion (default weight 0.1/0.7, tuned to maximize recall@10 in v0.10.0)
- **Cross-reference engine** — 605K+ edges from openbible.info (CC-BY 4.0), with outgoing, reciprocal, and 1–3 hop traversal
- **Eval harness** — 33-query benchmark with recall@K / MRR / nDCG metrics and CI threshold gate
- **JSON output** on every command for downstream pipelines
- **Base runtime 100% local, stdlib only** — optional embedder deps via `pip install -e ".[embeddings]"`

---

## Quick start

```bash
# Clone
git clone https://github.com/prive8/bible-llm-reference.git
cd bible-llm-reference

# Multi-translation parallel lookup
python3 -m bible parallel "John 3:16"                  # all 14 translations
python3 -m bible parallel "Genesis 1:1" --strongs      # + Strong's enrichment
python3 -m bible parallel "Genesis 1:1" --json        # JSON for pipelines
python3 -m bible parallel "John 3:16" -t WEB,YLT,RSV   # limit translations

# Strong's concordance
python3 -m bible strongs H1254                  # look up a number
python3 -m bible strongs "Genesis 1:1"          # all Strong's in a verse

# Okapi BM25 keyword search (multilingual)
python3 -m bible search "faith without works" -n 5 --strongs
python3 -m bible search "light" -t WEB -n 3 --json
python3 -m bible search "ברא" -t WLCa --limit 3 # Hebrew unpointed

# Semantic search (Milestone 3B; default = local MiniLM, free, offline)
python3 -m bible semantic "finding peace in suffering"
# Alternate backends (require API keys):
#   --backend openrouter  (needs credit at https://openrouter.ai/settings/credits)
#   --backend nim         (needs NVIDIA_API_KEY; ~$1.20 per full index build)
python3 -m bible semantic "verses about mercy" --tradition all --json

# Hybrid search — BM25 + semantic fusion (Milestone 3C; requires local index)
python3 -m bible hybrid "comfort in grief" --bm25-weight 0.5 --top-k 10

# Retrieval evaluation (Milestone 3C+ baseline; ~3 min on CPU)
python3 scripts/run_eval.py          # report
python3 scripts/run_eval.py --csv /tmp/eval.csv  # per-query CSV

# Cross-references (openbible.info, CC-BY 4.0)
python3 -m bible references "John 3:16"                  # outgoing edges
python3 -m bible references "John 3:16" --direction in   # reciprocal
python3 -m bible references "Genesis 1:1" --hops 2       # multi-hop expansion
python3 -m bible references "John 3:16" --min-votes 50 --json

# Quran multi-translation lookup (Phase 3.1 pilot tradition)
python3 -m bible quran "Al-Baqarah 2:255"                # Arabic Uthmani + Saheeh
python3 -m bible quran "2:255" -t uthmani,saheeh-international,yusuf-ali
python3 -m bible quran "Ayat al-Kursi" --json            # named verses + JSON

# Semantic vector search (Milestone 3B)
python3 -m bible semantic "finding peace in suffering"
python3 -m bible semantic "verses about mercy" --tradition all --json

# Generate a flat JSONL for embedding / training
python3 make_flat_training.py              # Output: kjv_training.jsonl

# Convert Strong's .js files to clean JSON (faster startup)
python3 convert_strongs_to_json.py

# Run the sister-script test suite (83 tests, stdlib-only)
python3 tests/run_all.py

# Evaluate retrieval quality against the 33-query benchmark
python3 scripts/run_eval.py            # ~3 min on CPU with local index; full report
python3 scripts/run_eval.py --csv /tmp/eval.csv  # per-query CSV for analysis
```

### How good is the search?

Baseline numbers from the v0.10.0 eval harness (33 queries, 179 expected
verses across Bible + Quran Saheeh International):

| Path | Recall@10 | MRR | nDCG@10 |
|------|----------|-----|---------|
| BM25 | 0.093 | 0.030 | 0.068 |
| **Semantic** | **0.279** | **0.165** | **0.222** |
| **Hybrid** (default 0.1/0.7) | 0.258 | 0.162 | 0.219 |

**Semantic is 3× better than BM25 on recall.** This is the headline finding.

**Methodological note:** The v0.9.0 Semantic recall@10 (0.279) is a *benchmark
expansion* result, not a model improvement over v0.8.0. The first version of
the benchmark had 105 unique citations; the second has 165. The v0.8.0
model run against the v0.9.0 benchmark would score ~0.081 (the same number
v0.8.0 logged, just against a stricter yardstick). **Always compare
like-for-like benchmarks across versions.** Full methodology and follow-on
tasks in [`docs/evaluation.md`](./docs/evaluation.md).

### OpenRouter vs local — verified in v0.15.0 (ADR-015)

After credits were added in 2026-09-11, the same 33-query benchmark was
run against the OpenRouter `text-embedding-3-small` embedder (1536-d,
$0.10/full-corpus index build):

| Embedder | dim | Recall@K | MRR | nDCG@K | Primary@1 | q/s |
|----------|-----|----------|-----|--------|-----------|-----|
| **Local** `all-MiniLM-L6-v2` | 384 | **0.279** | 0.165 | **0.222** | 0.151 | **0.3** |
| OpenRouter `text-embedding-3-small` | 1536 | 0.189 | **0.199** | 0.184 | 0.121 | 0.1 |

**Local wins on recall@K (+47%), nDCG@K (+21%), and throughput (0.3 q/s).**
Local remains the production embedder per ADR-001. OpenRouter path
remains available via `scripts/index_embeddings.py --backend openrouter`
for any future need.

---

## Runtime contract

If you're building an agent that consumes this dataset, read
[`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) — five rules (always cite,
surface Strong's lemma + gloss, never invent verses, surface internal
diversity, never impersonate Scripture) that bind any consumer of this
data. Extracted from `HANDOFF.md` §11 in v0.10.0 so consumers don't
have to scroll past project archaeology to find the rules.

### As a Python module

```python
import json
from pathlib import Path

# Load the canonical KJV
bible = json.loads(Path("kjv.json").read_text(encoding="utf-8"))
genesis_1_1 = bible["books"][0]["chapters"][0]["verses"][0]
print(genesis_1_1["text"])
# "In the beginning God created the heaven and the earth."
```

```python
# Strong's lookup
from bible.lookup import lookup_strongs
entry = lookup_strongs("H1254")  # בָּרָא bara' — "to create"
print(entry["strongs_def"][:120])

# Cross-references
from bible.references import get_references
for edge in get_references("John 3:16", min_votes=50)[:5]:
    print(f"  [{edge['votes']:>3}] → {edge['to']}")
```

---

## Project structure

```
bible-llm-reference/
├── HANDOFF.md                          # engineering handoff (vision, milestones, conventions)
├── COUNCIL.md                          # governance constitution (v0.4, constituted single-contributor body)
├── RUNTIME_CONTRACT.md                 # 5 rules binding any consumer agent (v0.10.0)
├── README.md                           # this file
├── LICENSE                             # MIT (code)
├── CHANGELOG.md                        # public API / data changes
├── CONTRIBUTING.md                     # how to contribute
├── SECURITY.md                         # reporting security issues
├── pyproject.toml                      # packaging
│
├── bible/                              # the bible package (Python 3.9+, stdlib-only)
│   ├── __init__.py
│   ├── __main__.py                     # CLI dispatcher
│   ├── lookup.py                       # data loading + reference parser + book aliases
│   ├── parallel.py                     # `bible parallel` — multi-translation view
│   ├── strongs.py                      # `bible strongs` — H/G lexicon lookup
│   ├── search.py                       # `bible search` — Okapi BM25 keyword search (ADR-007)
│   └── references.py                   # `bible references` — cross-reference engine (ADR-008)
│
├── convert_strongs_to_json.py          # Strong's .js → JSON
├── make_flat_training.py               # KJV → JSONL for training
├── normalize.py                        # JSON normalization (one translation)
├── normalize_all.py                    # batch normalizer
│
├── kjv.json                            # King James Version + Strong's tags
├── translations/                       # 13 additional translations
├── strongs_data/                       # Hebrew + Greek lexicon (Open Scriptures)
│
├── data/
│   ├── quran/                          # Phase 3.1 — 6 editions (saheeh-international, yusuf-ali, pickthall, mufti-taqi-usmani, arberry, uthmani)
│   │   ├── README.md
│   │   └── *.json
│   ├── torah/                          # Phase 3.2 — 2 editions (jps1917-modernized CC-BY, hebrew-nikkud Public Domain)
│   │   ├── README.md
│   │   └── *.json
│   ├── tanakh/                          # Phase 3.3 — 2 editions covering full 39-book canon (Torah + Nevi'im + Ketuvim)
│   │   ├── README.md
│   │   └── *.json                       # jps1917-modernized, hebrew-nikkud
│   └── references/                     # openbible.info cross-references (CC-BY 4.0)
│       ├── cross_references.txt        # raw 8 MB TSV snapshot
│       ├── cross_references.json       # normalized 19 MB, keyed by canonical verse
│       └── README.md                   # license + schema + refresh instructions
│
├── scripts/
│   └── ingest_cross_references.py      # one-shot ingest TSV → JSON
│
├── docs/
│   ├── data-schema.md                  # parallel-structure schema for multi-tradition support
│   ├── design-decisions.md             # ADRs (architectural decisions)
│   ├── evaluation.md                   # retrieval-quality metrics per milestone
│   ├── phase3-scope-quran.md           # Phase 3.1 scope doc — Quran as pilot tradition
│   └── governance/
│       ├── council-design.md           # long-form Council spec
│       ├── verdicts/                   # (Council verdicts — when the Council forms)
│       └── controversies/              # (Controversy Register — when the Council forms)
│
├── tests/
│   └── run_all.py                      # 38 sister-script tests, stdlib-only
│
└── .github/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Data sources

| Source | License | Notes |
|--------|---------|-------|
| KJV (1769, with Strong's) | Public domain | via Bolls Bible API |
| 13 additional translations | Public domain / fair use | via Bolls Bible API |
| Strong's Hebrew (H1–H8674) | CC-BY-SA | via Open Scriptures |
| Strong's Greek (G1–G5624) | CC-BY-SA | via Open Scriptures |
| Cross-references (605K edges) | CC-BY 4.0 | via openbible.info (mirror: scrollmapper/bible_databases) |

**License propagation:**
- **Strong's** is CC-BY-SA — any artifact that incorporates the lexicon must carry the same license when distributed.
- **Cross-references** are CC-BY 4.0 — attribution to openbible.info required when distributed.
- The rest of the codebase is MIT.

Verify licensing for your specific use case before building commercial applications.

---

## Project vision

The full vision (per [`COUNCIL.md`](./COUNCIL.md) §1) is "every living and historical human religion, spiritual path, indigenous tradition, new religious movement, and non-theistic worldview." Christian Bible is the first shippable rung; the Abrahamic slice is the next.

### Phase 1 — retrieval-only study tool ✅ SHIPPED (v0.5.0)

A user can ask "What does Genesis 1:1 say across translations?" and see all 13 Bible translations side-by-side, with Hebrew lemma + Strong's number for בָּרָא (H1254 bara', "to create") expanded, and Westminster Leningrad Codex original Hebrew next to English translations. They can find verses by exact reference, by keyword search (BM25, multilingual), by cross-reference (outgoing, reciprocal, or N-hop), and they can layer Strong's enrichment onto any result.

Milestones:

- ✅ **M1** — multi-translation lookup (`python -m bible parallel`)
- ✅ **M2** — Strong's integration (`python -m bible strongs`)
- ✅ **M3A** — BM25 keyword search (`python -m bible search`)
- ✅ **M3B** — semantic search (default = local `sentence-transformers/all-MiniLM-L6-v2`)
- ✅ **M3C** — hybrid BM25/semantic fusion with recall@10 baseline 0.279 / eval-regression CI gate
- ✅ **M4** — cross-reference engine (`python -m bible references`)
- ✅ **M5** — packaging + sister-script tests + docs

### Phase 2 — generative voice (deferred)

A tool that takes a question and writes a response in the voice of the tradition — the way a pastor would cite Romans, or a rabbi would cite Rashi on Genesis, or a qari would cite tafsir on a verse. Always grounded in the corpus, always with citations, never inventing doctrine. **Distill-only.** Compute decision deferred until the data shape is final. The runtime contract in v0.10.0 explicitly bounds what Phase 2 can produce: caption generation, translation comparison summarization, and cross-reference type classification are allowed; pure chat is not.

### Phase 3 — multi-tradition (Abrahamic slice shipped; non-Abrahamic pending)

Add Torah, Talmud, Quran, Hadith, Vedas, Upanishads, Bhagavad Gita, Dhammapada, Tao Te Ching, Book of Mormon, etc. Each tradition gets parallel structure (same canonical schema, same citation format, same cross-reference API, tradition-specific lexicon). The Phase 1 data layer was designed so this is a **config change, not a code rebuild**.

**Phase 3.1 pilot: Quran (shipped in v0.6.0).** 6 editions in `data/quran/` (Saheeh International, Yusuf Ali, Pickthall, Mufti Taqi Usmani, Arberry, and Arabic Uthmani Hafs) via [`fawazahmed0/quran-api`](https://github.com/fawazahmed0/quran-api) (Unlicense). Accessible via `python3 -m bible quran` with citation parsing and parallel view. See [`docs/phase3-scope-quran.md`](./docs/phase3-scope-quran.md) and ADR-009.

**Phase 3.2: Torah / Five Books of Moses (shipped in v0.11.0).** 2 editions in `data/torah/` — Modernized Tanakh based on JPS 1917 (English, CC-BY, Adam Cohn) and תנ״ך עם ניקוד (Hebrew with vowel points, Public Domain via tanach.us) — sourced from the Sefaria API. 187 chapters, 5,852 verses. Accessible via `python -m bible torah "Genesis 1:1"` with citation parsing supporting canonical names, short Latin aliases, transliterations, and Hebrew-with-nikkud. See [`docs/phase3-scope-torah.md`](./docs/phase3-scope-torah.md).

**Phase 3.3: Full Tanakh (Torah + Nevi'im + Ketuvim, shipped in v0.14.0).** 2 editions in `data/tanakh/` — same Modernized JPS 1917 (English, CC-BY) and תנ״ך עם ניקוד (Hebrew with vowel points, Public Domain) as the Torah phase — sourced from the Sefaria API. 39 books, ~927 chapters, ~23,000 verses. Accessible via `python -m bible tanakh "Isaiah 53:5"` with full alias support (canonical English, short Latin, transliteration, Hebrew-with-nikkud, Roman-numeral prefix). See [`docs/phase3-scope-tanakh.md`](./docs/phase3-scope-tanakh.md).

**Phase 3.4: OpenRouter-hosted embedding backend (shipped in v0.13.0; benchmarked in v0.15.0).** Added `OpenRouterEmbedder` as a fourth pluggable embedder backend alongside local, NIM, and mock. The full-corpus OpenRouter index was built in v0.15.0 ($0.11 actual cost). Per the v0.15.0 cross-embedder benchmark documented in [`ADR-015`](./docs/design-decisions.md#adr-015--openrouter-vs-local-recall-comparison-local-wins-0279-vs-0189) and [`docs/evaluation.md`](./docs/evaluation.md#cross-embedder-comparison-2026-09-11-v0150-follow-up), **local remains the production embedder** (recall@K=0.279 vs OpenRouter 0.189). The OpenRouter path is wired and available for any future swap-in, but the local-first principle (ADR-001) is vindicated by measurement.

### Phase 4+ — non-Abrahamic corpora + front-end (planning)

- **Reader Layer 1** front-end (Bundle 9 in `audience-similarities.md`): thin FastAPI + HTMX web UI wrapping the CLI. Defaults to a no-AI-sermon reading mode. Estimated 1 week of work.
- **Concordance** (Bundle 1): Strong's-indexed "every occurrence of lemma X" search across Bible + Tanakh. 1-2 days.
- **Non-Abrahamic corpora** (Vedas, Upanishads, Dhammapada, Tao Te Ching) — roadmap items per `audience-similarities.md` P2 tier. Each adds another tradition with the same canonical-schema discipline.
- **Typed cross-reference edges** (Bundle 7): the current 605K openbible.info edges have votes but no type labels. A typed dataset would enable Phase 2 inference on cross-reference classification.

Read more in [`HANDOFF.md` §1–§2](./HANDOFF.md), [`docs/audience-similarities.md`](./docs/audience-similarities.md), and the curated daily notes under `notes/`.

---

## Governance

The project has a **constituted governance body** ([`COUNCIL.md`](./COUNCIL.md),
v0.4 since 2026-09-10). The constitution is in force and binds all
project decisions, including the seven principles in §2 (neutral
across traditions, primary-source-first, no impersonation, etc.) and
the runtime contract in [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md).

**Current form:** single-contributor body (the project owner,
"father", acting chair). The acting chair makes all decisions subject
to the principles and the runtime contract, and has no authority to
override either. Decisions are recorded in daily notes
(`notes/YYYY-MM-DD.md`).

**Target form:** full multi-agent Council with the agent roster in
[`docs/governance/council-design.md`](./docs/governance/council-design.md).
That convenes when either (a) a second contributor joins, or (b) the
project enters Phase 2 (generative voice fine-tune). The expansion to
multi-member form is a *chamber expansion*, not a re-ratification —
the constitution, the runtime contract, and all prior decisions
transfer to the full Council without re-approval.

If you're a new contributor, read `COUNCIL.md` first (it's the
shortest), then `HANDOFF.md`. They are co-equal.

The runtime contract that any agent consuming this data must follow
lives in [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) (extracted
from `HANDOFF.md` §11 in v0.10.0 so downstream consumers don't have
to scroll past project archaeology to find the rules).

Architectural decisions are tracked as ADRs in [`docs/design-decisions.md`](./docs/design-decisions.md). Currently fifteen ADRs covering stdlib-only baseline, Strong's sourcing, hybrid fusion defaults, NIM + OpenRouter pluggable embedder backends, Quran / Torah / Tanakh / OpenRouter benchmark decisions, and the local-first reaffirmed decision (ADR-014, ADR-015).

---

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md). Short version: read [`HANDOFF.md`](./HANDOFF.md) §1–§4 and §7 (conventions), follow the runtime contract (§11), send a PR. Sister-script tests run via `python3 tests/run_all.py` — should print `N passed, 0 failed` before you push.

## Security

See [`SECURITY.md`](./SECURITY.md). This is a public repo with no secrets in the codebase. If you find a security issue, report via the address in `SECURITY.md` — do not open a public issue.

## License

**Code:** MIT. See [`LICENSE`](./LICENSE).

**Data:** Each source carries its own license. See the [Data sources](#data-sources) table. Public domain, CC-BY-SA, or CC-BY 4.0 — verify with your jurisdiction before commercial use.

## Use cases

Six user personas drive the front-end design (see [`docs/use-cases.md`](./docs/use-cases.md) for the full write-up, [`docs/audience_expectations.md`](./docs/audience_expectations.md) for the building-reference version, and [`docs/audience-similarities.md`](./docs/audience-similarities.md) for the cross-persona roadmap):

- **Academic** — original-language + critical apparatus + reproducible queries (the biblical studies scholar persona, Persona 1)
- **Secular seeker** — easy entry, cross-tradition comparison, plain-English summaries clearly marked as such (the wisdom-seeker persona, Persona 2)
- **Comparative researcher** — cross-tradition parallel display, source transparency, non-Abrahamic primary corpora (the religious-studies researcher persona, Persona 3)
- **Lay-faithful reader** (Persona 4 — *the load-bearing persona*) — read the actual text, cross-references for study, original-language awareness with one-line gloss, *no AI sermon*. The runtime contract exists because of this persona. Sized at ~10-100× the academic audience, this is where harm-reduction from the contract pays off most.
- **AI engineer / RAG builder** (Persona 5) — clean JSON API, stable schemas, clear licenses, pluggable backends. Determines whether the project has long-term downstream impact.
- **Interfaith dialogue facilitator** (Persona 6) — mixed-audience materials; drives Phase 4+ non-Abrahamic corpus planning.

The front-end roadmap is **three layers over the same CLI backend** — Reader (default for Persona 2 + 4), Scholar (Persona 1), Comparative (Persona 3 + 6) — so each persona gets a tailored surface without rebuilding the data layer. The Council role mapping per persona lives in `docs/audience_expectations.md`.

## Related projects

- **[`prive8/llm-from-scratch`](https://github.com/prive8/llm-from-scratch)** — a Karpathy-style workshop on building a GPT from scratch. Used as a reference when Phase 2 lands.
- **[`fawazahmed0/quran-api`](https://github.com/fawazahmed0/quran-api)** — the canonical public-domain Quran source identified for Phase 3.1 (Unlicense, 492 editions).
- **[`Open Scriptures / Strong's Hebrew/Greek dictionaries`](https://github.com/openscriptures/strongs)** — the source for our Strong's Concordance (CC-BY-SA).
- **[`scrollmapper/bible_databases`](https://github.com/scrollmapper/bible_databases)** — the openbible.info cross-reference mirror we use.
- **[`Sefaria`](https://www.sefaria.org/)** — primary source for the Torah + full Tanakh JSON we ingest.

## Acknowledgments

- The **Strong's Concordance** data comes from [Open Scriptures](https://github.com/openscriptures/strongs) under CC-BY-SA.
- The **Bible translation** data is sourced from the [Bolls Bible API](https://bolls.life/api/) (free, no key required).
- The **cross-reference** data is sourced from [openbible.info](https://www.openbible.info/labs/cross-references/) under CC-BY 4.0 (mirror: [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases)).
- The runtime contract, Council design, BM25 search engine, and cross-reference engine were drafted in collaboration with the project owner and the dad-h2 / DadClaw agents over multiple sessions.
