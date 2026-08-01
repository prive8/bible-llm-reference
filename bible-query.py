#!/usr/bin/env python3
"""
Bible LLM Reference Tool – upgraded
Exact refs + keyword search + Strong’s enrichment.
Designed for RAG / local LLM pipelines. Never pretends to be a spiritual entity.
"""

import json
import re
import sys
import os
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent
KJV_PATH = ROOT / "kjv.json"
STRONGS_HEB = ROOT / "strongs_data/hebrew/strongs-hebrew-dictionary.js"
STRONGS_GRK = ROOT / "strongs_data/greek/strongs-greek-dictionary.js"

# ---------- Book name / abbreviation maps ----------
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

# ---------- Load data once ----------
print("Loading KJV...", flush=True)
with open(KJV_PATH, encoding="utf-8") as f:
    BIBLE = json.load(f)
BOOK_INDEX = {b["name"].lower(): b for b in BIBLE["books"]}
print(f"Loaded {len(BIBLE['books'])} books", flush=True)

def load_strongs(js_path: Path) -> dict:
    """Very lightweight parser for the Open Scriptures .js dictionary files."""
    if not js_path.exists():
        return {}
    text = js_path.read_text(encoding="utf-8")
    # Strip the var assignment and trailing ;
    text = re.sub(r"^var\s+\w+\s*=\s*", "", text.strip())
    text = re.sub(r";\s*$", "", text)
    # Crude but effective: turn into JSON-like by quoting keys if needed
    # Most files are already almost valid JSON objects
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback regex extraction
        entries = {}
        for m in re.finditer(r'"(H|G)(\d+)":\s*(\{.*?\})(?=\s*,\s*"(?:H|G)\d+"|\s*\})', text, re.DOTALL):
            key = m.group(1) + m.group(2)
            try:
                entries[key] = json.loads(m.group(3))
            except Exception:
                pass
        return entries

print("Loading Strong's (this may take a few seconds)...", flush=True)
HEB = load_strongs(STRONGS_HEB)
GRK = load_strongs(STRONGS_GRK)
print(f"Strong's loaded: {len(HEB)} Hebrew, {len(GRK)} Greek", flush=True)

# ---------- Verse reference parser ----------
REF_RE = re.compile(
    r"""
    (?P<book>[1-3]?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)
    \s*
    (?P<chapter>\d+)
    (?:
        :\s*(?P<verse_start>\d+)
        (?:
            [-–—]\s*(?P<verse_end>\d+)
        )?
    )?
    """,
    re.VERBOSE | re.IGNORECASE,
)

def parse_ref(query: str):
    m = REF_RE.search(query.strip())
    if not m:
        return None
    book_raw = m.group("book").strip().lower()
    book = BOOK_ALIASES.get(book_raw) or BOOK_ALIASES.get(book_raw.replace(" ", ""))
    if not book:
        # fuzzy fallback
        for alias, name in BOOK_ALIASES.items():
            if alias in book_raw or book_raw in alias:
                book = name
                break
    if not book or book.lower() not in BOOK_INDEX:
        return None
    ch = int(m.group("chapter"))
    vs = int(m.group("verse_start")) if m.group("verse_start") else None
    ve = int(m.group("verse_end")) if m.group("verse_end") else vs
    return book, ch, vs, ve

def get_verses_by_ref(book, chapter, v_start=None, v_end=None):
    b = BOOK_INDEX[book.lower()]
    for ch in b["chapters"]:
        if ch["chapter"] == chapter:
            verses = ch["verses"]
            if v_start is None:
                return verses
            return [v for v in verses if v_start <= v["verse"] <= (v_end or v_start)]
    return []

# ---------- Keyword search ----------
def search_bible(query: str, max_verses=60):
    words = [w.lower() for w in re.findall(r"[a-zA-Z']+", query) if len(w) > 2]
    if not words:
        return []
    results = []
    for book in BIBLE["books"]:
        for ch in book["chapters"]:
            for v in ch["verses"]:
                text = v["text"].lower()
                score = sum(1 for w in words if w in text)
                if score:
                    results.append({
                        "book": book["name"],
                        "chapter": ch["chapter"],
                        "verse": v["verse"],
                        "text": v["text"],
                        "score": score,
                    })
    results.sort(key=lambda x: (-x["score"], len(x["text"])))
    return results[:max_verses]

# ---------- Strong’s enrichment ----------
STRONGS_TAG_RE = re.compile(r"<S>(\d+)</S>")

def enrich_with_strongs(text: str) -> str:
    def repl(m):
        num = m.group(1)
        entry = HEB.get(f"H{num}") or GRK.get(f"G{num}")
        if not entry:
            return f"[S{num}]"
        lemma = entry.get("lemma") or entry.get("xlit") or entry.get("translit") or ""
        gloss = entry.get("strongs_def") or entry.get("kjv_def") or ""
        return f"{lemma} (S{num}: {gloss[:60]}…)" if gloss else f"{lemma} (S{num})"
    return STRONGS_TAG_RE.sub(repl, text)

# ---------- Main ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python bible-query.py 'John 3:16'   or   'faith without works'")
        print("Flags: --strongs   --json")
        sys.exit(1)

    args = sys.argv[1:]
    want_strongs = "--strongs" in args
    want_json = "--json" in args
    query = " ".join(a for a in args if not a.startswith("--"))

    # 1. Try exact reference first
    ref = parse_ref(query)
    if ref:
        book, ch, vs, ve = ref
        verses = get_verses_by_ref(book, ch, vs, ve)
        print(f"\nExact reference: {book} {ch}" + (f":{vs}" + (f"-{ve}" if ve and ve != vs else "") if vs else ""))
        for v in verses:
            text = enrich_with_strongs(v["text"]) if want_strongs else v["text"]
            print(f"  [{book} {ch}:{v['verse']}] {text}")
        if want_json:
            print(json.dumps(verses, indent=2, ensure_ascii=False))
        return

    # 2. Keyword search
    print(f"\nSearching keywords: {query}")
    results = search_bible(query)
    if not results:
        print("No matches.")
        sys.exit(1)

    primary = [r for r in results if r["score"] >= 2]
    related = [r for r in results if r["score"] == 1]

    print(f"\nPRIMARY ({len(primary)}):")
    for r in primary[:15]:
        text = enrich_with_strongs(r["text"]) if want_strongs else r["text"]
        print(f"  [{r['book']} {r['chapter']}:{r['verse']}] {text}")

    if related:
        print(f"\nRELATED ({len(related)}):")
        for r in related[:20]:
            text = enrich_with_strongs(r["text"]) if want_strongs else r["text"]
            print(f"  [{r['book']} {r['chapter']}:{r['verse']}] {text}")

    # LLM context block
    print("\n" + "=" * 60)
    print("CONTEXT FOR LLM (copy-paste ready)")
    print("=" * 60)
    print(f"Query: {query}\n")
    for r in (primary + related)[:25]:
        text = enrich_with_strongs(r["text"]) if want_strongs else r["text"]
        print(f"[{r['book']} {r['chapter']}:{r['verse']}] {text}")
    print("=" * 60)
    print("NOTE: This is structured text only. Treat as a reference tool, not a spiritual authority.")

if __name__ == "__main__":
    main()