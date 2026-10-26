# A malformed canonical id crashed the hybrid eval — 2026-10-26

## What happened

The `text-embedding-3-large` held_out evaluation exited 1 with:

```
File "bible/registry.py", line 82, in parse_canonical_id
    verse = int(parts[2]) if len(parts) > 2 else None
ValueError: invalid literal for int() with base 10: 'None'
```

The crash was **non-deterministic**: three runs of the same command
gave one clean run and two crashes. That is because the failing
citation enters the retrieved set only when the semantic top-10 happens
to include it, and the semantic top-10 shifts with the OpenRouter
query embedding.

## Root cause — two defects, one chain

**Defect 1: `make_canonical_id` interpolated `None` as a literal
string.**

```python
# before
return f"{prefix}:{unit_str}.{chapter}.{verse}"
```

With `verse=None` this produced `bible:Psalms.151.None` — a string
containing the word "None" where a number belonged. `parse_canonical_id`
then called `int("None")` and raised.

**Defect 2: `parse_ref` mis-parsed book names containing digits.**

The KJV has 81 books, not 66. Several of the extra ones have names the
reference regex cannot express:

| corpus book name | regex captures |
|---|---|
| `Psalm 151` | book="Psalm", chapter=151 |
| `Psalms (EOB)` | no match |
| `Daniel (EOB)` | no match |
| `3 Esdras` | no match |
| `4 Esdras` | no match |

`REF_RE` allows at most two *alphabetic* words for the book, so
"Psalm 151 1:1" parsed as book="Psalms", chapter=151, verse=None —
a chapter that does not exist (KJV Psalms has 150) and a reference to
a book that was never meant. That is the citation that produced
`bible:Psalms.151.None`.

**The chain:** corpus entry "Psalm 151 1:1" → `parse_ref` mis-parses
it → `make_canonical_id` writes "None" into the id → `align_canonical_id`
→ `parse_canonical_id` → `int("None")` → **the whole evaluation run
dies**, taking the BM25 and semantic results with it.

## The fix

Three changes, in `bible/registry.py` and `bible/lookup.py`:

1. **`make_canonical_id` omits missing components** instead of
   interpolating them. `bible:Psalms.151` rather than
   `bible:Psalms.151.None`. A missing verse is genuinely absent, not
   the number "None".

2. **`parse_canonical_id` degrades instead of raising.** A new
   `_safe_int` helper returns `None` for an unparseable component. A
   malformed id now yields "no verse" rather than killing the caller.

3. **`parse_ref` prefers the longest matching corpus book name.** A new
   `_match_longest_corpus_book` helper matches the actual KJV book list
   longest-first, so "Psalm 151 1:1" resolves to the book "Psalm 151"
   with chapter 1, verse 1. The longer name is always the more
   specific one.

All four previously-broken references now parse correctly:

```
'Psalm 151 1:1'      -> ('Psalm 151', 1, 1, 1)      'bible:Psalm_151.1.1'
'Psalms (EOB) 1:1'   -> ('Psalms (EOB)', 1, 1, 1)   'bible:Psalms_(EOB).1.1'
'Daniel (EOB) 1:1'   -> ('Daniel (EOB)', 1, 1, 1)   'bible:Daniel_(EOB).1.1'
'3 Esdras 1:1'       -> ('3 Esdras', 1, 1, 1)       'bible:3_Esdras.1.1'
```

Ordinary references are unchanged: `Psalms 23:4`, `Matthew 5:4`,
`Psalms 119:151`, `John 3:16` all parse as before. That last one
matters — "Psalms 119:151" must stay book=Psalms, chapter=119, verse=151,
not be captured by the new longest-match rule.

## A second, larger bug found while fixing it: the whole Tanakh branch was dead

Fixing the crash exposed something bigger. `parse_reference` tries
Quran, then Tanakh, then the Christian Bible, then Tanakh again as a
fallback — each wrapped in `except Exception: pass`.

The Tanakh branches unpacked **four** values from `parse_tanakh_ref`,
which returns **three** (`book, chapter, verse_spec`). The unpack raised
`ValueError` on *every* call, and the surrounding bare `except` swallowed
it. **The entire Tanakh branch was dead code.**

Measured impact: **4,924 of 23,206 Tanakh corpus citations (21.2%) could
not be parsed at all** — they resolved to `None`. And because a
`None`-resolved expected citation can never be matched, recall was
silently understated for any query whose expected citations included
one.

Fixed with a `_unpack_tanakh` helper that normalizes the 3-tuple into
`(book, chapter, verse_start, verse_end)`, handling both the
single-verse and the `(start, end)` range forms.

