"""
File type detection and routing for ingestion pipeline.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from .types import DiscoveredFile


# Extension-to-type mapping (fallback when MIME detection unavailable)
EXTENSION_MAP = {
    '.pdf': 'pdf',
    '.doc': 'doc_legacy',
    '.docx': 'docx',
    '.xls': 'xls_legacy',
    '.xlsx': 'xlsx',
    '.ppt': 'ppt_legacy',
    '.pptx': 'pptx',
    '.pages': 'pages',
    '.numbers': 'numbers',
    '.key': 'keynote',
    '.html': 'html',
    '.htm': 'html',
    '.md': 'markdown',
    '.txt': 'text',
    '.rtf': 'rtf',
    '.odt': 'odt',
    '.ods': 'ods',
    '.odp': 'odp',
    '.epub': 'epub',
    '.csv': 'csv',
    '.tsv': 'tsv',
    '.json': 'json',
}


def detect_file_type(path: Path) -> str:
    """
    Detect file type using MIME detection with extension fallback.
    
    Returns:
        Type string (pdf|docx|xlsx|pages|html|txt|unknown)
    """
    # Try python-magic (Linux/macOS)
    try:
        import magic
        mime = magic.from_file(str(path), mime=True)
        return _mime_to_type(mime, path.suffix.lower())
    except (ImportError, Exception):
        pass
    
    # Try puremagic (Windows fallback)
    try:
        import puremagic
        results = puremagic.magic_file(str(path))
        if results:
            mime = results[0].mime_type
            return _mime_to_type(mime, path.suffix.lower())
    except (ImportError, Exception):
        pass
    
    # Fallback to extension
    ext = path.suffix.lower()
    return EXTENSION_MAP.get(ext, 'unknown')


def _mime_to_type(mime: str, extension: str) -> str:
    """Convert MIME type to internal type string."""
    mime_map = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
        'application/msword': 'doc_legacy',
        'application/vnd.ms-excel': 'xls_legacy',
        'application/vnd.ms-powerpoint': 'ppt_legacy',
        'text/html': 'html',
        'text/plain': 'text',
        'text/markdown': 'markdown',
        'text/csv': 'csv',
        'application/json': 'json',
    }
    
    # Apple iWork formats (often detected as ZIP)
    if mime == 'application/zip':
        return EXTENSION_MAP.get(extension, 'unknown')
    
    return mime_map.get(mime, EXTENSION_MAP.get(extension, 'unknown'))


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def discover_files(
    input_dir: Path,
    recursive: bool = True,
) -> list[DiscoveredFile]:
    """
    Scan directory and discover ingestible files.
    
    Args:
        input_dir: Directory to scan
        recursive: Scan subdirectories
        
    Returns:
        List of discovered files with type detection
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    discovered = []
    
    pattern = "**/*" if recursive else "*"
    
    for path in input_dir.glob(pattern):
        if not path.is_file():
            continue
        
        # Skip hidden files and system files
        if path.name.startswith('.'):
            continue
        
        # Detect type
        detected_type = detect_file_type(path)
        
        # Skip unknown types
        if detected_type == 'unknown':
            continue
        
        # Get file info
        size_bytes = path.stat().st_size
        
        # Compute hash
        sha256 = compute_file_hash(path)
        
        # Try to get MIME type (best effort)
        mime_type = 'application/octet-stream'
        try:
            import magic
            mime_type = magic.from_file(str(path), mime=True)
        except:
            pass
        
        discovered.append(DiscoveredFile(
            path=path,
            mime_type=mime_type,
            detected_type=detected_type,
            size_bytes=size_bytes,
            sha256=sha256,
        ))
    
    return discovered
