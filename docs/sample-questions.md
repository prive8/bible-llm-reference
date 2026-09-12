# Sample Questions by Persona & Front-End

> **Purpose:** a quick, scannable reference. Pick a persona, look at
> what kind of front-end suits them, then see the sample questions
> they'd actually ask. Designed to be the first thing a new contributor
> reads when scoping a front-end feature.
>
> For the long-form per-persona narrative (wants, must-not-haves,
> concrete feature requests), see [`docs/audience_expectations.md`](./audience_expectations.md).
> For cross-persona patterns, see [`docs/audience-similarities.md`](./audience-similarities.md).

---

## Persona 1 — Dr. Aisha (biblical-studies scholar)
**Type:** academic, original-language reader
**Front-end:** *Scholar* layer — original language + Strong's + cross-reference graph + reproducible citations

### Questions she'd ask
1. *"Show me the textual variants between MT and LXX for Isaiah 53."*
2. *"Find every hapax legomenon in the book of Isaiah."*
3. *"Trace the citation graph for Psalm 22 — depth 2, with edge weights visible."*
4. *"Compare JPS 1917, KJV, and NRSV for Psalm 23 side-by-side, with Strong's gloss on every Hebrew lemma."*
5. *"List every Strong's number used in the Pastoral Epistles with frequency and gloss."*

---

## Persona 2 — Marcus (secular wisdom-seeker)
**Type:** curious general reader, no theological commitment
**Front-end:** *Reader* layer — big search box, plain-English summaries clearly marked as such

### Questions he'd ask
1. *"What does the Quran say about mercy?"*
2. *"What does the Sermon on the Mount say about anger, and how does the Dhammapada talk about the same thing?"*
3. *"Show me the most famous verses about forgiveness across all three Abrahamic faiths."*
4. *"I have this quote: 'judge not lest ye be judged'. Where is it from, and what comes right before and after it?"*
5. *"Give me a 1-paragraph summary of Genesis 1 — clearly labeled as a summary, not scripture."*

---

## Persona 3 — Dr. Yuki Tanaka (non-Abrahamic religious-studies researcher)
**Type:** comparative-research academic
**Front-end:** *Comparative* layer — side-by-side parallel display, translation notes, source transparency

### Questions she'd ask
1. *"Show Genesis 1, Genesis 2, Enuma Elish, and the Rigveda Nasadiya sukta side by side."*
2. *"Compare what יְשׁוּעָה (OT) and σωτηρία (NT) mean — every occurrence in their original languages."*
3. *"What does the Quran say about Isa, and how do Christian sources quote him in return?"*
4. *"Generate a BibTeX export from the cross-reference structure for Psalms 22 and 69."*
5. *"Show me every cross-tradition parallel to Isaiah 53 — at least two passages per tradition."*

---

## Persona 4 — Sarah (lay-faithful reader) — *the load-bearing persona*
**Type:** active member of her tradition, reads to understand her own text
**Front-end:** *Reader* layer (default) — verse view + cross-references + brief original-language gloss; **no AI sermon**

### Questions she'd ask
1. *"Read me Psalm 23 — and show me the Hebrew word for 'still waters' with a one-line gloss."*
2. *"Where else in the Bible is 'the Lord is my shepherd' quoted or alluded to?"*
3. *"I'm leading a Bible study on Wednesday. Find 3 verses about hospitality in the OT that aren't 'love your neighbor'."*
4. *"I saw a meme quoting Isaiah 53:5. What comes right before and after it?"*
5. *"Show me a chapter map for the Psalms — one-line summaries (clearly labeled) so I can find a psalm for a friend's funeral."*

---

## Persona 5 — Jordan (AI engineer / RAG builder)
**Type:** software engineer integrating this as a backend
**Front-end:** not really a UI user — wants **JSON API docs + SDK** + pluggable embedder backend

### Questions they'd ask
1. *"What's the latency p50/p95/p99 of `bible.semantic.search_semantic()` on the local default index?"*
2. *"Does your retrieval layer support batched queries from a file?"*
3. *"Show me a Dockerfile + docker-compose that exposes the corpus + a simple FastAPI server."*
4. *"Compare two index runs side-by-side: my old local-default vs a fresh build."*
5. *"What's your version-stability promise between minor releases?"*

---

## Persona 6 — Priya (interfaith dialogue facilitator)
**Type:** runs mixed-audience programs
**Front-end:** *Comparative* layer + group-reading-friendly handout generator

### Questions she'd ask
1. *"Generate a 1-page handout for a synagogue-and-mosque joint study group on 'mercy in scripture' — citations from Tanakh and Quran, side by side, neutral framing."*
2. *"What three texts (one Jewish, one Christian, one Muslim) each tradition holds sacred on hospitality?"*
3. *"Show me where Genesis 1's 'let us make man' parallels 'you are all returning to God' in Quran 31."*
4. *"List 5 themes that appear in all three Abrahamic traditions — with a verse from each tradition that exemplifies the theme."*
5. *"What does each tradition's calendar call this week — by name and by what they commemorate?"* (might be a stretch goal for a later release)

---

## Quick navigation

| Persona | Front-end layer | Sample count |
|---|---|---|
| 1 — Aisha (academic) | Scholar | 5 |
| 2 — Marcus (seeker) | Reader | 5 |
| 3 — Yuki (comparative) | Comparative | 5 |
| 4 — Sarah (lay-faithful) | Reader (default) | 5 |
| 5 — Jordan (engineer) | API + SDK | 5 |
| 6 — Priya (facilitator) | Comparative + handout | 5 |

**Designing a new front-end feature?** Pick the persona whose questions it serves, look at what they'd ask, and aim your UI at those 5 (or similar). If your feature doesn't directly serve at least one persona's question, it probably isn't P0.
