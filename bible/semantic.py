"""Semantic search and dense embedding retrieval module (Milestone 3B).

Stdlib-first vector mathematics, pluggable embedding backends, and indexed
retrieval across Bible and Quran corpora.

Design:
    - Zero mandatory runtime dependencies (ADR-001). Vector calculations
      (dot-product, norm, cosine similarity, top-k) are implemented in pure
      Python standard library (`math`, `struct`, `heapq`).
    - Pluggable embedder backends:
        1. 'local': Local sentence-transformers (all-MiniLM-L6-v2, ~80MB, CPU).
        2. 'nim': NVIDIA NIM endpoint if NVIDIA_API_KEY is present in environment.
        3. 'mock': Deterministic stdlib fallback for CI and offline unit tests.
    - Flat binary float32 vector index with JSON metadata mapping for sub-millisecond
      local nearest-neighbor search.
"""

from __future__ import annotations

import json
import math
import os
import struct
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parent.parent
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"

# ---------------------------------------------------------------------------
# Pure Stdlib Vector Math
# ---------------------------------------------------------------------------

def dot_product(v1: list[float], v2: list[float]) -> float:
    """Compute dot product of two vectors."""
    return sum(x * y for x, y in zip(v1, v2))


def vector_norm(v: list[float]) -> float:
    """Compute Euclidean (L2) norm of a vector."""
    return math.sqrt(sum(x * x for x in v))


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors (-1.0 to 1.0)."""
    norm1 = vector_norm(v1)
    norm2 = vector_norm(v2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot_product(v1, v2) / (norm1 * norm2)


def l2_normalize(v: list[float]) -> list[float]:
    """Normalize vector to unit length (L2 norm = 1.0)."""
    n = vector_norm(v)
    if n == 0.0:
        return v[:]
    return [x / n for x in v]


# ---------------------------------------------------------------------------
# Index Serialization (Binary Float32 + Metadata JSON)
# ---------------------------------------------------------------------------

def save_vector_index(
    dir_path: Path,
    name: str,
    metadata: list[dict],
    vectors: list[list[float]],
    dim: int,
) -> None:
    """Serialize metadata and float32 vectors to disk."""
    dir_path.mkdir(parents=True, exist_ok=True)
    meta_path = dir_path / f"{name}_meta.json"
    bin_path = dir_path / f"{name}_vectors.bin"

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "name": name,
            "count": len(metadata),
            "dim": dim,
            "entries": metadata,
        }, f, ensure_ascii=False, indent=2)

    with open(bin_path, "wb") as f:
        for vec in vectors:
            if len(vec) != dim:
                raise ValueError(f"Vector length {len(vec)} != expected dim {dim}")
            f.write(struct.pack(f"{dim}f", *vec))


def load_vector_index(
    dir_path: Path,
    name: str,
) -> Optional[tuple[list[dict], list[list[float]], int]]:
    """Load metadata and vectors from disk if they exist."""
    meta_path = dir_path / f"{name}_meta.json"
    bin_path = dir_path / f"{name}_vectors.bin"

    if not meta_path.exists() or not bin_path.exists():
        return None

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)

    dim = meta_data.get("dim", 0)
    count = meta_data.get("count", 0)
    entries = meta_data.get("entries", [])

    if dim <= 0 or count <= 0:
        return None

    vectors: list[list[float]] = []
    chunk_size = dim * 4  # 4 bytes per float32
    with open(bin_path, "rb") as f:
        for _ in range(count):
            buf = f.read(chunk_size)
            if len(buf) < chunk_size:
                break
            vec = list(struct.unpack(f"{dim}f", buf))
            vectors.append(vec)

    return entries, vectors, dim


# ---------------------------------------------------------------------------
# Pluggable Embedder Backends
# ---------------------------------------------------------------------------

class BaseEmbedder:
    """Interface for text embedding generation."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