### And a third: the Deuterocanonical books had no aliases at all

The KJV carries 81 books, not 66. `BOOK_ALIASES` covered only the
canonical 66 plus a few extras, so the Deuterocanonical books were
unresolvable by their short names:

| benchmark form | corpus form | resolvable before? |
|---|---|---|
| `Wisdom 7:22-26` | `Wisdom of Solomon 1:1` | **no** |
| `Sirach 15:14-17` | `Sirach 1:1` | no |

`Wisdom` and `Sirach` are now aliased, along with the rest of the
Deuterocanonical set (Tobit, Judith, Baruch, the Maccabees, the
Esdras, Psalm 151, and the EOB variants).

### Coverage after all three fixes

```
christianity    37,247 entries,     0 unparseable (  0.0%)
islam            6,236 entries,     0 unparseable (  0.0%)
judaism         23,206 entries,     0 unparseable (  0.0%)
TOTAL           66,689 entries,     0 unparseable (  0.0%)
```

Before the fixes, 11,160 corpus citations (16.7%) and 3 benchmark
expected citations could not be parsed.

### Effect on the measured scores

Re-running the v2 dev benchmark on the MiniLM index with the fixed
scorer:

| | recall@10 | MRR | primary@1 | nDCG |
|---|---|---|---|---|
| before | 0.189 | 0.300 | 0.229 | 0.257 |
| after | **0.189** | 0.311 | 0.250 | 0.265 |

**Recall@10 is unchanged** — the fix does not change which citations are
found, only the ranking within the top-10 and the secondary metrics.
The improvement is small because the affected set is small: exactly
**one** dev expected citation (`Sirach 15:14-17`) and two on held_out
(`Wisdom 7:22-26` and one other) were unmatchable before.

v1 is unchanged entirely (0.108 / 0.282 / 0.273) — it is scoped to
Christianity, and every fixed citation is Tanakh or Deuterocanonical.

**The CI gates are therefore unaffected**: v2 thresholds (0.08 / 0.15 /
0.14) and v1 thresholds (0.06 / 0.25 / 0.22) all still pass with margin.

## Tests

Five new sister-script tests (165 → 170):

- `t_registry_canonical_id_omits_missing_components` — no `None` is ever
  interpolated, the full form is unchanged, and every id the function
  produces round-trips through `parse_canonical_id` without raising.
- `t_registry_parse_canonical_id_tolerates_malformed` — the historical
  `bible:Psalms.151.None` now parses to verse=None instead of raising,
  and a garbage component degrades the same way.
- `t_lookup_parse_ref_resolves_digit_and_parenthetical_book_names` —
  all five digit/parenthetical book names resolve to the right book,
  and four ordinary references are unchanged.
- `t_registry_tanakh_citations_all_parse` — the Tanakh branch works
  (it did not before), `parse_tanakh_ref` returns the 3-tuple the
  registry expects, and a range citation gives the same shape as a
  single verse.
- `t_registry_corpus_citations_all_parse` — **every one of the 66,689
  corpus citations parses.** This is the test that would have caught
  the dead Tanakh branch, and it is the one worth keeping: a scorer
  that parses data it did not produce needs a test over the whole
  corpus, not over a handful of examples.

## Why this matters beyond the crash

**A crash in one path took down the whole evaluation.** The hybrid
path shares the scorer with the semantic path, so a malformed citation
in one query's retrieved set killed the BM25 and semantic results too.
The run exited 1 with no report, which means the numbers for that
entire configuration were simply unavailable.

**The bug was reachable from the corpus, not from bad input.** Every
corpus entry goes through `parse_reference` on the way to being scored.
Any entry whose citation shape the regex cannot express was a latent
crash. There are 120 corpus entries citing "Psalms (EOB)" and 1 citing
"Psalm 151" — 121 entries that could each have triggered it.

**The non-determinism is the uncomfortable part.** A crash that appears
only sometimes is a crash that can pass CI and then fail on a user's
machine. This one was never caught by the CI gate, because the CI
gate scores the `default` (MiniLM) index, whose retrieved top-10 for
the v1 and v2 benchmark queries never included "Psalm 151 1:1".

The general lesson: **a scorer that parses data it did not produce is
a crash waiting for the right input.** The scorer here was reading
citations out of a 66,689-entry corpus that contains book names the
reference grammar does not model. The fix for that class of bug is not
only to catch the exception, but to make the parser model the corpus —
and to make the failure mode a degraded score rather than a dead run.
