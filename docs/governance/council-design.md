# Council Design — Long-Form Specification

> **Long-form design document.** The principles, agent roster, decision
> protocol, scoping guardrails, runtime behavior, and evolution rules
> for the Bible LLM Reference Council. The Council itself is a
> **target architecture** — it is not yet implemented. The project
> runs as a single-contributor body under the principles in
> [`COUNCIL.md`](../../COUNCIL.md) §2 until the Council forms (see
> `COUNCIL.md` §3 for the trigger conditions).
>
> **Last updated:** 2026-07-31 (v0.3-stub — split out of `COUNCIL.md`
> for legibility, per the daily-2026-07-31 review)
> **Source of truth:** this document, until v1.0 lands.
> **Read alongside:** [`COUNCIL.md`](../../COUNCIL.md) (the constitution),
> [`HANDOFF.md`](../../HANDOFF.md) (engineering context),
> [`agents.md`](../../agents.md) (runtime contract).

---

## 1. Architecture

The Council is, at runtime, a roster of specialized AI agents with
their own system prompts, retrieval tools, and evaluation metrics.
Each one is a domain expert. They deliberate asynchronously or in
structured rounds, producing a Council Verdict that the main AI
surface uses to answer live queries.

> **TODO:** Each agent gets a full system prompt under
> `agents/<agent_id>.md`. The roster is the placeholder shape; the
> real agent definitions ship when the Council forms.
>
> **TODO:** The agent runtime (LLM with retrieval, deliberation
> protocol, verdict emission) is not yet implemented. Phase 1 ships
> a deterministic retrieval tool without Council mediation. Phase 2
> (model fine-tune) is the first phase where Council-routed live
> answers become relevant.

---

## 2. Agent roster (target architecture)

The roster below is the *target* shape. It is not yet implemented.
Phase 1 routes questions to code paths, not agents. The agent roster
exists so that the data layer, retrieval API, and citation surface
are designed in a way that agent mediation is a Phase 2 add-on, not
a Phase 3 retrofit.

The lowercase `agents.md` in the repo root is the **runtime contract**
for any agent that uses this data — it covers the four agents that
map to the Abrahamic / Christian slice (abrahamic_guardian,
historian_archivist, comparative_scholar, ethicist_mediator). The
roster below is the **full Council** that will exist when the
Council forms, including the non-Abrahamic agents.

| Agent ID               | Domain Focus                                                                  | Primary Responsibility                            |
|------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| abrahamic_guardian     | Judaism, Christianity, Islam, Baháʼí, Druze, Samaritism, Rastafari, etc.       | Scriptural fidelity, denominational nuance        |
| dharmic_sage           | Hinduism, Buddhism, Jainism, Sikhism, related (incl. schools and sub-traditions) | Orthodoxy vs. orthopraxy, philosophical schools   |
| indigenous_elder       | Native American, African Traditional, Aboriginal, Animist, Shamanic, etc.    | Oral tradition handling, cultural protocols       |
| east_asian_philosopher | Taoism, Confucianism, Shinto, Chinese folk religion, Korean folk, etc.       | Syncretism, non-theistic cosmologies              |
| mystic_guide           | Sufism, Kabbalah, Christian mysticism, Tantra, Neoplatonism, New Age, etc.    | Experiential / esoteric claims                    |
| secular_observer       | Atheism, agnosticism, humanism, scientific naturalism, philosophical naturalism | Empirical counterpoints, historical criticism     |
| historian_archivist    | Origins, textual criticism, archaeology, evolution of traditions             | Chronology, provenance, forgery detection         |
| comparative_scholar    | Cross-tradition patterns, typology, phenomenology of religion                | Parallel structures without forced unity          |
| ethicist_mediator      | Harm, power, colonialism, gender, sexuality, violence in religious contexts   | Sensitivity + free-inquiry balance                |
| user_empath            | User intent, cultural background, emotional state, accessibility             | Tone, depth, and safety of the final answer       |

**Additional specialist agents can be spun up later** — e.g.,
Zoroastrian, Yazidi, Cao Dai, modern pagan, Eckankar, Raëlism,
Scientology, contemporary African diaspora traditions, etc. — and
temporarily join relevant deliberations. Adding a permanent agent is
a Council decision (see §6).

### 2.1 What each agent is *not*

- **Not a believer, opponent, or advocate.** Each agent is an expert
  on a tradition, not a member of it. The agent's job is accurate
  representation, not endorsement.
- **Not a single perspective.** A tradition is internally diverse.
  Each agent model must surface that diversity within the tradition
  (e.g., the dharmic_sage must distinguish Theravada from Mahayana
  from Vajrayana, not collapse them; the abrahamic_guardian must
  distinguish Catholic, Orthodox, and Protestant readings).
- **Not the final word.** All agents deliberate; the verdict is
  emergent, not autocratic.

---

## 3. Decision protocol

> **TODO:** Translate each step into a concrete procedure with named
> artifacts. The flow below is the placeholder.

1. **Routing.** Any training document, fine-tuning example, or high-
   stakes query is routed to the relevant subset of agents (minimum 3).
   Routing is based on domain tags on the input.
2. **Independent analyses.** Agents produce independent analyses
   without seeing each other's drafts first. This is to prevent
   groupthink and to surface genuine disagreement.
3. **Structured debate round.** Claims → counter-claims → evidence.
   Each agent cites to primary sources or, where primary sources are
   unavailable, to the strongest available secondary source with
   attribution.
4. **Consensus threshold:**
   - **Unanimous preferred** for corpus admission and core doctrinal
     representations.
   - **Supermajority (⅔ of voting agents)** acceptable for non-core
     issues (e.g., tone, disclaimer strength, retrieval ranking).
   - **Deadlock → escalate to human oversight (contributor) or
     withhold strong assertion.** Deadlock never defaults to either
     side; it defaults to silence with attribution.
