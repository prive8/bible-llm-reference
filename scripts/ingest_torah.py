#!/usr/bin/env python3
"""Ingestion script for Phase 3.2: Torah / Five Books of Moses.

Downloads Modernized JPS 1917 (English, CC-BY) and Tanach with Nikkud
(Hebrew, Public Domain) from the Sefaria API and transforms them into
the project canonical multi-tradition format (docs/data-schema.md §2):
    data/torah/{edition}.json

Stdlib-only (urllib.request, json, time). Sefaria asks for polite
client behavior (User-Agent, 1 request/sec) per their robots.txt; we
honor that with `time.sleep(1.05)` between calls.

Sources:
- Sefaria: https://www.sefaria.org/api/texts/<Book>.<Chapter>
- English: "Modernized Tanakh - Based on JPS 1917, Edited by Adam Cohn"
  License: CC-BY (attribution preserved in README.md)
- Hebrew:  "תנ״ך עם ניקוד" (tanach.us/Tanach.xml)
  License: Public Domain
"""

from __future__ import annotations

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
DATA_DIR = ROOT / "data" / "torah"

# ---------------------------------------------------------------------------
# Canonical Torah / Five Books of Moses metadata
# (canonical_name, hebrew_name, transliteration, total_chapters, total_verses)
# ---------------------------------------------------------------------------

BOOKS = [
    ("Genesis", "בראשית", "Bereshit", 50, 1533),
    ("Exodus", "שמות", "Shemot", 40, 1213),
    ("Leviticus", "ויקרא", "Vayikra", 27, 859),
    ("Numbers", "במדבר", "Bamidbar", 36, 1288),
    ("Deuteronomy", "דברים", "Devarim", 34, 959),
]

# Total = 187 chapters, 5,852 verses.

USER_AGENT = "BibleLLM-Ingest/0.11.0 (+https://github.com/prive8/bible-llm-reference)"
SEFARIA_BASE = "https://www.sefaria.org/api/texts"
# Polite delay between requests; Sefaria's robots.txt asks for ≤ 1 req/sec.
POLITE_DELAY_SEC = 1.05


def fetch_chapter(book: str, chapter: int) -> dict:
    """Fetch a single chapter's data from the Sefaria API.

    Returns the raw JSON dict with `text` (English) and `he` (Hebrew) arrays.
    Retries up to 3 times with exponential backoff on transient failures.
    """
    url = f"{SEFARIA_BASE}/{book}.{chapter}"
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # network, timeout, 5xx
            last_err = e
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {book} {chapter}: {last_err}")


def strip_html(text: str) -> str:
    """Remove Sefaria's HTML markup (footnote markers, poetry spans, etc.).

    We keep the verse text plain. Footnote markers like `<sup class="footnote-marker">a</sup>`
    and Hebrew cantillation markup like `<big>...</big>` or `&thinsp;` are
    stripped. This is a conservative stripper — anything we don't recognize
    is left alone (we err on the side of preserving content).
    """
    import re
    # Footnote marker blocks: <sup class="footnote-marker">X</sup>
    text = re.sub(r"<sup[^>]*>.*?</sup>", "", text, flags=re.DOTALL)
    # Footnote bodies: <i class="footnote">...</i>
    text = re.sub(r"<i[^>]*class=\"footnote\"[^>]*>.*?</i>", "", text, flags=re.DOTALL)
    # Other i tags (probably safe to drop — commentary)
    text = re.sub(r"<i[^>]*>.*?</i>", "", text, flags=re.DOTALL)
    # <big>, <small>, <span>, <b> ... </b> open/close
    text = re.sub(r"</?(big|small|span|b|br)[^>]*>", " ", text)
    # HTML entities Sefaria uses
    text = text.replace("&thinsp;", "").replace("&nbsp;", " ")
    text = text.replace("׀", "").replace("{פ}", "¶").replace("{ס}", "§")
    # Collapse whitespace runs
    text = re.sub(r"\s+", " ", text).strip()
    return text


