"""Shared data loading and reference parsing for the bible package.

All translations are loaded lazily on first use and cached.
Book name resolution handles three schemes:
  1. Named books ("Genesis", "1 Samuel") — used by KJV and most Protestant translations
  2. Indexed books ("Book 1", "Book 27") — used by LXX, Tisch, WEB, WLCa, Synod
  3. Unknown-named ("Unknown (1527v,50c)") — used by DRB, UKRK; resolved positionally

For parallel lookup, translations are aligned by canonical book index (1-66)
matching the standard Protestant Old + New Testament order. Translations with
extra books (deuterocanonical, apocryphal) keep them but parallel lookup only
joins on the shared 66-book canon.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
TRANSLATIONS_DIR = ROOT / "translations"
KJV_PATH = ROOT / "kjv.json"
STRONGS_HEB_JSON = ROOT / "strongs_data/hebrew/strongs-hebrew.json"
STRONGS_GRK_JSON = ROOT / "strongs_data/greek/strongs-greek.json"
STRONGS_HEB_JS = ROOT / "strongs_data/hebrew/strongs-hebrew-dictionary.js"
STRONGS_GRK_JS = ROOT / "strongs_data/greek/strongs-greek-dictionary.js"

# ---------------------------------------------------------------------------
# Canonical 66-book Protestant order (index 1-66)
# ---------------------------------------------------------------------------

CANONICAL_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation",
]
CANONICAL_INDEX = {name: i + 1 for i, name in enumerate(CANONICAL_BOOKS)}

# Set of OT book names (first 39) for Strong's H/G prefix resolution
_OT_BOOKS = set(CANONICAL_BOOKS[:39])

# Aliases for user input — book names and common abbreviations
BOOK_ALIASES = {
    "gen": "Genesis", "genesis": "Genesis",
    "ex": "Exodus", "exo": "Exodus", "exodus": "Exodus",
    "lev": "Leviticus", "leviticus": "Leviticus",
    "num": "Numbers", "numbers": "Numbers",
    "deut": "Deuteronomy", "deu": "Deuteronomy", "deuteronomy": "Deuteronomy",
    "josh": "Joshua", "jos": "Joshua", "joshua": "Joshua",
    "judg": "Judges", "jdg": "Judges", "judges": "Judges",
    "ruth": "Ruth",
    "1sam": "1 Samuel", "1 sam": "1 Samuel", "1samuel": "1 Samuel",
    "2sam": "2 Samuel", "2 sam": "2 Samuel", "2samuel": "2 Samuel",
    "1kgs": "1 Kings", "1kings": "1 Kings", "1 kin": "1 Kings",
    "2kgs": "2 Kings", "2kings": "2 Kings", "2 kin": "2 Kings",
    "1chr": "1 Chronicles", "1chronicles": "1 Chronicles",
    "2chr": "2 Chronicles", "2chronicles": "2 Chronicles",
    "ezra": "Ezra", "neh": "Nehemiah", "nehemiah": "Nehemiah",
    "esth": "Esther", "esther": "Esther",
    "job": "Job",
    "ps": "Psalms", "psa": "Psalms", "psalm": "Psalms", "psalms": "Psalms",
    "prov": "Proverbs", "proverbs": "Proverbs",
    "eccl": "Ecclesiastes", "ecc": "Ecclesiastes", "ecclesiastes": "Ecclesiastes",
    "song": "Song of Solomon", "sos": "Song of Solomon", "canticle": "Song of Solomon",
    "isa": "Isaiah", "isaiah": "Isaiah",
    "jer": "Jeremiah", "jeremiah": "Jeremiah",
    "lam": "Lamentations", "lamentations": "Lamentations",
    "ezek": "Ezekiel", "eze": "Ezekiel", "ezekiel": "Ezekiel",
    "dan": "Daniel", "daniel": "Daniel",
    "hos": "Hosea", "hosea": "Hosea",
    "joel": "Joel", "amos": "Amos",
    "obad": "Obadiah", "obadiah": "Obadiah",
    "jonah": "Jonah", "mic": "Micah", "micah": "Micah",
    "nah": "Nahum", "nahum": "Nahum",
    "hab": "Habakkuk", "habakkuk": "Habakkuk",
    "zeph": "Zephaniah", "zephaniah": "Zephaniah",
    "hag": "Haggai", "haggai": "Haggai",
    "zech": "Zechariah", "zechariah": "Zechariah",
    "mal": "Malachi", "malachi": "Malachi",
    "matt": "Matthew", "mt": "Matthew", "matthew": "Matthew",
    "mark": "Mark", "mk": "Mark",
    "luke": "Luke", "lk": "Luke",
    "john": "John", "jn": "John",
    "acts": "Acts",
    "rom": "Romans", "romans": "Romans",
    "1cor": "1 Corinthians", "1 cor": "1 Corinthians", "1corinthians": "1 Corinthians",
    "2cor": "2 Corinthians", "2 cor": "2 Corinthians", "2corinthians": "2 Corinthians",
    "gal": "Galatians", "galatians": "Galatians",
    "eph": "Ephesians", "ephesians": "Ephesians",
    "phil": "Philippians", "php": "Philippians", "philippians": "Philippians",
    "col": "Colossians", "colossians": "Colossians",
    "1thess": "1 Thessalonians", "1 th": "1 Thessalonians",
    "2thess": "2 Thessalonians", "2 th": "2 Thessalonians",
    "1tim": "1 Timothy", "1 timothy": "1 Timothy",
    "2tim": "2 Timothy", "2 timothy": "2 Timothy",
    "tit": "Titus", "titus": "Titus",
    "phlm": "Philemon", "philemon": "Philemon",
    "heb": "Hebrews", "hebrews": "Hebrews",
    "jas": "James", "james": "James",
    "1pet": "1 Peter", "1 peter": "1 Peter",
    "2pet": "2 Peter", "2 peter": "2 Peter",
    "1john": "1 John", "1 jn": "1 John",
    "2john": "2 John", "2 jn": "2 John",
    "3john": "3 John", "3 jn": "3 John",
    "jude": "Jude",
    "rev": "Revelation", "revelation": "Revelation", "apocalypse": "Revelation",
}

# ---------------------------------------------------------------------------
# Reference parser
# ---------------------------------------------------------------------------

REF_RE = re.compile(
    r"""
    (?P<book>[1-3]?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)
    \s+
    (?P<chapter>\d+)
    (?:
        :\s*(?P<verse_start>\d+)
        (?:
            [-\u2013\u2014]\s*(?P<verse_end>\d+)
        )?
    )?
    """,
    re.VERBOSE | re.IGNORECASE,
)


def resolve_book_name(raw: str) -> Optional[str]:
    """Resolve a user-provided book name to a canonical name."""
    key = raw.strip().lower()
    if key in BOOK_ALIASES:
        return BOOK_ALIASES[key]
    # try without spaces
    key_nospace = key.replace(" ", "")
    if key_nospace in BOOK_ALIASES:
        return BOOK_ALIASES[key_nospace]
    # fuzzy: check if any alias contains or is contained
    for alias, name in BOOK_ALIASES.items():
        if alias in key or key in alias:
            return name
    return None


def parse_ref(query: str) -> Optional[tuple]:
    """Parse a Bible reference string.

    Returns (canonical_book_name, chapter, verse_start, verse_end) or None.
    verse_start/verse_end are None if not specified (whole chapter).
    """
    m = REF_RE.search(query.strip())
    if not m:
        return None
    book_raw = m.group("book").strip()
    book = resolve_book_name(book_raw)
    if not book:
        return None
    ch = int(m.group("chapter"))
    vs = int(m.group("verse_start")) if m.group("verse_start") else None
    ve = int(m.group("verse_end")) if m.group("verse_end") else vs
    return book, ch, vs, ve


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_kjv() -> dict:
    """Load the KJV Bible with embedded Strong's numbers."""
    with open(KJV_PATH, encoding="utf-8") as f:
        return json.load(f)


