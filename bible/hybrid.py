"""Hybrid BM25 + semantic search fusion (Milestone 3C).

Combines keyword retrieval (BM25, `bible.search`) with dense vector
retrieval (cosine similarity, `bible.semantic`) into a single ranked
result set. Two key design choices:

1. **Citation-keyed join.** BM25 results use Bible citations like
   "John 3:16"; semantic results use "John 3:16" or "Quran 2:255".
   Hybrid fusion joins on citation string. Verses that appear in
   both sources get a combined score; verses that appear in only
   one source are scored on that source alone (multiplied by a
   `solo_weight` factor so they don't fully die but don't compete
   with reciprocal hits either).

2. **Min-max normalization before weighted sum.** BM25 raw scores
   have no upper bound and depend on query length; cosine similarities
   are in [-1, 1]. Without normalization the BM25 component would
   dominate. We normalize per-query (across the BM25 result set) into
   [0, 1], then `final = α * bm25_norm + (1 - α) * cosine` where
   `α = bm25_weight` (default 0.5). This is the standard Reciprocal
   Rank Fusion (RRF) cousin — slightly less principled but cheap and
   battle-tested.

CLI:
    python -m bible hybrid "comfort in grief" [--bm25-weight 0.5] [--top-k 10] [--json]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Optional


# Helper: reconfigure stdout to UTF-8 for Windows console safety. Done at
# module-import time so every entry point gets it (same pattern as the
# other CLIs in this package).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Default weight on BM25 vs semantic. 0.5 = equal. Tune per use case.
DEFAULT_BM25_WEIGHT = 0.5
# When a verse appears in only ONE source, scale that source's score by
# this factor. < 1.0 so reciprocal hits naturally outrank solos. 0.7 is
# a common default; tune if needed.
DEFAULT_SOLO_WEIGHT = 0.7


def _min_max_normalize(scores: list[float]) -> list[float]:
    """Normalize a list of scores to [0, 1]. Equal scores → all 1.0.

    Returns a list of the same length. If the range is 0 (all equal),
    every output is 1.0 (so the contribution isn't zeroed out).
    """
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi == lo:
        return [1.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def hybrid_search(
    query: str,
    bm25_results: list[dict],
    semantic_results: list[dict],
    bm25_weight: float = DEFAULT_BM25_WEIGHT,
    solo_weight: float = DEFAULT_SOLO_WEIGHT,
    top_k: int = 10,
) -> list[dict]:
    """Combine BM25 + semantic results into a single ranked list.

    Args:
        query: User's query (echoed in output for context).
        bm25_results: From `bible.search.run_search(...).as_dict_list`.
            Must have keys: ``citation``, ``score``, ``text``.
        semantic_results: From `bible.semantic.run_semantic(...).as_dict_list`.
            Must have keys: ``citation``, ``score``, ``text``, ``tradition``,
            ``translation``.
        bm25_weight: [0, 1]. 1.0 = pure BM25, 0.0 = pure semantic.
        solo_weight: Multiplier for sources that appear in only one result set.
        top_k: Return top N by combined score.

    Returns: list of dicts sorted by combined score (descending). Each dict
        has ``citation``, ``text``, ``combined_score``, ``bm25_score``
        (None if not in BM25), ``semantic_score`` (None if not in semantic),
        ``source`` (e.g. "both", "bm25", "semantic").
    """
    semantic_weight = 1.0 - bm25_weight

    # Index by citation. Build normalized scores per source.
    bm25_by_cite: dict[str, dict] = {}
    if bm25_results:
        bm25_scores = [r["score"] for r in bm25_results]
        bm25_norm = _min_max_normalize(bm25_scores)
        for r, norm in zip(bm25_results, bm25_norm):
            bm25_by_cite[r["citation"]] = {
                "raw_score": r["score"],
                "norm_score": norm,
                "text": r.get("text", ""),
                "translation": r.get("translation", "KJV"),
                "tradition": r.get("tradition", "christianity"),
            }

    semantic_by_cite: dict[str, dict] = {}
    if semantic_results:
        sem_scores = [r["score"] for r in semantic_results]
        sem_norm = _min_max_normalize(sem_scores)
        for r, norm in zip(semantic_results, sem_norm):
            semantic_by_cite[r["citation"]] = {
                "raw_score": r["score"],
                "norm_score": norm,
                "text": r.get("text", ""),
                "translation": r.get("translation", ""),
                "tradition": r.get("tradition", ""),
            }

    # Union of citations
    all_cites = set(bm25_by_cite) | set(semantic_by_cite)

    fused = []
    for cite in all_cites:
        in_bm25 = cite in bm25_by_cite
        in_semantic = cite in semantic_by_cite

        if in_bm25 and in_semantic:
            bm25_part = bm25_by_cite[cite]["norm_score"] * bm25_weight
            sem_part = semantic_by_cite[cite]["norm_score"] * semantic_weight
            combined = bm25_part + sem_part
            source = "both"
            # Prefer BM25's text for the citation's primary text (Bible canon
            # is the reference corpus; Quran text is the alternate)
            text = bm25_by_cite[cite]["text"]
            translation = bm25_by_cite[cite]["translation"]
            tradition = bm25_by_cite[cite]["tradition"]
            bm25_score = bm25_by_cite[cite]["raw_score"]
            semantic_score = semantic_by_cite[cite]["raw_score"]
        elif in_bm25:
            combined = bm25_by_cite[cite]["norm_score"] * bm25_weight * solo_weight
            source = "bm25"
            text = bm25_by_cite[cite]["text"]
            translation = bm25_by_cite[cite]["translation"]
            tradition = bm25_by_cite[cite]["tradition"]
            bm25_score = bm25_by_cite[cite]["raw_score"]
            semantic_score = None
        else:
            combined = semantic_by_cite[cite]["norm_score"] * semantic_weight * solo_weight
            source = "semantic"
            text = semantic_by_cite[cite]["text"]
            translation = semantic_by_cite[cite]["translation"]
            tradition = semantic_by_cite[cite]["tradition"]
            bm25_score = None
            semantic_score = semantic_by_cite[cite]["raw_score"]

        fused.append({
            "citation": cite,
            "text": text,
            "translation": translation,
            "tradition": tradition,
            "combined_score": round(combined, 4),
            "bm25_score": bm25_score,
            "semantic_score": semantic_score,
            "source": source,
        })

    fused.sort(key=lambda x: x["combined_score"], reverse=True)
    return fused[:top_k]


def run_hybrid(
    query: str,
    bm25_results: list[dict],
    semantic_results: list[dict],
    bm25_weight: float = DEFAULT_BM25_WEIGHT,
    solo_weight: float = DEFAULT_SOLO_WEIGHT,
    top_k: int = 10,
    as_json: bool = False,
) -> list[dict]:
    """High-level runner for hybrid search. Returns the fused result list."""
    results = hybrid_search(
        query=query,
        bm25_results=bm25_results,
        semantic_results=semantic_results,
        bm25_weight=bm25_weight,
        solo_weight=solo_weight,
        top_k=top_k,
    )

    if as_json:
        print(json.dumps({
            "query": query,
            "bm25_weight": bm25_weight,
            "solo_weight": solo_weight,
            "results_count": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2))
        return results

    print("=" * 78)
    print(f"  Hybrid Search for: {query!r}")
    print(f"  BM25 weight: {bm25_weight} | Solo weight: {solo_weight}")
    print("=" * 78)

    if not results:
        print("\nNo matches found in either source.")
        return results

    for i, r in enumerate(results, 1):
        trad = f"[{r['tradition'].upper()}]" if r.get("tradition") else ""
        print(f"\n{i}. {r['citation']} {trad} (combined: {r['combined_score']:.3f}, source: {r['source']})")
        print(f"   \"{r['text'][:200]}{'...' if len(r['text']) > 200 else ''}\"")

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="bible hybrid",
        description="Hybrid BM25 + semantic search (Milestone 3C)",
    )
    parser.add_argument("query", help="Natural-language query")
    parser.add_argument(
        "--bm25-weight", type=float, default=DEFAULT_BM25_WEIGHT,
        help=f"Weight on BM25 vs semantic in [0, 1] (default {DEFAULT_BM25_WEIGHT})",
    )
    parser.add_argument(
        "--solo-weight", type=float, default=DEFAULT_SOLO_WEIGHT,
        help=f"Multiplier for verses appearing in only one source (default {DEFAULT_SOLO_WEIGHT})",
    )
    parser.add_argument(
        "--top-k", type=int, default=10,
        help="Number of results to return (default 10)",
    )
    parser.add_argument(
        "--translation", default="KJV",
        help="Translation for the BM25 leg (default KJV)",
    )
    parser.add_argument(
        "--bm25-limit", type=int, default=20,
        help="How many BM25 candidates to fetch before fusion (default 20)",
    )
    parser.add_argument(
        "--semantic-limit", type=int, default=20,
        help="How many semantic candidates to fetch before fusion (default 20)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    # Lazy import to keep `bible hybrid` startup fast (sentence-transformers
    # is heavy; the BM25 path is much lighter).
    from bible.search import run_search
    from bible.semantic import run_semantic

    # Fetch candidates from both sources. run_search returns results
    # as printed output; we want the structured list. Use the underlying
    # BM25Index.search() for the BM25 leg and search_semantic() for
    # the semantic leg (they both return structured dicts).
    from bible.search import get_bm25_index
    from bible.semantic import search_semantic

    bm25_idx = get_bm25_index(args.translation)
    bm25_hits = bm25_idx.search(args.query, limit=args.bm25_limit)
    bm25_dicts = [
        {"citation": h["reference"], "score": h["score"], "text": h["text"],
         "translation": args.translation, "tradition": "christianity"}
        for h in bm25_hits
    ]

    sem_hits = search_semantic(
        args.query,
        index_name="default",
        top_k=args.semantic_limit,
        tradition=None,
        backend="auto",
    )

    run_hybrid(
        query=args.query,
        bm25_results=bm25_dicts,
        semantic_results=sem_hits,
        bm25_weight=args.bm25_weight,
        solo_weight=args.solo_weight,
        top_k=args.top_k,
        as_json=args.json,
    )


if __name__ == "__main__":
    main()
