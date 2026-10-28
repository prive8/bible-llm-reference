#!/usr/bin/env python3
"""Threshold gate for a retrieval evaluation report.

Reads a markdown report produced by `scripts/run_eval.py` and fails if any
retrieval path's recall@10 is below its threshold.

Usage:
    python scripts/eval_gate.py --report /tmp/eval_report.txt \
        --threshold bm25=0.06 --threshold semantic=0.25 --threshold hybrid=0.22

    python scripts/eval_gate.py --report /tmp/eval_report.txt \
        --gate local/v2-held_out

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
   live in `config/retrieval_gates.json`, keyed by profile and split.

4. **The report must match the gate.** `--gate` names an entry in that
   config, and the report must say it was produced by that profile on
   that split. Gating a dev report against held-out thresholds (or a
   MiniLM report against 3-large thresholds) would compare numbers from
   two different measurements and mean nothing.

5. **Stdlib only.** `bible/` is stdlib-only by ADR-001 and this script runs
   in the same CI job, so it must not import anything outside the standard
   library.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GATES_CONFIG = REPO_ROOT / "config" / "retrieval_gates.json"


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


def load_gates(config_path: Path) -> dict:
    """Load the gate configuration."""
    if not config_path.exists():
        raise FileNotFoundError(f"gate config not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_report_header(report: str) -> dict:
    """Read the profile/split lines run_eval.py writes into its report.

    Returns a dict with keys ``profile``, ``benchmark``, ``split``
    (each empty string when the report does not state it).
    """
    header: dict[str, str] = {"profile": "", "benchmark": "", "split": ""}
    for key in header:
        # The report writes "**Split:**" — match the key case-insensitively
        # so a rename of the header label cannot silently stop the gate
        # from seeing the mismatch.
        m = re.search(
            rf"^\*\*{key}:\*\*\s*(\S+)\s*$",
            report,
            re.MULTILINE | re.IGNORECASE,
        )
        if m:
            header[key] = m.group(1)
    return header


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
    parser.add_argument("--gate", default=None,
                        help="named gate from the config file, e.g. local/v2-held_out. "
                             "Supplies the thresholds and the expected profile/split.")
    parser.add_argument("--gates-config", type=Path, default=DEFAULT_GATES_CONFIG,
                        help="path to the gate configuration (default: config/retrieval_gates.json)")
    args = parser.parse_args(argv)

    if args.gate and args.threshold:
        print("--gate and --threshold are mutually exclusive", file=sys.stderr)
        return 2

    expected: dict = {}

    if args.gate:
        try:
            config = load_gates(args.gates_config)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"cannot read gate config: {e}", file=sys.stderr)
            return 2
        entry = config.get("gates", {}).get(args.gate)
        if entry is None:
            known = ", ".join(sorted(config.get("gates", {})))
            print(f"unknown gate {args.gate!r}. Known gates: {known}", file=sys.stderr)
            return 2
        for path_name, value in entry.get("thresholds", {}).items():
            args.threshold.append(f"{path_name}={value}")
        expected = {
            "profile": entry.get("profile", ""),
            "benchmark": entry.get("benchmark", ""),
            "split": entry.get("split", ""),
        }

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

    # A gate is only meaningful against the measurement it was derived
    # from. If the report says it came from a different profile or
    # split, the numbers are not the ones the thresholds were set
    # below, and comparing them would be meaningless at best.
    if expected:
        header = parse_report_header(report)
        mismatches = [
            f"{key}: report says {header[key]!r}, gate expects {value!r}"
            for key, value in expected.items()
            if value and header[key] and header[key] != value
        ]
        if mismatches:
            print("::error::report does not match the gate", file=sys.stderr)
            for line in mismatches:
                print(f"  {line}", file=sys.stderr)
            print("  The thresholds were derived from a different measurement.",
                  file=sys.stderr)
            return 1

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
