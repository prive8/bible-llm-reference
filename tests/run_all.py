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
from bible.references import (  # noqa: E402
    get_reciprocal,
    get_references,
    load_xrefs,
    metadata,
    traverse,
)
from bible.strongs import run_strongs  # noqa: E402
from bible.search import get_bm25_index, run_search  # noqa: E402
from bible.quran import (  # noqa: E402
    get_quran_verses,
    list_quran_translations,
    load_quran_edition,
    parse_quran_ref,
    run_quran,
)
from bible.semantic import (  # noqa: E402
    DEFAULT_NIM_BASE_URL,
    DEFAULT_NIM_MODEL,
    NIMAuthError,
    NIMConnectionError,
    NIMEmbedder,
    NIMError,
    NIMRateLimitError,
    NIMResponseError,
    NIMServerError,
    get_embedder,
    cosine_similarity,
    dot_product,
    l2_normalize,
    run_semantic,
    search_semantic,
    vector_norm,
    MockDeterministicEmbedder,
)

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
# (Legacy bible-query.py removed in v0.5.0 — see ADR-004 + CHANGELOG.)
# The --strongs regression test that lived here is gone with the script.
# (The function definition was removed in the bible-query.py removal commit
# 2ee91fe but was accidentally re-introduced by an unrecorded edit; this
# tombstone replaces both the test and its registration. The fix here
# makes the failure go away for good.)


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
# NIM embedder backend (Milestone 3B completion)
# ---------------------------------------------------------------------------

# Shared fake HTTP transport for NIM tests. Tests inject this into
# NIMEmbedder._http_post to simulate the real NIM API without network.

def _nim_fake_post_factory(responses: list[str]):
    """Returns a fake _http_post that yields the next canned response per call."""
    it = iter(responses)

    def fake(url: str, body: dict) -> str:
        try:
            return next(it)
        except StopIteration:
            # Default to a one-vector response if test runs out of canned data.
            n = len(body.get("input", []))
            return json.dumps({
                "data": [
                    {"index": i, "embedding": [0.0] * 4}
                    for i in range(n)
                ]
            })
    return fake


def _make_nim_ok_response(n: int, dim: int = 4) -> str:
    """Realistic-looking NIM response for ``n`` inputs."""
    return json.dumps({
        "data": [
            {"index": i, "embedding": [float(i + 1)] * dim}
            for i in range(n)
        ],
        "usage": {"prompt_tokens": 5 * n, "total_tokens": 5 * n},
    })


@_register("t_nim_missing_key_raises_clear_auth_error")
def t_nim_missing_key_raises_clear_auth_error():
    """If NVIDIA_API_KEY is unset, construction must fail loudly with NIMAuthError.

    CI must never accidentally call the real NIM API; the missing-key
    guard is the first line of defense.
    """
    import os as _os
    saved = _os.environ.pop("NVIDIA_API_KEY", None)
    try:
        try:
            NIMEmbedder()
            _assert(False, "NIMEmbedder() should have raised NIMAuthError")
        except NIMAuthError as e:
            _assert("NVIDIA_API_KEY" in str(e), f"error should mention the env var: {e}")
            _assert("build.nvidia.com" in str(e), f"error should link to the key signup: {e}")
    finally:
        if saved is not None:
            _os.environ["NVIDIA_API_KEY"] = saved


