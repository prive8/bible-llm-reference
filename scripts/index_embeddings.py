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


def _chunk_verses(
    items: list[tuple[int, str]],
    book_name: str,
    chapter_num: int,
    tradition: str,
    translation: str,
    chunk_size: int,
    chunk_step: int,
    start_id: int,
    limit: int = 0,
    citation_formatter=None,
) -> tuple[list[dict], int]:
    """Chunk a sequence of verses into sliding window passages."""
    entries: list[dict] = []
    curr_id = start_id
    if chunk_size <= 1:
        for v_num, v_text in items:
            cite = citation_formatter(v_num, v_num) if citation_formatter else f"{book_name} {chapter_num}:{v_num}"
            entries.append({
                "id": curr_id,
                "tradition": tradition,
                "translation": translation,
                "citation": cite,
                "text": v_text,
                "verses": [cite],
                "chunk_size": 1,
            })
            curr_id += 1
            if limit and curr_id >= limit:
                return entries, curr_id
        return entries, curr_id

    step = chunk_step if chunk_step > 0 else max(1, chunk_size - 1)
    n = len(items)
    for i in range(0, n, step):
        window = items[i:i + chunk_size]
        if not window:
            break
        v_start = window[0][0]
        v_end = window[-1][0]
        combined_text = " ".join(t for _, t in window)
        if citation_formatter:
            cite = citation_formatter(v_start, v_end)
            verses = [citation_formatter(v, v) for v, _ in window]
        else:
            cite = f"{book_name} {chapter_num}:{v_start}-{v_end}" if v_start != v_end else f"{book_name} {chapter_num}:{v_start}"
            verses = [f"{book_name} {chapter_num}:{v}" for v, _ in window]
        entries.append({
            "id": curr_id,
            "tradition": tradition,
            "translation": translation,
            "citation": cite,
            "text": combined_text,
            "verses": verses,
            "chunk_size": len(window),
        })
        curr_id += 1
        if limit and curr_id >= limit:
            return entries, curr_id
        if i + chunk_size >= n:
            break
    return entries, curr_id


def collect_corpus(
    include_bible: bool = True,
    include_quran: bool = True,
    limit: int = 0,
    judaism_edition: str = "jps1917-modernized",
    chunk_size: int = 1,
    chunk_step: int = 0,
) -> list[dict]:
    """Gather list of scripture passages across traditions, with optional sliding-window chunking."""
    entries: list[dict] = []
    curr_id = 0

    if include_bible:
        print("  Collecting Christian Bible (KJV)...")
        kjv = load_kjv()
        for book in kjv.get("books", []):
            book_name = book["name"]
            for ch in book.get("chapters", []):
                ch_num = ch["chapter"]
                items = [(v["verse"], strip_strongs_tags(v["text"])) for v in ch.get("verses", [])]
                ch_entries, curr_id = _chunk_verses(
                    items, book_name, ch_num, "christianity", "KJV",
                    chunk_size, chunk_step, curr_id, limit,
                )
                entries.extend(ch_entries)
                if limit and curr_id >= limit:
                    return entries

    if include_quran:
        print("  Collecting Quran (Saheeh International)...")
        try:
            quran = load_quran_edition("saheeh-international")
            for div in quran.get("divisions", []):
                s_id = div["id"]
                s_name = div["name"]
                items = [(ayah["ayah"], ayah["text"]) for ayah in div.get("ayahs", [])]
                def _q_cite(start_a, end_a, sid=s_id, sname=s_name):
                    if start_a == end_a:
                        return f"Quran {sid}:{start_a} ({sname})"
                    return f"Quran {sid}:{start_a}-{end_a} ({sname})"
                q_entries, curr_id = _chunk_verses(
                    items, s_name, s_id, "islam", "Saheeh International",
                    chunk_size, chunk_step, curr_id, limit,
                    citation_formatter=_q_cite,
                )
                entries.extend(q_entries)
                if limit and curr_id >= limit:
                    return entries
        except FileNotFoundError:
            print("  Warning: data/quran/saheeh-international.json not found, skipping Quran.")

    # Judaism (Torah + Tanakh)
    if _has_torah or _has_tanakh:
        if judaism_edition == "jps1917-modernized":
            judaism_editions_to_try = ["jps1917-modernized", "hebrew-nikkud"]
        else:
            judaism_editions_to_try = ["hebrew-nikkud", "jps1917-modernized"]
    else:
        judaism_editions_to_try = []

    # Torah (Phase 3.2) — Pentateuch
    if _has_torah:
        torah_tried = False
        for torah_key in judaism_editions_to_try:
            try:
                torah = load_torah_edition(torah_key)
                for div in torah.get("divisions", []):
                    book_name = div["name"]
                    grouped = _group_verses_by_chapter(div)
                    for ch_num in sorted(grouped.keys()):
                        items = [(v["verse"], v["text"]) for v in grouped[ch_num]]
                        t_entries, curr_id = _chunk_verses(
                            items, book_name, ch_num, "judaism", torah.get("translation", torah_key),
                            chunk_size, chunk_step, curr_id, limit,
                        )
                        entries.extend(t_entries)
                        if limit and curr_id >= limit:
                            return entries
                torah_tried = True
                print(f"  Collected Torah ({torah_key})...")
                break
            except FileNotFoundError:
                continue
        if not torah_tried:
            print("  Warning: no Torah data files found, skipping Judaism (Pentateuch).")

    # Tanakh (Phase 3.3) — Nevi'im + Ketuvim
    if _has_tanakh:
        tanakh_tried = False
        for tanakh_key in judaism_editions_to_try:
            try:
                tanakh = load_tanakh_edition(tanakh_key)
                neviim_ketuvim_books = (
                    BOOKS_BY_SECTION["Nevi'im"] + BOOKS_BY_SECTION["Ketuvim"]
                )
                for div in tanakh.get("divisions", []):
                    if div["name"] not in neviim_ketuvim_books:
                        continue
                    book_name = div["name"]
                    grouped = _group_tanakh_verses(div)
                    for ch_num in sorted(grouped.keys()):
                        items = [(v["verse"], v["text"]) for v in grouped[ch_num]]
                        tk_entries, curr_id = _chunk_verses(
                            items, book_name, ch_num, "judaism", tanakh.get("translation", tanakh_key),
                            chunk_size, chunk_step, curr_id, limit,
                        )
                        entries.extend(tk_entries)
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
    parser.add_argument("--judaism-edition",
                        choices=["jps1917-modernized", "hebrew-nikkud"],
                        default="jps1917-modernized",
                        help="Which Judaism edition to index (default: jps1917-modernized, "
                             "English; F0a fix). The non-default edition is used as a "
                             "fallback if the requested one is missing.")
    parser.add_argument("--chunk-size", type=int, default=1,
                        help="Number of verses per passage chunk (default: 1 for single verse)")
    parser.add_argument("--chunk-step", type=int, default=0,
                        help="Step/stride for sliding window passage chunking (default: max(1, chunk_size - 1))")
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
        judaism_edition=args.judaism_edition,
        chunk_size=args.chunk_size,
        chunk_step=args.chunk_step,
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
