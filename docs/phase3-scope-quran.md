# Phase 3 Scope — Quran as the second tradition

> **Status:** Shipped (v0.6.0, 2026-09-09 per ADR-009). Shipped 6 editions in
> `data/quran/`, `bible/quran.py` adapter, CLI `python -m bible quran`, and 10
> sister-script tests (48 passing).
>
> **Read alongside:** `docs/data-schema.md` §2 (Quran illustrative
> schema), `HANDOFF.md` §2 (Phase 3 success state), `COUNCIL.md` §1–§2
> (operating principles).

---

## Why Quran first (and not Torah, Vedas, Tao Te Ching, Dhammapada)

We picked Quran because it's the *most analogous* to the existing Christian
Bible substrate:

| Property              | Christian Bible | Quran |
|-----------------------|-----------------|-------|
| Monotheistic Abrahamic | ✓ | ✓ |
| Public-domain translations | 13 in repo | 20+ English available |
| Surah/Ayah ≠ Book/Chapter/Verse | — | ✓ (schema challenge, but documented in `docs/data-schema.md`) |
| Strong's-style word-level lexicon | ✓ (H/G) | Partial (Lane's, qurandictionary.com) |
| Cross-reference tradition | openbible.info | Tafsir cross-refs (ad-hoc) |
| Council framing in COUNCIL.md | ✓ | ✓ |

If Quran-ingestion fails on the data layer, *every other Phase 3 tradition
is harder*. If it works, the adapter pattern proves itself and the path to
Tanakh, Vedas, Bhagavad Gita, etc. becomes mechanical.

## What the work is (4 deliverables, all stdlib-only)

### 1. Ingestion script: `scripts/ingest_quran.py`

- Download `fawazahmed0/quran-api@1/editions/{edition}.json` for each
  chosen translation (curl + urllib only — no extra deps).
- Repack the flat `{chapter, verse, text}` list into the project's canonical
  shape:

  ```json
  {
    "tradition": "islam",
    "translation": "Saheeh International (1996)",
    "structure": "surah_ayah",
    "divisions": [
      {"id": 1, "name": "Al-Fatihah", "name_transliteration": "al-fatihah",
       "revelation_period": "Meccan",
       "ayahs": [{"ayah": 1, "text": "..."}, ...]},
      ...
    ]
  }
  ```

- Embed a 114-surah metadata table inline (well-known, public-domain —
  Al-Fatihah, Al-Baqarah, …; the canonical names + transliterations are
  not copyrightable).
- Output: `data/quran/{edition}.json` per translation.

**License:** `fawazahmed0/quran-api` is **Unlicense** (public domain,
equivalent to CC0). The translations themselves are sourced from
tanzil.net / qurancomplex.gov.sa — most are explicitly public domain
or distributed under CC-BY-SA. License propagation in the data README
(like `data/references/README.md`).

### 2. Adapter: `bible/quran.py`

A thin module that exposes the same surface as `bible.lookup` but
for Quran:

- `parse_quran_ref("Quran 2:255" | "Al-Baqarah 2:255" | "2:255")` →
  `(surah_id, ayah)`
- `get_quran_verses(translation, surah, ayah)` →
  `[{"surah", "ayah", "text"}]`
- `list_quran_translations()` → `[edition_name, ...]`

Adapter pattern per `docs/data-schema.md` §8. The adapter absorbs the
`surah/ayah` vs. `book/chapter/verse` difference.

### 3. CLI: `python -m bible quran "Al-Baqarah 2:255"`

- One new subcommand `quran` (parallel to `parallel`, `strongs`, `search`,
  `references`).
- Flags: `--translation` (default Saheeh International), `--translations`
  (comma-separated, multi-translation parallel view), `--json`.
- Output: same shape as `parallel` (citation + translation + text).

### 4. Schema-versioned data layer (the long-term win)

Per `docs/data-schema.md` §1, the `tradition` key + `structure` key +
`name_transliteration` field are the additions Christian Bible doesn't
have. They make Phase 3 *config-driven*:

```
data/
├── bible/                         # the 13 Christian translations
│   ├── kjv.json
│   └── translations/*.json
└── quran/
    ├── saheeh-international.json
    ├── yusuf-ali.json
    └── ...
bible/
├── lookup.py                      # Bible lookup (book/chapter/verse)
├── quran.py                       # Quran lookup (surah/ayah)
└── ...
```

The lookup dispatcher picks the adapter by tradition tag. New tradition
= new adapter + new data dir. No core code changes.

## What we're explicitly NOT doing in this round

- **No Arabic lemmatization.** Lane's lexicon is huge (~3,000 pages
  scanned) and not currently in a structured form. Out of scope until
  Phase 3B or later.
- **No tafsir cross-references.** Tafsir cross-references are not as
  well-structured as openbible.info — most are scattered across tafsir
  PDFs. We add Quran cross-references only when a public-domain source
  emerges.