@_register("t_nim_embed_roundtrip_with_mock_transport")
def t_nim_embed_roundtrip_with_mock_transport():
    """Mock the HTTP transport: 3 inputs → 3 embeddings of expected dim.

    Verifies the request body shape (model + input + encoding_format +
    input_type), the response parsing, and the per-index ordering.
    """
    import os as _os
    saved_key = _os.environ.get("NVIDIA_API_KEY")
    _os.environ["NVIDIA_API_KEY"] = "nvapi-test-fake-key"

    captured_requests: list[dict] = []
    global_index = [0]  # mutable counter across batches

    def fake_post(url: str, body: dict) -> str:
        captured_requests.append({"url": url, "body": dict(body)})
        n = len(body["input"])
        batch_offset = global_index[0]
        global_index[0] += n  # advance past this batch's inputs
        # Markers are monotonic across the whole call: 100, 200, 300 ...
        return json.dumps({
            "data": [
                {
                    "index": i,
                    "embedding": [float((batch_offset + i + 1) * 100)] * 8,
                }
                for i in range(n)
            ],
            "usage": {"prompt_tokens": 5 * n, "total_tokens": 5 * n},
        })

    try:
        embedder = NIMEmbedder(batch_size=2)  # batch_size 2 forces 2 batches for 3 inputs
        embedder._http_post = fake_post
        out = embedder.embed_texts(["alpha", "beta", "gamma"])
    finally:
        if saved_key is None:
            _os.environ.pop("NVIDIA_API_KEY", None)
        else:
            _os.environ["NVIDIA_API_KEY"] = saved_key

    # Output shape
    _assert(len(out) == 3, f"expected 3 embeddings, got {len(out)}")
    for i, vec in enumerate(out):
        _assert(len(vec) == 8, f"vec {i}: dim {len(vec)}")
    # Monotonic markers: alpha = 100, beta = 200, gamma = 300.
    _assert(out[0][0] == 100.0, f"first input (alpha): got {out[0][0]}, expected 100.0")
    _assert(out[1][0] == 200.0, f"second input (beta): got {out[1][0]}, expected 200.0")
    _assert(out[2][0] == 300.0, f"third input (gamma): got {out[2][0]}, expected 300.0")

    # Request body shape (two batches, so two captured requests)
    _assert(len(captured_requests) == 2, f"expected 2 batches, got {len(captured_requests)}")
    first_req = captured_requests[0]
    _assert(first_req["url"].endswith("/embeddings"), f"url: {first_req['url']}")
    _assert(first_req["body"]["model"] == DEFAULT_NIM_MODEL, first_req["body"]["model"])
    _assert(first_req["body"]["encoding_format"] == "float", first_req["body"])
    _assert(first_req["body"]["input_type"] == "passage", first_req["body"])
    _assert(first_req["body"]["input"] == ["alpha", "beta"], first_req["body"]["input"])
    _assert(captured_requests[1]["body"]["input"] == ["gamma"], captured_requests[1])


@_register("t_nim_embed_query_uses_query_input_type")
def t_nim_embed_query_uses_query_input_type():
    """embed_query() must set input_type=query, not the constructor default (passage).

    E5-family models distinguish query vs passage input types — this is the
    single biggest quality lever for retrieval. Getting it wrong silently
    would degrade every retrieval result.
    """
    import os as _os
    saved_key = _os.environ.get("NVIDIA_API_KEY")
    _os.environ["NVIDIA_API_KEY"] = "nvapi-test-fake-key"

    seen_input_types: list[str] = []

    def fake_post(url: str, body: dict) -> str:
        seen_input_types.append(body["input_type"])
        return _make_nim_ok_response(len(body["input"]), dim=4)

    try:
        embedder = NIMEmbedder()  # default input_type="passage"
        embedder._http_post = fake_post
        embedder.embed_query("What is mercy?")
        # Plus a passage-style batch call to verify the default still works.
        embedder.embed_texts(["verse one", "verse two"])
    finally:
        if saved_key is None:
            _os.environ.pop("NVIDIA_API_KEY", None)
        else:
            _os.environ["NVIDIA_API_KEY"] = saved_key

    _assert(seen_input_types == ["query", "passage"], f"got: {seen_input_types}")


