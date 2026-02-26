"""
Little Free Library (lfl) — Corpus curation and RAG validation toolkit.

Licensed under the Apache License, Version 2.0 with Commons Clause.
See LICENSE for details.
"""

__version__ = "1.0.0"

from .validation import (
    BenchmarkReport,
    Chunk,
    QuerySet,
    RetrievalResult,
    TuningParams,
    load_corpus,
    run_retrieval,
    score_results,
    generate_recommendations,
    save_report,
    load_reports,
    compare_reports,
)

from .query_gen import (
    QueryStrategy,
    generate_query_set,
    save_query_set,
    load_query_set,
)

from .benchmark import (
    run_benchmark,
    run_sweep,
    SWEEP_GRID,
)

from .chunking import (
    ChunkingStrategy,
    TextChunk,
    ChunkMetadata,
    chunk_document,
    chunk_text,
    save_chunk_to_markdown,
)

from .embeddings import (
    EmbeddingModel,
    embed_chunks,
    cosine_similarity,
    save_embeddings,
    load_embeddings,
)

from .retrieval import (
    HybridRetriever,
    RetrievalMode,
)

from .corpus_validation import (
    validate_corpus,
    format_validation_report,
)

from .profiles import (
    EmbeddingProfile,
    load_profile,
    list_profiles,
    get_default_profile,
)

__all__ = [
    # Core data structures
    "Chunk",
    "QuerySet",
    "RetrievalResult",
    "TuningParams",
    "BenchmarkReport",
    # Corpus & retrieval
    "load_corpus",
    "run_retrieval",
    "score_results",
    "generate_recommendations",
    # Report persistence
    "save_report",
    "load_reports",
    "compare_reports",
    # Query generation
    "QueryStrategy",
    "generate_query_set",
    "save_query_set",
    "load_query_set",
    # Benchmarking
    "run_benchmark",
    "run_sweep",
    "SWEEP_GRID",
    # Chunking
    "ChunkingStrategy",
    "TextChunk",
    "ChunkMetadata",
    "chunk_document",
    "chunk_text",
    "save_chunk_to_markdown",
    # Embeddings
    "EmbeddingModel",
    "embed_chunks",
    "cosine_similarity",
    "save_embeddings",
    "load_embeddings",
    # Retrieval
    "HybridRetriever",
    "RetrievalMode",
    # Validation
    "validate_corpus",
    "format_validation_report",
    # Profiles
    "EmbeddingProfile",
    "load_profile",
    "list_profiles",
    "get_default_profile",
]
