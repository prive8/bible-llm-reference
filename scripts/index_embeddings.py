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

    print(f"Generating vectors in batches of {args.batch_size}...")
    start_time = time.time()
    vectors: list[list[float]] = []

    texts = [e["text"] for e in corpus]
    for i in range(0, len(texts), args.batch_size):
        batch = texts[i:i + args.batch_size]
        batch_vecs = embedder.embed_texts(batch)
        for vec in batch_vecs:
            vectors.append(l2_normalize(vec))

        if (i // args.batch_size) % 20 == 0 or (i + len(batch)) == len(texts):
            pct = ((i + len(batch)) / len(texts)) * 100
            print(f"  Processed {i + len(batch):,}/{len(texts):,} passages ({pct:.1f}%)...")

    elapsed = time.time() - start_time
    dim = len(vectors[0]) if vectors else 0
    print(f"Generated {len(vectors):,} vectors (dim={dim}) in {elapsed:.2f}s ({len(vectors)/max(elapsed, 0.001):.1f} vec/s)")

    print(f"Saving vector index to {EMBEDDINGS_DIR}/{args.name}...")
    save_vector_index(EMBEDDINGS_DIR, args.name, corpus, vectors, dim)
    print("Vector indexing complete.")


if __name__ == "__main__":
    main()
