# 2026-10-08 — F0b: license audit (inventory + decision matrix)

## Done

- **Inventory + decision matrix landed in `LICENCE-AUDIT.md`.** No
  data files were modified. Per the scope agreed at session start,
  the audit produces a per-edition table with current label, the
  audit's own assessment, confidence level, cited source, and
  decision options. The project owner signs off per row; the
  audit does not relabel or remove anything.
- **27 editions catalogued:** KJV + 13 in `translations/`, 6 in
  `data/quran/`, 2 in `data/tanakh/`, 2 in `data/torah/`, Strong's
  Hebrew + Greek, and the cross-references.
- **Risk tiers, by row:**
  - **Clearly public domain in the US, high confidence:** KJV,
    YLT, GNV, DRB, LUT, TISCH, UKRK, WEB, LXX, SYNOD (US-only),
    WLCa, the Septuagint text, the Hebrew nikkud, Strong's
    underlying 1894 text, the Uthmani Arabic.
  - **Clearly copyrighted, high confidence:** RSV (NCC 1952),
    RV1960 (Sociedad Bíblica 1960), Saheeh International (1996),
    Mufti Taqi Usmani (recent), Arberry (1955).
  - **Mixed / needs human review:** CUV (US PD rule applies but
    the foreign-publication facts are non-trivial), Yusuf Ali
    (1934 — first edition likely PD, later revisions not), WLCa
    (underlying text is PD; confirm the specific WLC digital
    edition).
  - **Likely correct as labeled, no change needed:** Strong's
    CC-BY-SA headers, the JPS 1917 Adam Cohn CC-BY editions, the
    openbible.info cross-references (CC-BY 4.0).
- **Conservative posture throughout.** The audit flags rows
  "needs human review" rather than making a final call. The
  default action for each clearly-copyrighted row is "write to
  the source (Tanzil, the Bible societies, etc.) and get an
  explicit answer before changing the data." This is a slower
  path than "remove them now," but it is the path that preserves
  the project's options.

## Blocked

- **Tanzil license check.** The 3 modern Quran translations
  (Saheeh International, Mufti Taqi Usmani, Arberry) all carry
  Tanzil's "Public Domain" label. The audit cannot verify
  Tanzil's current terms from this session (no web-extract
  backend is configured; web-search only). The 1928 and earlier
  translations (Yusuf Ali 1934, Pickthall 1930) are PD in the
  US by the standard rule; the 1955+ ones are not. **Tanzil's
  own translation-license page is the right place to confirm.**
- **CUV copyright status.** The 1919 first edition of the
  Chinese Union Version may or may not be PD in the US depending
  on US-publication facts. The current copyright holder is the
  China Christian Council, which publishes a 2019 revision. Need
  a human check against Copyright Office records.

## Tomorrow (or whenever the owner returns to this)

- **Per-row sign-off.** The owner reads the LICENCE-AUDIT.md
  table and picks an option for each row. The default actions
  in the audit doc are conservative; the owner can pick the
  "remove" option for any clearly-copyrighted row, or the
  "replace" option (with a PD alternative), or the "keep as
  local-use-only" option if the project is local-only.
- **Follow-up: a sister-script test** that asserts every
  `translations/*.json` file has a `license` field once the
  owner signs off. Pinning the contract is the only way to
  prevent the audit from being silently undone by a future
  ingest that re-omits the field. Five-line test, fits in
  `tests/run_all.py`.
- **Follow-up: a README data-sources table rewrite** that
  reflects the per-edition labels, not the aggregate
  "Public domain / fair use" row. The current aggregate row
  is what's at the top of the README today; the per-edition
  breakdown belongs in the table.
- **Follow-up: Tanzil check.** If the project owner has a
  Tanzil contact, that single email resolves the 3 modern
  Quran translations at once.

## Decisions made

- **F0b scope is the audit, not the relabel or removal.** Per
  the owner's choice at session start. The audit doc is
  decision-support, not a decision.
- **Conservative labels in the audit doc.** Where the
  evidence is unclear (CUV, Yusuf Ali, WLCa), the audit
  says so explicitly. The doc does not claim certainty
  beyond what the evidence supports.
- **No web-fetch in this session.** The web-extract backend
  is not configured; web-search results returned only
  generic search-result titles, not content. The audit
  relies on (a) the project's own existing labels and
  (b) well-established facts about translation publication
  dates and US copyright rules. Where the project owner
  needs a URL-citable fact, they can re-run the audit
  with a configured web-extract backend.
- **No CHANGELOG entry yet.** Per the audit-only scope, the
  CHANGELOG will get its entry when the relabel / removal
  work lands. A "F0b audit complete" entry at this stage
  would invite a future contributor to think the work is
  done when it isn't.
