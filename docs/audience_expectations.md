# Audience Expectations — bible-llm-reference

> **Purpose:** A consolidated reference document for the personas the
> project serves. Use this when:
> - **Building a front-end** — pick the right default render for each
>   user type.
> - **Writing tests / docs / scripts** — pick the right level of detail
>   and the right tone for each user type.
> - **Filling Council roles later** — each persona maps to a constituency
>   the Council serves; use this to scope what each role protects.
> - **Evaluating trade-offs** — when "more X for persona A" costs
>   "less Y for persona B," use this to find the path that loses the
>   least.
>
> **Last updated:** 2026-09-11. Brainstormed 2026-09-10/11.
> **See also:** `docs/use-cases.md` for the original brainstorming
> session with reasoning behind each persona. This document is the
> **distilled, scannable, building-reference** version.
>
> **Source-of-truth reminder (non-negotiable across all personas):**
> this project is **not a chatbot** and **never impersonates a religious
> figure or spiritual authority** (`RUNTIME_CONTRACT.md`). Every output
> is grounded in a citation. The runtime contract binds any agent using
> this data. The personas below describe the *humans* the Council
> exists to serve — not endorsements of synthetic voices, no matter
> how fluent.

---

## The six personas at a glance

| # | Persona | One-line summary | Council constituency |
|---|---------|-------------------|----------------------|
| 1 | **Dr. Aisha** — biblical studies professor (academic) | Original-language + critical apparatus + reproducible queries | `historian_archivist`, `comparative_scholar` |
| 2 | **Marcus** — secular wisdom-seeker (no Abrahamic identification) | Easy entry, cross-tradition comparison, plain-English summaries clearly marked as such | `abrahamic_guardian` (neutrality guardian) |
| 3 | **Dr. Yuki Tanaka** — non-Abrahamic religious-studies researcher | Cross-tradition parallel display, source transparency, non-Abrahamic primary corpora | `comparative_scholar` |
| 4 | **Sarah** — lay-faithful reader (any tradition) | Read the actual text; cross-references for study; no AI sermon | `ethicist_mediator` (the moral center of the project) |
| 5 | **Jordan** — AI engineer / RAG builder (derivative-tool developer) | Clean JSON API, stable schemas, clear licenses, pluggable backends | (proposed) `technical_steward` |
| 6 | **Priya** — interfaith dialogue facilitator | Mixed-audience materials, group setting; drives Phase 4+ non-Abrahamic work | `comparative_scholar` (Phase 4+ lead) |

Personas are ordered by **stakes**, not by frequency:
- Persona 1 + Persona 3 are the smallest audiences but the highest methodological standards.
- Persona 2 + Persona 4 are the largest audiences.
- Persona 5 determines long-term downstream impact.
- Persona 6 is a near-term driver for non-Abrahamic corpus work.

If a design decision would help one persona and hurt another, prefer the change that **helps the highest-stakes persona** without disabling the others. The personas' needs are aligned on the data + retrieval substrate; they only diverge on rendering and depth.

---

## Persona 1 — Dr. Aisha (biblical studies professor)

### Core expectation
*"Give me the text in its original language, the apparatus to study it critically, and a query I can rerun in six months."*

### Wants
- Hebrew alongside English; Greek alongside English (when available); Strong's lemma on every word.
- Critical apparatus: textual variants, manuscript differences, parallel-passage links.
- Traceable methodology: cross-reference edge weights, tradition attribution, link type (quote-allusion vs. thematic).
- Reproducible queries she can paste into a footnote.
- Local + offline (conference travel, institutional access gaps).
- **No AI sermon.** No 400-word "what this verse means" reflection.

### Will request (concrete)
1. "Show me MT vs. LXX variants for Isaiah 53." → *Roadmap:* LXX ingest (Phase 4+).
2. "Find every place Isaiah 53 is quoted or alluded to in the NT." → *Capability:* yes, via `bible.references.traverse(hops=2)`.
3. "Compare JPS 1917, KJV, NRSV for Psalm 23 side-by-side." → *Capability:* yes, via `bible.parallel`.
4. "Find every hapax legomenon in Isaiah." → *Roadmap:* lexicon frequency analysis.
5. "Show me the semantic network around חסד/חנן/רחם across the Hebrew Bible." → *Capability:* yes, partial. Surface Hebrew lemma, not just English gloss.
6. "Generate a citation graph for Psalm 22 (depth 2, edge weights visible)." → *Front-end:* graph visualization.
7. "Show me Strong's numbers used in the Pastoral Epistles with frequency + gloss." → *Roadmap:* book-summary feature.

