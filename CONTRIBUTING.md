# Contributing to Bible LLM Reference

Thanks for your interest. This project is small, single-contributor (today), and built for clarity over speed. Before sending a PR, please read the docs in this order:

1. **[`README.md`](./README.md)** — what the repo is, the retrieval gates, and the current direction.
2. **[`AGENTS.md`](./AGENTS.md)** — what to work on next (the fleet to-do board and `notes/`), plus the commands and conventions.
3. **[`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md)** — five rules for any agent that uses this data.
4. **[`COUNCIL.md`](./COUNCIL.md)** — the governance constitution. Read before submitting anything that touches doctrinal claims, corpus admission, or scope expansion.
5. **[`docs/governance/council-design.md`](./docs/governance/council-design.md)** — the long-form Council spec, when relevant.

## How to contribute

- **Bug fixes** — open an issue first (template: `.github/ISSUE_TEMPLATE/bug_report.md`) unless the fix is trivial.
- **New translations** — pull request with the new JSON file in `translations/` and a one-line addition to the readme's data-sources table. Verify the schema matches the existing translations (see `docs/data-schema.md` §1 and `data/editions.json`).
- **New lexicon data** — pull request with the new files under `strongs_data/` (or a parallel structure if the lexicon is non-Abrahamic). Update the readme's data-sources table. Strong's is CC-BY-SA; new lexica must carry their own license.
- **Schema changes** — follow `bible/registry.py`, `data/editions.json`, and `docs/data-schema.md`. Corpus admission goes through Council review per `COUNCIL.md` §3.
- **Council-related contribution** — anything that touches doctrinal claims, model behavior, or scope expansion requires Council review per `COUNCIL.md` §3. Open an issue first; don't send a PR directly.

## Conventions

- **Commits** — Conventional Commits (`feat(scope):`, `fix(scope):`, `chore:`, `docs:`). One logical change per commit.
- **Branches** — `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`. One branch per concern.
- **Pull requests** — fill out the template at `.github/PULL_REQUEST_TEMPLATE.md`. Reference the relevant doc section in the body.
- **Daily notes** — if you're working on the project daily, write a `notes/YYYY-MM-DD.md` with Done / Blocked / Tomorrow / Decisions (see `AGENTS.md`).

## Code style

- Python 3.9+ (per `pyproject.toml`).
- Stdlib-only where possible. The `bible/` package and the ingest scripts use the standard library. Embedding libraries are an optional extra (`pip install -e ".[embeddings]"`), not a default import. See ADR-001 in `docs/design-decisions.md`.
- Type hints on public functions.
- Docstrings on modules.
- One file per concern. Don't bloat `__init__.py`.
- No model calls in the runtime beyond the retrieval paths that already exist. This is a deterministic reference tool.

## What we don't want

- **Do not anthropomorphize.** The runtime contract (rule 5) is explicit: the system outputs structured reference text, never "I am speaking as Scripture." PRs that violate this will be rejected.
- **Do not introduce a normative comparison engine.** Traditions are represented on their own terms (`COUNCIL.md` §2). Comparative features go through Council review.
- **Do not commit secrets or unlicensed text.** Data sources carry their own licenses; verify before adding a source. The five non-redistributable editions are under the owner's review (`LICENCE-AUDIT.md`).
- **Do not introduce a non-public-domain translation without Council approval.** Most modern translations (NIV, NASB, ESV, NKJV) are not public domain. We don't accept them.

## Triage

- Issues are triaged by the project owner (today: "father"). Response time is best-effort.
- PRs that touch the runtime contract, data schema, or governance documents require Council sign-off per `COUNCIL.md` §3.
- Security issues — see [`SECURITY.md`](./SECURITY.md). Do not open a public issue for security problems.

## License

By contributing, you agree that your contributions are licensed under the project's MIT license (see [`LICENSE`](./LICENSE)). If you contribute to the Strong's-derived lexicon section, that portion is CC-BY-SA — the license carries forward.

## Be respectful

This is a public repo. Be respectful in issues, PRs, and reviews. The subject matter — religious texts, traditions, and practices — is one where people have deeply held, sometimes divergent, convictions. The Council's principle #2 (no tradition is treated as the default) applies to project discussion too.
