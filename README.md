# Bible LLM Reference

A public-domain Bible dataset and reference tool for LLM training, retrieval, and research. This repository is the **canonical data + retrieval substrate** for the Abrahamic / Christian slice of the larger Religion & Spirituality AI project.

> **Read first:** if you're an AI agent or new contributor, start with
> [`HANDOFF.md`](./HANDOFF.md). It captures the project's vision,
> current state, conventions, and the milestone roadmap. The
> [`COUNCIL.md`](./COUNCIL.md) doc is the governance constitution.

---

## What this is

Generates personalized, citation-grounded answers about the Bible across 13 translations and the Strong's Hebrew/Greek lexicon. Built for:

- LLM training pipelines (corpus prep, JSONL export)
- RAG / retrieval workflows (exact reference + keyword search)
- Scholarly research (parallel passage lookup, original-language gloss)
- Local-first inference (no mandatory cloud dependency)

**Not a chatbot.** This is a structured reference tool. Every output is grounded in a citation. See [`HANDOFF.md` §11](./HANDOFF.md#11-runtime-contract-for-any-agent-using-this-data) for the runtime contract that governs any agent using this data.

---

## Highlights

- **13 translations** in normalized JSON: KJV (with Strong's tags), YLT, WEB, GNV, DRB, RSV, LUT, SYNOD, RV1960, CUV, UKRK, TISCH, LXX, WLCa
- **Strong's Concordance** for Hebrew (H1–H8674) and Greek (G1–G5624), via Open Scriptures
- **Exact reference parsing** — `John 3:16`, ranges (`John 3:16-18`), abbreviations (`1 Cor`, `Ps`)
- **Keyword search** with multi-word scoring and primary/related ranking
- **Strong's enrichment** on demand — `<S>1254</S>` tags expanded to lemma + short gloss
- **JSON output** for downstream pipelines
- **LLM-ready context block** — copy-paste formatted for RAG prompts
- **100% local, zero new dependencies** — stdlib only (Python 3.9+)

---

## Quick start

```bash
# Clone
git clone https://github.com/prive8/bible-llm-reference.git
cd bible-llm-reference

# Exact reference lookup
python3 bible-query.py "John 3:16"

# Keyword search
python3 bible-query.py "faith without works"

# With Strong's enrichment
python3 bible-query.py "John 3:16" --strongs

# JSON output
python3 bible-query.py "love" --json

# Generate a flat JSONL for embedding / training
python3 make_flat_training.py
# Output: kjv_training.jsonl

# Convert Strong's .js files to clean JSON
python3 convert_strongs_to_json.py
# Output: strongs_data/hebrew/strongs-hebrew.json + strongs_data/greek/strongs-greek.json
```

### As a Python module

```python
import json
from pathlib import Path

# Load the canonical KJV
bible = json.loads(Path("kjv.json").read_text(encoding="utf-8"))
genesis_1_1 = bible["books"][0]["chapters"][0]["verses"][0]
print(genesis_1_1["text"])
# "In the beginning God created the heaven and the earth."
```

---

## Project structure

```
bible-llm-reference/
├── HANDOFF.md                 # engineering handoff (vision, milestones, conventions)
├── COUNCIL.md                 # governance constitution
├── README.md                  # this file
├── LICENSE                    # MIT
├── CHANGELOG.md               # public API / data changes
├── CONTRIBUTING.md            # how to contribute
├── SECURITY.md                # reporting security issues
├── pyproject.toml             # packaging
├── bible-query.py             # CLI retrieval tool (exact refs + keyword + Strong's)
├── convert_strongs_to_json.py # Strong's .js → JSON
├── make_flat_training.py      # KJV → JSONL for training
├── normalize.py               # JSON normalization (one translation)
├── normalize_all.py           # batch normalizer
├── kjv.json                   # King James Version + Strong's tags
├── translations/              # 12 additional translations
├── strongs_data/              # Hebrew + Greek lexicon
├── docs/
│   ├── data-schema.md         # parallel-structure schema for multi-tradition support
│   └── governance/
│       ├── council-design.md  # long-form Council spec
│       ├── verdicts/          # (Council verdicts — when the Council forms)
│       └── controversies/     # (Controversy Register — when the Council forms)
└── .github/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Data sources

| Source | License | Notes |
|--------|---------|-------|
| KJV (1769, with Strong's) | Public domain | via Bolls Bible API |
| 12 additional translations | Public domain / fair use | via Bolls Bible API |
| Strong's Hebrew (H1–H8674) | CC-BY-SA | via Open Scriptures |
| Strong's Greek (G1–G5624) | CC-BY-SA | via Open Scriptures |

**License propagation:** The Strong's-derived lexicon data is CC-BY-SA. **Any artifact that incorporates it must carry the same license when distributed.** The rest of the codebase is MIT. Verify licensing for your specific use case before building commercial applications.

---

## Project vision

Phase 1 (current): retrieval-only study tool over the Christian Bible corpus. — **partially shipped** (the `bible-query.py` CLI is the working retrieval primitive as of 2026-07-31).

Phase 2 (deferred): generative voice fine-tune. Distill-only (start from an open-weights base like Llama, Mistral, or Qwen). Compute decision deferred.

Phase 3 (long-term): other religious corpora — Torah, Talmud, Quran, Hadith, Vedas, Upanishads, Bhagavad Gita, Dhammapada, Tao Te Ching, Book of Mormon, etc. — as a config change, not a code rebuild. The data layer is designed to scale toward this.

Read more in [`HANDOFF.md` §1–§2](./HANDOFF.md).

---

## Governance

The project has a constitution ([`COUNCIL.md`](./COUNCIL.md)) and a long-form Council design ([`docs/governance/council-design.md`](./docs/governance/council-design.md)). The Council is not yet constituted — it is a single-contributor body under the principles in `COUNCIL.md` §2. The Council forms when either a second contributor joins or the project enters Phase 2.

The runtime contract that any agent using this data must follow lives in [`HANDOFF.md` §11](./HANDOFF.md#11-runtime-contract-for-any-agent-using-this-data).

---

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md). Short version: read the handoff doc, follow the runtime contract, send a PR.

---

## Security

See [`SECURITY.md`](./SECURITY.md). This is a public repo with no secrets in the codebase. If you find a security issue, report it via the address in `SECURITY.md` — do not open a public issue.

---

## License

Code: MIT. See [`LICENSE`](./LICENSE).

Data: Each source carries its own license. See the [Data sources](#data-sources) table. Public domain or CC-BY-SA — verify with your jurisdiction before commercial use.

---

## Related projects

- **[`prive8/llm-from-scratch`](https://github.com/prive8/llm-from-scratch)** — a Karpathy-style workshop on building a GPT from scratch. Used as a reference when Phase 2 lands.
- The upstream Religion & Spirituality AI project — this repo serves the Abrahamic / Christian slice of that larger vision.

---

## Acknowledgments

- The Strong's Concordance data comes from [Open Scriptures](https://github.com/openscriptures/strongs) under CC-BY-SA.
- The translation data is sourced from the [Bolls Bible API](https://bolls.life/api/) (free, no key required).
- The runtime contract and Council design were drafted in collaboration with the project owner and OpenClaw / Hermes agents.
