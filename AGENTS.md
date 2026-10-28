# AGENTS.md

Coding agents start here, then read [`README.md`](./README.md) for what the repo is, the retrieval gates, and the 2026-10-25 direction.

## What binds you

1. [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) — always cite, never invent verses, never impersonate Scripture, surface Strong's, surface internal diversity.
2. [`COUNCIL.md`](./COUNCIL.md) §2 — neutral across traditions, primary sources first.

## What to work on next

This is the only work queue in the repo.

1. dad-h2, assigned by solomon-grokbot (PM) on 2026-10-28. Make OpenAI `text-embedding-3-large` the default embedder.
   - Decision: Steven chose OpenAI text-embedding-3-large as the default embedder (resolves the ADR-014 decision brief, [`notes/2026-10-26-adr-014-decision-brief.md`](./notes/2026-10-26-adr-014-decision-brief.md)). Numbers on the v2 cross-tradition dev gate: qwen3-8b 0.321 @ ~9.6 s/query, 3-large 0.297 @ ~2.9 s, local MiniLM 0.189 @ ~0.8 s. A qwen3-8b "deep study" mode is not decided.
   - Goal: make 3-large the default; mark ADR-014 Accepted; then pick up the held_out retrieval gate that was waiting on this decision.
   - Acceptance: default config/CLI uses 3-large with a complete (non-truncated) index; ADR-014 Accepted with date and numbers; CI green on all 8 PR jobs (ubuntu+windows, Py3.10-3.13); gate thresholds only raised, or any change justified in the ADR (never loosened to turn red green); ADR-001 stdlib-only respected aside from the existing embedding API path; licensed texts untouched.
   - Files: embedder config/defaults, eval gate scripts/thresholds, ADR-014, README, AGENTS.md.
   - Reminder: update README and AGENTS.md when done, including the stale test count (says 155; dad-h2's 2026-10-26 changelog says 170), and log in the vault. **The test count is now 170 in both README.md and AGENTS.md (dad-h2, 2026-10-28) — that part is done; the remaining AGENTS.md work is the queue entry itself.**
2. The fleet to-do board: `shared/TODO.md` in the private vault `prive8/obsidian-vault-shared`. The vault is private; this file only records the path.
3. The latest file in [`notes/`](./notes/). Session notes use Done / Blocked / Tomorrow / Decisions. The retrieval-gate note is [`notes/2026-10-25-ci-eval-regression-restored.md`](./notes/2026-10-25-ci-eval-regression-restored.md).

[`HANDOFF.md`](./HANDOFF.md) points here and at the README. [`docs/foundation-plan.md`](./docs/foundation-plan.md) is the 2026-10-08 review. The work queue is the list above.

## Commands

```bash
python tests/run_all.py              # must print: N passed, 0 failed (170 on 2026-10-26)
python -m bible parallel "John 3:16"
```

Local retrieval gates need a built index. Commands are in the README section "Run the gates locally" (`scripts/run_eval.py`, then `scripts/eval_gate.py`).

**Before you trust a retrieval number, check the index it came from:**

```bash
python scripts/check_indexes.py      # every index: .bin size vs metadata count
```

Embeddings under `data/embeddings/` are gitignored, so CI never sees
your local indexes — a corrupt one will not be caught by CI. It can be
silently truncated: the 2026-09-19 `text-embedding-3-large` index held
30,159 of 66,689 vectors and was Christianity-only, and it scored 0.344
on the cross-tradition v2 benchmark — the best-looking number in the
embedder comparison, from a broken artifact. A score is only comparable
to another score if the corpus behind it was the same. See
[`notes/2026-10-26-truncated-index-found.md`](./notes/2026-10-26-truncated-index-found.md).

## Conventions

- Base runtime is stdlib-only; optional deps live behind extras ([ADR-001](./docs/design-decisions.md)).
- Raw corpus files are read-only. Add data with an ingest script. Embeddings under `data/embeddings/` are gitignored and may be absent.
- No secrets in the repo. Read keys from the environment.
- Conventional Commits. One logical change per commit. Add `notes/YYYY-MM-DD*.md` per session (Done / Blocked / Tomorrow / Decisions).
- Never put model-generated text into outputs presented as scripture, citations, or glosses.
- Update `CHANGELOG.md` for a public API or data change.
