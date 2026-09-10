#!/usr/bin/env python3
"""Evaluation harness for the bible-llm-reference retrieval stack.

Runs the hand-curated benchmark in `tests/benchmark.py` through three
retrieval paths:

  1. **BM25-only** (`bible.search`)
  2. **Semantic-only** (`bible.semantic`, requires on-disk index)
  3. **Hybrid** (`bible/hybrid.py`, BM25 + semantic fused)

For each path, computes:
  - **recall@10**      — fraction of expected verses appearing in top-10
  - **MRR**            — mean reciprocal rank of first primary (weight=3) hit
  - **primary-in-top-1** — fraction of queries where any weight=3 verse is rank 1
  - **ndcg@10**        — normalized DCG using graded relevance (1/2/3)

Outputs a markdown report to stdout. Pass `--csv path.csv` to also dump
per-query rows for downstream analysis.

Usage:

    # Default: runs against real BM25 + real local index, all three paths
    python scripts/run_eval.py

    # Limit to one path (faster iteration during model tuning)
    python scripts/run_eval.py --paths bm25
    python scripts/run_eval.py --paths bm25,hybrid

    # Adjust top-k
    python scripts/run_eval.py --top-k 5

    # Save per-query CSV
    python scripts/run_eval.py --csv /tmp/eval.csv

This script is the dev-facing tool. CI doesn't run it (it would need the
real local index); instead, `tests/run_all.py` has a small self-contained
test of the harness logic itself (`t_eval_harness_*`).
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from pathlib import Path

# Make repo importable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bible.search import get_bm25_index  # noqa: E402
from bible.semantic import (  # noqa: E402
    EMBEDDINGS_DIR,
    load_vector_index,
    search_semantic,
)
from bible.hybrid import hybrid_search, DEFAULT_BM25_WEIGHT, DEFAULT_SOLO_WEIGHT  # noqa: E402
from tests.benchmark import BENCHMARK  # noqa: E402


# Reasonable default — semantic path is the slowest
DEFAULT_TOP_K = 10
PATHS_ALL = ("bm25", "semantic", "hybrid")


def _dcg(relavances: list[int]) -> float:
    """Discounted Cumulative Gain. Standard log2(rank+1) discount."""
    return sum(rel / math.log2(rank + 2) for rank, rel in enumerate(relavances))


def _ndcg_at_k(expected: dict[str, int], got: list[str], k: int) -> float:
    """Normalized DCG@k using the expected relevance weights as ideal DCG."""
    if not expected:
        return 0.0
    got_top = got[:k]
    # Actual DCG: relevance of each retrieved verse (0 if not in expected)
    actual_rels = [expected.get(c, 0) for c in got_top]
    actual_dcg = _dcg(actual_rels)
    # Ideal DCG: top-k expected verses by weight
    ideal_rels = sorted(expected.values(), reverse=True)[:k]
    # Pad with 0s if fewer than k expected
    while len(ideal_rels) < k:
        ideal_rels.append(0)
    ideal_dcg = _dcg(ideal_rels)
    if ideal_dcg == 0.0:
        return 0.0
    return actual_dcg / ideal_dcg


def _metrics_for_query(
    expected: list[tuple[str, int]],
    retrieved: list[str],
    top_k: int,
) -> dict:
    """Compute per-query metrics."""
    expected_dict = {citation: weight for citation, weight in expected}
    primary_citations = [c for c, w in expected if w == 3]

    # recall@10: how many expected verses appear in top-k?
    got_set = set(retrieved[:top_k])
    expected_set = set(c for c, _ in expected)
    if expected_set:
        recall = len(got_set & expected_set) / len(expected_set)
    else:
        recall = 0.0

    # MRR: reciprocal rank of first primary (weight=3) hit
    rr = 0.0
    for rank, citation in enumerate(retrieved, start=1):
        if citation in primary_citations:
            rr = 1.0 / rank
            break

    # primary-in-top-1: any weight=3 in position 1?
    primary_in_top1 = bool(retrieved and retrieved[0] in primary_citations)

    # ndcg@10
    ndcg = _ndcg_at_k(expected_dict, retrieved, top_k)

    return {
        "recall_at_k": round(recall, 4),
        "mrr": round(rr, 4),
        "primary_in_top1": primary_in_top1,
        "ndcg_at_k": round(ndcg, 4),
        "got_count": len(retrieved[:top_k]),
        "expected_count": len(expected),
        "got_top5": retrieved[:5],
    }


def run_path(
    path: str,
    benchmark: list,
    top_k: int,
    bm25_weight: float,
    solo_weight: float,
) -> dict:
    """Run one retrieval path against the benchmark; return aggregate metrics."""
    per_query: list[dict] = []
    t_start = time.time()

    for query, expected in benchmark:
        if path == "bm25":
            idx = get_bm25_index("KJV")
            hits = idx.search(query, limit=top_k)
            retrieved = [h["reference"] for h in hits]
        elif path == "semantic":
            # search_semantic uses the on-disk index; if it doesn't exist,
            # skip the path (don't crash — the harness should be runnable
            # in degraded mode for BM25-only testing).
            if not (EMBEDDINGS_DIR / "default_meta.json").exists():
                print(f"  [skip semantic] no index at {EMBEDDINGS_DIR}", file=sys.stderr)
                return {"skipped": True, "reason": "no semantic index built"}
            hits = search_semantic(
                query, index_name="default", top_k=top_k,
                tradition=None, backend="local",
            )
            retrieved = [h["citation"] for h in hits]
        elif path == "hybrid":
            # Need both BM25 + semantic. If semantic missing, skip.
            if not (EMBEDDINGS_DIR / "default_meta.json").exists():
                return {"skipped": True, "reason": "no semantic index built"}
            bm25_idx = get_bm25_index("KJV")
            bm25_hits = bm25_idx.search(query, limit=top_k)
            bm25_dicts = [
                {"citation": h["reference"], "score": h["score"], "text": h["text"],
                 "translation": "KJV", "tradition": "christianity"}
                for h in bm25_hits
            ]
            sem_hits = search_semantic(
                query, index_name="default", top_k=top_k,
                tradition=None, backend="local",
            )
            fused = hybrid_search(
                query=query,
                bm25_results=bm25_dicts,
                semantic_results=sem_hits,
                bm25_weight=bm25_weight,
                solo_weight=solo_weight,
                top_k=top_k,
            )
            retrieved = [f["citation"] for f in fused]
        else:
            raise ValueError(f"unknown path: {path!r}")

        per_query.append({"query": query, "expected": expected, **_metrics_for_query(expected, retrieved, top_k)})

    elapsed = time.time() - t_start

    # Aggregate
    n = len(per_query)
    aggregate = {
        "n_queries": n,
        "mean_recall_at_k": round(sum(q["recall_at_k"] for q in per_query) / n, 4),
        "mrr": round(sum(q["mrr"] for q in per_query) / n, 4),
        "primary_in_top1_rate": round(sum(q["primary_in_top1"] for q in per_query) / n, 4),
        "mean_ndcg_at_k": round(sum(q["ndcg_at_k"] for q in per_query) / n, 4),
        "elapsed_seconds": round(elapsed, 2),
        "queries_per_second": round(n / elapsed, 2),
        "per_query": per_query,
    }
    return aggregate


def format_report(results: dict[str, dict], top_k: int) -> str:
    """Format the three-path results as a human-readable markdown report."""
    lines = [
        "# Bible LLM Reference — Retrieval Evaluation Report",
        "",
        f"**Top-k:** {top_k}",
        f"**Benchmark queries:** {sum(r['n_queries'] for r in results.values() if not r.get('skipped'))}",
        "",
        "## Summary",
        "",
        "| Path | Recall@K | MRR | Primary-in-top-1 | nDCG@K | Queries/s |",
        "|------|----------|-----|------------------|--------|-----------|",
    ]
    for path in PATHS_ALL:
        if path not in results:
            continue
        r = results[path]
        if r.get("skipped"):
            lines.append(f"| {path} | *skipped ({r.get('reason')})* | — | — | — | — |")
            continue
        lines.append(
            f"| {path} | {r['mean_recall_at_k']:.3f} | {r['mrr']:.3f} | "
            f"{r['primary_in_top1_rate']:.3f} | {r['mean_ndcg_at_k']:.3f} | "
            f"{r['queries_per_second']:.1f} |"
        )

    lines.extend(["", "## Per-path detail", ""])

    for path in PATHS_ALL:
        if path not in results:
            continue
        r = results[path]
        if r.get("skipped"):
            continue
        lines.append(f"### {path.upper()}")
        lines.append(f"_{r['n_queries']} queries in {r['elapsed_seconds']}s_")
        lines.append("")
        # Worst-performing queries for this path
        worst = sorted(r["per_query"], key=lambda q: (q["recall_at_k"], q["mrr"]))[:5]
        lines.append("**5 lowest-scoring queries:**")
        lines.append("")
        for q in worst:
            top5 = ", ".join(q["got_top5"][:3]) or "(empty)"
            lines.append(
                f"- `{q['query']}` → recall={q['recall_at_k']:.2f}, "
                f"mrr={q['mrr']:.2f}, ndcg={q['ndcg_at_k']:.2f}, top: {top5}"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the bible-llm-reference retrieval benchmark"
    )
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K,
                        help=f"Top-k results per query (default {DEFAULT_TOP_K})")
    parser.add_argument("--paths", default=",".join(PATHS_ALL),
                        help=f"Comma-separated paths to run (default {','.join(PATHS_ALL)})")
    parser.add_argument("--bm25-weight", type=float, default=DEFAULT_BM25_WEIGHT,
                        help=f"Hybrid BM25 weight (default {DEFAULT_BM25_WEIGHT})")
    parser.add_argument("--solo-weight", type=float, default=DEFAULT_SOLO_WEIGHT,
                        help=f"Hybrid solo weight (default {DEFAULT_SOLO_WEIGHT})")
    parser.add_argument("--csv", type=Path,
                        help="Optional CSV output path for per-query rows")
    parser.add_argument("--limit", type=int, default=0,
                        help="Optional: limit benchmark to first N queries (for quick iteration)")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    for p in paths:
        if p not in PATHS_ALL:
            print(f"ERROR: unknown path {p!r}; valid: {PATHS_ALL}", file=sys.stderr)
            return 1

    benchmark = BENCHMARK[:args.limit] if args.limit else BENCHMARK
    print(f"Running {len(benchmark)} queries × {len(paths)} path(s), top_k={args.top_k}...",
          file=sys.stderr)

    results: dict[str, dict] = {}
    for path in paths:
        print(f"\n[{path}] starting...", file=sys.stderr)
        results[path] = run_path(
            path=path,
            benchmark=benchmark,
            top_k=args.top_k,
            bm25_weight=args.bm25_weight,
            solo_weight=args.solo_weight,
        )
        if not results[path].get("skipped"):
            r = results[path]
            print(f"[{path}] recall@K={r['mean_recall_at_k']:.3f} "
                  f"mrr={r['mrr']:.3f} primary-in-top1={r['primary_in_top1_rate']:.3f} "
                  f"ndcg={r['mean_ndcg_at_k']:.3f} ({r['queries_per_second']:.1f} q/s)",
                  file=sys.stderr)

    # CSV output
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["path", "query", "recall_at_k", "mrr", "primary_in_top1",
                        "ndcg_at_k", "got_top5", "expected_count", "got_count"])
            for path, r in results.items():
                if r.get("skipped"):
                    continue
                for q in r["per_query"]:
                    w.writerow([
                        path, q["query"], q["recall_at_k"], q["mrr"],
                        int(q["primary_in_top1"]), q["ndcg_at_k"],
                        "|".join(q["got_top5"]), q["expected_count"], q["got_count"],
                    ])
        print(f"\nWrote per-query CSV to {args.csv}", file=sys.stderr)

    print(format_report(results, args.top_k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
