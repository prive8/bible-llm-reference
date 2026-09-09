# 2026-09-09 — Phase 3.1 Quran Ingestion + Multi-Tradition Adapter (v0.6.0)

## Done

- **Phase 3.1 Pilot Tradition: Quran shipped (ADR-009).**
  - Canonical public-domain source identified by Hermes (`fawazahmed0/quran-api`, Unlicense) ingested via `scripts/ingest_quran.py`.
  - 6 editions committed to `data/quran/` (~8.2 MB):
    - Saheeh International (1996)
    - Abdullah Yusuf Ali (1934)
    - Mohammed Marmaduke Pickthall (1930)
    - Mufti Taqi Usmani
    - A. J. Arberry (1955)
    - Arabic Quran Uthmani Hafs recitation (King Fahd Quran Complex)
  - Data schema follows `docs/data-schema.md` §2 (`tradition: "islam"`, `structure: "surah_ayah"`, `divisions` with full 114 surah metadata).
  - Provenance documented in `data/quran/README.md`.
- **Quran Adapter Module (`bible/quran.py`).**
  - Full 114-surah metadata and alias table (transliterations, prefixes, English titles, and named verses such as Ayat al-Kursi).
  - Robust reference parsing: `"Quran 2:255"`, `"Al-Baqarah 2:255"`, `"2:255"`, `"Ayat al-Kursi"`, `"Quran 112:1-4"` (ranges).
  - Multi-edition parallel retrieval with lazy JSON caching (`@lru_cache`).
  - Terminal presentation helper `run_quran` with UTF-8 safe Arabic text rendering across Windows and Linux.
- **CLI Subcommand: `python -m bible quran`.**
  - Added to `bible/__main__.py` with `--translations` / `-t` and `--json` support.
- **Sister-Script Test Suite expanded to 48 tests.**
  - Added 10 tests in `tests/run_all.py` covering data existence, 114 surah count, canonical and alias ref parsing, ranges, garbage rejection, Arabic text integrity, multi-translation alignment, and CLI JSON contracts.
  - Test suite passes cleanly: **48 passed, 0 failed**.
- **Milestone 3B Semantic Search Architecture (ADR-010).**
  - Pure stdlib vector mathematics engine (`bible/semantic.py`) with dot product, Euclidean norm, and cosine similarity.
  - Flat binary float32 vector index storage (`.bin` + `.json`) for sub-millisecond in-memory vector cosine similarity search.
  - Pluggable embedder backends: `local` (`sentence-transformers`, `all-MiniLM-L6-v2`, ~80MB), `mock` (deterministic stdlib hash projection for tests), and `nim` (opt-in hosted API).
  - CLI: `python -m bible semantic "finding peace in suffering" [-n 10] [--tradition all|bible|islam] [--json]`.
  - Offline indexer: `scripts/index_embeddings.py` ready to generate production embeddings for Bible + Quran corpora.
  - `pyproject.toml` declared `[project.optional-dependencies] embeddings = ["sentence-transformers>=2.2.0", "numpy>=1.20.0"]`. Base install remains pure zero-dependency stdlib.
  - 5 new tests in `tests/run_all.py` — total suite at **53 passed, 0 failed**.
- **Governance & Docs:**
  - **ADR-009** accepted (Quran as Phase 3 Pilot Tradition).
  - **ADR-010** accepted (Milestone 3B Semantic Search Architecture).
  - `docs/phase3-scope-quran.md` marked as shipped.
  - `pyproject.toml` bumped to version 0.6.0.
  - `CHANGELOG.md`, `README.md`, and `HANDOFF.md` updated.

## Blocked

- Nothing.

## Ready for Hermes

- **Run offline embeddings:** When running inside Hermes (WSL with GPU/local Python), Hermes can run:
  ```bash
  pip install -e .[embeddings]
  python scripts/index_embeddings.py --backend local --name default
  ```
  This will embed all ~31,102 Bible verses and ~6,236 Quran ayahs into `data/embeddings/default_vectors.bin` and `data/embeddings/default_meta.json`.
- **Query semantic search:**
  ```bash
  python -m bible semantic "finding peace in suffering"
  python -m bible semantic "verses about mercy" --tradition all
  ```

## Verification

```
$ python tests/run_all.py
  ... 53 ✓ ...
  53 passed, 0 failed (of 53)

$ python -m bible quran "Al-Baqarah 2:255"
  (displays Arabic Uthmani + Saheeh International English)

$ python -m bible semantic --help
  (displays semantic search CLI options)
```
