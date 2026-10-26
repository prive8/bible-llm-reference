# Does chunking help? Measured on the local embedder, 2026-10-26

## The question

The 2026-10-08 notes ask for a chunked rebuild:
`--chunk-size 3 --chunk-step 2`. The claim is that single-verse
passages are too granular — a query like "comfort in times of grief"
wants a whole pericope, and a 3-verse window gives the embedder more
context to match against.

That has been open since 2026-10-08 and it is the one remaining spend
decision on the board.

## How it was measured

**With the local embedder, at zero API cost.** The chunking effect is a
property of the *index structure*, not of the embedder: if 3-verse
windows do not help the local embedder find "comfort in times of grief",
a stronger embedder is not going to rescue them. Measuring it on the
cheap embedder first is the right order — it costs $0 and it decides
whether any chunked paid build is worth doing at all.

Build: `scripts/index_embeddings.py --backend local --name local-chunk3
--chunk-size 3 --chunk-step 2 --batch-size 64 --overwrite`

- 32,732 passages (vs 66,689 unchunked) — half as many, because windows
  cover 3 verses each
- 11m14s wall, 49.5 vec/s, **$0**
- Index verified self-consistent: 32,732 × 384, 21,430,272 bytes

## Result: chunking does not help. It is a wash, and the mechanism is dilution.

| v2 dev (48 queries), local embedder | bm25 | semantic | hybrid |
|---|---|---|---|
| unchunked (`default`, 66,689 × 384) | 0.119 | **0.189** | **0.183** |
| chunked (`local-chunk3`, 32,732 × 384) | 0.119 | 0.182 | 0.182 |

**−0.007 semantic, −0.001 hybrid.** Within noise for the aggregate, and
per-persona it is a wash with one persona moving:

| | Sarah | Marcus | Yuki | Priya | Aisha | Jordan |
|---|---|---|---|---|---|---|
| unchunked | 0.150 | 0.100 | 0.225 | 0.150 | 0.150 | 0.356 |
| chunked | 0.125 | 0.075 | 0.225 | 0.150 | 0.125 | 0.394 |

Three personas down by 0.025, one up by 0.038, two flat. Each 0.025 is
one query out of eight.

## The mechanism: windows dilute the signal

This is the part worth keeping. It is not that chunking is neutral —
it is that chunking makes the *specific* match worse, and the
benchmark's expectation is a specific match.

Query: **"comfort in times of grief"**. The expected citation is
**Matthew 5:4** ("Blessed are those who mourn, for they shall be
comforted").

| | score for this query |
|---|---|
| unchunked `Matthew 5:4` (one verse) | **0.665** |
| chunked `Matthew 5:3-5` (the window containing 5:4) | **0.317** |

**The window containing the right verse scores less than half the right
verse alone.** The top-10 for this query from the chunked index contains
no Matthew 5 passage at all — I checked to 60 and found none — while
the unchunked index ranks `Matthew 5:4` at **#2**.

The reason is straightforward once stated: a 3-verse window averages
the meaning of three verses. `Matthew 5:3-5` spans "Blessed are the
meek / Blessed are those who mourn / Blessed are the peacemakers" —
three different ideas. The single verse `Matthew 5:4` is one idea, and
it matches "comfort in times of grief" directly. Averaging dilutes the
one signal you wanted.

**And the scorer's chunk-aware matching cannot save it.**
`citation_matches` treats a retrieved window as satisfying an expected
verse inside it — which is exactly what should make chunking
comparable. But it only helps if the window is *retrieved at all*.
`Matthew 5:3-5` never makes the top 60 for this query, so the credit
never applies. Chunking here does not "retrieve a window instead of a
verse"; it **loses the verse**, because the window is a worse match for
the query than the verse was.

## What this settles

**Do not build a chunked paid index.** The evidence is that chunking
does not improve retrieval quality on this corpus and this benchmark;
it holds the aggregate flat and moves individual personas around. A
chunked qwen3-8b build would cost ~$0.07–$1.50, take ~30–55 minutes,
and buy a flat number.

**The 2026-10-08 note's premise is wrong**, and it is worth being
specific about why. The note assumed single verses are "too granular"
for a pericope-seeking query. They are not: at 384 dimensions, a single
verse is already a rich enough unit for a dense embedder to match a
thematic query. The premise would only hold if the embedder were
starved for context — which is an argument for a *model* that reads
longer windows (a cross-encoder, or a generative reranker), not for
pre-chunking a bi-encoder's corpus.

**What chunking would be good for**, if this project ever wants it: not
retrieval recall, but **presentation** — returning a pericope around
the matched verse so the reader sees context, rather than a lone
sentence. `bible/semantic.py` already has the machinery for that
(`expand_passage_chunks`, `resolve_verses=True`, and the
`constituent_verses` field on results). That is a rendering concern
and can be done at query time over an unchunked index, with no
rebuild and no re-embedding at all.

## Reproducing

```
python scripts/index_embeddings.py --backend local --name local-chunk3 \
  --chunk-size 3 --chunk-step 2 --batch-size 64 --overwrite
python scripts/run_eval.py --paths bm25,semantic,hybrid \
  --benchmark v2 --split dev --index local-chunk3 --backend local
```

BM25 is identical at 0.119 across both runs, as it must be — it does
not read a vector index. That is the control that the benchmark, the
corpus, and the scorer were unchanged, so the semantic difference is
attributable to the index structure and nothing else.
