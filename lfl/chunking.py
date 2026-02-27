"""
lfl.chunking — Document chunking strategies.

Implements multiple chunking strategies for converting raw documents into
retrieval-ready chunks with configurable size and overlap.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal


ChunkingStrategy = Literal["naive_paragraph", "heading_aware", "sliding_window", "semantic"]


@dataclass
class ChunkMetadata:
    """Metadata for a generated chunk."""
    chunk_id: str
    title: str
    domain: str
    subdomain: str
    source: str
    source_license: str
    source_id: str
    source_path: str
    retrieved_at: str
    verified: str
    importance: float
    tags: list[str]
    version: str
    content_hash: str


@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    content: str
    metadata: ChunkMetadata
    token_count: int
    start_offset: int = 0
    end_offset: int = 0


def _count_tokens(text: str, tokenizer: Callable[[str], int] | None = None) -> int:
    """
    Count tokens in text. Uses provided tokenizer or naive approximation.
    
    Parameters
    ----------
    text : str
        Text to count tokens for
    tokenizer : callable, optional
        Function that takes text and returns token count
    
    Returns
    -------
    int
        Approximate token count
    """
    if tokenizer:
        return tokenizer(text)
    
    # Naive approximation: ~4 chars per token for English
    return max(1, len(text.strip()) // 4)


def _create_chunk_id(content: str, index: int) -> str:
    """Generate a unique, deterministic chunk ID."""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    return f"chunk_{index:04d}_{content_hash}"


def _create_content_hash(content: str) -> str:
    """Generate SHA256 hash of content."""
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _extract_title_from_content(content: str, max_length: int = 60) -> str:
    """Extract a title from chunk content."""
    # Try to extract first heading
    heading_match = re.search(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
    if heading_match:
        return heading_match.group(1).strip()[:max_length]
    
    # Try first sentence
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Remove markdown formatting
            line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
            line = re.sub(r'[*_`]', '', line)
            if len(line) > 10:
                return line[:max_length]
    
    return "Untitled Chunk"


# ---------------------------------------------------------------------------
# Strategy: naive_paragraph
# ---------------------------------------------------------------------------

def chunk_naive_paragraph(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """
    Split text on double newlines (paragraphs) and pack to chunk_size.
    
    Parameters
    ----------
    text : str
        Input text to chunk
    chunk_size : int
        Target tokens per chunk
    overlap : int
        Token overlap between consecutive chunks
    tokenizer : callable, optional
        Token counting function
    
    Returns
    -------
    list[str]
        List of chunk texts
    """
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if not paragraphs:
        return [text] if text.strip() else []
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = _count_tokens(para, tokenizer)
        
        # If single paragraph exceeds chunk_size, split it by sentences
        if para_tokens > chunk_size:
            # Flush current chunk
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            # Split large paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                sent_tokens = _count_tokens(sent, tokenizer)
                if current_tokens + sent_tokens > chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    # Keep overlap
                    overlap_text = ' '.join(current_chunk[-2:]) if len(current_chunk) >= 2 else ''
                    current_chunk = [overlap_text] if overlap_text else []
                    current_tokens = _count_tokens(overlap_text, tokenizer)
                
                current_chunk.append(sent)
                current_tokens += sent_tokens
            continue
        
        # Check if adding this paragraph would exceed chunk_size
        if current_tokens + para_tokens > chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            
            # Keep last paragraph for overlap if it fits
            if overlap > 0 and current_chunk:
                last_para = current_chunk[-1]
                last_para_tokens = _count_tokens(last_para, tokenizer)
                if last_para_tokens <= overlap:
                    current_chunk = [last_para]
                    current_tokens = last_para_tokens
                else:
                    current_chunk = []
                    current_tokens = 0
            else:
                current_chunk = []
                current_tokens = 0
        
        current_chunk.append(para)
        current_tokens += para_tokens
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


# ---------------------------------------------------------------------------
# Strategy: heading_aware
# ---------------------------------------------------------------------------

def chunk_heading_aware(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """
    Split at markdown headings first, then pack to chunk_size.
    
    Preserves document structure by keeping related content under headings together.
    
    Parameters
    ----------
    text : str
        Input text to chunk
    chunk_size : int
        Target tokens per chunk
    overlap : int
        Token overlap between consecutive chunks
    tokenizer : callable, optional
        Token counting function
    
    Returns
    -------
    list[str]
        List of chunk texts
    """
    # Split by headings (# to ######)
    sections = re.split(r'(^#{1,6}\s+.+$)', text, flags=re.MULTILINE)
    
    # Reconstruct sections with their headings
    structured_sections = []
    current_section = ""
    
    for i, part in enumerate(sections):
        if re.match(r'^#{1,6}\s+', part):
            # This is a heading
            if current_section:
                structured_sections.append(current_section)
            current_section = part
        else:
            # This is content
            current_section += part
    
    if current_section:
        structured_sections.append(current_section)
    
    if not structured_sections:
        # No headings found, fall back to naive paragraph
        return chunk_naive_paragraph(text, chunk_size, overlap, tokenizer)
    
    # Now pack sections into chunks
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for section in structured_sections:
        section = section.strip()
        if not section:
            continue
        
        section_tokens = _count_tokens(section, tokenizer)
        
        # If section is too large, split it by paragraphs
        if section_tokens > chunk_size:
            # Flush current chunk
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            # Split section by paragraphs
            section_chunks = chunk_naive_paragraph(section, chunk_size, overlap, tokenizer)
            chunks.extend(section_chunks)
            continue
        
        # Check if adding this section would exceed chunk_size
        if current_tokens + section_tokens > chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            
            # For heading-aware, we don't overlap sections to preserve structure
            current_chunk = []
            current_tokens = 0
        
        current_chunk.append(section)
        current_tokens += section_tokens
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


# ---------------------------------------------------------------------------
# Strategy: sliding_window
# ---------------------------------------------------------------------------

def chunk_sliding_window(
    text: str,
    chunk_size: int = 512,
    overlap: int = 128,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """
    Fixed-size sliding window with overlap.
    
    Creates chunks of consistent size by sliding a window across the text.
    Best for dense technical content where context boundaries are unclear.
    
    Parameters
    ----------
    text : str
        Input text to chunk
    chunk_size : int
        Target tokens per chunk
    overlap : int
        Token overlap between consecutive chunks
    tokenizer : callable, optional
        Token counting function
    
    Returns
    -------
    list[str]
        List of chunk texts
    """
    # Split into sentences for cleaner boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return [text] if text.strip() else []
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    i = 0
    while i < len(sentences):
        sent = sentences[i]
        sent_tokens = _count_tokens(sent, tokenizer)
        
        if current_tokens + sent_tokens <= chunk_size:
            current_chunk.append(sent)
            current_tokens += sent_tokens
            i += 1
        else:
            # Chunk is full, save it
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Slide window back by overlap amount
                overlap_tokens = 0
                overlap_sents = []
                
                # Collect sentences from the end until we have overlap tokens
                for j in range(len(current_chunk) - 1, -1, -1):
                    s = current_chunk[j]
                    s_tokens = _count_tokens(s, tokenizer)
                    if overlap_tokens + s_tokens <= overlap:
                        overlap_sents.insert(0, s)
                        overlap_tokens += s_tokens
                    else:
                        break
                
                current_chunk = overlap_sents
                current_tokens = overlap_tokens
            else:
                # Single sentence exceeds chunk_size, include it anyway
                chunks.append(sent)
                i += 1
                current_chunk = []
                current_tokens = 0
    
    # Add final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


# ---------------------------------------------------------------------------
# Strategy: semantic (placeholder)
# ---------------------------------------------------------------------------

def chunk_semantic(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """
    Semantic boundary detection (placeholder).
    
    Would use sentence embeddings to detect topical boundaries.
    Currently falls back to heading_aware strategy.
    
    Parameters
    ----------
    text : str
        Input text to chunk
    chunk_size : int
        Target tokens per chunk
    overlap : int
        Token overlap between consecutive chunks
    tokenizer : callable, optional
        Token counting function
    
    Returns
    -------
    list[str]
        List of chunk texts
    """
    # TODO: Implement using sentence-transformers for semantic segmentation
    # For now, fall back to heading_aware
    return chunk_heading_aware(text, chunk_size, overlap, tokenizer)


# ---------------------------------------------------------------------------
# Main chunking interface
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    strategy: ChunkingStrategy = "naive_paragraph",
    chunk_size: int = 512,
    overlap: int = 64,
    min_chunk_tokens: int = 32,
    max_chunk_tokens: int = 1024,
    tokenizer: Callable[[str], int] | None = None,
) -> list[str]:
    """
    Chunk text using the specified strategy.
    
    Parameters
    ----------
    text : str
        Input text to chunk
    strategy : ChunkingStrategy
        Chunking strategy to use
    chunk_size : int
        Target tokens per chunk
    overlap : int
        Token overlap between consecutive chunks
    min_chunk_tokens : int
        Discard chunks smaller than this
    max_chunk_tokens : int
        Hard cap per chunk (safety valve)
    tokenizer : callable, optional
        Token counting function
    
    Returns
    -------
    list[str]
        List of chunk texts
    """
    # Select strategy
    if strategy == "naive_paragraph":
        chunks = chunk_naive_paragraph(text, chunk_size, overlap, tokenizer)
    elif strategy == "heading_aware":
        chunks = chunk_heading_aware(text, chunk_size, overlap, tokenizer)
    elif strategy == "sliding_window":
        chunks = chunk_sliding_window(text, chunk_size, overlap, tokenizer)
    elif strategy == "semantic":
        chunks = chunk_semantic(text, chunk_size, overlap, tokenizer)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    # Filter by size constraints
    filtered_chunks = []
    for chunk in chunks:
        tokens = _count_tokens(chunk, tokenizer)
        if min_chunk_tokens <= tokens <= max_chunk_tokens:
            filtered_chunks.append(chunk)
    
    return filtered_chunks


def chunk_document(
    text: str,
    base_metadata: dict,
    strategy: ChunkingStrategy = "naive_paragraph",
    chunk_size: int = 512,
    overlap: int = 64,
    min_chunk_tokens: int = 32,
    max_chunk_tokens: int = 1024,
    tokenizer: Callable[[str], int] | None = None,
) -> list[TextChunk]:
    """
    Chunk a document and generate complete metadata for each chunk.
    
    Parameters
    ----------
    text : str
        Input text to chunk
    base_metadata : dict
        Base metadata to apply to all chunks (domain, source, etc.)
    strategy : ChunkingStrategy
        Chunking strategy to use
    chunk_size : int
        Target tokens per chunk
    overlap : int
        Token overlap between consecutive chunks
    min_chunk_tokens : int
        Discard chunks smaller than this
    max_chunk_tokens : int
        Hard cap per chunk
    tokenizer : callable, optional
        Token counting function
    
    Returns
    -------
    list[TextChunk]
        List of chunks with complete metadata
    """
    chunk_texts = chunk_text(
        text, strategy, chunk_size, overlap, min_chunk_tokens, max_chunk_tokens, tokenizer
    )
    
    chunks_with_metadata = []
    
    for i, text_content in enumerate(chunk_texts):
        chunk_id = _create_chunk_id(text_content, i)
        title = _extract_title_from_content(text_content)
        content_hash = _create_content_hash(text_content)
        token_count = _count_tokens(text_content, tokenizer)
        
        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            title=title,
            domain=base_metadata.get("domain", "unknown"),
            subdomain=base_metadata.get("subdomain", ""),
            source=base_metadata.get("source", ""),
            source_license=base_metadata.get("source_license", ""),
            source_id=base_metadata.get("source_id", ""),
            source_path=base_metadata.get("source_path", ""),
            retrieved_at=base_metadata.get("retrieved_at", ""),
            verified=base_metadata.get("verified", ""),
            importance=float(base_metadata.get("importance", 0.5)),
            tags=base_metadata.get("tags", []),
            version=base_metadata.get("version", "1.0.0"),
            content_hash=content_hash,
        )
        
        chunk_obj = TextChunk(
            content=text_content,
            metadata=metadata,
            token_count=token_count,
        )
        
        chunks_with_metadata.append(chunk_obj)
    
    return chunks_with_metadata


def save_chunk_to_markdown(chunk: TextChunk, output_path: Path) -> None:
    """
    Save a chunk as a markdown file with YAML frontmatter.
    
    Parameters
    ----------
    chunk : TextChunk
        Chunk to save
    output_path : Path
        Output file path
    """
    md = chunk.metadata
    
    # Escape double quotes inside string values for valid YAML
    def _esc(val: str) -> str:
        return str(val).replace('\\', '\\\\').replace('"', '\\"')
    
    frontmatter = f"""---
title: "{_esc(md.title)}"
domain: "{_esc(md.domain)}"
subdomain: "{_esc(md.subdomain)}"
source: "{_esc(md.source)}"
source_license: "{_esc(md.source_license)}"
source_id: "{_esc(md.source_id)}"
source_path: "{_esc(md.source_path)}"
retrieved_at: "{_esc(md.retrieved_at)}"
verified: "{_esc(md.verified)}"
importance: {md.importance}
tags: {md.tags}
version: "{_esc(md.version)}"
content_hash: "{_esc(md.content_hash)}"
---

{chunk.content}
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(frontmatter, encoding="utf-8")
