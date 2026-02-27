"""
lfl.corpus_validation — Corpus metadata and structure validation.

Validates corpus directories for:
- YAML frontmatter completeness
- Required metadata fields
- Field type correctness
- sources.json validity
- Source ID consistency
- Orphaned sources detection

Error codes: LFL-K3xx (chunk/frontmatter), LFL-V4xx (validation/sources).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
import yaml

from lfl.ingest.errors import (
    K300_no_frontmatter,
    K301_frontmatter_parse_error,
    K302_missing_required_field,
    K303_wrong_field_type,
    K304_importance_out_of_range,
    IngestionError,
)


REQUIRED_FIELDS = [
    "title",
    "domain",
    "source",
    "source_license",
    "verified",
    "importance",
    "tags",
    "version",
]

FIELD_TYPES = {
    "title": str,
    "domain": str,
    "source": str,
    "source_license": str,
    "verified": str,
    "importance": (int, float),
    "tags": list,
    "version": str,
}


def parse_frontmatter(filepath: Path) -> dict:
    """
    Parse YAML frontmatter from a Markdown file.
    
    Returns the parsed frontmatter dict, or raises ValueError if the file
    does not start with a valid YAML frontmatter block.
    """
    content = filepath.read_text(encoding="utf-8")
    
    if not content.startswith("---"):
        raise ValueError("File does not begin with YAML frontmatter ('---')")
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Could not find closing '---' for frontmatter block")
    
    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter: {exc}") from exc
    
    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter did not parse as a YAML mapping")
    
    return frontmatter


def validate_chunk(filepath: Path) -> list[str]:
    """
    Validate a single chunk file.
    
    Returns a list of error strings. An empty list means the chunk is valid.
    Each error string is prefixed with the error code for easy lookup.
    """
    errors = []
    
    try:
        frontmatter = parse_frontmatter(filepath)
    except ValueError as exc:
        exc_str = str(exc)
        # Map to specific error codes
        if "does not begin with YAML" in exc_str:
            ie = K300_no_frontmatter(str(filepath))
        elif "Invalid YAML" in exc_str or "Could not find closing" in exc_str:
            ie = K301_frontmatter_parse_error(str(filepath), exc_str)
        else:
            ie = K301_frontmatter_parse_error(str(filepath), exc_str)
        return [f"[{ie.code}] {exc_str}"]
    
    for field in REQUIRED_FIELDS:
        if field not in frontmatter or frontmatter[field] is None or frontmatter[field] == "":
            ie = K302_missing_required_field(str(filepath), field)
            errors.append(f"[{ie.code}] Missing or empty required field: '{field}'")
            continue
        
        expected_type = FIELD_TYPES.get(field)
        if expected_type and not isinstance(frontmatter[field], expected_type):
            ie = K303_wrong_field_type(
                str(filepath), field,
                str(expected_type), type(frontmatter[field]).__name__,
            )
            errors.append(
                f"[{ie.code}] Field '{field}' has wrong type: expected {expected_type}, "
                f"got {type(frontmatter[field]).__name__}"
            )
    
    importance = frontmatter.get("importance")
    if isinstance(importance, (int, float)) and not (0.0 <= importance <= 1.0):
        ie = K304_importance_out_of_range(str(filepath), importance)
        errors.append(
            f"[{ie.code}] Field 'importance' must be between 0.0 and 1.0, got {importance}"
        )
    
    return errors


def load_sources_json(corpus_dir: Path) -> dict | None:
    """
    Load and parse sources.json from corpus directory.
    
    Returns None if file doesn't exist, or the parsed dict if valid.
    Raises ValueError if file exists but is invalid JSON.
    """
    sources_file = corpus_dir / "sources.json"
    
    if not sources_file.exists():
        return None
    
    try:
        return json.loads(sources_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in sources.json: {e}")


def validate_sources_json(sources_data: dict) -> list[str]:
    """
    Validate sources.json structure and required fields.
    
    Returns list of error strings (empty if valid).
    """
    errors = []
    
    if not isinstance(sources_data, dict):
        return ["sources.json must be a JSON object"]
    
    if "sources" not in sources_data:
        return ["sources.json missing 'sources' key"]
    
    sources = sources_data["sources"]
    if not isinstance(sources, list):
        errors.append("'sources' must be an array")
        return errors
    
    required_source_fields = ["id", "name", "license", "url"]
    
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"Source #{i} is not an object")
            continue
        
        # Check required fields
        for field in required_source_fields:
            if field not in source or not source[field]:
                errors.append(f"Source #{i} (id={source.get('id', 'unknown')}): missing required field '{field}'")
        
        # Validate ID format (no spaces, reasonable length)
        source_id = source.get("id", "")
        if source_id:
            if " " in source_id:
                errors.append(f"Source '{source_id}': ID cannot contain spaces")
            if len(source_id) > 100:
                errors.append(f"Source '{source_id}': ID too long (max 100 chars)")
    
    # Check for duplicate IDs
    source_ids = [s.get("id") for s in sources if s.get("id")]
    if len(source_ids) != len(set(source_ids)):
        duplicates = [sid for sid in source_ids if source_ids.count(sid) > 1]
        errors.append(f"Duplicate source IDs found: {set(duplicates)}")
    
    return errors


def check_source_references(
    chunks_dir: Path,
    valid_source_ids: set[str],
) -> tuple[list[str], set[str]]:
    """
    Check that all chunk source_id values reference valid sources.
    
    Returns (errors, orphaned_source_ids).
    """
    errors = []
    referenced_ids = set()
    
    for filepath in sorted(chunks_dir.glob("*.md")):
        try:
            frontmatter = parse_frontmatter(filepath)
            source_id = frontmatter.get("source_id", "")
            
            if source_id:
                referenced_ids.add(source_id)
                
                if source_id not in valid_source_ids:
                    errors.append(
                        f"{filepath.name}: references unknown source_id '{source_id}'"
                    )
        except ValueError:
            # Already reported by chunk validation
            pass
    
    # Find orphaned sources (defined but never referenced)
    orphaned = valid_source_ids - referenced_ids
    
    return errors, orphaned


def validate_corpus(
    corpus_dir: Path,
    strict: bool = False,
    check_sources: bool = True,
) -> tuple[int, int, list[tuple[Path, list[str]]], list[str], set[str]]:
    """
    Validate all chunks in a corpus directory.
    
    Parameters
    ----------
    corpus_dir : Path
        Path to corpus directory (should contain chunks/ subdirectory)
    strict : bool
        If True, treat warnings as errors
    check_sources : bool
        If True, validate sources.json and check references
    
    Returns
    -------
    tuple[int, int, list, list, set]
        (valid_count, invalid_count, errors_by_file, source_errors, orphaned_sources)
    """
    chunks_dir = corpus_dir / "chunks"
    
    if not chunks_dir.exists():
        raise FileNotFoundError(f"No chunks/ directory found in {corpus_dir}")
    
    chunk_files = sorted(chunks_dir.glob("*.md"))
    
    if not chunk_files:
        raise ValueError(f"No .md files found in {chunks_dir}")
    
    valid_count = 0
    invalid_count = 0
    errors_by_file: list[tuple[Path, list[str]]] = []
    source_errors: list[str] = []
    orphaned_sources: set[str] = set()
    
    # Validate chunks
    for filepath in chunk_files:
        errors = validate_chunk(filepath)
        if errors:
            invalid_count += 1
            errors_by_file.append((filepath, errors))
        else:
            valid_count += 1
    
    # Validate sources.json if requested
    if check_sources:
        try:
            sources_data = load_sources_json(corpus_dir)
            
            if sources_data is None:
                source_errors.append("sources.json not found (recommended for provenance tracking)")
            else:
                # Validate sources.json structure
                src_errors = validate_sources_json(sources_data)
                source_errors.extend(src_errors)
                
                # Check source references if sources.json is valid
                if not src_errors:
                    valid_source_ids = {
                        s["id"] for s in sources_data.get("sources", [])
                        if isinstance(s, dict) and "id" in s
                    }
                    
                    ref_errors, orphaned = check_source_references(
                        chunks_dir, valid_source_ids
                    )
                    source_errors.extend(ref_errors)
                    orphaned_sources = orphaned
        
        except ValueError as e:
            source_errors.append(str(e))
    
    return valid_count, invalid_count, errors_by_file, source_errors, orphaned_sources


def format_validation_report(
    corpus_dir: Path,
    valid_count: int,
    invalid_count: int,
    errors_by_file: list[tuple[Path, list[str]]],
    source_errors: list[str],
    orphaned_sources: set[str],
    strict: bool = False,
) -> str:
    """Format validation results as a human-readable report."""
    lines = [
        "",
        "=" * 60,
        f"  Corpus Validation: {corpus_dir.name}",
        "=" * 60,
        f"  Valid chunks    : {valid_count}",
        f"  Invalid chunks  : {invalid_count}",
        f"  Total chunks    : {valid_count + invalid_count}",
    ]
    
    # Chunk errors
    if errors_by_file:
        lines.append("")
        lines.append("  Chunk Errors:")
        lines.append("-" * 60)
        for filepath, errors in errors_by_file:
            lines.append(f"  {filepath.name}:")
            for error in errors:
                lines.append(f"    • {error}")
            lines.append("")
    
    # Source errors
    if source_errors:
        lines.append("")
        lines.append("  Source Provenance Issues:")
        lines.append("-" * 60)
        for error in source_errors:
            if error.startswith("sources.json not found"):
                lines.append(f"  ⚠️  {error}")
            else:
                lines.append(f"  ❌ {error}")
        lines.append("")
    
    # Orphaned sources
    if orphaned_sources:
        lines.append("")
        lines.append("  Orphaned Sources (defined but not referenced):")
        lines.append("-" * 60)
        for source_id in sorted(orphaned_sources):
            lines.append(f"  ⚠️  {source_id}")
        lines.append("")
    
    lines.append("=" * 60)
    
    total_errors = invalid_count + len([e for e in source_errors if not e.startswith("sources.json not found")])
    total_warnings = len([e for e in source_errors if e.startswith("sources.json not found")]) + len(orphaned_sources)
    
    if total_errors == 0 and total_warnings == 0:
        lines.append("  ✅ All checks passed")
    elif total_errors == 0:
        lines.append(f"  ✅ No errors, {total_warnings} warning(s)")
    else:
        lines.append(f"  ❌ {total_errors} error(s), {total_warnings} warning(s)")
    
    lines.append("=" * 60)
    lines.append("")
    
    return "\n".join(lines)
