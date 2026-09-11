# Phase 3.3 Scope — Full Tanakh (Prophets + Writings)

> **Status:** Scope complete. Implementation pending (Phase 3.3 rung
> after Torah shipped in v0.11.0). Target version: v0.14.0.
>
> **Note:** The Torah (Five Books of Moses) is already shipped as
> Phase 3.2 in v0.11.0 (`bible/torah.py`, `data/torah/`). This scope
> doc covers the remaining 21 books of the Tanakh.

## What "full Tanakh" means here

The complete **Tanakh** (Hebrew Bible), minus the Torah already shipped
in Phase 3.2. Adds the remaining two of the three sections of the
Jewish canon:

1. **Nevi'im (Prophets)** — 11 books
2. **Ketuvim (Writings)** — 13 books (some grouped: Ezra+Nehemiah,
   1+2 Chronicles, 1+2 Samuel, 1+2 Kings in Sefaria's English)
   Total: **~24 books, ~570 chapters, ~13,000 verses**

### Nevi'im (Prophets)

| Book | Hebrew | English | Chapters | Verses | Notes |
|------|--------|---------|----------|--------|-------|
| Joshua | יהושע | Yehoshua | 24 | 658 | Conquest of Canaan |
| Judges | שופטים | Shoftim | 21 | 618 | Cycle of judges |
| Samuel I | שמואל א | Shemuel I | 31 | 810 | Samuel, Saul, early David |
| Samuel II | שמואל ב | Shemuel II | 24 | 695 | David's reign |
| Kings I | מלכים א | Melachim I | 22 | 816 | Solomon + divided kingdom |
| Kings II | מלכים ב | Melachim II | 25 | 719 | Fall of Israel/Judah |
| Isaiah | ישעיהו | Yeshayahu | 66 | 1,292 | Major prophet (Messianic) |
| Jeremiah | ירמיהו | Yirmiyahu | 52 | 1,364 | Major prophet (lamentations) |
| Ezekiel | יחזקאל | Yechezkel | 48 | 1,273 | Major prophet (visions) |
| Hosea | הושע | Hoshea | 14 | 197 | Minor prophet |
| Joel | יואל | Yoel | 4 | 73 | Minor prophet |
| Amos | עמוס | Amos | 9 | 146 | Minor prophet |
| Obadiah | עובדיה | Ovadyah | 1 | 21 | Minor prophet (shortest) |
| Jonah | יונה | Yonah | 4 | 48 | Minor prophet (short) |
| Micah | מיכה | Mikhah | 7 | 105 | Minor prophet |
| Nahum | נחום | Nachum | 3 | 47 | Minor prophet |
| Habakkuk | חבקוק | Chavaquq | 3 | 56 | Minor prophet |
| Zephaniah | צפניה | Tsefanyah | 3 | 53 | Minor prophet |
| Haggai | חגי | Chagai | 2 | 38 | Minor prophet |
| Zechariah | זכריה | Zecharyah | 14 | 211 | Minor prophet |
| Malachi | מלאכי | Malachi | 3 | 55 | Minor prophet |
| **Nevi'im total** | | | **~378** | **~9,295** | |

### Ketuvim (Writings)

| Book | Hebrew | English | Chapters | Verses | Notes |
|------|--------|---------|----------|--------|-------|
| Psalms | תהלים | Tehillim | 150 | 2,461 | Longest book (Songs) |
| Proverbs | משלי | Mishlei | 31 | 915 | Wisdom literature |
| Job | איוב | Iyov | 42 | 1,070 | Wisdom literature (suffering) |
| Song of Songs | שיר השירים | Shir HaShirim | 8 | 117 | Poetry |
| Ruth | רות | Rut | 4 | 85 | Narrative |
| Lamentations | איכה | Eikhah | 5 | 154 | Poetry |
| Ecclesiastes | קהלת | Kohelet | 12 | 222 | Wisdom literature |
| Esther | אסתר | Ester | 10 | 167 | Narrative |
| Daniel | דניאל | Daniel | 12 | 357 | Apocalyptic |
| Ezra | עזרא | Ezra | 10 | 280 | Post-exilic history |
| Nehemiah | נחמיה | Nechemyah | 13 | 406 | Post-exilic history |
| Chronicles I | דברי הימים א | Divrei HaYamim I | 29 | 943 | Genealogies + history |
| Chronicles II | דברי הימים ב | Divrei HaYamim II | 36 | 822 | History (ends with Cyrus) |
| **Ketuvim total** | | | **~362** | **~8,099** | |

### Combined totals (Phase 3.3 = Nevi'im + Ketuvim)

| Metric | Count |
|---|---|
| Books | ~24 |
| Chapters | ~740 |
| Verses | ~17,400 |

When added to Torah (Phase 3.2), the full Tanakh has ~30 books, ~927 chapters, ~23,000 verses (the count is approximate because Sefaria sometimes splits books like Samuel/Kings differently than other sources).

## Sources

Same as Torah: Sefaria API (`https://www.sefaria.org/api/texts/<Book>.<Chapter>`). Editions to ingest:

| Key | Translation | License |
|---|---|---|
| `jps1917-modernized` | Modernized Tanakh (Adam Cohn, 2013, based on JPS 1917) | CC-BY (same edition used for Torah) |
| `hebrew-nikkud` | תנ״ך עם ניקוד (tanach.us/Tanach.xml via Sefaria) | Public Domain |

We reuse the same editions across Torah + Nevi'im + Ketuvim so the canon is internally consistent. Attribution preserved in `data/tanakh/README.md`.

## Adapter design

The cleanest path: **generalize the existing Torah adapter** to handle all 30 books of the Tanakh. Renames:

| Phase 3.2 (current) | Phase 3.3 (target) |
|---|---|
| `bible/torah.py` | `bible/tanakh.py` (the full canon) |
| `BOOKS` list with 5 entries | `BOOKS` list with ~30 entries |
| `data/torah/` directory | `data/tanakh/` directory (move existing 2 JSONs) |
| `python -m bible torah` | `python -m bible tanakh` |
| `--tradition judaism` (already added in v0.11.0) | unchanged |

**Backward-compatibility shim:** `bible/torah.py` becomes a one-line re-export from `bible.tanakh` so existing callers don't break. CLI `bible torah` stays (alias to `bible tanakh` filtered to Torah books).

Actually, on reflection — the rename adds confusion without much benefit. Cleaner alternative:

- Keep `bible/torah.py` as the Pentateuch adapter (5 books, current behavior, current tests)
- Add `bible/tanakh.py` as the broader adapter (~30 books)
- CLI: `bible torah "Genesis 1:1"` → Pentateuch only; `bible tanakh "Joshua 1:1"` → broader canon
- Both adapters share the parsing + lookup logic (factor into `bible/_tanakh_common.py` if duplication gets painful)

**Recommendation:** the second approach. Two adapters, narrow surface each, no renames. Test the boundary explicitly: `t_tanakh_includes_all_30_books`, `t_torah_does_not_include_joshua`.

## Scripture index

Update `scripts/index_embeddings.py` to include Nevi'im + Ketuvim:

| Tradition | Corpus | Estimated passages |
|---|---|---|
| `christianity` | KJV Bible | 37,000 |
| `islam` | Quran Saheeh International | 6,236 |
| `judaism` | **Torah** (5 books, v0.11.0) | 5,846 |
| `judaism` | **Nevi'im + Ketuvim** (24 books, Phase 3.3) | ~17,400 |

Total after Phase 3.3: ~66,000 passages (vs current 49,000). Index build time: ~200s → ~280s on CPU.

## Acceptance criteria

1. `python -m bible tanakh "Joshua 1:1"` prints Hebrew + English from the Nevi'im canon.
2. `python -m bible tanakh "Psalms 23:1"` prints Hebrew + English from Ketuvim.
3. `python -m bible tanakh "Isaiah 53:5"` prints Hebrew + English with the Hebrew showing dagesh-before-sheva nikkud ordering (regression test for the NFC bug from v0.11.0).
4. `python -m bible semantic "Messiah prophecy" --tradition judaism` returns Isaiah 53 with high cosine sim (after index build).
5. `tests/run_all.py` includes 8+ Tanakh-specific tests (similar shape to Torah tests).
6. CI `eval-regression` job threshold unchanged (semantic ≥ 0.25); index rebuild handles the 24 new books.

## Out of scope (v0.14.0)

- **Targum** (Aramaic translations, e.g. Targum Onkelos on Torah) — separate dataset, separate tradition.
- **Talmud / Mishnah** — completely separate canon, separate tradition entry. (These are post-biblical rabbinic literature.)
- **Megillot ordering** (Song of Songs, Ruth, Lamentations, Ecclesiastes, Esther) — Hebrew Bibles order them differently than English Bibles. Sefaria follows the English order; we follow Sefaria's.
- **Apocrypha / Deuterocanonical books** (Tobit, Judith, Maccabees, etc.) — these are in Christian Bibles but not in the Jewish Tanakh. Different canon question; later phase.

## Risks

| Risk | Mitigation |
|------|-----------|
| Sefaria politeness delay × 24 books × 30 ch avg = ~35-40 min ingest | Acceptable; same pattern as Torah ingest. Could parallelize across books with asyncio if needed. |
| Sefaria splits books (Samuel 1+2, Kings 1+2) differently than other sources | Document Sefaria's split in the data README; cross-reference Hebrew canon with the standard Jewish numbering on next iteration |
| Hebrew punctuation differences across books (Psalms uses special markers) | Existing HTML stripper handles most; will likely need a few new patterns for Psalms/Job poetical formatting |
| License drift on Sefaria editions over time | Same as Torah: re-verify version metadata at ingest; preserve attribution |

## Estimated time

| Phase | Time |
|---|---|
| Write scope doc (this file) | ✅ done |
| Update `bible/tanakh.py` adapter (new file) | ~1.5 hours |
| Write `scripts/ingest_tanakh.py` (parallel to ingest_torah) | ~30 min |
| Run ingest | ~35-40 min (mostly waiting on Sefaria) |
| Write 8+ tests | ~30 min |
| Update `scripts/index_embeddings.py` to include Tanakh | ~15 min |
| CI verify | ~10 min |
| Commit + push + verify | ~5 min |
| **Total** | **~3.5 hours** |

## What's pending from Phase 3.2 that applies here

The Hebrew/English key-swap bug from v0.11.0 (where `extract_hebrew` initially called `extract_english` and wrote English text into the Hebrew field) must NOT recur in the Tanakh ingest. The fix is already in `scripts/ingest_torah.py`; mirror it in `scripts/ingest_tanakh.py` and add a test that asserts Hebrew chars are present (not just "the field is non-empty").

The NFC nikkud ordering test (`t_torah_cli_hebrew_alias`) should be mirrored in `t_tanakh_cli_hebrew_alias` so the same Unicode-canonical-order surprise doesn't bite twice.
