# data/tanakh/

Two editions of the full **Tanakh** (Hebrew Bible) — Torah + Nevi'im +
Ketuvim, 39 books, ~927 chapters, ~23,000 verses. Phase 3.3 (v0.14.0).

## Editions

### `jps1917-modernized.json` — Modernized Tanakh (Adam Cohn, 2013)
- **Language**: English
- **Source**: Sefaria API (`https://www.sefaria.org/api/texts/<Book>.<Chapter>`)
- **Underlying text**: JPS 1917 Tanakh (Jewish Publication Society, 1917 AD)
  — Public Domain in the United States (published 1917, >95 years ago)
- **Modernization**: Adam Cohn's 2013 modernization (spelling updates,
  punctuation cleanup, archaic-form removal)
- **License**: CC-BY (Adam Cohn / modernizedtanakh.blogspot.com)
- **Attribution**: "Modernized Tanakh based on JPS 1917 (Adam Cohn, 2013),
  retrieved via Sefaria (www.sefaria.org)."

### `hebrew-nikkud.json` — תנ״ך עם ניקוד (Tanach with Nikud)
- **Language**: Hebrew (with vowel points / nikkud)
- **Source**: Sefaria API; underlying text from `tanach.us/Tanach.xml`
- **License**: Public Domain
- **Attribution**: "Hebrew text from tanach.us/Tanach.xml, retrieved via
  Sefaria (www.sefaria.org)."

## Books (39 total)

Sefaria splits the 12 minor prophets (Hosea..Malachi) into individual
books rather than the Jewish-tradition "Book of the Twelve". This
project follows Sefaria's split because the source data is structured
that way.

### Torah (5)
Genesis, Exodus, Leviticus, Numbers, Deuteronomy

### Nevi'im — Prophets (21)
- **Historical** (6): Joshua, Judges, Samuel I, Samuel II, Kings I, Kings II
- **Major** (3): Isaiah, Jeremiah, Ezekiel
- **Minor** (12): Hosea, Joel, Amos, Obadiah, Jonah, Micah, Nahum,
  Habakkuk, Zephaniah, Haggai, Zechariah, Malachi

### Ketuvim — Writings (13)
Psalms, Proverbs, Job, Song of Songs, Ruth, Lamentations, Ecclesiastes,
Esther, Daniel, Ezra, Nehemiah, Chronicles I, Chronicles II

## Schema

Both editions follow the project canonical multi-tradition format
(`docs/data-schema.md` §2). Each division has an additional `section`
field ("Torah", "Nevi'im", or "Ketuvim") so the consumer can filter by
canon section without re-deriving it from the book name.

```json
{
  "tradition": "judaism",
  "translation": "<human-readable translation name>",
  "key": "<edition key>",
  "language": "en" | "he",
  "structure": "book_chapter_verse",
  "license": "<license string>",
  "source": "Sefaria API (www.sefaria.org)",
  "divisions": [
    {
      "name": "Genesis",
      "name_hebrew": "בראשית",
      "name_transliteration": "Bereshit",
      "section": "Torah",
      "chapters_count": 50,
      "verses": [
        {"verse": 1, "text": "..."},
        {"verse": 2, "text": "..."}
      ]
    },
    ...
  ]
}
```

## Ingestion

Re-run ingestion at any time:

```bash
python3 scripts/ingest_tanakh.py
```

The script is polite (1.05s delay between requests, per Sefaria
robots.txt), retries 3× with exponential backoff on transient failures,
and strips Sefaria's HTML markup (footnote markers, cantillation spans)
so the verse text is plain.

Options:
- `--only-book "Isaiah"` — ingest just one book for debugging
- `--skip-existing` — skip editions whose output file already exists

Total ingest time: ~35-40 minutes (~570 chapters × 1.05s politeness).
Hebrew first (smaller payload, sets baseline), then English.

## Expected verse counts (approximate)

| Section | Books | Chapters | Verses (canonical) | Verses (Sefaria feed, typical) |
|---------|-------|----------|--------------------|-------------------------------|
| Torah | 5 | 187 | 5,852 | ~5,846 (6 missing per Torah phase v0.11.0) |
| Nevi'im | 21 | ~378 | ~9,295 | varies; ~50-200 missing total |
| Ketuvim | 13 | ~362 | ~8,099 | varies; some verse merges |
| **Total** | **39** | **~927** | **~23,000** | typical gap <1% |

Sefaria's feed has minor discrepancies vs canonical verse totals (some
verses merged, some split differently across editions). The runtime
accepts refs that parse cleanly and returns an empty verses list for
out-of-range verses, so a 6-verse gap doesn't break lookups.

## What this is NOT

- This is the **full Tanakh** minus the Torah in `data/torah/` (which
  is the same Sefaria source, kept separate for adapter-narrowness —
  `bible.torah` is Pentateuch-only, `bible.tanakh` is the broader
  canon). Both directories point at the same underlying texts.
- This is **not** the Christian Old Testament (which adds deuterocanonical
  books like Tobit, Judith, Maccabees; see `docs/phase3-scope-tanakh.md`
  for the apocrypha question).
- **Talmud, Mishnah, Targum** — these are post-biblical rabbinic
  literature, not Tanakh. Separate datasets, separate traditions.

## License compatibility

| This dataset | Compatible with |
|--------------|----------------|
| Public Domain (Hebrew) + CC-BY (English) | MIT-licensed code (✓), Strong's CC-BY-SA (✓), openbible.info CC-BY 4.0 (✓), Quran Saheeh International Public Domain (✓) |
