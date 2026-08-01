"""Multi-translation parallel verse lookup.

Usage:
    python -m bible parallel "Genesis 1:1"
    python -m bible parallel "John 3:16" --translations WEB,YLT,RSV
    python -m bible parallel "Psalm 23:1" --strongs
    python -m bible parallel "Romans 8:28" --json

Shows a side-by-side comparison of the verse across all (or selected)
translations, plus Strong's enrichment for the key Hebrew/Greek words
when the KJV is available.
"""

from __future__ import annotations

import argparse
import json
import sys

from .lookup import (
    CANONICAL_BOOKS,
    extract_strongs_nums,
    get_kjv_verses,
    get_verses,
    list_translations,
    load_strongs_greek,
    load_strongs_hebrew,
    lookup_strongs,
    parse_ref,
    strip_strongs_tags,
)


def run_parallel(query: str, translations: list[str] | None = None,
                  want_strongs: bool = False, want_json: bool = False) -> None:
    ref = parse_ref(query)
    if not ref:
        print(f"Could not parse reference: {query!r}")
        print("Examples: 'Genesis 1:1', 'John 3:16', 'Psalm 23:1-6'")
        sys.exit(1)

    book, ch, vs, ve = ref
    ve = ve or vs
    ref_str = f"{book} {ch}:{vs}" + (f"-{ve}" if ve and ve != vs else "")

    available = list_translations()
    # Always include KJV (has Strong's numbers)
    all_trans = ["KJV"] + available if "KJV" not in available else available
    # KJV lives at root, not in translations/
    # Filter to requested translations if specified
    if translations:
        # Normalize: uppercase, allow "KJV" even though it's not in translations/
        wanted = [t.upper().strip() for t in translations]
        all_trans = [t for t in all_trans if t in wanted]
        if "KJV" in wanted and "KJV" not in all_trans:
            all_trans.insert(0, "KJV")

    # Collect verses
    results = {}
    for trans in all_trans:
        if trans == "KJV":
            verses = get_kjv_verses(book, ch, vs, ve)
        else:
            verses = get_verses(trans, book, ch, vs, ve)
        if verses:
            results[trans] = verses

    if not results:
        print(f"No translations found for {ref_str}")
        sys.exit(1)

    # JSON output
    if want_json:
        output = {
            "reference": ref_str,
            "book": book,
            "chapter": ch,
            "verse_start": vs,
            "verse_end": ve,
            "translations": {},
        }
        for trans, verses in results.items():
            output["translations"][trans] = [
                {"verse": v["verse"], "text": strip_strongs_tags(v["text"]) if trans == "KJV" else v["text"]}
                for v in verses
            ]
        # Add Strong's if requested
        if want_strongs and "KJV" in results:
            output["strongs"] = _collect_strongs(results["KJV"], book)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Human-readable output
    print(f"\n{'='*70}")
    print(f"  {ref_str}")
    print(f"{'='*70}\n")

    for trans, verses in results.items():
        label = trans
        for v in verses:
            text = strip_strongs_tags(v["text"]) if trans == "KJV" else v["text"]
            print(f"  [{label} {ch}:{v['verse']}] {text}")
        print()

    # Strong's enrichment
    if want_strongs and "KJV" in results:
        strongs_data = _collect_strongs(results["KJV"], book)
        if strongs_data:
            print(f"{'─'*70}")
            print("  Strong's Concordance:")
            print(f"{'─'*70}\n")
            seen = set()
            for item in strongs_data:
                key = item["number"]
                if key in seen:
                    continue
                seen.add(key)
                entry = item["entry"]
                if entry:
                    lemma = entry.get("lemma") or entry.get("xlit") or entry.get("translit") or ""
                    gloss = entry.get("strongs_def") or entry.get("kjv_def") or ""
                    print(f"  {key}  {lemma}")
                    print(f"       {gloss[:100]}")
                    print()

    print(f"{'='*70}")
    print("NOTE: This is a reference tool. Treat as structured text, not spiritual authority.")
    print(f"{'='*70}")


def _collect_strongs(kjv_verses: list[dict], book: str) -> list[dict]:
    """Extract and look up Strong's numbers from KJV verse text."""
    collected = []
    for v in kjv_verses:
        nums = extract_strongs_nums(v["text"], book=book)
        for num in nums:
            entry = lookup_strongs(num)
            collected.append({"number": num, "entry": entry})
    return collected


def main():
    parser = argparse.ArgumentParser(
        prog="bible parallel",
        description="Multi-translation parallel verse lookup",
    )
    parser.add_argument("reference", help="Bible reference (e.g. 'Genesis 1:1')")
    parser.add_argument(
        "--translations", "-t",
        help="Comma-separated list of translations (default: all available)",
        default=None,
    )
    parser.add_argument(
        "--strongs", "-s",
        action="store_true",
        help="Include Strong's concordance enrichment (requires KJV)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()
    translations = args.translations.split(",") if args.translations else None
    run_parallel(
        args.reference,
        translations=translations,
        want_strongs=args.strongs,
        want_json=args.json,
    )


if __name__ == "__main__":
    main()
