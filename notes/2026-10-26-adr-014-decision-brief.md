# Decision brief — should the production embedder default change? (2026-10-26)

**Status:** brief for the acting chair. **This is not an ADR.** ADR-014
is signed and stands until the chair amends it. This document lays out
the evidence and the trade-off so the amendment can be made on facts
rather than on the 2026-10-07 belief that "the local default is fine."

---

## 1. What changed

ADR-014 (2026-09-11) keeps `all-MiniLM-L6-v2` (local, 384-dim) as the
production embedder default. Its stated condition for changing that was
explicit:

> The OpenRouter path is wired and available but unused **until credits
> are purchased and quality is validated against the local baseline.**

Both conditions are now met. Credits are purchased ($10, $8.85
remaining) and the quality comparison has been run properly — on
**benchmark v2**, which is the multi-tradition benchmark that matches
the corpus this project actually ships (v1 is 100% Bible and was the
wrong instrument for a 3-tradition corpus).

## 2. The evidence

### Quality — v2, both splits, same benchmark and corpus

| embedder | dim | v2 dev semantic | v2 held_out semantic |
|---|---|---|---|
| MiniLM (local, current default) | 384 | 0.189 | 0.106 |
| qwen3-8b (OpenRouter) | 4096 | **0.321** | **0.255** |
| text-embedding-3-large (OpenRouter) | 3072 | *see §6* | *see §6* |

**qwen3-8b beats the current default by +0.132 on dev and +0.149 on
held_out** — a 70% and 141% relative gain respectively. The gain
*widens* on the harder split, which is the opposite of a benchmark
artifact.

Every one of the six personas improves. The largest gains land on the
two hardest personas:

| | Sarah | Marcus | Yuki | Priya | Aisha | Jordan |
|---|---|---|---|---|---|---|
| MiniLM | 0.150 | 0.100 | 0.225 | 0.150 | 0.150 | 0.356 |
| qwen3-8b | **0.275** | **0.225** | **0.362** | **0.375** | **0.275** | **0.412** |

Marcus is the comparative scholar and Priya the academic-neutral
persona — both query across traditions. A stronger embedder helping
them most is the shape you want for a corpus that is three traditions.

### Cost — this is not the deciding factor

| | per-query API cost | 48-query v2 dev eval |
|---|---|---|
| qwen3-8b | ~$0.00000008 | ~$0.000004 |
| 3-large | ~$0.00000008 | ~$0.000004 |

Three full evaluation runs on 2026-10-26 cost **$0.000119** total. A
paid embedder is affordable at any plausible traffic — a million
queries is under $0.10. **The ADR-014 concern about spend does not
bind.** The real costs are latency and index size (§3, §4).

(The one exception is a **full index rebuild**, not query serving: the
2026-09-19 3-large build cost ~$0.74 and the 2026-10-26 rebuild is
running now. Rebuilds are a build-time cost, amortized over every
query the index serves — the per-query number is what ADR-014's
"zero spend for production retrieval" clause is about, and that number
is negligible.)

### Latency — the actual constraint

Measured on the real indexes, using the shipped code path
(`operator.mul`, precomputed norms):

| | query embed | local index scan | end-to-end | one-time load |
|---|---|---|---|---|
| MiniLM (384-dim) | 161 ms | 0.67 s | **0.83 s** | 1.4 s |
| 3-large (3072-dim) | 645 ms | 2.27 s | **2.92 s** | 3.9 s |
| qwen3-8b (4096-dim) | 2,900 ms | 6.71 s | **9.61 s** | 22.3 s |

**A 9.6-second query is not shippable in a web reader.** Steven's
recorded direction (2026-10-25) is "likely a web reader / study help."
The quality ranking and the latency ranking point in opposite
directions, and **that trade-off is invisible in a recall table** —
which is why the earlier comparisons, having measured only quality,
did not surface it.

Note the composition: for qwen3-8b, the **API call is 30% of the query
and the local index scan is 70%**. The lever is index size (dimension ×
count), not the network.

## 3. The options

**Option A — keep MiniLM as the default.** Zero cost, 0.83 s queries.
But it leaves the retrieval quality 70% below what is already paid
for and measured. And on held_out, all three paths land within 0.023
of each other (bm25 0.092, semantic 0.106, hybrid 0.115) — the local
embedder adds almost nothing over keyword search on the harder split.

