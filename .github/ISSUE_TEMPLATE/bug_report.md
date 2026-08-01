---
name: Bug report
about: Report a bug in the Bible LLM Reference tooling
title: "[bug] "
labels: bug
assignees: ''
---

## Summary

<!-- One paragraph describing the bug. -->

## Reproduction

<!-- Smallest steps to reproduce. -->

```
python3 bible-query.py "John 3:16"
```

**Expected output**

<!-- What you expected to see. -->

**Actual output**

<!-- What you actually saw. Pasting the actual output (including any traceback) is the most useful thing. -->

## Environment

- Python version (`python3 --version`)
- OS (`uname -a` on Linux/macOS, Windows version where relevant)
- Repo commit (`git log -1 --oneline`)
- Are you running from a `git clone` or a packaged install?

## Data

- Which translation(s) were involved? (KJV, YLT, etc.)
- Which book / chapter / verse (if relevant)?
- Was Strong's enrichment involved? (`--strongs` flag)

## Severity

<!-- One of: blocker (can't run any command), major (can't run a specific command), minor (cosmetic / docs), nice-to-have. -->

## Checklists

- [ ] I have read [`HANDOFF.md`](../../HANDOFF.md) §1–§4 (the vision and what's in the repo)
- [ ] I have searched existing issues for this bug
- [ ] I have not modified the data files (`kjv.json`, `translations/*.json`, `strongs_data/`)

## Anything else

<!-- Anything else that might help — screenshots, links, related issues, etc. -->