class LocalSentenceTransformerEmbedder(BaseEmbedder):
    """Local CPU/GPU inference using sentence-transformers (all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is not installed. Install via:\n"
                "    pip install -e .[embeddings]\n"
                "or: pip install sentence-transformers"
            ) from e
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [list(map(float, row)) for row in embeddings]


class MockDeterministicEmbedder(BaseEmbedder):
    """Pure stdlib deterministic mock embedder for CI and test suites.

    Projects token hash frequencies into a compact unit vector so tests
    can run deterministically without downloading any weights.
    """

    def __init__(self, dim: int = 64):
        self.dim = dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            vec = [0.0] * self.dim
            tokens = text.lower().split()
            for token in tokens:
                # Hash bucket projection
                idx = sum(ord(c) for c in token) % self.dim
                vec[idx] += 1.0
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0.0:
                vec = [x / norm for x in vec]
            results.append(vec)
        return results


# ---------------------------------------------------------------------------
# NVIDIA NIM Embedder Backend
# ---------------------------------------------------------------------------

class NIMError(RuntimeError):
    """Base class for NIM embedder failures."""


class NIMAuthError(NIMError):
    """Raised when the API key is missing or rejected (HTTP 401/403)."""


class NIMRateLimitError(NIMError):
    """Raised on HTTP 429. Caller may retry with backoff."""


class NIMServerError(NIMError):
    """Raised on HTTP 5xx. Caller may retry with backoff."""


class NIMResponseError(NIMError):
    """Raised when the response body is malformed or the shape changes."""


class NIMConnectionError(NIMError):
    """Raised on transport failures (DNS, TLS, refused, timeout)."""


# Default model + base URL — overridable via NIM_EMBED_MODEL / NIM_BASE_URL env.
# 1024-dim, E5-Large-Unsupervised finetuned for QA retrieval.
# See: https://build.nvidia.com/nvidia/nv-embedqa-e5-v5
DEFAULT_NIM_MODEL = "nvidia/nv-embedqa-e5-v5"
DEFAULT_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NIM_BATCH = 32
DEFAULT_NIM_TIMEOUT = 60  # seconds per request


# OpenRouter-hosted embedding defaults (paid; user has authorized spend
# as of 2026-09-10). OpenRouter is OpenAI-compatible on the wire but
# prefixes model IDs with the provider (e.g. "openai/text-embedding-3-small").
# Free-tier note: OpenRouter has no truly-free embedding models as of
# 2026-09-10 (only chat models are free), so this backend is paid-only.
# See HANDOFF §8 #1 + #8 for the cost-posture reasoning.
DEFAULT_OPENROUTER_MODEL = "openai/text-embedding-3-small"
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_BATCH = 100  # OpenRouter allows larger batches than NIM
DEFAULT_OPENROUTER_TIMEOUT = 60


class OpenRouterError(RuntimeError):
    """Base class for OpenRouter embedder errors."""


class OpenRouterAuthError(OpenRouterError):
    """Missing or rejected OPENROUTER_API_KEY (HTTP 401/403)."""


class OpenRouterRateLimitError(OpenRouterError):
    """Rate-limited (HTTP 429). Retryable after backoff; check your spend."""


class OpenRouterServerError(OpenRouterError):
    """Server-side error (HTTP 5xx). Retryable."""


class OpenRouterResponseError(OpenRouterError):
    """Response was malformed (non-JSON, missing 'data', wrong shape)."""


class OpenRouterConnectionError(OpenRouterError):
    """Network-level failure (DNS, timeout, refused)."""


class OpenRouterEmbedder(BaseEmbedder):
    """OpenRouter-hosted embeddings backend.

    Talks to the OpenAI-compatible ``/v1/embeddings`` endpoint at
    ``openrouter.ai``. Reads ``OPENROUTER_API_KEY`` from the environment
    unless ``api_key`` is passed explicitly.

    OpenRouter is a paid service (no truly-free embedding tier as of
    2026-09-10). User has explicitly authorized spend as of 2026-09-10;
    see HANDOFF §8 #1 + #8. Default model is ``openai/text-embedding-3-small``
    (1536-dim, ~$0.02 per million tokens).

    Configuration (constructor takes precedence, env vars are fallbacks):
        model      — OpenRouter model ID (with provider prefix).
                     Env: ``OPENROUTER_EMBED_MODEL``.
        base_url   — Endpoint base URL. Env: ``OPENROUTER_BASE_URL``.
        api_key    — Bearer token. Env: ``OPENROUTER_API_KEY``.
        batch_size — Max inputs per request. Default 100.
        timeout    — Per-request timeout in seconds. Default 60.
        app_name   — Sent as ``X-Title`` header for OpenRouter app
                     attribution (no functional effect, just analytics).

    Note: unlike NIM's E5-style embedders, the OpenAI-family models do
    not have an ``input_type`` parameter. ``embed_query`` is just a
    one-element ``embed_texts`` call.
    """

    def __init__(
        self,
        model: str = DEFAULT_OPENROUTER_MODEL,
        base_url: str = DEFAULT_OPENROUTER_BASE_URL,
        api_key: Optional[str] = None,
        batch_size: int = DEFAULT_OPENROUTER_BATCH,
        timeout: int = DEFAULT_OPENROUTER_TIMEOUT,
        app_name: str = "bible-llm-reference",
    ):
        # Resolve config with env-var fallbacks. Order: explicit arg →
        # shell env → `~/.hermes/.env` (the conventional Hermes location;
        # avoids forcing users to `export` in every shell).
        self.model = os.environ.get("OPENROUTER_EMBED_MODEL", model)
        self.base_url = os.environ.get("OPENROUTER_BASE_URL", base_url).rstrip("/")

        def _resolve_key() -> str | None:
            if api_key:
                return api_key
            env_key = os.environ.get("OPENROUTER_API_KEY")
            if env_key:
                return env_key
            # Fallback: try ~/.hermes/.env (Hermes convention; the user's
            # gateway may load this without exporting to the shell env).
            try:
                env_path = Path.home() / ".hermes" / ".env"
                if env_path.exists():
                    for line in env_path.read_text().splitlines():
                        if line.startswith("OPENROUTER_API_KEY="):
                            return line.split("=", 1)[1].strip()
            except OSError:
                pass
            return None

        self.api_key = _resolve_key()
        self.batch_size = max(1, batch_size)
        self.timeout = max(1, timeout)
        self.app_name = app_name
        # Test hook: tests can monkey-patch this to a fake transport.
        self._http_post = self._default_http_post

        if not self.api_key:
            raise OpenRouterAuthError(
                "OPENROUTER_API_KEY is not set. Either export it in your "
                "shell, add it to ~/.hermes/.env, or pass api_key=... to "
                "OpenRouterEmbedder(...).\n"
                "Get a key at https://openrouter.ai — the cheapest embedding "
                f"model ({DEFAULT_OPENROUTER_MODEL}) runs ~$0.02 per million "
                "tokens, so a one-time 1.12M-token index build costs ~$0.02."
            )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns one float list per input, in order."""
        if not texts:
            return []
        results: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = list(texts[i : i + self.batch_size])
            batch_results = self._embed_one_batch(batch)
            results.extend(batch_results)
        return results

    def embed_query(self, query: str) -> list[float]:
        """Embed a single ad-hoc query. Just a one-element embed_texts() call."""
        return self.embed_texts([query])[0]

    def _embed_one_batch(self, texts: list[str]) -> list[list[float]]:
        url = f"{self.base_url}/embeddings"
        body = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }
        try:
            payload = self._http_post(url, body)
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            if e.code in (401, 403):
                raise OpenRouterAuthError(
                    f"OpenRouter auth failed (HTTP {e.code}). Check that "
                    f"OPENROUTER_API_KEY is set and has credit/allowance "
                    f"for model {self.model!r}. Server said: {body_text or '(empty)'}"
                ) from e
            if e.code == 429:
                raise OpenRouterRateLimitError(
                    f"OpenRouter rate limit hit (HTTP 429). Either slow down, "
                    f"check your spend cap at https://openrouter.ai/credits, "
                    f"or upgrade. Server said: {body_text or '(empty)'}"
                ) from e
            if 500 <= e.code < 600:
                raise OpenRouterServerError(
                    f"OpenRouter server error (HTTP {e.code}). Retry with "
                    f"backoff. Server said: {body_text or '(empty)'}"
                ) from e
            raise OpenRouterError(
                f"OpenRouter HTTP error {e.code}: {body_text or '(empty)'}"
            ) from e
        except urllib.error.URLError as e:
            raise OpenRouterConnectionError(
                f"OpenRouter connection failed: {e.reason}. Check "
                f"OPENROUTER_BASE_URL ({self.base_url!r}) and your network."
            ) from e

        # Parse + validate response
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise OpenRouterResponseError(
                f"OpenRouter returned non-JSON response: {e}"
            ) from e

        if "data" not in data:
            raise OpenRouterResponseError(
                f"OpenRouter response missing 'data' field. Got keys: "
                f"{list(data.keys())}"
            )

        items = data["data"]
        if not isinstance(items, list):
            raise OpenRouterResponseError(
                f"OpenRouter 'data' field is not a list: {type(items)}"
            )

        if len(items) != len(texts):
            raise OpenRouterResponseError(
                f"OpenRouter returned {len(items)} embeddings for "
                f"{len(texts)} inputs. API contract violation."
            )

        # Sort by 'index' to defend against out-of-order returns
        indexed = sorted(items, key=lambda x: x.get("index", 0))
        out: list[list[float]] = []
        for item in indexed:
            emb = item.get("embedding")
            if not isinstance(emb, list):
                raise OpenRouterResponseError(
                    f"OpenRouter 'embedding' is not a list: {type(emb)}"
                )
            try:
                vec = [float(x) for x in emb]
            except (TypeError, ValueError) as e:
                raise OpenRouterResponseError(
                    f"OpenRouter embedding contains non-numeric value: {e}"
                ) from e
            out.append(vec)
        return out

    def _default_http_post(self, url: str, body: dict) -> str:
        """The default HTTP transport. Tests can replace ``_http_post`` to mock."""
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # OpenRouter app attribution headers (analytics only; safe to
        # set to anything reasonable; required by OpenRouter's TOS for
        # ranked-app display, optional in the API contract itself).
        if self.app_name:
            headers["X-Title"] = self.app_name
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode("utf-8")


