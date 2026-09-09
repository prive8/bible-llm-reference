# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the Python package (per `pyproject.toml`).

## [Unreleased]

## [0.2.0] — 2026-09-09

### Added
- `tests/run_all.py` — sister-script test runner (stdlib-only, no pytest). 20 tests covering reference parser, KJV loading, translation enumeration, parallel lookup, Strong's CLI, and legacy-script regression. Run via `python3 tests/run_all.py`.
- `docs/design-decisions.md` — six ADRs capturing the architectural decisions made since the Grok upgrade: stdlib-only, multi-tradition constraint, Strong's-as-JS, legacy CLI deprecation, sister-script tests, and the book-resolution fuzzy-match removal.
- `docs/evaluation.md` — shell document defining what we measure (and explicitly what we don't) at each milestone.
- `notes/2026-09-09.md` — daily journal entry (see HANDOFF.md §7.2).

### Changed
- `bible/lookup.py::resolve_book_name` — removed fuzzy substring fallback that incorrectly resolved `1jn` to `John` instead of `1 John`. Added `1jn`/`2jn`/`3jn` no-space aliases.
- `pyproject.toml` version bumped to `0.2.0`. `[project.scripts]` exposes `bible` (the new package CLI), not `bible-query`.

### Fixed
- `bible-query.py --strongs` — previously inlined lemma + gloss into the English text, producing unreadable output ("Forבִּכּוּרָה…Godחֲדַר…"). Now strips Strong's tags from the English line and prints Strong's references as a separate block. `python -m bible parallel --strongs` remains the canonical output path.
- `tests/run_all.py` — exposes the regression test for the `--strongs` bug above so it can't silently come back.

### Deprecated
- `bible-query.py` is now legacy. Use `python -m bible parallel ...` / `python -m bible strongs ...`. Will be removed when Milestone 3 (semantic search) lands the `bible search` command.

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
