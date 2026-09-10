# data/torah/

Two editions of the Five Books of Moses (Genesis, Exodus, Leviticus,
Numbers, Deuteronomy) — 187 chapters, 5,852 verses total.

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

## Schema

Both editions follow the project canonical multi-tradition format
(`docs/data-schema.md` §2):

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
python3 scripts/ingest_torah.py
```

The script is polite (1.05s delay between requests, per Sefaria
robots.txt), retries 3× with exponential backoff on transient failures,
and strips Sefaria's HTML markup (footnote markers, cantillation spans)
so the verse text is plain.

## Coverage

| Book | Hebrew | Transliteration | Chapters | Verses |
|------|--------|-----------------|----------|--------|
| Genesis | בראשית | Bereshit | 50 | 1,533 |
| Exodus | שמות | Shemot | 40 | 1,213 |
| Leviticus | ויקרא | Vayikra | 27 | 859 |
| Numbers | במדבר | Bamidbar | 36 | 1,288 |
| Deuteronomy | דברים | Devarim | 34 | 959 |
| **Total** | | | **187** | **5,852** |

## What this is NOT

This is the **Five Books of Moses only** (the Torah / Chumash / Pentateuch).
The full **Tanakh** (Prophets + Writings) is Phase 3.3. **Talmud** is a
separate dataset, separate tradition. **Targum** (Aramaic translations)
is separate.

## License compatibility

| This dataset | Compatible with |
|--------------|----------------|
| Public Domain (Hebrew) + CC-BY (English) | MIT-licensed code (✓), Strong's CC-BY-SA (✓), openbible.info CC-BY 4.0 (✓) |