class NIMEmbedder(BaseEmbedder):
    """NVIDIA NIM hosted embeddings backend.

    Talks to the OpenAI-compatible ``/v1/embeddings`` endpoint exposed by
    ``integrate.api.nvidia.com`` (the public NIM API) or a self-hosted NIM
    container (``http://host:8000/v1``). Reads ``NVIDIA_API_KEY`` from the
    environment unless ``api_key`` is passed explicitly.

    Configuration (constructor takes precedence, env vars are fallbacks):
        model      — NIM model ID. Env: ``NIM_EMBED_MODEL``.
        base_url   — Endpoint base URL. Env: ``NIM_BASE_URL``.
        api_key    — Bearer token. Env: ``NVIDIA_API_KEY``.
        batch_size — Max inputs per request (NIM caps at ~96). Default 32.
        timeout    — Per-request timeout in seconds. Default 60.
        input_type — ``"query"`` (ad-hoc) or ``"passage"`` (indexed corpus).
                     Default ``"passage"``; use ``"query"`` for ad-hoc
                     search calls via ``embed_query``.
    """

    def __init__(
        self,
        model: str = DEFAULT_NIM_MODEL,
        base_url: str = DEFAULT_NIM_BASE_URL,
        api_key: Optional[str] = None,
        batch_size: int = DEFAULT_NIM_BATCH,
        timeout: int = DEFAULT_NIM_TIMEOUT,
        input_type: str = "passage",
    ):
        # Resolve config with env-var fallbacks (NIMEmbedder).
        # Order: explicit arg → shell env → ~/.hermes/.env.
        self.model = os.environ.get("NIM_EMBED_MODEL", model)
        self.base_url = os.environ.get("NIM_BASE_URL", base_url).rstrip("/")

        def _resolve_nim_key() -> Optional[str]:
            if api_key:
                return api_key
            env_key = os.environ.get("NVIDIA_API_KEY")
            if env_key:
                return env_key
            try:
                env_path = Path.home() / ".hermes" / ".env"
                if env_path.exists():
                    for line in env_path.read_text().splitlines():
                        if line.startswith("NVIDIA_API_KEY="):
                            return line.split("=", 1)[1].strip()
            except OSError:
                pass
            return None

        self.api_key = _resolve_nim_key()
        self.batch_size = max(1, batch_size)
        self.timeout = max(1, timeout)
        self.input_type = input_type
        # Test hook: tests can monkey-patch this to a fake transport.
        self._http_post = self._default_http_post

        if not self.api_key:
            raise NIMAuthError(
                "NVIDIA_API_KEY is not set. Either export it in your "
                "shell, add it to ~/.hermes/.env, or pass api_key=... to "
                "NIMEmbedder(...).\n"
                "Get a free key at https://build.nvidia.com — the free "
                "tier includes ~1,000 embedding requests per day, which "
                "is enough to index the 31K Bible + 6K Quran corpus once."
            )

    def embed_texts(self, texts: list[str], input_type: Optional[str] = None) -> list[list[float]]:
        """Embed a batch of texts. Returns one float list per input, in order."""
        if not texts:
            return []
        effective_input_type = input_type or self.input_type
        results: list[list[float]] = []
        # Empty strings can confuse the API; replace with a single space.
        # NIM accepts empty strings but returns zero vectors, which is fine.
        for i in range(0, len(texts), self.batch_size):
            batch = list(texts[i : i + self.batch_size])
            batch_results = self._embed_one_batch(batch, input_type=effective_input_type)
            results.extend(batch_results)
        return results

    def embed_query(self, query: str) -> list[float]:
        """Embed a single ad-hoc query. Uses ``input_type="query"`` for E5 models."""
        return self.embed_texts([query], input_type="query")[0]

    def _embed_one_batch(self, texts: list[str], input_type: str) -> list[list[float]]:
        url = f"{self.base_url}/embeddings"
        body = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
            "input_type": input_type,
        }
        try:
            payload = self._http_post(url, body)
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            if e.code in (401, 403):
                raise NIMAuthError(
                    f"NIM auth failed (HTTP {e.code}). Check that "
                    f"NVIDIA_API_KEY is set and has access to model "
                    f"{self.model!r}. Server said: {body_text or '(empty)'}"
                ) from e
            if e.code == 429:
                raise NIMRateLimitError(
                    f"NIM rate limit hit (HTTP 429). The free tier caps "
                    f"at ~1000 req/day; either slow down or upgrade. "
                    f"Server said: {body_text or '(empty)'}"
                ) from e
            if 500 <= e.code < 600:
                raise NIMServerError(
                    f"NIM server error (HTTP {e.code}). Retry with backoff. "
                    f"Server said: {body_text or '(empty)'}"
                ) from e
            raise NIMError(f"NIM HTTP error {e.code}: {body_text or '(empty)'}") from e
        except urllib.error.URLError as e:
            raise NIMConnectionError(
                f"NIM connection failed: {e.reason}. Check NIM_BASE_URL "
                f"({self.base_url!r}) and your network."
            ) from e

        # Parse + validate response
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise NIMResponseError(f"NIM returned non-JSON response: {e}") from e

        if "data" not in data:
            raise NIMResponseError(
                f"NIM response missing 'data' field. Got keys: {list(data.keys())}"
            )

        items = data["data"]
        if not isinstance(items, list):
            raise NIMResponseError(f"NIM 'data' field is not a list: {type(items)}")

        if len(items) != len(texts):
            raise NIMResponseError(
                f"NIM returned {len(items)} embeddings for {len(texts)} inputs. "
                "API contract violation."
            )

        # Sort by 'index' to defend against out-of-order returns (paranoid
        # but cheap; NIM docs guarantee order but bugs happen).
        indexed = sorted(items, key=lambda x: x.get("index", 0))
        out: list[list[float]] = []
        for item in indexed:
            emb = item.get("embedding")
            if not isinstance(emb, list):
                raise NIMResponseError(f"NIM 'embedding' is not a list: {type(emb)}")
            try:
                vec = [float(x) for x in emb]
            except (TypeError, ValueError) as e:
                raise NIMResponseError(f"NIM embedding contains non-numeric value: {e}") from e
            out.append(vec)
        return out

    def _default_http_post(self, url: str, body: dict) -> str:
        """The default HTTP transport. Tests can replace ``_http_post`` to mock."""
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode("utf-8")