@_register("t_nim_out_of_order_indexes_are_sorted")
def t_nim_out_of_order_indexes_are_sorted():
    """Defend against NIM returning out-of-order 'index' values."""
    import os as _os
    saved_key = _os.environ.get("NVIDIA_API_KEY")
    _os.environ["NVIDIA_API_KEY"] = "nvapi-test-fake-key"

    def fake_post(url: str, body: dict) -> str:
        n = len(body["input"])
        # Return in REVERSE order — buggy but realistic
        return json.dumps({
            "data": [
                {"index": n - 1 - i, "embedding": [float(n - 1 - i)] * 4}
                for i in range(n)
            ]
        })

    try:
        embedder = NIMEmbedder()
        embedder._http_post = fake_post
        out = embedder.embed_texts(["a", "b", "c"])
    finally:
        if saved_key is None:
            _os.environ.pop("NVIDIA_API_KEY", None)
        else:
            _os.environ["NVIDIA_API_KEY"] = saved_key

    # After index-sort: first vec = index 0 marker, third = index 2 marker
    _assert(out[0][0] == 0.0, f"out-of-order not sorted: first={out[0][0]}")
    _assert(out[2][0] == 2.0, f"out-of-order not sorted: third={out[2][0]}")


@_register("t_nim_http_429_maps_to_rate_limit_error")
def t_nim_http_429_maps_to_rate_limit_error():
    """HTTP 429 must surface as NIMRateLimitError, not a generic error.

    Caller needs to distinguish retry-with-backoff from abort.
    """
    import os as _os
    import urllib.error as _ue
    saved_key = _os.environ.get("NVIDIA_API_KEY")
    _os.environ["NVIDIA_API_KEY"] = "nvapi-test-fake-key"

    def fake_post(url: str, body: dict) -> str:
        raise _ue.HTTPError(url, 429, "Too Many Requests", {}, None)

    try:
        embedder = NIMEmbedder()
        embedder._http_post = fake_post
        try:
            embedder.embed_texts(["test"])
            _assert(False, "expected NIMRateLimitError")
        except NIMRateLimitError as e:
            _assert("429" in str(e), str(e))
        except NIMError as e:
            _assert(False, f"wrong error class: {type(e).__name__}: {e}")
    finally:
        if saved_key is None:
            _os.environ.pop("NVIDIA_API_KEY", None)
        else:
            _os.environ["NVIDIA_API_KEY"] = saved_key


@_register("t_nim_http_401_maps_to_auth_error")
def t_nim_http_401_maps_to_auth_error():
    """HTTP 401/403 must surface as NIMAuthError."""
    import os as _os
    import urllib.error as _ue
    saved_key = _os.environ.get("NVIDIA_API_KEY")
    _os.environ["NVIDIA_API_KEY"] = "nvapi-test-fake-key"

    def fake_post(url: str, body: dict) -> str:
        raise _ue.HTTPError(url, 401, "Unauthorized", {}, None)

    try:
        embedder = NIMEmbedder()
        embedder._http_post = fake_post
        try:
            embedder.embed_texts(["test"])
            _assert(False, "expected NIMAuthError")
        except NIMAuthError as e:
            _assert("401" in str(e) or "auth" in str(e).lower(), str(e))
    finally:
        if saved_key is None:
            _os.environ.pop("NVIDIA_API_KEY", None)
        else:
            _os.environ["NVIDIA_API_KEY"] = saved_key


@_register("t_nim_malformed_json_raises_response_error")
def t_nim_malformed_json_raises_response_error():
    """Non-JSON response (or wrong shape) must surface as NIMResponseError."""
    import os as _os
    saved_key = _os.environ.get("NVIDIA_API_KEY")
    _os.environ["NVIDIA_API_KEY"] = "nvapi-test-fake-key"

    def fake_post(url: str, body: dict) -> str:
        # Wrong shape: missing 'data' field
        return json.dumps({"result": "ok", "vectors": []})

    try:
        embedder = NIMEmbedder()
        embedder._http_post = fake_post
        try:
            embedder.embed_texts(["test"])
            _assert(False, "expected NIMResponseError")
        except NIMResponseError as e:
            _assert("data" in str(e), str(e))
    finally:
        if saved_key is None:
            _os.environ.pop("NVIDIA_API_KEY", None)
        else:
            _os.environ["NVIDIA_API_KEY"] = saved_key


