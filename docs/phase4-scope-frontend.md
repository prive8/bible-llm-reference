# Phase 4 Scope — Front-End (Reader / Scholar / Comparative Layers)

> **Status:** Scope complete. Implementation pending. Phase 4 begins
> after Phase 3.3 (Full Tanakh, v0.14.0) and v0.16.0 (polish) are
> shipped.
>
> **Last updated:** 2026-09-12.
>
> **See also:**
> - [`docs/use-cases.md`](./use-cases.md) — original 6-persona brainstorming
> - [`docs/audience_expectations.md`](./audience_expectations.md) — distilled per-persona building reference
> - [`docs/audience-similarities.md`](./audience-similarities.md) — cross-persona roadmap (the 9-bundle matrix)
> - [`docs/sample-questions.md`](./sample-questions.md) — quick per-persona question + front-end table
> - [`RUNTIME_CONTRACT.md`](../RUNTIME_CONTRACT.md) — the five rules that bind any consumer of this data
> - [`notes/2026-09-12-v0.16.0-polish.md`](../notes/2026-09-12-v0.16.0-polish.md) — the session this scope doc was written in

---

## The pattern under everything

This project would help humans **read their own and each other's sacred texts well, without anyone — including the tool — pretending to be a tradition's voice.**

Six personas, six facets of the same diamond:

| # | Persona | If it could do one thing, it would help humans… |
|---|---------|-------------------------------------------------|
| 1 | **Dr. Aisha** (academic) | …rigorously cite, in six-month-still-resolvable form, every Hebrew lemma that grounds her argument in a peer-reviewed journal article. |
| 2 | **Marcus** (secular seeker) | …read what the world's religions actually say without anyone — including the tool — telling him what to believe. |
| 3 | **Dr. Yuki Tanaka** (comparative scholar) | …build a paper-credible, system-claim-free comparison across traditions where she controls every annotation and the tool never invents a parallel. |
| 4 | **Sarah** (lay-faithful) | …read her own sacred text carefully — in the original language, with cross-references — and trust the tool to never speak in her tradition's voice. |
| 5 | **Jordan** (RAG builder) | …ship scripture-grounded AI to his client today without legal, reliability, or schema-surprise surprises six months from now. |
| 6 | **Priya** (interfaith facilitator) | …hand a one-page printout to a room of mixed-tradition adults that she can defend line-by-line, with sourced reception notes, no synthesis. |

**All six converge on: the tool stays out of the interpretive act.** The human reads; the human decides; the tool grounds. The data discipline, the runtime contract, the no-AI-synthesis stance, the version-stability promise, the reception-notes curation — they're all operationalizations of that single principle applied at different surfaces.

**Sarah (Persona 4) is the load-bearing persona.** Her failure mode is moral, not UX: if the tool substitutes for her interpretive community, she internalizes an AI-mediated understanding of her own sacred text. The runtime contract exists to prevent that outcome. Every other persona's requirements are layered on top of the foundation that serves Sarah.

---

## What this phase is

A thin front-end layer over the existing CLI backend. **No data-layer rebuilds. No new retrieval algorithms. No new corpora for the MVP.** The data + retrieval substrate is mature (v0.15.0: 66K indexed passages across 3 traditions, recall@10 0.279, 126+ sister-script tests passing). Phase 4 is **rendering work**, not new engineering.

Three layers, one CLI backend:

| Layer | Audience | Default for | Page-style |
|-------|----------|-------------|------------|
| **1 — Reader** | Anyone; default for Sarah + Marcus | Largest audience (10-100× academics) | Single search box → results with citation chips |
| **2 — Scholar** | Aisha | Academic users | Original language + Strong's + morphology + cross-reference graph |
| **3 — Comparative** | Yuki + Priya | Cross-tradition researchers | Side-by-side parallel display across 2-4 traditions |

All three layers share the **same CLI backend** and the **same data + retrieval substrate**. The FastAPI server is the surface that fronts all three.

---

## Front-end architecture

Per `audience_expectations.md` §"MVP scope":

> Web UI that wraps the existing CLI as a thin layer. Backend is Python
> (FastAPI), frontend is single HTML page with HTMX-style progressive
> enhancement. **No build step, no SPA framework, no JS bundler.**
> Local-host-friendly. No accounts. No tracking. No cloud lock-in.

```
FastAPI server
   ├── thin wrapper around bible.* CLI commands
   │      (each CLI command has a /api/<command> endpoint)
   ├── /api/<command> returns JSON with schema_version + ETag
   └── single HTML page (HTMX) at /
          ├── Reader layer (default)
          ├── Scholar layer (toggle)
          └── Comparative layer (toggle)
```

**Tech stack:** Python 3.11+ (matches WSL env), FastAPI, Jinja2 templates, HTMX. No npm. No webpack. No React/Vue/Svelte. **The frontend is HTML + CSS + a 14KB JS library.** That's the discipline.

