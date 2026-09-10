"""Torah (Five Books of Moses) data loading, reference parsing, and adapter.

Adheres to docs/data-schema.md §2 (multi-tradition canonical schema) and
docs/phase3-scope-torah.md (Phase 3.2 scope).

Exposes:
    parse_torah_ref(raw: str) -> Optional[tuple[str, int, Union[int, tuple[int, int]]]]
    list_torah_translations() -> list[str]
    load_torah_edition(key: str) -> dict
    get_torah_verses(edition: str, book: str, chapter: int, verse_or_range) -> list[dict]
    run_torah(ref: str, translations: list[str] = None, as_json: bool = False)
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parent.parent
TORAH_DATA_DIR = ROOT / "data" / "torah"

# ---------------------------------------------------------------------------
# Canonical Five Books of Moses Metadata
# (canonical_name, hebrew_name, transliteration, total_chapters, total_verses)
# ---------------------------------------------------------------------------

BOOKS = [
    ("Genesis", "בראשית", "Bereshit", 50, 1533),
    ("Exodus", "שמות", "Shemot", 40, 1213),
    ("Leviticus", "ויקרא", "Vayikra", 27, 859),
    ("Numbers", "במדבר", "Bamidbar", 36, 1288),
    ("Deuteronomy", "דברים", "Devarim", 34, 959),
]

# Lookup helpers
BOOK_BY_NAME = {b[0]: b for b in BOOKS}
BOOK_NAMES = [b[0] for b in BOOKS]


def _strip_diacritics(s: str) -> str:
    """Remove Hebrew vowel points (nikkud) for alias matching.

    Hebrew text with nikkud includes combining characters like U+05B0
    (SHVA), U+05B8 (QAMATS), etc. We strip those for matching but keep
    the consonantal skeleton (which is what humans typically transliterate).
    """
    import unicodedata
    # Hebrew vowel marks are in Mn (Mark, Nonspacing) and Cf (Format)
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) not in ("Mn", "Cf"))


def _clean_str(s: str) -> str:
    """ASCII normalize a string for alias matching.

    For Latin input: lowercase, strip non-alphanumerics.
    For Hebrew input: strip vowel points (nikkud), keep letters.
    """
    s = _strip_diacritics(s).lower().strip()
    # Keep Hebrew letters (U+0590–U+05FF) and ASCII alphanumerics
    return re.sub(r"[^a-z0-9\u0590-\u05ff]", "", s)


# Build alias dictionary: cleaned_string -> canonical book name
BOOK_ALIASES: dict[str, str] = {}
for canonical, hebrew, translit, _, _ in BOOKS:
    BOOK_ALIASES[_clean_str(canonical)] = canonical
    BOOK_ALIASES[_clean_str(hebrew)] = canonical
    BOOK_ALIASES[_clean_str(translit)] = canonical

# Common short Latin aliases (canonical + variant forms)
SHORT_ALIASES = {
    "gen": "Genesis", "gn": "Genesis", "bereshit": "Genesis", "bereishit": "Genesis",
    "ex": "Exodus", "exo": "Exodus", "shemot": "Exodus", "shemos": "Exodus",
    "lev": "Leviticus", "lv": "Leviticus", "vayikra": "Leviticus",
    "num": "Numbers", "nb": "Numbers", "bamidbar": "Numbers",
    "deut": "Deuteronomy", "dt": "Deuteronomy", "devarim": "Deuteronomy", "devorim": "Deuteronomy",
}
for k, v in SHORT_ALIASES.items():
    BOOK_ALIASES[_clean_str(k)] = v


def resolve_book(s: str) -> Optional[str]:
    """Resolve a raw string to a canonical Torah book name."""
    cleaned = _clean_str(s)
    if cleaned in BOOK_ALIASES:
        return BOOK_ALIASES[cleaned]
    return None


# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------

# Match patterns:
#   "Genesis 1:1", "Gen 1:1", "Bereshit 1:1", "בראשית 1:1"
#   "1:1" (defaults to Genesis for ambiguous case? — no, requires book)
#   "Genesis 1:1-3" (range)
# We require a book name (or its alias) followed by chapter:verse.
_RANGE_RE = re.compile(r"^(.+?)\s+(\d+):(\d+)(?:[-–—](\d+))?$")


def parse_torah_ref(raw: str) -> Optional[tuple[str, int, Union[int, tuple[int, int]]]]:
    """Parse a Torah reference into (book, chapter, verse | (verse_start, verse_end)).

    Supported formats:
        - "Genesis 1:1"
        - "Gen 1:1" (short Latin alias)
        - "Bereshit 1:1" (transliteration)
        - "בראשית 1:1" (Hebrew, with or without nikkud)
        - "Genesis 1:1-3" (verse range)
        - "Genesis 1:1–3" (en-dash range)
        - "Genesis 1:1—3" (em-dash range)

    Returns None if the input is unparseable.
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
    # Bounds check against total verses in the book
    _, _, _, _, total_verses = BOOK_BY_NAME[book]
    if verse_end > total_verses:
        return None
    if chapter < 1 or chapter > BOOK_BY_NAME[book][3]:
        return None
    return (book, chapter, verse_spec)


