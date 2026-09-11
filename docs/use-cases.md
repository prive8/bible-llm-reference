# Use Case Catalog — Bible LLM Reference

> **Status:** brainstorming document. Output of a one-session
> design exercise on 2026-09-11. The goal is to map who might
> actually use this corpus/tool, what they'd ask for, and what
> that implies for the front-end design — BEFORE we start building
> one.
>
> **Source-of-truth reminder:** this project is **not a chatbot**.
> Per `RUNTIME_CONTRACT.md`, every output is grounded in a citation;
> the system never invents verses or paraphrases citations away; it
> never impersonates Scripture or a religious figure. Any front-end
> design must preserve these constraints. The project is also
> **local-first / no mandatory cloud dependency** (ADR-001) and
> **citation-first / never silent paraphrase** (ADR-007).
>
> **Capability surface today (v0.14.0):**
> - 13 Bible translations + Strong's Hebrew/Greek lexicon
> - Quran: 6 editions (5 English + Arabic Uthmani)
> - Torah: 2 editions (English CC-BY + Hebrew-with-nikkud Public Domain)
> - Full Tanakh: 2 editions (same editions as Torah; 39 books / 23,206 verses)
> - 605K cross-reference edges (openbible.info, CC-BY 4.0)
> - Retrieval: BM25 (`bible.search`), dense semantic (`bible.semantic`),
>   hybrid fusion (`bible.hybrid`), 1-3 hop cross-ref traversal
>   (`bible.references.traverse`), Strong's lookup (`bible.strongs`)
> - JSON output on every command (machine-readable)
> - CLI only today — no GUI

---

## Persona 1 — Dr. Aisha, biblical studies professor (academic)

### Background