def _build_book_map(data: dict) -> dict:
    """Build a {canonical_book_name: book_data} mapping for a translation.

    Handles named, indexed, and unknown-named books.
    """
    books = data["books"]
    mapping = {}

    for i, b in enumerate(books):
        name = b["name"]
        # Case 1: name is already a canonical book name
        if name in CANONICAL_INDEX:
            mapping[name] = b
            continue
        # Case 2: "Book N" — use canonical index
        m = re.match(r"Book\s+(\d+)", name)
        if m:
            idx = int(m.group(1))
            if 1 <= idx <= 66:
                mapping[CANONICAL_BOOKS[idx - 1]] = b
            continue
        # Case 3: "Unknown (...)" — use positional index (0-based)
        if name.startswith("Unknown"):
            if i < 66:
                mapping[CANONICAL_BOOKS[i]] = b
            continue
        # Case 4: any other name — try case-insensitive match
        for canon in CANONICAL_BOOKS:
            if name.lower() == canon.lower():
                mapping[canon] = b
                break

    return mapping


@lru_cache(maxsize=1)
def list_translations() -> list[str]:
    """Return sorted list of available translation file stems."""
    return sorted(
        f.stem for f in TRANSLATIONS_DIR.glob("*.json")
    )


@lru_cache(maxsize=32)
def load_translation(name: str) -> dict:
    """Load a translation by file stem (e.g. 'WEB', 'YLT')."""
    path = TRANSLATIONS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Translation '{name}' not found. Available: {list_translations()}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=32)