**Option B — switch the default to a paid embedder.** Best quality,
~1.4M queries per dollar. Costs latency and a large index.

**Option C — switch the default AND fix the latency first.** Same
quality as B, with the scan cost addressed. The scan is pure-Python
over 66,689 × 4096 float32s; a numpy path is ~22× faster on scoring
and numpy is already an `embeddings` extra and is already installed in
the CI eval job. **The constraint is ADR-001, which makes `bible/`
stdlib-only** — so a numpy path needs a stdlib fallback and an ADR
amendment to permit it, or it must live outside `bible/`.

**Option D — route per persona.** The persona data supports it: the
gains differ by persona, and jordan (0.356 → 0.412) needs the
embedder least while priya (0.150 → 0.375) needs it most. But a
per-persona router is Phase 4 work, which is still blocked on the
use-case pick (chatbot vs full LLM vs lookup tool).

## 4. What this brief does not settle

- **Phase 4's shape.** The use-case pick is still open, and it
  determines whether per-query retrieval latency is a user-visible
  wait or an offline batch step. If the reader is a search box, 9.6 s
  is disqualifying. If it is an offline "study help" pipeline, it is
  irrelevant.
- **Whether 3-large or qwen3-8b wins.** The 3-large index was
  truncated (see §6) and is being rebuilt; its true number is not yet
  in.
- **Any production deployment shape.** The 22.3 s index load for
  qwen3-8b is a cold-start cost that a real deployment has to address
  (preload, mmap, or a smaller index).

## 5. What is already decided and not up for debate

- **The embedder stays pluggable.** ADR-010's factory pattern holds;
  this is a default-value question, not an architecture question.
- **The `bible/` package stays stdlib-only** unless a separate ADR
  amends ADR-001. Any numpy work needs that decision first.
- **Chunking is not the answer.** Measured 2026-10-26 with the local
  embedder at zero cost: 3-verse windows score 0.182 against 0.189
  unchunked on v2 dev. The mechanism is dilution — for "comfort in
  times of grief", the unchunked `Matthew 5:4` scores 0.665 while the
  window `Matthew 5:3-5` containing it scores 0.317, and the chunked
  index returns no Matthew 5 passage in its top 10. See
  `notes/2026-10-26-chunking-measured.md`.

## 6. A note on how the 3-large number was wrong

The 2026-09-19 `text-embedding-3-large` index on disk holds **30,159
of 66,689 vectors** — 45.2% — and because the corpus is collected
Christianity-first, the surviving vectors are **Christianity-only**.
It scored 0.344 on the cross-tradition v2 benchmark, appearing to beat
qwen3-8b, while being unable to retrieve a single Quran or Tanakh
passage.

The harness had checked the benchmark, the corpus files, and the
scorer, and all three were identical across every arm. It never
checked the **integrity of the artifact being scored** — and BM25,
which is identical across every arm and looks like a reassuring
control, does not read a vector index, so it said nothing about it.

Fixed in `59789d5`: `save_vector_index` now refuses to write an index
whose metadata and vectors disagree, the loader warns by name when a
`.bin` is short, and a CI step checks every index on disk for
self-consistency.

**This is the reason the 3-large row is blank in §2 rather than a
number.** It is being rebuilt and re-measured. It is also the reason
no number in this brief should be trusted without the same
artifact-integrity check applied to it.

## 7. The decision, when the chair makes it

Three things would make this brief answerable rather than merely
informative:

1. **The use-case pick** (chatbot vs full LLM vs lookup tool) — because
   it determines whether 9.6 s is disqualifying.
2. **A complete 3-large number** — to know whether the cheaper and
   faster of the two paid options is also the best.
3. **A decision on ADR-001** — whether an optional numpy scoring path
   (with a stdlib fallback) may live in `bible/`. If yes, Option C
   collapses the latency gap and the quality question becomes the only
   one left. If no, then qwen3-8b's 6.71 s scan is a permanent
   characteristic and the routing decision (Option D) matters more.

Until then the current default is defensible: it is fast, free, and
works. It is just measurably the worst of the three at the thing the
project is for.

---

*Measurements: `notes/2026-10-26-qwen3-v2-eval.md`,
`notes/2026-10-26-chunking-measured.md`,
`notes/2026-10-26-truncated-index-found.md`,
`notes/2026-10-26-index-reload-fix.md`. All measured on the same host
against the same corpus and benchmark; BM25 identical across every
arm is the control.*
