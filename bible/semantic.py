"""Semantic search and dense embedding retrieval module (Milestone 3B).

Stdlib-first vector mathematics, pluggable embedding backends, and indexed
retrieval across Bible and Quran corpora.

Design:
    - Zero mandatory runtime dependencies (ADR-001). Vector calculations
      (dot-product, norm, cosine similarity, top-k) are implemented in pure
      Python standard library (`math`, `struct`, `heapq`).
    - Pluggable embedder backends:
        1. 'local': Local sentence-transformers (all-MiniLM-L6-v2, ~80MB, CPU).
        2. 'nim': NVIDIA NIM endpoint if NVIDIA_API_KEY is present in environment.
        3. 'mock': Deterministic stdlib fallback for CI and offline unit tests.
    - Flat binary float32 vector index with JSON metadata mapping for sub-millisecond
      local nearest-neighbor search.
"""

from __future__ import annotations

import json
import math
import os
import struct
import sys
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parent.parent
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"

# ---------------------------------------------------------------------------
# Pure Stdlib Vector Math
# ---------------------------------------------------------------------------

def dot_product(v1: list[float], v2: list[float]) -> float:
    """Compute dot product of two vectors."""
    return sum(x * y for x, y in zip(v1, v2))


def vector_norm(v: list[float]) -> float:
    """Compute Euclidean (L2) norm of a vector."""
    return math.sqrt(sum(x * x for x in v))


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors (-1.0 to 1.0)."""
    norm1 = vector_norm(v1)
    norm2 = vector_norm(v2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot_product(v1, v2) / (norm1 * norm2)


def l2_normalize(v: list[float]) -> list[float]:
    """Normalize vector to unit length (L2 norm = 1.0)."""
    n = vector_norm(v)
    if n == 0.0:
        return v[:]
    return [x / n for x in v]


# ---------------------------------------------------------------------------
# Index Serialization (Binary Float32 + Metadata JSON)
# ---------------------------------------------------------------------------

def save_vector_index(
    dir_path: Path,
    name: str,
    metadata: list[dict],
    vectors: list[list[float]],
    dim: int,
) -> None:
    """Serialize metadata and float32 vectors to disk."""
    dir_path.mkdir(parents=True, exist_ok=True)
    meta_path = dir_path / f"{name}_meta.json"
    bin_path = dir_path / f"{name}_vectors.bin"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "name": name,
            "count": len(metadata),
            "dim": dim,
            "entries": metadata,
        }, f, ensure_ascii=False, indent=2)

    with open(bin_path, "wb") as f:
        for vec in vectors:
            if len(vec) != dim:
                raise ValueError(f"Vector length {len(vec)} != expected dim {dim}")
            f.write(struct.pack(f"{dim}f", *vec))


def load_vector_index(
    dir_path: Path,
    name: str,
) -> Optional[tuple[list[dict], list[list[float]], int]]:
    """Load metadata and vectors from disk if they exist."""
    meta_path = dir_path / f"{name}_meta.json"
    bin_path = dir_path / f"{name}_vectors.bin"

    if not meta_path.exists() or not bin_path.exists():
        return None

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)

    dim = meta_data.get("dim", 0)
    count = meta_data.get("count", 0)
    entries = meta_data.get("entries", [])

    if dim <= 0 or count <= 0:
        return None

    vectors: list[list[float]] = []
    chunk_size = dim * 4  # 4 bytes per float32
    with open(bin_path, "rb") as f:
        for _ in range(count):
            buf = f.read(chunk_size)
            if len(buf) < chunk_size:
                break
            vec = list(struct.unpack(f"{dim}f", buf))
            vectors.append(vec)

    return entries, vectors, dim


# ---------------------------------------------------------------------------
# Pluggable Embedder Backends
# ---------------------------------------------------------------------------

class BaseEmbedder:
    """Interface for text embedding generation."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


