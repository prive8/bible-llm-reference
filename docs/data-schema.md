# Data Schema — Parallel Structure Across Traditions

> **Last updated:** 2026-07-31 (initial draft, per the
> daily-2026-07-31 review — see `HANDOFF.md` §7.1 for the constraint
> this doc supports)
>
> **Read alongside:** `HANDOFF.md` §7.1 (the data-layer constraint),
> `COUNCIL.md` (the principles), `docs/governance/council-design.md`
> §4.1 (the cross-tradition scoping guardrails).

This document is the answer to the question *"what does a non-Christian
tradition actually look like in the data layer?"* It pairs the existing
Christian Bible JSON schema with parallel-structure examples for four
non-Christian tradition families, so that a future agent building
`bible/lookup.py` (or its successor) has a concrete target for the
"all-traditions-capable from day one" constraint.

The current `bible-query.py` is **hardcoded to KJV** — the schema
below is the *target* the next refactor (HANDOFF.md §5 Milestone 1)
should converge toward, not the present.

The examples below are **illustrative** — they show the schema shape,
not the actual content. When each tradition is ingested, the real
source data populates these shapes.

---

## 1. Christian Bible (existing — the reference shape)

**Canonical structure:** book → chapter → verse.

**Citation format:** `Genesis 1:1` (book chapter:verse).

**Lexicon:** Strong's (H Hebrew, G Greek). Already in the repo.

**Existing schema (from `README.md`):**

```json
{
  "translation": "King James Version (1769) with Strong's Numbers",
  "books": [
    {
      "name": "Genesis",
      "chapters": [
        {"chapter": 1, "verses": [{"verse": 1, "text": "In the beginning..."}]}
      ]
    }
  ]
}
```

**Notes:**
- 13 translations already in the repo. Schema is consistent across
  them (verified 2026-07-31 — Genesis 1:1 present in all 13).
- LXX (Septuagint) is 52 books; includes deuterocanonical. WLCa
  (Westminster Leningrad Codex) is Hebrew source.
- TISCH (Tischendorf Greek NT) is the Greek New Testament source.
- Strong's tags are embedded in KJV text as `<S>nnnn</S>` for word-
  level Hebrew/Greek lookup. The current `bible-query.py`
  `enrich_with_strongs()` function parses these on demand.

---

## 2. Quran (Abrahamic — not in repo yet)

**Canonical structure:** surah → ayah. 114 surahs, 6,236 ayahs
(standard Cairo edition). Not book-chapter-verse; it's a single
continuous division.

**Citation format:** `Quran 2:255` (surah ayah). The famous "Verse of
the Throne" is Quran 2:255. Sometimes written as "2:255" with the
tradition implied, or "Al-Baqarah 2:255" with the surah name.

**Lexicon:** Lane's Arabic-English Lexicon (Edward William Lane,
1863). Public domain. Plus modern additions like the Qur'anic
Arabic Corpus (qurandictionary.com) for morphological data.

**Illustrative schema (what it should look like in the data layer):**

```json
{
  "tradition": "Quran",
  "translation": "Saheeh International (1996)",
  "structure": "surah_ayah",
  "divisions": [
    {
      "id": 2,
      "name": "Al-Baqarah",
      "name_transliteration": "al-baqarah",
      "revelation_period": "Medinan",
      "ayahs": [
        {
          "ayah": 255,
          "text": "Allah - there is no deity except Him, the Ever-Living..."
        }
      ]
    }
  ]
}
```

**Differences from Christian Bible schema:**
- Top-level key is `divisions`, not `books` (more generic — fits
  Quran, Vedas, etc.).
- Each division has `id` (numeric) and `name` (canonical name +
  transliteration). Christian books have only `name`; this is
  additive.
- No `chapters` — the Quran uses a flat two-level structure. To
  preserve the data-layer abstraction, the `bible/lookup.py` surface
  should accept both `book.chapter.verse` and `division.id.ayah`
  styles without hardcoding either.
- Ayahs can be *very* long (Quran 2:282 is the longest, ~128 words).
  Not a unit-paragraph like Bible verses typically are.

**Ingestion note:** Quranic verse numbering is conventional, not
inherent in the original Arabic text. Different editions (Hafs vs.
Warsh) have different numbering for a handful of ayahs. The
`structure` field in the schema should track which edition the
numbering follows.

---

## 3. Bhagavad Gita (Dharmic — not in repo yet)

**Canonical structure:** chapter → verse. 18 chapters, 700 verses.
The Gita is a 700-verse dialog embedded in the Mahabharata; the
verse-level structure is stable across editions.