A senior faculty member in a religious studies / Hebrew Bible department. Holds a PhD, publishes peer-reviewed work on textual criticism of the prophetic books (Nevi'im). Reads Hebrew and Greek fluently. Has institutional access to paid databases (BibleWorks, Logos, Accordance) but finds them expensive, hard to script against, and locked to specific scholarly traditions. Wants a tool that respects her training.

### What she actually wants out of a tool

- **Original-language support without fighting the UI.** Show me the Hebrew alongside English; give me the lemma (Strong's); let me click through to every place a particular root appears.
- **Critical apparatus visibility.** Variant readings, manuscript differences, parallel passages across traditions — the kind of thing expensive databases do well but cheap websites do poorly.
- **Traceable methodology.** If a tool tells me "this verse connects to that verse", I want to see the cross-reference edge weight, what tradition it comes from, and whether it's a quote-allusion or a thematic link.
- **Reproducible queries.** "Show me every place Isaiah 53 is quoted in the New Testament" — should be a one-liner I can paste into a footnote or rerun six months from now.
- **Local + offline.** My university library access is patchy on conference travel. I want this on my laptop.
- **No AI sermonizing.** If I ask "what does Isaiah 53 say about suffering," I do NOT want a 400-word AI reflection. I want the verses, with citations, and maybe a brief scholarly note saying "see also: Psalms 22, Daniel 12, etc."

### Things she'd actually request (concrete examples)

1. **"Show me the textual variants between MT (Masoretic Text) and LXX (Septuagint) for Isaiah 53."**
   Current capability: none. LXX edition isn't in the corpus. **Roadmap implication:** if we want this, we need to ingest LXX. Could be a Phase 4 thing.

2. **"Find every place in the New Testament that quotes or alludes to Isaiah 53."**
   Current capability: partial. `bible.references.traverse(ref="Isaiah 53:1", hops=2, min_votes=10)` would surface outgoing references. **Front-end implication:** this should be a one-click "trace citations" action on any verse page.

3. **"Compare JPS 1917, KJV, and NRSV side-by-side for Psalm 23."**
   Current capability: yes. `python3 -m bible parallel "Psalms 23:1" --translations jps1917-modernized,kjv,nrsv`. **Front-end implication:** a three-column verse view with translation toggle.

4. **"Find every hapax legomenon in the book of Isaiah."**
   Current capability: no. Would require lexicon-level frequency analysis. **Roadmap implication:** nice-to-have, not core.

5. **"Show me the semantic network around 'mercy' (חסד / חנן / רחם) across the entire Hebrew Bible."**
   Current capability: partial. `python3 -m bible semantic "mercy and lovingkindess" --tradition judaism --top-k 50` works, but doesn't show the underlying Hebrew roots. **Front-end implication:** if we surface this, the front-end should display the Hebrew lemma, not just an English gloss.

6. **"Generate a citation graph for Psalm 22 — both directions, depth 2, with edge weights visible."**
   Current capability: yes. `python3 -m bible references "Psalms 22:1" --hops 2 --direction both`. **Front-end implication:** a graph visualization, not a list.

7. **"Show me every Strong's number used in the Pastoral Epistles with gloss and frequency."**
   Current capability: partial. `bible.strongs.H####` works for individual lookups. **Roadmap implication:** bulk aggregation is a "build it later" feature.

### Front-end features that would matter to her

- **Inline original-language display with grammar tagging** — Hebrew with vowel points + morphological tagging (BHS morphology if we ever get it).
- **Critical apparatus panel** — toggle between MT / DSS / LXX / Vulgate when available.
- **Citation graph visualizer** — interactive, with edge-weight filter.
- **Cross-tradition comparison view** — JPS 1917 vs KJV vs LXX side-by-side, line-by-line.
- **Methodology footnote** — every AI-generated suggestion should cite which cross-reference dataset (openbible.info CC-BY 4.0), which edition, which retrieval method.
- **Export to BibTeX / Zotero** — for her actual workflow.

### What would make her leave

- AI-generated content that paraphrases citations
- Results that aren't reproducible (no citation trail)
- Forced sign-up or subscription
- Translation choices that hide the original text
- Theology-colored commentary presented as scholarly fact

---

## Persona 2 — Marcus, the secular wisdom-seeker

### Background

40-something software engineer. Grew up vaguely Christian, drifted away in his 20s, doesn't identify with any religion. Reads widely — Stoic philosophy, Alan Watts, the Tao Te Ching, the Dhammapada, sometimes the Bible and the Gita when something comes up. Not a scholar; doesn't read Hebrew or Arabic. Wants the *wisdom* without the *inscription*.

### What he actually wants out of a tool

- **Easy entry into unfamiliar texts.** "What's the Quran say about forgiveness?" should give him 5 verses with brief context, not 50 pages of academic apparatus.
- **Cross-tradition comparison.** "How do Buddhism, Christianity, and Islam each describe suffering?" is the kind of question he asks himself while walking. He wants the texts to speak, side by side, without an LLM editor telling him what to think.
- **Plain-English summaries, clearly labeled.** Not the verse itself — but the verse **plus** a brief summary of its context, clearly marked as "summary, not the text." He values honesty about what the tool is doing.
- **No spiritual authority claims.** If the tool says "the Bible teaches X," Marcus immediately disengages. If it says "the Gospel of Matthew, chapter 5, says X — note that this is one Christian tradition's text, and other traditions interpret differently," he stays.
- **Save / share / quote-cite.** When he finds something good, he wants to send it to a friend with the citation included, not a screenshot.

### Things he'd actually request (concrete examples)

1. **"What does the Quran say about mercy?"**
   Current capability: yes. `python3 -m bible semantic "mercy" --tradition islam --top-k 10`. **Front-end implication:** a simple search box, no setup, returns 10 verses with citation chips.

2. **"Compare what the Sermon on the Mount says to what the Dhammapada says about anger."**
   Current capability: partial on our side (Sermon on the Mount is in the Bible corpus). **Roadmap implication:** Dhammapada ingestion is one of the planned Phase 4+ targets; this would be the showcase cross-tradition query.

3. **"Show me the most famous verses about forgiveness across all three Abrahamic faiths."**
   Current capability: yes. `python3 -m bible semantic "forgiveness" --tradition all --top-k 30`, filtered by hand for canonical "famous" verses (the user would do this curation, or we'd add a "popularity" signal later). **Front-end implication:** a tag-cloud or carousel showing top hits across traditions.

4. **"I want to read the Tao Te Ching, chapter 1, and a Psalm side-by-side. The tool shouldn't tell me they 'mean the same thing.' Just let me read both."**
   Current capability: partial. Side-by-side parallel view exists for Bible translations. Cross-canon comparison isn't built yet. **Front-end implication:** a "parallel reader" UI that respects silence — shows two texts, doesn't summarize the third.

5. **"I found this beautiful verse online ('God is our refuge and strength'). Where is it from?"**
   Current capability: yes (it's Psalm 46:1). `python3 -m bible search "refuge and strength"`. **Front-end implication:** a "reverse citation lookup" — paste a quote, find the source.

6. **"Explain the historical context of this verse without preaching to me."**
   Current capability: none — we don't have historical context data. **Roadmap implication:** would require either a curated historical-annotations dataset OR a LLM call that's explicitly scoped to "summarize historical consensus only, cite sources." (Not on our roadmap today.)

7. **"Save this search. Share this with a friend. Email me a PDF of these 10 verses."**
   Current capability: partial. JSON output exists. No save / share / PDF. **Front-end implication:** standard export / share affordances, with citation included automatically.

### Front-end features that would matter to him

- **Big search box, no setup.** Like Google. Type, get verses, click to read.
- **Quick context toggle** — for each verse, "show me the chapter" or "show me 5 verses before/after" without leaving the page.
- **Plain-English summaries, ALWAYS marked as such.** Never conflated with the verse text.
- **No theology coloring.** If the tool has an opinion, it's labeled as "this tradition says X; other traditions say Y."
- **Citation chips** — every quote has a clickable citation that opens the full verse + cross-references.
- **Bookmark / save / share** — basic web app stuff.
- **Works offline / doesn't require an account.**

### What would make him leave

- Any AI-generated commentary presented as if it were scripture
- Forced theological framing ("here's what God wants you to know")
- Aggressive evangelism in copy ("discover the truth")
- Required email signup
- Slow load times

---

## Persona 3 — Dr. Yuki Tanaka, religious-studies researcher (non-Abrahamic focus)

### Background

Academic at a university in Japan. Studies Buddhist-Taoist-Confucian comparative religion, with a side interest in how Abrahamic texts entered East Asian discourse (via Jesuits, colonial contact, modern translations). Reads Japanese, English, classical Chinese; has limited but workable Sanskrit. Reads Hebrew Bible in English translation because her Japanese sources are uneven.

### What she actually wants out of a tool

- **Comparative analysis across traditions, presented neutrally.** She doesn't want a Christian tool that pretends to be interfaith; she wants a tool that's *honest* about its primary corpus (Abrahamic) but *useful* for cross-tradition comparison.
- **Translation transparency.** She wants to see what translation she's reading and ideally the source language. Japanese translations of Bible/Tanakh have interesting editorial choices; she wants to compare.
- **Trails into secondary literature.** When the tool surfaces a cross-reference between Psalm 22 and Mark 15, she wants to know "what does the academic literature say about this connection?" — but she doesn't want the tool to *be* the academic literature.
- **Respect for non-Abrahamic frames.** When her comparison includes Buddhist texts, she doesn't want a "Bible explains the Dhammapada" frame; she wants parallel presentation.
- **Reproducibility and citation discipline** — same as the academic, but for cross-tradition work the citation discipline matters even more because she can't verify Hebrew without looking it up.

### Things she'd actually request (concrete examples)

1. **"Compare Genesis 1 (creation account) to Genesis 2 (creation account) to Enuma Elish to the Rigveda Nasadiya sukta. Show me primary sources side-by-side."**
   Current capability: partial. Genesis 1 + Genesis 2 are in our corpus. Enuma Elish and Nasadiya sukta are NOT. **Roadmap implication:** if we want this user, we need to ingest non-Abrahamic primary sources. Rigveda (Public Domain translations exist) is the obvious target; Enuma Elish too. **This is a Phase 4+ rung.**

2. **"Show me every place Jewish and Christian commentators disagree on a verse — Midrash Rabbah vs. Church Fathers."**
   Current capability: no. We don't have Midrash or Patristic commentary corpora. **Roadmap implication:** these are separate datasets with their own licensing. *Not in scope for this repo* (different tradition, different scope).

3. **"Trace how Psalm 22 entered East Asian religious discourse — Japanese Bible translations, Jesuit missionary writings, modern Japanese theological works."**
   Current capability: partial on the source side (Psalm 22 is in the corpus). The "how it entered East Asian discourse" is bibliography work, not corpus work. **Roadmap implication:** out of scope for this repo; this is her literature-review work, not a corpus tool.

4. **"Compare what 'salvation' (יְשׁוּעָה / σωτηρία) means in the Hebrew Bible vs. the New Testament, with every occurrence and its context."**
   Current capability: partial. The corpus has every occurrence. The contextual analysis isn't a corpus function — but the tool could *enable* her work by giving her a clean concordance: every occurrence of a lemma, in order, with verse-level context. **Front-end implication:** a "concordance" view that lets her scan 200 verses quickly.

5. **"Show me the Strong's numbers used in Isaiah 53 with frequency distribution and gloss."**
   Current capability: yes per-lemma, no aggregate. **Roadmap implication:** a "book summary" feature that aggregates Strong's stats per book.

6. **"What does the Quran say about Jesus / Isa? Cross-reference to Christian sources."**
   Current capability: partial. Quran corpus has it (`python3 -m bible quran "Mary"`). Christian cross-reference side is `bible.references`. **Front-end implication:** cross-tradition query that doesn't privilege either source.

7. **"I need to write a paper comparing Islamic and Christian views on prophecy. Generate a bibliography seed from the cross-reference structure."**
   Current capability: no. We have cross-reference EDGES but not academic citations. **Roadmap implication:** we'd need a curated bibliography dataset (real academic citations, not auto-generated).

### Front-end features that would matter to her

- **Source transparency.** Always show: which edition, which tradition's textual tradition, which translation, who translated it, when.
- **Multi-tradition comparison view.** Genesis 1 + Quran 32 + Tao Te Ching 25 (if we had it) — pure parallel display, no synthesis.
- **Lemmatized concordance.** "Every occurrence of word X in text Y" with verse-level context.
- **Cross-reference graph with edge-type labels.** "Quote-allusion," "thematic parallel," "linguistic cognate," etc. — currently openbible.info's edges are just votes-counted, no edge type.
- **Honest scope disclosure.** The tool says "I have Abrahamic corpora. For non-Abrahamic comparison, here's where to find the public-domain primary sources" rather than pretending to be interfaith.
- **Citation export for academic papers.** BibTeX, with primary source + translation attribution.

### What would make her leave

- Any theological framing of comparative analysis
- Hidden theological biases in the "cross-tradition comparison" mode
- Translation choices that hide primary source language
- AI-generated "synthesis" of cross-tradition parallels (she does this work herself)
- Marketing copy that pretends the tool is interfaith when it's really Abrahamic-first

---

## Cross-cutting design implications

These three personas share more than they differ on the structural side:

### What all three need from the front-end

1. **Citation-first rendering.** Every verse, every quote, every cross-reference has a clickable citation. None of them trust an unsourced assertion.
2. **Source/translation transparency.** Always show what edition, what translation, what text-family the data is from. Persona 1 wants this for textual criticism; Persona 2 wants this so he knows he's reading a particular tradition's voice; Persona 3 wants this for cross-tradition honesty.
3. **Reproducible queries.** "I should be able to come back tomorrow and run the same query and get the same results." None of them want a "personalized" feed.
4. **Local-first / offline-capable.** Persona 1 flies to conferences; Persona 2 travels; Persona 3 has spotty institutional access. They all want the tool on their laptop.
5. **No AI homily / no spiritual authority claims.** This is in the runtime contract already. Persona 2 and Persona 3 would leave instantly if violated; Persona 1 would file a peer-review complaint.

### What differs

| | Persona 1 (academic) | Persona 2 (secular seeker) | Persona 3 (comparative) |
|---|---|---|---|
| **Primary corpus they'd use** | Hebrew Bible + LXX + DSS + Tanakh | Bible + Quran + Tao Te Ching + Dhammapada (broad) | Tanakh + Quran + Buddhist canon + Hindu canon |
| **Front-end complexity they'd accept** | High (textual apparatus, morphology, variants) | Low (Google-style search, one click) | Medium (cross-tradition comparison, lemma tools) |
| **What they'd cite to colleagues** | "I queried your tool for X, got Y, my methodology footnote is Z" | "Here's a quote I saved" | "I cross-referenced Tanakh X with Buddhist Y via your tool" |
| **Frontend aesthetic preference** | Academic / minimal / dense | Warm / readable / spacious | Comparative / parallel-display / structured |
| **Sensitive to theology** | Yes (but in a scholarly frame) | Yes (in a marketing frame) | Yes (in any frame) |
| **Save/share needed?** | Maybe (export citations) | Yes (bookmark + share) | Yes (export to BibTeX) |
| **Mobile needed?** | No | Yes | Maybe |

### Front-end architecture implications

Given the diversity, I'd build the front-end in **three layers** rather than one app:

**Layer 1 — "Reader" (Persona 2)**
- Web app, single-page, mobile-responsive
- Big search box → results with citation chips
- "Show me the chapter" inline expansion
- Bookmark + share buttons
- Plain-English summaries, always marked as such
- Runs on a hosted static site OR locally with `bible serve`

**Layer 2 — "Scholar" (Persona 1)**
- Same web app, different mode
- Shows: original language + translation + Strong's + morphology + cross-reference graph
- Query builder: "find every hapax legomenon in Isaiah 53" or "compare MT vs LXX for chapter X"
- Export to BibTeX / CSV
- Probably a desktop app or a heavy web-app mode

**Layer 3 — "Comparative" (Persona 3)**
- Side-by-side parallel display: Tanakh column / Quran column / Buddhist column
- Cross-tradition lemma lookup ("what does 'mercy' mean in each tradition's canonical text?")
- Translation notes: "Japanese translation X chose this word; English translation Y chose that word"
- Probably a separate page from the main reader; not the default UI

All three layers share the same **CLI backend** (which we already have) and the same **data + retrieval substrate**. The front-end is a thin layer over the CLI.

### Implementation sequencing

If I were building this front-end, I'd start with **Layer 1 (Reader)** because:
1. It serves the broadest audience (anyone with curiosity about a text)
2. It exercises the entire CLI backend
3. It's the smallest front-end surface
4. Personas 1 and 3 will use it for casual queries even if their deep-work uses Layer 2/3

Then **Layer 2 (Scholar)** because:
1. Persona 1 is the highest-leverage early user (her endorsement matters for academic adoption)
2. It's mostly "more toggle-panels on Layer 1" architecturally
3. It introduces the cross-reference graph visualization (the hardest UI piece)

**Layer 3 (Comparative)** last because:
1. Persona 3 represents the smallest user base
2. It requires non-Abrahamic corpora we don't have yet
3. The honest-scope-disclosure UI ("this is Abrahamic-first; here's where to find Buddhist primary sources") is its own design challenge

### Open design questions

- **Web app vs. native app vs. CLI?** All three personas would accept a polished web app. None of them want a native app that needs an App Store round-trip. CLI is for developers / AI agents; the front-end is for humans.
- **Self-hosting story?** All three would prefer "I can run this on my laptop." But also: "I'd like to try it before I install anything." So: hosted demo + downloadable single-binary / Docker image.
- **What's "the answer"?** Persona 1 wants "no answer, just data." Persona 2 wants "summaries." Persona 3 wants "cross-tradition parallels, not synthesized." The front-end has to NOT pick one — it has to expose all three modes and let the user choose.

### What NOT to build

- A "Bible chatbot" or "Talk to Moses" mode. Persona 2 would leave; Persona 1 would be horrified; Persona 3 would call it cultural appropriation.
- AI-generated homilies, devotionals, or sermons. Out of scope per `RUNTIME_CONTRACT.md`.
- Synthesis-mode for cross-tradition comparisons. Persona 3 explicitly doesn't want it.
- Anything that requires user accounts by default. All three would abandon the tool at signup.
- Anything that hides which edition / translation is being shown.

### What to build first (one-week MVP)

Given all of the above, the **one-week MVP** I'd ship:

1. **Web UI** that wraps the existing CLI as a thin layer. Backend is Python (FastAPI), frontend is single HTML page with HTMX-style progressive enhancement. No build step, no SPA framework, no JS bundler. Keeps it local-host-friendly.
2. **Three modes**:
   - **Reader** (Persona 2 default): search box → results with citation chips
   - **Scholar** (Persona 1 toggle): adds original-language + Strong's + cross-reference panel
   - **Compare** (Persona 3 toggle): side-by-side parallel display
3. **JSON API** at `/api/<command>` mirroring the CLI — so AI agents and external tools can hit the same backend.
4. **No accounts. No tracking. No cloud lock-in.** Runs locally; can be deployed to a VPS; can be served from a static export.

If that MVP lands cleanly, Layer 2's cross-reference graph visualization and Layer 3's non-Abrahamic corpora are the natural next steps — and both depend on user feedback from the MVP to know which direction to invest in.

---

## Closing note

The thing that's interesting about these three personas: they're not in tension. They want **the same tool with different surfaces**. The data, the retrieval, the citation discipline — all the same. Only the rendering layer changes. That's a healthy sign for the architecture: if we build the right substrate, the front-end is mostly UI work, not new engineering.

The biggest risk is the temptation to add AI-generated "synthesis" modes. Persona 2 doesn't want it (paraphrased citations), Persona 3 explicitly forbids it (academic honesty), and Persona 1 would tolerate it only if it's rigorously labeled and scoped to "academic consensus summaries with citations to the underlying papers." That's a hard mode to ship well; defer it.

---

## Persona 4 — Sarah, the lay-faithful reader (the missing majority)

### Background

This is intentionally not named "Rabbi Sarah" or "Pastor Sarah" or "Imam Sarah." The persona spans traditions because the *relationship with the text* is the same even though the *tradition* differs. She's a 35-year-old active member of her congregation/mosque/synagogue/temple. Not a scholar, doesn't read Hebrew/Arabic/Greek/Sanskrit, has never opened BibleWorks and never will. Uses a study Bible or a printed Quran with commentary when she studies. Active on social media where she sometimes sees verses quoted out of context and finds it annoying.

This is the largest single user population by an order of magnitude — every "Reader"-style use case study suggests lay-faithful are 10-100× more numerous than academics, and "want to read their own tradition's text better" is the most-cited reason people interact with religious corpora online. **If we get this persona wrong, the failure modes are concrete and harmful**, not just "they leave" — see below.

### What she actually wants

- **Read the actual text, not commentary on it.** When she opens a verse, she wants the verse — not an AI summary, not a "what this means for you today," not a parallel theological interpretation. She has her own pastor/rabbi/imam/spiritual director for that. The tool's job is to give her the words.
- **Cross-reference for personal study.** "Where else does this idea appear in the Bible/Quran/Torah?" is a real and frequent question. She wants answers her pastor could give her if she asked, but at 11pm on a Tuesday when she's reading.
- **Multiple translations side-by-side, clearly labeled.** "How does the KJV render this verse vs. the NIV vs. the NRSV" is a normal study question. She wants to *see* the differences, not be told what the differences mean.
- **Original-language awareness, light touch.** She's curious that the "sheol" in Psalm 6:5 is the Hebrew word שְׁאוֹל and it has a meaning the English doesn't quite capture — but she's not going to learn Hebrew. Show the original word once with a short gloss; don't lecture about Hebrew morphology.
- **Strong's / lemma lookup for "what's this word mean."** She sometimes sees a word in her study Bible (e.g. "chesed" in the Old Testament) and wants a quick definition. Strong's numbers + a one-line gloss per number is exactly right for this.
- **No surprise theology, no AI sermon.** She does NOT want the tool to:
  - tell her what her tradition teaches
  - tell her what to believe
  - generate devotional content
  - generate "discussion questions for your Bible study group"
  - suggest she pray
  - refer to her tradition's authority figures as if the tool had standing to do so

This last point is non-negotiable. The runtime contract (`RUNTIME_CONTRACT.md`) forbids exactly this kind of impersonation; Sarah is the user that contract was written for.

### Things she'd actually request (concrete examples)

1. **"Read me Psalm 23, but show me the Hebrew word for 'still waters' with a one-line gloss."**
   Current capability: yes. `python3 -m bible parallel "Psalms 23:2" --translations kjv,niv,nrsv` + a Hebrew-with-nikkud edition showing מֵ֣י מְנוּחֹ֑ת and a brief note that מְנוּחָה means "rest" / "settled place." **Front-end:** verse view with translation columns + original-language sidebar with short gloss.

2. **"Where else in the Bible does 'the Lord is my shepherd' get quoted or alluded to?"**
   Current capability: yes. `python3 -m bible references "Psalms 23:1" --hops 2` shows 75 outgoing references including John 10 (the Good Shepherd), Hebrews 13:20 (the great Shepherd), etc. **Front-end:** "See also" panel under each verse; clickable to full citation graph.

3. **"I'm leading a Bible study on Wednesday. Help me find 3 verses about hospitality in the OT that aren't 'love your neighbor.'"**
   Current capability: partial. `python3 -m bible semantic "hospitality" --tradition judaism --top-k 30` returns relevant verses. She would still have to read through and curate. **Front-end:** search results with semantic similarity score visible so she can self-filter; "I've already saved these" state per user (no account, so just sessionStorage or URL-encoded list).

4. **"What's the Hebrew word for 'lovingkindness' and how many times does it appear in the Psalms?"**
   Current capability: partial. She can look up H2617 (`python3 -m bible strongs H2617`) and see the gloss ("lovingkindness, lovingkindness, mercy") and the full definition. Counting occurrences across the corpus requires a bulk query. **Roadmap:** a "concordance" feature — "all verses with this lemma" — would be exactly right for her.

5. **"My pastor said Paul quotes the Greek poets in Acts 17. Which verses?"**
   Current capability: partial. `python3 -m bible search "poets" --strongs` finds Acts 17:28 with the Areopagus quote ("In God we live and move and have our being" — citing Epimenides / Aratus). **Front-end:** search bar; result includes the cross-reference annotation. **Roadmap:** a "classic-source citations in the Bible" feature (Greek poets, OT references to Canaanite myths) would be a delightful unexpected discovery for her.

6. **"I want to memorize Psalm 23. Give me a way to study it verse by verse, hide the text, and test myself."**
   Current capability: no. **Roadmap:** memorization / spaced-repetition tool would be a high-value feature for lay-faithful. Not a corpus problem; a UI problem. But the corpus feeds it.

7. **"I saw a meme that quoted Isaiah 53:5 ('by his stripes we are healed'). What does the rest of the chapter say?"**
   Current capability: yes. `python3 -m bible parallel "Isaiah 53"` gives all 12 verses of the chapter. **Front-end:** reverse citation lookup (paste a quote, find the source + the rest of the chapter) would be perfect.

8. **"Show me the chapter map for Psalms — give me a thumbnail of what each psalm is 'about' (without preaching)."**
   Current capability: partial. Each psalm is in the corpus. The "what's it about" is not in the corpus. **Roadmap:** requires a curated psalm-summary dataset (community project, public domain). Worth doing.

### Front-end features that would matter to her

- **Translation toggle, not selection.** Don't make her pick a translation at signup. Show all 13 Bible translations side-by-side by default; let her collapse the ones she doesn't read.
- **Original-language sidebar with one-line gloss.** NOT a Hebrew lesson; just "this word in your translation is the Hebrew שלום, which means peace/wholeness/completeness." Three words max.
- **Strong's numbers visible but not mandatory.** Hover for the gloss; click for full entry.
- **Cross-reference panel** that's clearly labeled "Other places this idea appears" — not "scholarly apparatus."
- **No AI synthesis.** This is the runtime contract. She's the user for whom this is non-negotiable.
- **Personal bookmarks / verse lists.** She'd save "Psalm 23" and "Isaiah 53" and "1 Cor 13" to come back to. Local storage, no account.
- **Print / share-a-card.** "I want to print this verse as a one-page PDF to put in my Bible." Or "share on Signal with a citation link." Standard web-app stuff.

### What would make her leave — and why this matters more than other personas

- **AI-generated devotional content** that pretends to be from her tradition's voice: she would recognize this as cultural vandalism and lose trust in the tool forever. Worse, she might share it with her community and damage *their* trust in online Bible study tools generally.
- **Theology drift.** If the tool starts framing verses with "Christians believe X" vs. "Jews believe Y," she's reading an external description of her own tradition, which is patronizing.
- **Trivialization of sacred text.** Showing Psalm 23 next to a Stoic meditation as "basically the same idea" without explicit framing would be disrespectful in a way she would feel.
- **Surprise AI behavior.** Anything that the tool does that she didn't ask for. She came to read, not to be served.
- **Forced interpretation.** Even a "neutral" gloss is interpretive. Make it clear when something is the literal translation, when it's a contextual gloss, and when it's a traditional interpretation from her tradition.

The failure mode for this persona is not "she leaves and writes a negative review." It's "she uses the tool for a year, gradually internalizes an AI-mediated understanding of her own sacred text, and her tradition's actual interpretive community loses a member to a chatbot."

**This is why `RUNTIME_CONTRACT.md` exists.** The four rules — every claim cited, no paraphrased citations, internal diversity surfaced, no spiritual authority impersonation — were not written with Persona 1 (the academic) or Persona 3 (the comparative researcher) in mind. They were written with Persona 4 in mind. If we get her right, we get everyone right. If we get her wrong, we make the world slightly worse for people trying to read their own sacred texts.

---

## Persona 5 — Jordan, the AI engineer / RAG builder (the developer of derivative tools)

### Background

Not a user of religious texts at all. Builds LLM applications for a living — RAG pipelines, agent frameworks, evaluation harnesses, dataset tooling. Has heard about this project, sees that it's a "structured reference tool for religion corpora," and wonders: *can I use this as the retrieval backend for the religion question-answering product I'm building for [client / startup / employer]?*

This is the persona that determines whether this project has *long-term impact* outside the immediate user-facing community. The three religious-text personas (1, 3, 4) determine whether the project is *correct*. Persona 2 determines whether it's *accessible*. Persona 5 determines whether it's *useful at scale* — because if RAG builders can plug this into their stacks cleanly, the tool gets embedded in dozens of downstream applications.

### What they actually want

- **A clean JSON API** for every corpus operation. (We have this — every CLI command supports `--json`.)
- **Stable, predictable schemas.** The data shape shouldn't change between minor versions. (Per ADR-003-style discipline: raw committed, derived gitignored.)
- **Clear license terms** that they can show their legal team. (Public Domain Hebrew, CC-BY English, CC-BY 4.0 cross-references — all documented in `data/*/README.md`.)
- **Self-hostable.** Their client's compliance team won't let them ship a cloud API. Docker image + clear local-runs work.
- **Documentation that reads like an SDK reference, not a religious studies paper.** Method, examples, edge cases, performance characteristics.
- **Pluggable backend support.** The fact that v0.13.0 added OpenRouter means they can swap embedding models without code changes — that's exactly the API surface they want.

### Things they'd actually request

1. **"Does your retrieval layer support batched queries? I need to embed 10,000 questions at once."**
   Current capability: partial. `bible.semantic.search_semantic` accepts a single query. Batching is via the embedder. The `OpenRouterEmbedder` has `batch_size=100` configurable. **Roadmap:** a `bible search --batch-queries file.txt` CLI would be perfect.

2. **"What's the latency / throughput of your hybrid retrieval?"**
   Current capability: unknown (no formal benchmark). The eval harness (`scripts/run_eval.py`) measures *quality* (recall, MRR, nDCG) but not *latency*. **Roadmap:** a `scripts/benchmark.py` that records p50/p95/p99 retrieval latency would help Persona 5 (and us, internally).

3. **"Can I get a Dockerfile + docker-compose.yml that runs the corpus + a simple FastAPI server?"**
   Current capability: no. **Roadmap:** a Dockerfile would be high-leverage for Persona 5. We have a Python package; packaging it as a container with a FastAPI frontend would let them ship.

4. **"I want to evaluate my fine-tuned Llama-3.1-8B against your citation-grounded retrieval baseline."**
   Current capability: yes. `scripts/run_eval.py` already produces MRR / nDCG / recall metrics. **Roadmap:** a `scripts/run_eval.py --against-saved-index baseline.npz` mode that compares two index runs side-by-side would be exactly what evaluation engineers want.

5. **"What's your versioning story? When you bump to v1.0, will v0.14 data files still work?"**
   Current capability: weak. We don't have a stability promise. **Roadmap:** a `docs/stability.md` with a commitment to schema stability for the 0.x series would help Persona 5.

### What would make them leave

- Hidden cloud dependencies ("works on my laptop but only when this internal service is up").
- API breakage between minor versions.
- Unclear licensing.
- Undocumented performance characteristics.
- "Just read the source" answers in lieu of docs.

---

## Persona 6 — Priya, the interfaith dialogue facilitator (briefly)

Different from Persona 3 in important ways. Persona 3 is a researcher who produces academic papers. Persona 6 *runs programs*. She organizes multi-faith reading groups, synagogues-and-mosques joint study sessions, "Christian-Buddhist-Jewish comparative ethics" weekend retreats. She needs materials that work for *mixed audiences* — people who are each rooted in their own tradition but willing to read each other's texts respectfully.

Out of scope for this repo's *first* front-end, but worth mentioning because:
- She's a natural advocate for the tool once it exists
- Her needs overlap heavily with Persona 3 (cross-tradition display) but with different emphasis on "what works for a group setting, not just for one scholar"
- Her use case eventually drives the non-Abrahamic corpus work (Phase 4+)

---

## Updated cross-cutting implications

Adding Persona 4 changes the calculus in one important way: **the front-end MVP can't be tech-bro / minimal-academic only.** It has to feel like a *reading* tool, not a *research* tool. Persona 2 was right that big-search-box-Google-style is the entry point; Persona 4 reinforces that the *initial render* must be the text itself, not commentary on it.

It also doesn't change the three-layer architecture — Reader / Scholar / Comparative — but it does change *which layer is the default*. **Reader is the default for everyone except Persona 1.** Persona 4 doesn't want to opt into "scholar mode" by default; she wants to opt *out* of basic reading and into technical display only when she explicitly wants it.

It also means the MVP rejection criterion shifts: a feature that confuses Persona 4 (e.g. AI-generated sermon) is a *blocker*. A feature that confuses Persona 1 (e.g. doesn't show variant readings) is *missing* but not blocking. Build the Persona-4-shaped MVP first; the rest can iterate on top.

---

## Closing note (updated)

The thing that's interesting about these six personas: they're not in tension. They want **the same tool with different surfaces**. The data, the retrieval, the citation discipline — all the same. Only the rendering layer changes. That's a healthy sign for the architecture: if we build the right substrate, the front-end is mostly UI work, not new engineering.

The biggest risk is the temptation to add AI-generated "synthesis" modes. Persona 2 doesn't want it (paraphrased citations), Persona 3 explicitly forbids it (academic honesty), Persona 1 would tolerate it only if it's rigorously labeled and scoped to "academic consensus summaries with citations to the underlying papers," and **Persona 4 must not be exposed to it under any framing.** That's a hard mode to ship well; defer it indefinitely.

If we ship one persona well, **Persona 4 is the one to ship first.** She's the largest audience, the highest-stakes failure mode, and the one whose trust — once lost — is hardest to rebuild. Get her right and the rest follow.