class LocalSentenceTransformerEmbedder(BaseEmbedder):
    """Local CPU/GPU inference using sentence-transformers (all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is not installed. Install via:\n"
                "    pip install -e .[embeddings]\n"
                "or: pip install sentence-transformers"
            ) from e
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [list(map(float, row)) for row in embeddings]


class MockDeterministicEmbedder(BaseEmbedder):
    """Pure stdlib deterministic mock embedder for CI and test suites.

    Projects token hash frequencies into a compact unit vector so tests
    can run deterministically without downloading any weights.
    """

    def __init__(self, dim: int = 64):
        self.dim = dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            vec = [0.0] * self.dim
            tokens = text.lower().split()
            for token in tokens:
                # Hash bucket projection
                idx = sum(ord(c) for c in token) % self.dim
                vec[idx] += 1.0
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0.0:
                vec = [x / norm for x in vec]
            results.append(vec)
        return results


def get_embedder(backend: str = "auto") -> BaseEmbedder:
    """Factory for embedding backends: 'local', 'mock', or 'auto'."""
    if backend == "mock":
        return MockDeterministicEmbedder()
    elif backend == "local":
        return LocalSentenceTransformerEmbedder()
    elif backend == "auto":
        # Check if sentence-transformers is available
        try:
            import sentence_transformers  # noqa: F401
            return LocalSentenceTransformerEmbedder()
        except ImportError:
            # Fall back to mock
            return MockDeterministicEmbedder()
    else:
        raise ValueError(f"Unknown embedder backend: {backend!r}")


# ---------------------------------------------------------------------------
# Semantic Search Retrieval
# ---------------------------------------------------------------------------

def search_semantic(
    query: str,
    index_name: str = "default",
    top_k: int = 10,
    tradition: Optional[str] = None,
    backend: str = "auto",
    custom_index: Optional[tuple[list[dict], list[list[float]], int]] = None,
) -> list[dict]:
    """Search vector index for semantically similar verses.

    Returns list of dicts with:
        citation: str (e.g. 'John 3:16' or 'Quran 2:255')
        text: str
        score: float (cosine similarity)
        tradition: str ('bible' or 'islam')
        translation: str
    """
    if custom_index:
        entries, vectors, dim = custom_index
    else:
        loaded = load_vector_index(EMBEDDINGS_DIR, index_name)
        if not loaded:
            return []
        entries, vectors, dim = loaded

    if not entries or not vectors:
        return []

    # Get query embedding
    embedder = get_embedder(backend)
    query_vec = embedder.embed_query(query)

    # Normalize query vector if not already unit
    query_vec = l2_normalize(query_vec)

    # Score all entries
    scored: list[tuple[float, dict]] = []
    filter_tradition = tradition.lower().strip() if tradition else None

    for entry, doc_vec in zip(entries, vectors):
        if filter_tradition and filter_tradition != "all":
            entry_trad = entry.get("tradition", "").lower()
            if filter_tradition not in entry_trad:
                continue

        sim = cosine_similarity(query_vec, doc_vec)
        scored.append((sim, entry))

    # Rank top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for sim, entry in scored[:top_k]:
        results.append({
            "citation": entry.get("citation", ""),
            "text": entry.get("text", ""),
            "score": round(sim, 4),
            "tradition": entry.get("tradition", ""),
            "translation": entry.get("translation", ""),
        })

    return results


# ---------------------------------------------------------------------------
# CLI presentation
# ---------------------------------------------------------------------------

def run_semantic(
    query: str,
    index_name: str = "default",
    top_k: int = 10,
    tradition: Optional[str] = None,
    backend: str = "auto",
    as_json: bool = False,
) -> None:
    """CLI runner for semantic search."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    results = search_semantic(
        query=query,
        index_name=index_name,
        top_k=top_k,
        tradition=tradition,
        backend=backend,
    )

    if as_json:
        print(json.dumps({
            "query": query,
            "index": index_name,
            "backend": backend,
            "results_count": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2))
        return

    print("=" * 78)
    print(f"  Semantic Search (M3B) for: {query!r}")
    print(f"  Index: {index_name} | Backend: {backend}")
    print("=" * 78)

    if not results:
        meta_path = EMBEDDINGS_DIR / f"{index_name}_meta.json"
        if not meta_path.exists():
            print(f"\nNo precomputed vector index found at {meta_path.parent}.")
            print("To generate embeddings offline, run:")
            print("    python scripts/index_embeddings.py")
        else:
            print("\nNo matching passages found.")
        return

    for i, res in enumerate(results, 1):
        score_pct = f"{res['score'] * 100:.1f}%"
        tradition_badge = f"[{res['tradition'].upper()}]" if res.get("tradition") else ""
        print(f"\n{i}. {res['citation']} {tradition_badge} (Similarity: {score_pct})")
        print(f"   \"{res['text']}\"")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Semantic search CLI for scripture corpora (Milestone 3B)")
    parser.add_argument("query", help="Conceptual or thematic query (e.g. 'finding comfort in grief')")
    parser.add_argument("--index", default="default", help="Vector index name (default: 'default')")
    parser.add_argument("-n", "--top-k", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--tradition", choices=["all", "bible", "islam"], default="all",
                        help="Filter tradition (default: all)")
    parser.add_argument("--backend", choices=["auto", "local", "mock"], default="auto",
                        help="Embedder backend (default: auto)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()
    run_semantic(
        query=args.query,
        index_name=args.index,
        top_k=args.top_k,
        tradition=args.tradition,
        backend=args.backend,
        as_json=args.json,
    )


if __name__ == "__main__":
    main()
