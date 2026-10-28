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
- **Retrieval** — Okapi BM25, semantic search (default embedder: OpenRouter `openai/text-embedding-3-large`, 3072-dim, per [ADR-016](./docs/design-decisions.md)), and hybrid fusion (BM25 weight 0.1, solo weight 0.7). The offline `all-MiniLM-L6-v2` embedder is still available as `--profile local`; it is what CI builds and gates.
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

python3 -m bible semantic "finding peace in suffering"   # needs an index; default profile is 3-large
python3 -m bible semantic "finding peace in suffering" --profile local   # offline MiniLM index
python3 -m bible hybrid "comfort in grief" -n 10
python3 -m bible hybrid "comfort in grief" --profile local -n 10

python3 -m bible references "John 3:16"
python3 -m bible references "John 3:16" --direction in
python3 -m bible references "Genesis 1:1" --hops 2

python3 -m bible quran "Al-Baqarah 2:255"
python3 -m bible torah "Genesis 1:1"
python3 -m bible tanakh "Isaiah 53:5"

python3 tests/run_all.py                                # 179 tests; expect "179 passed, 0 failed"
```

JSON output is available on the lookup commands (`--json`) for downstream pipelines.

---

## Retrieval quality and CI

**Three** recall@10 gates run in the `eval-regression` job on push to `main`: `local/v1`, `local/v2-dev`, and `local/v2-held_out`. Pull requests run the test matrix. A cold index build is about 14 minutes on the 2-vCPU runner. The built index is cached on a content hash of the corpus files plus the indexer (`scripts/index_embeddings.py`, `bible/semantic.py`, `bible/lookup.py`, `bible/quran.py`, `bible/torah.py`, `bible/tanakh.py`). The cache key is exact, so a corpus or indexer change rebuilds. The job timeout is 60 minutes. With a cache hit, the two gates together took 17.1 minutes (run `40230771370`, 2026-10-25). Docs-only pushes to `main` skip CI.

The semantic index is decoded from disk on every query, which is most of the v2 gate's ~9 minutes. Detail is in [`notes/2026-10-25-ci-eval-regression-restored.md`](./notes/2026-10-25-ci-eval-regression-restored.md).

**The thresholds live in [`config/retrieval_gates.json`](./config/retrieval_gates.json)** — one entry per (profile, benchmark, split), each recording the measured baseline it was derived from. `scripts/eval_gate.py --gate <name>` reads that file, and refuses a report whose profile or split does not match the gate it is checking. A threshold is never set at or above its baseline, and an existing gate's thresholds are never raised to turn a red run green.

CI runs all three gates on the **`local`** profile: CI builds the local MiniLM index and has no embedding-API credential. The `3large` gates are in the config under the same scheme but need an OpenRouter key and a 3072-dim index, so they are not run by the default CI job.

### v1 — Christianity, historical single-corpus gate (`local/v1`)

`scripts/run_eval.py --tradition christianity`. The v1 expected citations are Bible verses. The gate is scoped to Christianity so the rest of the corpus does not dilute the score. Thresholds are the v0.10.0 Bible-only baselines minus a margin (BM25 0.093, semantic 0.279, hybrid 0.258) and were left unchanged.

| Path | Recall@10 on 2026-10-25 | Threshold |
|------|-------------------------|-----------|
| BM25 | 0.108 | 0.06 |
| Semantic | 0.282 | 0.25 |
| Hybrid | 0.273 | 0.22 |

### v2 dev — cross-tradition gate (`local/v2-dev`)

`scripts/run_eval.py --benchmark v2 --split dev` (48 dev queries, unscoped, citations across Christianity, Tanakh, and Quran). Measured on the 66,689-passage index. These scores sit below v1 because the benchmark asks for more, across three canons.

| Path | Baseline recall@10 | Threshold |
|------|--------------------|-----------|
| BM25 | 0.119 | 0.08 |
| Semantic | 0.189 | 0.15 |
| Hybrid | 0.183 | 0.14 |

The v2 semantic baseline (0.189) is a different measurement from the OpenRouter `text-embedding-3-small` recall of 0.189 on the older 33-query set (below).

### v2 held out — the split nobody tuned against (`local/v2-held_out`)

`scripts/run_eval.py --benchmark v2 --split held_out` (42 queries, unscoped). This split is the honest measurement: its thresholds are derived from **its own** baselines, not copied from the dev gate. It is harder, so its baselines are lower and its thresholds are correspondingly lower — reusing the dev thresholds here would fail on current code and prove nothing.

| Path | Baseline recall@10 (2026-10-28) | Threshold |
|------|---------------------------------|-----------|
| BM25 | 0.092 | 0.05 |
| Semantic | 0.106 | 0.06 |
| Hybrid | 0.115 | 0.07 |

Held-out is a measurement split, not a tuning split. Its thresholds are derived from its baselines and then frozen; they are not adjusted in response to what the gate reports, which is what would turn a held-out split into a second dev split.

### Run the gates locally

Requires a built local index (`pip install -e ".[embeddings]"`, then `python scripts/index_embeddings.py --profile local`). `scripts/eval_gate.py` reads a `run_eval.py` report and fails if a path is under its threshold or missing. Each command below names its gate, so the thresholds come from `config/retrieval_gates.json` rather than being retyped.

```bash
# v1 — scoped to Christianity
python scripts/run_eval.py --paths bm25,semantic,hybrid --tradition christianity \
  --profile local > /tmp/eval_report_v1.txt
