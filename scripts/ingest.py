#!/usr/bin/env python3
"""
ingest.py — Reads markdown chunks from a corpus directory and outputs a
Hugging Face compatible dataset format.

Licensed under the Apache License, Version 2.0 with Commons Clause.
See LICENSE for details.

Usage:
    python scripts/ingest.py <chunks_directory> [--output <output_path>]

The output directory can be loaded with:
    from datasets import load_from_disk
    dataset = load_from_disk("<output_path>")
"""

import argparse
import os
import sys

import yaml


def parse_frontmatter(filepath):
    """Parse YAML frontmatter and body from a Markdown file.

    Returns a tuple of (frontmatter_dict, body_text).
    Raises ValueError if the file does not contain valid frontmatter.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        raise ValueError(f"{filepath}: does not begin with YAML frontmatter ('---')")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{filepath}: could not find closing '---' for frontmatter block")

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{filepath}: invalid YAML frontmatter: {exc}") from exc

    body = parts[2].strip()
    return frontmatter, body


def load_chunks(chunks_dir):
    """Load all chunk files from a directory.

    Returns a list of dicts, each containing frontmatter fields plus 'text'
    (the chunk body) and 'filename'.
    """
    records = []
    if not os.path.isdir(chunks_dir):
        print(f"Error: '{chunks_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    for filename in sorted(os.listdir(chunks_dir)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(chunks_dir, filename)
        try:
            frontmatter, body = parse_frontmatter(filepath)
        except ValueError as exc:
            print(f"Warning: skipping {filename}: {exc}", file=sys.stderr)
            continue

        record = {
            "filename": filename,
            "text": body,
            "title": frontmatter.get("title", ""),
            "domain": frontmatter.get("domain", ""),
            "subdomain": frontmatter.get("subdomain", ""),
            "source": frontmatter.get("source", ""),
            "source_license": frontmatter.get("source_license", ""),
            "verified": frontmatter.get("verified", ""),
            "importance": float(frontmatter.get("importance", 0.0)),
            "tags": frontmatter.get("tags") or [],
            "version": frontmatter.get("version", ""),
        }
        records.append(record)

    return records


def save_dataset(records, output_path):
    """Save records as a Hugging Face dataset to output_path."""
    try:
        from datasets import Dataset
    except ImportError:
        print(
            "Error: the 'datasets' library is required. Install it with:\n"
            "  pip install datasets",
            file=sys.stderr,
        )
        sys.exit(1)

    if not records:
        print("Warning: no valid chunk records found; nothing to save.", file=sys.stderr)
        return

    dataset = Dataset.from_list(records)
    dataset.save_to_disk(output_path)
    print(f"Saved {len(records)} record(s) to '{output_path}'.")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest corpus chunks into a Hugging Face dataset format."
    )
    parser.add_argument("chunks_dir", help="Path to the corpus chunks directory")
    parser.add_argument(
        "--output",
        default="./lfl_dataset",
        help="Output path for the Hugging Face dataset (default: ./lfl_dataset)",
    )
    args = parser.parse_args()

    records = load_chunks(args.chunks_dir)
    print(f"Loaded {len(records)} chunk(s) from '{args.chunks_dir}'.")
    save_dataset(records, args.output)


if __name__ == "__main__":
    main()
