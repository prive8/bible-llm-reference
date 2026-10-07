# Design: Sarah-persona eval slice + cross-tradition queries (Option B v2)

> Working notes — NOT for commit. Captures the rethinking after reading
> `tests/benchmark.py` in full.

## What I got wrong in the menu

The 33-query set in `tests/benchmark.py` is *not* purely doctrinal.
Counting by theme from the actual file:

- **Pastoral / life-question** (Sarah-shaped, "what does the Bible say about X"):
  ~14 queries (grief, fear, trust, hope, mercy, anger, patience, overwhelmed,
  abandoned, strength, etc.)
- **Doctrinal** (theological-query-shaped, "what does the Bible teach about Y"):
  ~13 queries (creation, judgment, love, faith, prophecy, resurrection, etc.)
- **Narrative** (story-anchored, "Joseph's story", "King David's psalms"):
  ~3 queries
- **Single-word / adversarial** (precision-sensitive, "light", "shepherd",
  "grace", "eternal life", "the Holy Spirit"): ~5 queries

So roughly half the set *is* already Sarah-shaped. I miscounted in the
menu when I said "the 33-query set is theological-doctrinal".

## What's actually missing (the real Option B)

Three gaps, in priority order:

### Gap 1: per-persona labels on the 33 queries

A `persona: "sarah" | "marcus" | "yuki" | "priya" | "aisha" | "jordan"`
field on each query. Compute recall@K per persona. The cross-embedder
comparison (local vs 3-large) on 2026-09-19 ran on the aggregate
33-query average; the per-persona breakdown is a *new* view of the
same data.

Why it matters: if 3-large wins on the doctrinal queries (precision)
and loses on the pastoral queries (recall), the trade-off has a
persona shape. Sarah's pastoral queries might want the recall; Aisha's
doctrinal queries might want the precision. The aggregate number
hides that. The "which embedder for which persona" question is the
load-bearing question for Phase 4 (front-end default).

Cost: 1-2 hours. Pure data work + a new section in `docs/evaluation.md`
+ a sister-script test that asserts the persona labels are present.

### Gap 2: cross-tradition queries

The 33-query set is overwhelmingly Christian/Bible. The Quran and
Tanakh corpora are in the index (66K passages total per ADR-015) but
not exercised by the eval. Adding 5-10 cross-tradition queries (some
Muslim, some Jewish, some explicitly cross-tradition) would let the
eval measure whether the retrieval substrate actually serves Marcus
and Priya, not just Sarah.

Examples I'm considering:
- "mercy and forgiveness in the Quran" → Quran 2:64, 39:53
- "God as creator in the Torah" → Genesis 1:1, Psalm 33:6
- "prayer in Jewish tradition" → Deuteronomy 6:5-7 (Shema)
- "the prophetic tradition across Bible and Quran" → mixed
- "what do the Bible and Quran both say about the poor" → mixed

Cost: 1 hour (mostly careful curation, since cross-tradition relevance
is harder to score). Worth doing but the per-persona labeling (Gap 1)
is more load-bearing.

### Gap 3: re-run on the new slices

Once Gap 1 + Gap 2 land, re-run the eval against the existing
`data/embeddings/openrouter-3large_{meta.json,vectors.bin}` (the
on-disk 3-large index from 2026-09-19, $0.74 paid for, still there)
and the local `all-MiniLM-L6-v2` index. Compare per-persona and
per-tradition recall@K. Document in `notes/` + a follow-up to
ADR-015.

Cost: 30-60 min once Gap 1 + 2 are in.

## What I am NOT doing (in Option B v2)

- **Not adding 5-10 *new* Sarah queries.** The 33-query set already
  has ~14 Sarah-shaped queries. Adding more would unbalance the set.
  Per-persona *labeling* of the existing queries is the right move;
  not net-new queries.
- **Not regenerating the 3-large index.** It's on disk (22 MB metadata
  + 370 MB vectors) and the user's spend posture is "free-tier
  endpoints only until you're comfortable with spend." The 3-large
  was a one-time $0.74 experiment; rerunning on a slightly different
  query set doesn't need a re-embed.
- **Not changing the eval pass/fail thresholds.** The thresholds in
  `run_eval.py` (`recall@10 >= 0.50` etc.) are aggregate. Per-persona
  thresholds are a separate conversation — most personas will fail
  the aggregate threshold because they're smaller slices. Need to
  think about what "pass" means for a 6-query slice.

## Estimated time

- Gap 1 (persona labels + per-persona eval): 1.5 hours
- Gap 2 (cross-tradition queries): 1 hour
- Gap 3 (re-run + ADR-015 follow-up): 45 min
- CHANGELOG + daily note + commit: 30 min

Total: ~4 hours. "Take your time" per the user. But the user's
typical session is 30 min. I should:

- Land Gap 1 in this session if possible (highest leverage, smallest
  change, opens the new view of the existing 33-query set)
- Document Gap 2 + 3 in this doc as the "next session" list
- Commit Gap 1 separately from Gap 2/3 so each is independently
  shippable

## Why Gap 1 first

The 3-large vs local question is currently answered at the aggregate
level. If I add per-persona labels, the same on-disk index produces
a *new* comparison without any re-embed spend. That's the highest
leverage-to-cost ratio of the three gaps. The cross-tradition queries
(Gap 2) are also valuable but they're net-new queries that need
careful curation; doing them on a separate session lets me focus.

## Plan: do Gap 1 now, hand off Gaps 2+3 to the next session

1. Add `persona` field to each entry in `tests/benchmark.py`'s
   `BENCHMARK` list.
2. Update `scripts/run_eval.py` to compute and report per-persona
   recall@K, MRR, primary@1.
3. Add a sister-script test that asserts every benchmark entry has
   a valid persona label and that every persona label appears in
   the 6-persona list (so a typo is caught).
4. Re-run the eval against the local + 3-large indexes (no re-embed
   needed — both are on disk). Compute the per-persona table.
5. CHANGELOG + daily note + ADR-015 follow-up doc.
6. Commit.

If time runs out, ship after step 3 (data + test landed, no new
analysis). The re-run + ADR-015 follow-up can wait for the next
session; the data work is the part that doesn't change.