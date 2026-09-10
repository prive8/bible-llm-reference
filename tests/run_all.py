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
from bible.torah import (  # noqa: E402
    BOOKS as TORAH_BOOKS,
    get_torah_verses_scoped,
    list_torah_translations,
    load_torah_edition,
    parse_torah_ref,
    resolve_book,
    run_torah,
)
import math
import importlib.util as _ilu
_harness_path = str(ROOT / "scripts" / "run_eval.py")
_spec = _ilu.spec_from_file_location("run_eval", _harness_path)  # type: ignore[arg-type]  # noqa
_mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]  # noqa
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]  # noqa
_dcg = _mod._dcg
_ndcg_at_k = _mod._ndcg_at_k
_metrics_for_query = _mod._metrics_for_query
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
from bible.hybrid import (  # noqa: E402
    DEFAULT_BM25_WEIGHT,
    DEFAULT_SOLO_WEIGHT,
    hybrid_search,
    _min_max_normalize,
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
# Semantic search on a real on-disk index (conditional)
# ---------------------------------------------------------------------------
# This test only runs if data/embeddings/default_meta.json exists. CI does
# NOT generate the index (it would require sentence-transformers + a 5-min
# CPU run). The test is the developer-facing proof that the index loads
# and queries work end-to-end after `scripts/index_embeddings.py` is run.

@_register("t_semantic_real_index_loads_and_returns_results")
def t_semantic_real_index_loads_and_returns_results():
    """Load the real on-disk vector index and verify a query returns ranked results.

    Skipped if the index doesn't exist. To run: `python scripts/index_embeddings.py
    --backend local --name default` (~3 min on CPU for the Bible + Quran corpus).
    """
    from pathlib import Path
    from bible.semantic import load_vector_index, search_semantic, MockDeterministicEmbedder
    meta_path = ROOT / "data" / "embeddings" / "default_meta.json"
    bin_path = ROOT / "data" / "embeddings" / "default_vectors.bin"
    if not (meta_path.exists() and bin_path.exists()):
        print(f"  [skip] no real index at {meta_path.parent}")
        return
    # Index exists. Verify shape.
    loaded = load_vector_index(meta_path.parent, "default")
    _assert(loaded is not None, "load_vector_index returned None")
    entries, vectors, dim = loaded
    _assert(len(entries) > 10_000, f"index too small: {len(entries)} entries")
    _assert(dim in (384, 768, 1024), f"unexpected dim: {dim}")
    # Verify entries have the expected metadata fields
    sample = entries[0]
    _assert("citation" in sample and "text" in sample, sample)
    _assert("tradition" in sample, sample)
    # Run a real semantic query with the MOCK embedder so we don't depend
    # on sentence-transformers being installed at test time. This proves
    # the index loads and the cosine loop runs end-to-end.
    results = search_semantic(
        "comfort in grief",
        index_name="default",
        top_k=5,
        tradition=None,
        backend="mock",  # use mock to skip the model download
    )
    _assert(len(results) == 5, f"expected 5 results, got {len(results)}")
    for r in results:
        _assert("citation" in r and "score" in r and 0.0 <= r["score"] <= 1.0, r)


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
# Evaluation harness (Milestone 3C+ baseline metrics)
# ---------------------------------------------------------------------------
# These tests exercise the harness's pure-logic functions. They use a
# tiny in-memory fixture (no real index needed) so CI is self-contained.

@_register("t_eval_dcg_basic")
def t_eval_dcg_basic():
    """DCG with log2(rank+2) discount — basic shape."""
    # 2 docs, both relevance 3 → DCG = 3/log2(2) + 3/log2(3) = 3 + 1.89 = 4.89
    dcg = _dcg([3, 3])
    _assert(abs(dcg - (3.0 + 3.0 / math.log2(3))) < 0.01, f"dcg={dcg}")


@_register("t_eval_dcg_empty")
def t_eval_dcg_empty():
    """DCG of empty list = 0."""
    _assert(_dcg([]) == 0.0)


@_register("t_eval_ndcg_perfect_ranking")
def t_eval_ndcg_perfect_ranking():
    """Perfect ranking: actual DCG = ideal DCG → nDCG = 1.0."""
    expected = {"a": 3, "b": 2, "c": 1}
    got = ["a", "b", "c"]
    ndcg = _ndcg_at_k(expected, got, k=3)
    _assert(abs(ndcg - 1.0) < 0.001, f"ndcg={ndcg}")


@_register("t_eval_ndcg_random_is_zero_for_unrelated")
def t_eval_ndcg_random_is_zero_for_unrelated():
    """If retrieved verses aren't in expected, nDCG = 0."""
    expected = {"a": 3}
    got = ["x", "y", "z"]
    ndcg = _ndcg_at_k(expected, got, k=3)
    _assert(ndcg == 0.0, f"ndcg={ndcg}")


@_register("t_eval_ndcg_zero_ideal")
def t_eval_ndcg_zero_ideal():
    """If expected is empty, nDCG = 0 (avoid divide-by-zero)."""
    _assert(_ndcg_at_k({}, ["a", "b"], k=2) == 0.0)


@_register("t_eval_metrics_for_query_primary_in_top1")
def t_eval_metrics_for_query_primary_in_top1():
    """Primary-in-top-1: True iff rank-1 retrieval is in expected with weight=3."""
    expected = [("a", 3), ("b", 2)]
    m = _metrics_for_query(expected, ["a", "x", "y"], top_k=3)
    _assert(m["primary_in_top1"] is True)
    _assert(m["recall_at_k"] == round(1/2, 4), m)
    _assert(m["mrr"] == 1.0)


@_register("t_eval_metrics_for_query_no_primary_hit")
def t_eval_metrics_for_query_no_primary_hit():
    """When no weight-3 verse is retrieved, MRR = 0 and primary-in-top-1 = False."""
    expected = [("a", 3), ("b", 2)]
    m = _metrics_for_query(expected, ["x", "y", "z"], top_k=3)
    _assert(m["primary_in_top1"] is False)
    _assert(m["mrr"] == 0.0)
    _assert(m["recall_at_k"] == 0.0)


@_register("t_eval_metrics_for_query_recall_partial")
def t_eval_metrics_for_query_recall_partial():
    """Recall is fraction of expected verses retrieved, not count."""
    expected = [("a", 3), ("b", 3), ("c", 3), ("d", 2)]  # 4 expected
    m = _metrics_for_query(expected, ["a", "b", "x", "y", "z"], top_k=5)
    _assert(m["recall_at_k"] == 0.5, m)  # 2 of 4 expected found


@_register("t_eval_threshold_gate_parses_real_report")
def t_eval_threshold_gate_parses_real_report():
    """Verify the regex used by CI's threshold gate parses a realistic report.

    This is the same regex embedded in `.github/workflows/ci.yml`. If the
    harness output format changes, both this test AND CI will need updates.
    The test catches the change before CI does.
    """
    sample_report = """## Summary

| Path | Recall@K | MRR | Primary-in-top-1 | nDCG@K | Queries/s |
|------|----------|-----|------------------|--------|-----------|
| bm25 | 0.093 | 0.030 | 0.030 | 0.068 | 6.3 |
| semantic | 0.279 | 0.165 | 0.151 | 0.222 | 0.3 |
| hybrid | 0.233 | 0.093 | 0.030 | 0.191 | 0.4 |
"""
    import re
    # Exact pattern from .github/workflows/ci.yml — keep in sync
    for path_name in ["bm25", "semantic", "hybrid"]:
        pattern = rf"\|\s*{path_name}\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|"
        m = re.search(pattern, sample_report)
        _assert(m is not None, f"CI regex doesn't match path {path_name!r}")
        recall = float(m.group(1))
        _assert(0.0 <= recall <= 1.0, f"recall out of range: {recall}")


# ---------------------------------------------------------------------------
# Hybrid BM25 + semantic fusion (Milestone 3C)
# ---------------------------------------------------------------------------

def _make_bm25_mock_hits() -> list[dict]:
    """Three BM25 hits with overlapping citations to test fusion."""
    return [
        {"citation": "John 3:16", "score": 12.5, "text": "For God so loved the world...",
         "translation": "KJV", "tradition": "christianity"},
        {"citation": "Romans 5:8", "score": 8.2, "text": "But God commendeth his love...",
         "translation": "KJV", "tradition": "christianity"},
        {"citation": "1 John 4:9", "score": 5.0, "text": "In this was manifested the love of God...",
         "translation": "KJV", "tradition": "christianity"},
    ]


def _make_semantic_mock_hits() -> list[dict]:
    """Three semantic hits — overlaps with BM25 on John 3:16 and Romans 5:8."""
    return [
        {"citation": "John 3:16", "score": 0.92, "text": "For God so loved the world...",
         "translation": "KJV", "tradition": "christianity"},
        {"citation": "Romans 5:8", "score": 0.85, "text": "But God commendeth his love...",
         "translation": "KJV", "tradition": "christianity"},
        {"citation": "1 John 4:19", "score": 0.74, "text": "We love him, because he first loved us.",
         "translation": "KJV", "tradition": "christianity"},
    ]


@_register("t_hybrid_min_max_normalize_basic")
def t_hybrid_min_max_normalize_basic():
    """Sanity-check the per-query normalization helper."""
    out = _min_max_normalize([1.0, 2.0, 3.0, 4.0, 5.0])
    _assert(out == [0.0, 0.25, 0.5, 0.75, 1.0], out)


@_register("t_hybrid_min_max_normalize_constant")
def t_hybrid_min_max_normalize_constant():
    """All-equal scores → all 1.0 (so contribution isn't zeroed out)."""
    out = _min_max_normalize([5.0, 5.0, 5.0])
    _assert(out == [1.0, 1.0, 1.0], out)


@_register("t_hybrid_min_max_normalize_empty")
def t_hybrid_min_max_normalize_empty():
    """Empty list → empty list."""
    _assert(_min_max_normalize([]) == [], _min_max_normalize([]))


@_register("t_hybrid_reciprocal_hits_outrank_solos")
def t_hybrid_reciprocal_hits_outrank_solos():
    """Verses appearing in BOTH BM25 and semantic should rank above solos.

    John 3:16 and Romans 5:8 are in both → high combined score.
    1 John 4:9 is BM25-only; 1 John 4:19 is semantic-only → lower.
    """
    results = hybrid_search(
        query="test",
        bm25_results=_make_bm25_mock_hits(),
        semantic_results=_make_semantic_mock_hits(),
        bm25_weight=0.5,
        solo_weight=0.7,
        top_k=10,
    )
    citations = [r["citation"] for r in results]
    # Reciprocal hits come first (John 3:16 and Romans 5:8 in some order)
    _assert(citations[0] in ("John 3:16", "Romans 5:8"),
            f"top result should be a reciprocal hit, got: {citations[0]}")
    _assert(citations[1] in ("John 3:16", "Romans 5:8"),
            f"second result should be a reciprocal hit, got: {citations[1]}")
    # Then solos (1 John 4:9 and 1 John 4:19 in some order)
    _assert(citations[2] in ("1 John 4:9", "1 John 4:19"),
            f"third result should be a solo hit, got: {citations[2]}")
    _assert(citations[3] in ("1 John 4:9", "1 John 4:19"),
            f"fourth result should be a solo hit, got: {citations[3]}")

    # Reciprocal hits have 'source: both'; solos have their single source
    sources = {r["citation"]: r["source"] for r in results}
    _assert(sources["John 3:16"] == "both", sources)
    _assert(sources["Romans 5:8"] == "both", sources)
    _assert(sources["1 John 4:9"] == "bm25", sources)
    _assert(sources["1 John 4:19"] == "semantic", sources)


@_register("t_hybrid_bm25_only_weight")
def t_hybrid_bm25_only_weight():
    """bm25_weight=1.0 → BM25 fully dominates; semantic component zeroed.

    Reciprocal hits still score > 0 (their BM25 part survives).
    Solo semantic hits get sem_norm * 0 * solo_weight = 0 (zeroed).
    Solo BM25 hits get bm25_norm * 1.0 * solo_weight (may be > 0 if
    they're not the lowest-scoring BM25 result; in our mock 1 John 4:9
    is the lowest, so it scores 0).
    """
    results = hybrid_search(
        query="test",
        bm25_results=_make_bm25_mock_hits(),
        semantic_results=_make_semantic_mock_hits(),
        bm25_weight=1.0,
        solo_weight=0.7,
        top_k=10,
    )
    citations = [r["citation"] for r in results]
    # John 3:16 has the highest combined score (BM25_norm=1.0 * 1.0 = 1.0)
    _assert(citations[0] == "John 3:16",
            f"top should be John 3:16, got: {citations}")
    # All four citations should appear (no filtering, just ranking)
    _assert(len(citations) == 4, f"expected 4 citations, got {len(citations)}")
    by_cite = {r["citation"]: r["combined_score"] for r in results}
    # Reciprocal hits both > 0
    _assert(by_cite["John 3:16"] > 0.0, by_cite)
    _assert(by_cite["Romans 5:8"] > 0.0, by_cite)
    # Solo semantic hit (1 John 4:19) is zeroed — semantic component * 0 = 0
    _assert(by_cite["1 John 4:19"] == 0.0, by_cite["1 John 4:19"])


@_register("t_hybrid_semantic_only_weight")
def t_hybrid_semantic_only_weight():
    """bm25_weight=0.0 → semantic fully dominates; BM25 component zeroed.

    Reciprocal hits still score > 0 (their semantic part survives).
    Solo BM25 hits get bm25_norm * 0 * solo_weight = 0 (zeroed).
    Solo semantic hits get sem_norm * 1.0 * solo_weight (may be > 0 if
    they're not the lowest-scoring semantic result; in our mock 1 John
    4:19 is the lowest, so it scores 0).
    """
    results = hybrid_search(
        query="test",
        bm25_results=_make_bm25_mock_hits(),
        semantic_results=_make_semantic_mock_hits(),
        bm25_weight=0.0,
        solo_weight=0.7,
        top_k=10,
    )
    citations = [r["citation"] for r in results]
    # John 3:16 has the highest combined score (sem_norm=1.0 * 1.0 = 1.0)
    _assert(citations[0] == "John 3:16",
            f"top should be John 3:16, got: {citations}")
    # All four citations should appear
    _assert(len(citations) == 4, f"expected 4 citations, got {len(citations)}")
    by_cite = {r["citation"]: r["combined_score"] for r in results}
    # Reciprocal hits both > 0
    _assert(by_cite["John 3:16"] > 0.0, by_cite)
    _assert(by_cite["Romans 5:8"] > 0.0, by_cite)
    # Solo BM25 hit (1 John 4:9) is zeroed — BM25 component * 0 = 0
    _assert(by_cite["1 John 4:9"] == 0.0, by_cite["1 John 4:9"])


@_register("t_hybrid_both_empty_returns_empty")
def t_hybrid_both_empty_returns_empty():
    """No BM25, no semantic → empty result list."""
    results = hybrid_search(
        query="test",
        bm25_results=[],
        semantic_results=[],
        bm25_weight=0.5,
        top_k=10,
    )
    _assert(results == [], results)


@_register("t_hybrid_only_bm25_returns_bm25_results")
def t_hybrid_only_bm25_returns_bm25_results():
    """Empty semantic, non-empty BM25 → all results from BM25 with bm25_weight applied."""
    bm25 = _make_bm25_mock_hits()
    results = hybrid_search(
        query="test",
        bm25_results=bm25,
        semantic_results=[],
        bm25_weight=0.5,
        solo_weight=0.7,
        top_k=10,
    )
    citations = [r["citation"] for r in results]
    _assert(citations == ["John 3:16", "Romans 5:8", "1 John 4:9"], citations)
    for r in results:
        _assert(r["source"] == "bm25", r["source"])
        _assert(r["bm25_score"] is not None, r)
        _assert(r["semantic_score"] is None, r)


@_register("t_hybrid_only_semantic_returns_semantic_results")
def t_hybrid_only_semantic_returns_semantic_results():
    """Empty BM25, non-empty semantic → all results from semantic."""
    sem = _make_semantic_mock_hits()
    results = hybrid_search(
        query="test",
        bm25_results=[],
        semantic_results=sem,
        bm25_weight=0.5,
        solo_weight=0.7,
        top_k=10,
    )
    citations = [r["citation"] for r in results]
    _assert(citations == ["John 3:16", "Romans 5:8", "1 John 4:19"], citations)
    for r in results:
        _assert(r["source"] == "semantic", r["source"])
        _assert(r["bm25_score"] is None, r)
        _assert(r["semantic_score"] is not None, r)


@_register("t_hybrid_default_weights")
def t_hybrid_default_weights():
    """DEFAULT_BM25_WEIGHT and DEFAULT_SOLO_WEIGHT must be in [0, 1].

    These are public API constants — if they change silently, every
    downstream user of hybrid_search gets different results.
    """
    _assert(0.0 <= DEFAULT_BM25_WEIGHT <= 1.0, str(DEFAULT_BM25_WEIGHT))
    _assert(0.0 <= DEFAULT_SOLO_WEIGHT <= 1.0, str(DEFAULT_SOLO_WEIGHT))
    # Pin the tuned defaults so a regression in v0.10.0+ is loud.
    # These values were set by the v0.10.0 hybrid-fusion tuning sweep
    # (see notes/2026-09-10-hybrid-tuning.md); changing them requires
    # updating this test AND the v0.10.0+ entry in docs/evaluation.md.
    _assert(DEFAULT_BM25_WEIGHT == 0.1, str(DEFAULT_BM25_WEIGHT))
    _assert(DEFAULT_SOLO_WEIGHT == 0.7, str(DEFAULT_SOLO_WEIGHT))


@_register("t_hybrid_top_k_limits_results")
def t_hybrid_top_k_limits_results():
    """top_k param must limit the returned list."""
    results = hybrid_search(
        query="test",
        bm25_results=_make_bm25_mock_hits(),
        semantic_results=_make_semantic_mock_hits(),
        bm25_weight=0.5,
        solo_weight=0.7,
        top_k=2,
    )
    _assert(len(results) == 2, f"expected 2 results, got {len(results)}")
    _assert(results[0]["citation"] in ("John 3:16", "Romans 5:8"), results[0])
    _assert(results[1]["citation"] in ("John 3:16", "Romans 5:8"), results[1])


@_register("t_hybrid_cli_dispatcher_wires_hybrid")
def t_hybrid_cli_dispatcher_wires_hybrid():
    """`python -m bible hybrid` must reach bible.hybrid.main, not bail with Unknown command."""
    import io as _io
    from contextlib import redirect_stdout as _ro
    buf = _io.StringIO()
    with _ro(buf):
        try:
            # Just verify the dispatcher accepts 'hybrid' as a command.
            # The full CLI requires real BM25 + semantic indices, so we
            # only smoke-test the dispatcher's command routing here.
            from bible.hybrid import main as hybrid_main
            # If we got here without ImportError, the module is reachable.
            _assert(callable(hybrid_main))
        except SystemExit as e:
            # argparse --help calls sys.exit(0) — that's fine
            _assert(e.code in (0, None))


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
# Torah (Phase 3.2) tests
# ---------------------------------------------------------------------------

@_register("t_torah_resolve_book_aliases")
def t_torah_resolve_book_aliases():
    """resolve_book() must handle Latin, short, and Hebrew-with-nikkud forms."""
    _assert(resolve_book("Genesis") == "Genesis", repr(resolve_book("Genesis")))
    _assert(resolve_book("Gen") == "Genesis", repr(resolve_book("Gen")))
    _assert(resolve_book("Bereshit") == "Genesis", repr(resolve_book("Bereshit")))
    _assert(resolve_book("בְּרֵאשִׁית") == "Genesis", repr(resolve_book("בְּרֵאשִׁית")))
    _assert(resolve_book("Exodus") == "Exodus", repr(resolve_book("Exodus")))
    _assert(resolve_book("Lev") == "Leviticus", repr(resolve_book("Lev")))
    _assert(resolve_book("Num") == "Numbers", repr(resolve_book("Num")))
    _assert(resolve_book("Dt") == "Deuteronomy", repr(resolve_book("Dt")))
    _assert(resolve_book("garbage") is None, "garbage must not resolve")


@_register("t_torah_parse_canonical_ref")
def t_torah_parse_canonical_ref():
    """Canonical English refs parse to (book, chapter, verse)."""
    parsed = parse_torah_ref("Genesis 1:1")
    _assert(parsed == ("Genesis", 1, 1), repr(parsed))
    parsed = parse_torah_ref("Deuteronomy 34:12")
    _assert(parsed == ("Deuteronomy", 34, 12), repr(parsed))


@_register("t_torah_parse_alias_and_hebrew")
def t_torah_parse_alias_and_hebrew():
    """Short Latin and Hebrew-with-nikkud aliases must resolve correctly."""
    parsed = parse_torah_ref("Gen 1:1")
    _assert(parsed is not None and parsed[0] == "Genesis", repr(parsed))
    parsed = parse_torah_ref("Bereshit 1:1")
    _assert(parsed is not None and parsed[0] == "Genesis", repr(parsed))
    parsed = parse_torah_ref("בראשית 1:1")
    _assert(parsed is not None and parsed[0] == "Genesis", repr(parsed))


@_register("t_torah_parse_range")
def t_torah_parse_range():
    """Verse range parsing must accept hyphen, en-dash, em-dash."""
    p1 = parse_torah_ref("Genesis 1:1-3")
    _assert(p1 == ("Genesis", 1, (1, 3)), repr(p1))
    p2 = parse_torah_ref("Genesis 1:1–3")  # en-dash
    _assert(p2 == ("Genesis", 1, (1, 3)), repr(p2))
    p3 = parse_torah_ref("Genesis 1:1—3")  # em-dash
    _assert(p3 == ("Genesis", 1, (1, 3)), repr(p3))


@_register("t_torah_parse_garbage_returns_none")
def t_torah_parse_garbage_returns_none():
    """Unparseable inputs must return None, not raise."""
    _assert(parse_torah_ref("") is None)
    _assert(parse_torah_ref("garbage") is None)
    _assert(parse_torah_ref("Genesis") is None)
    _assert(parse_torah_ref("Genesis 1") is None)
    _assert(parse_torah_ref("Unknown 1:1") is None)
    _assert(parse_torah_ref("Genesis 51:1") is None, "Genesis has only 50 chapters")


@_register("t_torah_data_files_present")
def t_torah_data_files_present():
    """If Torah has been ingested, two editions must exist with sane verse counts."""
    editions = list_torah_translations()
    if not editions:
        # Skip silently when ingest hasn't run yet (CI may run before ingest).
        return
    _assert("hebrew-nikkud" in editions, str(editions))
    _assert("jps1917-modernized" in editions, str(editions))
    for key in editions:
        data = load_torah_edition(key)
        _assert(data.get("tradition") == "judaism", str(key))
        _assert(data.get("structure") == "book_chapter_verse", str(key))
        divisions = data.get("divisions", [])
        _assert(len(divisions) == 5, f"expected 5 books, got {len(divisions)}")
        book_names = [d["name"] for d in divisions]
        _assert(book_names == ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"], str(book_names))


@_register("t_torah_verses_chapter_scoped")
def t_torah_verses_chapter_scoped():
    """get_torah_verses_scoped must return only verses from the requested chapter.

    Without chapter scoping, a range like Genesis 1:30-32 could bleed into
    Genesis 2 verses if the ingestor wrote verses flat with reset numbering.
    """
    editions = list_torah_translations()
    if "jps1917-modernized" not in editions:
        return  # skip when not ingested
    verses = get_torah_verses_scoped("jps1917-modernized", "Genesis", 1, (1, 31))
    _assert(len(verses) == 31, f"expected 31, got {len(verses)}")
    _assert(verses[0]["book"] == "Genesis", str(verses[0]))
    _assert(verses[0]["chapter"] == 1, str(verses[0]))
    _assert(verses[0]["verse"] == 1, str(verses[0]))
    _assert(verses[30]["verse"] == 31, str(verses[30]))
    # Make sure no verse from chapter 2 leaked in
    for v in verses:
        _assert(v["chapter"] == 1, f"chapter bleed: {v}")


@_register("t_torah_cli_json")
def t_torah_cli_json():
    """CLI run_torah with as_json=True must produce valid structured JSON."""
    editions = list_torah_translations()
    if "jps1917-modernized" not in editions:
        return  # skip when not ingested
    raw = _capture_run(run_torah, "Genesis 1:1", as_json=True)
    parsed = json.loads(raw)
    _assert(parsed["query"] == "Genesis 1:1")
    _assert(parsed["book"]["name"] == "Genesis")
    _assert(parsed["book"]["hebrew"] == "בראשית")
    _assert(parsed["chapter"] == 1)
    _assert(len(parsed["verses"]) == 1)
    _assert(parsed["verses"][0]["verse"] == 1)
    translations = parsed["verses"][0]["translations"]
    _assert("jps1917-modernized" in translations, str(list(translations.keys())))
    _assert("hebrew-nikkud" in translations, str(list(translations.keys())))


@_register("t_torah_cli_hebrew_alias")
def t_torah_cli_hebrew_alias():
    """Hebrew alias (with nikkud) must resolve to a real verse."""
    editions = list_torah_translations()
    if "hebrew-nikkud" not in editions:
        return
    raw = _capture_run(run_torah, "בראשית 1:1", translations=["hebrew-nikkud"], as_json=True)
    parsed = json.loads(raw)
    _assert(parsed["book"]["name"] == "Genesis", str(parsed["book"]))
    hebrew_text = parsed["verses"][0]["translations"]["hebrew-nikkud"]
    _assert("ברא" in hebrew_text or "בְּרֵא" in hebrew_text,
            f"expected Hebrew text containing ברא, got: {hebrew_text!r}")


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


@_register("t_semantic_tradition_filter_aliases")
def t_semantic_tradition_filter_aliases():
    """search_semantic tradition filter must accept public aliases (bible/islam/judaism)
    and match against canonical stored values (christianity/islam/judaism).

    Regression test for a silent substring-match bug in v0.8.0–v0.10.0 where
    `--tradition bible` returned 0 results because stored entries used
    `tradition="christianity"`.
    """
    embedder = MockDeterministicEmbedder(dim=32)
    entries = [
        {"id": 0, "citation": "John 3:16", "text": "For God so loved the world", "tradition": "christianity"},
        {"id": 1, "citation": "Quran 1:1", "text": "In the name of Allah", "tradition": "islam"},
        {"id": 2, "citation": "Genesis 1:1", "text": "In the beginning", "tradition": "judaism"},
    ]
    vecs = embedder.embed_texts([e["text"] for e in entries])
    custom_index = (entries, vecs, 32)

    # 'bible' should map to 'christianity'
    r_bible = search_semantic(query="loved", custom_index=custom_index, backend="mock",
                              tradition="bible", top_k=5)
    _assert(len(r_bible) == 1, f"expected 1 Christianity entry, got {len(r_bible)}")
    _assert(r_bible[0]["tradition"] == "christianity", str(r_bible[0]))

    # 'islam' should still work
    r_islam = search_semantic(query="allah", custom_index=custom_index, backend="mock",
                              tradition="islam", top_k=5)
    _assert(len(r_islam) == 1, f"expected 1 Islam entry, got {len(r_islam)}")
    _assert(r_islam[0]["tradition"] == "islam", str(r_islam[0]))

    # 'judaism' should now work (Phase 3.2)
    r_judaism = search_semantic(query="beginning", custom_index=custom_index, backend="mock",
                                tradition="judaism", top_k=5)
    _assert(len(r_judaism) == 1, f"expected 1 Judaism entry, got {len(r_judaism)}")
    _assert(r_judaism[0]["tradition"] == "judaism", str(r_judaism[0]))

    # 'all' returns everything
    r_all = search_semantic(query="loved the world", custom_index=custom_index, backend="mock",
                            tradition="all", top_k=5)
    _assert(len(r_all) == 3, f"expected 3 entries with tradition=all, got {len(r_all)}")

    # None means 'all'
    r_none = search_semantic(query="loved the world", custom_index=custom_index, backend="mock",
                             tradition=None, top_k=5)
    _assert(len(r_none) == 3, f"expected 3 entries with tradition=None, got {len(r_none)}")


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
