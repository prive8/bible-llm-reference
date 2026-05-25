# Bible LLM Reference

A public domain Bible dataset and reference tool designed for fast research and clarity. Built for developers, researchers, and translation teams who need structured Scriptural data for LLM training, toolbuilding, and study.

## Core Design Principles

### Research Speed & Clarity
Every decision in this project prioritizes **fast comprehension over aesthetic appeal**. Data is structured for direct machine access. No buried context. No ambiguity. When you query this dataset, you get answers with clear provenance.

### Grace and Truth Balance
This tool is designed to avoid two failure modes:
- **Sterile academic distance** — treating Scripture as mere text without weight
- **Shallow positivity** — reducing the Bible to self-help aphorisms

The data and tooling should support answers that are both **rigorous** and **pastorally honest**.

### The Local Infrastructure Problem
A massive push in the open-source Bible LLM space is optimizing models to run locally via Ollama/Proxmox on low-power hardware (Raspberry Pis, old PCs). This is vital for:
- Translation teams operating in off-grid or restricted-access areas
- Pastors without reliable internet
- Ministries requiring data sovereignty

This project is infrastructure-agnostic. The data works with any LLM stack — cloud or local.

## Unofficial "Rules of the Road"

The faith-tech development community (spearheaded by platforms like [faith.tools](https://faith.tools)) has rallied around ethical and functional guardrails that shape this project's product design:

### Do Not Anthropomorphize
Apps that mimic historical figures or Jesus directly (e.g., "Text with Jesus") face heavy pushback for crossing a healthy boundary. This project makes it explicitly clear that users interact with a **computational tool**, not a spiritual entity. Every output should make it obvious you're working with structured text and software.

### Grace and Truth Balance (Expanded)
Models built on this data must be tuned to avoid:
- Sterile, overly critical academic analysis
- Shallow, therapeutic "toxic positivity"

The Bible contains hard truths, difficult histories, and questions without easy answers. A Bible LLM tool should help users engage with all of it honestly.

### Local-First Architecture
Where possible, this project enables local-only operation. No mandatory cloud dependency. No telemetry. Data stays on your infrastructure.

## What This Project Provides

### Bible Text Data
Structured JSON corpora for multiple public domain translations:

| Translation | Code | Language | Notes |
|-------------|------|----------|-------|
| King James Version | KJV | English | 1769, with Strong's numbers |
| Young's Literal Translation | YLT | English | 1898 |
| World English Bible | WEB | English | public domain |
| Geneva Bible | GNV | English | 1599 |
| Douay-Rheims | DRB | English | 1609/1610 |
| Revised Standard Version | RSV | English | 1952 |
| Luther Bibel | LUT | German | 1912 |
| Russian Synodal | SYNOD | Russian | 1876 |
| Reina-Valera 1960 | RV1960 | Spanish | public domain |
| Chinese Union Version | CUV | Chinese | public domain |
| Ukrainian Bible | UKRK | Ukrainian | Kulykh, 1903 |
| Tischendorf Greek NT | TISCH | Greek | 8th ed. 1869-72, Strong's |
| Septuagint | LXX | Greek | 52 books |
| Westminster Leningrad Codex | WLCa | Hebrew | with Strong's numbers |

All files use a normalized nested structure:
```json
{
  "translation": "King James Version (1769) with Strong's Numbers",
  "books": [
    {
      "name": "Genesis",
      "chapters": [
        {"chapter": 1, "verses": [{"verse": 1, "text": "In the beginning..."}]}
      ]
    }
  ]
}
```

### Strong's Concordance
Hebrew and Greek lexicon data (`strongs_data/`):
- `hebrew/strongs-hebrew-dictionary.js` — H1–H8674 (8,674 entries)
- `greek/strongs-greek-dictionary.js` — G1–G5624 (5,624 entries)

Each entry includes:
- Lemma (original word)
- Transliteration
- Pronunciation
- Derivation
- Strong's definition
- KJV renderings

### Query Tool
`bible-query.py` — Loads the full KJV corpus, searches relevant passages by keyword, and formats results with verse citations. Drop-in ready for LLM pipelines.

## Quick Start

```bash
# Query the KJV directly
python3 bible-query.py "faith without works is dead"

# Search for a specific concept
python3 bible-query.py "what does the Bible say about baptism"

# Load in your Python project
import json
with open('kjv.json') as f:
    kjv = json.load(f)
    genesis_1_1 = kjv['books'][0]['chapters'][0]['verses'][0]
    print(genesis_1_1['text'])
```

## Data Sources

- **KJV + Strong's**: Bolls Bible API (`bolls.life/api`) — free, no key required
- **All other translations**: Bolls Bible API — same source, normalized
- **Strong's lexicons**: Open Scriptures (`github.com/openscriptures/strongs`) — CC-BY-SA

All data is public domain or permissively licensed. See individual source repositories for details.

## Project Structure

```
bible-llm-reference/
├── kjv.json                    # King James Version with Strong's tags
├── kjv_strongs_flat.json       # Flat verse format (for NLP pipeline ingestion)
├── bible-query.py              # Query CLI tool
├── normalize.py                # JSON normalization utilities
├── normalize_all.py            # Batch normalizer for all translations
├── translations/                # Additional Bible versions (JSON)
│   ├── YLT.json
│   ├── WEB.json
│   ├── GNV.json
│   ├── RSV.json
│   ├── LUT.json
│   ├── SYNOD.json
│   ├── RV1960.json
│   ├── CUV.json
│   ├── UKRK.json
│   ├── TISCH.json
│   ├── LXX.json
│   └── WLCa.json
└── strongs_data/               # Hebrew + Greek lexicon
    ├── hebrew/
    │   ├── strongs-hebrew-dictionary.js
    │   ├── strongs-hebrew-spellings.dic
    │   └── strongshebrew.dat
    └── greek/
        ├── strongs-greek-dictionary.js
        ├── strongs-greek-spellings.dic
        └── strongsgreek.dat
```

## Version Notes

- KJV text includes embedded Strong's numbers as `<S>nnnn</S>` tags for word-level Hebrew/Greek lookup
- All translations normalized to the same JSON schema for easy cross-version comparison
- Non-66-book translations (LXX, WLCa, etc.) retain their native book structure

## Contributing

This project is nascent. If you're working on Bible LLM tooling, translation data, Strong's integration, or local-inference optimization, we'd welcome contributions.

Key areas for expansion:
- More public domain translations (particularly more early English and non-English versions)
- Improved Strong's → verse mapping for training pipelines
- Integration examples for Ollama, llama.cpp, and other local inference engines
- Cross-version parallel passage lookup
- Hebrew/Greek word frequency analysis for NLP training

## License

Each data source carries its own license:
- **KJV + translations via Bolls**: Public domain / fair use — verify with your jurisdiction
- **Strong's lexicons** (Open Scriptures): CC-BY-SA

Always verify licensing requirements for your specific use case before building commercial applications.