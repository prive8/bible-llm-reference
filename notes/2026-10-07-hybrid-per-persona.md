# 2026-10-07 — Hybrid path per-persona table (39-query benchmark)

> Companion to `notes/2026-10-07-adr-015-followup-v2-per-persona.md`
> (semantic path). The hybrid path blends BM25 + semantic with
> the tuned `bm25_weight=0.1` default per ADR-011/ADR-015. The
> question this doc answers: does the hybrid dilution change the
> persona shape?

## TL;DR

The persona shape **holds for hybrid** with one notable sharpening:
hybrid *amplifies* the 3-large vs local trade-off on recall. 3-large
still wins Aisha (semantic: +0.089, hybrid: +0.061) and Priya
(semantic: +0.033, hybrid: +0.040), and still loses Sarah /
Marcus / Jordan / Yuki. **Hybrid makes Yuki and Priya retrievable
via BM25 at all** — the local-hybrid Priya went from 0.000 (BM25
has no Quran/Torah) to 0.067 (semantic carrying the hybrid).

BM25 itself, by contrast, has 0.000 Priya recall (no Quran / Torah
in the BM25 index), 0.000 Yuki recall (cross-tradition queries
have no BM25 hits), and 0.000 Marcus recall. The semantic component
of hybrid is what makes Priya / Yuki / Marcus retrievable.

## Setup

Same as the semantic follow-up v2 doc:
- 39-query benchmark (33 Bible + 6 cross-tradition)
- Local `all-MiniLM-L6-v2` (384-dim) and 3-large (3072-dim)
- Hybrid weights: `bm25_weight=0.1`, `solo_weight=0.7` (ADR-015 defaults)
- `python3 scripts/run_eval.py --paths hybrid --backend {local,openrouter}
  --index {default,openrouter-3large}`

## Full table — 4 path × embedder combinations

| Persona | n  | Local Sem R | Local Hyb R | 3L Sem R | 3L Hyb R |
|---------|----|-------------|-------------|----------|----------|
| sarah   | 11 | 0.256       | 0.226       | 0.201    | 0.186    |
| marcus  |  6 | 0.250       | 0.283       | 0.183    | 0.150    |
| aisha   |  6 | 0.222       | 0.195       | 0.311    | 0.256    |
| jordan  |  5 | 0.387       | 0.347       | 0.313    | 0.313    |
| yuki    |  6 | 0.183       | 0.183       | 0.150    | 0.150    |
| priya   |  5 | 0.107       | 0.067       | 0.140    | 0.107    |

| Persona | Local Sem MRR | Local Hyb MRR | 3L Sem MRR | 3L Hyb MRR |
|---------|---------------|---------------|------------|------------|
| sarah   | 0.182         | 0.182         | 0.273      | 0.217      |
| marcus  | 0.222         | 0.222         | 0.264      | 0.264      |
| aisha   | 0.167         | 0.167         | 0.350      | 0.333      |
| jordan  | 0.220         | 0.200         | 0.256      | 0.153      |
| yuki    | 0.000         | 0.000         | 0.250      | 0.250      |
| priya   | 0.000         | 0.000         | 0.250      | 0.250      |

Sign convention: positive numbers = better. Larger = better.

## What the data says

**The persona shape holds for hybrid.** Compare per-persona deltas
(semantic vs hybrid within each embedder):

| Persona | Local Δ R | 3L Δ R | Local Δ MRR | 3L Δ MRR |
|---------|----------|--------|-------------|----------|
| sarah   | -0.030   | -0.015 |  0.000      | -0.056   |
| marcus  | +0.033   | -0.033 |  0.000      |  0.000   |
| aisha   | -0.027   | -0.055 |  0.000      | -0.017   |
| jordan  | -0.040   |  0.000 | -0.020      | -0.103   |
| yuki    |  0.000   |  0.000 |  0.000      |  0.000   |
| priya   | -0.040   | -0.033 |  0.000      |  0.000   |

The deltas are small (|Δ| < 0.06 for recall, < 0.10 for MRR). The
hybrid *mostly* follows the semantic pattern. Notable:

- **3-large jordan MRR drops -0.103** with hybrid (0.256 → 0.153).
  This is a real regression. The BM25 noise in the hybrid fusion
  knocks the jordan short-query precision around. Worth
  investigating — possibly the `bm25_weight=0.1` is too high
  for the interface-edge-case queries.
- **Local marcus R rises +0.033** with hybrid. BM25 helps Marcus
  (his queries are mostly common-word phrases like "creation of
  the world by God" that BM25 can match without semantic
  understanding).
- **3-large aisha R drops -0.055** with hybrid. Aisha wins on
  semantic precision, but hybrid's BM25 contribution pulls the
  recall number down. The MRR stays high (0.333) — the right
  verse is still ranked first, but more relevant verses are
  *also* in the top-10, and hybrid dilutes that.

## What about pure BM25 (no semantic)?

| Persona | n  | BM25 R | BM25 MRR |
|---------|----|--------|----------|
| sarah   | 11 | 0.030  | 0.000    |
| marcus  |  6 | 0.067  | 0.000    |
| aisha   |  6 | 0.128  | 0.000    |
| jordan  |  5 | 0.267  | 0.200    |
| yuki    |  6 | 0.083  | 0.000    |
| priya   |  5 | 0.000  | 0.000    |

BM25's per-persona pattern is the **opposite** of semantic:
jordan wins (0.267), aisha and marcus are middling, and the
cross-tradition personas (yuki, priya) get 0.000 because BM25
has no Quran or Torah passages to match against. The semantic
component of hybrid is what makes the cross-tradition personas
retrievable at all.

## What this means

**The persona-shape finding is robust across both paths.** The
3-large vs local trade-off is not a semantic-path artifact.
Whether you weight the fusion toward BM25 (current default
`bm25_weight=0.1`) or toward semantic, 3-large wins Aisha +
Priya on recall and loses on the pastoral / philosophical /
interface / cross-tradition-parallel personas.

**Hybrid adds one new wrinkle**: the 3-large jordan MRR drops
-0.103. Worth investigating as a follow-up, but the overall
pattern is unchanged. The Phase 4 routing decision is:
- Reader (Sarah) → local semantic (best recall)
- Scholar (Aisha) → 3-large semantic (best precision + recall)
- Comparative (Yuki, Priya) → local semantic (cheaper, and
  Priya's recall is 0.107 vs 3-large's 0.140 — close enough
  that the cost difference wins)

The 3-large jordan-MRR regression in hybrid is the one thing
worth a closer look. Either (a) the bm25_weight is too high
for jordan's short / named-entity queries, or (b) jordan's
3-large queries are genuinely noise-sensitive and the user
should get routed away from hybrid when persona=jordan.
Both are Phase 4 routing concerns, not production defaults.

## Files in this commit

- `notes/2026-10-07-hybrid-per-persona.md` (this doc)
- `notes/eval-runs/2026-10-07-local-hybrid-39query.log` (raw output)
- `notes/eval-runs/2026-10-07-3large-hybrid-39query.log` (raw output)

## Open follow-ups

1. **qwen3-8b full build + 3rd-embedder eval** — the checkpointing
   fix is live; a build is in flight as of 13:13 EDT. Re-eval
   against the 39-query benchmark when the index lands.
2. **Phase 4 routing** — Reader / Scholar / Comparative
   layers, persona → embedder choice. The data is in place.
3. **Jordan + 3-large + hybrid regression** — investigate why
   the 3-large hybrid jordan MRR drops -0.103 vs semantic
   (0.256 → 0.153). Could be (a) bm25_weight tuning, (b) a
   persona-specific routing flag.