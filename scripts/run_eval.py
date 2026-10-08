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
from bible.registry import TraditionRegistry  # noqa: E402
from tests.benchmark import BENCHMARK  # noqa: E402
from tests.benchmark_v2 import BENCHMARK_V2  # noqa: E402


# Reasonable default — semantic path is the slowest
DEFAULT_TOP_K = 10
PATHS_ALL = ("bm25", "semantic", "hybrid")

_REGISTRY_CACHE: list[TraditionRegistry] = []


def _get_registry() -> TraditionRegistry:
    if not _REGISTRY_CACHE:
        _REGISTRY_CACHE.append(TraditionRegistry())
    return _REGISTRY_CACHE[0]


def citation_matches(
    retrieved: str,
    expected: str,
    registry: Optional[TraditionRegistry] = None,
) -> bool:
    """Check if a retrieved citation satisfies an expected citation.

    Handles:
      - Exact string matches (case-insensitive)
      - Verse ranges (e.g. expected '2 Corinthians 1:3-4', retrieved '2 Corinthians 1:3')
      - Passage chunks (e.g. expected 'Matthew 5:4', retrieved 'Matthew 5:3-5')
      - Canonical ID formats (e.g. 'bible:Matthew.5.4', 'quran:2.255')
      - Aliased book names (e.g. 'Psalms' vs 'Psalm')
      - Cross-tradition versification alignments where applicable
    """
    ret_clean = retrieved.strip()
    exp_clean = expected.strip()
    if ret_clean.lower() == exp_clean.lower():
        return True

    reg = registry or _get_registry()
    p_ret = reg.parse_reference(ret_clean)
    p_exp = reg.parse_reference(exp_clean)

    if not p_ret or not p_exp:
        return False

    # Quran citations
    if p_ret.get("tradition") == "islam" and p_exp.get("tradition") == "islam":
        if p_ret.get("surah") == p_exp.get("surah"):
            r_s = p_ret.get("ayah_start", 0)
            r_e = p_ret.get("ayah_end", r_s)
            e_s = p_exp.get("ayah_start", 0)
            e_e = p_exp.get("ayah_end", e_s)
            return max(r_s, e_s) <= min(r_e, e_e)
        return False

    # Bible / Tanakh citations
    if p_ret.get("tradition") in ("christianity", "judaism") and p_exp.get("tradition") in ("christianity", "judaism"):
        b_ret = p_ret.get("book") or ""
        b_exp = p_exp.get("book") or ""
        b_ret_norm = reg._book_mappings.get(b_ret, b_ret)
        b_exp_norm = reg._book_mappings.get(b_exp, b_exp)

        ch_ret = p_ret.get("chapter")
        ch_exp = p_exp.get("chapter")

        r_s = p_ret.get("verse_start", 0)
        r_e = p_ret.get("verse_end", r_s)
        e_s = p_exp.get("verse_start", 0)
        e_e = p_exp.get("verse_end", e_s)

        if b_ret_norm.lower() == b_exp_norm.lower() and ch_ret == ch_exp:
            return max(r_s, e_s) <= min(r_e, e_e)

        # Cross-tradition versification alignment check
        can_ret = p_ret.get("canonical_id")
        can_exp = p_exp.get("canonical_id")
        if can_ret and can_exp:
            aligned_ret = reg.align_canonical_id(can_ret, p_exp.get("tradition", ""))
            if aligned_ret == can_exp:
                return True
            aligned_exp = reg.align_canonical_id(can_exp, p_ret.get("tradition", ""))
            if aligned_exp == can_ret:
                return True

    return False


def _score_retrieved_verse(
    ret_cite: str,
    expected: list[tuple[str, int]],
    registry: Optional[TraditionRegistry] = None,
) -> int:
    """Return highest relevance weight among matching expected citations, or 0."""
    max_rel = 0
    for exp_cite, weight in expected:
        if citation_matches(ret_cite, exp_cite, registry):
            if weight > max_rel:
                max_rel = weight
    return max_rel


def _dcg(relavances: list[int]) -> float:
    """Discounted Cumulative Gain. Standard log2(rank+1) discount."""
    return sum(rel / math.log2(rank + 2) for rank, rel in enumerate(relavances))


