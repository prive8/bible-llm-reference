# The 3-large index was truncated — and it was scoring the best — 2026-10-26

## What was found

While measuring per-query latency for each candidate embedder, the
3-large arm reported **30,159** index entries where its metadata
claimed 66,689. The index was not what its own metadata said it was.

```
$ python -c "check each index's .bin size against its meta count"
  default              meta= 66689 dim=  384   OK        (100.0% present)
  openrouter-3large    meta= 66689 dim= 3072   TRUNCATED ( 45.2% present)
  openrouter-qwen3-8b  meta= 66689 dim= 4096   OK        (100.0% present)
```

The 3-large `.bin` is 370,601,984 bytes. At 3072 float32s per vector
that is **30,159 vectors — 36,530 missing**.

**And those 30,159 are not a random subset.** The corpus is collected
Christianity-first, so the surviving vectors are the first 30,159
Christian passages:

| index | metadata says | actually queryable | traditions actually present |
|---|---|---|---|
| 3-large | 66,689 | 30,159 | **Christianity only** |
| qwen3-8b | 66,689 | 66,689 | Christianity + Islam + Judaism |
| MiniLM | 66,689 | 66,689 | Christianity + Islam + Judaism |

**So the 3-large "0.344 semantic on v2 dev" from yesterday's write-up
was measured against a Christianity-only index.** v2 is the
cross-tradition benchmark — its expected citations span all three
traditions. A 0.344 that looks like *beating* qwen3-8b's 0.321 is
actually a score from an index that could not retrieve a single Quran
or Tanakh passage at all.

## Root cause

`git show 21f77eb:scripts/index_embeddings.py` — the indexer as it was
at the 2026-09-19 build:

```python
save_vector_index(EMBEDDINGS_DIR, args.name, corpus, vectors, dim)
```

`corpus` is the full 66,689-passage list. `vectors` is whatever the
build actually produced before it stopped. The old `save_vector_index`
wrote `"count": len(metadata)` into `meta.json` and wrote only
`len(vectors)` vectors into the `.bin` — **with no check that the two
agreed.** The build died partway (the note records 26 min of work and
a 370 MB file, which is exactly the truncated size), and the metadata
was written for the full corpus regardless.

This predates the checkpointing fix (`b987405`, 2026-10-07), which
added `--resume`/`--overwrite` and per-batch appends. The checkpointing
fix addressed losing work on a crash; it did not address the metadata
lying about what was saved.

## Why it went unnoticed for a month

Three things had to fail at once:

1. **The loader degraded silently.** `load_vector_index` read vectors
   in a `for _ in range(count)` loop with a `break` on a short read.
   A short file produced a short list, and nothing said so.
2. **The benchmark's own numbers looked plausible.** 0.344 is in the
   same range as the other embedders' scores, so it read as "3-large
   is good" rather than "3-large's index is broken."
3. **The v1 benchmark is 100% Bible.** The 2026-09-19 note scored
   3-large on the v1 39-query benchmark, whose expected citations are
   all Bible — so a Christianity-only index scored *well* on it. The
   truncation was invisible in the one measurement that was taken.

Only running it on **v2**, the cross-tradition benchmark, exposed it.

## The fix

Two guards, both in `bible/semantic.py`:

1. **`save_vector_index` now refuses to write a mismatched index.**
   If `len(metadata) != len(vectors)`, it raises `ValueError` before
   touching the filesystem. A corrupt index cannot be created.
2. **`_load_vector_index_flat` now warns when the file is short.** It
   still degrades to the data that is actually there — a truncated file
   should not be fatal — but it prints a warning naming both counts
   and stating that scores against it are not comparable to a
   full-corpus index.

Two new sister-script tests (162 → 164):

- `t_save_vector_index_rejects_metadata_vector_mismatch` — both
  directions (too many metadata entries, too few) raise, no partial
  files are left behind, and equal counts still round-trip.
- `t_semantic_truncated_index_warns_loudly` — a truncated `.bin` loads
  the partial data AND emits a warning naming both counts.

## What this changes about yesterday's numbers

Yesterday's table:

| v2 split | MiniLM | 3-large | qwen3-8b |
|---|---|---|---|
| dev (48q) | 0.189 | **0.344** | 0.321 |
| held_out (42q) | 0.106 | **0.283** | 0.255 |

**The 3-large column is void.** Both its numbers were computed against
a Christianity-only index. Its held_out number (0.283) is likewise
uninterpretable — it beat qwen3-8b's full-corpus 0.255 while being
able to retrieve nothing from two of the three traditions.

The valid comparison is now:

| v2 split | MiniLM | qwen3-8b |
|---|---|---|
| dev (48q) | 0.189 | 0.321 |
| held_out (42q) | 0.106 | 0.255 |

qwen3-8b still beats the local default by a wide margin on both splits,
and that conclusion is unaffected — it was measured on a complete
index.

**3-large may still be the better embedder.** Its dev score of 0.344 on
a Christianity-only index is not a measurement of 3-large's quality at
all, in either direction. Rebuilding it is the only way to find out,
and that is a paid build (~$0.74 for the full 66,689 at 3-large's
2026-09-19 rate, or ~$1.10 for the chunked corpus).

## The lesson worth keeping

**A score is only comparable to another score if the corpus behind it
was the same.** The eval harness checks the benchmark, the corpus
files, and the scorer — and all three were identical across every arm
in yesterday's comparison. The thing it did not check was the
*integrity of the artifact being scored*. BM25 being identical across
runs was the internal control that proved the benchmark was unchanged;
it said nothing about the vector index, because BM25 does not read one.

Two habits that would have caught this:

- **Check the artifact, not just the harness.** The `.bin` size against
  the meta count is a one-line check. Run it before trusting any number
  an index produced.
- **Score a new index on the benchmark that matches its corpus.** The
  v1 benchmark is 100% Bible; scoring a possibly-Bible-only index
  against it hides the fault. v2 caught it.