def ingest_edition(edition_key: str, edition_label: str, license_str: str,
                   extract_fn, target_filename: str) -> Path:
    """Walk all books × chapters, call extract_fn(raw) → text, build schema."""
    print(f"  [{edition_key}] starting ({edition_label})...")
    divisions = []
    for canonical, hebrew, translit, n_chapters, n_verses in BOOKS:
        verses = []
        for ch in range(1, n_chapters + 1):
            raw = fetch_chapter(canonical, ch)
            verses_in_chapter = extract_fn(raw)
            for v_num, text in enumerate(verses_in_chapter, start=1):
                verses.append({"verse": v_num, "text": text})
            time.sleep(POLITE_DELAY_SEC)  # polite rate limit
        divisions.append({
            "name": canonical,
            "name_hebrew": hebrew,
            "name_transliteration": translit,
            "chapters_count": n_chapters,
            "verses": verses,
        })
        total_v = sum(len(d["verses"]) for d in divisions)
        print(f"    {canonical}: {n_chapters} chapters, {len(verses)} verses (running total: {total_v})")
    canonical_doc = {
        "tradition": "judaism",
        "translation": edition_label,
        "key": edition_key,
        "language": "he" if edition_key == "hebrew-nikkud" else "en",
        "structure": "book_chapter_verse",
        "license": license_str,
        "source": "Sefaria API (www.sefaria.org)",
        "divisions": divisions,
    }
    target = DATA_DIR / target_filename
    with open(target, "w", encoding="utf-8") as f:
        json.dump(canonical_doc, f, ensure_ascii=False, indent=2)
    print(f"  Wrote {target.name} ({sum(len(d['verses']) for d in divisions)} verses)")
    return target


def extract_english(raw: dict) -> list[str]:
    """Extract the English verse array from Sefaria's response.

    Sefaria returns verses as plain strings or HTML-tagged strings with
    footnote markers. We strip the markup and drop empty entries (chapter
    headers that have no verse content).
    """
    texts = raw.get("text", [])
    cleaned = [strip_html(t) for t in texts if isinstance(t, str)]
    return [t for t in cleaned if t]


def extract_hebrew(raw: dict) -> list[str]:
    """Extract the Hebrew verse array from Sefaria's response.

    Sefaria stores Hebrew in the `he` key (not `text`). Strip HTML markup
    but preserve all Hebrew letters including vowel points (nikkud).
    """
    hebrews = raw.get("he", [])
    cleaned = [strip_html(h) for h in hebrews if isinstance(h, str)]
    return [h for h in cleaned if h]


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ingesting Torah editions into {DATA_DIR}...")
    print(f"Source: Sefaria API ({SEFARIA_BASE}/<Book>.<Chapter>)")
    print(f"Polite delay: {POLITE_DELAY_SEC}s between requests")
    print()
    # Hebrew first (smaller payload, sets baseline)
    ingest_edition(
        edition_key="hebrew-nikkud",
        edition_label="תנ״ך עם ניקוד (Hebrew, vowel-pointed)",
        license_str="Public Domain (tanach.us/Tanach.xml via Sefaria)",
        extract_fn=extract_hebrew,
        target_filename="hebrew-nikkud.json",
    )
    # English (Modernized JPS 1917)
    ingest_edition(
        edition_key="jps1917-modernized",
        edition_label="Modernized Tanakh based on JPS 1917 (Adam Cohn, 2013)",
        license_str="CC-BY (Adam Cohn / modernizedtanakh.blogspot.com)",
        extract_fn=extract_english,
        target_filename="jps1917-modernized.json",
    )
    print()
    print("Torah ingestion complete.")
    print(f"Total verses: {sum(v for _, _, _, _, v in BOOKS)}")
    print(f"Output directory: {DATA_DIR}")


if __name__ == "__main__":
    main()
