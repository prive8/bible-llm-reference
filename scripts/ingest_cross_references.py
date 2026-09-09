#!/usr/bin/env python3
"""Ingest openbible.info cross-references into a canonical JSON for the bible package.

Source:  data/references/cross_references.txt  (344,800 edges, CC-BY 4.0)
Output:  data/references/cross_references.json   (~25 MB, normalized)

The raw file is one TSV line per edge:

    From_Verse_ID<TAB>To_Verse_IDs<TAB>Votes

where IDs look like ``Gen.1.1`` (book.chapter.verse) and ``To_Verse_IDs`` may be
a single verse or a hyphenated range like ``Prov.8.22-Prov.8.30``. The Votes
column is an integer in roughly [-10, +100]; negative votes mean the openbible
crowdsourcing flagged the edge as low-quality.

This script:
  - Parses each line into a list of canonical {book, chapter, verse} triples.
  - Splits ranges into individual verse edges so the JSON is queryable by any
    verse (the lookup surface can't enumerate a range at query time).
  - Filters out negative-vote edges.
  - Groups outgoing edges by source verse into ``{source_ref: [edges...]}``.
  - Writes a compact JSON. Pretty-printing makes the file 5x larger.

Run from repo root:

    python3 scripts/ingest_cross_references.py

Output structure:

    {
      "metadata": {"source": "...", "license": "CC-BY 4.0", "edges_total": N, ...},
      "outgoing": {
        "Genesis 1:1": [
          {"to": "Proverbs 8:22", "votes": 59},
          {"to": "Proverbs 8:23", "votes": 59},
          ...
        ],
        ...
      }
    }

Verse references use canonical book names (matching CANONICAL_BOOKS in
bible/lookup.py). Lookup by ``"{book} {chapter}:{verse}"`` is therefore
consistent with the rest of the bible package.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Repo-rooted paths
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "data" / "references" / "cross_references.txt"
OUTPUT = REPO_ROOT / "data" / "references" / "cross_references.json"

# Book-name abbreviations from the openbible.info TSV → canonical names.
# Must stay in sync with CANONICAL_BOOKS in bible/lookup.py.
BOOK_ABBREV = {
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
    "Deut": "Deuteronomy", "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth",
    "1Sam": "1 Samuel", "2Sam": "2 Samuel", "1Kgs": "1 Kings", "2Kgs": "2 Kings",
    "1Chr": "1 Chronicles", "2Chr": "2 Chronicles", "Ezra": "Ezra",
    "Neh": "Nehemiah", "Esth": "Esther", "Job": "Job", "Ps": "Psalms",
    "Prov": "Proverbs", "Eccl": "Ecclesiastes", "Song": "Song of Solomon",
    "Isa": "Isaiah", "Jer": "Jeremiah", "Lam": "Lamentations",
    "Ezek": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea", "Joel": "Joel",
    "Amos": "Amos", "Obad": "Obadiah", "Jonah": "Jonah", "Mic": "Micah",
    "Nah": "Nahum", "Hab": "Habakkuk", "Zeph": "Zephaniah", "Hag": "Haggai",
    "Zech": "Zechariah", "Mal": "Malachi", "Matt": "Matthew", "Mark": "Mark",
    "Luke": "Luke", "John": "John", "Acts": "Acts", "Rom": "Romans",
    "1Cor": "1 Corinthians", "2Cor": "2 Corinthians", "Gal": "Galatians",
    "Eph": "Ephesians", "Phil": "Philippians", "Col": "Colossians",
    "1Thess": "1 Thessalonians", "2Thess": "2 Thessalonians",
    "1Tim": "1 Timothy", "2Tim": "2 Timothy", "Titus": "Titus",
    "Phlm": "Philemon", "Heb": "Hebrews", "Jas": "James",
    "1Pet": "1 Peter", "2Pet": "2 Peter", "1John": "1 John",
    "2John": "2 John", "3John": "3 John", "Jude": "Jude", "Rev": "Revelation",
}


def parse_verse_id(s: str) -> tuple[str, int, int] | None:
    """Parse 'Book.Chapter.Verse' → ('Canonical Book', chapter, verse)."""
    parts = s.strip().split(".")
    if len(parts) != 3:
        return None
    book = BOOK_ABBREV.get(parts[0])
    if not book:
        return None
    try:
        return book, int(parts[1]), int(parts[2])
    except ValueError:
        return None


def expand_range(to_str: str) -> list[tuple[str, int, int]]:
    """Expand 'Book.C.V-Book.C.V' or 'Book.C.V' into individual verse triples.

    Only same-book ranges are supported (that's all openbible emits).
    """
    if "-" in to_str:
        # Split on the FIRST hyphen to avoid 'Prov-Name' edge cases.
        a, b = to_str.split("-", 1)
        head = parse_verse_id(a)
        tail = parse_verse_id(b)
        if head is None or tail is None:
            return []
        if head[0] != tail[0] or head[1] != tail[1]:
            return [t for t in (head, tail) if t is not None]
        verses = []
        for v in range(head[2], tail[2] + 1):
            verses.append((head[0], head[1], v))
        return verses
    parsed = parse_verse_id(to_str)
    return [parsed] if parsed else []


def ref_str(book: str, chapter: int, verse: int) -> str:
    return f"{book} {chapter}:{verse}"


def main() -> int:
    if not SOURCE.exists():
        print(f"ERROR: source not found: {SOURCE}", file=sys.stderr)
        print("Download from openbible.info first (CC-BY 4.0):", file=sys.stderr)
        print("  curl -L -o data/references/cross_references.txt \\", file=sys.stderr)
        print("    https://raw.githubusercontent.com/scrollmapper/bible_databases/master/sources/extras/cross_references.txt", file=sys.stderr)
        return 1

    outgoing: dict[str, list[dict]] = {}
    edges_kept = 0
    edges_dropped_negative = 0
    edges_dropped_invalid = 0
    lines_total = 0

    with open(SOURCE, encoding="utf-8") as f:
        for line in f:
            lines_total += 1
            if line.startswith("From Verse"):
                continue  # header
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                edges_dropped_invalid += 1
                continue
            try:
                votes = int(parts[2])
            except ValueError:
                edges_dropped_invalid += 1
                continue
            if votes < 0:
                # Negative votes = openbible crowd flagged as low-quality.
                # The runtime consumer can choose to lower the bar; the
                # default ingest keeps only non-negative signal.
                edges_dropped_negative += 1
                continue

            src = parse_verse_id(parts[0])
            if src is None:
                edges_dropped_invalid += 1
                continue
            src_ref = ref_str(*src)

            for tgt in expand_range(parts[1]):
                tgt_ref = ref_str(*tgt)
                if src_ref == tgt_ref:
                    continue  # drop self-loops
                outgoing.setdefault(src_ref, []).append({"to": tgt_ref, "votes": votes})
                edges_kept += 1

    metadata = {
        "source": "openbible.info cross-references",
        "source_url": "https://www.openbible.info/labs/cross-references/",
        "license": "CC-BY 4.0",
        "license_propagation": (
            "Any artifact derived from this data must carry the CC-BY 4.0 license "
            "and attribute openbible.info when distributed."
        ),
        "raw_lines": lines_total,
        "edges_kept": edges_kept,
        "edges_dropped_negative_votes": edges_dropped_negative,
        "edges_dropped_invalid": edges_dropped_invalid,
        "outgoing_keys": len(outgoing),
        "ingest_date_utc": "2026-09-09",
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "outgoing": outgoing}, f, ensure_ascii=False, separators=(",", ":"))

    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"Wrote {OUTPUT} ({size_mb:.1f} MB)")
    print(f"  lines parsed:         {lines_total}")
    print(f"  edges kept:           {edges_kept}")
    print(f"  edges dropped (<0):   {edges_dropped_negative}")
    print(f"  edges dropped (bad):  {edges_dropped_invalid}")
    print(f"  source verses:        {len(outgoing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
