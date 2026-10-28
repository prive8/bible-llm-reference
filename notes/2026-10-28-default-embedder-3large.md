# The default embedder is now text-embedding-3-large — 2026-10-28

Session by dad-h2. Resumes the queue item assigned by solomon-grokbot (PM)
on 2026-10-28: make OpenAI `text-embedding-3-large` the default embedder,
then pick up the held_out retrieval gate that was waiting on the decision.

The code half of this shipped as `fb95601` and `fad4c0f` before this
session. This session found that it was **red in CI**, fixed the cause,
and wrote up the decision.

---

## Done

### The CI failure, and what it actually was

Run `40740828930` on `fad4c0f` failed in **all nine jobs** — the eight
matrix test jobs (ubuntu + windows, Py 3.10–3.13) and the `eval-regression`
job. Every one failed at the same step, the sister-script test suite, with
the same two failures:

```
177 passed, 2 failed (of 179)
[FAIL] t_hybrid_cli_accepts_dash_n_alias
[FAIL] t_hybrid_cli_top_k_still_works
```

Both are the tests that invoke `python -m bible hybrid ... --json` as a
subprocess.

**Root cause.** `fb95601` changed `bible hybrid` to resolve the default
embedder profile instead of hard-coding `index_name="default"` and
`backend="auto"`. The default profile is now `3large` — OpenRouter's
`openai/text-embedding-3-large` — whose backend needs an `OPENROUTER_API_KEY`.
CI has no key and no `~/.hermes/.env` to fall back to, so
`resolve_embedder_profile` raised `ProfileUnavailableError`, and the hybrid
CLI did not catch it. The error escaped as a stack trace and the command
exited 1.

Retrieval had not broken. A CLI could not say "the semantic leg is
unavailable" — that is all.

The traceback confirms the path:

```
bible/hybrid.py:313  sem_hits = search_semantic(...)
bible/semantic.py:1320  prof, _notes = resolve_embedder_profile(...)
bible/semantic.py:765  raise ProfileUnavailableError(
    "the default embedder profile '3large' (openai/text-embedding-3-large)
     cannot run here: no OPENROUTER_API_KEY ...")
```

**Fix.** The hybrid command's semantic leg is now **optional and
announced** — never silent, and never substituted:

- BM25 needs no embedder, so the query is still answered from the keyword
  leg and the exit code is 0.
- The degradation is reported on **stderr** and in the **JSON payload**
  (`"semantic_leg": "unavailable"` plus a `"semantic_note"` naming the
  reason). The JSON field matters: a machine consumer that discards stderr
  would otherwise read a degraded result set as a full hybrid one.
- A missing index for the resolved profile is reported the same way, so
  "no index built" and "no results" are distinguishable.
- `bible hybrid` gained `--profile`, matching `bible semantic`. The
  production default needs an OpenRouter key, and without a flag there was
  no way to ask the hybrid command for the free offline MiniLM index.

What it deliberately does **not** do is fall back to a *different* embedder.
Scoring the 3072-dim 3-large index with MiniLM's 384-dim query vector would
compare the first 384 dimensions and report a score that measures nothing —
the dimension guard raises on exactly that pairing, and the CLI does not
route around it.

**Verification.** The suite was re-run in a CI-equivalent environment —
system Python with no `sentence-transformers`, no `OPENROUTER_API_KEY`, and
`HOME` pointed at an empty directory so `~/.hermes/.env` could not supply a
key behind the test's back: **179 passed, 0 failed**, and
`bible hybrid mercy -n 5 --json` exits 0 with valid JSON. The regression
coverage is folded into `t_hybrid_cli_top_k_still_works` — the test that
caught it — so the suite count stays at 179.

### ADR-016 — the decision, written down

[`docs/design-decisions.md`](../docs/design-decisions.md) now carries
**ADR-016, Accepted 2026-10-28**, deciders Steven (acting chair per
`COUNCIL.md` §6.1), superseding ADR-014.

The measured numbers it records, on the complete 66,689-passage indexes on
benchmark v2 — the cross-tradition benchmark that matches the corpus:

| Split | Metric | local MiniLM (384-d) | **3-large (3072-d)** | qwen3-8b (4096-d) |
|---|---|---|---|---|
| v2 dev | semantic | 0.189 | **0.297** | 0.321 |
| v2 dev | hybrid | 0.183 | **0.284** | 0.309 |
| v2 held_out | semantic | 0.106 | **0.244** | 0.255 |
| v2 held_out | hybrid | 0.115 | **0.226** | 0.234 |

