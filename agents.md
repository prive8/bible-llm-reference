# agents.md – Bible LLM Reference

This repository is the **canonical data + retrieval substrate** for the Abrahamic / Christian slice of the larger Religion & Spirituality AI.

## Agent mapping (from council.md)

| Council Agent          | How this repo is used                                      |
|------------------------|------------------------------------------------------------|
| abrahamic_guardian     | Primary retrieval source for all Protestant / Catholic / Orthodox queries |
| historian_archivist    | Exact verse + Strong’s provenance                          |
| comparative_scholar    | Parallel passage lookup across versions                    |
| ethicist_mediator      | Hard texts kept in full context (no soft-pedaling)         |

## Runtime contract for any agent that uses this data
1. Always cite exact reference + translation.
2. When Strong’s is available, surface lemma + short gloss.
3. Never invent verses or claim personal revelation.
4. Present internal diversity (different manuscript traditions, denominational readings) when relevant.
5. Output is always “structured reference text”, never “I am speaking as Scripture”.

## Quick integration example (Python)
```python
from bible_query import search_bible, parse_ref, enrich_with_strongs  # after packaging

Also drop a short pointer into the original `council.md` under the Abrahamic section:

```markdown
Data source: https://github.com/prive8/bible-llm-reference  
(Use `bible-query.py` or the packaged retrieval helpers.