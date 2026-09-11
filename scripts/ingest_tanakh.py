#!/usr/bin/env python3
"""Ingestion script for Phase 3.3: Tanakh (Torah + Nevi'im + Ketuvim).

Downloads Modernized JPS 1917 (English, CC-BY) and תנ״ך עם ניקוד (Hebrew
with vowel points, Public Domain) from the Sefaria API, and transforms
them into the project canonical multi-tradition format
(docs/data-schema.md §2):

    data/tanakh/{edition}.json

Stdlib-only (urllib.request, json, time). Sefaria asks for polite
client behavior (User-Agent, 1 request/sec) per their robots.txt; we
honor that with `time.sleep(1.05)` between calls.

Sources (per docs/phase3-scope-tanakh.md):
- Sefaria: https://www.sefaria.org/api/texts/<Book>.<Chapter>
- English: "Modernized Tanakh based on JPS 1917, Edited by Adam Cohn"
  License: CC-BY (Adam Cohn / modernizedtanakh.blogspot.com)
- Hebrew:  "תנ״ך עם נikud" (tanach.us/Tanach.xml)
  License: Public Domain

Reuses the same editions as the Torah phase (v0.11.0) so the canon is
internally consistent across the Torah + Nevi'im + Ketuvim boundary.

Usage:
    # Full ingest (~35-40 min due to Sefaria politeness × ~570 chapters)
    python3 scripts/ingest_tanakh.py

    # Just one book (debugging)
    python3 scripts/ingest_tanakh.py --only-book "Joshua"

    # Skip books we already have (for re-runs after partial failures)
    python3 scripts/ingest_tanakh.py --skip-existing

Note: Torah books (Genesis..Deuteronomy) will be re-ingested from
Sefaria and written to data/tanakh/*.json. The data/torah/*.json
files remain untouched. Both directories point at the same underlying
texts; the split exists for adapter-narrowness (bible.torah vs
bible.tanakh), not data duplication concerns.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "tanakh"

# ---------------------------------------------------------------------------
# Canonical Tanakh metadata
# (canonical_name, hebrew_name, transliteration, total_chapters, total_verses, section)
# Mirrors bible/tanakh.py BOOKS exactly. Kept self-contained for clarity.
# ---------------------------------------------------------------------------

BOOKS = [
    ("Genesis", "בראשית", "Bereshit", 50, 1533, "Torah"),
    ("Exodus", "שמות", "Shemot", 40, 1213, "Torah"),
    ("Leviticus", "ויקרא", "Vayikra", 27, 859, "Torah"),
    ("Numbers", "במדבר", "Bamidbar", 36, 1288, "Torah"),
    ("Deuteronomy", "דברים", "Devarim", 34, 959, "Torah"),
    ("Joshua", "יהושע", "Yehoshua", 24, 658, "Nevi'im"),
    ("Judges", "שופטים", "Shoftim", 21, 618, "Nevi'im"),
    ("Samuel I", "שמואל א", "Shemuel I", 31, 810, "Nevi'im"),
    ("Samuel II", "שמואל ב", "Shemuel II", 24, 695, "Nevi'im"),
    ("Kings I", "מלכים א", "Melachim I", 22, 816, "Nevi'im"),
    ("Kings II", "מלכים ב", "Melachim II", 25, 719, "Nevi'im"),
    ("Isaiah", "ישעיהו", "Yeshayahu", 66, 1292, "Nevi'im"),
    ("Jeremiah", "ירמיהו", "Yirmiyahu", 52, 1364, "Nevi'im"),
    ("Ezekiel", "יחזקאל", "Yechezkel", 48, 1273, "Nevi'im"),
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

# Sefaria uses Roman-numeral prefixes for split books. Sefaria accepts
# spaces or underscores in URL paths but urllib3 (and many HTTP
# libraries) treat literal-space URLs as malformed; we use underscores.
SEFARIA_BOOK_NAME = {
    "Samuel I": "I_Samuel",
    "Samuel II": "II_Samuel",
    "Kings I": "I_Kings",
    "Kings II": "II_Kings",
    "Chronicles I": "I_Chronicles",
    "Chronicles II": "II_Chronicles",
    "Song of Songs": "Song_of_Songs",
}

USER_AGENT = "BibleLLM-Ingest/0.14.0 (+https://github.com/prive8/bible-llm-reference)"
SEFARIA_BASE = "https://www.sefaria.org/api/texts"
POLITE_DELAY_SEC = 1.05


# ---------------------------------------------------------------------------
# HTTP + parsing
# ---------------------------------------------------------------------------

def fetch_chapter(sefaria_book: str, chapter: int) -> dict:
    """Fetch a single chapter's data from the Sefaria API.

    Returns the raw JSON dict with `text` (English) and `he` (Hebrew) arrays.
    Retries up to 3 times with exponential backoff on transient failures.

    Notes on HTTP client choices:
    - We use stdlib `urllib.request` (no extra dependency).
    - We send `Connection: close` to disable HTTP keep-alive — during the
      long Tanakh ingest (1,858 chapters), Python's urllib keep-alive
      pool was hanging on Sefaria's rate limiter after ~20 minutes of
      continuous use. Forcing a fresh connection per request trades a
      tiny per-request latency penalty for reliable long-running behavior.
    - We also use a short (10s) timeout — if Sefaria is slow, fail fast
      and retry rather than hang.
    """
    url = f"{SEFARIA_BASE}/{sefaria_book}.{chapter}"
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                    "Connection": "close",  # disable keep-alive; see docstring
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # network, timeout, 5xx
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {sefaria_book} {chapter}: {last_err}")


def strip_html(text: str) -> str:
    """Remove Sefaria's HTML markup.

    Footnote markers, poetry spans, cantillation markers (big/small/span),
    NBSP/THINSP, paragraph markers — all stripped. Conservatively leaves
    unrecognized markup alone (we err on the side of preserving content).
    """
    import re
    text = re.sub(r"<sup[^>]*>.*?</sup>", "", text, flags=re.DOTALL)
    text = re.sub(r"<i[^>]*class=\"footnote\"[^>]*>.*?</i>", "", text, flags=re.DOTALL)
    text = re.sub(r"<i[^>]*>.*?</i>", "", text, flags=re.DOTALL)
    text = re.sub(r"</?(big|small|span|b|br)[^>]*>", " ", text)
    text = text.replace("&thinsp;", "").replace("&nbsp;", " ")
    text = text.replace("׀", "").replace("{פ}", "¶").replace("{ס}", "§")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_english(raw: dict) -> list[str]:
    """Extract the English verse array from Sefaria's response."""
    texts = raw.get("text", [])
    cleaned = [strip_html(t) for t in texts if isinstance(t, str)]
    return [t for t in cleaned if t]


