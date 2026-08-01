# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the Python package (per `pyproject.toml`).

## [Unreleased]

### Added
- `HANDOFF.md` — engineering handoff (vision, state, conventions, milestone roadmap).
- `COUNCIL.md` — governance constitution (short stub).
- `docs/data-schema.md` — parallel-structure schema for multi-tradition support.
- `docs/governance/council-design.md` — long-form Council spec (agent roster, decision protocol, scoping guardrails).
- `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` (this file), `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`.
- Runtime contract for any agent using this data — see `HANDOFF.md` §11.

### Changed
- `README.md` rewritten to reflect the project's current vision, scope, and what's in the repo. The old framing ("Bible Q&A dataset + tool") is replaced with the Religion & Spirituality AI substrate framing.
- `agents.md` (the 2026-07-31 Grok runtime contract) absorbed into `HANDOFF.md` §11. The file is removed; the contract is the canonical section of the engineering handoff.

### Removed
- `agents.md` (lowercase). The runtime contract survives in `HANDOFF.md` §11.

## [0.1.0] — 2026-07-31

### Added
- `bible-query.py` upgraded with exact reference parsing (book, chapter, verse, ranges), keyword search with multi-word scoring, Strong's enrichment on demand, JSON output, and an LLM-ready context block.
- `convert_strongs_to_json.py` — converts Open Scriptures Strong's `.js` files to clean JSON.
- `make_flat_training.py` — produces a JSONL for embedding / training.
- `LICENSE` (MIT).
- `pyproject.toml` — packaging metadata.
- `agents.md` — runtime contract for any agent using this data (later absorbed into `HANDOFF.md` §11).

### Notes
- This is the "Grok upgrade" commit (`61c9f0a`). Distinguished from the prior initial commit by the addition of the `bible-query` rewrite and the supporting tooling.

## [0.0.1] — 2026-07-31

### Added
- Initial commit (`42b9996`).
- `kjv.json` — King James Version (1769) with embedded Strong's tags.
- `translations/*.json` — 12 additional translations (YLT, WEB, GNV, DRB, RSV, LUT, SYNOD, RV1960, CUV, UKRK, TISCH, LXX, WLCa).
- `strongs_data/hebrew/` — H1–H8674 (8,674 entries).
- `strongs_data/greek/` — G1–G5624 (5,624 entries).
- `bible-query.py` (v0) — basic keyword search.
- `normalize.py`, `normalize_all.py` — JSON normalization utilities.
- `README.md` — initial framing.

---

## Versioning notes

- **Pre-1.0 versions** are pre-stabilization. Breaking changes are possible between minor versions.
- **1.0** ships when Milestone 1 (multi-translation lookup, `HANDOFF.md` §5) lands.
- **The data schema** is versioned independently in `docs/data-schema.md`. Schema changes go through the field-map bump process and require Council review.
- **The governance documents** (`COUNCIL.md`, `docs/governance/council-design.md`) version per their own embedded version history, not the Python package version.
