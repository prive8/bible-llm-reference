#!/usr/bin/env python3
"""Sister-script test runner for the bible package.

Stdlib-only (no pytest). Each test is a top-level function whose name starts
with `t_`. Run from the repo root:

    python3 tests/run_all.py

Exit code 0 = all pass. Non-zero = failures.

Convention: tests exercise the public surface (`bible.lookup`,
`bible.parallel`, `bible.strongs`) end-to-end. They do NOT mock data; they
load the real KJV + translations + Strong's from the repo. If you find
yourself wanting a mock, you're probably testing implementation, not
contract — write a unit test in `tests/unit/` instead.
"""
from __future__ import annotations

import json
import sys
import traceback
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bible.lookup import (  # noqa: E402
    extract_strongs_nums,
    list_translations,
    load_kjv,
    load_strongs_greek,
    load_strongs_hebrew,
    parse_ref,
    strip_strongs_tags,
)
from bible.parallel import run_parallel  # noqa: E402
from bible.strongs import run_strongs  # noqa: E402
from bible.search import get_bm25_index, run_search  # noqa: E402

# ---------------------------------------------------------------------------
# Mini-framework: results + reporter
# ---------------------------------------------------------------------------

_results: list[tuple[str, str, str]] = []


def _can_unicode() -> bool:
    try:
        "✓".encode(sys.stdout.encoding or "ascii")
        return True
    except Exception:
        return False


ICON_PASS = "✓" if _can_unicode() else "[PASS]"
ICON_FAIL = "✗" if _can_unicode() else "[FAIL]"


def _capture_run(fn, *args, **kwargs):
    """Run fn() with stdout captured; return (parsed_json_if_json_flag, text)."""
    buf = StringIO()
    with redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


def _assert(cond: bool, msg: str = "assertion failed"):
    if not cond:
        raise AssertionError(msg)


def _register(name: str):
    """Decorator: wrap fn so it appends to _results and prints PASS/FAIL."""
    def deco(fn):
        def wrapper():
            try:
                fn()
                _results.append((name, "PASS", ""))
                print(f"  {ICON_PASS} {name}")
            except AssertionError as e:
                _results.append((name, "FAIL", str(e) or "assertion failed"))
                print(f"  {ICON_FAIL} {name}: {e or 'assertion failed'}")
            except Exception as e:
                _results.append((name, "ERROR", f"{type(e).__name__}: {e}"))
                print(f"  {ICON_FAIL} {name}: {type(e).__name__}: {e}")
                traceback.print_exc()
        wrapper.__name__ = name
        # Stash in module globals so the runner can find us by name
        globals()[name] = wrapper
        return wrapper
    return deco


# ---------------------------------------------------------------------------
# Reference parser
# ---------------------------------------------------------------------------

@_register("t_parse_john_3_16")
def t_parse_john_3_16():
    _assert(parse_ref("John 3:16") == ("John", 3, 16, 16))


@_register("t_parse_genesis_1_1")
def t_parse_genesis_1_1():
    _assert(parse_ref("Genesis 1:1") == ("Genesis", 1, 1, 1))


@_register("t_parse_range")
def t_parse_range():
    _assert(parse_ref("Psalm 23:1-6") == ("Psalms", 23, 1, 6))


@_register("t_parse_whole_chapter")
def t_parse_whole_chapter():
    book, ch, vs, ve = parse_ref("1 Cor 13")
    _assert(book == "1 Corinthians", f"book={book}")
    _assert(ch == 13)
    _assert(vs is None)
    _assert(ve is None)


@_register("t_parse_alias_jn")
def t_parse_alias_jn():
    _assert(parse_ref("jn 3:16")[0] == "John")


@_register("t_parse_alias_1jn")
def t_parse_alias_1jn():
    _assert(parse_ref("1jn 4:8")[0] == "1 John")


