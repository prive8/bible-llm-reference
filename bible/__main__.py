"""Bible LLM Reference CLI entry point.

Usage:
    python -m bible parallel "Genesis 1:1" [--strongs] [--json] [-t WEB,YLT]
    python -m bible strongs H1254
    python -m bible strongs "Genesis 1:1"
    python -m bible search "faith without works" [-t WEB] [-n 10] [--strongs] [--json]
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

USAGE = """\
bible — Bible LLM Reference CLI

Usage:
    python -m bible parallel "Genesis 1:1"
        Show a verse across all available translations.

    python -m bible parallel "John 3:16" --strongs
        Include Strong's concordance enrichment.

    python -m bible parallel "John 3:16" -t WEB,YLT,RSV
        Limit to specific translations.

    python -m bible strongs H1254
        Look up a Strong's number.

    python -m bible strongs "Genesis 1:1"
        Show all Strong's numbers in a verse.

    python -m bible search "faith without works"
        Search Bible text using Okapi BM25 keyword ranking.

    python -m bible search "light" -t WEB -n 5
        Search specific translation with a limit.

Flags:
    --strongs, -s       Include Strong's enrichment
    --json              JSON output
    -t, --translations  Comma-separated list of translations (parallel)
    -t, --translation   Translation to search (search, default: KJV)
    -n, --limit         Result limit (search, default: 10)
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(0)

    command = sys.argv[1]
    rest = sys.argv[2:]

    if command == "parallel":
        from bible.parallel import main as parallel_main
        sys.argv = ["bible parallel"] + rest
        parallel_main()
    elif command == "strongs":
        from bible.strongs import main as strongs_main
        sys.argv = ["bible strongs"] + rest
        strongs_main()
    elif command == "search":
        from bible.search import main as search_main
        sys.argv = ["bible search"] + rest
        search_main()
    else:
        print(f"Unknown command: {command!r}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
