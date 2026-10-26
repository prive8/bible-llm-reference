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
    "1john": "1 John", "1jn": "1 John", "1 jn": "1 John",
    "2john": "2 John", "2jn": "2 John", "2 jn": "2 John",
    "3john": "3 John", "3jn": "3 John", "3 jn": "3 John",
    "jude": "Jude",
    "rev": "Revelation", "revelation": "Revelation", "apocalypse": "Revelation",
    # Deuterocanonical / apocryphal books. The KJV carries 81 books, not
    # 66, and these extra ones had no aliases at all - so "Wisdom
    # 7:22-26" (the form the v2 benchmark uses) did not resolve, while
    # the corpus's own name "Wisdom of Solomon 1:1" did. An unresolvable
    # expected citation can never be matched, which silently costs
    # recall.
    "tobit": "Tobit", "tob": "Tobit",
    "judith": "Judith", "jdt": "Judith",
    "wisdom": "Wisdom of Solomon", "wisdom of solomon": "Wisdom of Solomon",
    "book of wisdom": "Wisdom of Solomon",
    "sirach": "Sirach", "ecclesiasticus": "Sirach",
    "baruch": "Baruch", "bar": "Baruch",
    "letter of jeremiah": "Letter of Jeremiah",
    "1 maccabees": "1 Maccabees", "1maccabees": "1 Maccabees", "1 mac": "1 Maccabees",
    "2 maccabees": "2 Maccabees", "2maccabees": "2 Maccabees", "2 mac": "2 Maccabees",
    "3 maccabees": "3 Maccabees", "3maccabees": "3 Maccabees", "3 mac": "3 Maccabees",
    "4 maccabees": "4 Maccabees", "4maccabees": "4 Maccabees", "4 mac": "4 Maccabees",
    "1 esdras": "1 Esdras", "1esdras": "1 Esdras",
    "2 esdras": "2 Esdras", "2esdras": "2 Esdras",
    "3 esdras": "3 Esdras", "3esdras": "3 Esdras",
    "4 esdras": "4 Esdras", "4esdras": "4 Esdras",
    "prayer of manasseh": "Prayer of Manasseh",
    "psalms (eob)": "Psalms (EOB)", "psalms eob": "Psalms (EOB)",
    "psalm 151": "Psalm 151",
    "daniel (eob)": "Daniel (EOB)", "daniel eob": "Daniel (EOB)",
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
    """Resolve a user-provided book name to a canonical name.

    Resolution order:
      1. Exact match (with or without spaces) against BOOK_ALIASES keys.
      2. Fuzzy match: exact book name (case-insensitive) against CANONICAL_BOOKS.

    Returns None if no exact match is found. Fuzzy alias-substring match was
    removed 2026-09-09: it was over-permissive and turned "1jn" into "John"
    instead of "1 John" (the alias key "1john" exists but the substring
    fallback matched "jn" first).
    """
    key = raw.strip().lower()
    if key in BOOK_ALIASES:
        return BOOK_ALIASES[key]
    # try without spaces (so "1 john" matches "1john")
    key_nospace = key.replace(" ", "")
    if key_nospace in BOOK_ALIASES:
        return BOOK_ALIASES[key_nospace]
    # exact case-insensitive match against canonical names (no fuzzy)
    for canon in CANONICAL_BOOKS:
        if canon.lower() == key or canon.lower() == key_nospace:
            return canon
    return None


# Chapter[:verse] portion of a reference, used when the book name has
# already been matched separately (see _match_longest_corpus_book).
CHAPTER_VERSE_RE = re.compile(
    r"""
    \s*
    (?P<chapter>\d+)
    (?:
        :\s*(?P<verse_start>\d+)
        (?:
            [-–—]\s*(?P<verse_end>\d+)
        )?
    )?
    """,
    re.VERBOSE,
)


def _match_longest_corpus_book(raw: str) -> Optional[tuple[str, str]]:
    """Match the longest book name from the corpus at the start of ``raw``.

    Returns ``(book_name, remainder)`` or None. The KJV's 81 books
    include several whose names are not in the 66-book canonical list
    and which contain a digit or a parenthetical: "Psalm 151",
    "3 Esdras", "4 Esdras", "Psalms (EOB)", "Daniel (EOB)".

    The reference regex captures at most two alphabetic words, so it
    cannot match "Psalm 151" or "Psalms (EOB)". Left alone it produces
    a wrong parse: "Psalm 151 1:1" became book="Psalms", chapter=151,
    verse=None — a chapter that does not exist. That malformed id
    ("bible:Psalms.151.None") later crashed an evaluation run.

    Longest-match-first is the correct rule: a longer book name is
    always more specific than a shorter prefix of it.
    """
    try:
        books = load_kjv().get("books", [])
    except Exception:
        return None

    names = sorted(
        (b.get("name", "") for b in books if b.get("name")),
        key=len,
        reverse=True,
    )

    lowered = raw.lower()
    for name in names:
        n = name.lower()
        if lowered.startswith(n):
            rest = raw[len(name):].strip()
            # The book name must be followed by a chapter, not by more
            # book-name text.
            if rest and rest[0].isdigit():
                return name, rest
    return None


def parse_ref(query: str) -> Optional[tuple]:
    """Parse a Bible reference string.

    Returns (canonical_book_name, chapter, verse_start, verse_end) or None.
    verse_start/verse_end are None if not specified (whole chapter).

    The KJV contains books whose names are not in the 66-book canonical
    list and which contain a digit: "Psalm 151", "3 Esdras", "4 Esdras",
    "Psalms (EOB)", "Daniel (EOB)". The reference regex captures at most
    two alphabetic words, so "Psalm 151 1:1" parsed as book="Psalm",
    chapter=151 — a chapter that does not exist and a reference to a
    book that was never meant. Prefer the longest book name from the
    actual corpus when one matches.
    """
    raw = query.strip()

    # Prefer a longer, more specific book name from the corpus over the
    # regex's shorter greedy match. "Psalm 151 1:1" must resolve to the
    # book "Psalm 151", not to book "Psalms" chapter 151.
    specific = _match_longest_corpus_book(raw)
    if specific is not None:
        book, rest = specific
        # `rest` is just the chapter[:verse] part - the book name has
        # already been matched, so parse that portion on its own.
        m = CHAPTER_VERSE_RE.match(rest)
        if m:
            ch = int(m.group("chapter"))
            vs = int(m.group("verse_start")) if m.group("verse_start") else None
            ve = int(m.group("verse_end")) if m.group("verse_end") else vs
            return book, ch, vs, ve

    m = REF_RE.search(raw)
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