python scripts/eval_gate.py --report /tmp/eval_report_v1.txt --gate local/v1

# v2 dev — cross-tradition, 48 queries
python scripts/run_eval.py --paths bm25,semantic,hybrid --benchmark v2 --split dev \
  --profile local > /tmp/eval_report_v2.txt
python scripts/eval_gate.py --report /tmp/eval_report_v2.txt --gate local/v2-dev

# v2 held out — cross-tradition, 42 queries, thresholds from its own baselines
python scripts/run_eval.py --paths bm25,semantic,hybrid --benchmark v2 --split held_out \
  --profile local > /tmp/eval_report_v2_heldout.txt
python scripts/eval_gate.py --report /tmp/eval_report_v2_heldout.txt --gate local/v2-held_out
```

The `3large` gates use the same commands with `--profile 3large` and `--gate 3large/v2-dev` / `--gate 3large/v2-held_out`, and need an OpenRouter key plus a built 3072-dim index.

### Embedder comparison (not the CI gate)

**The production embedder is `openai/text-embedding-3-large`** ([ADR-016](./docs/design-decisions.md)). Measured 2026-10-28 on the complete 66,689-passage indexes, on benchmark v2 (the cross-tradition benchmark that matches the corpus). BM25 is identical in every arm — 0.119 dev, 0.092 held_out — which is the internal control that the corpus, benchmark, and scorer were unchanged.

| Embedder | dim | v2 dev semantic | v2 dev hybrid | held_out semantic | held_out hybrid | End-to-end latency |
|----------|-----|-----------------|---------------|--------------------|------------------|--------------------|
| local `all-MiniLM-L6-v2` | 384 | 0.189 | 0.183 | 0.106 | 0.115 | ~0.83 s |
| **`openai/text-embedding-3-large`** (default) | 3072 | **0.297** | **0.284** | **0.244** | **0.226** | ~2.92 s |
| `qwen/qwen3-embedding-8b` | 4096 | 0.321 | 0.309 | 0.255 | 0.234 | ~9.61 s |

`qwen3-8b` scores highest but at ~9.6 s/query. It is **not** the default, and a "deep study" mode on it is **undecided and not built** — the profile is registered only so the comparison stays reproducible. A full 3-large index rebuild costs about $0.74; per-query cost is negligible.

The earlier 33-query comparison (2026-09-11) that made local the default:

| Embedder | dim | Recall@K | MRR | nDCG@K |
|----------|-----|----------|-----|--------|
| Local `all-MiniLM-L6-v2` | 384 | 0.279 | 0.165 | 0.222 |
| OpenRouter `text-embedding-3-small` | 1536 | 0.189 | 0.199 | 0.184 |

That was the right comparison on the data then available ([ADR-015](./docs/design-decisions.md)), but it used a Bible-only 33-query set — the wrong instrument for a three-tradition corpus. The v0.10.0 write-up is [`docs/evaluation.md`](./docs/evaluation.md). It is the history of the v1 thresholds, not the live v2 baseline.

---

## Status and direction (2026-10-28)

**Direction.** Anyone looking into scripture. A web reader with study help is the likely shape. Depth and cross-referencing come before breadth. Use cases are still being defined. Earlier persona and front-end notes ([`docs/use-cases.md`](./docs/use-cases.md), [`docs/phase4-scope-frontend.md`](./docs/phase4-scope-frontend.md)) are background, not the current product definition.

**Where the code is.**

- Lookup, Strong's, BM25, semantic search, hybrid search, and Bible cross-references ship from the CLI.
- The default embedder is OpenRouter `openai/text-embedding-3-large` ([ADR-016](./docs/design-decisions.md)). Embedder profiles bind backend, model, index, and dimension together, and a query embedder whose width disagrees with the index raises rather than silently truncating.
- Quran, Torah, and Tanakh are ingested. The Judaism slice of the semantic index defaults to English `jps1917-modernized`.
- A passage model, canonical IDs, a versification map, and `--tradition` on `parallel` and `search` are in the tree (`bible/registry.py`). A further tradition still needs its own ingest and wiring; `references` and `strongs` stay on the Bible.
- Three retrieval gates run in CI — `local/v1`, `local/v2-dev`, `local/v2-held_out` — with thresholds in `config/retrieval_gates.json`. The held-out split's thresholds come from its own baselines, not the dev gate's.
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
config/retrieval_gates.json  retrieval thresholds, keyed by profile + split
tests/run_all.py       179 sister-script tests
data/                  quran, torah, tanakh, references, editions.json,
                       versification_map.json
kjv.json, translations/, strongs_data/
notes/                 session notes (Done / Blocked / Tomorrow / Decisions)
docs/                  ADRs, eval history, scope sketches, governance design
```