---

## MVP scope (Phase 4.1)

The minimum viable product. **One-week target.** A feature that confuses Persona 4 is a *blocker*; a feature that confuses Persona 1 is *missing* but not blocking. **Ship to Persona 4 first.**

### MVP backend (4 features, all HIGH priority)

| # | Feature | Personas requesting | Effort | Source |
|---|---------|---------------------|--------|--------|
| 1 | **Stable JSON API at `/api/<cmd>`** + `schema_version` field + HTTP `ETag` + auto-generated OpenAPI | Jordan + (everyone via UI) | 1 week | Jordan Q1 |
| 2 | **Concordance / lemma search** (`bible concordance H2617 --translation KJV --json`) — parses KJV `<S>nnnn</S>` tags once, indexes every occurrence | Yuki + Sarah | 2 days | Yuki Q2 |
| 3 | **Reverse citation lookup** (paste-text input → confidence-ranked verse candidates) — thin wrapper over `bible search --json` | Marcus + Sarah | 1 day | Marcus Q1 + Sarah Q1 |
| 4 | **3-word gloss template constraint + no-theological-language UI lint as sister-script tests** | Sarah (load-bearing) | 1 day | Sarah Q1 |

**Estimated MVP backend effort: 2-3 weeks of focused work.** The JSON shapes already exist; the API work is glue + tests + docs.

### MVP frontend (3 surfaces, all served by MVP backend)

| # | Surface | Personas | Effort | Source |
|---|---------|----------|--------|--------|
| 1 | **Reader landing page** — single search box, results with citation chips, "show me the chapter" affordance, no signup, no tradition picker, URL-stable queries | Marcus + Sarah | 2 days | Marcus Q2 + Sarah Q1 |
| 2 | **Verse view** — multi-edition parallel columns (default: all 14), Strong's-per-verse sidebar with 3-word glosses, "Other places this idea appears" cross-reference panel (no theological verbs) | Sarah + Marcus | 1 day | Sarah Q1 |
| 3 | **Concordance view** — sortable table of lemma occurrences with per-edition translations, CSV download button, no commentary column | Yuki + Sarah | 1 day | Yuki Q2 |

**Estimated MVP frontend effort: 1 week of HTML/HTMX work.** No JS framework; template files + CSS.

### MVP cross-cutting constraints (mandatory, ship-blockers)

These apply to every MVP feature. A regression test for each ships in the same commit as the feature.

1. **`schema_version` discipline** — every JSON response carries `{"schema_version": "<bible.__version__>", "data": ...}`. Breaking schema changes bump the major version.
2. **ETag caching** — every GET response carries an `ETag`. `If-None-Match` returns 304.
3. **No AI synthesis** — no LLM-generated text in any UI template. Every string is template-rendered from a data field. The runtime contract already binds this for the agent layer; the UI templates must operationalize it.
4. **No theological language in Reader/Scholar templates** — sister-script test greps HTML/Jinja2 templates for forbidden words: `fulfillment`, `prophecy`, `typology`, `about`, `means`, `refers to`, `points to`, `Jesus`, `Christ`, `Mashiach`, etc. **Load-bearing test for Sarah.**
5. **3-word gloss cap** — sister-script test asserts no Strong's gloss in any UI template exceeds 3 words. Exception: full Strong's glossary page (where the full gloss is the point).
6. **Citation chip on every verse** — every quote rendered in any surface has a clickable chip with edition + translator + license link.
7. **URL-stable queries** — every search has a stable URL: `/?q=...&tradition=all&format=parallel`. No cookies, no localStorage requirement.
8. **No account, no signup, no tracking** — verified by the absence of those surface areas. The landing page is a search box.

**Estimated cross-cutting test work: 1 week.** Many of these are sister-script tests that run on every CI push.

---

## Post-MVP roadmap (Phase 4.2+)

The features the MVP defers. **Order matters** — each item should not start until the MVP is shipped + validated against real users.

### Phase 4.2 — Operational + RAG builder (Jordan's questions, Q2)

| # | Feature | Effort | Notes |
|---|---------|--------|-------|
| 1 | **Dockerfile + docker-compose** with nginx + FastAPI + volume mount for the embedding index | 1 day | Single-persona (Jordan), but unlocks downstream adoption |
| 2 | **Latency benchmark script** (`scripts/benchmark_latency.py`) reporting p50/p95/p99 for `/api/parallel`, `/api/semantic`, `/api/concordance` at concurrency 1, 10, 50 | 1-2 days | Different from `scripts/run_eval.py` (which measures retrieval *quality*; this measures *latency*) |
| 3 | **Batched queries endpoint** (`POST /api/search/batch` accepting 1000 queries, returning 1000 result lists) | 2 days | Jordan Q2 explicit requirement |
| 4 | **`docs/stability.md`** — version-stability commitment (minor = additive only; major = allowed breakage with migration guide) | 0.5 day | Already partially drafted in `audience_expectations.md` §5 |

