# HANDOFF.md

**Deprecated 2026-10-25 — see [`README.md`](./README.md) (and [`AGENTS.md`](./AGENTS.md)).**

This was the engineering handoff: vision, milestones, conventions, and a priority list. It drifted. Large sections were a 2026-07-31 snapshot, and the 2026-10-08 priorities were left in place after that work landed. A second status document was sending the next session at stale facts.

- Status, retrieval gates, and direction: [`README.md`](./README.md)
- What to work on next, commands, and conventions: [`AGENTS.md`](./AGENTS.md)
- Rules for any agent using the data: [`RUNTIME_CONTRACT.md`](./RUNTIME_CONTRACT.md) (formerly §11 of this file)
- Governance: [`COUNCIL.md`](./COUNCIL.md)

The previous text is in git history at `e46fa7b`:

```bash
git show e46fa7b:HANDOFF.md
```

Conventions that were still true moved to `AGENTS.md`. The 2026-10-25 direction (audience, web reader, depth and cross-referencing, use cases still open) is in the README.

## Phrases the test suite still checks

`tests/run_all.py` matches these lines. They record decisions that are closed. They are not a work queue. The full write-ups are in git history at `e46fa7b` and in the ADRs.

2. **Phase 2 base model (RESOLVED 2026-09-10, v0.12.0).** Family pick: Llama-3.1-8B-Instruct. See ADR-012. Generative-voice work stays deferred.

8. **NIM embedding default hit HTTP 410 Gone (EOL 2026-08-25).** `nvidia/nv-embedqa-e5-v5` is end of life. Free-tier NIM exposes chat models and no embedding models. OpenRouter is the alternative paid path (v0.13.0). Production embeddings stay on local `all-MiniLM-L6-v2`. This is HANDOFF §8 #8.

9. **Council convening (RESOLVED 2026-09-10, v0.12.0).** `COUNCIL.md` v0.4 is constituted as an active single-contributor body. The project owner is acting chair.
