"""Tanakh (full Hebrew Bible: Torah + Nevi'im + Ketuvim) data loading,
reference parsing, and adapter.

Adheres to docs/data-schema.md §2 (multi-tradition canonical schema) and
docs/phase3-scope-tanakh.md (Phase 3.3 scope).

Exposes:
    parse_tanakh_ref(raw: str) -> Optional[TanakhRef]
    list_tanakh_translations() -> list[str]
    load_tanakh_edition(key: str) -> dict
    get_tanakh_verses(edition, book, chapter, verse_or_range) -> list[dict]
    list_books(section=None) -> list[str]   # section in {"Torah","Nevi'im","Ketuvim",None}
    run_tanakh(ref, translations=None, as_json=False)
    main()  # CLI entry

This is the broader canon than `bible.torah` (which is Pentateuch-only).
Both adapters exist intentionally — see scope doc §"Adapter design".
The Torah adapter remains the canonical narrow surface for the Five
Books of Moses; the Tanakh adapter is the canonical narrow surface for
the full canon.
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parent.parent
TANAKH_DATA_DIR = ROOT / "data" / "tanakh"

# ---------------------------------------------------------------------------
# Canonical Tanakh book metadata
# (canonical_name, hebrew_name, transliteration, total_chapters, total_verses, section)
# Section ∈ {"Torah", "Nevi'im", "Ketuvim"}
# ---------------------------------------------------------------------------

BOOKS = [
    # Torah (5 books — same as bible.torah.BOOKS but kept self-contained here)
    ("Genesis", "בראשית", "Bereshit", 50, 1533, "Torah"),
    ("Exodus", "שמות", "Shemot", 40, 1213, "Torah"),
    ("Leviticus", "ויקרא", "Vayikra", 27, 859, "Torah"),
    ("Numbers", "במדבר", "Bamidbar", 36, 1288, "Torah"),
    ("Deuteronomy", "דברים", "Devarim", 34, 959, "Torah"),
    # Nevi'im — Prophets (11 books)
    ("Joshua", "יהושע", "Yehoshua", 24, 658, "Nevi'im"),
    ("Judges", "שופטים", "Shoftim", 21, 618, "Nevi'im"),
    ("Samuel I", "שמואל א", "Shemuel I", 31, 810, "Nevi'im"),
    ("Samuel II", "שמואל ב", "Shemuel II", 24, 695, "Nevi'im"),
    ("Kings I", "מלכים א", "Melachim I", 22, 816, "Nevi'im"),
    ("Kings II", "מלכים ב", "Melachim II", 25, 719, "Nevi'im"),
    ("Isaiah", "ישעיהו", "Yeshayahu", 66, 1292, "Nevi'im"),
    ("Jeremiah", "ירמיהו", "Yirmiyahu", 52, 1364, "Nevi'im"),
    ("Ezekiel", "יחזקאל", "Yechezkel", 48, 1273, "Nevi'im"),
    # Twelve Minor Prophets — Sefaria uses "Hosea", "Joel", ..., "Malachi"
    # (singular book names), NOT "The Twelve".
    ("Hosea", "הושע", "Hoshea", 14, 197, "Nevi'im"),
    ("Joel", "יואל", "Yoel", 4, 73, "Nevi'im"),
    ("Amos", "עמוס", "Amos", 9, 146, "Nevi'im"),
    ("Obadiah", "עובדיה", "Ovadyah", 1, 21, "Nevi'im"),
    ("Jonah", "יונה", "Yonah", 4, 48, "Nevi'im"),
    ("Micah", "מיכה", "Mikhah", 7, 105, "Nevi'im"),
    ("Nahum", "נחום", "Nachum", 3, 47, "Nevi'im"),
    ("Habakkuk", "חבקוק", "Chavaquq", 3, 56, "Nevi'im"),
    ("Zephaniah", "צפניה", "Tsefanyah", 3, 53, "Nevi'im"),
    ("Haggai", "חגי", "Chagai", 2, 38, "Nevi'im"),
    ("Zechariah", "זכריה", "Zecharyah", 14, 211, "Nevi'im"),
    ("Malachi", "מלאכי", "Malachi", 3, 55, "Nevi'im"),
    # Ketuvim — Writings (13 books)
    ("Psalms", "תהלים", "Tehillim", 150, 2461, "Ketuvim"),
    ("Proverbs", "משלי", "Mishlei", 31, 915, "Ketuvim"),
    ("Job", "איוב", "Iyov", 42, 1070, "Ketuvim"),
    ("Song of Songs", "שיר השירים", "Shir HaShirim", 8, 117, "Ketuvim"),
    ("Ruth", "רות", "Rut", 4, 85, "Ketuvim"),
    ("Lamentations", "איכה", "Eikhah", 5, 154, "Ketuvim"),
    ("Ecclesiastes", "קהלת", "Kohelet", 12, 222, "Ketuvim"),
    ("Esther", "אסתר", "Ester", 10, 167, "Ketuvim"),
    ("Daniel", "דניאל", "Daniel", 12, 357, "Ketuvim"),
    ("Ezra", "עזרא", "Ezra", 10, 280, "Ketuvim"),
    ("Nehemiah", "נחמיה", "Nechemyah", 13, 406, "Ketuvim"),
    ("Chronicles I", "דברי הימים א", "Divrei HaYamim I", 29, 943, "Ketuvim"),
    ("Chronicles II", "דברי הימים ב", "Divrei HaYamim II", 36, 822, "Ketuvim"),
]

# Lookup helpers
BOOK_BY_NAME: dict[str, tuple] = {b[0]: b for b in BOOKS}
BOOK_NAMES: list[str] = [b[0] for b in BOOKS]
BOOKS_BY_SECTION: dict[str, list[str]] = {
    "Torah": [b[0] for b in BOOKS if b[5] == "Torah"],
    "Nevi'im": [b[0] for b in BOOKS if b[5] == "Nevi'im"],
    "Ketuvim": [b[0] for b in BOOKS if b[5] == "Ketuvim"],
}
# Total verse counts per section (computed once)
SECTION_TOTALS = {
    section: (len(books), sum(b[4] for b in BOOKS if b[5] == section))
    for section, books in BOOKS_BY_SECTION.items()
}


# ---------------------------------------------------------------------------
# Book alias resolution + Hebrew-with-nikkud matching
# ---------------------------------------------------------------------------

def _strip_diacritics(s: str) -> str:
    """Remove Hebrew vowel points (nikkud) for alias matching."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) not in ("Mn", "Cf"))


