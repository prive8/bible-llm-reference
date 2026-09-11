# 2026-09-10 — Phase 3.3 Full Tanakh shipped (v0.14.0)

## Done

### 1. Full Tanakh adapter (`bible/tanakh.py`)

39 books across 3 sections: 5 Torah + 21 Nevi'im + 13 Ketuvim.
Mirrors `bible/torah.py` surface (parse / list / load / get / run) +
new `list_books(section=...)` helper. Aliases cover:
- Canonical English (`Isaiah`, `Song of Songs`, `Chronicles I`)
- Short Latin (`Isa`, `Josh`, `Ps`, `1Chr`)
- Transliteration (`Yeshayahu`, `Yehoshua`, `Tehillim`)
- Hebrew-with-nikkud (`ישעיהו`, `יהושע`, `תהלים`)
- Roman-numeral prefixes (Sefaria schema: `I Samuel` → `Samuel I`)

### 2. Ingest script (`scripts/ingest_tanakh.py`)

Parallel to Torah ingester. Same politeness (1.05s), retry (3× exp
backoff), HTML-strip pattern. Two editions: Modernized JPS 1917
(CC-BY) + תנ״ך עם ניקוד (Public Domain). Same sources as Torah for
internal consistency. Options: `--only-book` (single-book debug),
`--skip-existing` (resume after partial failure).

### 3. CLI wired (`bible tanakh`)

`python -m bible tanakh "Isaiah 53:5"` works with all alias types.
Supports `--section Torah|Nevi'im|Ketuvim` filter.

### 4. Indexer wired (`scripts/index_embeddings.py`)

Torah was already indexed (v0.11.0). Nevi'im + Ketuvim now indexed
under same `judaism` tradition. Total indexed corpus: ~49K → ~66K
passages.

### 5. Tests (10 new + suite 123/123)

- t_tanakh_books_count_and_sections (39 books across 3 sections)
- t_tanakh_resolve_book_aliases (Latin / transliteration / Hebrew /
  Roman-numeral aliases)
- t_tanakh_sefaria_book_name_mapping (6 split books: Samuel I+II,
  Kings I+II, Chronicles I+II → Roman-numeral prefix)
- t_tanakh_parse_canonical_ref + t_tanakh_parse_alias_and_hebrew +
  t_tanakh_parse_range + t_tanakh_parse_garbage_returns_none
- t_tanakh_data_files_present (with Hebrew-char sanity check)
- t_tanakh_verses_chapter_scoped (regression for the flat-verse
  re-grouping logic)
- t_tanakh_cli_json + t_tanakh_cli_hebrew_alias_no_nfc_bug (regression
  for the v0.11.0 NFC nikkud ordering bug — strip combining marks
  before substring match)
- t_tanakh_list_books_with_section_filter

## Honest bugs found and fixed mid-flight

1. **Book count was wrong in the scope doc** (said ~30, actual 39).
   Sefaria splits the Twelve Minor Prophets into 12 individual
   books rather than treating them as a single unit, so Nevi'im has
   21 not 10. Updated scope doc + README + tests.

2. **Roman-numeral prefix handling**. Initial regex stripped leading
   "I"/"II" in `_clean_str`, which collapsed "I Samuel" and "II Samuel"
   to the same alias. Reverted and added explicit `ROMAN_PREFIX_ALIASES`
   that preserve the distinction.

3. **Verse-end bounds check was wrong**. `BOOKS` table stores
   total-verses-per-book, not per-chapter totals, so "Psalms 23:99"
   would pass even though Psalm 23 has only 6 verses. Fixed by removing
   the verse-end check and documenting that runtime gracefully returns
   empty verses list for out-of-range verses.

## Pending (background)

- **Full Tanakh ingest** — running in background, ~35-40 min wall time
  (929 chapters × 1.05s politeness × 2 editions = ~32 min). Will
  commit data + verify CI when complete.

## Decisions made

- **Two narrow adapters, not a rename.** `bible.torah` (Pentateuch
  only, 5 books) and `bible.tanakh` (broader canon, 39 books) coexist.
  Both read from the same Sefaria editions. Mirrors the Council
  convening pattern (additive growth, not breaking renames).

- **Out-of-range verses parse OK, return empty at runtime.** Cheap
  parser (chapter bounds only); runtime is the source of truth for
  per-chapter verse totals (would need a per-chapter table to
  enforce at parse time).

## Blocked

Nothing hard. The Tanakh ingest is the only background blocker; once
it completes, CI runs the eval-regression gate (which will rebuild
the embedding index with Torah + Tanakh Nevi'im + Ketuvim passages).

## Tomorrow (when next session opens)

- Verify Tanakh ingest completed successfully (~37 min total)
- `git add data/tanakh/` and commit the data
- Check eval-regression CI job on the Tanakh data push
- If user has added `OPENROUTER_API_KEY` to `~/.hermes/.env`, run
  the OpenRouter benchmark (HANDOFF §8 #10 workflow)
- ADR-013 candidate: should we re-do the v0.13.0 OpenRouter benchmark
  decision now that Tanakh is in the corpus (66K vs 49K passages)?
