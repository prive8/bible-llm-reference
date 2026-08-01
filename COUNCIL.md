# COUNCIL.md — Bible LLM Reference Governance

> **STUB DOCUMENT — v0.3-stub. DO NOT TREAT AS FINAL POLICY.**
> The Constitution is here. The implementation is not.
>
> **Last updated:** 2026-07-31 (v0.3-stub — reconciled against the
> Grok upgrade; `agents.md` (lowercase) on the remote is the
> Council mapping table, this is the constitution)
> **Read alongside:** `HANDOFF.md` (engineering context),
> `agents.md` (runtime contract for any agent using this data),
> `docs/governance/council-design.md` (long-form Council spec).

---

## 0. What this document is

This is the project's **constitution**. It says what the Council is,
when it forms, and what it will do when it forms. The Council itself
does not exist yet — it is a single-contributor body (the project
owner, "father") and the agent roster in the long-form design doc is
the *target architecture*, not the running implementation.

**The detailed Council design** — agent roster, decision protocol,
scoping guardrails, runtime behavior, evolution rules — lives in
[`docs/governance/council-design.md`](docs/governance/council-design.md).
Read this stub first; the long-form doc is the source of truth for
"how does the Council actually work."

**The runtime contract** — citation rules, Strong's policy, no-
anthropomorphizing — lives in the lowercase [`agents.md`](agents.md).
That's a different document with a different purpose: the runtime
contract binds any agent that uses this data, regardless of whether
the Council has formed. This Constitution binds the Council when it
forms.

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

These principles bind the contributor today. They bind the Council
when it forms. The contributor does not have the authority to
override the principles at any phase.

---

## 3. When the Council forms

The Council forms when either of two conditions is met:

1. **A second contributor joins the project.** Multi-author
   contributor decisions (corpus admission, doctrinal representation,
   scope expansion) require a body larger than a single pair of hands.
2. **The project enters Phase 2** (generative voice fine-tune). At
   that point, model-behavior and evaluation decisions need a
   governance process the contributor alone cannot credibly run.

Until then, the Council is a single-contributor body operating under
these principles. The principles bind the contributor today; they
bind the Council when it forms. The contributor does not have the
authority to override the principles at any phase.

---

## 4. Companion docs

- `HANDOFF.md` — engineering context, conventions, milestone plan.
  Co-equal with this document, not subordinate.
- `agents.md` — runtime contract for any agent using this data.
  Smaller and tighter than this document; covers citation rules,
  Strong's policy, no-anthropomorphizing.
- `docs/governance/council-design.md` — long-form Council spec:
  agent roster, decision protocol, scoping guardrails, runtime
  behavior, evolution rules.
- `README.md` — user-facing.
- `LICENSE` — MIT (per Grok upgrade 2026-07-31). Note: different
  licensing applies to specific data sources (Strong's is CC-BY-SA;
  KJV is public domain).
- `docs/governance/verdicts/` — to be created when the Council is
  constituted. Each verdict is a separate file (template in the
  design doc, §3.1).
- `docs/governance/controversies/` — Controversy Register, per
  design doc §5.

---

## 5. Versioning

- **v0.1-stub (2026-07-31)** — initial placeholder, removed.
- **v0.2-stub (2026-07-31)** — first grok-aligned draft. Removed
  after the daily-2026-07-31 review exposed the Phase-1-vs-Phase-2
  legibility problem.
- **v0.3-stub (2026-07-31, this version)** — short stub + long-form
  split. The "not yet implemented" disclaimer is now prominent;
  the runtime contract is in `agents.md` (lowercase) where the
  Grok draft put it; the engineering context is in `HANDOFF.md`.
- **v1.0** — drafted when a real Council is constituted. Every
  TODO in the design doc becomes either a real policy or is folded
  into v1.0 with rationale for why it was dropped.
- **v1.x** — amendments require a recorded Council vote.
- **v2.x** — major structural changes (e.g., adding a third chamber)
  require a recorded vote and a public comment period.

---

## 6. Quick orientation

If you're a new contributor: read this, then read `HANDOFF.md`. They
are co-equal.

If you're a future Council member: read §2 (principles) and §3
(when the Council forms) here. Then read the design doc.

If you're a future father or successor: this document is the
project's constitution. Treat it accordingly.
