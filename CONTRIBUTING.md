# Contributing to Bible LLM Reference

Thanks for your interest. This project is small, single-contributor (today), and built for clarity over speed. Before sending a PR, please read the docs in this order:

1. **[`HANDOFF.md`](./HANDOFF.md)** — the engineering handoff. Vision, current state, conventions, milestone roadmap.
2. **[`HANDOFF.md` §11](./HANDOFF.md#11-runtime-contract-for-any-agent-using-this-data)** — the runtime contract. Any agent that uses this data (including downstream consumers) is bound by these five rules.
3. **[`COUNCIL.md`](./COUNCIL.md)** — the governance constitution. Read before submitting anything that touches doctrinal claims, corpus admission, or scope expansion.
4. **[`docs/governance/council-design.md`](./docs/governance/council-design.md)** — the long-form Council spec, when relevant.

If you have 30 minutes, the [`HANDOFF.md` §10 quick-orientation block](./HANDOFF.md#10-quick-orientation-for-the-next-agent) tells you what to read in what order.

## How to contribute

- **Bug fixes** — open an issue first (template: `.github/ISSUE_TEMPLATE/bug_report.md`) unless the fix is trivial.
- **New translations** — pull request with the new JSON file in `translations/` and a one-line addition to the readme's data-sources table. Verify the schema matches the existing 13 (see `docs/data-schema.md` §1).
- **New lexicon data** — pull request with the new files under `strongs_data/` (or a parallel structure if the lexicon is non-Abrahamic). Update the readme's data-sources table. Strong's is CC-BY-SA; new lexica must carry their own license.
- **Schema changes** — read [`HANDOFF.md` §7.1](./HANDOFF.md#71-data-layer-constraint-all-traditions-capable) first. The data layer is the only Phase 1 design surface Phase 3 depends on. Schema changes go through the field-map bump process (see `merger/config/field_map.yaml` patterns in the Religion & Spirituality AI upstream project).
- **Council-related contribution** — anything that touches doctrinal claims, model behavior, or scope expansion requires Council review per `COUNCIL.md` §3. Open an issue first; don't send a PR directly.

## Conventions

- **Commits** — Conventional Commits (`feat(scope):`, `fix(scope):`, `chore:`, `docs:`). One logical change per commit.
- **Branches** — `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`. One branch per concern.
- **Pull requests** — fill out the template at `.github/PULL_REQUEST_TEMPLATE.md`. Reference the relevant doc section in the body.
- **Daily notes** — if you're working on the project daily, write a `notes/YYYY-MM-DD.md` with the Done / Blocked / Tomorrow / Decisions sections described in `HANDOFF.md` §5.

## Code style

- Python 3.9+ (per `pyproject.toml`).
- Stdlib-only where possible. The current tools (`bible-query.py`, `convert_strongs_to_json.py`, `make_flat_training.py`) use only the standard library. Adding a dependency is a Mile-3 decision (see `HANDOFF.md` §5 Milestone 3), not a default.
- Type hints on public functions.
- Docstrings on modules.
- One file per concern. Don't bloat `__init__.py`.
- No AI/ML calls in the runtime beyond what's explicitly designed in. This is a deterministic reference tool, not a chat surface.

## What we don't want

- **Do not anthropomorphize.** The runtime contract (rule 5) is explicit: the system outputs structured reference text, never "I am speaking as Scripture." PRs that violate this will be rejected.
- **Do not introduce a comparative-theology engine.** Phase 1 is Christian-corpus-only by design. Phase 3 is multi-tradition, but the framing is "represent each tradition faithfully on its own terms," not "compare them in a normative judgment." Comparative features go through Council review.
- **Do not commit real employee / customer / sacred-text data.** Data sources are public domain or CC-BY-SA; verify before adding a new source.
- **Do not introduce a non-public-domain translation without Council approval.** Most modern translations (NIV, NASB, ESV, NKJV) are not public domain. We don't accept them.

## Triage

- Issues are triaged by the project owner (today: "father"). Response time is best-effort.
- PRs that touch the runtime contract, data schema, or governance documents require Council sign-off per `COUNCIL.md` §3.
- Security issues — see [`SECURITY.md`](./SECURITY.md). Do not open a public issue for security problems.

## License

By contributing, you agree that your contributions are licensed under the project's MIT license (see [`LICENSE`](./LICENSE)). If you contribute to the Strong's-derived lexicon section, that portion is CC-BY-SA — the license carries forward.

## Be respectful

This is a public repo. Be respectful in issues, PRs, and reviews. The subject matter — religious texts, traditions, and practices — is one where people have deeply held, sometimes divergent, convictions. The Council's principle #2 (no tradition is treated as the default) applies to project discussion too.