- **No comparative queries yet.** "Find verses about mercy across Bible
  + Quran" is Phase 3+ evaluation work. The Quran schema design
  supports it (the `structure: surah_ayah` tag is the lever) but no
  retrieval code ships until the Quran substrate is real.
- **No Hadith, no Sira, no Islamic jurisprudence.** Tradition scope
  for Phase 3 is Quran first; the rest is downstream.

## Translation shortlist (proposed Phase 3.1 ingest)

| Edition key            | Author            | Source           | License     |
|------------------------|-------------------|------------------|-------------|
| `saheeh-international` | Umm Muhammad      | tanzil.net       | Public domain |
| `yusuf-ali`            | Yusuf Ali (1934)  | tanzil.net       | Public domain |
| `pickthall`            | Marmaduke Pickthall (1930) | tanzil.net | Public domain |
| `mufti-taqi-usmani`    | Mufti Taqi Usmani | tanzil.net       | Public domain |
| `arberry`              | A. J. Arberry (1955) | tanzil.net     | Public domain |
| `abdel-haleem`         | Abdel Haleem (2004) | tanzil.net      | Check before commit |

Five public-domain English translations + the Abdel Haleem (more modern,
clearer English) is enough for a real "parallel view across translations"
similar to what Bible users have now.

## Acceptance criteria for Phase 3.1 (the Quran ship)

A user can run `python -m bible quran "Al-Baqarah 2:255"` and see:

- The Arabic (Uthmani script) verse text
- Saheeh International English alongside
- The surah name + transliteration
- A citation like `Quran 2:255 (Al-Baqarah)` that resolves consistently
- The verse is reachable via `parse_quran_ref("2:255")` too

If those five work, the adapter pattern is proven and Phase 3 is a
mechanical extension to other traditions.

## Estimated size of the ship

- 114-surah metadata table: ~3 KB inline
- Ingestion script: ~80 lines (stdlib urllib + json)
- Quran adapter: ~150 lines (mirrors `bible/lookup.py` shape)
- CLI integration in `bible/__main__.py`: ~30 lines
- Sister-script tests: ~10 tests
- Data files: 5 translations × ~1.5 MB each = ~7.5 MB committed
- Docs: this scope doc + CHANGELOG + HANDOFF update + ADR-009 (Phase 3
  substrate decision)

**Estimate:** ~600 lines of code, 1 working day of focused time. Stdlib
throughout (ADR-001 consistent).

## Risks and open questions

1. **Arabic rendering.** The repo doesn't currently have a Hebrew/Greek
   text display problem because the search/lookup uses ASCII-safe
   operations and the JSON loads lazily. Quran adds Arabic script, which
   has the same UTF-8 concerns Hebrew/Greek already exercised. The
   CI workflow's Python 3.10–3.13 matrix already proves cross-platform
   Unicode works. **Risk: low.**

2. **Citation ambiguity.** Quran 2:255 is unambiguous, but
   "Quran 2:255" vs. "Surah Al-Baqarah 2:255" vs. "The Verse of the
   Throne" all refer to the same verse. The adapter must accept all
   three. **Risk: low — well-defined parsing.**

3. **Surah naming.** "Al-Fatihah" vs. "Al-Faatihah" vs. "Fatihah" vs.
   "The Opening" — translations differ on the article prefix. Use the
   canonical Arabic-with-article as the primary key, accept English
   aliases as a secondary alias table. **Risk: low — handled by the
   same `BOOK_ALIASES` pattern.**

4. **Edition selection politics.** Picking which English translations
   to include is a Council-level decision per `COUNCIL.md` §1 ("No
   favored tradition. No anti-religious bias."). The proposed
   shortlist above is the canonical historical set (Saheeh, Yusuf Ali,
   Pickthall — the same trio every Quran study Bible uses); Abdel
   Haleem and Arberry are modern academic alternatives. **Risk:
   medium — but the design supports adding/removing editions without
   schema changes.**

5. **The bigger question.** Does the project *want* Phase 3 to happen
   now, or should we keep the focus on Phase 1 Christian-substrate
   completeness and Phase 2 generative work? HANDOFF §1 says
   multi-tradition is "long-term, by design not by plan" — which means
   we *can* build it but don't *have* to ship it in 2026. This scope
   doc lets the answer be "yes when we have a day to give it" rather
   than "yes but where do we start?".

## What I recommend

**Don't ship this in the next block.** This scope doc IS the deliverable
for this scout. The next block can be:
- ADR-009 (Milestone 3B embedding model) — if the priority is "make
  retrieval better"
- Refining the openbible cross-ref engine — if the priority is "make
  the existing data more useful"

When Phase 3 work *does* start, this doc tells the next agent exactly
what the work is and what's been ruled out.

## Companion ADR

When Phase 3.1 actually ships, draft **ADR-009 — Quran as Phase 3 pilot
tradition**, capturing:
- Why Quran over Torah/Vedas/Gita/etc. (this doc, distilled)
- The adapter pattern as the long-term scaling strategy
- License propagation for Quran-derived data (Unlicense + per-translation
  attribution)
- Council approval status (the translation shortlist is a Council call)
