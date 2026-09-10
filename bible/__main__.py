"""Bible LLM Reference CLI entry point.

Usage:
    python -m bible parallel "Genesis 1:1" [--strongs] [--json] [-t WEB,YLT]
    python -m bible strongs H1254
    python -m bible strongs "Genesis 1:1"
    python -m bible search "faith without works" [-t WEB] [-n 10] [--strongs] [--json]
    python -m bible references "John 3:16" [--hops N] [--min-votes V] [--direction out|in|both]
    python -m bible hybrid "comfort in grief" [--bm25-weight 0.5] [--top-k 10]
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

    python -m bible references "John 3:16"
        Look up cross-references (outgoing + reciprocal).

    python -m bible references "Genesis 1:1" --hops 2
        Multi-hop cross-reference expansion (openbible.info, CC-BY 4.0).

    python -m bible quran "Al-Baqarah 2:255"
        Show Quran verse with Arabic text and Saheeh International English.

    python -m bible quran "2:255" -t uthmani,saheeh-international,yusuf-ali
        Show Quran verse across multiple translations.

    python -m bible semantic "finding peace in suffering"
        Search scripture using dense vector embeddings (Milestone 3B).

    python -m bible hybrid "comfort in grief"
        Hybrid BM25 + semantic search (Milestone 3C).

Flags:
    --strongs, -s       Include Strong's enrichment
    --json              JSON output
    -t, --translations  Comma-separated list of translations (parallel, quran)
    -t, --translation   Translation to search (search, default: KJV)
    -n, --limit         Result limit (search, default: 10)
    --top-k             Result limit (semantic, default: 10)
    --tradition         Filter tradition: all|bible|islam (semantic, default: all)
    --hops              Multi-hop depth (references, 1-3, default: 1)
    --min-votes         Vote threshold (references, default: 3)
    --direction         out|in|both (references, default: out)
    --bm25-weight       Weight on BM25 vs semantic in hybrid (default: 0.5)
    --solo-weight       Multiplier for solo (non-reciprocal) hits (default: 0.7)
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
    elif command == "references":
        from bible.references import main as references_main
        sys.argv = ["bible references"] + rest
        references_main()
    elif command == "quran":
        from bible.quran import main as quran_main
        sys.argv = ["bible quran"] + rest
        quran_main()
    elif command == "semantic":
        from bible.semantic import main as semantic_main
        sys.argv = ["bible semantic"] + rest
        semantic_main()
    elif command == "hybrid":
        from bible.hybrid import main as hybrid_main
        sys.argv = ["bible hybrid"] + rest
        hybrid_main()
    else:
        print(f"Unknown command: {command!r}")
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
