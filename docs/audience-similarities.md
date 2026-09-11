# Cross-Persona Similarities — driving us to the next level

> **Purpose:** The previous docs (`docs/use-cases.md`,
> `docs/audience_expectations.md`) catalogued what each persona
> *wants in isolation*. This doc surfaces what they want **in common**
> — the cross-cutting patterns that, when addressed, drive the
> project from "works for one user" to "works for everyone, and works
> at scale."
>
> **Last updated:** 2026-09-11.
>
> **Three similarity layers drive this doc:**
> 1. **Same want, same capability** — already shipped (these are
>    the substrate we can lean on).
> 2. **Same want, different naming** — capability exists but personas
>    don't know about it (these are the "discoverability" wins).
> 3. **Same want, capability missing** — multiple personas ask for
>    variants of the same thing that we don't yet have (these are the
>    **next-level roadmap**).

---

## Layer 1 — Same want, same capability (the substrate we already have)

These are the capabilities that already serve multiple personas. They
form the foundation of "works for everyone" — don't change them, just
expose them better.

| Capability | Already in | Personas served | Status |
|---|---|---|---|
| Multi-translation parallel view | `bible.parallel.run_parallel` | Aisha (translation comparison), Sarah (her own tradition's text), Yuki (translation transparency) | ✅ Shipped (v0.5.0) |
| BM25 keyword search | `bible.search.run_search` | Aisha (Greek/Hebrew term search), Marcus (curiosity queries), Yuki (verse-level lookups) | ✅ Shipped (v0.3.0) |
| Semantic search across traditions | `bible.semantic.search_semantic` | Marcus (intuitive queries), Sarah (study prep), Yuki (cross-tradition) | ✅ Shipped (v0.8.0) |
| Cross-references 1-hop | `bible.references.get_references` | Aisha (quote-allusion tracking), Sarah (study), Yuki (parallel passages) | ✅ Shipped (v0.5.0) |
| Cross-references reciprocal | `bible.references.get_reciprocal` | Aisha (who cites this verse), Yuki (incoming cross-tradition citations) | ✅ Shipped (v0.5.0) |
| Cross-references 1-3 hop | `bible.references.traverse` | Aisha (citation chain), Yuki (theme networks) | ✅ Shipped (v0.5.0) |
| Strong's lemma lookup | `bible.strongs.run_strongs` | Aisha (technical study), Sarah (what does this word mean) | ✅ Shipped (v0.2.0) |
| Quran lookup | `bible.quran.run_quran` | Yuki (cross-tradition), Marcus (curiosity), Sarah-muslim (her text) | ✅ Shipped (v0.6.0) |
| Torah / Tanakh lookup | `bible.torah.run_torah`, `bible.tanakh.run_tanakh` | Sarah-jewish (her text), Aisha (Hebrew study), Yuki (Tanakh) | ✅ Shipped (v0.11.0, v0.14.0) |
| Reference parser (book + chapter + verse) | `bible.lookup.parse_ref` | All personas | ✅ Shipped (v0.2.0) |
| JSON output on every command (`--json`) | All CLI commands | Jordan (RAG builder), Aisha (reproducible), Yuki (citation discipline) | ✅ Shipped (per command) |
| Adapter-level alias resolution (Hebrew, Latin, transliteration, Roman-numeral) | `bible/torah.py`, `bible/tanakh.py` | Sarah (Hebrew-with-nikkud), Aisha (transliteration), Jordan (CLI ergonomics) | ✅ Shipped (v0.11.0, v0.14.0) |
| Full public-domain text data | `data/{bible,quran,torah,tanakh}` | All personas | ✅ Shipped (v0.6.0–v0.14.0) |
| Honest source attribution | `data/*/README.md`, license headers | All personas (transparency) | ✅ Shipped |
| Citation discipline (no paraphrased citations) | Runtime contract, all CLI commands | All personas (cross-cutting) | ✅ Shipped (v0.10.0) |
| Local-first / no mandatory cloud | Architecture (ADR-001) | Aisha, Marcus, Sarah, Yuki, Jordan | ✅ Shipped (ADR-001) |

**What this layer tells us:** the substrate is mature. The data, the
retrieval, the citation discipline, the multi-tradition coverage — all
there. The next level is not "build more capability" — it's "expose the
capability we have in more surfaces." Layer 2 + Layer 3.

---

## Layer 2 — Same want, different naming (discoverability wins)

Capabilities exist but personas ask for them under different framings
because the CLI doesn't surface them in their vocabulary. These are
**quick wins**: re-frame, re-document, expose in front-end. No new code.

### Pattern A — "Show me where else this idea appears"

| Persona | Their phrasing | Capability that answers it |
|---|---|---|
| Aisha | "Find every place Isaiah 53 is quoted in the NT" | `bible.references.traverse(ref="Isaiah 53:1", hops=2)` |
| Sarah | "Where else in the Bible does 'the Lord is my shepherd' get quoted or alluded to?" | `bible.references.traverse(ref="Psalms 23:1", hops=2)` |
| Yuki | "Compare what 'salvation' means in OT vs. NT" | (cross-reference per occurrence) — needs concordance (Layer 3) |

**The unifying capability is `bible.references.traverse`.** All three
want the same thing — "show me the network around this verse" — and
we already have it. What's missing is:
- A **front-end "See also" panel** under every verse (Phase 1 of front-end).
- A **graph visualization** (Phase 2 of front-end) — already on Persona 1's roadmap.
- A **search-by-lemma** front-end that uses traverse on every occurrence of a lemma (Persona 1's hapax search, Sarah's "every occurrence of 'lovingkindness'") — currently you'd have to write a Python script.

### Pattern B — "Show me the original / show me the translation"

| Persona | Their phrasing | Capability that answers it |
|---|---|---|
| Aisha | "Hebrew alongside English; Greek alongside English" | `bible.parallel` with multiple editions |
| Sarah | "Show me the Hebrew word for 'still waters' with a one-line gloss" | `bible.parallel --translations jps1917-modernized,hebrew-nikkud` + Strong's lookup for the lemma |
| Yuki | "Translation transparency" | `bible.parallel` with edition labels in output |
| Marcus | "Easy entry into unfamiliar texts" | `bible.semantic` finds English verses; for the original, `bible.parallel` includes Hebrew |

**The unifying capability is `bible.parallel` with edition selection.**
We already pass `--translations` per command, but the front-end needs
to make this *the default render*, not an opt-in switch.

### Pattern C — "What does the corpus say about this concept?"

| Persona | Their phrasing | Capability that answers it |
|---|---|---|
| Marcus | "What does the Quran say about mercy?" | `bible.semantic search_semantic(query="mercy", tradition="islam", top_k=10)` |
| Sarah | "Verses about hospitality in the OT that aren't 'love your neighbor'" | `bible.semantic` + filter by tradition + manual curation |
| Yuki | "What does the Quran say about Isa? Cross-reference to Christian sources" | `bible.semantic search_semantic(query="Isa", tradition="all", top_k=30)` + cross-reference filter |
| Aisha | "Semantic network around חסד/חנן/רחם across the Hebrew Bible" | `bible.semantic search_semantic(query, tradition="judaism")` |

**The unifying capability is `bible.semantic.search_semantic` with
tradition filter.** We already have this. What's missing is:
- A front-end search bar that's the *default* — no CLI invocation required.
- Tradition filter as a UI checkbox, not a CLI flag.

### Pattern D — "Reproducible query / cite this for my paper"

| Persona | Their phrasing | Capability that answers it |
|---|---|---|
| Aisha | "A query I can rerun in six months and paste into a footnote" | `--json` output → reproducible |
| Jordan | "Clean JSON API" | `--json` output → API |
| Yuki | "Citation discipline (BibTeX export)" | `--json` → BibTeX export (Layer 3 work) |
| Sarah | "Save this search / share with citation" | `--json` → bookmark (Layer 3 work) |

**The unifying capability is the `--json` flag + the entire CLI.** All
four personas want machine-readable output for different reasons. The
capability is there; the **front-end JSON API** (FastAPI wrapper
around the CLI) is the next step.

### Pattern E — "Don't preach at me / don't claim spiritual authority"

| Persona | Their phrasing | Binding document |
|---|---|---|
| Sarah | "Don't tell me what to believe, generate devotional content" | `RUNTIME_CONTRACT.md` |
| Marcus | "No evangelism in copy" | (implicit in runtime contract) |
| Aisha | "No AI sermon, no 400-word reflection" | (implicit) |
| Yuki | "No theological framing of comparative analysis" | (implicit) |

**The unifying document is `RUNTIME_CONTRACT.md`.** All four want
the same thing — citation-grounded, never-paraphrased, never-spiritual.
This is already in force. **What's missing is making the contract
visible in the front-end** (a small footer "All output is citation-grounded;
this tool never claims spiritual authority" + a link to the contract).

### Pattern F — "Self-host / no cloud lock-in"

| Persona | Their phrasing | Architecture property |
|---|---|---|
| Aisha | "Local + offline (conference travel)" | ADR-001 (no mandatory cloud dep) |
| Marcus | "Works offline. No account required." | ADR-001 |
| Sarah | (no cloud lock-in) | ADR-001 |
| Yuki | (no cloud lock-in) | ADR-001 |
| Jordan | "Self-hostable. Docker image." | ADR-001 (Docker not yet built — Layer 3 work) |

**All five want ADR-001.** It's already in place. The Docker image is
the next level (Persona 5's roadmap item).

### Layer 2 summary — these are mostly discoverability wins

The unifying capabilities exist; personas don't know about them. The
**next-level work here is documentation + front-end**:

1. **Front-end Layer 1 (Reader)** that surfaces `bible.search`, `bible.parallel`, `bible.references`, `bible.semantic` as UI affordances instead of CLI flags.
2. **Onboarding / orientation** that explains "this tool can do X, Y, Z" in plain language per persona.
3. **Visible runtime contract** in the front-end footer.
4. **Docker image** that exposes the CLI as a local service (Persona 5's specific ask).
5. **JSON API** (FastAPI wrapper around CLI) for Persona 5's RAG-pipeline use.

None of this requires new corpus work. All of it is rendering the
substrate we already have. That's why it's "Layer 2" — high leverage, low cost.

---

## Layer 3 — Same want, capability missing (the next-level roadmap)

These are the things **multiple personas ask for variants of** that we
don't yet have. They're the real "next level" work. Some are corpus
additions, some are retrieval features, some are UI features. The
similarity is what tells us to bundle them as **one design** rather
than three separate ones.

### Bundle 1 — **Concordance** (Personas 1 + 4 + 3)

All three want "every occurrence of word X in text Y" but currently the
only way to do it is to write a Python script that walks the corpus.
None of them want to write a Python script.

- **Aisha:** "Find every hapax legomenon in Isaiah." "Every Strong's number used in the Pastoral Epistles with frequency + gloss."
- **Sarah:** "What's the Hebrew word for 'lovingkindness' and how many times does it appear in the Psalms?"
- **Yuki:** "Compare what יְשׁוּעָה / σωτηρία means in the Hebrew Bible vs. the New Testament, with every occurrence and its context."

**One capability serves all three:** a `bible.concordance` module with
API like:
```python
concordance(lemma="H2617", books=["Psalms"], limit=100) -> list[Verse]
concordance(strongs="G4991", testament="NT", limit=100) -> list[Verse]
concordance(arabic_root="رح-م", collection="quran") -> list[Verse]  # Quran needs Arabic morphology
```

**Roadmap implication:** This is **the next-level feature** that would
serve 3+ personas. Implementation:
- For Hebrew Bible / Greek NT: needs Strong's-number-indexed lookup (we have Strong's data; need an index).
- For Quran: needs Arabic morphology data (LemmaBuckwalter or similar). Not in scope today.
- Estimated effort: 1-2 days for Hebrew/Greek (we have the data); separate effort for Arabic.

### Bundle 2 — **Bookmarks / saved lists / personal corpus** (Personas 4 + 2 + 5)

All three want to save things and come back to them:
- **Sarah:** "I'd save 'Psalm 23' and 'Isaiah 53' and '1 Cor 13' to come back to."
- **Marcus:** "Save this search. Share this with a friend."
- **Jordan:** "Bookmark / save / share buttons" (standard web-app stuff, but they're calling it out).

**One capability serves all three:** local-first state management
(localStorage or URL-encoded lists) with optional export (PDF, JSON).
This is a **front-end feature**, not a corpus feature.

**Roadmap implication:** Layer 1 (Reader) MVP should include this from
day one. No account, no server-side state, no synchronization — just
local browser storage.

### Bundle 3 — **Reverse citation lookup** (Personas 4 + 1 + 5)

"I saw a quote. Where is it from?" — three personas want this in
slightly different ways:
- **Sarah:** "I saw a meme that quoted Isaiah 53:5 ('by his stripes we are healed'). What does the rest of the chapter say?"
- **Aisha:** "I have a paraphrase of a Bible verse from a journal article. Find the exact source."
- **Jordan:** "My users will paste quotes. I need a way to look them up."

**One capability serves all three:** a `bible.search` mode that does
**fuzzy verse lookup** — given a quote, find the most likely verse.
This is harder than exact-match BM25; it needs either:
- Embedding-based fuzzy match (we have `bible.semantic` infrastructure)
- A "quote fragment → verse" trained model (out of scope)

**Roadmap implication:** Use the semantic search infrastructure to
find the best-match verse for a quote fragment. Phrase the search as
"reverse citation" in the front-end. Implementation: ~half a day.

### Bundle 4 — **Classic-source citation recognition** (Personas 4 + 1)

"Sarah asked: 'My pastor said Paul quotes the Greek poets in Acts 17.
Which verses?'" Persona 1 would also find this useful for NT
apologetics work.

We'd need a curated dataset of "classical allusions in scripture"
(e.g. Epimenides in Titus 1:12, Aratus in Acts 17:28, etc.) that the
search layer can use to highlight when a verse contains or alludes
to a known classical source.

**Roadmap implication:** This is a community-curated dataset, similar
to how psalm-summaries would be. Public-domain commentary that maps
specific verses to their extra-biblical allusions. Reasonable scope
(~100 verses × ~20 traditions = ~2000 annotations), needs a
maintainer.

### Bundle 5 — **"Save as PDF / share-a-card"** (Personas 4 + 2 + 6)

Sarah wants to print a verse as a one-page PDF for her Bible.
Marcus wants to share on Signal with citation link. Priya wants
group-reading handouts.

**One capability serves all three:** "Render this verse as a
self-contained printable/shareable artifact with citation baked in."
Front-end feature. No corpus work. Implementation: 1 day.

### Bundle 6 — **Multi-tradition comparison view** (Personas 3 + 2 + 6)

Yuki wants Genesis 1 + Enuma Elish + Rigveda Nasadiya. Marcus wants
Sermon on the Mount + Dhammapada. Priya wants group-reading
across-tradition handouts.

We need **non-Abrahamic corpora** (Rigveda, Dhammapada, Tao Te Ching)
to fully serve this bundle. Estimated Phase 4+ work. The capability
itself — "side-by-side parallel display" — is already there for
Bible translations (`bible.parallel`); extending to cross-tradition
is just adding more corpora to the parallel-view UI.

**Roadmap implication:** Corpus work (Phase 4+) + UI work that mirrors
the existing `bible.parallel` pattern.

### Bundle 7 — **Edge-type labels on cross-references** (Personas 1 + 3)

Yuki wants "edge-type labels" — "quote-allusion," "thematic parallel,"
"linguistic cognate" — on cross-references. Aisha also wants this
implicitly ("whether it's a quote-allusion or a thematic link").

The current openbible.info dataset has just votes-counted edges. No
edge-type. **Roadmap implication:** would need either:
- A different cross-reference dataset (e.g. Treasury of Scripture
  Knowledge, Michel Boody's Logos datasets) that has typed edges, or
- A curated enhancement layer over openbible.info.

Public-domain typed-edge cross-reference datasets exist; ingesting
one would be Phase 4+ work. Estimated: 1-2 weeks.

### Bundle 8 — **Latency / throughput benchmarks** (Persona 5)

Jordan wants "What's the latency / throughput of your hybrid retrieval?"
We have `scripts/run_eval.py` for *quality* (recall, MRR, nDCG) but
not *latency*.

**Roadmap implication:** Write `scripts/benchmark.py` that records
p50/p95/p99 retrieval latency. ~half a day. Pure measurement work.

### Bundle 9 — **Docker + FastAPI front-end** (Persona 5 + all personas)

Jordan wants Docker + FastAPI server. All personas benefit from the
front-end Layer 1 (Reader) that the server would expose.

**Roadmap implication:** This is the "MVP front-end" work in Bundle
terms. See `audience_expectations.md` for the 1-week Layer 1 MVP scope.
Estimated: 1 week.

---

## Cross-bundle pattern — the "do-next" priority order

The nine bundles above sort by **persona count × leverage × cost**:

| Bundle | Personas | Effort | Type | Priority |
|---|---|---|---|---|
| 9 — Docker + FastAPI front-end | All except 1 directly; 1 indirectly via graph view | 1 week | Front-end | **P0** |
| 2 — Bookmarks / saved lists | 4, 2, 5 | 1 day (subset of Bundle 9) | Front-end | **P0** (ship with Bundle 9) |
| 5 — Save as PDF / share-a-card | 4, 2, 6 | 1 day (subset of Bundle 9) | Front-end | **P0** (ship with Bundle 9) |
| 1 — Concordance | 1, 4, 3 | 1-2 days | Corpus (Strong's-indexed) | **P1** |
| 3 — Reverse citation lookup | 4, 1, 5 | 0.5 day | Search (semantic reuse) | **P1** |
| 8 — Latency benchmarks | 5 | 0.5 day | Measurement | **P1** (unblocks Bundle 9 perf tuning) |
| 4 — Classic-source citation dataset | 4, 1 | Phase 4+ (corpus work) | Community dataset | **P2** |
| 6 — Multi-tradition comparison | 3, 2, 6 | Phase 4+ | Corpus (non-Abrahamic) + UI | **P2** |
| 7 — Typed cross-reference edges | 1, 3 | Phase 4+ | Corpus (typed xref) | **P3** |

**Key insight from the table:** the **P0 row** is the Reader Layer 1
front-end, which simultaneously ships Bundles 9, 2, and 5. **One week
of front-end work satisfies 3 bundles and serves every persona.** The
front-end is the highest-leverage place to invest right now.

The P1 row is corpus- and measurement-focused. **The concordance
(Bundle 1) is the most important corpus work after the Reader layer
ships** — it serves 3 personas with existing data.

The P2-P3 rows are Phase 4+ work — non-Abrahamic corpora, typed
cross-references, community-curated classical-source citations. These
are the natural next milestones after Phase 2 (Llama fine-tune) lands.

---

## "Inference is begging" — what changes once Phase 2 lands

Per `HANDOFF.md` §1 + `ADR-012`, Phase 2 is the Llama-3.1-8B-Instruct
fine-tune ("generative voice"). The constraint in `RUNTIME_CONTRACT.md`
is **explicit: this fine-tuned model must not be used as a chat
surface.** It's a tool for the front-end, not a persona of its own.

When Phase 2 lands, the **only** valid use cases for the fine-tuned
model are:
- **Caption generation** — "what does this chapter contain?" (marked
  as AI summary, never as scripture)
- **Translation comparison summarization** — "the KJV and NIV differ
  here because..." (marked as AI summary)
- **Cross-reference type classification** — "this edge looks like a
  quote-allusion because..." (matches Bundle 7)

All three of these are **Layer 2 of the front-end** — Scholar mode —
and **none** of them are the Sarah-disqualifying "AI sermon" use
case. The runtime contract binds this; the personas tell us why.

**Inference is begging** means: "We have a fine-tuned model. What
features does it enable?" — not "Let's add a chatbot." The personas
are unambiguous about this distinction. The next-level features that
inference enables are:
- AI-generated study-Bible-style captions for chapters (clearly
  marked as summaries)
- AI-suggested cross-reference edge types (then verified by
  Persona 1 against openbible.info data)
- AI-assisted translation comparison notes

None of these are AI sermons. All are clearly labeled, scope-limited,
and persona-validated.

---

## The do-next line of thinking — what's missing from HANDOFF §8

`HANDOFF.md` §8 lists pending decisions. Looking at the bundle list,
three of them are **not yet on the §8 list** but should be:

1. **Reader Layer 1 MVP** (Bundle 9 + 2 + 5) — currently no §8 entry
   for "ship a front-end." Should add: "Build Layer 1 (Reader) MVP —
   thin web UI wrapping the CLI; serves Bundles 2, 5, 9 simultaneously."

2. **Concordance** (Bundle 1) — currently no §8 entry. Should add:
   "Add Strong's-indexed concordance — 1-2 days, serves Aisha + Sarah + Yuki."

3. **Reverse citation lookup** (Bundle 3) — currently no §8 entry.
   Should add: "Use existing semantic-search infrastructure for
   paste-a-quote-fuzzy-find — 0.5 day."

Adding these three to `HANDOFF.md` §8 as the **next-level roadmap
beyond the OpenRouter benchmark** would close the loop. The OpenRouter
benchmark is the *last* Phase 1-style work item; these three are the
*first* Phase 2-style (front-end + corpus feature) work items.

The ordering becomes:
1. **Now:** OpenRouter benchmark (HANDOFF §8 #10 — once `OPENROUTER_API_KEY` is in `.env`).
2. **P0:** Reader Layer 1 front-end (Bundle 9 + 2 + 5). 1 week.
3. **P1:** Concordance + reverse citation lookup + latency benchmarks (Bundle 1 + 3 + 8). 3 days.
4. **Phase 2 work:** Llama fine-tune (per ADR-012; gated on Phase 1 quality).
5. **Phase 4+:** Non-Abrahamic corpora + typed cross-references + community-curated classical-source citations.

That's a complete roadmap from "the tool works for one user in the
terminal" to "the tool works for every persona with a UI they want."

---

## Closing note — what the similarities tell us

The strongest signal from this doc is that **Bundle 9 (the front-end)
is the highest-leverage work available.** Almost every Layer-2
similarity is "the capability exists; the persona doesn't know about
it because there's no UI." Once the Reader Layer 1 ships, Persona 2,
4, 5, and the casual queries of 1, 3, 6 are all served by existing
substrate.

Bundles 1-8 (corpus + retrieval features) matter but they're
**rendered well by the existing CLI**, so they don't block the
"works for everyone" milestone. They matter for the personas' *deep*
use — the queries they'll run a hundred times a year, not the ones
they'll run on day one.

The next-level question isn't "what data should we add?" (the corpus
is mature enough to ship). It's "what surface are we putting on
top of it?" The answer, per the personas, is: **a fast, local-first,
citation-first, no-account, no-AI-sermon web UI that defaults to
reading-mode and offers scholar-mode for the academics.** That's the
Reader Layer 1 MVP. That's where this all points.

The infrastructure is ready. The substrate is mature. The personas
are aligned on what they need. **The next-level work is mostly
rendering work, not engineering.** That's the gift of building the
right substrate first.
