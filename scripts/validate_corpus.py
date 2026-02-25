#!/usr/bin/env python3
"""
validate_corpus.py — Validates corpus chunk files for required YAML frontmatter fields.

Licensed under the Apache License, Version 2.0 with Commons Clause.
See LICENSE for details.

Usage:
    python scripts/validate_corpus.py <chunks_directory>

Exit codes:
    0 — all chunks are valid
    1 — one or more chunks failed validation
"""

import sys
import os
import yaml

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


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a Markdown file.

    Returns the parsed frontmatter dict, or raises ValueError if the file
    does not start with a valid YAML frontmatter block.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

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


def validate_chunk(filepath):
    """Validate a single chunk file.

    Returns a list of error strings. An empty list means the chunk is valid.
    """
    errors = []

    try:
        frontmatter = parse_frontmatter(filepath)
    except ValueError as exc:
        return [str(exc)]

    for field in REQUIRED_FIELDS:
        if field not in frontmatter or frontmatter[field] is None or frontmatter[field] == "":
            errors.append(f"Missing or empty required field: '{field}'")
            continue

        expected_type = FIELD_TYPES.get(field)
        if expected_type and not isinstance(frontmatter[field], expected_type):
            errors.append(
                f"Field '{field}' has wrong type: expected {expected_type}, "
                f"got {type(frontmatter[field]).__name__}"
            )

    importance = frontmatter.get("importance")
    if isinstance(importance, (int, float)) and not (0.0 <= importance <= 1.0):
        errors.append(
            f"Field 'importance' must be between 0.0 and 1.0, got {importance}"
        )

    return errors


def validate_directory(chunks_dir):
    """Validate all .md files in a directory.

    Returns a dict mapping filenames to lists of errors.
    """
    if not os.path.isdir(chunks_dir):
        print(f"Error: '{chunks_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    results = {}
    for filename in sorted(os.listdir(chunks_dir)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(chunks_dir, filename)
        errors = validate_chunk(filepath)
        if errors:
            results[filename] = errors

    return results


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <chunks_directory>", file=sys.stderr)
        sys.exit(1)

    chunks_dir = sys.argv[1]
    failures = validate_directory(chunks_dir)

    if not failures:
        md_files = [f for f in os.listdir(chunks_dir) if f.endswith(".md")]
        print(f"All {len(md_files)} chunk(s) passed validation.")
        sys.exit(0)
    else:
        for filename, errors in failures.items():
            print(f"\n{filename}:")
            for error in errors:
                print(f"  - {error}")
        total = sum(len(e) for e in failures.values())
        print(f"\n{len(failures)} file(s) failed with {total} error(s) total.")
        sys.exit(1)


if __name__ == "__main__":
    main()