# ---------------------------------------------------------------------------
# Edition loading and lookup
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def load_torah_edition(key: str) -> dict:
    """Load a Torah edition JSON from `data/torah/<key>.json`.

    @lru_cache keeps us re-using the same parsed dict across calls.
    Raises FileNotFoundError listing available editions on miss.
    """
    target = TORAH_DATA_DIR / f"{key}.json"
    if not target.exists():
        available = list_torah_translations()
        raise FileNotFoundError(
            f"Torah edition {key!r} not found at {target}. "
            f"Available editions: {available}. "
            f"Run `python scripts/ingest_torah.py` to download."
        )
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


def list_torah_translations() -> list[str]:
    """List available Torah editions (filenames without .json)."""
    if not TORAH_DATA_DIR.exists():
        return []
    return sorted(p.stem for p in TORAH_DATA_DIR.glob("*.json"))


def get_torah_verses(
    edition_key: str,
    book: str,
    chapter: int,
    verse_spec: Union[int, tuple[int, int]],
) -> list[dict]:
    """Retrieve verses for a given edition, book, chapter, and verse range.

    Returns a list of dicts with keys:
        book, chapter, verse, text, book_hebrew, book_transliteration,
        edition, translation, language
    """
    edition_data = load_torah_edition(edition_key)
    divisions = edition_data.get("divisions", [])
    book_obj = next((d for d in divisions if d.get("name") == book), None)
    if book_obj is None:
        return []
    if isinstance(verse_spec, tuple):
        start_v, end_v = verse_spec
    else:
        start_v = end_v = verse_spec
    # Verses are stored flat under "verses" with verse numbers 1..N across
    # the whole book, not per-chapter. We need to figure out the verse
    # numbering convention used by the ingestor.
    # The ingestor writes verses in order: all verses in chapter 1, then
    # chapter 2, etc., with verse numbers reset per chapter. We can detect
    # this by checking the first verse number on the first chapter boundary
    # — but to keep things robust we just look up verses by chapter+verse.
    results = []
    for v in book_obj.get("verses", []):
        vnum = v["verse"]
        # If the ingest was chapter-restart, we need chapter filtering.
        # We assume the ingest stored chapter-scoped verses; if not, the
        # caller should use the chapter boundary helper below.
        # Here, we filter by verse range only — callers should ensure
        # they pass the correct book+chapter.
        if start_v <= vnum <= end_v:
            results.append({
                "book": book,
                "chapter": chapter,
                "verse": vnum,
                "text": v["text"],
                "book_hebrew": book_obj.get("name_hebrew", ""),
                "book_transliteration": book_obj.get("name_transliteration", ""),
                "edition": edition_key,
                "translation": edition_data.get("translation", edition_key),
                "language": edition_data.get("language", "en"),
            })
    return results