@_register("t_nim_default_model_and_base_url")
def t_nim_default_model_and_base_url():
    """Sanity-check defaults — if these change silently the contract breaks.

    DEFAULT_NIM_MODEL is the QA-tuned E5 retriever (1024-dim).
    DEFAULT_NIM_BASE_URL is the public NIM endpoint.
    """
    _assert(DEFAULT_NIM_MODEL == "nvidia/nv-embedqa-e5-v5", DEFAULT_NIM_MODEL)
    _assert("integrate.api.nvidia.com" in DEFAULT_NIM_BASE_URL, DEFAULT_NIM_BASE_URL)
    _assert(DEFAULT_NIM_BASE_URL.endswith("/v1"), DEFAULT_NIM_BASE_URL)


@_register("t_get_embedder_factory_routes_nim")
def t_get_embedder_factory_routes_nim():
    """get_embedder('nim') must return a NIMEmbedder instance."""
    import os as _os
    saved_key = _os.environ.get("NVIDIA_API_KEY")
    _os.environ["NVIDIA_API_KEY"] = "nvapi-test-fake-key"
    try:
        embedder = get_embedder("nim")
        _assert(isinstance(embedder, NIMEmbedder), type(embedder).__name__)
    finally:
        if saved_key is None:
            _os.environ.pop("NVIDIA_API_KEY", None)
        else:
            _os.environ["NVIDIA_API_KEY"] = saved_key


# ---------------------------------------------------------------------------
# Cross-references (Milestone 4)
# ---------------------------------------------------------------------------

@_register("t_xrefs_metadata_present")
def t_xrefs_metadata_present():
    md = metadata()
    _assert("source" in md, list(md.keys()))
    _assert("CC-BY" in md.get("license", ""), md.get("license"))
    _assert(md.get("edges_kept", 0) > 100_000, f"edges_kept={md.get('edges_kept')}")


@_register("t_xrefs_outgoing_john_3_16_known_verse")
def t_xrefs_outgoing_john_3_16_known_verse():
    """John 3:16 is the most cross-referenced verse in the Bible.
    The top edge at default min_votes MUST be Romans 5:8 (the parallel
    'God commended his love' verse). If this fails, the data file is
    wrong, not the code."""
    edges = get_references("John 3:16", min_votes=3)
    _assert(len(edges) > 10, f"only {len(edges)} edges for John 3:16")
    _assert(edges[0]["to"] == "Romans 5:8", f"top: {edges[0]}")
    # Romans 5:8 and 1 John 4:9 are the two canonical parallels
    targets = {e["to"] for e in edges[:10]}
    _assert("Romans 5:8" in targets, targets)
    _assert("1 John 4:9" in targets, targets)


@_register("t_xrefs_outgoing_genesis_1_1_to_john_1_1")
def t_xrefs_outgoing_genesis_1_1_to_john_1_1():
    """Genesis 1:1 → John 1:1 is the OT/NT 'In the beginning' link.
    Should appear at high votes."""
    edges = get_references("Genesis 1:1", min_votes=10)
    targets = {e["to"] for e in edges}
    _assert("John 1:1" in targets, f"missing John 1:1, got {len(edges)} edges")


@_register("t_xrefs_reciprocal_john_3_16")
def t_xrefs_reciprocal_john_3_16():
    """Reciprocal lookup should find at least a few incoming refs."""
    inc = get_reciprocal("John 3:16", min_votes=10)
    _assert(len(inc) > 0, "no incoming refs for John 3:16 at min_votes=10")
    for e in inc:
        _assert("from" in e and "votes" in e, e)
        _assert(e["votes"] >= 10, e)


@_register("t_xrefs_alias_normalization")
def t_xrefs_alias_normalization():
    """Reference parser aliases should resolve in the references engine.
    'jn 3:16' → 'John 3:16'."""
    a = get_references("John 3:16", min_votes=100)
    b = get_references("jn 3:16", min_votes=100)
    _assert(len(a) == len(b), f"alias mismatch: {len(a)} vs {len(b)}")
    _assert(a and b and a[0] == b[0], f"{a[:2]} vs {b[:2]}")


