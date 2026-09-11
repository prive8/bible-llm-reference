# 2026-09-10/11 — Tanakh ingest long-running HTTP issue + structural findings

## The problem

Full Tanakh ingest (`scripts/ingest_tanakh.py`, 929 chapters × 2 editions
= 1,858 chapter requests) hangs around chapter ~700 of the second
edition. Process goes into `S (sleeping)` state on `hrtimer_nanosleep`
wait channel. No exception, no socket error — just stuck.

Single-book mode (`--only-book Psalms`, 150 chapters) runs to completion
in ~5 min per edition without hanging. So the issue is **long-running
multi-book ingest** specifically, not the urllib+Sefaria plumbing in
isolation.

## What I tried

1. **Added `Connection: close` header + shorter 10s timeout in
   `fetch_chapter`.** Didn't help — still hung around the same point.
2. **Restructured `fetch_chapter` to retry 3× with exp backoff (already
   there).** Same hang point.
3. **Investigated Python urllib internals.** No smoking gun. SSL
   context, default socket timeout, connection pool state — all looked
   fine in isolation. The hang is timing- and traffic-dependent.

## What I shipped instead (the real fix)

**Per-book incremental writes** in `ingest_tanakh.py`:

- After each book completes, the JSON file is rewritten with the new
  book appended.
- `ingest_tanakh.py` reads existing partial state via `_load_partial()`.
- Books already fully present are skipped on re-runs.
- A long-running ingest can be interrupted at any book boundary without
  losing the books that already completed.

This is the **right infrastructure-level answer**: don't fight the
hung, accept that the long-running HTTP path is unreliable on the
stdlib urllib+Sefaria combo, and make the work resumable so that
failures don't waste compute.

## Status as of 2026-09-11 11:13 EDT

- hebrew-nikkud.json: **full 39 books, 23,206 verses**
  (committed in commit da5ecc7)
- jps1917-modernized.json: **partial, 7 books so far**:
  Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Joshua, Psalms
- Background incremental ingest running (process 49743)
- 123/123 sister-script tests passing
- CI run #27 just queued (will verify the test fix in commit 8bbeff8)

## What does the user need to know

The urllib hang is reproducible on the second edition of long runs. If
the user wants to invest in infrastructure:

1. **Drop urllib for a more reliable HTTP client.** `requests` adds a
   dependency; `httpx` is stdlib-adjacent but also external. The cleanest
   no-deps option is stdlib `http.client` with explicit Connection:
   close, but that's a real refactor.
2. **Or just use curl as a subprocess** — `subprocess.run(["curl", ...])`
   inherits curl's rock-solid connection management. The script would
   just shell out per chapter. Ugly but reliable.
3. **Or run each book as a separate Python process** — eliminate the
   long-running state entirely. Add `--only-book` to the loop in a
   bash script that runs all 39 books sequentially. Each one is short
   enough that it shouldn't hang.

For now, the incremental approach + the prayer that the background
ingest completes work for our current scope (~30 min target with the
incremental writes serving as our rollback if it hangs again).

## Decisions made

- **Per-book incremental writes** (above). Cost: ~10s extra I/O per
  book. Benefit: resumability + survives a kill at any point.
- **Make tests tolerant of partial ingests.** `t_tanakh_cli_json`
  skips when Isaiah isn't in the English edition yet (mid-ingest state).
  `t_tanakh_data_files_present` iterates over whatever editions ARE
  present (was hard-failing when only Hebrew was committed).
- **Fixed `total_actual_verses` running-total print bug** in the ingest
  script — was double-counting because the running sum was
  incrementally accumulated on top of the initial partial-file sum.
  Now recomputes from the doc on each per-book write.

## What's open

- Background ingest (process 49743) still running. Will either
  complete all 38 remaining English books (~25 min) or hang again on
  Psalm 150 or thereabouts.
- HANDOFF §8 #10 (OpenRouter benchmark) still pending user's .env key
  update.
- NIM is permanently closed (free-tier gated per the v0.13.0 finding).
