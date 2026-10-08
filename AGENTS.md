# AGENTS.md — start here

Short entry point for AI agents. Authoritative detail lives in the
linked docs; this file only says what to read, what binds you, and
what to work on.

## Read in this order
1. [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) — five rules that bind any agent using this data (always cite, never invent verses, never impersonate Scripture, surface Strong's, surface internal diversity).
2. [`COUNCIL.md`](./COUNCIL.md) §2 — seven non-negotiable principles (neutral across traditions, primary sources first).
3. [`HANDOFF.md`](./HANDOFF.md) — vision, state, conventions. Start with "Current priorities".
4. [`docs/foundation-plan.md`](./docs/foundation-plan.md) — the active plan.
5. Latest file in `notes/` — where the last session stopped.

## Current priorities (2026-10-08)
1. **F0a** — Judaism is indexed as Hebrew in an English-only embedder; index from `jps1917-modernized`.
2. **F0b** — licence audit of translations (several are labelled public domain but likely aren't).
3. **F1–F4** — passage model, canonical IDs, versification map; route core commands through a tradition registry.
4. Do **not** start new embedder bake-offs, new traditions, or Phase 2 training until F4 lands.

## Commands
```bash
python tests/run_all.py                 # must print: N passed, 0 failed (137 at last count)
python -m bible parallel "John 3:16"    # Bible only today; see foundation plan
python scripts/run_eval.py              # ~3 min on CPU; needs a local index
```

## Conventions
- Base runtime is **stdlib-only**; optional deps live behind extras (ADR-001).
- Raw corpus files are read-only; add data via an ingest script (HANDOFF §7.5).
- No secrets in the repo; read keys from the environment.
- Conventional Commits; one logical change per commit; add `notes/YYYY-MM-DD*.md` per session (Done / Blocked / Tomorrow / Decisions).
- Never put LLM-generated text into outputs presented as scripture, citations, or glosses.
- Embeddings under `data/embeddings/` are gitignored and may be absent; don't assume they exist.
- Update `CHANGELOG.md` for any public API or data change.