def extract_hebrew(raw: dict) -> list[str]:
    """Extract the Hebrew verse array from Sefaria's response.

    NOTE: Hebrew is in the `he` key, NOT `text`. This is the silent-bug
    fix that prevents the v0.11.0-class English-into-Hebrew-field mistake
    (see scripts/ingest_torah.py revision history).
    """
    hebrews = raw.get("he", [])
    cleaned = [strip_html(h) for h in hebrews if isinstance(h, str)]
    return [h for h in cleaned if h]


# ---------------------------------------------------------------------------
# Edition ingest
# ---------------------------------------------------------------------------

def _load_partial(target_path: Path) -> tuple[dict, list[str]]:
    """Load an existing partial edition file for incremental update.

    Returns (canonical_doc, books_already_present).
    The doc dict is built from scratch; books_already_present is the list
    of book names with non-empty verse arrays. Caller uses this to skip
    books that are already fully ingested.
    """
    if not target_path.exists():
        return None, []
    with open(target_path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    already = [d["name"] for d in doc.get("divisions", []) if d.get("verses")]
    return doc, already


def ingest_edition(edition_key: str, edition_label: str, license_str: str,
                   extract_fn, target_filename: str,
                   only_book: str | None = None,
                   skip_existing: bool = False,
                   incremental: bool = True) -> Path | None:
    """Walk all books × chapters, call extract_fn(raw) → text, build schema.

    Per-book writes: after each book completes, the JSON file is rewritten
    with the new book appended. This means a long-running ingest can be
    interrupted and resumed without losing the books that already completed.

    With --only-book: writes only that one book (still per-book incremental).
    With --skip-existing and a complete edition on disk: skip the edition.
    """
    print(f"  [{edition_key}] starting ({edition_label})...")
    target = DATA_DIR / target_filename

    # Load partial state for incremental mode
    canonical_doc = None
    already_present: list[str] = []
    if incremental and target.exists():
        canonical_doc, already_present = _load_partial(target)
        if canonical_doc is not None:
            print(f"  [{edition_key}] resuming — {len(already_present)} book(s) already present: {already_present}")

    if skip_existing and target.exists() and not only_book and not canonical_doc:
        # skip the whole edition (no partial state to resume)
        print(f"  [{edition_key}] {target.name} exists, skipping (--skip-existing)")
        return None

    if canonical_doc is None:
        canonical_doc = {
            "tradition": "judaism",
            "translation": edition_label,
            "key": edition_key,
            "language": "he" if edition_key == "hebrew-nikkud" else "en",
            "structure": "book_chapter_verse",
            "license": license_str,
            "source": "Sefaria API (www.sefaria.org)",
            "divisions": [],
        }

    divisions_by_name = {d["name"]: d for d in canonical_doc.get("divisions", [])}
    total_expected_verses = 0
    total_actual_verses = sum(
        sum(len(v) for v in d.get("verses", []))
        for d in canonical_doc.get("divisions", [])
    )

    for canonical, hebrew, translit, n_chapters, n_verses, section in BOOKS:
        if only_book and canonical != only_book:
            continue

        # Skip if this book is already fully present (incremental mode)
        if incremental and canonical in already_present:
            print(f"    {canonical} ({section}): already present, skipping")
            total_expected_verses += n_verses
            continue

        sefaria_book = SEFARIA_BOOK_NAME.get(canonical, canonical)
        verses = []
        for ch in range(1, n_chapters + 1):
            try:
                raw = fetch_chapter(sefaria_book, ch)
            except RuntimeError as e:
                print(f"    ERROR {canonical} chapter {ch}: {e}")
                continue
            verses_in_chapter = extract_fn(raw)
            for v_num, text in enumerate(verses_in_chapter, start=1):
                verses.append({"verse": v_num, "text": text})
            time.sleep(POLITE_DELAY_SEC)  # polite rate limit

        total_expected_verses += n_verses
        total_actual_verses += len(verses)
        book_obj = {
            "name": canonical,
            "name_hebrew": hebrew,
            "name_transliteration": translit,
            "section": section,
            "chapters_count": n_chapters,
            "verses": verses,
        }
        divisions_by_name[canonical] = book_obj
        # Reorder canonical_doc["divisions"] to follow BOOKS order
        canonical_doc["divisions"] = [
            divisions_by_name[b[0]]
            for b in BOOKS if b[0] in divisions_by_name
        ]
        # Per-book write: incremental progress so a long-running ingest
        # can be interrupted and resumed. Recompute totals from the doc
        # itself rather than incrementally (which had a double-count bug).
        total_actual_verses = sum(
            len(v) for d in canonical_doc.get("divisions", [])
            for v in d.get("verses", [])
        )
        if incremental and not only_book:
            with open(target, "w", encoding="utf-8") as f:
                json.dump(canonical_doc, f, ensure_ascii=False, indent=2)
            print(f"    {canonical} ({section}): {n_chapters} chapters, "
                  f"{len(verses)} verses (wrote {target.name}; "
                  f"running total: {total_actual_verses} of {total_expected_verses} expected)")
        else:
            print(f"    {canonical} ({section}): {n_chapters} chapters, "
                  f"{len(verses)} verses (running total: {total_actual_verses} "
                  f"of {total_expected_verses} expected)")
        if only_book:
            break  # Only ingest the requested book

    if incremental:
        # Final write ensures the file is canonical-ordered and complete
        with open(target, "w", encoding="utf-8") as f:
            json.dump(canonical_doc, f, ensure_ascii=False, indent=2)
    else:
        # Single-shot write (legacy behavior)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(canonical_doc, f, ensure_ascii=False, indent=2)

    print(f"  Wrote {target.name} ({total_actual_verses} verses, "
          f"{total_expected_verses - total_actual_verses} missing)")
    return target


def main():
    parser = argparse.ArgumentParser(description="Tanakh ingestion (Torah + Nevi'im + Ketuvim)")
    parser.add_argument("--only-book", default=None,
                        help="Only ingest a single book (e.g. 'Joshua') for debugging")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip editions whose output file already exists")
    parser.add_argument("--no-incremental", action="store_true",
                        help="Disable per-book incremental writes (legacy single-shot mode)")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ingesting Tanakh editions into {DATA_DIR}...")
    print(f"Source: Sefaria API ({SEFARIA_BASE}/<Book>.<Chapter>)")
    print(f"Polite delay: {POLITE_DELAY_SEC}s between requests")
    print(f"Books: {len(BOOKS)} total (5 Torah + 21 Nevi'im + 13 Ketuvim)")
    print(f"Total chapters: {sum(b[3] for b in BOOKS)}")
    print(f"Total verses (canonical): {sum(b[4] for b in BOOKS)}")
    print()

    if args.only_book:
        print(f"*** --only-book {args.only_book}: single-book mode ***")
        print()

    incremental = not args.no_incremental
    if not incremental:
        print("*** --no-incremental: legacy single-shot mode ***")
        print()

    # Hebrew first (smaller payload, sets baseline)
    ingest_edition(
        edition_key="hebrew-nikkud",
        edition_label="תנ״ך עם ניקוד (Hebrew, vowel-pointed)",
        license_str="Public Domain (tanach.us/Tanach.xml via Sefaria)",
        extract_fn=extract_hebrew,
        target_filename="hebrew-nikkud.json",
        only_book=args.only_book,
        skip_existing=args.skip_existing,
        incremental=incremental,
    )
    # English (Modernized JPS 1917)
    ingest_edition(
        edition_key="jps1917-modernized",
        edition_label="Modernized Tanakh based on JPS 1917 (Adam Cohn, 2013)",
        license_str="CC-BY (Adam Cohn / modernizedtanakh.blogspot.com)",
        extract_fn=extract_english,
        target_filename="jps1917-modernized.json",
        only_book=args.only_book,
        skip_existing=args.skip_existing,
        incremental=incremental,
    )
    print()
    print("Tanakh ingestion complete.")


if __name__ == "__main__":
    main()