**Citation format:** `Bhagavad Gita 2.47` (chapter.verse). Note the
period, not the colon — Dharmic convention. Sometimes written as
"BG 2.47" or "Gita 2.47" with tradition implied.

**Lexicon:** Monier-Williams Sanskrit-English Dictionary (1899).
Public domain. Plus the Vachaspathyam edition for cross-reference.

**Illustrative schema:**

```json
{
  "tradition": "Hinduism",
  "text": "Bhagavad Gita",
  "translation": "Swami Sivananda (1996)",
  "structure": "chapter_verse",
  "divisions": [
    {
      "id": 2,
      "name": "Sankhya Yoga",
      "verses": [
        {
          "verse": 47,
          "text": "Thy right is to action alone, never to its fruits..."
        }
      ]
    }
  ]
}
```

**Differences from Christian Bible schema:**
- Same two-level structure as Bible (chapter.verse), but Dharmic
  citation uses period. The lookup surface must accept both `:`
  and `.` separators, or accept the tradition tag and apply the
  right one.
- Chapter names are substantive (Sanskrit names of the yoga / form
  of discipline), not ordinal. Christian chapters are ordinal. The
  schema accepts both via `name`.
- No book level — the Gita is a single book within the Mahabharata.
  To support the full Mahabharata, you'd add a `book` level above
  `divisions`. The schema should be 1-to-4 levels deep (book →
  division → chapter → verse) and lookup should handle any subset.

---

## 4. Tao Te Ching (East Asian — not in repo yet)

**Canonical structure:** chapter only. 81 chapters (the standard
Wang Bi edition). No verse subdivision in the canonical text; verse
breaks are translation-dependent.

**Citation format:** `Tao Te Ching 1` (chapter) or `Dao De Jing 1`.
Note the alternate romanization (Tao/Dao, Te/De) — these are the
same text, different transliteration traditions. The schema should
preserve the chapter's canonical number.

**Lexicon:** No single dominant lexicon. Multiple scholarly editions
(Wing-tsit Chan, D. C. Lau, Ames & Hall, etc.). The translation
metadata field tracks which one.

**Illustrative schema:**

```json
{
  "tradition": "Taoism",
  "text": "Tao Te Ching",
  "translation": "D. C. Lau (1963)",
  "structure": "chapter",
  "divisions": [
    {
      "id": 1,
      "name": null,
      "text": "The way that can be spoken of is not the constant way..."
    }
  ]
}
```

**Differences from Christian Bible schema:**
- Single-level structure. The `divisions` array has `text` directly,
  no inner `verses` or `chapters`. Lookup needs to handle this
  case (the path is `division.id`, not `division.chapter.verse`).
- Verses (where the translation provides them) are a translation-
  added feature, not a canonical feature. The schema should support
  optional `verses` field per chapter, but not require it.
- Two coexisting romanizations (Tao/Dao, Te/De). The `text` field
  carries the canonical name; lookup should accept both as aliases.

---

## 5. Dhammapada (Buddhist — not in repo yet)

**Canonical structure:** vagga (chapter) → verse. 26 vaggas, 423
verses. Sequential verse numbering across vaggas (verse 1 of vagga 2
is verse 24 overall, not verse 1 again).

**Citation format:** `Dhammapada 1.1` (vagga.verse). Some translations
use "I.1" (Roman numeral for vagga). Both are valid.

**Lexicon:** Pali-English dictionaries (PTS Pali-English Dictionary,
Childers). Public domain. Plus the Digital Pali Dictionary (online).

**Illustrative schema:**

```json
{
  "tradition": "Buddhism",
  "text": "Dhammapada",
  "translation": "Max Muller (1881)",
  "structure": "vagga_verse",
  "divisions": [
    {
      "vagga": 1,
      "name": "Yamakavagga (The Twins)",
      "verses": [
        {
          "verse": 1,
          "text": "All that we are is the result of what we have thought..."
        }
      ]
    }
  ],
  "citation_style": "vagga.verse"
}
```

**Differences from Christian Bible schema:**
- Sequential verse numbering across the whole text, not per-chapter
  reset. The schema is identical to chapter-verse, but lookup needs
  to know whether to reset. The `citation_style` field can carry
  this metadata.
- The text has explicit verse numbers in the source (unlike the
  Bible, where verse breaks are translation-added). The schema
  preserves this.

---

## 6. Cross-tradition summary

This is the cheat-sheet a future agent can use to design the
`bible/lookup.py` API surface so it scales without rewrite.

