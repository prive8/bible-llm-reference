"""Strong's Concordance lookup.

Usage:
    python -m bible strongs H1254
    python -m bible strongs G25
    python -m bible strongs "Genesis 1:1"   # shows all Strong's numbers in that verse
"""

from __future__ import annotations

import argparse
import json
import sys

from .lookup import (
    extract_strongs_nums,
    get_kjv_verses,
    lookup_strongs,
    parse_ref,
    strip_strongs_tags,
)


def run_strongs(query: str, want_json: bool = False) -> None:
    query = query.strip()

    # Check if it's a reference (contains a space + number)
    ref = parse_ref(query)
    if ref:
        book, ch, vs, ve = ref
        ve = ve or vs
        verses = get_kjv_verses(book, ch, vs, ve)
        if not verses:
            print(f"No verses found for {query}")
            sys.exit(1)

        ref_str = f"{book} {ch}:{vs}" + (f"-{ve}" if ve and ve != vs else "")
        print(f"\nStrong's numbers in {ref_str}:\n")

        all_nums = []
        for v in verses:
            nums = extract_strongs_nums(v["text"], book=book)
            plain = strip_strongs_tags(v["text"])
            if nums:
                print(f"  [{ch}:{v['verse']}] {plain}")
                for num in nums:
                    entry = lookup_strongs(num)
                    all_nums.append((num, entry))
                    if entry:
                        lemma = entry.get("lemma") or entry.get("xlit") or entry.get("translit") or ""
                        gloss = entry.get("strongs_def") or entry.get("kjv_def") or ""
                        derivation = entry.get("derivation") or ""
                        print(f"    {num}  {lemma}")
                        print(f"         {gloss}")
                        if derivation:
                            print(f"         {derivation}")
                    else:
                        print(f"    {num}  (no entry found)")
                print()
        return

    # Direct number lookup
    num = query.upper()
    if not num or num[0] not in "HG":
        print(f"Invalid Strong's number: {query!r}")
        print("Use format like 'H1254' or 'G25', or a Bible reference like 'Genesis 1:1'")
        sys.exit(1)

    entry = lookup_strongs(num)
    if not entry:
        print(f"No entry found for {num}")
        sys.exit(1)

    if want_json:
        print(json.dumps({"number": num, "entry": entry}, indent=2, ensure_ascii=False))
        return

    lemma = entry.get("lemma") or entry.get("xlit") or entry.get("translit") or ""
    gloss = entry.get("strongs_def") or entry.get("kjv_def") or ""
    derivation = entry.get("derivation") or ""
    translit = entry.get("translit") or ""
    kjv_def = entry.get("kjv_def") or ""

    print(f"\n{'='*60}")
    print(f"  Strong's {num}")
    print(f"{'='*60}\n")
    if lemma:
        print(f"  Lemma:        {lemma}")
    if translit:
        print(f"  Transliteration: {translit}")
    if derivation:
        print(f"  Derivation:   {derivation}")
    if gloss:
        print(f"  Definition:   {gloss}")
    if kjv_def and kjv_def != gloss:
        print(f"  KJV rendering: {kjv_def}")
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        prog="bible strongs",
        description="Strong's Concordance lookup by number or verse reference",
    )
    parser.add_argument("query", help="Strong's number (H1254, G25) or Bible reference (Genesis 1:1)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    run_strongs(args.query, want_json=args.json)


if __name__ == "__main__":
    main()
