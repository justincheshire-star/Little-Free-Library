"""
chunking.py — Text chunking utilities for pxctx.

Strategies:
  chunk_text()     — paragraph/sentence-aware chunking with overlap
  chunk_markdown() — heading-context-aware chunking, returns (heading_path, text)
"""

from __future__ import annotations

import re
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Rough word-based token estimate (1 token ≈ 0.75 words → invert: words * 1.3)."""
    words = len(text.split())
    return max(1, int(words * 1.3))


def estimate_chars_per_token() -> int:
    return 4  # approx average


# ---------------------------------------------------------------------------
# Sentence splitter
# ---------------------------------------------------------------------------

_SENT_RE = re.compile(r'([.!?]+\s+)(?=[A-Z"\'])')


def split_sentences(text: str) -> List[str]:
    """Split text into sentences on '.!?' followed by whitespace + uppercase."""
    parts = _SENT_RE.split(text)
    # _SENT_RE.split returns alternating [text, delim, text, delim, ...]
    sentences: List[str] = []
    buf = ""
    for part in parts:
        if _SENT_RE.fullmatch(part):
            buf += part
            sentences.append(buf.strip())
            buf = ""
        else:
            buf += part
    if buf.strip():
        sentences.append(buf.strip())
    return [s for s in sentences if s]


# ---------------------------------------------------------------------------
# Plain text chunking
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    target_tokens: int = 600,
    overlap_tokens: int = 100,
    min_chunk_tokens: int = 50,
) -> List[str]:
    """
    Split text into overlapping chunks of approximately target_tokens.

    Algorithm:
    1. Split on double-newlines (paragraphs).
    2. Accumulate paragraphs into a chunk until target_tokens is reached.
    3. Overlap: carry the last paragraph into the next chunk.
    4. If a single paragraph exceeds target_tokens, split by sentences.
    5. Merge tail chunks below min_chunk_tokens into the previous chunk.

    Returns list of chunk strings.
    """
    paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]
    if not paragraphs:
        return [text.strip()] if text.strip() else []

    # Expand overly large paragraphs into sentences
    expanded: List[str] = []
    for para in paragraphs:
        if estimate_tokens(para) > target_tokens:
            sents = split_sentences(para)
            if sents:
                expanded.extend(sents)
            else:
                expanded.append(para)
        else:
            expanded.append(para)

    chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for piece in expanded:
        piece_tokens = estimate_tokens(piece)

        if current_tokens + piece_tokens > target_tokens and current:
            # Flush
            chunks.append("\n\n".join(current))
            # Overlap: keep last piece of current as start of next chunk
            overlap_piece = current[-1]
            current = [overlap_piece]
            current_tokens = estimate_tokens(overlap_piece)

        current.append(piece)
        current_tokens += piece_tokens

    if current:
        chunks.append("\n\n".join(current))

    # Merge tail chunk if too small
    if len(chunks) > 1 and estimate_tokens(chunks[-1]) < min_chunk_tokens:
        merged = chunks[-2] + "\n\n" + chunks[-1]
        chunks = chunks[:-2] + [merged]

    return chunks


# ---------------------------------------------------------------------------
# Markdown-aware chunking
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)', re.MULTILINE)


def chunk_markdown(
    text: str,
    target_tokens: int = 600,
    overlap_tokens: int = 100,
) -> List[Tuple[str, str]]:
    """
    Split markdown text into (heading_path, chunk_text) tuples.

    heading_path captures the hierarchy context, e.g.:
      "# Architecture > ## Database > ### Schema"

    This preserves semantic context when text is retrieved in isolation.
    """
    lines = text.splitlines(keepends=True)

    # Parse heading stack and section extents
    sections: List[Tuple[str, str]] = []  # (heading_path, body_text)
    heading_stack: List[Tuple[int, str]] = []  # [(level, heading_text), ...]
    current_body: List[str] = []
    current_path = ""

    for line in lines:
        m = _HEADING_RE.match(line.rstrip())
        if m:
            # Flush current section
            if current_body:
                body = "".join(current_body).strip()
                if body:
                    sections.append((current_path, body))
            current_body = []

            level = len(m.group(1))
            heading_text = m.group(2).strip()

            # Trim stack to current level
            heading_stack = [(l, h) for l, h in heading_stack if l < level]
            heading_stack.append((level, heading_text))

            current_path = " > ".join(h for _, h in heading_stack)
            current_body = [line]
        else:
            current_body.append(line)

    # Flush last section
    if current_body:
        body = "".join(current_body).strip()
        if body:
            sections.append((current_path, body))

    if not sections:
        # No headings — fall back to plain chunking
        for chunk in chunk_text(text, target_tokens, overlap_tokens):
            yield ("", chunk)
        return

    # Now chunk each section; large sections get split further
    results: List[Tuple[str, str]] = []
    for path, body in sections:
        if estimate_tokens(body) <= target_tokens:
            results.append((path, body))
        else:
            sub_chunks = chunk_text(body, target_tokens, overlap_tokens)
            for i, sub in enumerate(sub_chunks):
                sub_path = path + (f" [part {i+1}/{len(sub_chunks)}]" if len(sub_chunks) > 1 else "")
                results.append((sub_path, sub))

    # Merge tiny sections (< 25 tokens) into the previous chunk
    merged: List[Tuple[str, str]] = []
    for path, body in results:
        if merged and estimate_tokens(body) < 25:
            prev_path, prev_body = merged[-1]
            merged[-1] = (prev_path, prev_body + "\n\n" + body)
        else:
            merged.append((path, body))

    yield from merged


# ---------------------------------------------------------------------------
# Convenience: chunk + count tokens
# ---------------------------------------------------------------------------

def chunk_with_counts(
    text: str,
    is_markdown: bool = False,
    target_tokens: int = 600,
    overlap_tokens: int = 100,
) -> List[Tuple[str, str, int]]:
    """
    Returns list of (heading_path, chunk_text, estimated_tokens).
    heading_path is empty string for plain-text mode.
    """
    result: List[Tuple[str, str, int]] = []
    if is_markdown:
        for path, chunk in chunk_markdown(text, target_tokens, overlap_tokens):
            result.append((path, chunk, estimate_tokens(chunk)))
    else:
        for chunk in chunk_text(text, target_tokens, overlap_tokens):
            result.append(("", chunk, estimate_tokens(chunk)))
    return result