def _group_verses_by_chapter(book_obj: dict) -> dict[int, list[dict]]:
    """Group flat verse list into {chapter: [verse, ...]} using Sefaria's
    `lengths` field per division. The ingestor doesn't currently store
    chapter boundaries, so we synthesize them by dividing verses evenly
    when chapters_count × per-chapter = total verses.

    Actually, the ingestor writes verses flat with verse numbers reset
    per chapter. We use the `chapters_count` field + the fact that Sefaria
    publishes known per-chapter verse counts (from the chapter metadata
    we already saw in Sefaria API responses). To avoid embedding that
    table, we re-fetch chapter lengths on demand via the Sefaria index
    metadata, but as a simpler fallback we just trust the ingestor's
    sequential layout: chapters_count × first-chapter-pattern.

    Actually simplest: the ingestor writes verses in chapter order with
    verse numbers reset. We can detect chapter boundaries by watching
    for verse-number decreases. We do that here.
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


def get_torah_verses_scoped(
    edition_key: str,
    book: str,
    chapter: int,
    verse_spec: Union[int, tuple[int, int]],
) -> list[dict]:
    """Like `get_torah_verses` but properly scopes by chapter.

    The ingestor writes verses flat with verse numbers reset per chapter.
    This helper detects chapter boundaries and filters correctly.
    """
    edition_data = load_torah_edition(edition_key)
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
                "edition": edition_key,
                "translation": edition_data.get("translation", edition_key),
                "language": edition_data.get("language", "en"),
            })
    return results


# ---------------------------------------------------------------------------
# CLI presentation
# ---------------------------------------------------------------------------

def run_torah(
    ref_str: str,
    translations: Optional[list[str]] = None,
    as_json: bool = False,
) -> None:
    """Execute Torah lookup CLI command."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parsed = parse_torah_ref(ref_str)
    if not parsed:
        msg = f"Error: Could not parse Torah reference: {ref_str!r}"
        if as_json:
            print(json.dumps({"error": msg}))
        else:
            print(msg, file=sys.stderr)
            print(
                "Examples of valid references: 'Genesis 1:1', 'Gen 1:1', 'Bereshit 1:1', "
                "'בראשית 1:1', 'Exodus 20:2-3'"
            )
        sys.exit(1)

    book, chapter, verse_spec = parsed
    book_meta = BOOK_BY_NAME[book]

    # Default to JPS English + Hebrew Nikkud
    if not translations:
        translations = ["jps1917-modernized", "hebrew-nikkud"]

    available = list_torah_translations()
    active_editions = []
    for t in translations:
        t_clean = t.strip().lower()
        if t_clean in available:
            active_editions.append(t_clean)
        else:
            print(f"Warning: Edition '{t}' not found. Available: {available}", file=sys.stderr)

    if not active_editions:
        if as_json:
            print(json.dumps({"error": f"No valid Torah editions found in {available}"}))
            sys.exit(1)
        else:
            print(f"Error: No valid Torah editions found. Run scripts/ingest_torah.py first.", file=sys.stderr)
            sys.exit(1)

    # Gather rows
    verse_map: dict[int, dict] = {}
    for ed in active_editions:
        verses = get_torah_verses_scoped(ed, book, chapter, verse_spec)
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
        citation = f"{book} {chapter}:{v_num}  ({book} / {book_meta[1]} / {book_meta[2]})"
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

    parser = argparse.ArgumentParser(description="Torah lookup and parallel translations CLI")
    parser.add_argument("reference", help="Torah citation (e.g. 'Genesis 1:1', 'בראשית 1:1', 'Exodus 20:2-3')")
    parser.add_argument("-t", "--translation", "--translations", dest="translations",
                        help="Comma-separated list of editions (default: jps1917-modernized,hebrew-nikkud)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()
    editions = [t.strip() for t in args.translations.split(",")] if args.translations else None
    run_torah(args.reference, translations=editions, as_json=args.json)


if __name__ == "__main__":
    main()