def _clean_str(s: str) -> str:
    """ASCII/Hebrew-normalize a string for alias matching.

    For Latin input: lowercase, strip non-alphanumerics.
    For Hebrew input: strip vowel points (nikkud), keep letters.

    Note: Roman-numeral prefixes ("I Samuel", "II Kings") are handled
    by explicit ROMAN_PREFIX_ALIASES below, NOT by stripping here —
    stripping at the cleaner would collapse "I Samuel" and "II Samuel"
    to the same key, losing distinction between Samuel I and Samuel II.
    """
    s = _strip_diacritics(s).lower().strip()
    return re.sub(r"[^a-z0-9\u0590-\u05ff]", "", s)


# Build alias dictionary: cleaned_string -> canonical book name
BOOK_ALIASES: dict[str, str] = {}
for canonical, hebrew, translit, _, _, _ in BOOKS:
    BOOK_ALIASES[_clean_str(canonical)] = canonical
    BOOK_ALIASES[_clean_str(hebrew)] = canonical
    BOOK_ALIASES[_clean_str(translit)] = canonical

# Add aliases for the Sefaria Roman-numeral-prefix schema (after _clean_str
# normalization). With the Roman-numeral-stripping in _clean_str, "I Samuel"
# and "1 Samuel" both normalize to "samuel", and the SHORT_ALIASES below
# already include "samuel" → "Samuel I". Same for Kings, Chronicles.
# We also add explicit numeric-prefix aliases for defense-in-depth:
ROMAN_PREFIX_ALIASES = {
    "1 samuel": "Samuel I", "1samuel": "Samuel I",
    "2 samuel": "Samuel II", "2samuel": "Samuel II",
    "1 kings": "Kings I", "1kings": "Kings I",
    "2 kings": "Kings II", "2kings": "Kings II",
    "1 chronicles": "Chronicles I", "1chronicles": "Chronicles I",
    "2 chronicles": "Chronicles II", "2chronicles": "Chronicles II",
    "i samuel": "Samuel I",
    "ii samuel": "Samuel II",
    "i kings": "Kings I",
    "ii kings": "Kings II",
    "i chronicles": "Chronicles I",
    "ii chronicles": "Chronicles II",
}
for k, v in ROMAN_PREFIX_ALIASES.items():
    BOOK_ALIASES[_clean_str(k)] = v