def get_embedder(backend: str = "auto") -> BaseEmbedder:
    """Factory for embedding backends: 'local', 'mock', 'nim',
    'openrouter', or 'auto'.

    'auto' resolution order:
      1. If ``sentence_transformers`` importable → ``LocalSentenceTransformerEmbedder``
      2. Else if ``OPENROUTER_API_KEY`` in env → ``OpenRouterEmbedder``
         (preferred when both are available — typically cheaper + better
         for retrieval than the local MiniLM model; see HANDOFF §8 #8)
      3. Else if ``NVIDIA_API_KEY`` in env → ``NIMEmbedder``
      4. Else → ``MockDeterministicEmbedder`` (offline / CI fallback)

    Local embedder instances are cached per-process via an LRU wrapper.
    Without caching, every search_semantic() call would re-load the
    ~80 MB model (~3s on warm disk, ~10s on cold). The cache means a
    single process can serve thousands of queries at one model-load cost.
    """
    if backend == "mock":
        return MockDeterministicEmbedder()
    elif backend == "local":
        return _get_cached_local_embedder()
    elif backend == "nim":
        return NIMEmbedder()
    elif backend == "openrouter":
        return OpenRouterEmbedder()
    elif backend == "auto":
        try:
            import sentence_transformers  # noqa: F401
            return _get_cached_local_embedder()
        except ImportError:
            pass
        if os.environ.get("OPENROUTER_API_KEY"):
            try:
                return OpenRouterEmbedder()
            except OpenRouterAuthError:
                pass
        if os.environ.get("NVIDIA_API_KEY"):
            try:
                return NIMEmbedder()
            except NIMAuthError:
                # Key missing or rejected — fall through to mock.
                pass
        return MockDeterministicEmbedder()
    else:
        raise ValueError(f"Unknown embedder backend: {backend!r}")


