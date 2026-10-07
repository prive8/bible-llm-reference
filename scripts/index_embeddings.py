#!/usr/bin/env python3
"""Offline embedding generation script for Milestone 3B semantic search.

Embeds Christian Bible and Quran corpora into a compact, precomputed binary float32
vector index + metadata JSON for sub-millisecond local cosine similarity retrieval.

Usage:
    # Generate mock deterministic index (stdlib-only, instant, 0 dependencies)
    python scripts/index_embeddings.py --backend mock

    # Generate neural embeddings (when sentence-transformers is installed in Hermes)
    python scripts/index_embeddings.py --backend local --model all-MiniLM-L6-v2

    # Fast trial run on first 500 verses
    python scripts/index_embeddings.py --limit 500
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bible.lookup import load_kjv, strip_strongs_tags
from bible.quran import list_quran_translations, load_quran_edition
from bible.semantic import (
    EMBEDDINGS_DIR,
    get_embedder,
    l2_normalize,
    save_vector_index,
)
try:
    from bible.torah import load_torah_edition, _group_verses_by_chapter
    _has_torah = True
except ImportError:
    _has_torah = False
try:
    from bible.tanakh import BOOKS_BY_SECTION, BOOK_BY_NAME as TANAKH_BOOK_BY_NAME, list_tanakh_translations, load_tanakh_edition, _group_verses_by_chapter as _group_tanakh_verses
    _has_tanakh = True
except ImportError:
    _has_tanakh = False

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def collect_corpus(include_bible: bool = True, include_quran: bool = True, limit: int = 0) -> list[dict]:
    """Gather flat list of scripture passages across traditions."""
    entries: list[dict] = []
    curr_id = 0

    if include_bible:
        print("  Collecting Christian Bible (KJV)...")
        kjv = load_kjv()
        for book in kjv.get("books", []):
            book_name = book["name"]
            for ch in book.get("chapters", []):
                ch_num = ch["chapter"]
                for v in ch.get("verses", []):
                    v_num = v["verse"]
                    text = strip_strongs_tags(v["text"])
                    entries.append({
                        "id": curr_id,
                        "tradition": "christianity",
                        "translation": "KJV",
                        "citation": f"{book_name} {ch_num}:{v_num}",
                        "text": text,
                    })
                    curr_id += 1
                    if limit and curr_id >= limit:
                        return entries

    if include_quran:
        print("  Collecting Quran (Saheeh International)...")
        try:
            quran = load_quran_edition("saheeh-international")
            for div in quran.get("divisions", []):
                s_id = div["id"]
                s_name = div["name"]
                for ayah in div.get("ayahs", []):
                    a_num = ayah["ayah"]
                    text = ayah["text"]
                    entries.append({
                        "id": curr_id,
                        "tradition": "islam",
                        "translation": "Saheeh International",
                        "citation": f"Quran {s_id}:{a_num} ({s_name})",
                        "text": text,
                    })
                    curr_id += 1
                    if limit and curr_id >= limit:
                        return entries
        except FileNotFoundError:
            print("  Warning: data/quran/saheeh-international.json not found, skipping Quran.")

    # Torah (Phase 3.2) — use the Hebrew nikkud edition as the index source
    # since it's structurally clean (no English translation in same file).
    # If you want English-text indexing, also iterate hebrew-nikkud.json and
    # swap text for jps1917-modernized.json.
    if _has_torah:
        torah_tried = False
        for torah_key in ("hebrew-nikkud", "jps1917-modernized"):
            try:
                torah = load_torah_edition(torah_key)
                for div in torah.get("divisions", []):
                    book_name = div["name"]
                    # Re-group verses by chapter boundary detection
                    grouped = _group_verses_by_chapter(div)
                    for ch_num in sorted(grouped.keys()):
                        for v in grouped[ch_num]:
                            entries.append({
                                "id": curr_id,
                                "tradition": "judaism",
                                "translation": torah.get("translation", torah_key),
                                "citation": f"{book_name} {ch_num}:{v['verse']}",
                                "text": v["text"],
                            })
                            curr_id += 1
                            if limit and curr_id >= limit:
                                return entries
                torah_tried = True
                print(f"  Collected Torah ({torah_key})...")
                break  # use first available edition
            except FileNotFoundError:
                continue
        if not torah_tried:
            print("  Warning: no Torah data files found, skipping Judaism (Pentateuch).")

    # Tanakh (Phase 3.3) — Nevi'im + Ketuvim (Pentateuch already covered above).
    # Uses the same Sefaria editions as Torah for internal consistency.
    if _has_tanakh:
        tanakh_tried = False
        for tanakh_key in ("hebrew-nikkud", "jps1917-modernized"):
            try:
                tanakh = load_tanakh_edition(tanakh_key)
                # Only ingest Nevi'im + Ketuvim here; Torah was ingested above.
                neviim_ketuvim_books = (
                    BOOKS_BY_SECTION["Nevi'im"] + BOOKS_BY_SECTION["Ketuvim"]
                )
                for div in tanakh.get("divisions", []):
                    if div["name"] not in neviim_ketuvim_books:
                        continue  # skip Torah books here
                    book_name = div["name"]
                    grouped = _group_tanakh_verses(div)
                    for ch_num in sorted(grouped.keys()):
                        for v in grouped[ch_num]:
                            entries.append({
                                "id": curr_id,
                                "tradition": "judaism",
                                "translation": tanakh.get("translation", tanakh_key),
                                "citation": f"{book_name} {ch_num}:{v['verse']}",
                                "text": v["text"],
                            })
                            curr_id += 1
                            if limit and curr_id >= limit:
                                return entries
                tanakh_tried = True
                print(f"  Collected Tanakh Nevi'im + Ketuvim ({tanakh_key})...")
                break
            except FileNotFoundError:
                continue
        if not tanakh_tried:
            print("  Warning: no Tanakh data files found, skipping Judaism (Nevi'im + Ketuvim).")

    return entries


def main():
    parser = argparse.ArgumentParser(description="Generate offline vector index for semantic search (Milestone 3B)")
    parser.add_argument("--name", default="default", help="Output index name (default: 'default')")
    parser.add_argument("--backend", choices=["auto", "local", "mock", "nim", "openrouter"], default="auto",
                        help="Embedder backend to use (default: 'auto')")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size for embedding (default: 64)")
    parser.add_argument("--limit", type=int, default=0, help="Optional max verses to index (for quick testing)")
    parser.add_argument("--no-bible", action="store_true", help="Exclude Bible from index")
    parser.add_argument("--no-quran", action="store_true", help="Exclude Quran from index")
    parser.add_argument("--no-torah", action="store_true", help="Exclude Torah from index")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from an existing partial index. Skips already-embedded corpus entries. "
                             "The last batch is assumed complete; if a partial batch was in flight, those "
                             "passages are lost.")
    parser.add_argument("--overwrite", action="store_true",
                        help="Delete any existing index with this name before building.")

    args = parser.parse_args()

    print(f"Initializing embedder (backend: {args.backend})...")
    embedder = get_embedder(args.backend)

    print("Collecting scripture corpus...")
    corpus = collect_corpus(
        include_bible=not args.no_bible,
        include_quran=not args.no_quran,
        limit=args.limit,
    )
    print(f"Total passages collected: {len(corpus):,}")

    if not corpus:
        print("No passages to index. Exiting.")
        sys.exit(1)

    # Handle existing partial index
    meta_path = EMBEDDINGS_DIR / f"{args.name}_meta.json"
    bin_path = EMBEDDINGS_DIR / f"{args.name}_vectors.bin"
    existing_partial = meta_path.exists() and bin_path.exists()

    if existing_partial:
        if args.overwrite:
            print(f"  --overwrite: removing existing partial index at {EMBEDDINGS_DIR}/{args.name}_*")
            meta_path.unlink()
            bin_path.unlink()
            existing_partial = False
        elif not args.resume:
            print(f"ERROR: partial index exists at {EMBEDDINGS_DIR}/{args.name}_*",
                  file=sys.stderr)
            print("  Pass --resume to continue from where it left off, or --overwrite to start fresh.",
                  file=sys.stderr)
            sys.exit(1)

    # Detect resume state
    start_index = 0
    if existing_partial and args.resume:
        with open(meta_path, "r", encoding="utf-8") as f:
            existing_meta = json.load(f)
        existing_count = existing_meta.get("count", 0)
        existing_max_id = max(
            (e.get("id", -1) for e in existing_meta.get("entries", [])),
            default=-1,
        )
        # The corpus is built sequentially with id 0, 1, 2, ...; we
        # can skip the first `existing_max_id + 1` corpus entries.
        start_index = existing_max_id + 1
        print(f"  --resume: existing partial index has {existing_count} vectors "
              f"(max id {existing_max_id}); resuming from corpus index {start_index}.")
        if start_index >= len(corpus):
            print("  Resume index is past end of corpus; nothing to do.")
            return

    print(f"Generating vectors in batches of {args.batch_size} "
          f"({len(corpus) - start_index:,} to embed)...")
    start_time = time.time()

    # The texts we still need to embed (resume-aware)
    pending_corpus = corpus[start_index:]
    pending_texts = [e["text"] for e in pending_corpus]

    for i in range(0, len(pending_texts), args.batch_size):
        batch = pending_texts[i:i + args.batch_size]
        batch_meta = pending_corpus[i:i + args.batch_size]
        batch_vecs = embedder.embed_texts(batch)
        normalized = [l2_normalize(v) for v in batch_vecs]

        # Append this batch to the on-disk index
        # (no-op for the first batch in a fresh build since the
        # files were just removed by --overwrite or never existed)
        first_batch = (not existing_partial) and (i == 0)
        save_vector_index(
            EMBEDDINGS_DIR, args.name,
            metadata=batch_meta, vectors=normalized, dim=len(normalized[0]),
            append=not first_batch,
        )

        batch_num = (i // args.batch_size)
        is_checkpoint = batch_num % 20 == 0
        is_last = (i + len(batch)) == len(pending_texts)
        if is_checkpoint or is_last:
            global_done = start_index + i + len(batch)
            pct = (global_done / len(corpus)) * 100
            print(f"  Processed {global_done:,}/{len(corpus):,} passages "
                  f"({pct:.1f}%)...")

    elapsed = time.time() - start_time
    total_now = json.load(open(meta_path))["count"]
    print(f"Indexed {len(pending_corpus):,} new vectors in {elapsed:.2f}s "
          f"({len(pending_corpus)/max(elapsed, 0.001):.1f} vec/s). "
          f"Index now has {total_now:,} total entries.")
    print("Vector indexing complete.")


if __name__ == "__main__":
    main()