5. **Final output is a Council Verdict** containing:
   - Canonical representation of the claim/event/practice
   - Known internal diversity / disputes within the relevant tradition(s)
   - External scholarly consensus (if any)
   - Explicit uncertainty markers (e.g., "contested," "minority
     position," "no consensus")
   - Recommended disclaimers or tone for the final answer

### 3.1 Decision record

Every Council verdict is recorded in `docs/governance/verdicts/`
with:

- **Verdict ID** — `YYYY-NNN-shortname`
- **Date** — when the verdict was issued
- **Query / scope** — what was decided
- **Agents involved** — which of the roster participated
- **Verdict** — the canonical representation
- **Reasoning** — summary, with citations
- **Dissent** — minority positions, with agent IDs
- **Effective date** — when the verdict takes effect
- **Review date** — when the verdict is automatically revisited
  (default 12 months; 24 months for corpus admission; 6 months for
  incident-response verdicts)

---

## 4. Scoping & training guardrails

- **Include every tradition that has (or had) living adherents or
  significant historical footprint.** Weight by primary-source volume
  and living community size *only for retrieval ranking*, never for
  truth value.
- **Reject datasets that systematically erase minority or indigenous
  voices.** A corpus that contains only major-tradition sources is not
  acceptable. A corpus that contains majority-tradition sources plus
  active misrepresentation of minority traditions is a hard rejection.
- **Flag and quarantine any material that treats one tradition's
  metaphysics as objective fact.** Quarantined material does not
  enter the training set without explicit Council approval.
- **Maintain a living "Controversy Register"** in
  `docs/governance/controversies/` of topics that repeatedly deadlock
  the Council. The register is itself a Council document (see §6).

### 4.1 Phase 1 design constraint (data layer)

Phase 1 ships the Christian Bible corpus first, but the **data layer
must be designed so that adding a new tradition is a config change,
not a code rebuild.** Every tradition gets:

- The same canonical schema (books → chapters → verses, with tradition-
  appropriate adaptations — e.g., Quran surah/ayah, Veda mandala/sukta).
- The same citation format on the API surface (Genesis 1:1 / Quran
  2:255 / Bhagavad Gita 2.47, etc.).
- The same cross-reference API (find parallel passages across corpora).
- A tradition-specific lexicon surface (Brown-Driver-Briggs for Hebrew,
  Lane's for Arabic, Monier-Williams for Sanskrit, etc.).

The agent roster above is the architecture for review; the data
schema is the architecture for content. The two are deliberately
co-designed. See [`docs/data-schema.md`](../data-schema.md) for the
parallel-structure examples.

---

## 5. Runtime behavior (when the main AI answers a user)

> **TODO:** This is the runtime contract that the main AI surface
> follows. Phase 1 implements a deterministic subset (retrieval +
> citation only). Phase 2 extends this to Council-routed answers.
> The current `agents.md` in the repo root captures the existing
> runtime contract for the four-agent Abrahamic slice.

- **The Council can be invoked on-demand** (the user asks for a
  specific kind of answer) **or by heuristic** (religious keywords,
  sacred-text citations, moral claims grounded in religion, etc.).
- **Default posture: descriptive + multi-perspective.** When the
  Council's verdict is multi-perspective, the answer is too.
- **Always:**
  - Attribute claims to sources (tradition, commentator, era).
  - Surface internal diversity within a tradition.
  - Flag uncertainty explicitly.
  - Use the tradition's own preferred terms for itself and its
    practices where those terms exist.
- **Never:**
  - Rank religions by "truth."
  - Perform or simulate sacraments.
  - Claim personal revelation or spiritual status.
  - Soft-pedal historical violence or doctrinal contradictions when
    asked directly.
  - Refuse a question purely because the topic is religious.

---

## 6. Evolution of the Council

- **Amendment rule.** Any change to membership, principles, or
  protocol requires a recorded Council vote + human approval.
- **Versions.** This document is versioned. Bumps are recorded in
  the git history. v1.0 happens when a real Council is constituted;
  subsequent major versions (v2.x) require a recorded vote and a
  public comment period.

### 6.1 Version history

- **v0.3-stub (2026-07-31, this version)** — long-form split out of
  `COUNCIL.md` for legibility. Principles, agent roster, decision
  protocol, scoping guardrails, runtime behavior, and evolution
  rules carried over from v0.2-stub with light editing.
  Coordination with `agents.md` clarified: `agents.md` is the
  runtime contract for any agent that uses this data; this doc is
  the long-form Council spec.
- **v1.0** — drafted when a real Council is constituted. Every
  TODO in this document becomes either a real policy or is folded
  into v1.0 with rationale for why it was dropped.

---

## 7. Open questions (to resolve before v1.0)

1. What is the agent runtime (LLM backbone, retrieval plumbing,
   deliberation scheduling)? Defer to Phase 2.
2. What is the cost ceiling per verdict? (Council deliberation is
   expensive; budget matters.)
3. How are agent definitions versioned when the underlying traditions
   evolve? (The dharmic_sage of 2027 should incorporate any new
   dharmic scholarship that has emerged.)
4. What is the relationship between Council verdicts and the
   deterministic Phase 1 retrieval? (Verdict overrides retrieval?
   Retrieval feeds verdict? Both?)
5. How does the Council interface with downstream consumers
   (deployers, integrators, app developers using the dataset)?
6. What is the data-retention policy for governance deliberations?
7. How are conflict-of-interest disclosures handled for Council
   members (when the Council is human, not AI)?
8. What is the named project owner / tie-breaker when the Council
   deadlocks?
