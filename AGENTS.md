# AGENTS.md

Coding agents start here, then read [`README.md`](./README.md) for what the repo is, the retrieval gates, and the 2026-10-25 direction.

## What binds you

1. [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) — always cite, never invent verses, never impersonate Scripture, surface Strong's, surface internal diversity.
2. [`COUNCIL.md`](./COUNCIL.md) §2 — neutral across traditions, primary sources first.

## What to work on next

This is the only work queue in the repo.

1. The fleet to-do board: `shared/TODO.md` in the private vault `prive8/obsidian-vault-shared`. The vault is private; this file only records the path.
2. The latest file in [`notes/`](./notes/). Session notes use Done / Blocked / Tomorrow / Decisions. The retrieval-gate note is [`notes/2026-10-25-ci-eval-regression-restored.md`](./notes/2026-10-25-ci-eval-regression-restored.md).

[`HANDOFF.md`](./HANDOFF.md) points here and at the README. [`docs/foundation-plan.md`](./docs/foundation-plan.md) is the 2026-10-08 review. The work queue is the list above.

## Commands

```bash
python tests/run_all.py              # must print: N passed, 0 failed (155 on 2026-10-25)
python -m bible parallel "John 3:16"
```

Local retrieval gates need a built index. Commands are in the README section "Run the gates locally" (`scripts/run_eval.py`, then `scripts/eval_gate.py`).

## Conventions

- Base runtime is stdlib-only; optional deps live behind extras ([ADR-001](./docs/design-decisions.md)).
- Raw corpus files are read-only. Add data with an ingest script. Embeddings under `data/embeddings/` are gitignored and may be absent.
- No secrets in the repo. Read keys from the environment.
- Conventional Commits. One logical change per commit. Add `notes/YYYY-MM-DD*.md` per session (Done / Blocked / Tomorrow / Decisions).
- Never put model-generated text into outputs presented as scripture, citations, or glosses.
- Update `CHANGELOG.md` for a public API or data change.