### Phase 4.3 — Reception notes + handout generator (Priya's question)

| # | Feature | Effort | Notes |
|---|---------|--------|-------|
| 1 | **`bible handout` CLI command** (theme → verse → context → PDF) | 1 week | Priya's flagship ask |
| 2 | **Reception notes dataset** (`data/reception/<theme>.json`) per theme — sourced from public-domain academic sources (Jewish Encyclopedia 1901-06 PD, Encyclopaedia of Islam PD entries) | 2 weeks for initial 5-7 themes | Yuki-clause-provenance requirement adapted for thematic handouts |
| 3 | **Discussion question bank** (`data/questions/<theme>.json`) per theme — sourced from public-domain interfaith curricula, typed (`factual` / `comparative` / `personal` / **never** `normative`) | 1 week for initial 5-7 themes | Question type taxonomy enforced at schema level |
| 4 | **PDF layout template** (WeasyPrint or ReportLab; double-sided, half-page-per-tradition, edition labels visible) | 2 days | Print-ready |

### Phase 4.4 — Scholar layer features (Aisha's questions)

| # | Feature | Effort | Notes |
|---|---------|--------|-------|
| 1 | **LXX critical text (NA27 / Göttingen) ingest** | Phase 4+ corpus work | Blocks Aisha's "MT vs LXX variants for Isaiah 53" question |
| 2 | **Per-word Strong's overlay** (tokenizer + word-aligned data) | 1-2 weeks | Different render granularity than verse-level Strong's |
| 3 | **Citation graph export** (BibTeX with `cites` for primary source + `comment` for the parallel claim) | 1 week | Aisha Q1 + Yuki Q1 |
| 4 | **Hapax legomenon search** | 1 day | Aisha's specific request; needs lemma-frequency dataset |

### Phase 4.5 — Comparative layer features (Yuki + Priya)

| # | Feature | Effort | Notes |
|---|---------|--------|-------|
| 1 | **Cross-tradition parallel view** (Tanakh + Quran + placeholder for Rigveda, side-by-side, scrollable, original + translation per column) | 1 week | Yuki Q1 |
| 2 | **Per-clause provenance metadata** (manuscript family, translator, date, license) | 2 weeks | Yuki Q1 |
| 3 | **User-authored clause-level annotations** (localStorage, exportable) | 1 week | Yuki Q1 — **never** system-generated parallels |
| 4 | **Honest scope-disclosure banner** (Abrahamic-first; pointer to non-Abrahamic primary sources) | 0.5 day | Yuki + Priya + Marcus |

### Phase 4.6 — Non-Abrahamic corpus work (Priya's roadmap)

The handout generator is the productization surface for multi-tradition content. Without Phase 4.3's handout feature, the non-Abrahamic corpora have no concrete user.

| # | Tradition | Effort | Notes |
|---|-----------|--------|-------|
| 1 | **Hadith** (smallest, fastest, completes the Abrahamic trio) | 2-3 weeks | Natural Abrahamic completion; many personas ask for it |
| 2 | **Dhammapada** (small, public domain) | 1-2 weeks | Unlocks Marcus "Quran + Dhammapada on anger" question |
| 3 | **Tao Te Ching** (small, public domain) | 1-2 weeks | Same scale as Dhammapada |
| 4 | **Rigveda (Nasadiya sukta subset first)** | 4-6 weeks | Unlocks Yuki's "Genesis + Quran + Rigveda" question; full Rigveda is much larger |
| 5 | **Upanishads, Bhagavad Gita, Book of Mormon** | TBD | Roadmap items per `audience-similarities.md` P2 tier; not in MVP scope |

**Each new tradition gets the same canonical-schema discipline** — same `data/<tradition>/` layout, same `bible/<tradition>.py` adapter pattern, same per-tradition scope doc.

---

## Cross-cutting constraints (apply to ALL features)

These constraints are non-negotiable and surface in every persona's departure triggers (per `audience_expectations.md` §"Cross-cutting design constraints"):

1. **Every output is cited.** Verse + reference; quote + source; cross-reference + edge weight; comparison + edition labels.
2. **No paraphrased citations.** When we display a verse, it's the verse. When we display a cross-reference, it's the edge. When we display a translation, it's labeled "JPS 1917" not "the Bible."
3. **No spiritual authority claims.** The tool never tells anyone what to believe, who to pray to, what their tradition teaches. The runtime contract binds this.
4. **Internal diversity surfaced.** When a tradition has multiple readings (MT vs. LXX, Saheeh vs. Yusuf Ali for Quran), both are shown. We don't pick a winner.
5. **Source/translation transparency.** Every render shows what edition, what translation, what text-family. No hidden defaults.
6. **Local-first / no mandatory cloud dependency** (ADR-001). All six personas explicitly want this.
7. **Reproducible queries.** No personalized feed, no stateful "what you read yesterday" surface that affects what you see today. Same query, same results.
8. **No account required.** All six personas would abandon the tool at signup.

