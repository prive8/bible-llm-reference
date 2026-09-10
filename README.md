# Bible LLM Reference

[![CI](https://github.com/prive8/bible-llm-reference/actions/workflows/ci.yml/badge.svg)](https://github.com/prive8/bible-llm-reference/actions)

A public-domain Bible dataset and reference tool for LLM training, retrieval, and research. This repository is the **canonical data + retrieval substrate** for the Abrahamic / Christian slice of the larger Religion & Spirituality AI project.

> **Read first:** if you're an AI agent or new contributor, start with
> [`HANDOFF.md`](./HANDOFF.md). It captures the project's vision,
> current state, conventions, and the milestone roadmap.
> [`COUNCIL.md`](./COUNCIL.md) is the dormant governance constitution —
> see the Governance section below for what that means today.
> [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) is the contract any
> downstream agent must follow.

---

## What this is

A structured reference tool over the Christian Bible — 14 translations, Strong's Hebrew/Greek lexicon, Okapi BM25 keyword search, and 605K cross-references — that any LLM agent or RAG pipeline can query locally without cloud dependencies.

Built for:

- **LLM training pipelines** — corpus prep, JSONL export
- **RAG / retrieval workflows** — exact-reference lookup, keyword search, semantic parallels
- **Scholarly research** — parallel passage lookup across translations, original-language gloss, citation-graph traversal
- **Local-first inference** — no mandatory cloud dependency; runs offline on a laptop

**Not a chatbot.** This is a structured reference tool. Every output is grounded in a citation. See [`HANDOFF.md` §11](./HANDOFF.md#11-runtime-contract-for-any-agent-using-this-data) for the runtime contract that governs any agent using this data.

---

## Highlights

- **14 translations** in normalized JSON: KJV (with Strong's tags), YLT, WEB, GNV, DRB, RSV, LUT, SYNOD, RV1960, CUV, UKRK, TISCH, LXX, WLCa
- **Strong's Concordance** for Hebrew (H1–H8674) and Greek (G1–G5624), via Open Scriptures
- **Exact reference parsing** — `John 3:16`, ranges (`John 3:16-18`), abbreviations (`1 Cor`, `Ps`, `jn`, `1jn`)
- **Parallel view** across all translations, with optional Strong's enrichment and JSON output
- **Okapi BM25 keyword search** — multilingual (Latin, Hebrew, Greek, Cyrillic, CJK), diacritic-insensitive, translation-pluggable
- **Cross-reference engine** — 605K+ edges from openbible.info (CC-BY 4.0), with outgoing, reciprocal, and 1–3 hop traversal
- **Quran multi-tradition adapter (Phase 3.1)** — 6 editions in `data/quran/` (5 English + Uthmani Arabic), citation parsing, and parallel lookup
- **Torah adapter (Phase 3.2)** — 2 editions in `data/torah/` (Modernized JPS 1917 English CC-BY + Hebrew-with-nikkud Public Domain), citation parsing, Hebrew-with-nikkud alias support, and parallel lookup
- **JSON output** on every command for downstream pipelines
- **100% local, zero new dependencies** — stdlib only (Python 3.9+)

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

# Semantic search (Milestone 3B; auto backend = local → NIM → mock)
python3 -m bible semantic "finding peace in suffering" --backend nim  # needs NVIDIA_API_KEY
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
| Semantic | **0.279** | **0.165** | **0.222** |
| **Hybrid** (default 0.1/0.7) | **0.258** | 0.162 | **0.219** |

**Methodological note:** The v0.9.0 Semantic recall@10 (0.279) is a *benchmark
expansion* result, not a model improvement over v0.8.0. The first version of
the benchmark had 105 unique citations; the second has 165. The v0.8.0
model run against the v0.9.0 benchmark would score ~0.081 (the same number
v0.8.0 logged, just against a stricter yardstick). **Always compare
like-for-like benchmarks across versions.** Full methodology and follow-on
tasks in [`docs/evaluation.md`](./docs/evaluation.md).

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
├── COUNCIL.md                          # governance constitution (dormant until Phase 2 / 2nd contributor)
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

The full vision (per [`COUNCIL.md`](./COUNCIL.md) §1) is "every living and historical human religion, spiritual path, indigenous tradition, new religious movement, and non-theistic worldview." Christian Bible is the first shippable rung.

### Phase 1 — retrieval-only study tool ✅ SHIPPED (v0.5.0)

A user can ask "What does Genesis 1:1 say across translations?" and see all 14 translations side-by-side, with Hebrew lemma + Strong's number for בָּרָא (H1254 bara', "to create") expanded, and Westminster Leningrad Codex original Hebrew next to English translations. They can find verses by exact reference, by keyword search (BM25, multilingual), by cross-reference (outgoing, reciprocal, or N-hop), and they can layer Strong's enrichment onto any result.

Milestones:

- ✅ **M1** — multi-translation lookup (`python -m bible parallel`)
- ✅ **M2** — Strong's integration (`python -m bible strongs`)
- ✅ **M3A** — BM25 keyword search (`python -m bible search`)
- ✅ **M4** — cross-reference engine (`python -m bible references`)
- ✅ **M5** — packaging + sister-script tests + docs

### Phase 2 — generative voice (deferred)

A tool that takes a question and writes a response in the voice of the tradition — the way a pastor would cite Romans, or a rabbi would cite Rashi on Genesis, or a qari would cite tafsir on a verse. Always grounded in the corpus, always with citations, never inventing doctrine. **Distill-only.** Compute decision deferred until the data shape is final.

### Phase 3 — multi-tradition (designed, not dated)

Add Torah, Talmud, Quran, Hadith, Vedas, Upanishads, Bhagavad Gita, Dhammapada, Tao Te Ching, Book of Mormon, etc. Each tradition gets parallel structure (same canonical schema, same citation format, same cross-reference API, tradition-specific lexicon). The Phase 1 data layer is designed so this is a **config change, not a code rebuild**.

**Phase 3.1 pilot: Quran (shipped in v0.6.0).** 6 editions in `data/quran/` (Saheeh International, Yusuf Ali, Pickthall, Mufti Taqi Usmani, Arberry, and Arabic Uthmani Hafs) via [`fawazahmed0/quran-api`](https://github.com/fawazahmed0/quran-api) (Unlicense). Accessible via `python3 -m bible quran` with citation parsing and parallel view. See [`docs/phase3-scope-quran.md`](./docs/phase3-scope-quran.md) and ADR-009.

**Phase 3.2: Torah / Five Books of Moses (shipped in v0.11.0).** 2 editions in `data/torah/` — Modernized Tanakh based on JPS 1917 (English, CC-BY, Adam Cohn) and תנ״ך עם ניקוד (Hebrew with vowel points, Public Domain via tanach.us) — sourced from the Sefaria API. 187 chapters, 5,852 verses. Accessible via `python3 -m bible torah "Genesis 1:1"` with citation parsing supporting canonical names, short Latin aliases, transliterations, and Hebrew-with-nikkud. See [`docs/phase3-scope-torah.md`](./docs/phase3-scope-torah.md).

Read more in [`HANDOFF.md` §1–§2](./HANDOFF.md).

---

## Governance

The project has a **dormant** constitution ([`COUNCIL.md`](./COUNCIL.md))
that activates when either (a) a second contributor joins, or
(b) the project enters Phase 2 (generative voice fine-tune). Until
then, the project is run as a single-contributor body (the project
owner, "father") operating under the seven principles in `COUNCIL.md` §2.

The detailed Council design — agent roster, decision protocol,
evolution rules — lives in [`docs/governance/council-design.md`](./docs/governance/council-design.md)
as the *target architecture* for when the Council forms. It is not
running today.

The runtime contract that any agent consuming this data must follow
lives in [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) (extracted
from `HANDOFF.md` §11 in v0.10.0 so downstream consumers don't have
to scroll past project archaeology to find the rules).

Architectural decisions are tracked as ADRs in [`docs/design-decisions.md`](./docs/design-decisions.md). Currently twelve ADRs covering stdlib-only baseline, Strong's sourcing, hybrid fusion defaults, NIM backend, and the Quran-as-Phase-3-pilot decision.

---

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md). Short version: read [`HANDOFF.md`](./HANDOFF.md) §1–§4 and §7 (conventions), follow the runtime contract (§11), send a PR. Sister-script tests run via `python3 tests/run_all.py` — should print `N passed, 0 failed` before you push.

## Security

See [`SECURITY.md`](./SECURITY.md). This is a public repo with no secrets in the codebase. If you find a security issue, report via the address in `SECURITY.md` — do not open a public issue.

## License

**Code:** MIT. See [`LICENSE`](./LICENSE).

**Data:** Each source carries its own license. See the [Data sources](#data-sources) table. Public domain, CC-BY-SA, or CC-BY 4.0 — verify with your jurisdiction before commercial use.

## Related projects

- **[`prive8/llm-from-scratch`](https://github.com/prive8/llm-from-scratch)** — a Karpathy-style workshop on building a GPT from scratch. Used as a reference when Phase 2 lands.
- **[`fawazahmed0/quran-api`](https://github.com/fawazahmed0/quran-api)** — the canonical public-domain Quran source identified for Phase 3.1 (Unlicense, 492 editions).

## Acknowledgments

- The **Strong's Concordance** data comes from [Open Scriptures](https://github.com/openscriptures/strongs) under CC-BY-SA.
- The **Bible translation** data is sourced from the [Bolls Bible API](https://bolls.life/api/) (free, no key required).
- The **cross-reference** data is sourced from [openbible.info](https://www.openbible.info/labs/cross-references/) under CC-BY 4.0 (mirror: [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases)).
- The runtime contract, Council design, BM25 search engine, and cross-reference engine were drafted in collaboration with the project owner and the dad-h2 / DadClaw agents over multiple sessions.
