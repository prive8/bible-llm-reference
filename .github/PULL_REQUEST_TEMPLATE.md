---
name: Pull request
about: Submit a change to the Bible LLM Reference
title: ''
labels: ''
assignees: ''
---

## What this PR does

<!-- One paragraph. -->

## Related issues

<!-- `Fixes #N`, `Closes #N`, or `Related to #N`. -->

## Affected docs

<!-- Which docs in this repo (if any) does this change? -->

- [ ] `README.md`
- [ ] `AGENTS.md`
- [ ] `COUNCIL.md`
- [ ] `docs/data-schema.md`
- [ ] `docs/governance/council-design.md`
- [ ] `CHANGELOG.md` (if user-facing change)
- [ ] None

## Affected milestones

<!-- Name the area of the repo this touches. Status lives in README.md. -->

- [ ] Milestone 0 — repo hygiene
- [ ] Milestone 1 — multi-translation lookup
- [ ] Milestone 2 — Strong's integration
- [ ] Milestone 3 — semantic search
- [ ] Milestone 4 — cross-reference engine
- [ ] Milestone 5 — packaging + tests
- [ ] None of the existing milestones (this is a new milestone, or doc-only)

## Requires Council review

<!-- Per `COUNCIL.md` §3, anything that touches doctrinal claims, model behavior, or scope expansion needs Council sign-off. -->

- [ ] This PR touches doctrinal claims (Council review required)
- [ ] This PR touches model behavior (Council review required)
- [ ] This PR touches scope expansion (Council review required)
- [ ] This PR is data-only / tooling / docs (no Council review needed)

## Runtime contract

<!-- The runtime contract in `RUNTIME_CONTRACT.md` governs any agent that uses this data. If this PR changes the surface that agents see, the contract may need updating too. -->

- [ ] I have reviewed the runtime contract and this PR is consistent with it
- [ ] This PR changes the runtime contract (explain in the body)

## Checklists

- [ ] I have read [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md)
- [ ] I have run `python3 tests/run_all.py` and it prints `N passed, 0 failed`
- [ ] I have not modified `kjv.json` or `translations/*.json` directly
- [ ] I have followed Conventional Commits in the commit message
- [ ] I have added a `notes/YYYY-MM-DD.md` entry if this is part of a daily cadence

## Anything else

<!-- Anything else that might help — screenshots, related projects, breaking changes, etc. -->