# Common short Latin aliases
SHORT_ALIASES = {
    # Torah
    "gen": "Genesis", "gn": "Genesis", "bereshit": "Genesis", "bereishit": "Genesis",
    "ex": "Exodus", "exo": "Exodus", "shemot": "Exodus", "shemos": "Exodus",
    "lev": "Leviticus", "lv": "Leviticus", "vayikra": "Leviticus",
    "num": "Numbers", "nb": "Numbers", "bamidbar": "Numbers",
    "deut": "Deuteronomy", "dt": "Deuteronomy", "devarim": "Deuteronomy", "devorim": "Deuteronomy",
    # Nevi'im
    "josh": "Joshua", "yehoshua": "Joshua",
    "judg": "Judges", "judges": "Judges", "shoftim": "Judges",
    "1sam": "Samuel I", "2sam": "Samuel II",
    "1samuel": "Samuel I", "2samuel": "Samuel II",
    "1kings": "Kings I", "2kings": "Kings II",
    "1kgs": "Kings I", "2kgs": "Kings II",
    "isa": "Isaiah", "yeshayahu": "Isaiah",
    "jer": "Jeremiah", "yirmiyahu": "Jeremiah",
    "ezek": "Ezekiel", "yechezkel": "Ezekiel",
    "hos": "Hosea", "hoshea": "Hosea",
    "obad": "Obadiah", "ovadyah": "Obadiah",
    "jon": "Jonah", "yonah": "Jonah",
    "mic": "Micah", "mikhah": "Micah",
    "nah": "Nahum", "nachum": "Nahum",
    "hab": "Habakkuk", "chavaquq": "Habakkuk",
    "zeph": "Zephaniah", "tsefanyah": "Zephaniah",
    "hag": "Haggai", "chagai": "Haggai",
    "zech": "Zechariah", "zecharyah": "Zechariah",
    "mal": "Malachi",
    # Ketuvim
    "ps": "Psalms", "psa": "Psalms", "psalm": "Psalms", "tehillim": "Psalms",
    "prov": "Proverbs", "proverbs": "Proverbs", "mishlei": "Proverbs",
    "songs": "Song of Songs", "songofsongs": "Song of Songs", "shirhashirim": "Song of Songs",
    "lam": "Lamentations", "lamentations": "Lamentations", "eikhah": "Lamentations",
    "eccl": "Ecclesiastes", "ecclesiastes": "Ecclesiastes", "kohelet": "Ecclesiastes",
    "esth": "Esther", "esther": "Esther",
    "chr1": "Chronicles I", "1chr": "Chronicles I", "1chronicles": "Chronicles I",
    "chr2": "Chronicles II", "2chr": "Chronicles II", "2chronicles": "Chronicles II",
}
for k, v in SHORT_ALIASES.items():
    BOOK_ALIASES[_clean_str(k)] = v

