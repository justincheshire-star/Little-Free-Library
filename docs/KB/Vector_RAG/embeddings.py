"""
embeddings.py — Embedding model wrapper for pxctx.

Primary model: nomic-ai/nomic-embed-text-v1.5 (768-dim, Apache 2.0)
Gracefully degrades to a no-vector fallback when sentence-transformers
or numpy are unavailable (FTS-only retrieval still works).

Public API::

    from Vector_RAG.embeddings import (
        encode, encode_single,
        serialize_embedding, deserialize_embedding,
        cosine_similarity, vector_search,
        embedding_available, EMBEDDING_DIM,
    )
"""

from __future__ import annotations

import os
import struct
import warnings
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Optional heavy deps
# ---------------------------------------------------------------------------

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except ImportError:
    _HAS_ST = False

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(os.environ.get("PXCTX_ROOT", Path(__file__).parent.parent.parent.parent))
_LOCAL_MODEL_PATH = _REPO_ROOT / "models" / "nomic-embed-text"
_DEFAULT_MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
_TRUST_REMOTE = True

EMBEDDING_DIM = 768
EMBEDDING_MODEL_NAME = os.environ.get("PXCTX_EMBED_MODEL", _DEFAULT_MODEL_NAME)

# Global lazy-loaded model
_model: Optional[object] = None
_load_attempted: bool = False
_load_error: Optional[str] = None


def embedding_available() -> bool:
    """Returns True if vector embeddings can be computed."""
    return _HAS_NUMPY and _HAS_ST


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def get_model() -> object:
    """
    Lazy-load the embedding model.
    Tries local path first, then HuggingFace download.
    Raises RuntimeError if unavailable.
    """
    global _model, _load_attempted, _load_error

    if _load_attempted:
        if _model is not None:
            return _model
        raise RuntimeError(f"Embedding model unavailable: {_load_error}")

    _load_attempted = True

    if not _HAS_NUMPY:
        _load_error = "numpy not installed — run: pip install numpy"
        raise RuntimeError(_load_error)

    if not _HAS_ST:
        _load_error = "sentence-transformers not installed — run: pip install sentence-transformers"
        raise RuntimeError(_load_error)

    # Try local path first
    if _LOCAL_MODEL_PATH.exists():
        model_path = str(_LOCAL_MODEL_PATH)
    else:
        model_path = EMBEDDING_MODEL_NAME

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _model = SentenceTransformer(
                model_path,
                trust_remote_code=_TRUST_REMOTE,
            )
        return _model  # type: ignore[return-value]
    except Exception as exc:
        _load_error = str(exc)
        raise RuntimeError(f"Failed to load embedding model '{model_path}': {exc}") from exc


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def encode(
    texts: Sequence[str],
    show_progress: bool = False,
    batch_size: int = 32,
) -> "np.ndarray":
    """
    Encode a list of texts into normalized embeddings.
    Returns ndarray of shape (len(texts), EMBEDDING_DIM), dtype float32.
    """
    model = get_model()
    # nomic-embed-text uses task prefixes
    prefixed = [f"search_document: {t}" for t in texts]
    embeddings = model.encode(  # type: ignore[attr-defined]
        prefixed,
        normalize_embeddings=True,
        show_progress_bar=show_progress,
        batch_size=batch_size,
    )
    return np.array(embeddings, dtype=np.float32)


def encode_query(text: str) -> "np.ndarray":
    """
    Encode a *query* string (uses 'search_query:' prefix for nomic).
    Returns ndarray of shape (EMBEDDING_DIM,).
    """
    model = get_model()
    prefixed = f"search_query: {text}"
    emb = model.encode(  # type: ignore[attr-defined]
        [prefixed],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.array(emb[0], dtype=np.float32)


def encode_single(text: str) -> "np.ndarray":
    """Encode a single document text. Returns shape (EMBEDDING_DIM,)."""
    return encode([text])[0]


# ---------------------------------------------------------------------------
# Serialization — packed float32 (no numpy dependency at read time)
# ---------------------------------------------------------------------------

def serialize_embedding(embedding: "np.ndarray") -> bytes:
    """Pack float32 array to bytes."""
    if _HAS_NUMPY:
        arr = np.array(embedding, dtype=np.float32)
        return struct.pack(f"{len(arr)}f", *arr)
    raise RuntimeError("numpy required for serialization")


def deserialize_embedding(data: bytes, dim: int = EMBEDDING_DIM) -> "np.ndarray":
    """Unpack bytes to float32 ndarray."""
    count = len(data) // 4  # 4 bytes per float32
    values = struct.unpack(f"{count}f", data)
    if _HAS_NUMPY:
        return np.array(values, dtype=np.float32)
    raise RuntimeError("numpy required for deserialization")


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

def cosine_similarity(a: "np.ndarray", b: "np.ndarray") -> float:
    """
    Cosine similarity of two vectors.
    If both are already unit-normalized (as returned by encode/encode_query),
    this is just np.dot(a, b).
    """
    if not _HAS_NUMPY:
        return 0.0
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def vector_search(
    query_emb: "np.ndarray",
    candidates: Sequence[Tuple[str, bytes]],
    top_k: int = 20,
) -> List[Tuple[str, float]]:
    """
    Brute-force cosine search.

    Args:
        query_emb: (EMBEDDING_DIM,) query vector (already normalized).
        candidates: list of (chunk_id, embedding_bytes) pairs.
        top_k: max results.

    Returns:
        List of (chunk_id, similarity_score) sorted descending.
    """
    if not _HAS_NUMPY or not candidates:
        return []

    ids: List[str] = []
    vecs: List["np.ndarray"] = []

    for cid, raw in candidates:
        try:
            vec = deserialize_embedding(raw)
            ids.append(cid)
            vecs.append(vec)
        except Exception:
            continue

    if not vecs:
        return []

    matrix = np.stack(vecs, axis=0)  # (N, DIM)
    q = np.array(query_emb, dtype=np.float32)

    # Cosine sim = dot product when vectors are unit-normalized
    q_norm = np.linalg.norm(q)
    if q_norm > 0:
        q = q / q_norm

    # Normalize rows
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    matrix = matrix / norms

    scores = matrix @ q  # (N,)

    # Top-k (partial sort)
    k = min(top_k, len(scores))
    top_indices = int_indices = scores.argsort()[::-1][:k]

    return [(ids[i], float(scores[i])) for i in top_indices]
