#!/usr/bin/env python3
"""Threshold gate for a retrieval evaluation report.

Reads a markdown report produced by `scripts/run_eval.py` and fails if any
retrieval path's recall@10 is below its threshold.

Usage:
    python scripts/eval_gate.py --report /tmp/eval_report.txt \
        --threshold bm25=0.06 --threshold semantic=0.25 --threshold hybrid=0.22

Exit codes:
    0  every path met its threshold
    1  at least one path was below threshold, or a path was missing
    2  usage error

Design notes (each of these is a failure mode this script exists to prevent):

1. **A missing row is a failure, not a pass.** The eval harness silently
   SKIPS a path whose artifact is missing (e.g. "[skip semantic] no index"),
   and then emits no row for it in the summary table. A gate that treats a
   missing row as "nothing to check" passes on the paths that did run. This
   script fails when a thresholded path has no row.

2. **Only the Summary table is parsed.** The report has a second,
   per-persona table whose rows also start with a path name
   ("| bm25 | sarah | 8 | 0.025 | ..."). Parsing the whole document risks
   matching a per-persona row instead of the aggregate. We slice out the
   "## Summary" section first and parse only that.

3. **Thresholds are supplied by the caller, not hardcoded.** The v1 and v2
   benchmarks have different scales and different baselines; the numbers
   live with the workflow that uses them.

4. **Stdlib only.** `bible/` is stdlib-only by ADR-001 and this script runs
   in the same CI job, so it must not import anything outside the standard
   library.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def extract_summary(report: str) -> str:
    """Return the '## Summary' section of a report, or the whole report if
    the section header is absent."""
    if "## Summary" not in report:
        return report
    tail = report.split("## Summary", 1)[1]
    # Stop at the next top-level section header.
    for marker in ("\n## ", "\n# ", "\n---"):
        if marker in tail:
            tail = tail.split(marker, 1)[0]
    return tail


def parse_recall(summary: str, path_name: str):
    """Return the recall@10 for a path, or None if the path has no row."""
    pattern = (
        rf"\|\s*{re.escape(path_name)}\s*\|"
        r"\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|"
    )
    m = re.search(pattern, summary)
    if not m:
        return None
    return float(m.group(1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path,
                        help="markdown report from scripts/run_eval.py")
    parser.add_argument("--threshold", action="append", default=[],
                        metavar="PATH=VALUE",
                        help="threshold for a path, e.g. semantic=0.25 (repeatable)")
    args = parser.parse_args(argv)

    if not args.threshold:
        print("no thresholds given", file=sys.stderr)
        return 2

    thresholds: dict[str, float] = {}
    for item in args.threshold:
        if "=" not in item:
            print(f"malformed --threshold {item!r}; expected PATH=VALUE", file=sys.stderr)
            return 2
        name, _, value = item.partition("=")
        try:
            thresholds[name.strip()] = float(value)
        except ValueError:
            print(f"malformed threshold value in {item!r}", file=sys.stderr)
            return 2

    if not args.report.exists():
        print(f"::error::report not found: {args.report}", file=sys.stderr)
        return 1

    report = args.report.read_text(encoding="utf-8")
    summary = extract_summary(report)

    failed: list[str] = []
    for name, threshold in thresholds.items():
        recall = parse_recall(summary, name)
        if recall is None:
            # The path did not run. Do NOT treat this as a pass.
            failed.append(
                f"{name}: no row in the eval report summary "
                f"(the path may have been skipped — a missing index looks like this)"
            )
            continue
        status = "PASS" if recall >= threshold else "FAIL"
        print(f"  {name:9} recall@10={recall:.3f}  threshold={threshold:.3f}  [{status}]")
        if recall < threshold:
            failed.append(f"{name}: recall@10={recall:.3f} < threshold {threshold:.3f}")

    if failed:
        print("RETRIEVAL REGRESSION DETECTED", file=sys.stderr)
        for line in failed:
            print(f"  {line}", file=sys.stderr)
        return 1

    print("All retrieval thresholds met ("
          + ", ".join(f"{n} >= {t:g}" for n, t in thresholds.items())
          + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
