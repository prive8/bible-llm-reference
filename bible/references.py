"""Cross-reference engine for the bible package.

Backed by the openbible.info cross-references dataset (CC-BY 4.0) — see
``data/references/README.md`` for license details. The dataset has 605K+
edges across 29K+ source verses and was ingested by
``scripts/ingest_cross_references.py`` into
``data/references/cross_references.json``.

The lookup surface:

  - ``load_xrefs()`` — returns the parsed JSON (cached).
  - ``get_references(ref, min_votes=3, limit=100)`` — outgoing edges
    (verses that the source points to).
  - ``get_reciprocal(ref, min_votes=3, limit=100)`` — incoming edges
    (verses that point AT the source). Built once on first call.
  - ``traverse(ref, hops=2, min_votes=3)`` — multi-hop expansion; returns
    a dict keyed by hop distance.

All public functions take a verse reference in the same form
``bible.lookup.parse_ref()`` returns: ``"Genesis 1:1"`` (canonical book name +
chapter + verse). Use ``parse_ref()`` to convert user input.

CLI: ``python -m bible references "John 3:16" [--hops N] [--min-votes V]``.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

from bible.lookup import parse_ref

REPO_ROOT = Path(__file__).resolve().parent.parent
XREFS_JSON = REPO_ROOT / "data" / "references" / "cross_references.json"

# Votes >= this threshold get into the default "primary" list for a verse.
# Below this they're still in the data but flagged as low-confidence.
DEFAULT_MIN_VOTES = 3


# ---------------------------------------------------------------------------
# Data load
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_xrefs() -> dict:
    """Load and cache the parsed cross-references JSON.

    Returns the top-level dict: ``{"metadata": {...}, "outgoing": {...}}``.
    """
    with open(XREFS_JSON, encoding="utf-8") as f:
        return json.load(f)


def metadata() -> dict:
    """Return just the metadata block (no edges)."""
    return load_xrefs().get("metadata", {})


# ---------------------------------------------------------------------------
# Reference normalization
# ---------------------------------------------------------------------------

def _ref_to_lookup_key(ref: str) -> Optional[str]:
    """Normalize a user ref string to the ``"{Book} {C}:{V}"`` key used in the JSON.

    Accepts anything ``parse_ref()`` accepts. Returns None if unparseable.
    """
    parsed = parse_ref(ref)
    if parsed is None:
        return None
    book, chapter, vs, ve = parsed
    if vs is None:
        # Whole-chapter reference → only return verses that exist.
        # Caller should use ``get_references`` per-verse in that case.
        return None
    return f"{book} {chapter}:{vs}"


# ---------------------------------------------------------------------------
# Outgoing / reciprocal lookups
# ---------------------------------------------------------------------------

def get_references(
    ref: str,
    min_votes: int = DEFAULT_MIN_VOTES,
    limit: int = 100,
) -> list[dict]:
    """Return outgoing cross-references from ``ref``.

    Each result: ``{"to": "<ref>", "votes": int}``. Sorted by votes desc.
    Empty list if ref is unparseable or has no outgoing edges.
    """
    key = _ref_to_lookup_key(ref)
    if key is None:
        return []
    edges = load_xrefs().get("outgoing", {}).get(key, [])
    # Filter and sort
    filtered = [e for e in edges if e.get("votes", 0) >= min_votes]
    filtered.sort(key=lambda e: -e.get("votes", 0))
    return filtered[:limit]


def _build_reciprocal_index() -> dict[str, list[dict]]:
    """Build inverted index: target_ref -> [{"from": ..., "votes": ...}, ...]."""
    inv: dict[str, list[dict]] = defaultdict(list)
    for src_ref, edges in load_xrefs().get("outgoing", {}).items():
        for e in edges:
            inv[e["to"]].append({"from": src_ref, "votes": e["votes"]})
    return dict(inv)


@lru_cache(maxsize=1)
def _reciprocal_index() -> dict[str, list[dict]]:
    return _build_reciprocal_index()


def get_reciprocal(
    ref: str,
    min_votes: int = DEFAULT_MIN_VOTES,
    limit: int = 100,
) -> list[dict]:
    """Return incoming cross-references — verses that point AT ``ref``.

    Each result: ``{"from": "<ref>", "votes": int}``. Sorted by votes desc.
    """
    key = _ref_to_lookup_key(ref)
    if key is None:
        return []
    edges = _reciprocal_index().get(key, [])
    filtered = [e for e in edges if e.get("votes", 0) >= min_votes]
    filtered.sort(key=lambda e: -e.get("votes", 0))
    return filtered[:limit]


# ---------------------------------------------------------------------------
# Multi-hop traversal
# ---------------------------------------------------------------------------

def traverse(
    ref: str,
    hops: int = 2,
    min_votes: int = DEFAULT_MIN_VOTES,
    per_hop_limit: int = 50,
) -> dict[int, list[dict]]:
    """Expand ``ref`` outward by ``hops`` edges in the cross-reference graph.

    Returns ``{1: [...], 2: [...], ...}`` where each list is the outgoing
    edges discovered at that distance, sorted by votes desc. Visited verses
    are tracked so cycles don't loop forever; the same verse can appear at
    multiple hops but only its shortest-distance edges are kept.

    Hops is clamped to [1, 3]. Beyond 3 hops the result set explodes and
    becomes noise rather than signal — that belongs in a graph DB, not in
    this stdlib loader.
    """
    if hops < 1:
        return {}
    hops = min(hops, 3)

    seed = _ref_to_lookup_key(ref)
    if seed is None:
        return {}

    results: dict[int, list[dict]] = {h: [] for h in range(1, hops + 1)}
    visited: set[str] = {seed}
    frontier: list[tuple[str, int]] = [(seed, 1)]
    outgoing = load_xrefs().get("outgoing", {})

    while frontier:
        next_frontier: list[tuple[str, int]] = []
        for src, current_hop in frontier:
            if current_hop > hops:
                continue
            edges = [
                e for e in outgoing.get(src, [])
                if e.get("votes", 0) >= min_votes
            ]
            edges.sort(key=lambda e: -e.get("votes", 0))
            edges = edges[:per_hop_limit]
            for e in edges:
                tgt = e["to"]
                results[current_hop].append({
                    "from": src,
                    "to": tgt,
                    "votes": e["votes"],
                })
                if tgt not in visited and current_hop < hops:
                    visited.add(tgt)
                    next_frontier.append((tgt, current_hop + 1))
        frontier = next_frontier

    # Final per-hop sort (frontier ordering already did this, but be safe)
    for h, items in results.items():
        items.sort(key=lambda e: -e["votes"])
    return results


# ---------------------------------------------------------------------------
# High-level runner & CLI formatting
# ---------------------------------------------------------------------------

def run_references(
    ref: str,
    hops: int = 1,
    min_votes: int = DEFAULT_MIN_VOTES,
    direction: str = "out",
    as_json: bool = False,
) -> dict:
    """Look up cross-references and print (or return) a structured result.

    ``direction`` is one of ``"out"`` (outgoing only), ``"in"`` (reciprocal
    only), or ``"both"``. ``hops`` is the multi-hop expansion depth when
    ``direction == "out"``; it's ignored for ``"in"``.

    Returns the dict structure that gets printed in JSON mode (or that
    callers can post-process).
    """
    parsed = parse_ref(ref)
    if parsed is None:
        print(f"Could not parse reference: {ref!r}", file=sys.stderr)
        print("Examples: 'Genesis 1:1', 'John 3:16', 'Psalm 23:1-6'", file=sys.stderr)
        sys.exit(1)

    book, chapter, vs, ve = parsed
    ref_str = f"{book} {chapter}:{vs}" + (
        f"-{ve}" if ve and ve != vs else ""
    )

    out: dict = {
        "reference": ref_str,
        "min_votes": min_votes,
        "direction": direction,
        "hops": hops if direction == "out" else 1,
        "outgoing": [],
        "incoming": [],
        "hops_expanded": {},
    }

    if direction in ("out", "both"):
        if hops == 1:
            out["outgoing"] = get_references(ref_str, min_votes=min_votes)
        else:
            out["hops_expanded"] = traverse(ref_str, hops=hops, min_votes=min_votes)

    if direction in ("in", "both"):
        out["incoming"] = get_reciprocal(ref_str, min_votes=min_votes)

    if as_json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return out

    # Human-readable output
    print(f"\n{'='*70}")
    print(f"  Cross-references for {ref_str}")
    print(f"  (min votes: {min_votes}, direction: {direction})")
    print(f"{'='*70}\n")

    if out["outgoing"]:
        print(f"  Outgoing ({len(out['outgoing'])}):")
        for e in out["outgoing"][:30]:
            print(f"    [{e['votes']:>3}] → {e['to']}")
        if len(out["outgoing"]) > 30:
            print(f"    ... (+{len(out['outgoing']) - 30} more)")
        print()

    if out["hops_expanded"]:
        for hop_n in sorted(out["hops_expanded"].keys()):
            items = out["hops_expanded"][hop_n]
            print(f"  Hop {hop_n} ({len(items)}):")
            for e in items[:30]:
                print(f"    [{e['votes']:>3}] {e['from']} → {e['to']}")
            if len(items) > 30:
                print(f"    ... (+{len(items) - 30} more)")
            print()

    if out["incoming"]:
        print(f"  Incoming / Reciprocal ({len(out['incoming'])}):")
        for e in out["incoming"][:30]:
            print(f"    [{e['votes']:>3}] ← {e['from']}")
        if len(out["incoming"]) > 30:
            print(f"    ... (+{len(out['incoming']) - 30} more)")
        print()

    if not any([out["outgoing"], out["incoming"], out["hops_expanded"]]):
        print(f"  No cross-references found at min_votes={min_votes}.")
        print(f"  Try lowering --min-votes (default {DEFAULT_MIN_VOTES}).\n")

    print(f"{'='*70}")
    print("NOTE: Cross-references are crowd-sourced from openbible.info")
    print("      (CC-BY 4.0). They are interpretive, not authoritative.")
    print(f"{'='*70}")
    return out


def main():
    """CLI entry point for ``python -m bible references``."""
    import argparse

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        prog="bible references",
        description="Look up cross-references for a Bible verse.",
    )
    parser.add_argument("reference", help="Bible reference (e.g. 'Genesis 1:1')")
    parser.add_argument(
        "--hops", type=int, default=1,
        help="Multi-hop expansion depth for outgoing refs (1-3, default 1)",
    )
    parser.add_argument(
        "--min-votes", type=int, default=DEFAULT_MIN_VOTES,
        help=f"Minimum openbible votes to include (default {DEFAULT_MIN_VOTES})",
    )
    parser.add_argument(
        "--direction", choices=["out", "in", "both"], default="out",
        help="out=outgoing only, in=incoming only, both=both (default out)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output structured JSON",
    )

    args = parser.parse_args()
    run_references(
        args.reference,
        hops=args.hops,
        min_votes=args.min_votes,
        direction=args.direction,
        as_json=args.json,
    )


if __name__ == "__main__":
    main()
