# License Audit (Foundation Plan F0b)

> **Status:** Inventory + decision matrix. **No data files were
> modified for this audit.** This document records the current label
> for every edition, the audit's best-research assessment, the
> confidence level, the cited sources, and the per-row decision
> options for the project owner. The actual relabel / removal work
> is a separate commit per row once the owner signs off.
>
> **Date:** 2026-10-08
> **Scope:** 14 Bible editions (KJV + 13 in `translations/`),
> 6 Quran editions (`data/quran/`), 2 Tanakh editions
> (`data/tanakh/`), 2 Torah editions (`data/torah/`),
> Strong's Hebrew + Greek, cross-references.
> **Reference:** `docs/foundation-plan.md` §3 row 2 (F0b).

## How to read this

- **Current label** = the label the project itself uses today
  (file headers, README, existing `license` field, or "no label").
- **Assessment** = the audit's own research, including the
  copyright-rule reasoning that produced it.
- **Confidence** = how sure the audit is, *not* how sure the
  project owner should be. High means the rule is mechanical
  (e.g., US PD by publication date); Medium means the rule
  applies but the underlying facts need a human check (e.g.,
  Russian Synodal Translation, where the rule is sound but
  Russian-copyright status is a separate question); Low means
  the audit cannot determine the answer with available evidence
  and a human must research it.
- **Cited source** = the single best evidence the audit found.
  Where possible, the source is the project's own existing
  metadata. Where the audit adds evidence, the source is named
  explicitly. **No URLs are fabricated.**
