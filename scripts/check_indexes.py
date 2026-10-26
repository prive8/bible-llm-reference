#!/usr/bin/env python3
"""Check every vector index on disk for self-consistency.

Why this exists
---------------
The 2026-09-19 `text-embedding-3-large` index held 30,159 of 66,689
vectors, and because the corpus is collected Christianity-first, the
surviving vectors were Christianity-only. It scored 0.344 on the
cross-tradition v2 benchmark -- the best-looking number in the
embedder comparison -- while being unable to retrieve a single Quran
or Tanakh passage. It went unnoticed because:

  - the metadata claimed the full corpus, so nothing looked wrong;
  - the loader degraded silently on a short read;
  - and `data/embeddings/*` is **gitignored**, so CI never saw the
    broken file at all. A CI-only check could not have caught it.

So this check is deliberately runnable **on a developer host**, where
the real indexes live, as well as in CI.

Usage
-----
    python scripts/check_indexes.py            # check all indexes
    python scripts/check_indexes.py --name default
    python scripts/check_indexes.py --quiet    # only report failures

Exit code 0 if every index is self-consistent, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EMBEDDINGS_DIR = REPO_ROOT / "data" / "embeddings"


def check_index(meta_path: Path) -> tuple[bool, str, str]:
    """Check one index. Returns (ok, name, message)."""
    name = meta_path.name[: -len("_meta.json")]
    bin_path = meta_path.with_name(f"{name}_vectors.bin")

    if not bin_path.exists():
        return False, name, "has metadata but no .bin file"

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, name, f"metadata is unreadable: {e}"

    count = meta.get("count", 0)
    dim = meta.get("dim", 0)
    entries = meta.get("entries", [])

    if count <= 0 or dim <= 0:
        return False, name, f"metadata has count={count} dim={dim}"

    if len(entries) != count:
        return False, name, (
            f"metadata is internally inconsistent: count={count} but "
            f"{len(entries)} entries"
        )

    expected_bytes = count * dim * 4
    actual_bytes = bin_path.stat().st_size
    if actual_bytes != expected_bytes:
        present = actual_bytes // (dim * 4) if dim else 0
        return False, name, (
            f"is truncated - {actual_bytes} bytes, expected {expected_bytes} "
            f"({count} x {dim} float32). Only {present:,} of {count:,} vectors "
            f"are present. Scores computed against it are NOT comparable to "
            f"a full-corpus index."
        )

    return True, name, f"{count:,} x {dim}, {actual_bytes:,} bytes"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=None,
                        help="check only this index (default: all)")
    parser.add_argument("--dir", default=str(EMBEDDINGS_DIR),
                        help="embeddings directory to scan")
    parser.add_argument("--quiet", action="store_true",
                        help="only print failures")
    args = parser.parse_args()

    emb = Path(args.dir)
    if not emb.exists():
        print(f"::error::embeddings directory not found: {emb}")
        return 1

    if args.name:
        meta_paths = [emb / f"{args.name}_meta.json"]
        if not meta_paths[0].exists():
            print(f"::error::no index named '{args.name}' in {emb}")
            return 1
    else:
        meta_paths = sorted(emb.glob("*_meta.json"))

    if not meta_paths:
        if not args.quiet:
            print(f"no indexes found in {emb}")
        return 0

    failures = 0
    for meta_path in meta_paths:
        ok, name, message = check_index(meta_path)
        if ok:
            if not args.quiet:
                print(f"  ok: {name} - {message}")
        else:
            failures += 1
            print(f"::error::index '{name}' {message}")

    if failures:
        print(f"::error::{failures} of {len(meta_paths)} index(es) failed "
              f"the integrity check")
        return 1

    if not args.quiet:
        print(f"all {len(meta_paths)} index(es) passed the integrity check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