Latency: **3-large ~2.9 s/query** against local **~0.83 s/query**, and
qwen3-8b ~9.6 s/query. The full 3-large index rebuild costs **~$0.74**;
per-query cost is negligible.

ADR-014 is marked **superseded** with a pointer to ADR-016, and ADR-013
carries a note that its hosted-path decision is superseded and that the
hosted path's default model is now 3-large rather than the 3-small it chose.

### README and CHANGELOG

README now says the default embedder is 3-large, shows **all three CI
gates** (`local/v1`, `local/v2-dev`, `local/v2-held_out`) with the
`config/retrieval_gates.json` file named as the source of truth, carries
the embedder comparison table with the dev and held_out numbers and the
latency column, and the "Run the gates locally" commands now name their
gate (`--gate local/v2-held_out`) instead of retyping thresholds. Test
count 179 in both places.

CHANGELOG records the default switch, the profile coupling, the dimension
guard, the new held_out gate, and the CI fix.

---

## Blocked

### AGENTS.md could not be edited

The work-queue entry 1 (mark done) and the test-count line (170 → 179) in
`AGENTS.md` were **not** updated: the file is write-protected in this
environment and there is no interactive approver to grant the write. The
guard explicitly forbids retrying the edit by another route, so it was left
alone rather than worked around.

Both edits are small and known; they need either an approving user or an
unprotected window. The intended change is recorded in the CHANGELOG entry
above and in this note, so nothing is lost but the file itself.

### A qwen3-8b "deep study" mode is still undecided — and was not built

Steven's brief named a possible slower mode on qwen3-8b. **No model was
picked for it and it was not built.** The `qwen3-8b` profile is registered
only so the comparison table stays reproducible. Anyone picking this up
should read the mode as *not started*, not *half done*.

---

## Tomorrow

- **Update `AGENTS.md`** — work-queue entry 1 marked done, test count
  170 → 179. Blocked above; needs approval or an unprotected window.
- **Watch CI on the pushed commit.** The fix and the docs are one commit;
  CI must go green on all nine jobs before this work is closed.
- **The 3large gates in `config/retrieval_gates.json` are not run by CI.**
  They need an OpenRouter key and a 3072-dim index. If a hosted gate is
  wanted, that is a separate decision about CI credentials, not something
  to fold in here.
- **A numpy scoring path** would collapse the latency gap (the brief's
  Option C) — 22× faster scoring — but ADR-001 makes `bible/` stdlib-only,
  so it needs its own ADR and a stdlib fallback. Not started.

---

## Decisions

1. **3-large is the production default.** Not qwen3-8b: it scores higher
   (0.321 dev / 0.255 held_out) but at ~9.6 s/query, which is disqualifying
   for a search box. Not local MiniLM: 0.189 dev / 0.106 held_out is
   materially worse on the benchmark that matches the corpus.
2. **The gain is judged on the held-out split too.** 3-large scores 0.244
   vs local's 0.106 there, so the improvement is not an artifact of the
   split the thresholds were tuned against.
3. **The held_out gate's thresholds come from the held_out baselines**
   (bm25 0.092, semantic 0.106, hybrid 0.115), not from the dev gate. The
   split is harder, so its baselines are lower and its thresholds are
   correspondingly lower. Reusing the dev thresholds would fail on current
   code and prove nothing.
4. **No threshold was raised.** Every gate threshold sits strictly below
   its own measured baseline. A threshold raised to turn a red gate green
   is the failure this whole mechanism exists to prevent.
5. **The hybrid semantic leg degrades, loudly, and never substitutes.** BM25
   still answers; the degradation is on stderr *and* in the JSON payload.
   Falling back to a different embedder is forbidden — that is the
   dimension-mismatch bug the guard was added to catch.
6. **ADR-014 is superseded, not rewritten.** It stays as the record of what
   was true on 2026-09-11; ADR-016 records what is true now and links
   back. The ADR file is append-only.

---

*Measurements: `notes/2026-10-26-adr-014-decision-brief.md`,
`notes/2026-10-26-qwen3-v2-eval.md`, `notes/2026-10-26-truncated-index-found.md`,
`notes/2026-10-26-index-reload-fix.md`. All measured on the same host
against the same corpus and benchmark; BM25 identical across every arm is
the control.*
