# 2026-10-07 — Phase 2 dataset: load-bearing voice coverage + system-prompt fix

## What I did

Two issues with `scripts/prepare_phase2_dataset.py` that needed fixing before
Phase 2 work can actually start. Both are about *the shape of the data* (the
script's docstring is explicit: "the *shape* of the data is now locked in"),
not the data itself.

### Issue 1: system-prompt bug

`build_system_prompt(tradition, voice)` was formatting
`"You are a {voice_label}. ..."` with `voice_label` = the *citation-style
description* from `VOICE_TAXONOMY`. So the prompt opened with garbage like:

> "You are a Cites Romans/Ephesians heavily; conversational; ends with
> application. You answer questions about Christian texts..."

The role slot had a verb in it ("Cites") and read as nonsense. The 3 existing
samples still produced sensible *assistant* content (because the actual voice
was carried in the assistant turn, not the system prompt), so the bug was
latent — but a real model trained on this would be confused.

Fix: new `SYSTEM_PROMPT_TEMPLATE` with two explicit slots —
`voice_humanized` for the role ("Pastor (Evangelical)") and
`voice_label_capitalized` for the citation style as a separate sentence. New
`VOICE_HUMANIZED` map and `TRADITION_ARTICLE` map handle role rendering and
"a/an" agreement respectively. Verified all 12 (tradition, voice) combinations
read grammatically:

> "You are an Islamic Qari (Sunni). Arabic original + tafsir reference;
> cites Sahih Bukhari/Muslim hadith where relevant. You answer questions
> about Islamic texts..."

### Issue 2: thin sample coverage

`SAMPLE_EXAMPLES` had 3 examples, all showing denominational voices
(`pastor_evangelical`, `rabbi_orthodox`, `qari_sunni`). The actual user
base per `docs/audience_expectations.md` is Sarah (Persona 4, the
load-bearing persona) and Marcus + Priya (Personas 2 + 6). They map to
`plain_reader` and `academic_neutral` respectively. A hand-curated sample
set that doesn't demonstrate those voices would teach a fine-tuned model
the wrong shape for the actual queries it'll see.

Expanded to 10 samples, one per (tradition, voice) load-bearing pair plus a
denominational breadth sample:

| # | tradition | voice | primary citation |
|---|-----------|-------|------------------|
| 1 | christianity | pastor_evangelical | Ephesians 4:32 |
| 2 | judaism | rabbi_orthodox | Genesis 1:1 |
| 3 | islam | qari_sunni | Quran 2:255 |
| 4 | christianity | plain_reader | Matthew 11:28 |
| 5 | islam | plain_reader | Quran 2:186 |
| 6 | judaism | plain_reader | Deuteronomy 6:4 (Shema) |
| 7 | christianity | academic_neutral | James 2:24 |
| 8 | islam | academic_neutral | Quran 4:34 |
| 9 | judaism | academic_neutral | Exodus 34:6-7 |
| 10 | christianity | pastor_catholic | John 19:26-27 |

Each new sample was hand-curated to *demonstrate* the voice, not just label
it. The `plain_reader` examples are short, single-citation, and phrased as
Sarah would actually ask ("I'm exhausted and feel like I can't keep going").
The `academic_neutral` examples surface internal diversity across traditions
without taking sides (the James 2:24 / Romans 3:28 sample presents both
readings and notes where they disagree). The `pastor_catholic` sample
demonstrates Vulgate numbering + CCC reference style, which is missing
from the other Christian samples.

### Coverage + grammar tests

Two new sister-script tests pin the fixes:

- `t_phase2_sample_examples_cover_load_bearing_voices` — asserts at least
  one sample per (plain_reader × 3, academic_neutral × 3) pair. Without
  this, a future contributor could remove all 6 and the suite would still
  pass (the old `>= 3` floor only checks *count*, not voice coverage).
- `t_phase2_system_prompt_reads_grammatically` — asserts the system prompt
  starts with "You are ", the role slot doesn't begin with a verb (which
  would mean the citation-style description leaked back into the role),
  and the citation-style sentence starts with a capital. Verified
  manually that the test catches the buggy form: switching
  `SYSTEM_PROMPT_TEMPLATE` back to the old `"You are a {voice_label}"`
  form would produce "You are a Cites Romans..." and fail the role-slot
  check.

The sample-count floor in `t_phase2_sample_examples_validate_schema` was
also bumped from `>= 3` to `>= 8` to match the new sample set (10 with
headroom for 2 one-off removals without breaking).

## Blocked

Nothing blocked. The seed mode (cross-references → placeholder) is
intentionally placeholder per the script's docstring; the actual seed
data needs a stronger model to distill and is Phase 2 work proper, not
this prep pass.

## Tomorrow (or "next session")

- **Option B** — add 5-10 Sarah-style queries to `tests/benchmark.py` to
  measure the load-bearing persona's actual retrieval quality. The current
  33-query set is doctrinal-query shaped; Sarah questions are
  life-question shaped. Worth re-running the 3-large vs local comparison
  on a persona-relevant set before committing to the FastAPI MVP.
- **Cross-tradition sample** — would require adding a 4th `tradition` value
  to the schema (a "comparative" tradition), which crosses into Phase 4
  front-end scope. Better as a separate ADR than an opportunistic change.
- **Phase 2 actual** — the schema is now loadable. The next step is
  distilling real answers (using a stronger model on the cross-reference
  substrate) to replace the seed-mode placeholders. That's a separate
  work stream, not this prep pass.

## Decisions

- **Fix the system-prompt bug, don't document it.** A "documented bug" is
  a tax on every future reader; a fix is a one-time cost. The risk of
  breaking the JSONL schema is bounded — the seed mode emits placeholders,
  not the system-prompt text, and the sample mode is a hand-curated
  document, not consumed by anything yet.
- **Don't add a 4th `tradition` value for cross-tradition samples.** It's
  a schema change that affects the test (`t_phase2_sample_examples_validate_schema`
  enforces `tradition ∈ {christianity, islam, judaism}`). Cross-tradition
  is Phase 4 territory (Reader / Scholar / Comparative layers) and
  deserves an ADR, not an opportunistic add.
- **Bump the sample-count floor and add a voice-coverage test together.**
  They're coupled: bumping the floor alone doesn't protect the load-bearing
  voices (a contributor could still ship 8 `pastor_evangelical` examples
  and pass). The coverage test pins the *distribution*.
- **7 new samples, not 10.** I stopped after the 6 load-bearing voices
  plus one denominational breadth (Catholic) because the other 7
  unsampled voices (`pastor_orthodox`, `qari_shia`, `rabbi_conservative`,
  `rabbi_reform`) are documented-but-unsampled. Phase 2 actual work
  should grow the sample set when there's a real question to ask in
  those voices; speculative samples without a real question would
  teach the model a wrong shape.

## Verification

```
$ python3 tests/run_all.py | tail -3
  131 passed, 0 failed (of 131)
```

Baseline was 129; the 2 new tests (`..._cover_load_bearing_voices`,
`..._system_prompt_reads_grammatically`) bring the total to 131. No
existing tests changed behavior — the floor bump in
`t_phase2_sample_examples_validate_schema` (3 → 8) passes because the
sample set is now 10.