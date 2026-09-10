# COUNCIL.md — Bible LLM Reference Governance

> **Version:** v0.4 — **constituted as single-contributor body on 2026-09-10.**
> The Constitution is in force. The full multi-agent Council is still
> the *target architecture* (§3 below); the project has formally
> convened the constitution with the project owner as sole acting chair.
>
> **Last updated:** 2026-09-10 (v0.4 — formal convening as
> single-contributor body. v0.3 → v0.4: added §3.1 "Current constitution
> status", §6.1 "Acting chair", updated §5 versioning, removed the
> "STUB" disclaimer from the header. Spirit unchanged.)
>
> **Read alongside:** `HANDOFF.md` (engineering context — and §11
> for the runtime contract), `docs/governance/council-design.md`
> (long-form Council spec).

---

## 0. What this document is

This is the project's **constitution**. It says what the Council is,
when it forms, and what it does when it forms. Since 2026-09-10 the
Council **is constituted** in its single-contributor-body form (see
§3.1 below). The full multi-agent roster in the long-form design doc
is the *target architecture* — that arrives when either a second
contributor joins or Phase 2 begins.

**The detailed Council design** — agent roster, decision protocol,
scoping guardrails, runtime behavior, evolution rules — lives in
[`docs/governance/council-design.md`](docs/governance/council-design.md).
Read this constitution first; the long-form doc is the source of truth
for "how does the Council actually work."

**The runtime contract** — citation rules, Strong's policy, no-
anthropomorphizing — lives in [`RUNTIME_CONTRACT.md`](RUNTIME_CONTRACT.md)
(extracted from `HANDOFF.md` §11 in v0.10.0). That's a different
document with a different purpose: the runtime contract binds any
agent that uses this data, regardless of whether the Council has
formed. This Constitution binds the Council.

---

## 1. Purpose

The Council exists to keep the system:

- **Maximally truth-seeking and historically accurate.** Strongest
  thing we can offer: here is what the texts actually say, in their
  original languages where possible, with provenance.
- **Strictly neutral.** No favored tradition. No anti-religious bias.
  No "spiritual but not religious" privilege. No default frame.
- **Inclusive of every living and historical human religion, spiritual
  path, indigenous tradition, new religious movement, and non-theistic
  worldview.** Including those that are small, recent, contested,
  unpopular, or whose adherents have been historically marginalized.
- **Respectful without becoming sycophantic or censorious.** The
  system reports what traditions actually say, including hard truths
  about history, doctrine, and conduct. It does not soften, equivocate,
  or refuse-as-a-default.
- **Capable of presenting conflicting claims side-by-side without
  forcing synthesis or hierarchy.** When two traditions disagree, both
  get surfaced with attribution. The system does not pick a winner.

The Council is the final authority on:

- What enters the training corpus (and what is excluded).
- How doctrines, scriptures, and practices are represented.
- How the system answers live queries that touch religion or
  spirituality.
- When to escalate, refuse, or add strong disclaimers.

---

## 2. Operating principles (non-negotiable)

1. Beliefs are reported as beliefs; empirical claims are tested against
   evidence.
2. No tradition is treated as the default or "true" one.
3. Primary sources outrank secondary commentary.
4. Living practitioners' self-descriptions are privileged over external
   academic caricatures, but both are surfaced.
5. Comparative statements must be explicit about the frame of
   comparison.
6. Mystical, experiential, and "spiritual but not religious" claims
   are handled with the same rigor as institutional religions.
7. The system never performs rituals, grants absolution, or claims
   spiritual authority.

These principles bind the Council at every phase, including the
single-contributor-body phase. The acting chair does not have the
authority to override the principles.

---

## 3. When the full Council forms

The **full multi-agent Council** forms when either of two conditions
is met:

1. **A second contributor joins the project.** Multi-author
   contributor decisions (corpus admission, doctrinal representation,
   scope expansion) require a body larger than a single pair of hands.
2. **The project enters Phase 2** (generative voice fine-tune). At
   that point, model-behavior and evaluation decisions need a
   governance process the acting chair alone cannot credibly run.