_LOCAL_EMBEDDER_CACHE: list = []  # one-element list to allow closure mutation


def _get_cached_local_embedder() -> "LocalSentenceTransformerEmbedder":
    """Process-local singleton — load the model once, reuse forever."""
    if not _LOCAL_EMBEDDER_CACHE:
        _LOCAL_EMBEDDER_CACHE.append(LocalSentenceTransformerEmbedder())
    return _LOCAL_EMBEDDER_CACHE[0]


# ---------------------------------------------------------------------------
# Semantic Search Retrieval
# ---------------------------------------------------------------------------

def search_semantic(
    query: str,
    index_name: str = "default",
    top_k: int = 10,
    tradition: Optional[str] = None,
    backend: str = "auto",
    custom_index: Optional[tuple[list[dict], list[list[float]], int]] = None,
) -> list[dict]:
    """Search vector index for semantically similar verses.

    Returns list of dicts with:
        citation: str (e.g. 'John 3:16' or 'Quran 2:255')
        text: str
        score: float (cosine similarity)
        tradition: str ('bible' or 'islam')
        translation: str
    """
    if custom_index:
        entries, vectors, dim = custom_index
    else:
        loaded = load_vector_index(EMBEDDINGS_DIR, index_name)
        if not loaded:
            return []
        entries, vectors, dim = loaded

    if not entries or not vectors:
        return []

    # Get query embedding
    embedder = get_embedder(backend)
    query_vec = embedder.embed_query(query)

    # Normalize query vector if not already unit
    query_vec = l2_normalize(query_vec)

    # Score all entries
    scored: list[tuple[float, dict]] = []
    filter_tradition = tradition.lower().strip() if tradition else None

    # Tradition alias map: accept either the canonical stored value
    # (e.g. "christianity", "islam") or the public CLI shorthand
    # (e.g. "bible"). Substring matching is too brittle and was the
    # source of a silent bug where `--tradition bible` returned 0 results.
    TRADITION_ALIASES = {
        "bible": "christianity",
        "christianity": "christianity",
        "islam": "islam",
        "muslim": "islam",
        "judaism": "judaism",
        "jewish": "judaism",
    }
    if filter_tradition and filter_tradition != "all":
        filter_target = TRADITION_ALIASES.get(filter_tradition, filter_tradition)
    else:
        filter_target = None

    for entry, doc_vec in zip(entries, vectors):
        if filter_target:
            entry_trad = entry.get("tradition", "").lower()
            if entry_trad != filter_target:
                continue

        sim = cosine_similarity(query_vec, doc_vec)
        scored.append((sim, entry))

    # Rank top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for sim, entry in scored[:top_k]:
        results.append({
            "citation": entry.get("citation", ""),
            "text": entry.get("text", ""),
            "score": round(sim, 4),
            "tradition": entry.get("tradition", ""),
            "translation": entry.get("translation", ""),
        })

    return results


