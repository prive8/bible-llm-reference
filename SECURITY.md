# Security Policy

This is a public open-source repository. There are no secrets in the codebase. The repo contains only public-domain or CC-BY-SA religious text data and stdlib-only Python tooling.

## Reporting a vulnerability

If you discover a security issue in this repo, please report it privately to the project owner:

- **Email:** [prive8pierce@gmail.com](mailto:prive8pierce@gmail.com)
- **Subject prefix:** `[bible-llm-reference security]`

Please do **not** open a public issue for security problems. Public disclosure gives attackers a head start and doesn't help users.

## What counts as a security issue here

This repo is small and the surface is narrow. Genuine security issues are rare. Things that would count:

- **A redaction bug** — if a contributor accidentally commits a private key, an API token, or any credential. (Hasn't happened; let's keep it that way.)
- **A path traversal or arbitrary file read** in `bible-query.py` or the planned `bible/` package — if the CLI ever accepts paths from untrusted input, that becomes a concern.
- **A Strong's license violation** — if a derivative work is published without CC-BY-SA attribution, that's a legal/security issue for the project.
- **A data corruption bug** — if the merger / pipeline silently produces wrong canonical rows (e.g., wrong book / chapter / verse numbers), that's a correctness issue with downstream blast radius.

## What does NOT count

- **Doctrinal disagreements** — the project's design intentionally surfaces doctrinal diversity. Disagreement with the framing is not a security issue.
- **Performance / scalability issues** — file an issue, not a security report.
- **Feature requests** — file an issue, not a security report.

## Response

- **Acknowledgment:** within 7 days.
- **Triage:** within 30 days for confirmed issues.
- **Fix:** depends on severity. Critical issues (data integrity, credential leak) get a same-day patch. Lower-severity issues ship on the next regular cadence.

## Disclosure preference

Coordinated disclosure is preferred. We'll work with you on a disclosure timeline that gives users time to update.
