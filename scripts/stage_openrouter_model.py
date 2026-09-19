#!/usr/bin/env python3
"""Stage 1 sanity check: embed 200 passages with a chosen OpenRouter model.

Same shape as scripts/stage_openrouter_benchmark.py Block 2, but accepts
a --model arg so we can compare candidate models against the existing
openrouter-staging-b2 baseline (text-embedding-3-small).

Reports: wall time, throughput, projected full-corpus cost, and runs the
same 8 conceptual quality queries used in 2026-09-11-openrouter-staging.md.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

# Bootstrap the key from ~/.hermes/.env
key = None
for line in (Path.home() / ".hermes" / ".env").read_text().splitlines():
    if line.startswith("OPENROUTER_API_KEY="):
        key = line.split("=", 1)[1].strip()
        os.environ["OPENROUTER_API_KEY"] = key
        break
if not key:
    print("ERROR: OPENROUTER_API_KEY not in ~/.hermes/.env", file=sys.stderr)
    sys.exit(2)

REPO = Path("/home/pierce/repos/bible-llm-reference")
sys.path.insert(0, str(REPO))

from bible.semantic import (
    OpenRouterEmbedder,
    save_vector_index,
    EMBEDDINGS_DIR,
    l2_normalize,
)
import scripts.index_embeddings as indexer_mod

# 8 conceptual queries from 2026-09-11 staging note Block 3
QUALITY_QUERIES = [
    "the beginning of the world when God created",
    "God's mercy/lovingkindness in the Psalms",
    "forgive us our trespasses",
    "be still and know I am God",
    "the Lord is my shepherd",
    "heavens declare glory",
    "I am the way the truth and the life",
    "God is love",
]


def cosine_top_k(query_vec, index_vecs, index_meta, k=5):
    """Return top-k (meta, score) pairs by cosine similarity."""
    import numpy as np
    q = np.asarray(query_vec)
    M = np.asarray(index_vecs)
    sims = M @ q  # all vectors are L2-normalized
    top_idx = sims.argsort()[::-1][:k]
    return [(index_meta[i], float(sims[i])) for i in top_idx]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="OpenRouter model ID, e.g. qwen/qwen3-embedding-8b")
    p.add_argument("--n", type=int, default=200, help="Block 2 size in passages (default 200)")
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--out-name", default=None, help="Index name (default: derived from model)")
    args = p.parse_args()

    out_name = args.out_name or f"openrouter-staging-{args.model.split('/')[-1]}-b2"
    print(f"Model: {args.model}")
    print(f"Block size: {args.n} passages")
    print(f"Output index: {out_name}")

    # Read account state before
    import urllib.request
    auth_header = f"Bearer {os.environ['OPENROUTER_API_KEY']}"
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": auth_header},
    )
    before = json.loads(urllib.request.urlopen(req, timeout=15).read())["data"]
    print(f"\nAccount BEFORE: usage=${before['usage']:.4f}, remaining=${before['limit_remaining']:.4f}")

    # Collect corpus and slice
    print("\nCollecting corpus...")
    corpus = indexer_mod.collect_corpus(limit=0)
    payload = corpus[: args.n]
    print(f"  Sliced to {len(payload)} passages")

    # Embed
    emb = OpenRouterEmbedder(model=args.model, batch_size=args.batch)
    t0 = time.time()
    vectors = emb.embed_texts([p["text"] for p in payload])
    elapsed = time.time() - t0

    dim = len(vectors[0])
    total_chars = sum(len(p["text"]) for p in payload)
    est_tokens = max(1, total_chars // 4)
    rate = len(payload) / elapsed

    print(f"\n  Wall time: {elapsed:.2f}s ({elapsed/len(payload):.3f}s per verse)")
    print(f"  Throughput: {rate:.1f} verses/sec")
    print(f"  Dimension: {dim}")
    print(f"  Est tokens billed: {est_tokens:,}")

    # Save index
    normed = [l2_normalize(v) for v in vectors]
    save_vector_index(EMBEDDINGS_DIR, out_name, payload, normed, dim)
    print(f"  Saved → data/embeddings/{out_name}_*.*")

    # Read account state after
    time.sleep(2)  # let the usage settle
    after = json.loads(urllib.request.urlopen(req, timeout=15).read())["data"]
    actual_cost = after["usage"] - before["usage"]
    print(f"\nAccount AFTER: usage=${after['usage']:.4f}, remaining=${after['limit_remaining']:.4f}")
    print(f"  Actual cost this run: ${actual_cost:.6f}")
    print(f"  Effective $/M tokens: ${(actual_cost / est_tokens * 1_000_000):.4f}")

    # Project to full corpus (~2.2M tokens, 66K passages)
    full_cost = actual_cost * (66_000 / args.n)
    full_wall_min = (66_000 / rate) / 60
    print(f"\n  --- EXTRAPOLATED TO 66K ---")
    print(f"  Wall:    {full_wall_min:.1f} min")
    print(f"  Cost:    ${full_cost:.4f}")
    if full_cost > 0:
        print(f"  Budget $10/mo: ~{10/full_cost:.0f} full rebuilds")
    else:
        print(f"  Cost rounds to zero — model is effectively free at this scale")

    # Quality spot-check on the same 8 queries used in 2026-09-11
    print(f"\n{'='*72}\nQUALITY SPOT-CHECK (8 conceptual queries)\n{'='*72}")
    import numpy as np
    M = np.asarray(normed)

    q_emb = OpenRouterEmbedder(model=args.model, batch_size=8)
    for query in QUALITY_QUERIES:
        # qwen and e5-style models use input_type="query"; OpenAI doesn't care
        # but our embedder signature: embed_query is single-text
        qv = q_emb.embed_query(query)
        qv = l2_normalize(qv)
        sims = M @ np.asarray(qv)
        top_idx = sims.argsort()[::-1][:3]
        top1 = payload[top_idx[0]]
        print(f"\n  Q: {query!r}")
        print(f"    #1 {top1['ref']} ({top1.get('translation','?')}) score={sims[top_idx[0]]:.3f}")
        text_preview = top1["text"][:80].replace("\n", " ")
        print(f"        \"{text_preview}...\"")

    # Final summary line
    print(f"\n{'='*72}")
    print(f"STAGE 1 RESULT: model={args.model}, cost=${actual_cost:.4f}, dim={dim}, throughput={rate:.1f}/s")
    print(f"{'='*72}")


if __name__ == "__main__":
    main()
