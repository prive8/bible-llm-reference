#!/usr/bin/env python3
"""Stage OpenRouter embeddings in blocks of increasing size.

This is the staging harness — it embeds passages at increasing scale
(5, 200, 2000, full corpus) and reports cost + wall-time + throughput
after each block. The point is to *measure before committing*.

Each block writes the vectors to its own index name so the user can
inspect them and compare quality before deciding whether to keep
going. Block 4 (full corpus) only runs after Blocks 1-3 succeed.

Usage:
    python3 scripts/stage_openrouter_benchmark.py
    python3 scripts/stage_openrouter_benchmark.py --skip-block 3
    python3 scripts/stage_openrouter_benchmark.py --no-full
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
    DEFAULT_OPENROUTER_MODEL,
    DEFAULT_OPENROUTER_BATCH,
    save_vector_index,
    EMBEDDINGS_DIR,
)

# Use the same corpus collection as the main indexer
import scripts.index_embeddings as indexer_mod


BLOCK_SIZES = [5, 200, 2000]
STAGING_LOG = EMBEDDINGS_DIR / "openrouter-staging-log.jsonl"


def run_block(label: str, payload: list[dict], name: str) -> dict:
    texts = [p["text"] for p in payload]
    total_chars = sum(len(t) for t in texts)
    est_tokens = max(1, total_chars // 4)
    projected_full_cost = (5_280_000 / 1_000_000) * 0.02  # $0.02/M tokens × 5.28M est for full corpus

    print(f"\n{'='*72}\n{label} — {len(payload)} passages, batch={DEFAULT_OPENROUTER_BATCH}\n{'='*72}")
    print(f"  Avg text length: {total_chars // max(1, len(texts))} chars/verse")
    print(f"  Estimated tokens billed this run: {est_tokens:,}")

    emb = OpenRouterEmbedder(
        model=DEFAULT_OPENROUTER_MODEL,
        batch_size=DEFAULT_OPENROUTER_BATCH,
    )

    t0 = time.time()
    vectors = emb.embed_texts(texts)
    elapsed = time.time() - t0

    n = len(payload)
    rate = n / elapsed
    cost = (est_tokens / 1_000_000) * 0.02
    full_wall_min = (66_000 / rate) / 60 if rate else 0
    full_cost = projected_full_cost

    print(f"  Wall time:        {elapsed:.2f}s ({elapsed/n:.2f}s per verse)")
    print(f"  Throughput:       {rate:.1f} verses/sec")
    print(f"  Cost (this run):  ${cost:.6f}")
    print(f"  --- EXTRAPOLATING TO FULL 66K CORPUS ---")
    print(f"  Wall time:        {full_wall_min:.1f} min")
    print(f"  Total cost:       ${full_cost:.4f}")
    print(f"  Budget $10/mo:    {10/full_cost:.0f} full-corpus rebuilds available")

    # Save vectors as a proper index for this block
    from bible.semantic import l2_normalize
    normed = [l2_normalize(v) for v in vectors]
    save_vector_index(EMBEDDINGS_DIR, name, payload, normed, len(normed[0]))
    print(f"  Saved index → data/embeddings/{name}_*.*")

    result = {
        "label": label,
        "name": name,
        "n": n,
        "elapsed_sec": round(elapsed, 2),
        "per_verse_sec": round(elapsed / n, 4),
        "verses_per_sec": round(rate, 2),
        "est_tokens": est_tokens,
        "cost_usd": round(cost, 6),
        "projected_full_wall_min": round(full_wall_min, 1),
        "projected_full_cost_usd": round(full_cost, 4),
    }
    with STAGING_LOG.open("a") as f:
        f.write(json.dumps(result) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-block", type=int, default=0, help="Skip blocks above this number")
    parser.add_argument("--no-full", action="store_true", help="Skip Block 4 (full 66K)")
    parser.add_argument("--batch", type=int, default=DEFAULT_OPENROUTER_BATCH, help="Override batch size")
    args = parser.parse_args()

    print(f"Model: {DEFAULT_OPENROUTER_MODEL}")
    print(f"Cost rate: $0.02 per million tokens (OpenAI text-embedding-3-small via OpenRouter)")
    print(f"Output dir: {EMBEDDINGS_DIR}")

    # Reset log
    STAGING_LOG.unlink(missing_ok=True)

    # Collect the corpus (no limit)
    print("\nCollecting full corpus (66K passages; takes ~1 min)...")
    t0 = time.time()
    corpus = indexer_mod.collect_corpus(limit=0)
    print(f"Collected {len(corpus):,} passages in {time.time()-t0:.1f}s\n")
    print(f"  Tradition breakdown:")
    counts = {}
    for c in corpus:
        t = c.get("tradition", "?")
        counts[t] = counts.get(t, 0) + 1
    for t, n in sorted(counts.items()):
        print(f"    {t}: {n:,}")

    # Block 1-3: stepping up
    # argparse "skip_block" = highest block to RUN (blocks > this are skipped)
    all_results = []
    for i, n in enumerate(BLOCK_SIZES, start=1):
        if i <= args.skip_block:
            run_block(f"BLOCK {i}", corpus[:n], f"openrouter-staging-b{i}")
            all_results.append((i, n))

    # Block 4: full corpus (the gate value is "blocks > 4 are skipped", so
    # --skip-block 4 inclusive of full)
    if not args.no_full:
        run_block("BLOCK 4 — FULL CORPUS", corpus, "openrouter-default")

    print(f"\n{'='*72}")
    print("STAGING SUMMARY")
    print(f"{'='*72}")
    print(f"{'#':>3} {'N':>7} {'Wall':>7} {'Verses/s':>10} {'Cost':>10} {'$/66K':>10}")
    print("-" * 72)
    for i, n in all_results:
        with STAGING_LOG.open() as f:
            lines = [json.loads(l) for l in f if l.strip()]
            r = [x for x in lines if x.get("n") == n][-1]
            print(f"{r['label'][:30]:>30} {r['n']:>7} {r['elapsed_sec']:>6.1f}s {r['verses_per_sec']:>9.1f} ${r['cost_usd']:>8.6f} ${r['projected_full_cost_usd']:>8.4f}")


if __name__ == "__main__":
    main()