@_register("t_xrefs_min_votes_threshold_works")
def t_xrefs_min_votes_threshold_works():
    """Higher min_votes → fewer (or equal) edges."""
    low = get_references("John 3:16", min_votes=1)
    high = get_references("John 3:16", min_votes=100)
    _assert(len(low) >= len(high), f"low={len(low)} high={len(high)}")
    # And every high-vote edge has votes >= 100
    for e in high:
        _assert(e["votes"] >= 100, e)


@_register("t_xrefs_unknown_reference_returns_empty")
def t_xrefs_unknown_reference_returns_empty():
    """A verse that has no outgoing edges should return [] not raise."""
    out = get_references("Revelation 22:21", min_votes=999)
    _assert(out == [], f"expected [], got {out}")
    inc = get_reciprocal("Revelation 22:21", min_votes=999)
    _assert(inc == [], f"expected [], got {inc}")


@_register("t_xrefs_garbage_input_returns_empty")
def t_xrefs_garbage_input_returns_empty():
    """Unparseable refs return empty without crashing."""
    for bad in ["foo bar", "xyzzy", "1jn 999:999", "", "Genesis"]:
        _assert(get_references(bad) == [], f"unexpected edges for {bad!r}")
        _assert(get_reciprocal(bad) == [], f"unexpected incoming for {bad!r}")


@_register("t_xrefs_traverse_2hop_john_3_16")
def t_xrefs_traverse_2hop_john_3_16():
    """2-hop traversal from John 3:16 should reach many verses.
    Hop 1 must include Romans 5:8 (top edge at min_votes=50)."""
    t = traverse("John 3:16", hops=2, min_votes=50, per_hop_limit=200)
    _assert(1 in t and 2 in t, list(t.keys()))
    _assert(len(t[1]) > 5, f"hop 1 only has {len(t[1])} edges")
    _assert(len(t[2]) > 5, f"hop 2 only has {len(t[2])} edges")
    targets_h1 = {e["to"] for e in t[1]}
    _assert("Romans 5:8" in targets_h1, f"hop 1 missing Romans 5:8: {targets_h1}")


@_register("t_xrefs_traverse_clamps_hops")
def t_xrefs_traverse_clamps_hops():
    """hops=10 should clamp to 3 (per HANDOFF §5 design)."""
    t = traverse("John 3:16", hops=10, min_votes=200)
    _assert(max(t.keys()) <= 3, list(t.keys()))


@_register("t_xrefs_self_loops_excluded")
def t_xrefs_self_loops_excluded():
    """No outgoing edge from a verse should point back to itself."""
    edges = get_references("John 3:16", min_votes=1, limit=500)
    for e in edges:
        _assert(e["to"] != "John 3:16", f"self-loop: {e}")


@_register("t_xrefs_votes_sorted_descending")
def t_xrefs_votes_sorted_descending():
    """Results must be sorted by votes descending."""
    edges = get_references("John 3:16", min_votes=1, limit=200)
    for i in range(len(edges) - 1):
        _assert(edges[i]["votes"] >= edges[i + 1]["votes"],
                f"out of order at {i}: {edges[i]} vs {edges[i + 1]}")


@_register("t_xrefs_cli_basic")
def t_xrefs_cli_basic():
    """CLI: 'python -m bible references John 3:16' must succeed."""
    out = _capture_run(
        __import__("bible.references", fromlist=["run_references"]).run_references,
        "John 3:16",
    )
    _assert("Cross-references for John 3:16" in out)
    _assert("Romans 5:8" in out)


@_register("t_xrefs_cli_reciprocal")
def t_xrefs_cli_reciprocal():
    out = _capture_run(
        __import__("bible.references", fromlist=["run_references"]).run_references,
        "John 3:16", direction="in",
    )
    _assert("Incoming / Reciprocal" in out)


# ---------------------------------------------------------------------------
# Quran tests (Phase 3.1)
# ---------------------------------------------------------------------------