@_register("t_parse_garbage_returns_none")
def t_parse_garbage_returns_none():
    _assert(parse_ref("foo bar baz") is None)


# ---------------------------------------------------------------------------
# KJV + Strong's
# ---------------------------------------------------------------------------

@_register("t_kjv_loads")
def t_kjv_loads():
    kjv = load_kjv()
    _assert("books" in kjv)
    _assert(len(kjv["books"]) >= 66, f"got {len(kjv['books'])}")


@_register("t_kjv_genesis_1_1_text")
def t_kjv_genesis_1_1_text():
    kjv = load_kjv()
    gen = next(b for b in kjv["books"] if b["name"] == "Genesis")
    v1 = gen["chapters"][0]["verses"][0]
    _assert(v1["text"].startswith("In the beginning"), v1["text"])


@_register("t_kjv_genesis_1_1_strongs_h1254")
def t_kjv_genesis_1_1_strongs_h1254():
    kjv = load_kjv()
    gen = next(b for b in kjv["books"] if b["name"] == "Genesis")
    v1 = gen["chapters"][0]["verses"][0]
    nums = extract_strongs_nums(v1["text"], book="Genesis")
    _assert("H1254" in nums, f"nums={nums}")


@_register("t_strip_strongs_tags")
def t_strip_strongs_tags():
    cleaned = strip_strongs_tags("In the <S>1254</S> beginning <S>430</S> God")
    _assert("<S>" not in cleaned)
    _assert("</S>" not in cleaned)
    # Tags leave double-spaces — that's fine, the consumer normalizes.
    _assert("beginning" in cleaned)
    _assert("God" in cleaned)


@_register("t_strongs_hebrew_h1254")
def t_strongs_hebrew_h1254():
    entry = load_strongs_hebrew().get("H1254")
    _assert(entry is not None, "H1254 missing")
    _assert("lemma" in entry or "xlit" in entry)


@_register("t_strongs_greek_g25")
def t_strongs_greek_g25():
    _assert(load_strongs_greek().get("G25") is not None)


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------

@_register("t_list_translations_count")
def t_list_translations_count():
    names = list_translations()
    # 13 translations in translations/ (KJV is at root, not in this dir)
    _assert(len(names) == 13, f"got {len(names)}: {names}")


@_register("t_required_translations_present")
def t_required_translations_present():
    names = set(list_translations())
    expected = {"YLT", "WEB", "GNV", "DRB", "RSV", "LUT", "SYNOD",
                "RV1960", "CUV", "UKRK", "TISCH", "LXX", "WLCa"}
    _assert(expected.issubset(names), f"missing: {expected - names}")


# ---------------------------------------------------------------------------
# Parallel lookup
# ---------------------------------------------------------------------------

@_register("t_parallel_genesis_1_1_has_13_rows")
def t_parallel_genesis_1_1_has_13_rows():
    out = _capture_run(run_parallel, "Genesis 1:1", want_json=True)
    data = json.loads(out)
    _assert("translations" in data, list(data.keys()))
    n_trans = len(data["translations"])
    _assert(n_trans >= 13, f"only {n_trans} translations returned")


@_register("t_parallel_john_3_16_with_strongs")
def t_parallel_john_3_16_with_strongs():
    out = _capture_run(run_parallel, "John 3:16", want_json=True, want_strongs=True)
    data = json.loads(out)
    _assert("KJV" in data["translations"])
    _assert("strongs" in data, list(data.keys()))


# ---------------------------------------------------------------------------
# Strong's CLI
# ---------------------------------------------------------------------------

@_register("t_strongs_cli_h1254")
def t_strongs_cli_h1254():
    out = _capture_run(run_strongs, "H1254")
    _assert("H1254" in out)
    # The lemma renders with Hebrew chars; we just verify the definition line
    # is present (locale/encoding inside redirect_stdout can escape the
    # Hebrew codepoints).
    _assert("Definition:" in out, out[:300])
    _assert("create" in out, out[:400])


