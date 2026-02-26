"""
lfl.query_gen
=============
Synthetic query generation for retrieval validation.

Generates ground-truth (query → chunk_id) pairs from corpus chunks
without requiring human annotation. Three strategies are available:

  heuristic   — fast, no model needed, good baseline
  extractive  — extracts key sentences using term frequency
  llm         — uses a local LLM via pxctx or llama.cpp (best quality)

The heuristic strategy is the default and is always available.
"""

from __future__ import annotations

import random
import re
import string
from dataclasses import dataclass
from typing import Literal

from .validation import Chunk, QuerySet


# ---------------------------------------------------------------------------
# Strategy: heuristic
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Strip markdown syntax and normalize whitespace."""
    text = re.sub(r"```[\s\S]*?```", "", text)       # code blocks
    text = re.sub(r"`[^`]+`", "", text)               # inline code
    text = re.sub(r"#{1,6}\s+", "", text)             # headings
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links
    text = re.sub(r"[*_~]{1,3}", "", text)            # bold/italic
    text = re.sub(r"\s+", " ", text)                  # normalize whitespace
    return text.strip()


def _sentences(text: str) -> list[str]:
    """Split text into sentences."""
    raw = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw if len(s.strip()) > 20]


def _tf_score(sentence: str, all_text: str) -> float:
    """Score a sentence by term frequency of its words in the full chunk."""
    words = sentence.lower().translate(str.maketrans("", "", string.punctuation)).split()
    corpus_words = all_text.lower().split()
    if not words or not corpus_words:
        return 0.0
    freq = {w: corpus_words.count(w) for w in set(words)}
    return sum(freq.values()) / len(words)


def _to_question(sentence: str, domain: str) -> str:
    """
    Convert a declarative sentence into a question using simple heuristics.
    Not perfect — but good enough to drive recall tests.
    """
    sentence = sentence.rstrip(".!?")

    # Pattern: "X is/are Y" → "What is/are X?"
    m = re.match(r"^(.+?)\s+(is|are|was|were|refers to|means)\s+(.+)$", sentence, re.I)
    if m:
        subject = m.group(1).strip()
        verb = m.group(2).strip()
        return f"What {verb} {subject}?"

    # Pattern: "To X, you must Y" → "How do you X?"
    m = re.match(r"^To\s+(\w[\w\s]+?),\s+you", sentence, re.I)
    if m:
        return f"How do you {m.group(1).strip().lower()}?"

    # Pattern: starts with "The X" → "What is the X?"
    m = re.match(r"^The\s+(\w[\w\s]{2,40}?)\s+(is|are|can|will|should|must)", sentence, re.I)
    if m:
        return f"What is the {m.group(1).strip().lower()}?"

    # Fallback: prepend domain context
    short = sentence[:80] + ("..." if len(sentence) > 80 else "")
    return f"In {domain}, what does this mean: {short}?"


def _heuristic_queries(chunk: Chunk, n: int = 2) -> list[str]:
    """Generate n synthetic queries from a chunk using heuristics."""
    cleaned = _clean(chunk.body)
    sents = _sentences(cleaned)
    if not sents:
        return [f"What is {chunk.title}?"]

    # Score and pick top sentences
    scored = [(s, _tf_score(s, cleaned)) for s in sents]
    scored.sort(key=lambda x: -x[1])
    top = [s for s, _ in scored[:max(n * 2, 4)]]

    # Convert to questions
    questions = [_to_question(s, chunk.domain) for s in top]

    # Deduplicate and limit
    seen: set[str] = set()
    unique = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)
        if len(unique) >= n:
            break

    # Pad with title-based query if needed
    if not unique:
        unique.append(f"What is {chunk.title}?")

    return unique


# ---------------------------------------------------------------------------
# Strategy: extractive (TF-IDF key phrase)
# ---------------------------------------------------------------------------

def _extractive_queries(chunk: Chunk, n: int = 2) -> list[str]:
    """
    Extract key noun phrases and build queries around them.
    Slightly better than pure heuristic for technical content.
    """
    cleaned = _clean(chunk.body)

    # Extract capitalized phrases (likely technical terms / proper nouns)
    phrases = re.findall(r"\b[A-Z][a-zA-Z0-9_\-]{2,30}(?:\s+[A-Z][a-zA-Z0-9_\-]{2,30})*\b", cleaned)
    phrases = list(dict.fromkeys(phrases))  # deduplicate, preserve order

    # Also grab terms from the title
    title_terms = [t for t in chunk.title.split() if len(t) > 3]

    queries = []
    for phrase in (phrases + title_terms)[:n * 2]:
        queries.append(f"How does {phrase} work in {chunk.domain}?")

    if not queries:
        return _heuristic_queries(chunk, n)

    return queries[:n]


# ---------------------------------------------------------------------------
# Strategy: LLM (optional, uses local inference)
# ---------------------------------------------------------------------------

def _llm_queries(chunk: Chunk, n: int = 2, model_endpoint: str = "") -> list[str]:
    """
    Generate high-quality queries using a local LLM endpoint.
    Falls back to heuristic if the endpoint is unavailable.

    model_endpoint: URL for a local inference server (e.g. llama.cpp HTTP server)
    """
    try:
        import urllib.request
        import json as _json

        prompt = (
            f"Generate {n} short, specific questions that can be answered using "
            f"the following text. Output only the questions, one per line, no numbering.\n\n"
            f"Domain: {chunk.domain}\n\n"
            f"Text:\n{chunk.body[:1200]}"
        )

        payload = _json.dumps({
            "prompt": prompt,
            "max_tokens": 256,
            "temperature": 0.3,
            "stop": ["\n\n"],
        }).encode("utf-8")

        req = urllib.request.Request(
            model_endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())
            text = data.get("content", data.get("text", ""))
            lines = [l.strip() for l in text.strip().splitlines() if l.strip() and "?" in l]
            if lines:
                return lines[:n]
    except Exception as e:
        print(f"  [WARN] LLM query gen failed ({e}), falling back to heuristic")

    return _heuristic_queries(chunk, n)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

QueryStrategy = Literal["heuristic", "extractive", "llm"]


def generate_query_set(
    chunks: list[Chunk],
    queries_per_chunk: int = 2,
    strategy: QueryStrategy = "heuristic",
    llm_endpoint: str = "",
    seed: int = 42,
    max_chunks: int | None = None,
) -> QuerySet:
    """
    Generate a ground-truth QuerySet from a list of corpus chunks.

    Parameters
    ----------
    chunks            : loaded corpus chunks
    queries_per_chunk : how many queries to generate per chunk
    strategy          : heuristic | extractive | llm
    llm_endpoint      : local LLM HTTP endpoint (required for llm strategy)
    seed              : random seed for reproducibility
    max_chunks        : if set, sample this many chunks (useful for large corpora)

    Returns
    -------
    QuerySet with (query_text, expected_chunk_id) pairs
    """
    import datetime

    random.seed(seed)

    sample = chunks
    if max_chunks and len(chunks) > max_chunks:
        sample = random.sample(chunks, max_chunks)

    pairs: list[tuple[str, str]] = []

    for chunk in sample:
        if strategy == "heuristic":
            questions = _heuristic_queries(chunk, queries_per_chunk)
        elif strategy == "extractive":
            questions = _extractive_queries(chunk, queries_per_chunk)
        elif strategy == "llm":
            questions = _llm_queries(chunk, queries_per_chunk, llm_endpoint)
        else:
            questions = _heuristic_queries(chunk, queries_per_chunk)

        for q in questions:
            pairs.append((q, chunk.chunk_id))

    return QuerySet(
        queries=pairs,
        generated_at=datetime.datetime.utcnow().isoformat(),
        strategy=strategy,
    )


def save_query_set(qs: QuerySet, path: "Path") -> None:  # type: ignore[name-defined]
    import json
    from pathlib import Path as _Path
    p = _Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({
            "generated_at": qs.generated_at,
            "strategy": qs.strategy,
            "count": len(qs.queries),
            "queries": [{"query": q, "chunk_id": cid} for q, cid in qs.queries],
        }, indent=2),
        encoding="utf-8",
    )


def load_query_set(path: "Path") -> QuerySet:  # type: ignore[name-defined]
    import json
    from pathlib import Path as _Path
    d = json.loads(_Path(path).read_text(encoding="utf-8"))
    return QuerySet(
        queries=[(item["query"], item["chunk_id"]) for item in d["queries"]],
        generated_at=d.get("generated_at", ""),
        strategy=d.get("strategy", "heuristic"),
    )