@_register("t_quran_data_files_exist")
def t_quran_data_files_exist():
    """Verify data/quran contains all 6 required edition files."""
    editions = list_quran_translations()
    required = {
        "saheeh-international", "yusuf-ali", "pickthall",
        "mufti-taqi-usmani", "arberry", "uthmani",
    }
    _assert(required.issubset(set(editions)),
            f"missing required editions: {required - set(editions)}")


@_register("t_quran_loads_saheeh")
def t_quran_loads_saheeh():
    """Verify Saheeh International loads with 114 surahs and 6236 ayahs."""
    data = load_quran_edition("saheeh-international")
    _assert(data.get("tradition") == "islam")
    _assert(data.get("structure") == "surah_ayah")
    divisions = data.get("divisions", [])
    _assert(len(divisions) == 114)
    total_ayahs = sum(len(d["ayahs"]) for d in divisions)
    _assert(total_ayahs == 6236, f"expected 6236 ayahs, got {total_ayahs}")


@_register("t_quran_parse_canonical_name")
def t_quran_parse_canonical_name():
    """'Al-Baqarah 2:255' must resolve to (2, 255)."""
    parsed = parse_quran_ref("Al-Baqarah 2:255")
    _assert(parsed == (2, 255), f"failed to parse canonical: {parsed}")


@_register("t_quran_parse_numeric_ref")
def t_quran_parse_numeric_ref():
    """'2:255' and 'Quran 2:255' must resolve to (2, 255)."""
    _assert(parse_quran_ref("2:255") == (2, 255))
    _assert(parse_quran_ref("Quran 2:255") == (2, 255))
    _assert(parse_quran_ref("Surah 2:255") == (2, 255))


@_register("t_quran_parse_alias_and_named_verse")
def t_quran_parse_alias_and_named_verse():
    """Aliases like 'baqarah 255' and 'Ayat al-Kursi' must resolve to (2, 255)."""
    _assert(parse_quran_ref("baqarah 255") == (2, 255))
    _assert(parse_quran_ref("Ayat al-Kursi") == (2, 255))
    _assert(parse_quran_ref("Verse of the Throne") == (2, 255))


@_register("t_quran_parse_range")
def t_quran_parse_range():
    """'Quran 112:1-4' and 'Al-Fatihah 1-7' must resolve to range tuples."""
    _assert(parse_quran_ref("Quran 112:1-4") == (112, (1, 4)))
    _assert(parse_quran_ref("Al-Fatihah 1-7") == (1, (1, 7)))
    _assert(parse_quran_ref("2:255-256") == (2, (255, 256)))


@_register("t_quran_parse_garbage_returns_none")
def t_quran_parse_garbage_returns_none():
    """Garbage, out-of-range surahs, or out-of-range ayahs must return None."""
    _assert(parse_quran_ref("garbage input") is None)
    _assert(parse_quran_ref("115:1") is None)
    _assert(parse_quran_ref("Al-Baqarah 999") is None)
    _assert(parse_quran_ref("Al-Fatihah 10") is None)


@_register("t_quran_verse_text_uthmani_arabic")
def t_quran_verse_text_uthmani_arabic():
    """Uthmani text for 2:255 must contain Allah and Al-Qayyum in Arabic script."""
    verses = get_quran_verses("uthmani", 2, 255)
    _assert(len(verses) == 1)
    text = verses[0]["text"]
    _assert("ٱللَّهُ" in text or "الله" in text or "ٱللَّهُ" in text)
    _assert("ٱلۡقَيُّومُ" in text or "القيوم" in text or "ٱلۡقَيُّومُ" in text)


@_register("t_quran_multi_translation_lookup")
def t_quran_multi_translation_lookup():
    """112:1 lookup across Saheeh, Yusuf Ali, and Pickthall must return expected text."""
    v_saheeh = get_quran_verses("saheeh-international", 112, 1)[0]["text"]
    v_yusuf = get_quran_verses("yusuf-ali", 112, 1)[0]["text"]
    v_pickthall = get_quran_verses("pickthall", 112, 1)[0]["text"]
    _assert("One" in v_saheeh)
    _assert("One" in v_yusuf)
    _assert("One" in v_pickthall)


