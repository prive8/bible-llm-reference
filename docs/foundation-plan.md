# Foundation Plan — making "all traditions" real

> **Written:** 2026-10-08, from a whole-project direction review,
> cross-checked against every commit through `0a4df0e` (2026-10-07).
> **Status:** proposed — needs chair (project owner) sign-off on the
> open questions in §6 before step F2 starts.

## 1. Why this plan exists

HANDOFF §7.1 promises that adding a tradition is "a config change, not
a code rewrite." Today it is not: the Bible has a core
(`lookup/parallel/search/references/strongs`), and Quran / Torah /
Tanakh are separate modules that only `semantic`/`hybrid` combine.
The 2026-10-07 commits (all eval tuning and notes) confirm this rather
than fix it — e.g. `notes/2026-10-07-hybrid-per-persona.md` records
BM25 recall of 0.000 for the cross-tradition personas "because BM25
has no Quran or Torah passages", and treats it as a given.

## 2. Review claims vs. what the latest commits show

| # | Claim from review | Check against commits through `0a4df0e` | Status |
|---|---|---|---|
| 1 | Multi-tradition is bolted on | Core modules still Bible-only; yesterday's notes state BM25 has no Quran/Torah | **Confirmed** |
| 2 | No shared passage ID across traditions | No commit touches it; Gap 2 queries use free-text citations | **Confirmed** |
| 3 | Judaism slice indexed as Hebrew in an English embedder | `index_embeddings.py` still tries `hebrew-nikkud` first; cross-tradition recall is 0.07–0.18 | **Confirmed in code; index not verifiable here** (embeddings are gitignored and live on the WSL/Hermes host) |
| 4 | License labels likely wrong | No license commits | **Open — needs a human audit** |
| 5 | No product surface | No Phase 4 code | **Confirmed** |
| 6 | Eval effort at diminishing returns | 13 of 16 commits on 2026-10-07 are eval/notes; routing conclusions rest on n=5–11 slices; the qwen3-8b 1 GB index was built but its eval never ran | **Confirmed, and worse than stated** |
| 7 | Lexicon coverage uneven | Unchanged | **Confirmed** |
| 8 | Doc drift | HANDOFF header still says 2026-07-31; README test count stale | **Confirmed; fixed in this commit** |

**Corrections to the original review:**
- Yesterday's work was not wasted: `index_embeddings.py` checkpointing
  (`b987405`) fixes a real fragility, and per-persona labels on the
  benchmark are a sound idea.
- The earlier "single-verse parser bug" in a note (`Hosea 6:6`) could
  not be reproduced: `python -m bible parallel "Hosea 6:6"` works.
- The Phase 2 dataset work is also early relative to COUNCIL §3.

## 3. Immediate fixes (before any refactor)

| ID | Task | Done when |
|---|---|---|
| F0a | Switch Judaism indexing to `jps1917-modernized` (English); keep Hebrew as a separate, optionally multilingual index | Rebuilt index shows Judaism passages as English; re-run the 39-query eval and archive the log |
| F0b | License audit of all 14 Bible + 6 Quran translations and the Uthmani text; relabel or remove | Each data file's `license` field is backed by a cited source; README table updated |
| F0c | Park the qwen3-8b eval (index stays on disk) | Note added; no further embedder bake-offs until F2 lands |

## 4. Foundation work

| ID | Task | Detail |
|---|---|---|
| F1 | **Passage model + tradition registry** | One `Passage` shape (`tradition`, `text_id`, `edition`, `division`, `unit`, `text`, `lang`) and a registry (`bible/registry.py`) listing every tradition's editions, structure, citation style and license |
| F2 | **Canonical passage IDs** | e.g. `bible:Gen.1.1`, `tanakh:Gen.1.1`, `quran:2.255`; one per (tradition, canonical location), independent of edition |
| F3 | **Versification map** | Bible ↔ Tanakh book names and verse offsets (Mal 3:19–24 ↔ 4:1–6, Joel 2:28 ↔ 3:1, Psalm superscriptions) as a data file |
| F4 | **Route core commands through the registry** | `search`, `parallel`, `references`, `semantic`, `hybrid` accept `--tradition`; BM25 indexes any registered edition; fold `torah.py` into `tanakh.py` as a filtered view |
| F5 | **Docs to v0.2** | `data-schema.md` v0.2 validated against real data; HANDOFF §4/§6 refreshed |

**Exit criterion for F1–F4:** a throwaway test tradition (e.g. a
five-verse stub) can be registered by adding a data file and a registry
entry — no new module, no CLI edits — and shows up in `parallel`,
`search`, and `semantic`.

## 5. After the foundation

1. **Phase 4 Reader MVP** on the unified layer (scope: `docs/phase4-scope-frontend.md`).
2. **Hadith**, then **one non-Abrahamic text** (Dhammapada or Tao Te Ching) as the real test of F1–F4.
3. **Eval hygiene:** grow the benchmark with independently written
   queries and a held-out split before any more tuning; don't tune
   hybrid weights on the reported set.
4. Resume embedder comparison and Phase 2 data work only after 1–3.

## 6. Open questions for the chair

1. LLM or reference tool first? (Vision says "working LLM"; Phase 4 forbids generated text in the UI.) When does Phase 2 start — it also triggers the full Council (COUNCIL §3).
2. Depth (lexicons, Hadith) or breadth (one Eastern text) right after F4?
3. Copyrighted translations: remove, or keep as local-use-only?
4. Rename the `bible` package (e.g. to a tradition-neutral name) during F4, or keep it for compatibility?
