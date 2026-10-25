# Bible LLM Reference

[![CI](https://github.com/prive8/bible-llm-reference/actions/workflows/ci.yml/badge.svg)](https://github.com/prive8/bible-llm-reference/actions)

A scripture reference dataset and retrieval tool. The audience is anyone looking into scripture. The likely shape is a web reader with study help; this repository is the text, the citations, and the search underneath that reader. The goal is depth and cross-referencing over breadth. Use cases are still being defined.

The corpus today is the Christian Bible, the Quran, and the Tanakh. [`COUNCIL.md`](./COUNCIL.md) §1 records a longer multi-tradition horizon. The direction in the paragraph above is what governs current work.

> **Agents:** read this file for status, then [`AGENTS.md`](./AGENTS.md) for what to work on next. [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) binds any use of the data. [`COUNCIL.md`](./COUNCIL.md) §2 is the operating principles.

Every result is a citation. The five rules, including never impersonating Scripture, are in [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md).

---

## What is in the repo

- **66,689 indexed passages** — 37,247 Christianity, 6,236 Islam, 23,206 Judaism.
- **Bible** — 14 translations (KJV with Strong's tags at `kjv.json`, plus 13 in `translations/`).
- **Quran** — 6 editions (Saheeh International, Yusuf Ali, Pickthall, Mufti Taqi Usmani, Arberry, Uthmani Arabic Hafs).
- **Tanakh** — 39 books, two editions: modernized JPS 1917 (English, CC-BY) and Hebrew-with-nikkud. The default semantic index uses the English edition.
- **Strong's** Hebrew (H1–H8674) and Greek (G1–G5624), via Open Scriptures.
- **Cross-references** — 605K+ edges from openbible.info (CC-BY 4.0), Bible-scoped.
- **Retrieval** — Okapi BM25, local semantic search (`sentence-transformers/all-MiniLM-L6-v2`), and hybrid fusion (BM25 weight 0.1, solo weight 0.7).
- **Tradition registry** — `bible/registry.py`, canonical passage IDs, and a Bible↔Tanakh versification map (`data/versification_map.json`). `parallel` and `search` accept `--tradition`. `strongs` and `references` cover the Bible. Quran, Torah, and Tanakh also have their own commands.
- **Base runtime is stdlib.** Embeddings are an extra: `pip install -e ".[embeddings]"`. Built indexes under `data/embeddings/` are gitignored.

A web reader is the likely product shape. It is not built. Phase 2 (a generative voice) stays deferred.

---

## Quick start

```bash
git clone https://github.com/prive8/bible-llm-reference.git
cd bible-llm-reference

python3 -m bible parallel "John 3:16"                  # Bible translations
python3 -m bible parallel "Genesis 1:1" --strongs
python3 -m bible parallel "John 3:16" -t WEB,YLT,RSV
python3 -m bible parallel "Genesis 1:1" --tradition all

python3 -m bible strongs H1254
python3 -m bible search "faith without works" -n 5
python3 -m bible search "ברא" -t WLCa --limit 3

python3 -m bible semantic "finding peace in suffering"   # needs a local index
python3 -m bible hybrid "comfort in grief" -n 10

python3 -m bible references "John 3:16"
python3 -m bible references "John 3:16" --direction in
python3 -m bible references "Genesis 1:1" --hops 2

python3 -m bible quran "Al-Baqarah 2:255"
python3 -m bible torah "Genesis 1:1"
python3 -m bible tanakh "Isaiah 53:5"

python3 tests/run_all.py                                # 155 tests; expect "155 passed, 0 failed"
```

JSON output is available on the lookup commands (`--json`) for downstream pipelines.

---

## Retrieval quality and CI

Two recall@10 gates run in the `eval-regression` job on push to `main`. Pull requests run the test matrix. A cold index build is about 14 minutes on the 2-vCPU runner. The built index is cached on a content hash of the corpus files plus the indexer (`scripts/index_embeddings.py`, `bible/semantic.py`, `bible/lookup.py`, `bible/quran.py`, `bible/torah.py`, `bible/tanakh.py`). The cache key is exact, so a corpus or indexer change rebuilds. The job timeout is 60 minutes. With a cache hit, both gates together took 17.1 minutes (run `40230771370`, 2026-10-25). Docs-only pushes to `main` skip CI.

The semantic index is decoded from disk on every query, which is most of the v2 gate's ~9 minutes. Detail is in [`notes/2026-10-25-ci-eval-regression-restored.md`](./notes/2026-10-25-ci-eval-regression-restored.md).

### v1 — Christianity, historical single-corpus gate

`scripts/run_eval.py --tradition christianity`. The v1 expected citations are Bible verses. The gate is scoped to Christianity so the rest of the corpus does not dilute the score. Thresholds are the v0.10.0 Bible-only baselines minus a margin (BM25 0.093, semantic 0.279, hybrid 0.258) and were left unchanged.

| Path | Recall@10 on 2026-10-25 | Threshold |
|------|-------------------------|-----------|
| BM25 | 0.108 | 0.06 |
| Semantic | 0.282 | 0.25 |
| Hybrid | 0.273 | 0.22 |

### v2 dev — cross-tradition gate

`scripts/run_eval.py --benchmark v2 --split dev` (48 dev queries, unscoped, citations across Christianity, Tanakh, and Quran). Measured on the 66,689-passage index. These scores sit below v1 because the benchmark asks for more, across three canons. The held-out split (42 queries) is not the CI gate.

| Path | Baseline recall@10 | Threshold |
|------|--------------------|-----------|
| BM25 | 0.119 | 0.08 |
| Semantic | 0.189 | 0.15 |
| Hybrid | 0.183 | 0.14 |

The v2 semantic baseline (0.189) is a different measurement from the OpenRouter `text-embedding-3-small` recall of 0.189 on the older 33-query set (below).

### Run the gates locally

Requires a built local index (`pip install -e ".[embeddings]"`, then `python scripts/index_embeddings.py --backend local --name default`). `scripts/eval_gate.py` reads a `run_eval.py` report and fails if a path is under its threshold or missing.

```bash
python scripts/run_eval.py --paths bm25,semantic,hybrid --tradition christianity > /tmp/eval_report_v1.txt
python scripts/eval_gate.py --report /tmp/eval_report_v1.txt \
  --threshold bm25=0.06 --threshold semantic=0.25 --threshold hybrid=0.22

python scripts/run_eval.py --paths bm25,semantic,hybrid --benchmark v2 --split dev > /tmp/eval_report_v2.txt
python scripts/eval_gate.py --report /tmp/eval_report_v2.txt \
  --threshold bm25=0.08 --threshold semantic=0.15 --threshold hybrid=0.14
```

### Earlier embedder comparison (not the CI gate)

On 2026-09-11 the same 33-query set was run against OpenRouter `text-embedding-3-small`. Local `all-MiniLM-L6-v2` remained the production embedder ([ADR-015](./docs/design-decisions.md)).

| Embedder | dim | Recall@K | MRR | nDCG@K |
|----------|-----|----------|-----|--------|
| Local `all-MiniLM-L6-v2` | 384 | 0.279 | 0.165 | 0.222 |
| OpenRouter `text-embedding-3-small` | 1536 | 0.189 | 0.199 | 0.184 |

The v0.10.0 write-up of that Bible-heavy benchmark is [`docs/evaluation.md`](./docs/evaluation.md). It is the history of the v1 thresholds, not the live v2 baseline.

---

## Status and direction (2026-10-25)

**Direction.** Anyone looking into scripture. A web reader with study help is the likely shape. Depth and cross-referencing come before breadth. Use cases are still being defined. Earlier persona and front-end notes ([`docs/use-cases.md`](./docs/use-cases.md), [`docs/phase4-scope-frontend.md`](./docs/phase4-scope-frontend.md)) are background, not the current product definition.

**Where the code is.**

- Lookup, Strong's, BM25, semantic search, hybrid search, and Bible cross-references ship from the CLI.
- Quran, Torah, and Tanakh are ingested. The Judaism slice of the semantic index defaults to English `jps1917-modernized`.
- A passage model, canonical IDs, a versification map, and `--tradition` on `parallel` and `search` are in the tree (`bible/registry.py`). A further tradition still needs its own ingest and wiring; `references` and `strongs` stay on the Bible.
- The retrieval gate is green again as of run `40230771370` (both benchmarks above).
- The web reader is still ahead of the code. Generative-voice work stays deferred.
- The 2026-10-08 review is [`docs/foundation-plan.md`](./docs/foundation-plan.md). It records why the registry was built. It is not the work queue.

**Work queue.** People writing code take the next task from [`AGENTS.md`](./AGENTS.md): the fleet to-do board and [`notes/`](./notes/).

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
- The rest of the codebase is MIT ([`LICENSE`](./LICENSE)).

> **Licensing under review.** Several translations are labelled public domain / fair use (RSV, RV1960, Saheeh International, Mufti Taqi Usmani, Arberry) and are likely still under copyright. The compilation licence of the ingest sources does not cover the underlying translations. Treat those editions as **local research use only**. The inventory is [`LICENCE-AUDIT.md`](./LICENCE-AUDIT.md). The owner's decision on these five is still open.

---

## Layout

```
bible/                 CLI package (stdlib). registry, parallel, search,
                       semantic, hybrid, strongs, references, quran, torah, tanakh
scripts/run_eval.py    retrieval benchmark (v1 and v2)
scripts/eval_gate.py   recall@10 threshold gate used by CI
scripts/index_embeddings.py
tests/run_all.py       155 sister-script tests
data/                  quran, torah, tanakh, references, editions.json,
                       versification_map.json
kjv.json, translations/, strongs_data/
notes/                 session notes (Done / Blocked / Tomorrow / Decisions)
docs/                  ADRs, eval history, scope sketches, governance design
```

---

## Governance

[`COUNCIL.md`](./COUNCIL.md) (v0.4, since 2026-09-10) is in force: a single-contributor body, project owner as acting chair. The seven principles in §2 bind the project. Decisions land in `notes/`. The full multi-member Council in [`docs/governance/council-design.md`](./docs/governance/council-design.md) waits on a second contributor or Phase 2.

Architectural decisions are ADRs in [`docs/design-decisions.md`](./docs/design-decisions.md).

## Contributing

[`CONTRIBUTING.md`](./CONTRIBUTING.md). Tests: `python3 tests/run_all.py` (155 passed, 0 failed, as of 2026-10-25).

## Security

[`SECURITY.md`](./SECURITY.md). No secrets in the repo. Report security issues to the address in `SECURITY.md`.

## Related

- [`prive8/llm-from-scratch`](https://github.com/prive8/llm-from-scratch) — workshop reference if Phase 2 ever starts.
- [`fawazahmed0/quran-api`](https://github.com/fawazahmed0/quran-api) — Quran ingest source.
- [Open Scriptures Strong's](https://github.com/openscriptures/strongs) — CC-BY-SA lexicon.
- [openbible.info cross-references](https://www.openbible.info/labs/cross-references/) — CC-BY 4.0, via [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases).
- [Sefaria](https://www.sefaria.org/) — Torah and Tanakh ingest source.
- [Bolls Bible API](https://bolls.life/api/) — Bible translation ingest source.