| Tradition     | Canonical structure | Citation format             | Example citation       |
|---------------|---------------------|-----------------------------|------------------------|
| Christian Bible | book → chapter → verse | `Book C:V`               | `Genesis 1:1`          |
| Quran           | surah → ayah         | `Surah A`                 | `Quran 2:255`          |
| Bhagavad Gita   | chapter → verse      | `C.V` (period)            | `Bhagavad Gita 2.47`   |
| Tao Te Ching    | chapter              | `C`                       | `Tao Te Ching 1`       |
| Dhammapada      | vagga → verse        | `V.V` (period or Roman)    | `Dhammapada 1.1`       |
| Vedas           | mandala → sukta → mantra | `M.S.M` (varies)        | `Rig Veda 1.1.1`       |
| Book of Mormon  | book → chapter → verse | `Book C:V`               | `1 Nephi 3:7`          |
| Quran hadith    | collection → book → hadith | `C.B.H`                | `Sahih Bukhari 1.1.1`   |

**API surface implications:**

- The lookup function should accept a tradition tag (e.g., "christian",
  "quran", "gita", "tao", "buddhist-dhammapada") and apply the
  canonical citation format.
- The internal path can be normalized to a common shape:
  `tradition → division[id] → sub_unit[id] → verse[id]` where the
  levels are nullable.
- The lexicon surface accepts a tradition-specific lexicon key
  (e.g., "strongs", "lane", "monier-williams") and routes to the
  right resource.
- Cross-tradition queries (Phase 3) operate on the normalized
  structure. "Verses about forgiveness across all traditions"
  becomes a multi-corpus retrieval problem.

---

## 7. Open questions (the ones that need design before Phase 1 ships)

1. **How is `tradition` keyed?** A controlled vocabulary
   (`"christian"`, `"quran"`, `"gita"`, ...) is simple but rigid. A
   hierarchical key (`"abrahamic.islamic.quran"`) is flexible but
   harder to validate. Recommendation: controlled vocabulary for the
   top-level tradition, free-form `text` field within.
2. **Where do translation variants live?** The same Quran verse in
   Saheeh International vs. Yusuf Ali vs. Pickthall is a translation
   difference, not a textual difference. The Christian Bible schema
   handles this by having multiple top-level JSON files (one per
   translation). The same pattern works for any tradition.
3. **What about traditions without chapter/verse structure?** The
   Tao Te Ching is the easy case (single-level). What about oral
   traditions that resist text representation entirely? The
   `indigenous_elder` agent's domain (see
   `docs/governance/council-design.md` §2) is the harder case —
   oral traditions are not corpus-ready in the same way. Phase 1
   ships as text-only; oral traditions are a Phase 3+ design
   conversation.
4. **What is the cross-reference key?** Two verses are equivalent
   when their content matches; citation strings are not the right
   surface for cross-tradition reference. The `kjv.json` schema
   doesn't carry a stable reference key today. The next version
   should add a cross-tradition reference key at the verse level
   (UUID, OSIS, or a project-specific scheme).

---

## 8. Adapter pattern (proposed)

To keep the data layer convention-light and the lookup surface
tradition-agnostic, the codebase should follow an adapter pattern:

```
data/
├── traditions/
│   ├── christian/
│   │   ├── kjv.json
│   │   ├── ylt.json
│   │   └── ... (the existing 13 translations)
│   ├── quran/
│   │   └── saheeh-international.json
│   ├── gita/
│   │   └── sivananda.json
│   └── ...
├── lexicons/
│   ├── strongs/
│   ├── lane/
│   └── monier-williams/
└── adapters/
    ├── christian.py   # book → chapter → verse normalizer
    ├── quran.py       # surah → ayah normalizer
    ├── gita.py        # chapter → verse normalizer (period citation)
    └── ...
```

The `bible/lookup.py` (or successor) becomes a thin dispatcher over
the adapters. Each adapter exposes the same interface:

```python
class TraditionAdapter:
    def lookup(self, citation: str) -> Verse: ...
    def parse_citation(self, citation: str) -> (tradition, division, sub, verse): ...
    def format_citation(self, division, sub, verse) -> str: ...
```

The adapters absorb the per-tradition quirks (Lane's vs. Strong's,
period vs. colon citation, sequential vs. per-chapter verse
numbering). The lookup surface is uniform.

**This is the design the Phase 1 code should converge toward.** The
current `bible-query.py` is hardcoded to KJV-only; the adapter
pattern is what replaces it.

---

## 9. Versioning

- **v0.1 (2026-07-31)** — initial draft. Five tradition families
  documented (Christian, Quran, Gita, Tao Te Ching, Dhammapada).
  Cross-tradition summary table and adapter pattern proposed.
- **v0.2** — when at least one non-Christian tradition is ingested,
  the schema can be validated against real data and the gaps
  formalized.
- **v1.0** — when the data layer ships multiple traditions, the
  schema is battle-tested. v1.0 reflects what actually works, not
  what looks clean on paper.