### Front-end requirements
- Inline original-language display with grammar tagging.
- Critical apparatus panel (MT / DSS / LXX / Vulgate).
- Citation graph visualizer (interactive, with edge-weight filter).
- Cross-tradition comparison view (translation toggle).
- Methodology footnote on every AI-assisted suggestion.
- Export to BibTeX / Zotero.

### Departure triggers
AI-generated content that paraphrases citations; results that aren't reproducible; forced sign-up; translation choices that hide the original text; theology-colored commentary presented as scholarly fact.

---

## Persona 2 — Marcus (secular wisdom-seeker)

### Core expectation
*"Let me read the texts from many traditions without anyone preaching at me."*

### Wants
- Easy entry into unfamiliar texts.
- Cross-tradition comparison without forced synthesis.
- Plain-English summaries, clearly labeled as such.
- No spiritual authority claims.
- Save / share / quote-cite with citation included.

### Will request (concrete)
1. "What does the Quran say about mercy?" → *Capability:* yes, via `bible.semantic`.
2. "Compare what the Sermon on the Mount says to what the Dhammapada says about anger." → *Roadmap:* Dhammapada ingest (Phase 4+).
3. "Show me the most famous verses about forgiveness across all three Abrahamic faiths." → *Capability:* yes, hand-curated or popularity-signal needed.
4. "Show me the Tao Te Ching, chapter 1, and a Psalm side-by-side — don't tell me they mean the same thing." → *Roadmap:* non-Abrahamic corpora.
5. "I found this quote online. Where is it from?" → *Front-end:* reverse citation lookup.
6. "Explain the historical context without preaching." → *Roadmap:* scoped LLM summaries with citations (deferred).
7. "Save this search. Share this with a friend. Email me a PDF." → *Front-end:* standard export/share.

### Front-end requirements
- Big search box, no setup (Google-style entry).
- Quick context toggle ("show me the chapter" without leaving the page).
- Plain-English summaries, ALWAYS labeled as summaries — never conflated with verse text.
- Citation chips — every quote clickable.
- Bookmark / save / share.
- Works offline. No account required.

### Departure triggers
Any AI-generated commentary presented as if it were scripture; forced theological framing ("here's what God wants you to know"); aggressive evangelism in copy; required email signup; slow load times.

---

## Persona 3 — Dr. Yuki Tanaka (non-Abrahamic religious-studies researcher)

### Core expectation
*"Let me compare across traditions with source transparency and no theological framing of the comparison."*