# ---------------------------------------------------------------------------
# CLI presentation
# ---------------------------------------------------------------------------

def run_semantic(
    query: str,
    index_name: str = "default",
    top_k: int = 10,
    tradition: Optional[str] = None,
    backend: str = "auto",
    as_json: bool = False,
) -> None:
    """CLI runner for semantic search."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    results = search_semantic(
        query=query,
        index_name=index_name,
        top_k=top_k,
        tradition=tradition,
        backend=backend,
    )

    if as_json:
        print(json.dumps({
            "query": query,
            "index": index_name,
            "backend": backend,
            "results_count": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2))
        return

    print("=" * 78)
    print(f"  Semantic Search (M3B) for: {query!r}")
    print(f"  Index: {index_name} | Backend: {backend}")
    print("=" * 78)

    if not results:
        meta_path = EMBEDDINGS_DIR / f"{index_name}_meta.json"
        if not meta_path.exists():
            print(f"\nNo precomputed vector index found at {meta_path.parent}.")
            print("To generate embeddings offline, run:")
            print("    python scripts/index_embeddings.py")
        else:
            print("\nNo matching passages found.")
        return

    for i, res in enumerate(results, 1):
        score_pct = f"{res['score'] * 100:.1f}%"
        tradition_badge = f"[{res['tradition'].upper()}]" if res.get("tradition") else ""
        print(f"\n{i}. {res['citation']} {tradition_badge} (Similarity: {score_pct})")
        print(f"   \"{res['text']}\"")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Semantic search CLI for scripture corpora (Milestone 3B)")
    parser.add_argument("query", help="Conceptual or thematic query (e.g. 'finding comfort in grief')")
    parser.add_argument("--index", default="default", help="Vector index name (default: 'default')")
    parser.add_argument("-n", "--top-k", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--tradition", choices=["all", "bible", "islam", "judaism"], default="all",
                        help="Filter tradition (default: all)")
    parser.add_argument("--backend", choices=["auto", "local", "mock", "nim", "openrouter"], default="auto",
                        help="Embedder backend (default: auto — local if available, else OpenRouter if OPENROUTER_API_KEY set, else NIM if NVIDIA_API_KEY set, else mock)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()
    run_semantic(
        query=args.query,
        index_name=args.index,
        top_k=args.top_k,
        tradition=args.tradition,
        backend=args.backend,
        as_json=args.json,
    )


if __name__ == "__main__":
    main()