Until then, the project is run as a single-contributor body under
the principles in §2 — see §3.1 below.

### 3.1. Current constitution status (since 2026-09-10)

The Council **is constituted** in its single-contributor-body form.
The project owner ("father", GitHub: `prive8`) is the acting chair.
This is not a placeholder; this is a real, binding, working Council
with one member. The constitution is in force and §2 binds all
decisions.

When the full Council forms per §3, the convening is a *chamber
expansion*, not a *constitution creation*. The seven principles,
the runtime contract, and all decisions made under the
single-contributor-body form carry over without re-ratification.

---

## 4. Companion docs

- `HANDOFF.md` — engineering context, conventions, milestone plan.
  Co-equal with this document, not subordinate.
- `RUNTIME_CONTRACT.md` — runtime contract for any agent using this
  data (citation rules, Strong's policy, no-anthropomorphizing).
  Extracted from `HANDOFF.md` §11 in v0.10.0.
- `docs/governance/council-design.md` — long-form Council spec:
  agent roster, decision protocol, scoping guardrails, runtime
  behavior, evolution rules.
- `README.md` — user-facing.
- `LICENSE` — MIT (per Grok upgrade 2026-07-31). Note: different
  licensing applies to specific data sources (Strong's is CC-BY-SA;
  KJV is public domain; Torah editions per `data/torah/README.md`).
- `docs/governance/verdicts/` — created when the full Council is
  constituted with multi-member votes. Single-contributor-body
  decisions are recorded inline in `notes/YYYY-MM-DD.md` daily
  journals (see §6.1 below).
- `docs/governance/controversies/` — Controversy Register, per
  design doc §5. Empty as of v0.4 (no controversies have surfaced).

---

## 5. Versioning

- **v0.1-stub (2026-07-31)** — initial placeholder, removed.
- **v0.2-stub (2026-07-31)** — first grok-aligned draft. Removed
  after the daily-2026-07-31 review exposed the Phase-1-vs-Phase-2
  legibility problem.
- **v0.3-stub (2026-07-31)** — short stub + long-form split. The
  "not yet implemented" disclaimer was prominent.
- **v0.4 (2026-09-10, this version)** — **constituted as
  single-contributor body**. Added §3.1 (current status), §6.1
  (acting chair). The constitution is in force; the full multi-agent
  Council remains the target architecture. Principles unchanged.
- **v1.0** — drafted when the full multi-agent Council is constituted
  (second contributor joins OR Phase 2 begins). Every TODO in the
  design doc becomes either a real policy or is folded into v1.0
  with rationale for why it was dropped.
- **v1.x** — amendments require a recorded Council vote.
- **v2.x** — major structural changes (e.g., adding a third chamber)
  require a recorded vote and a public comment period.

---

## 6. Quick orientation

If you're a new contributor: read this, then read `HANDOFF.md`. They
are co-equal.

If you're a future Council member: read §2 (principles) and §3.1
(current status) here. Then read the design doc.

If you're a future father or successor: this document is the
project's constitution. The acting chair changes by succession
(per §6.1 below); the principles in §2 do not.

### 6.1. Acting chair

**Current acting chair:** the project owner, "father" (GitHub: `prive8`).
**Since:** 2026-09-10 (Council convening).
**Authority:** the acting chair makes all decisions subject to the
seven principles in §2 and the runtime contract in
`RUNTIME_CONTRACT.md`. The acting chair has no authority to override
either.
**Succession:** the acting chair transfers the role to another person
through a recorded succession event (date, from, to, signature on
both sides, public notice on the project's main channel). The
constitution, the runtime contract, and all prior decisions transfer
with the role; the principles in §2 do not.
**Removal:** the acting chair can be removed by their own resignation
or by the formation of the full Council per §3 (which establishes
the multi-member vote process that supersedes single-chair authority).
**Decision recording:** all chair decisions are recorded in the daily
notes (`notes/YYYY-MM-DD.md`) with rationale, dissent (if any), and
followup actions. Multi-member Council votes (post-§3) use the
Verdict format per design doc §3.1.