---

## Out of scope (deferred indefinitely)

These were considered and explicitly deferred:

- **AI-generated "synthesis" modes** ("let the model summarize what these verses have in common"). Persona 2 doesn't want it; Persona 3 forbids it; Persona 1 tolerates it only under strict labels; **Persona 4 must not be exposed to it under any framing.**
- **Chat surface / conversational personality.** "Not a chatbot" is a project-level commitment.
- **Comparative theology engine.** Phase 1 is Christian-corpus-only by design; Phase 4's Comparative layer presents each tradition faithfully on its own terms, not "compare them in a normative judgment."
- **Commercial / SaaS hosting.** The MVP is local-first; self-hostable to a VPS; never deployed as a managed cloud service the project controls.
- **Account / personalization / bookmark sync.** All six personas reject this.

---

## Acceptance criteria for Phase 4 (MVP shipped)

A user (any of the six personas) can:

1. Open the FastAPI server locally (one command), visit `/` in a browser, type a question, see real verses from real translations with clickable citation chips. **No signup, no tradition picker, no theological framing.**
2. Click any citation chip, see the source panel (edition, translator, license, dataset URL).
3. Click "show me the chapter" on any verse, see the surrounding 3-5 verses with the queried verse highlighted.
4. Paste a quote they found online (e.g., "judge not lest ye be judged"), get confidence-ranked verse candidates + the verse + chapter context.
5. Visit `/concordance/H2617`, see every occurrence of חֶסֶד with translation columns per edition, download as CSV with documented column names.
6. Verify that **no LLM-generated text appears anywhere in the UI** — every string is template-rendered from a data field. The sister-script UI lint test passes on every CI push.
7. Verify that **no theological verb appears in any Reader-layer template** — the no-theological-language sister-script test passes on every CI push.
8. The `schema_version` field on every JSON response matches `bible.__version__`. Breaking changes bump the major version; minor versions are additive only.
9. Every search has a stable URL that returns the same results in 6 months.

If any acceptance criterion fails, Phase 4 is not shipped. **Criterion #6 + #7 are load-bearing for Sarah.**

---

## Council role ↔ Phase 4 surface mapping

When the full multi-agent Council forms (per `COUNCIL.md` §3 trigger conditions), each Council role exists to serve a specific persona through a specific Phase 4 surface:

| Persona | Primary Council role | Phase 4 surface they protect |
|---------|---------------------|-------------------------------|
| 1 — Aisha | `historian_archivist` | Scholar layer (Phase 4.4) |
| 2 — Marcus | `abrahamic_guardian` | Reader landing page (Phase 4.1 MVP #1) |
| 3 — Yuki | `comparative_scholar` | Comparative layer (Phase 4.5) |
| 4 — Sarah | `ethicist_mediator` | Every Reader-layer surface (Phase 4.1 MVP) |
| 5 — Jordan | *(proposed)* `technical_steward` | JSON API + Docker (Phase 4.2) |
| 6 — Priya | `comparative_scholar` (Phase 4+ lead) | Handout generator (Phase 4.3) |

The mapping is **bidirectional**: when a Council role's responsibilities feel ambiguous, ask "which persona does this role serve, and what does that persona need?" If you can't answer, the role might not be needed yet.

---

## Closing note

The Phase 4 MVP scope above is **rendering work, not new engineering**. The data layer is mature (v0.15.0). The retrieval algorithms are benchmarked and locked (ADR-014, ADR-015). The runtime contract binds what any consumer can do. The 129 sister-script tests cover the substrate.

What's left is: **wrap the CLI in a stable HTTP API, surface three layers over it, ship the cross-cutting constraints as automated tests, and ship the Reader layer first because Sarah is the load-bearing persona and the rest follows from getting her right.**

The biggest risk is the temptation to add AI-generated "synthesis" modes ("let the model summarize what these verses have in common"). Persona 2 doesn't want it. Persona 3 forbids it. Persona 1 tolerates it only under strict labels. **Persona 4 must not be exposed to it under any framing.** Defer it indefinitely. **The runtime contract exists for Sarah.**

If you only remember three things from this document:

1. **The personas are not in tension.** Same substrate, different surfaces. Build it right and the front-end is rendering work.
2. **Sarah (Persona 4) is the load-bearing persona.** Get her right. The runtime contract exists because of her.
3. **Build the Reader layer first, default for everyone except Persona 1.** A feature that confuses Sarah is a blocker; a feature that confuses Aisha is missing but not blocking.