### Wants
- Comparative analysis across traditions, neutrally presented.
- Translation transparency (which edition, which translation, which text-family).
- Trails into secondary literature ("what does the academic literature say about this connection?") — but she does that work, the tool just gives her data.
- Respect for non-Abrahamic frames (parallel presentation, not "Bible explains the Dhammapada").
- Reproducibility and citation discipline (even more important than Persona 1 because she can't verify Hebrew without looking it up).

### Will request (concrete)
1. "Compare Genesis 1 + Genesis 2 + Enuma Elish + Rigveda Nasadiya sukta, side-by-side." → *Roadmap:* non-Abrahamic corpora (Rigveda + Enuma Elish, Phase 4+).
2. "Show me Jewish vs. Christian disagreements — Midrash Rabbah vs. Church Fathers." → *Out of scope* (separate tradition, separate corpus).
3. "Trace how Psalm 22 entered East Asian religious discourse." → *Out of scope* (literature review, not corpus work).
4. "Compare what יְשׁוּעָה / σωτηρία means in OT vs. NT." → *Capability:* partial. *Roadmap:* concordance view.
5. "Strong's numbers used in Isaiah 53 with frequency + gloss." → *Roadmap:* book-summary feature.
6. "What does the Quran say about Isa? Cross-reference to Christian sources." → *Capability:* partial. Cross-tradition query without privileging either source.
7. "Generate a bibliography seed from cross-reference structure." → *Roadmap:* curated bibliography dataset.

### Front-end requirements
- Source transparency (always: edition, tradition's textual tradition, translation, translator, date).
- Multi-tradition comparison view (Genesis 1 + Quran 32 + Tao 25 if we had it — pure parallel display).
- Lemmatized concordance ("every occurrence of word X in text Y" with verse context).
- Cross-reference graph with edge-type labels.
- Honest scope disclosure ("Abrahamic-first; here's where to find Buddhist primary sources").
- Citation export for academic papers (BibTeX, with primary source + translation attribution).

### Departure triggers
Theological framing of comparative analysis; hidden theological biases in "cross-tradition comparison" mode; translation choices that hide primary source language; AI-generated synthesis of cross-tradition parallels; marketing copy that pretends the tool is interfaith when it's really Abrahamic-first.

---

## Persona 4 — Sarah (lay-faithful reader) — the load-bearing persona

### Core expectation
*"Let me read my own sacred text well, with cross-references and the original-language context, but don't preach at me and don't pretend to be my tradition's voice."*

This is the **largest single user population by an order of magnitude** and the persona with the highest stakes for misuse. Every "Reader"-style use case study suggests lay-faithful are 10-100× more numerous than academics. If we get this persona wrong, the failure mode is not "she leaves" — it's "she internalizes an AI-mediated understanding of her own sacred text and her actual interpretive community loses a member to a chatbot."

### Wants
- Read the actual text, not commentary on it.
- Cross-references for personal study.
- Multiple translations side-by-side, clearly labeled.
- Original-language awareness, light touch (word + one-line gloss, not a Hebrew lesson).
- Strong's / lemma lookup for "what's this word mean."

### Does NOT want
- The tool telling her what her tradition teaches
- The tool telling her what to believe
- Devotional content, generated discussion questions, prayer suggestions
- The tool referring to her tradition's authority figures as if it had standing to do so

These constraints are non-negotiable. They are exactly what `RUNTIME_CONTRACT.md` enforces.

### Will request (concrete)
1. "Read me Psalm 23, but show me the Hebrew word for 'still waters' with a one-line gloss." → *Front-end:* verse view + translation columns + original-language sidebar.
2. "Where else in the Bible does 'the Lord is my shepherd' get quoted or alluded to?" → *Front-end:* "See also" panel.
3. "I'm leading a Bible study on Wednesday. Find 3 verses about hospitality in the OT that aren't 'love your neighbor.'" → *Front-end:* search with similarity scores; saved-list state.
4. "What's the Hebrew word for 'lovingkindness' and how many times does it appear in the Psalms?" → *Roadmap:* concordance.
5. "Paul quotes the Greek poets in Acts 17. Which verses?" → *Roadmap:* classic-source citations feature.
6. "I want to memorize Psalm 23. Give me a way to study it verse by verse." → *Roadmap:* memorization UI.
7. "I saw a meme that quoted Isaiah 53:5. What does the rest of the chapter say?" → *Front-end:* reverse citation lookup.
8. "Show me the chapter map for Psalms — a thumbnail of what each psalm is 'about' (without preaching)." → *Roadmap:* curated psalm summaries.

### Front-end requirements
- Translation toggle, not selection (show all 13 by default; let her collapse).
- Original-language sidebar with one-line gloss (three words max per gloss).
- Strong's numbers visible but not mandatory (hover for gloss).
- Cross-reference panel labeled "Other places this idea appears."
- **No AI synthesis.** Period.
- Personal bookmarks / verse lists (local storage, no account).
- Print / share-a-card (PDF for the fridge; share-link for Signal).

### Departure triggers (these are *moral* failures, not UX failures)
- AI-generated devotional content that pretends to be from her tradition's voice.
- Theology drift ("Christians believe X vs. Jews believe Y" framing).
- Trivialization of sacred text (Psalm 23 next to a Stoic meditation as "basically the same idea" without explicit framing).
- Surprise AI behavior.
- Forced interpretation (a "neutral" gloss is still interpretive — make it clear when something is literal translation vs. contextual gloss vs. traditional interpretation).

**This is why `RUNTIME_CONTRACT.md` exists.** The four rules were not written with Personas 1 or 3 in mind. They were written with Persona 4 in mind. **If we get her right, we get everyone right. If we get her wrong, we make the world slightly worse for people trying to read their own sacred texts.**

---

## Persona 5 — Jordan (AI engineer / RAG builder)

### Core expectation
*"Can I drop this into my RAG pipeline and ship to my client without legal or reliability surprises?"*

This persona determines whether the project has *long-term impact* outside the immediate user community. If RAG builders can plug this in cleanly, the tool gets embedded in dozens of downstream applications.

### Wants
- Clean JSON API for every corpus operation (✓ we have this via `--json`).
- Stable, predictable schemas (raw committed, derived gitignored per ADR-003).
- Clear license terms (✓ documented per `data/*/README.md`).
- Self-hostable (Docker image + clear local-runs work).
- Documentation as SDK reference, not religious-studies paper.
- Pluggable backend support (✓ OpenRouter added in v0.13.0).

### Will request (concrete)
1. "Does your retrieval layer support batched queries?" → *Roadmap:* `bible search --batch-queries file.txt`.
2. "What's the latency / throughput?" → *Roadmap:* `scripts/benchmark.py` with p50/p95/p99.
3. "Dockerfile + docker-compose for the corpus + a simple FastAPI server." → *Roadmap:* high-leverage Dockerfile.
4. "Compare two index runs side-by-side." → *Roadmap:* `run_eval.py --against-saved-index`.
5. "What's your versioning story?" → *Roadmap:* `docs/stability.md` commitment.

### Departure triggers
Hidden cloud dependencies; API breakage between minors; unclear licensing; undocumented performance characteristics; "just read the source" instead of docs.

---

## Persona 6 — Priya (interfaith dialogue facilitator)

### Core expectation
*"Give me materials that work for mixed audiences — people who are each rooted in their own tradition but willing to read each other's texts respectfully."*

Different from Persona 3: Persona 3 produces academic papers; Persona 6 *runs programs* — multi-faith reading groups, synagogues-and-mosques joint study sessions, weekend retreats.

Out of scope for the first front-end, but her use case eventually drives the non-Abrahamic Phase 4+ corpus work.

### Wants
- Multi-tradition parallel display tuned for *group* (not individual) reading.
- Materials that explicitly mark which tradition's perspective each passage is from.
- Facilitator-friendly framing: this is "comparative reading" not "comparative theology."

---

## Council roles ↔ personas mapping

This is the working hypothesis for how the personas relate to the Council's role design. When the full multi-agent Council forms (per `COUNCIL.md` §3 trigger conditions), each persona should have at least one Council role that exists specifically to serve them.

| Persona | Primary Council role | Secondary role |
|---|---|---|
| 1 — Aisha (academic) | `historian_archivist` (textual apparatus, source transparency) | `comparative_scholar` |
| 2 — Marcus (secular) | `abrahamic_guardian` (neutrality guardian; ensures the tool never claims spiritual authority) | `historian_archivist` |
| 3 — Yuki (comparative) | `comparative_scholar` (cross-tradition display, non-Abrahamic expansion lead) | (none) |
| 4 — Sarah (lay-faithful) | `ethicist_mediator` (the moral center; prevents theological drift and AI-sermon framing) | `abrahamic_guardian` |
| 5 — Jordan (AI engineer) | *(proposed)* `technical_steward` (license clarity, API stability, downstream embeddability) | (none) |
| 6 — Priya (interfaith facilitator) | `comparative_scholar` (Phase 4+ lead for non-Abrahamic corpora) | `ethicist_mediator` |

The mapping is **bidirectional**: when a Council role's responsibilities feel ambiguous, ask "which persona does this role serve, and what does that persona need?" If you can't answer, the role might not be needed yet.

The mapping is also **non-1:1**: a single Council role can serve multiple personas (e.g. `ethicist_mediator` serves Sarah directly, and serves Aisha indirectly by preventing the tool from drifting into AI-sermon mode that would discredit her as an academic tool). This overlap is intentional.

When the full Council forms, this mapping should be the input to the agent system prompts — each Council role's prompt should explicitly list which personas it serves and what each needs.

---

## Cross-cutting design constraints (apply to ALL personas)

These constraints are non-negotiable and surface in every persona's departure triggers:

1. **Every output is cited.** Verse + reference; quote + source; cross-reference + edge weight; comparison + edition labels.
2. **No paraphrased citations.** When we display a verse, it's the verse. When we display a cross-reference, it's the edge. When we display a translation, it's labeled "JPS 1917" not "the Bible."
3. **No spiritual authority claims.** The tool never tells anyone what to believe, who to pray to, what their tradition teaches. The runtime contract binds this.
4. **Internal diversity surfaced.** When a tradition has multiple readings (MT vs. LXX, Saheeh vs. Yusuf Ali for Quran), both are shown. We don't pick a winner.
5. **Source/translation transparency.** Every render shows what edition, what translation, what text-family. No hidden defaults.
6. **Local-first / no mandatory cloud dependency.** (ADR-001) All three personas (1, 2, 4) explicitly want this. NIM is the alternative paid path; OpenRouter is the other paid path; local sentence-transformers is the free path.
7. **Reproducible queries.** No personalized feed, no stateful "what you read yesterday" surface that affects what you see today. Same query, same results.
8. **No account required.** All six personas would abandon the tool at signup.

---

## Front-end architecture (decision summary)

Three layers over the same CLI backend:

**Layer 1 — Reader** (Persona 2 + Persona 4 default; Persona 1 / 3 / 5 / 6 also use for casual queries)
- Big search box → results with citation chips
- "Show me the chapter" inline expansion
- Translation toggle (multiple visible by default)
- Original-language sidebar with one-line gloss
- Strong's numbers (hover for gloss)
- Bookmark / save / share / print
- **Default for everyone except Persona 1**

**Layer 2 — Scholar** (Persona 1)
- Same web app, different mode
- Original language + translation + Strong's + morphology + cross-reference graph
- Query builder ("find every hapax legomenon in Isaiah 53")
- Export to BibTeX / CSV

**Layer 3 — Comparative** (Persona 3 + Persona 6)
- Side-by-side parallel display: Tanakh column / Quran column / Buddhist column (when corpora exist)
- Cross-tradition lemma lookup
- Translation notes
- Honest scope disclosure ("this is Abrahamic-first; here's where to find Buddhist primary sources")

All three layers share the same **CLI backend** (already exists at v0.14.0) and the same **data + retrieval substrate**. The front-end is a thin layer over the CLI; it does not duplicate any logic.

---

## MVP scope (one-week)

Build **Layer 1 (Reader)** first. The minimum viable product:
- Web UI that wraps the existing CLI as a thin layer. Backend is Python (FastAPI), frontend is single HTML page with HTMX-style progressive enhancement. No build step, no SPA framework, no JS bundler. Local-host-friendly.
- Three modes (Reader default; Scholar + Compare toggles).
- JSON API at `/api/<command>` mirroring the CLI — so AI agents and external tools can hit the same backend.
- No accounts. No tracking. No cloud lock-in. Runs locally; can be deployed to a VPS; can be served from a static export.

**MVP rejection criteria:** a feature that confuses Persona 4 is a *blocker*. A feature that confuses Persona 1 is *missing* but not blocking. Ship to Persona 4 first.

---

## Roadmap implications (consolidated)

| Source | Implication | Persona served | MVP-blocking? |
|---|---|---|---|
| Persona 1 | LXX / DSS / Vulgate ingest for textual criticism | 1 | No |
| Persona 1, 4 | Concordance view (every occurrence of a lemma) | 1, 4 | No |
| Persona 1, 4 | Greek NT apparatus (we have Hebrew + Greek lexicon; need morphological tagging) | 1, 4 | No |
| Persona 2, 3 | Dhammapada, Tao Te Ching, Rigveda, Upanishads corpora | 2, 3, 6 | No |
| Persona 2, 3 | Inter-tradition parallel reader UI | 2, 3 | No |
| Persona 3 | Bibliography dataset (curated academic citations) | 3 | No |
| Persona 4 | Memorization UI (verse-by-verse study) | 4 | No |
| Persona 4 | Curated psalm-summary dataset | 4 | No |
| Persona 5 | Dockerfile + docker-compose | 5 | No |
| Persona 5 | `scripts/benchmark.py` (latency p50/p95/p99) | 5 | No |
| Persona 5 | `docs/stability.md` (versioning promise) | 5 | No |
| Persona 5 | Batched queries (`--batch-queries file.txt`) | 5 | No |
| Persona 6 | Multi-tradition group-reading UI | 6 | No |
| All | Layer 1 Reader MVP | All except 1 | **Yes** |
| All | JSON API at `/api/<command>` | All | **Yes** |

---

## Closing note

The personas' expectations are **mostly aligned**. They disagree on rendering depth, not on data integrity or retrieval methodology. The fact that the same substrate (CLI + data + retrieval + runtime contract) serves all six is the architecture's strongest claim: a front-end is rendering work, not new engineering.

The **load-bearing persona is Sarah (Persona 4)**. She's the largest audience, the highest-stakes failure mode, and the one whose trust — once lost — is hardest to rebuild. **If you only have time to get one persona right, get her right.** The runtime contract exists for her. The data discipline exists for her. The "no AI synthesis" stance exists for her. Everything else — the academic rigor for Aisha, the cross-tradition parity for Yuki, the developer ergonomics for Jordan — is layered on top of the foundation that serves Sarah.

When the Council roles get filled in later, the personas above are the constituencies they serve. Each Council role should know which persona it exists for, what that persona needs, and what failure modes would hurt that persona specifically. The mapping table above is a starting point.

The biggest risk is the temptation to add AI-generated "synthesis" modes — "let the model summarize what these verses have in common." Persona 2 doesn't want it. Persona 3 forbids it. Persona 1 tolerates it only under strict labels. **Persona 4 must not be exposed to it under any framing.** Defer it indefinitely.

If you only remember three things from this document:

1. **The personas are not in tension.** Same substrate, different surfaces. Build it right and the front-end is rendering work.
2. **Sarah (Persona 4) is the load-bearing persona.** Get her right. The runtime contract exists because of her.
3. **Build the Reader layer first, default for everyone except Persona 1.** A feature that confuses Sarah is a blocker; a feature that confuses Aisha is missing but not blocking.

That's the entire design center in three sentences.
