"""
Document ingestion subsystem for Little Free Library.

Provides drop-folder ingestion workflow: arbitrary docs → validated corpus.

Usage:
    from lfl.ingest import ingest_directory
    
    ingest_directory(
        domain="programming",
        input_dir="ingestion/programming",
        corpus_dir="corpora/programming",
    )
"""

from .types import (
    DiscoveredFile,
    ExtractedDoc,
    ExtractedTable,
    IngestionResult,
    IngestionManifest,
)

from .pipeline import ingest_directory

__all__ = [
    "DiscoveredFile",
    "ExtractedDoc",
    "ExtractedTable",
    "IngestionResult",
    "IngestionManifest",
    "ingest_directory",
]

__version__ = "1.0.0"
