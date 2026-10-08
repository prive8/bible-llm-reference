# 2026-10-08 — F0a: Judaism index default to English

## Done

- **F0a fix landed in `scripts/index_embeddings.py`.** Judaism slice
  (Torah + Tanakh) now defaults to the `jps1917-modernized` English
  edition instead of the pointed Hebrew. Before: 23,206 Hebrew-text
  passages were being fed into the local English-only embedder
  (`all-MiniLM-L6-v2`). After: same 23,206 passages, English text.
  Verified end-to-end with the mock backend by inspecting the meta
  JSON.
- **New `--judaism-edition` flag** in `index_embeddings.py`. Choices:
  `jps1917-modernized` (default, English) or `hebrew-nikkud` (opt-in).
  The "use first available edition" semantics are preserved — if the
  requested edition's data file is missing, the other one is used as
  a fallback rather than dropping Judaism from the index. The flag
  is a parameter, not a hardcoded default, so F1's tradition registry
  can subsume it without rewriting the call sites.
- **Inline comment in `collect_corpus` updated** to reflect the new
  default and to point at the F1–F4 registry as the long-term
  replacement.
- **Verification.** Re-ran the full sister-script suite: 137/137 tests
  pass. Argparse accepts the new flag. `collect_corpus(...)` with
  `judaism_edition="jps1917-modernized"` returns 23,206 entries,
  translation label `Modernized Tanakh based on JPS 1917 (Adam Cohn,
  2013)`, 23,204/23,206 entries with English letters, Genesis 1:1
  reads `"When God began to create heaven and earth—"`. Same call
  with `judaism_edition="hebrew-nikkud"` returns 23,206 entries with
  the Hebrew pointed text (Genesis 1:1: `בְּ רֵאשִׁ֖ית בָּרָ֣א
  אֱלֹהִ֑ים...`). Both paths produce the same passage count.
- **F0a scope confirmed as the minimal fix.** No two-index
  scaffolding, no Hebrew-as-second-default, no embedder bake-off,
  no Phase 2 work. The "done when" criterion in the foundation plan
  §3 (rebuild + re-run 39-query eval + archive) is *partially* met:
  the rebuild verified, the eval is blocked on the local embedder
  not being installed in the hermes-managed Python (see Blocked).

## Blocked

- **Local 39-query eval not run.** The hermes-managed Python at
  `~/.hermes/tools/python-3.14.7+202****0901-linux-x64/bin/python3`
  and the system `/usr/bin/python3` (3.12.3) both lack
  `sentence_transformers` and `numpy`, which the local embedder
  backend requires. The prior session's handoff doc
  (`notes/2026-10-07-qwen3-index-built-eval-pending.md`) assumed the
  hermes Python would have them. It does not. Installing the
  `embeddings` extra is a separate decision — deferred per the
  scope agreed for this session. Without the eval, the precision
  improvement from the F0a fix is *inferred* (English text into an
  English embedder is the correct alignment) rather than *measured*.
  The full eval can be re-run from any environment that has
  `sentence-transformers` + `numpy` installed; no code change in
  this repo is needed.
- **OpenRouter 39-query eval still not run.** Same gateway-timeout
  issue from `notes/2026-10-07-qwen3-index-built-eval-pending.md`.
  Per foundation plan §3 row 3 (F0c), the qwen3-8b eval is parked
  until F2 lands. Not in scope here.

## Tomorrow

- The 39-query local eval is the natural next session's opener for
  whoever has an environment with the embeddings extra installed.
  Command (from foundation plan + the `--judaism-edition` flag):
  ```
  python scripts/index_embeddings.py --backend local --name f0a-verify --overwrite
  python scripts/run_eval.py --paths semantic,hybrid --backend local --index f0a-verify
  ```
  Archive the eval log as `notes/eval-runs/2026-XX-XX-f0a-39query.log`
  and compare the Judaism-slice numbers (Yuki 0.183, Priya 0.107
  in the pre-F0a local-semantic table) against the post-F0a run.
- F0b (license audit) is the next priority in the foundation plan.
  It's a human-audit task — translations are labelled public
  domain but several are likely not. Not in scope for this session
  because the AGENTS.md convention puts it on the project owner,
  not the agent.

## Decisions made

- **F0a = default flip only, no two-index scaffolding.** Per the
  scope question answered at session start. Keeps F0a from
  pre-empting the F1–F4 registry design. The `--judaism-edition`
  flag is the bridge — it makes the choice explicit and overridable
  without committing to a multi-edition storage model.
- **The "first available edition" fallback was kept.** The original
  code silently used whichever edition's data file loaded first.
  That intent (be resilient to missing data files) is sound; F0a
  only changes the *priority order* within that fallback chain.
  This means if someone runs F0a on a tree with only
  `hebrew-nikkud.json` present (no English file), they still get
  a Judaism slice — it just defaults to Hebrew, which is the
  right thing for that tree.
- **No new test for F0a.** The fix is a default-value change in a
  single script, not a behavior change in the `bible/` package.
  The 137-test suite still passes, and the verification above
  (rebuild + inspect) is the right test surface for this kind of
  fix. A sister-script test that asserts the default edition is
  English would lock in the F0a decision; if Dad wants that, it's
  a 5-line addition for the next session.
- **CHANGELOG entry added under `[Unreleased]` → `Fixed`.** Per
  AGENTS.md convention. The entry is short and points at the
  foundation plan and the verification details.