@_register("t_strongs_cli_genesis_1_1")
def t_strongs_cli_genesis_1_1():
    out = _capture_run(run_strongs, "Genesis 1:1")
    _assert("Strong's numbers in Genesis 1:1" in out)
    _assert("H1254" in out)


# ---------------------------------------------------------------------------
# Legacy bible-query.py (deprecation path)
# ---------------------------------------------------------------------------

@_register("t_legacy_bible_query_does_not_inline_strongs_into_text")
def t_legacy_bible_query_does_not_inline_strongs_into_text():
    """Regression test for the bug fixed 2026-09-09:
    `bible-query.py --strongs` used to inline lemma+gloss into the English
    text, producing unreadable output. Verify the legacy script now emits
    clean English with Strong's refs on separate lines.
    """
    import os
    import subprocess
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(
        [sys.executable, "bible-query.py", "John 3:16", "--strongs"],
        capture_output=True, text=True, cwd=ROOT, env=env, encoding="utf-8", errors="replace",
    )
    _assert(p.returncode == 0, f"exit {p.returncode}: {p.stderr}")
    # The English line should be clean — no Hebrew interleaved
    for line in p.stdout.splitlines():
        if "[John 3:16]" in line:
            _assert("בִּכּוּרָה" not in line, f"inlined Hebrew in: {line}")
            _assert("God so loved the world" in line, line)
            break


# ---------------------------------------------------------------------------
# Search (BM25) tests (Milestone 3A)
# ---------------------------------------------------------------------------

@_register("t_search_faith_without_works")
def t_search_faith_without_works():
    idx = get_bm25_index("KJV")
    res = idx.search("faith without works", limit=5)
    _assert(len(res) > 0, "expected search results")
    top = res[0]
    _assert(top["reference"] in ("James 2:20", "James 2:26"), f"unexpected top result: {top['reference']}")
    _assert("faith without works" in top["text"].lower())


@_register("t_search_no_results")
def t_search_no_results():
    idx = get_bm25_index("KJV")
    res = idx.search("zyxwvutsrqponmlkjihgfedcba9876543210", limit=5)
    _assert(len(res) == 0, f"expected no results, got {res}")


@_register("t_search_translation_web")
def t_search_translation_web():
    idx = get_bm25_index("WEB")
    res = idx.search("light", limit=5)
    refs = [r["reference"] for r in res]
    _assert("Genesis 1:3" in refs, f"expected Genesis 1:3 in {refs}")


@_register("t_search_cli_json")
def t_search_cli_json():
    out = _capture_run(run_search, "faith without works", limit=2, as_json=True)
    data = json.loads(out)
    _assert(isinstance(data, list) and len(data) == 2, f"unexpected data: {data}")
    _assert("reference" in data[0] and "score" in data[0])


@_register("t_search_multilingual_wlca_hebrew")
def t_search_multilingual_wlca_hebrew():
    idx = get_bm25_index("WLCa")
    res = idx.search("ברא", limit=5)
    refs = [r["reference"] for r in res]
    _assert("Genesis 1:1" in refs or "Genesis 1:27" in refs, f"expected Genesis 1 in {refs}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"\nRunning sister-script tests from {ROOT}\n")

    # Find all t_-prefixed test wrappers and invoke them
    test_fns = [(n, v) for n, v in globals().items()
                if n.startswith("t_") and callable(v)]
    test_fns.sort()
    for name, fn in test_fns:
        fn()

    passed = sum(1 for _, s, _ in _results if s == "PASS")
    failed = len(_results) - passed

    print(f"\n{'='*60}")
    print(f"  {passed} passed, {failed} failed (of {len(_results)})")
    print(f"{'='*60}\n")

    if failed:
        for name, status, detail in _results:
            if status != "PASS":
                print(f"  [{status}] {name}: {detail}")
        sys.exit(1)
    sys.exit(0)