def load_translation_books(name: str) -> dict:
    """Load a translation and return the {canonical_name: book_data} map."""
    data = load_translation(name)
    return _build_book_map(data)


@lru_cache(maxsize=1)
def load_strongs_hebrew() -> dict:
    """Load Strong's Hebrew dictionary. Prefers generated JSON, falls back to .js."""
    if STRONGS_HEB_JSON.exists():
        with open(STRONGS_HEB_JSON, encoding="utf-8") as f:
            return json.load(f)
    return _parse_strongs_js(STRONGS_HEB_JS)


@lru_cache(maxsize=1)
def load_strongs_greek() -> dict:
    """Load Strong's Greek dictionary. Prefers generated JSON, falls back to .js."""
    if STRONGS_GRK_JSON.exists():
        with open(STRONGS_GRK_JSON, encoding="utf-8") as f:
            return json.load(f)
    return _parse_strongs_js(STRONGS_GRK_JS)


def _parse_strongs_js(path: Path) -> dict:
    """Parse Open Scriptures .js dictionary file (handles comment + module.exports)."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^/\*\*.*?\*/\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"^var\s+\w+\s*=\s*", "", text.strip())
    text = re.sub(r";\s*module\.exports.*$", "", text, flags=re.DOTALL)
    text = re.sub(r";\s*$", "", text)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Verse retrieval
# ---------------------------------------------------------------------------

def get_verses(translation: str, book: str, chapter: int,
               verse_start: Optional[int] = None,
               verse_end: Optional[int] = None) -> list[dict]:
    """Get verses from a specific translation.

    Returns list of {"verse": int, "text": str} dicts.
    """
    book_map = load_translation_books(translation)
    if book not in book_map:
        return []
    b = book_map[book]
    for ch in b["chapters"]:
        if ch["chapter"] == chapter:
            verses = ch["verses"]
            if verse_start is None:
                return verses
            ve = verse_end or verse_start
            return [v for v in verses if verse_start <= v["verse"] <= ve]
    return []


def get_kjv_verses(book: str, chapter: int,
                   verse_start: Optional[int] = None,
                   verse_end: Optional[int] = None) -> list[dict]:
    """Get verses from KJV (with Strong's numbers embedded)."""
    kjv = load_kjv()
    book_map = _build_book_map(kjv)
    if book not in book_map:
        return []
    b = book_map[book]
    for ch in b["chapters"]:
        if ch["chapter"] == chapter:
            verses = ch["verses"]
            if verse_start is None:
                return verses
            ve = verse_end or verse_start
            return [v for v in verses if verse_start <= v["verse"] <= ve]
    return []


# ---------------------------------------------------------------------------
# Strong's tag extraction (from KJV text)
# ---------------------------------------------------------------------------

STRONGS_TAG_RE = re.compile(r"<S>(\d+)</S>")


def extract_strongs_nums(text: str, book: str | None = None) -> list[str]:
    """Extract Strong's numbers from KJV verse text.

    Returns ['H7225', 'G25', ...]. Bare numbers (no H/G prefix in the
    tag) are resolved using the book name: OT books -> Hebrew (H),
    NT books -> Greek (G).
    """
    nums = STRONGS_TAG_RE.findall(text)
    result = []
    for n in nums:
        if n[0] in "HG":
            result.append(n)
        else:
            # Bare number — resolve by testament
            prefix = "H" if book is None or book in _OT_BOOKS else "G"
            result.append(f"{prefix}{n}")
    return result


def strip_strongs_tags(text: str) -> str:
    """Remove <S>N</S> tags from verse text for plain reading."""
    return STRONGS_TAG_RE.sub("", text)


def lookup_strongs(num: str) -> Optional[dict]:
    """Look up a Strong's entry by number (e.g. 'H1254', 'G25')."""
    if not num:
        return None
    num = num.upper()
    if num[0] == "H":
        return load_strongs_hebrew().get(num)
    elif num[0] == "G":
        return load_strongs_greek().get(num)
    return None
