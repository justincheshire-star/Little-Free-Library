"""
Dataclasses and type definitions for the ingestion system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class DiscoveredFile:
    """Represents a file discovered during ingestion scan."""
    
    path: Path
    mime_type: str
    detected_type: str  # pdf|docx|xlsx|pages|html|txt|...
    size_bytes: int
    sha256: str
    

@dataclass
class ExtractedTable:
    """Represents a table extracted from a document."""
    
    sheet_name: str | None  # For XLSX; None for inline tables
    data: list[dict]  # Rows as list of dicts
    markdown: str  # Table rendered as Markdown
    

@dataclass
class ExtractedDoc:
    """Result of extracting content from a document."""
    
    text: str
    title: str | None
    source_path: Path
    detected_type: str
    extraction_method: Literal['native', 'converted', 'ocr']
    tables: list[ExtractedTable] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    structured_errors: list = field(default_factory=list)  # list[IngestionError]
    

@dataclass
class IngestionResult:
    """Result of ingesting a single file."""
    
    file_path: Path
    sha256: str
    detected_type: str
    extraction_method: str
    chunks_produced: int
    status: Literal['success', 'failed']
    error: str | None = None
    error_code: str | None = None              # e.g. "LFL-E101"
    warnings: list[str] = field(default_factory=list)
    structured_errors: list[dict] = field(default_factory=list)  # IngestionError.to_dict()
    

@dataclass
class IngestionManifest:
    """Manifest of an ingestion run."""
    
    run_id: str
    domain: str
    input_dir: str
    output_dir: str
    timestamp: datetime
    
    files_discovered: int
    files_converted: int
    files_extracted: int
    chunks_created: int
    chunks_updated: int
    failures: int
    
    results: list[IngestionResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    system_info: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            'run_id': self.run_id,
            'domain': self.domain,
            'input_dir': self.input_dir,
            'output_dir': self.output_dir,
            'timestamp': self.timestamp.isoformat(),
            'stats': {
                'files_discovered': self.files_discovered,
                'files_converted': self.files_converted,
                'files_extracted': self.files_extracted,
                'chunks_created': self.chunks_created,
                'chunks_updated': self.chunks_updated,
                'failures': self.failures,
            },
            'files': [
                {
                    'path': str(r.file_path),
                    'sha256': r.sha256,
                    'detected_type': r.detected_type,
                    'extraction_method': r.extraction_method,
                    'chunks_produced': r.chunks_produced,
                    'status': r.status,
                    'error': r.error,
                    'error_code': r.error_code,
                    'warnings': r.warnings,
                    'structured_errors': r.structured_errors,
                }
                for r in self.results
            ],
            'warnings': self.warnings,
            'system_info': self.system_info,
        }