# Sefaria-side aliases for books that exist in their DB under a different
# canonical name than ours. Sefaria uses Roman numerals for Samuel/Kings/Chronicles
# in their canonical schema: "I Samuel", "II Samuel", "I Kings", "II Kings",
# "I Chronicles", "II Chronicles". Our canonical names are "Samuel I", "Kings I", etc.
# Map our canonical name → Sefaria's expected Book string. Sefaria accepts
# spaces OR underscores in URL paths, but urllib3 (and many HTTP libraries)
# treat literal-space URLs as malformed; we use underscores to be safe.
SEFARIA_BOOK_NAME = {
    "Samuel I": "I_Samuel",
    "Samuel II": "II_Samuel",
    "Kings I": "I_Kings",
    "Kings II": "II_Kings",
    "Chronicles I": "I_Chronicles",
    "Chronicles II": "II_Chronicles",
}


def sefaria_book_name(canonical: str) -> str:
    """Return the Sefaria-canonical Book string for use in /api/texts/<Book>.<Chapter>.

    Default: return our canonical name unchanged (works for most books).
    Samuel/Kings/Chronicles use Roman-numeral prefix in Sefaria.
    """
    return SEFARIA_BOOK_NAME.get(canonical, canonical)


def resolve_book(s: str) -> Optional[str]:
    """Resolve a raw string to a canonical Tanakh book name."""
    cleaned = _clean_str(s)
    if cleaned in BOOK_ALIASES:
        return BOOK_ALIASES[cleaned]
    return None


# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------

# Match patterns:
#   "Genesis 1:1", "Gen 1:1", "Bereshit 1:1", "בראשית 1:1"
#   "Psalms 23:1-6" (verse range)
#   "Psalms 119:105" (single verse)
# We require a book name (or its alias) followed by chapter:verse.
_RANGE_RE = re.compile(r"^(.+?)\s+(\d+):(\d+)(?:[-–—](\d+))?$")


def parse_tanakh_ref(raw: str) -> Optional[tuple[str, int, Union[int, tuple[int, int]]]]:
    """Parse a Tanakh reference into (book, chapter, verse | (verse_start, verse_end)).

    Supported formats:
        - "Genesis 1:1"           (canonical English)
        - "Gen 1:1"               (short Latin alias)
        - "Bereshit 1:1"          (transliteration)
        - "בראשית 1:1"           (Hebrew, with or without nikkud)
        - "Psalms 119:105"        (single verse, high number OK)
        - "Isaiah 53:5-12"        (verse range, hyphen)
        - "Song of Songs 2:1–7"  (verse range, en-dash)
        - "1 Samuel 3:1"          (Roman-numeral prefix)
        - "II Kings 5:1"          (Sefaria-style prefix)

    Returns None if the input is unparseable.

    Bounds checks: chapter is bounds-checked against the book's total
    chapter count (cheap, known statically). Verse-end is NOT bounds-checked
    here — the BOOKS table stores total-verses-per-book, not per-chapter
    totals, so a verse like "Psalms 23:99" would pass our naive check
    even though Psalms 23 has only 6 verses. Runtime gracefully returns
    an empty list when no matching verses exist, so the user sees
    "no verses found" rather than a hard error.
    """
    if not raw or not isinstance(raw, str):
        return None
    clean = raw.strip()
    if not clean:
        return None

    m = _RANGE_RE.match(clean)
    if not m:
        return None
    book_str, ch_str, v_start_str, v_end_str = m.groups()
    book = resolve_book(book_str)
    if book is None:
        return None
    chapter = int(ch_str)
    verse_start = int(v_start_str)
    verse_end = int(v_end_str) if v_end_str else verse_start
    if verse_end < verse_start:
        verse_start, verse_end = verse_end, verse_start
    verse_spec: Union[int, tuple[int, int]] = (
        (verse_start, verse_end) if verse_end != verse_start else verse_start
    )
    # Bounds check against total chapters only (cheap; known statically).
    # Verse bounds intentionally loose — see docstring.
    book_meta = BOOK_BY_NAME[book]
    total_chapters = book_meta[3]
    if chapter < 1 or chapter > total_chapters:
        return None
    return (book, chapter, verse_spec)