@_register("t_quran_cli_json")
def t_quran_cli_json():
    """CLI run_quran with as_json=True must produce valid structured JSON."""
    raw = _capture_run(run_quran, "Al-Baqarah 2:255", as_json=True)
    parsed = json.loads(raw)
    _assert(parsed["query"] == "Al-Baqarah 2:255")
    _assert(parsed["surah"]["id"] == 2)
    _assert(len(parsed["ayahs"]) == 1)
    _assert(parsed["ayahs"][0]["ayah"] == 255)
    translations = parsed["ayahs"][0]["translations"]
    _assert("uthmani" in translations)
    _assert("saheeh-international" in translations)


# ---------------------------------------------------------------------------
# Semantic search (Milestone 3B) tests
# ---------------------------------------------------------------------------

@_register("t_semantic_vector_math")
def t_semantic_vector_math():
    """Verify dot product, L2 norm, and cosine similarity."""
    _assert(dot_product([1.0, 0.0], [0.0, 1.0]) == 0.0)
    _assert(dot_product([1.0, 2.0], [3.0, 4.0]) == 11.0)
    _assert(vector_norm([3.0, 4.0]) == 5.0)
    _assert(cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0)
    _assert(cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0)
    _assert(round(cosine_similarity([1.0, 1.0], [-1.0, -1.0]), 4) == -1.0)


@_register("t_semantic_vector_normalize")
def t_semantic_vector_normalize():
    """L2 normalization must produce a unit-length vector."""
    v = l2_normalize([3.0, 4.0])
    _assert(len(v) == 2)
    _assert(round(v[0], 2) == 0.6)
    _assert(round(v[1], 2) == 0.8)
    _assert(round(vector_norm(v), 4) == 1.0)


@_register("t_semantic_mock_embedder")
def t_semantic_mock_embedder():
    """Mock deterministic embedder produces normalized vectors of requested dim."""
    embedder = MockDeterministicEmbedder(dim=32)
    vecs = embedder.embed_texts(["grace and mercy", "light and truth"])
    _assert(len(vecs) == 2)
    _assert(len(vecs[0]) == 32)
    _assert(len(vecs[1]) == 32)
    _assert(round(vector_norm(vecs[0]), 4) == 1.0)
    _assert(round(vector_norm(vecs[1]), 4) == 1.0)


@_register("t_semantic_custom_index_search")
def t_semantic_custom_index_search():
    """search_semantic ranks nearest neighbor correctly with custom in-memory index."""
    embedder = MockDeterministicEmbedder(dim=32)
    entries = [
        {"id": 0, "citation": "John 3:16", "text": "For God so loved the world", "tradition": "christianity"},
        {"id": 1, "citation": "Genesis 1:1", "text": "In the beginning God created the heaven and earth", "tradition": "christianity"},
        {"id": 2, "citation": "Quran 1:1", "text": "In the name of Allah the Entirely Merciful", "tradition": "islam"},
    ]
    vecs = embedder.embed_texts([e["text"] for e in entries])
    custom_index = (entries, vecs, 32)

    results = search_semantic(
        query="God loved the world",
        custom_index=custom_index,
        backend="mock",
        top_k=2,
    )
    _assert(len(results) == 2)
    _assert(results[0]["citation"] == "John 3:16")
    _assert("score" in results[0])
    _assert(results[0]["score"] > 0.0)


@_register("t_semantic_cli_missing_index_graceful")
def t_semantic_cli_missing_index_graceful():
    """CLI run_semantic handles missing vector index without crashing."""
    out = _capture_run(run_semantic, "peace in suffering", index_name="__nonexistent_index__")
    _assert("No precomputed vector index found" in out or "No matching passages found" in out)

    # Test JSON mode
    raw_json = _capture_run(run_semantic, "peace in suffering", index_name="__nonexistent_index__", as_json=True)
    data = json.loads(raw_json)
    _assert(data["query"] == "peace in suffering")
    _assert(data["results_count"] == 0)


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
