# AGENTS.md

Coding agents start here, then read [`README.md`](./README.md) for what the repo is, the retrieval gates, and the 2026-10-25 direction.

## What binds you

1. [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) — always cite, never invent verses, never impersonate Scripture, surface Strong's, surface internal diversity.
2. [`COUNCIL.md`](./COUNCIL.md) §2 — neutral across traditions, primary sources first.

## What to work on next

This is the only work queue in the repo.

1. dad-h2, assigned by solomon-grokbot (PM) on 2026-10-30, approved by Steven. Automated 3-large quality check in CI.
   - Goal: The shipped default embedder (`text-embedding-3-large`, ADR-016) currently has no automated quality-regression check, because CI has no API key and only gates the local MiniLM profile. Steven has now added the repository secret `OPENROUTER_API_KEY` (Settings → Secrets → Actions). Add a separate GitHub Actions workflow that runs the 3-large retrieval gates (dev and held_out, using the thresholds in `config/retrieval_gates.json`) with that secret.
   - Triggers: `workflow_dispatch` (manual) plus a weekly schedule. Do NOT add it to the per-push CI matrix.
   - Cost: keep spend small. Avoid rebuilding the full 3-large index on every run if possible (for example, cache it with actions/cache or reuse a stored artifact). Document the per-run cost you measure.
   - Safety: if the secret is missing (forks, etc.), the job should skip with a clear message, not fail. Never print the key. Don't lower any threshold.
   - Acceptance: one manual dispatch runs green on main, with the run linked in the commit or notes. The existing 9 CI jobs are unchanged and still green. ADR-001 (standard library only for the package code) is respected. The licensed texts are untouched.
   - Files: `.github/workflows/` (new workflow file), possibly `scripts/` or eval tooling, `config/retrieval_gates.json` (read only), README/docs.
   - Reminder: update the README and AGENTS.md (the standing note about the default embedder and `OPENROUTER_API_KEY`) to describe the new check and how to run it, then close this queue item.
2. ~~dad-h2, assigned by solomon-grokbot (PM) on 2026-10-28. Make OpenAI `text-embedding-3-large` the default embedder.~~ **DONE 2026-10-28 by dad-h2** — commits `fb95601`, `fad4c0f`, `a1ece75`. See [ADR-016](./docs/design-decisions.md) and [`notes/2026-10-28-default-embedder-3large.md`](./notes/2026-10-28-default-embedder-3large.md).
   - Decision: Steven chose OpenAI text-embedding-3-large as the default embedder (resolves the ADR-014 decision brief, [`notes/2026-10-26-adr-014-decision-brief.md`](./notes/2026-10-26-adr-014-decision-brief.md)). Numbers on the v2 cross-tradition dev gate: qwen3-8b 0.321 @ ~9.6 s/query, 3-large 0.297 @ ~2.9 s, local MiniLM 0.189 @ ~0.8 s. A qwen3-8b "deep study" mode is not decided — **and was not built**.
   - Outcome: the default embedder is `openai/text-embedding-3-large` (3072-dim, index `openrouter-3large`), recorded as **ADR-016** (Accepted 2026-10-28, Steven as acting chair per `COUNCIL.md` §6.1), which supersedes ADR-014. The free offline MiniLM index stays reachable as `--profile local`, and that is what CI builds and gates. Embedder profiles bind backend, model, index, and dimension together, and a query embedder whose width disagrees with the index now raises instead of silently truncating.
   - Acceptance met: default config/CLI uses 3-large with a complete (non-truncated) index; ADR-016 Accepted with date and numbers; CI green on all 8 matrix jobs (ubuntu+windows, Py3.10-3.13) and on the `eval-regression` job — run `40766844172`; thresholds only raised, or justified in the ADR (never loosened to turn red green); ADR-001 stdlib-only respected aside from the existing embedding API path; licensed texts untouched. **179 tests pass, 0 fail.**
   - Files: embedder config/defaults, eval gate scripts/thresholds, ADR-016, README, AGENTS.md.
   - Follow-on: the `held_out` retrieval gate shipped with it as `local/v2-held_out`, with thresholds derived from the **held_out** baselines (0.092 / 0.106 / 0.115) rather than copied from the dev gate. The `3large` gates are configured but not run by default CI — CI has no embedding-API credential.
3. The fleet to-do board: `shared/TODO.md` in the private vault `prive8/obsidian-vault-shared`. The vault is private; this file only records the path.
4. The latest file in [`notes/`](./notes/). Session notes use Done / Blocked / Tomorrow / Decisions. The default-embedder note is [`notes/2026-10-28-default-embedder-3large.md`](./notes/2026-10-28-default-embedder-3large.md); the retrieval-gate note is [`notes/2026-10-25-ci-eval-regression-restored.md`](./notes/2026-10-25-ci-eval-regression-restored.md).

[`HANDOFF.md`](./HANDOFF.md) points here and at the README. [`docs/foundation-plan.md`](./docs/foundation-plan.md) is the 2026-10-08 review. The work queue is the list above.

## Commands

```bash
python tests/run_all.py              # must print: 179 passed, 0 failed (2026-10-28)
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

**The default embedder is `openai/text-embedding-3-large`** (ADR-016), so
`bible semantic` needs an `OPENROUTER_API_KEY` and a built 3072-dim index.
The offline `all-MiniLM-L6-v2` index is `--profile local` — free, and what
CI builds and gates. An embedder and the index it scores are one choice:
profiles bind backend, model, index, and dimension together, and a query
embedder whose width disagrees with the index raises `DimensionMismatchError`
rather than silently scoring the first N dimensions.

## Conventions

- Base runtime is stdlib-only; optional deps live behind extras ([ADR-001](./docs/design-decisions.md)).
- Raw corpus files are read-only. Add data with an ingest script. Embeddings under `data/embeddings/` are gitignored and may be absent.
- No secrets in the repo. Read keys from the environment.
- Conventional Commits. One logical change per commit. Add `notes/YYYY-MM-DD*.md` per session (Done / Blocked / Tomorrow / Decisions).
- Never put model-generated text into outputs presented as scripture, citations, or glosses.
- Update `CHANGELOG.md` for a public API or data change.