# ---------------------------------------------------------------------------
# Edition loading and lookup
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def load_tanakh_edition(key: str) -> dict:
    """Load a Tanakh edition JSON from `data/tanakh/<key>.json`.

    @lru_cache keeps us re-using the same parsed dict across calls.
    Raises FileNotFoundError listing available editions on miss.
    """
    target = TANAKH_DATA_DIR / f"{key}.json"
    if not target.exists():
        available = list_tanakh_translations()
        raise FileNotFoundError(
            f"Tanakh edition {key!r} not found at {target}. "
            f"Available editions: {available}. "
            f"Run `python scripts/ingest_tanakh.py` to download."
        )
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


def list_tanakh_translations() -> list[str]:
    """List available Tanakh editions (filenames without .json)."""
    if not TANAKH_DATA_DIR.exists():
        return []
    return sorted(p.stem for p in TANAKH_DATA_DIR.glob("*.json"))


def _group_verses_by_chapter(book_obj: dict) -> dict[int, list[dict]]:
    """Group flat verse list into {chapter: [verse, ...]}.

    The ingestor writes verses flat with verse numbers reset per chapter.
    We detect chapter boundaries by watching for verse-number decreases.
    """
    verses = book_obj.get("verses", [])
    chapters: dict[int, list[dict]] = {}
    current_ch = 1
    chapters[current_ch] = []
    prev_verse = 0
    for v in verses:
        if v["verse"] <= prev_verse and prev_verse > 0:
            current_ch += 1
            chapters[current_ch] = []
        chapters[current_ch].append(v)
        prev_verse = v["verse"]
    return chapters


def get_tanakh_verses_scoped(
    edition_key: str,
    book: str,
    chapter: int,
    verse_spec: Union[int, tuple[int, int]],
) -> list[dict]:
    """Retrieve verses for a given edition, book, chapter, and verse range.

    Returns a list of dicts with keys:
        book, chapter, verse, text, book_hebrew, book_transliteration,
        book_section, edition, translation, language
    """
    edition_data = load_tanakh_edition(edition_key)
    divisions = edition_data.get("divisions", [])
    book_obj = next((d for d in divisions if d.get("name") == book), None)
    if book_obj is None:
        return []
    chapters = _group_verses_by_chapter(book_obj)
    ch_verses = chapters.get(chapter, [])
    if isinstance(verse_spec, tuple):
        start_v, end_v = verse_spec
    else:
        start_v = end_v = verse_spec
    results = []
    for v in ch_verses:
        if start_v <= v["verse"] <= end_v:
            results.append({
                "book": book,
                "chapter": chapter,
                "verse": v["verse"],
                "text": v["text"],
                "book_hebrew": book_obj.get("name_hebrew", ""),
                "book_transliteration": book_obj.get("name_transliteration", ""),
                "book_section": book_obj.get("section", ""),
                "edition": edition_key,
                "translation": edition_data.get("translation", edition_key),
                "language": edition_data.get("language", "en"),
            })
    return results


def list_books(section: Optional[str] = None) -> list[str]:
    """List books in the Tanakh, optionally filtered by section.

    section: one of {"Torah", "Nevi'im", "Ketuvim", None}.
    None returns all books in canonical order.
    """
    if section is None:
        return list(BOOK_NAMES)
    return list(BOOKS_BY_SECTION.get(section, []))


# ---------------------------------------------------------------------------
# CLI presentation
# ---------------------------------------------------------------------------