def _ndcg_at_k(
    expected: Union[dict[str, int], list[tuple[str, int]]],
    got: list[str],
    k: int,
    registry: Optional[TraditionRegistry] = None,
) -> float:
    """Normalized DCG@k using the expected relevance weights as ideal DCG."""
    if not expected:
        return 0.0
    got_top = got[:k]
    if isinstance(expected, dict):
        actual_rels = [expected.get(c, 0) for c in got_top]
        ideal_rels = sorted(expected.values(), reverse=True)[:k]
    else:
        actual_rels = [_score_retrieved_verse(c, expected, registry) for c in got_top]
        ideal_rels = sorted([w for _, w in expected], reverse=True)[:k]

    actual_dcg = _dcg(actual_rels)
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
    registry: Optional[TraditionRegistry] = None,
) -> dict:
    """Compute per-query metrics with range and passage match support."""
    reg = registry or _get_registry()

    # recall@k: fraction of expected citations matched by top-k
    matched_expected_indices = set()
    for idx, (exp_cite, _) in enumerate(expected):
        for ret_cite in retrieved[:top_k]:
            if citation_matches(ret_cite, exp_cite, reg):
                matched_expected_indices.add(idx)
                break
    recall = len(matched_expected_indices) / len(expected) if expected else 0.0

    # MRR: reciprocal rank of first primary (weight=3) hit
    rr = 0.0
    for rank, citation in enumerate(retrieved, start=1):
        if _score_retrieved_verse(citation, expected, reg) == 3:
            rr = 1.0 / rank
            break

    # primary-in-top-1: any weight=3 in position 1?
    primary_in_top1 = bool(retrieved and _score_retrieved_verse(retrieved[0], expected, reg) == 3)

    # ndcg@k
    ndcg = _ndcg_at_k(expected, retrieved, top_k, registry=reg)

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
    index_name: str = "default",
    backend: str = "local",
    tradition: Optional[str] = None,
) -> dict:
    """Run one retrieval path against the benchmark; return aggregate metrics."""
    per_query: list[dict] = []
    t_start = time.time()
    reg = _get_registry()

    for query, persona, expected in benchmark:
        if path == "bm25":
            idx = get_bm25_index("KJV", tradition=tradition)
            hits = idx.search(query, limit=top_k)
            retrieved = [h["reference"] for h in hits]
        elif path == "semantic":
            # search_semantic uses the on-disk index; if it doesn't exist,
            # skip the path (don't crash — the harness should be runnable
            # in degraded mode for BM25-only testing).
            if not (EMBEDDINGS_DIR / f"{index_name}_meta.json").exists():
                print(f"  [skip semantic] no index '{index_name}' at {EMBEDDINGS_DIR}", file=sys.stderr)
                return {"skipped": True, "reason": f"no semantic index '{index_name}' built"}
            hits = search_semantic(
                query, index_name=index_name, top_k=top_k,
                tradition=tradition, backend=backend,
            )
            retrieved = [h["citation"] for h in hits]
        elif path == "hybrid":
            # Need both BM25 + semantic. If semantic missing, skip.
            if not (EMBEDDINGS_DIR / f"{index_name}_meta.json").exists():
                return {"skipped": True, "reason": f"no semantic index '{index_name}' built"}
            bm25_idx = get_bm25_index("KJV", tradition=tradition)
            bm25_hits = bm25_idx.search(query, limit=top_k)
            bm25_dicts = [
                {"citation": h["reference"], "score": h["score"], "text": h["text"],
                 "translation": h.get("translation", "KJV"), "tradition": tradition or "christianity"}
                for h in bm25_hits
            ]
            sem_hits = search_semantic(
                query, index_name=index_name, top_k=top_k,
                tradition=tradition, backend=backend,
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

        per_query.append({
            "query": query,
            "persona": persona,
            "expected": expected,
            **_metrics_for_query(expected, retrieved, top_k, registry=reg),
        })

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
    # Per-persona aggregation. The persona field on each benchmark
    # entry comes from tests/benchmark.py or benchmark_v2.py.
    per_persona: dict[str, list[dict]] = {}
    for q in per_query:
        per_persona.setdefault(q["persona"], []).append(q)
    persona_summaries: dict[str, dict] = {}
    for persona, qs in per_persona.items():
        m = len(qs)
        persona_summaries[persona] = {
            "n_queries": m,
            "mean_recall_at_k": round(sum(q["recall_at_k"] for q in qs) / m, 4),
            "mrr": round(sum(q["mrr"] for q in qs) / m, 4),
            "primary_in_top1_rate": round(sum(q["primary_in_top1"] for q in qs) / m, 4),
            "mean_ndcg_at_k": round(sum(q["ndcg_at_k"] for q in qs) / m, 4),
        }
    aggregate["per_persona"] = persona_summaries
    return aggregate


def format_report(results: dict[str, dict], top_k: int, benchmark_info: str = "v1") -> str:
    """Format the three-path results as a human-readable markdown report."""
    lines = [
        "# Bible LLM Reference — Retrieval Evaluation Report",
        "",
        f"**Benchmark:** {benchmark_info}",
        f"**Top-k:** {top_k}",
        f"**Benchmark queries evaluated:** {sum(r['n_queries'] for r in results.values() if not r.get('skipped'))}",
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

    any_per_persona = any(r.get("per_persona") for r in results.values() if not r.get("skipped"))
    if any_per_persona:
        first_r = next(r for r in results.values() if not r.get("skipped"))
        persona_counts = {p: s["n_queries"] for p, s in first_r["per_persona"].items()}
        total = sum(persona_counts.values())
        lines.extend(["", "## Per-persona detail", ""])
        lines.append(
            f"Benchmark covers {len(persona_counts)} personas across "
            f"{total} queries (Sarah / Marcus / Yuki / Priya / Aisha / Jordan "
            f"per `docs/audience_expectations.md`):"
        )
        lines.append("")
        for p in ["sarah", "marcus", "yuki", "priya", "aisha", "jordan"]:
            if p in persona_counts:
                lines.append(f"- `{p}`: {persona_counts[p]} queries")
        lines.append("")
        lines.append(
            "_Per-persona slices reveal where the retrieval system serves each user type._"
        )
        lines.append("")
        lines.append("| Path | Persona | n | Recall@K | MRR | Primary@1 | nDCG@K |")
        lines.append("|------|---------|---|----------|-----|-----------|---------|")
        for path in PATHS_ALL:
            if path not in results or results[path].get("skipped"):
                continue
            r = results[path]
            for persona in ["sarah", "marcus", "yuki", "priya", "aisha", "jordan"]:
                if persona not in r["per_persona"]:
                    continue
                s = r["per_persona"][persona]
                lines.append(
                    f"| {path} | {persona} | {s['n_queries']} | "
                    f"{s['mean_recall_at_k']:.3f} | {s['mrr']:.3f} | "
                    f"{s['primary_in_top1_rate']:.3f} | {s['mean_ndcg_at_k']:.3f} |"
                )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the bible-llm-reference retrieval benchmark"
    )
    parser.add_argument("--benchmark", choices=["v1", "v2"], default="v1",
                        help="Benchmark version to run: 'v1' (30 queries) or 'v2' (90 queries, multi-tradition, dev/held-out)")
    parser.add_argument("--split", choices=["all", "dev", "held_out"], default="all",
                        help="Split filter for benchmark v2: 'all' (90 queries), 'dev' (48 queries), or 'held_out' (42 queries)")
    parser.add_argument("--tradition", choices=["all", "christianity", "islam", "judaism"], default=None,
                        help="Tradition filter for retrieval (default: 'all' for benchmark v2, None/KJV for v1)")
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
    parser.add_argument("--index", default="default",
                        help="Vector index name for semantic/hybrid paths (default 'default')")
    parser.add_argument("--backend", default="local",
                        choices=["local", "openrouter", "nim", "mock", "auto"],
                        help="Embedder backend for query encoding (default 'local'; use "
                             "'openrouter' if the named --index was built with the OpenRouter "
                             "embedder — dimensions must match)")
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

    if args.benchmark == "v2":
        raw = BENCHMARK_V2
        if args.split != "all":
            raw = [item for item in raw if item[2] == args.split]
        benchmark_items = [(item[0], item[1], item[3]) for item in raw]
        trad = args.tradition or "all"
        bench_info = f"v2 ({args.split} split, {len(benchmark_items)} queries)"
    else:
        benchmark_items = BENCHMARK
        trad = args.tradition
        bench_info = f"v1 ({len(benchmark_items)} queries)"

    benchmark = benchmark_items[:args.limit] if args.limit else benchmark_items
    print(f"Running {len(benchmark)} queries ({bench_info}) × {len(paths)} path(s), top_k={args.top_k}...",
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
            index_name=args.index,
            backend=args.backend,
            tradition=trad,
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
            w.writerow(["path", "persona", "query", "recall_at_k", "mrr",
                        "primary_in_top1", "ndcg_at_k", "got_top5",
                        "expected_count", "got_count"])
            for path, r in results.items():
                if r.get("skipped"):
                    continue
                for q in r["per_query"]:
                    w.writerow([
                        path, q["persona"], q["query"], q["recall_at_k"], q["mrr"],
                        int(q["primary_in_top1"]), q["ndcg_at_k"],
                        "|".join(q["got_top5"]), q["expected_count"], q["got_count"],
                    ])
        print(f"\nWrote per-query CSV to {args.csv}", file=sys.stderr)

    print(format_report(results, args.top_k, benchmark_info=bench_info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
