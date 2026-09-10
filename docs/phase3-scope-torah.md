# Phase 3.2 Scope — Torah

> **Status:** Implementation in progress (v0.11.0 target).
> **Driver:** closes HANDOFF §5 Phase 3.2 rung; next-largest non-Quran
> Abrahamic tradition after Bible proper.

## What "Torah" means here

Strictly the Five Books of Moses (Chumash / Pentateuch):

| Book | Hebrew | English | Chapters | Verses | Notes |
|------|--------|---------|----------|--------|-------|
| Genesis | בראשית | Bereshit | 50 | 1,533 | Creation, patriarchs, Joseph |
| Exodus | שמות | Shemot | 40 | 1,213 | Egypt, Sinai, tabernacle |
| Leviticus | ויקרא | Vayikra | 27 | 859 | Priestly code |
| Numbers | במדבר | Bamidbar | 36 | 1,288 | Wilderness wanderings |
| Deuteronomy | דברים | Devarim | 34 | 959 | Moses' final speeches |
| **Total** | | | **187** | **5,852** | |

This is **NOT** the full Tanakh (Prophets + Writings). Full Tanakh is
Phase 3.3 or later. Torah is the right next rung because:
1. Same Tanakh data layer as Quran's Arabic text pattern
2. Well-trodden public-domain sources (Sefaria, eBible, Mechon Mamre)
3. Schema is identical to Quran: book → chapter → verse
4. Tiny corpus (5.8K verses vs 6.2K Quran ayahs) — easy to ship
5. Adding 1 tradition brings tradition coverage from 2 → 3 in semantic search

## Sources

### Primary: Sefaria API (single source, two languages)

`GET https://www.sefaria.org/api/texts/<Book>.<Chapter>`

Returns JSON with:
- `text`: array of English verse strings (Modernized JPS 1917, **CC-BY**)
- `he`: array of Hebrew verse strings with vowel points (Tanach with Nikkud, **Public Domain**)
- `ref`, `heRef`, `book`, `length`, `sections`, `versions[]`

License: Both versions we pull are explicitly Public Domain or CC-BY per
Sefaria's version catalog. Attribution preserved in `data/torah/README.md`.

### Why not Sefaria directly into the repo?

Two reasons:
1. **Schema normalization** — Sefaria returns flat verse arrays; we need
   the same `tradition → book → chapter → verse` shape as Quran.
2. **Source independence** — if Sefaria's API ever changes or rate-limits
   us, our ingest is decoupled and re-runnable from the cached JSON.

So we ingest once into `data/torah/<edition>.json` (committed, public
domain / CC-BY), then the runtime reads from local files.

### Editions to ingest

| Key | Translation | Source | License |
|-----|------------|--------|---------|
| `jps1917-modernized` | Modernized Tanakh (Adam Cohn, 2013) — based on JPS 1917 | Sefaria API | CC-BY |
| `hebrew-nikkud` | תנ״ך עם ניקוד (tanach.us/Tanach.xml via Sefaria) | Sefaria API | Public Domain |

Optional future editions (not in v0.11.0):
- Hebrew: Miqra According to the Masorah (CC-BY-SA)
- English: JPS 1985 (CC-BY-NC, requires further review)

## Adapter surface (mirrors `bible/quran.py`)

```python
from bible.torah import (
    parse_torah_ref,        # "Genesis 1:1", "Gen 1:1", "Bereshit 1:1", "בראשית א:א"
    list_torah_translations,  # ['jps1917-modernized', 'hebrew-nikkud']
    load_torah_edition,       # @lru_cache, returns the JSON for that edition
    get_torah_verses,         # (edition, book, chapter, verse_or_range) -> list[dict]
    run_torah,                # CLI entry: refs + translation choice
)

BOOK_ALIASES = {
    'genesis': 'Genesis', 'gen': 'Genesis', 'gn': 'Genesis',
    'bereshit': 'Genesis',  'בראשית': 'Genesis',
    # ... etc
}
```

CLI: `python -m bible torah "Genesis 1:1" [--translation jps1917-modernized,hebrew-nikkud]`

Output format mirrors Quran:
```
[Genesis 1:1]  (Genesis, chapter 1, verse 1)
  JPS 1917 (Modernized): In the beginning God created the heaven and the earth.
  Hebrew (Nikkud):       בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרץ׃
```

## Semantic index integration

Add `tradition: 'judaism'` (next available slot after `christianity` and
`islam` from v0.7.0). Update:
- `scripts/index_embeddings.py` — no code change needed, just data
- `bible/semantic.py` — `--tradition` choices: `all|christianity|islam|judaism`
- `bible/quran.py` (read-only, for tradition field)
- `bible/lookup.py` (existing tradition dispatch — add jewish entry)

## Acceptance criteria

1. `python -m bible torah "Genesis 1:1"` prints Hebrew + English.
2. `python -m bible torah "Bereshit 1:1"` (transliterated alias) prints Hebrew + English.
3. `python -m bible torah "בראשית א:א"` (Hebrew alias) prints Hebrew + English.
4. `python -m bible semantic "creation of the world" --tradition judaism` returns Genesis 1 with high cosine sim.
5. `tests/run_all.py` includes 8+ Torah-specific tests; suite ≥ 92.
6. CI `eval-regression` job threshold unchanged (semantic ≥ 0.25) — Torah adds passages, doesn't subtract.

## Out of scope (v0.11.0)

- Full Tanakh (Prophets + Writings) — that's Phase 3.3
- Targum Onkelos / Rashi commentary — separate dataset
- Talmud — separate dataset, separate tradition
- Hebrew without nikkud (unpointed) — modern source preference is pointed
- Cross-tradition query routing — separate Phase 3.5 work

## Risks

| Risk | Mitigation |
|------|-----------|
| Sefaria rate limits | One ingest pass, cached locally; runtime reads local files |
| Sefaria API schema drift | Version-pin the JSON shape in adapter; ingest is re-runnable |
| Hebrew encoding bugs | Same Windows UTF-8 reconfigure pattern as Quran; sister-script tests |
| License drift on Sefaria versions | Re-verify version metadata at each ingest; preserve attribution |