def run_tanakh(
    ref_str: str,
    translations: Optional[list[str]] = None,
    as_json: bool = False,
    section_filter: Optional[str] = None,
) -> None:
    """Execute Tanakh lookup CLI command.

    section_filter: optional "Torah" / "Nevi'im" / "Ketuvim" to narrow
    the displayed book (mostly useful for cross-tradition presentation;
    canonical parsing via parse_tanakh_ref already validates).
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parsed = parse_tanakh_ref(ref_str)
    if not parsed:
        msg = f"Error: Could not parse Tanakh reference: {ref_str!r}"
        if as_json:
            print(json.dumps({"error": msg}))
        else:
            print(msg, file=sys.stderr)
            print(
                "Examples of valid references: 'Genesis 1:1', 'Psalms 23:1', "
                "'Isaiah 53:5-12', 'Song of Songs 2:1', 'בראשית 1:1'"
            )
        sys.exit(1)

    book, chapter, verse_spec = parsed
    book_meta = BOOK_BY_NAME[book]

    if not translations:
        translations = ["jps1917-modernized", "hebrew-nikkud"]

    available = list_tanakh_translations()
    active_editions = []
    for t in translations:
        t_clean = t.strip().lower()
        if t_clean in available:
            active_editions.append(t_clean)
        else:
            print(f"Warning: Edition '{t}' not found. Available: {available}", file=sys.stderr)

    if not active_editions:
        if as_json:
            print(json.dumps({"error": f"No valid Tanakh editions found in {available}"}))
            sys.exit(1)
        else:
            print(f"Error: No valid Tanakh editions found. Run scripts/ingest_tanakh.py first.", file=sys.stderr)
            sys.exit(1)

    # Gather rows
    verse_map: dict[int, dict] = {}
    for ed in active_editions:
        verses = get_tanakh_verses_scoped(ed, book, chapter, verse_spec)
        for v in verses:
            vn = v["verse"]
            if vn not in verse_map:
                verse_map[vn] = {"book": book, "chapter": chapter, "verse": vn, "texts": {}}
            verse_map[vn]["texts"][ed] = {
                "text": v["text"],
                "translation": v["translation"],
                "language": v["language"],
            }

    if not verse_map:
        msg = f"Error: No verses found for {book} {chapter}:{verse_spec}"
        if as_json:
            print(json.dumps({"error": msg}))
        else:
            print(msg, file=sys.stderr)
        sys.exit(1)

    if as_json:
        output_json = {
            "query": ref_str,
            "book": {
                "name": book,
                "hebrew": book_meta[1],
                "transliteration": book_meta[2],
                "section": book_meta[5],
                "total_chapters": book_meta[3],
                "total_verses": book_meta[4],
            },
            "chapter": chapter,
            "verses": [
                {
                    "verse": v_num,
                    "citation": f"{book} {chapter}:{v_num}",
                    "translations": {
                        ed: verse_map[v_num]["texts"][ed]["text"]
                        for ed in active_editions
                        if ed in verse_map[v_num]["texts"]
                    },
                }
                for v_num in sorted(verse_map.keys())
            ],
        }
        print(json.dumps(output_json, ensure_ascii=False, indent=2))
        return

    # Text presentation
    for v_num in sorted(verse_map.keys()):
        citation = f"{book} {chapter}:{v_num}  ({book} / {book_meta[1]} / {book_meta[2]} / {book_meta[5]})"
        print("=" * 78)
        print(f"  {citation}")
        print("=" * 78)
        for ed in active_editions:
            if ed in verse_map[v_num]["texts"]:
                info = verse_map[v_num]["texts"][ed]
                ed_name = info["translation"]
                text = info["text"]
                lang = info["language"]
                print(f"[{ed_name}]  ({lang})")
                print(f"{text}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Tanakh lookup and parallel translations CLI")
    parser.add_argument("reference", help="Tanakh citation (e.g. 'Genesis 1:1', 'Psalms 23:1', 'Isaiah 53:5-12', 'בראשית 1:1')")
    parser.add_argument("-t", "--translation", "--translations", dest="translations",
                        help="Comma-separated list of editions (default: jps1917-modernized,hebrew-nikkud)")
    parser.add_argument("--section", choices=["Torah", "Nevi'im", "Ketuvim"], default=None,
                        help="Filter books to a specific section (default: all)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()
    editions = [t.strip() for t in args.translations.split(",")] if args.translations else None
    run_tanakh(args.reference, translations=editions, as_json=args.json,
               section_filter=args.section)


if __name__ == "__main__":
    main()