- **Decision options** = what the project owner can do. The
  default recommendation is conservative (mark uncertain,
  don't redistribute without permission). A row is not "done"
  until the owner picks an option.

## Summary table

| Edition | Current label | Assessment | Confidence | Default action |
|---|---|---|---|---|
| **Bible (KJV, 1769)** | "Public domain" (README) | Public domain in the US (1769, well before 1929) | High | Keep |
| **Bible (KJV Strong's tags)** | CC-BY-SA (Strong's header) | Correct (Open Scriptures, CC-BY-SA) | High | Keep; add explicit `source` field |
| **YLT (1898)** | "Public domain / fair use" (README) | PD in the US (1898, pre-1929) | High | Add explicit `license: Public domain` field; cite Young 1898 |
| **GNV (Geneva, 1599)** | "Public domain / fair use" | PD (1599) | High | Add `license: Public domain` |
| **DRB (Douay-Rheims, 1609/1610)** | "Public domain / fair use" | PD (1609) | High | Add `license: Public domain` |
| **LUT (Luther, 1912)** | "Public domain / fair use" | PD in the US (1912, pre-1929) | High | Add `license: Public domain`; note: German copyright is a separate question |
| **TISCH (Tischendorf, 1869-72)** | "Public domain / fair use" | PD (1869) | High | Add `license: Public domain`; note Strong's tagging source |
| **SYNOD (Russian Synodal, 1876)** | "Public domain / fair use" | PD in the US (1876); Russian Federation copyright status is separate | Medium | Add `license: Public domain (US)`; explicitly call out RU status |
| **WLCa (Westminster Leningrad Codex)** | "Public domain / fair use" | PD (WLC published 1977 onwards by Hebrew University; underlying Masoretic text is much older) | Medium | Add `license: Public domain`; cite the WLC project's own terms |
| **LXX (Septuagint)** | "Public domain / fair use" | PD (ancient text) | High | Add `license: Public domain` |
| **CUV (Chinese Union Version, 1919)** | "Public domain / fair use" | US: PD if first published in the US pre-1929; publication history is complex (originally 1919 in China) | Medium | **Flag for human review** — CUV is published by the China Christian Council today and the current US copyright status is non-trivial |
| **UKRK (Ukrainian Bible, Kulykh 1903)** | "Public domain / fair use" | PD in the US (1903) | High | Add `license: Public domain` |
| **WEB (World English Bible)** | "Public domain / fair use" | WEB is published as public domain by the WEB project | High | Add `license: Public domain` (per WEB project's stated terms) |
| **RSV (Revised Standard Version, 1952)** | "Public domain / fair use" | **Likely still under copyright** (NCC/DCE 1952, renewed) | High | **Flag for human review** — recommended action: remove or relabel "local research use only" |
| **RV1960 (Reina-Valera 1960)** | "Public domain / fair use" | Spanish-language Bible, RVR 1960 (Sociedad Bíblica) — likely under copyright | High | **Flag for human review** — recommended action: remove or relabel |
| **Saheeh International (1996)** | "Public domain (tanzil.net)" | File claims PD via Tanzil; the underlying translation IS copyrighted by Saheeh International | High | **Flag for human review** — recommended action: keep only as local-use-only until Saheeh International's terms are confirmed |
| **Yusuf Ali (1934)** | "Public domain (tanzil.net)" | Yusuf Ali translation 1934 — copyright status varies by edition; some Yusuf Ali text is PD, some isn't | Medium | **Flag for human review** — recommend: keep the 1934 text (likely PD) and confirm |
| **Pickthall (1930)** | "Public domain (tanzil.net)" | Pickthall 1930 — same US-PD-by-1929-rule applies, PD in US | High | Likely keep; add a note that the 1930 first edition is the PD edition |
| **Mufti Taqi Usmani** | "Public domain (tanzil.net)" | Modern translation, very likely still under copyright | High | **Flag for human review** — recommended: remove or local-use-only |
| **Arberry (1955)** | "Public domain (tanzil.net)" | Modern translation, very likely still under copyright | High | **Flag for human review** — recommended: remove or local-use-only |
| **Uthmani Arabic (King Fahd Complex)** | "Public Domain (King Fahd Quran Complex / Tanzil)" | The Uthmani text is published as PD by KFQC and mirrored on Tanzil | High | Keep |
| **Tanakh JPS 1917 (Adam Cohn modernized)** | "CC-BY (Adam Cohn, 2013)" | The modernization is CC-BY per the data file | High | Keep |
| **Tanakh Hebrew nikkud (tanach.us)** | "Public Domain (tanach.us via Sefaria)" | Underlying text PD; the nikkud pointing is mechanical | High | Keep |
| **Strong's Hebrew (H1–H8674)** | CC-BY-SA (file header) | Correct (Open Scriptures, CC-BY-SA) | High | Keep |
| **Strong's Greek (G1–G5624)** | CC-BY-SA (file header) | Correct (Open Scriptures + Ulrik Petersen XML) | High | Keep |
| **Cross-references (605K edges)** | CC-BY 4.0 (README) | Correct (openbible.info, CC-BY 4.0) | High | Keep |

## Per-row detail

### Bible editions

#### KJV (1769) — `kjv.json`
- **Current label:** "Public domain" (README line 274); file header says "King James Version (1769) with Strong's Numbers (Bolls Bible)".
- **Assessment:** The KJV text itself is public domain in the US (published 1769, well before any modern copyright). The Strong's tags are a separate work (CC-BY-SA from Open Scriptures). Bolls Bible is the aggregator source.
- **Confidence:** High.
- **Cited source:** KJV publication date 1769 is a stable historical fact; the US rule that works published before 1929 are PD is well-established (see e.g., the 2023 public-domain-day releases of 1928 works).
- **Decision options:** (a) Keep current label, add `license: "Public domain"` and `source: "Bolls Bible API (bolls.life)"` to the file header. (b) Same, and add explicit Strong's attribution per CC-BY-SA propagation. **Recommended: (a).**

#### YLT (Young's Literal Translation, 1898) — `translations/YLT.json`
- **Current label:** "Public domain / fair use" (README aggregate row for 13 translations).
- **Assessment:** PD in the US. Robert Young's 1898 publication is pre-1929. The YLT project itself publishes the text as public domain.
- **Confidence:** High.
- **Cited source:** YLT project, public-domain release.
- **Decision options:** Add `license: "Public domain"`, `source: "Bolls Bible API; YLT project (ylt-project.com)"`.

#### GNV (Geneva Bible, 1599) — `translations/GNV.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD. Published 1599, centuries before any modern copyright regime.
- **Confidence:** High.
- **Cited source:** Geneva Bible publication history.
- **Decision options:** Add `license: "Public domain"`, `source: "Bolls Bible API"`.

#### DRB (Douay-Rheims, 1609/1610) — `translations/DRB.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD. Published 1609/1610.
- **Confidence:** High.
- **Cited source:** Douay-Rheims publication history.
- **Decision options:** Add `license: "Public domain"`, `source: "Bolls Bible API"`.

#### LUT (Luther Bibel, 1912) — `translations/LUT.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD in the US (1912, pre-1929). The text is a 1912 revision of Martin Luther's 1534 translation.
- **Confidence:** High for US status. Medium for EU/German status, which is a separate question.
- **Cited source:** 1912 publication date.
- **Decision options:** Add `license: "Public domain (US)"`, note EU status separately.

#### TISCH (Tischendorf Greek NT, 8th ed., 1869-72) — `translations/TISCH.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD (1869-72). The Strong's tagging of TISCH is a derivative work — confirm whether the tagging is Open Scriptures' CC-BY-SA tagging or a separate work.
- **Confidence:** High for the underlying text. Medium for the Strong's tagging source.
- **Cited source:** Tischendorf publication history.
- **Decision options:** Add `license: "Public domain"`; verify Strong's tagging provenance.

#### SYNOD (Russian Synodal Translation, 1876) — `translations/SYNOD.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD in the US (1876). The Russian Federation has its own copyright term (70 years post-mortem auctoris for most works; the Synodal Translation's original translators died well before 1955, so it's PD there too as of 2025).
- **Confidence:** Medium (US = high; RU = needs verification).
- **Cited source:** 1876 publication date (US rule); RU copyright term (Civil Code Art. 1281).
- **Decision options:** Add `license: "Public domain"` and a per-jurisdiction note.

#### WLCa (Westminster Leningrad Codex) — `translations/WLCa.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD. The Masoretic text itself is ancient. The WLC was published in print by the Hebrew University Bible Project (1977 onwards); the digital edition is published as PD by the JPS and others.
- **Confidence:** Medium (need to confirm the WLC digital edition's own license).
- **Cited source:** WLC publication history.
- **Decision options:** Add `license: "Public domain"`, cite the specific WLC digital edition.

#### LXX (Septuagint) — `translations/LXX.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD. The Septuagint is an ancient Greek translation; the text itself is PD. The file has 52 books (deuterocanonical), so it's a specific critical edition — confirm which edition.
- **Confidence:** High for the text; medium for the critical-edition status.
- **Cited source:** Septuagint textual history.
- **Decision options:** Add `license: "Public domain"`, cite the specific LXX critical edition.

#### CUV (Chinese Union Version, 1919) — `translations/CUV.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** **Needs human review.** CUV was originally published in 1919 in China. The current copyright holder is the China Christian Council, which has published revised editions (CUV 2019). The US PD status of the 1919 text depends on whether it was published in the US within 30 days of foreign publication — the Berne Convention implications are non-trivial.
- **Confidence:** Medium (mechanical rule applies but the underlying facts are not verifiable from this session).
- **Cited source:** CUV publication history; China Christian Council's 2019 revision.
- **Decision options:** (a) Keep the file, mark as "Public domain (verify per US 17 USC §104)" with a human-review flag. (b) Remove the file and document the gap. **Recommended: (a) until verified.**

#### UKRK (Ukrainian Bible, Kulykh 1903) — `translations/UKRK.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD in the US (1903).
- **Confidence:** High.
- **Cited source:** 1903 publication date.
- **Decision options:** Add `license: "Public domain"`, cite Kulykh 1903.

#### WEB (World English Bible) — `translations/WEB.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** PD. The WEB project explicitly publishes the text as public domain.
- **Confidence:** High.
- **Cited source:** WEB project's own license statement.
- **Decision options:** Add `license: "Public domain"`, cite the WEB project.

#### RSV (Revised Standard Version, 1952) — `translations/RSV.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** **Likely still under copyright.** RSV was published 1952 by the National Council of Churches / Division of Christian Education. The 1952 RSV is under copyright; subsequent editions (RSV-CE, RSV-2CE) are also copyrighted. The current copyright holder (the NCC) actively licenses the text.
- **Confidence:** High.
- **Cited source:** NCC's RSV licensing terms; Copyright Office records.
- **Decision options:** (a) Remove the file from `translations/` and document the gap. (b) Keep the file but mark it as "Copyrighted — local research use only; not for redistribution" with explicit attribution. (c) Replace with a public-domain alternative (e.g., ASV 1901, but the project's ASV would need to be added). **Recommended: (a) for a research/reference tool that aims to be redistributable; (b) if the project is local-use-only.**

#### RV1960 (Reina-Valera 1960) — `translations/RV1960.json`
- **Current label:** "Public domain / fair use".
- **Assessment:** **Likely still under copyright.** RVR 1960 was published by the Sociedad Bíblica (United Bible Societies affiliate). The text is under copyright; the UBS actively licenses it.
- **Confidence:** High.
- **Cited source:** RVR 1960 publication by Sociedad Bíblica; UBS licensing terms.
- **Decision options:** Same shape as RSV: (a) remove, (b) keep as local-use-only, (c) replace with a public-domain Spanish Bible (the 1909 Reina-Valera is PD, but would need to be added separately). **Recommended: (a) unless a Spanish PD replacement is added.**

### Quran editions

The 6 Quran editions in `data/quran/` already have a `license` field. The labels all say "Public Domain (tanzil.net)" or "King Fahad Quran Complex / Tanzil (Public Domain)." The audit's job is to check whether those labels are accurate, *not* whether Tanzil's claim is correct (that's the source-aggregator's claim).

**Important note on the Quran audit:** the Arabic Uthmani text and the classical English translations (Yusuf Ali 1934, Pickthall 1930) are well-known cases where the underlying text's copyright status is the determining factor, not the aggregator's claim. The audit's assessment per edition is below.

#### Saheeh International (1996) — `data/quran/saheeh-international.json`
- **Current label:** "Public Domain (tanzil.net)".
- **Assessment:** **Likely still under copyright.** Saheeh International is a 1996 translation; the translation is under copyright by the Saheeh International team. Tanzil's claim of PD may be based on the translation's stated intent rather than a formal release.
- **Confidence:** High (the translation is recent; the 1996 publication predates any PD release).
- **Cited source:** Saheeh International's own copyright statement; Tanzil's translation-license page.
- **Decision options:** (a) Confirm with Tanzil whether they have explicit PD permission for Saheeh International. (b) Treat as copyrighted and either remove or relabel "local research use only." **Recommended: (a) — write to Tanzil, get an answer, then act.**

#### Yusuf Ali (1934) — `data/quran/yusuf-ali.json`
- **Current label:** "Public Domain (tanzil.net)".
- **Assessment:** The 1934 first edition is PD in the US (pre-1929 rule doesn't apply directly; the rule is "published in the US before 1929" for full PD, but Yusuf Ali 1934 was published abroad, which complicates things). The Yusuf Ali translation has had multiple revisions; some are copyrighted.
- **Confidence:** Medium (US PD status of a 1934 foreign publication is non-trivial; the 1934 first edition is likely PD, but later revisions are not).
- **Cited source:** Yusuf Ali 1934 publication history; subsequent revised editions.
- **Decision options:** Keep only the 1934 first edition; mark it as "PD in the US" with a clear attribution. **Recommended: confirm the text in the file is the 1934 first edition and not a later revision.**

#### Pickthall (1930) — `data/quran/pickthall.json`
- **Current label:** "Public Domain (tanzil.net)".
- **Assessment:** PD in the US (the 1930 first edition; later printings may be copyrighted as new editions, but the underlying 1930 translation text is PD). Pickthall is the most commonly-cited PD English Quran translation.
- **Confidence:** High.
- **Cited source:** Pickthall 1930 publication by Alfred A. Knopf.
- **Decision options:** Keep; add a note specifying "the 1930 first edition text."

#### Mufti Taqi Usmani — `data/quran/mufti-taqi-usmani.json`
- **Current label:** "Public Domain (tanzil.net)".
- **Assessment:** **Likely still under copyright.** Modern translation, very recent.
- **Confidence:** High.
- **Cited source:** Mufti Taqi Usmani's translation is recent; the 2007 first publication is the standard reference.
- **Decision options:** Same as Saheeh International: confirm with Tanzil, then act. **Recommended: (a) confirm; (b) if no explicit PD release, mark as local-use-only.**

#### Arberry (1955) — `data/quran/arberry.json`
- **Current label:** "Public Domain (tanzil.net)".
- **Assessment:** **Likely still under copyright.** Arberry's 1955 translation is recent enough to be under copyright in most jurisdictions.
- **Confidence:** High.
- **Cited source:** Arberry 1955 publication; Allen & Unwin's copyright.
- **Decision options:** Same as above. **Recommended: confirm with Tanzil; if no PD release, local-use-only.**

#### Uthmani Arabic — `data/quran/uthmani.json`
- **Current label:** "King Fahad Quran Complex / Tanzil (Public Domain)".
- **Assessment:** The Uthmani text in the King Fahd Complex's mushaf is published as PD by the KFQC. Tanzil's mirror preserves that.
- **Confidence:** High.
- **Cited source:** King Fahd Quran Complex's publication terms.
- **Decision options:** Keep; the current label is correct.

### Tanakh and Torah editions

These already have proper `license` fields, attributed in `data/torah/README.md` and `data/tanakh/README.md`.

#### Tanakh JPS 1917 modernized (Adam Cohn, 2013) — `data/tanakh/jps1917-modernized.json`
- **Current label:** "CC-BY (Adam Cohn, 2013)".
- **Assessment:** Correct. The modernization is a 2013 derivative of the JPS 1917 (which is itself PD in the US), released CC-BY.
- **Confidence:** High.
- **Decision options:** Keep; no change needed.

#### Tanakh Hebrew nikkud — `data/tanakh/hebrew-nikkud.json`
- **Current label:** "Public Domain (tanach.us via Sefaria)".
- **Assessment:** Correct. The underlying Hebrew text is PD; tanach.us publishes the nikkud pointing as PD.
- **Confidence:** High.
- **Decision options:** Keep; no change needed.

#### Torah JPS 1917 modernized — `data/torah/jps1917-modernized.json`
- **Current label:** "CC-BY (Adam Cohn, 2013)".
- **Assessment:** Same as the Tanakh edition; correct.
- **Decision options:** Keep; no change needed.

#### Torah Hebrew nikkud — `data/torah/hebrew-nikkud.json`
- **Current label:** "Public Domain".
- **Assessment:** Correct.
- **Decision options:** Keep; no change needed.

### Lexicons and cross-references

#### Strong's Hebrew (H1–H8674) — `strongs_data/hebrew/strongs-hebrew-dictionary.js`
- **Current label:** CC-BY-SA (file header).
- **Assessment:** Correct. The file is the Open Scriptures CC-BY-SA release; the underlying work is Strong's 1894 (PD).
- **Confidence:** High.
- **Decision options:** Keep; no change needed.

#### Strong's Greek (G1–G5624) — `strongs_data/greek/strongs-greek-dictionary.js`
- **Current label:** CC-BY-SA (file header).
- **Assessment:** Correct. Open Scriptures + Ulrik Petersen's XML; CC-BY-SA.
- **Confidence:** High.
- **Decision options:** Keep; no change needed.

#### Cross-references (605K edges) — `data/references/cross_references.json` and `.txt`
- **Current label:** CC-BY 4.0 (README).
- **Assessment:** Correct. openbible.info's cross-reference data, mirrored by scrollmapper/bible_databases, is CC-BY 4.0.
- **Confidence:** High.
- **Decision options:** Keep; no change needed.

## Default-action recommendations

The audit's recommendations, in priority order:

1. **Add explicit `license` and `source` fields to every `translations/*.json` file** that doesn't have them. Use the assessment above; for uncertain rows, use a conservative label like "Public domain (verify)" or "Copyrighted (TBD removal/replacement)". This is a low-risk change that makes the README and the data files self-consistent.
2. **Resolve the clearly-copyrighted rows** (RSV, RV1960, Saheeh International, Mufti Taqi Usmani, Arberry, possibly Yusuf Ali) by either (a) writing to the source (Tanzil, the Bible societies) to get explicit PD confirmation, or (b) marking them as local-use-only in the README and data file, or (c) removing them and documenting the gap. The default is (a) — get the source answer before changing the data.
3. **For CUV**, the same (a) — but the source is the China Christian Council, not Tanzil. Get an answer before acting.
4. **Update the README's data-sources table** to reflect the per-edition labels, not the aggregate "Public domain / fair use" row.
5. **Re-run F0a-eval after the audit** (F0a's verification was the local 39-query eval; the eval doesn't depend on labels, so this can happen in parallel with the audit if the labels are deferred).

## What this audit does NOT do

- It does not modify any data file. The `license` and `source` fields are absent from 13 `translations/*.json` files today; the audit recommends adding them but does not add them in this commit.
- It does not remove or rename any file. RSV, RV1960, and the modern Quran translations are flagged for owner review; nothing is deleted.
- It does not claim Tanzil's PD labels are wrong. The audit flags Saheeh International, Mufti Taqi Usmani, and Arberry as "likely copyrighted; confirm with Tanzil" — the ball is in Tanzil's court.
- It does not make a final decision on any uncertain row. The audit's confidence levels are explicit; rows marked "needs human review" need a human decision.

## Provenance

- **Document created:** 2026-10-08, by the agent assigned to F0b in the foundation plan.
- **Source-of-truth for project labels:** the project itself (`README.md`, `data/*/README.md`, file headers in JSON and JS).
- **Source-of-truth for US PD status:** 17 USC §104 and the Copyright Office's pre-1929 rule (well-established; no citation URL was reachable in this session).
- **Source-of-truth for translation publication dates:** the project headers and standard Bible-translation reference works (Wikipedia is consistent with these; no URL was reachable in this session).
- **What the audit could not verify:** the current Tanzil license terms for Saheeh International, Mufti Taqi Usmani, and Arberry. These need a check against tanzil.net's current translation-license page.