---

## Governance

[`COUNCIL.md`](./COUNCIL.md) (v0.4, constituted 2026-09-10) is in force as an active single-contributor body, with the project owner as acting chair. The seven principles in §2 bind the project. Decisions land in `notes/`. The full multi-member Council in [`docs/governance/council-design.md`](./docs/governance/council-design.md) waits on a second contributor or Phase 2.

Architectural decisions are ADRs in [`docs/design-decisions.md`](./docs/design-decisions.md).

## Contributing

[`CONTRIBUTING.md`](./CONTRIBUTING.md). Tests: `python3 tests/run_all.py` (179 passed, 0 failed, as of 2026-10-28).

## Security

[`SECURITY.md`](./SECURITY.md). No secrets in the repo. Report security issues to the address in `SECURITY.md`.

## Related

- [`prive8/llm-from-scratch`](https://github.com/prive8/llm-from-scratch) — workshop reference if Phase 2 ever starts.
- [`fawazahmed0/quran-api`](https://github.com/fawazahmed0/quran-api) — Quran ingest source.
- [Open Scriptures Strong's](https://github.com/openscriptures/strongs) — CC-BY-SA lexicon.
- [openbible.info cross-references](https://www.openbible.info/labs/cross-references/) — CC-BY 4.0, via [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases).
- [Sefaria](https://www.sefaria.org/) — Torah and Tanakh ingest source.
- [Bolls Bible API](https://bolls.life/api/) — Bible translation ingest source.
