#!/usr/bin/env python3
"""
Pre-commit hook: block forbidden file types from being committed.

Prevents accidental commit of raw documents, binaries, and ingestion artifacts
into the repository. Approved binary paths (models/, corpora archives) are
allowlisted.

Usage as pre-commit hook:
    # .pre-commit-config.yaml
    - repo: local
      hooks:
        - id: check-forbidden-files
          name: Check forbidden files
          entry: python scripts/check_forbidden_files.py
          language: python
          stages: [commit]

    # Or manually: python scripts/check_forbidden_files.py [--staged | file1 file2 ...]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# ── Forbidden extensions ─────────────────────────────────────────────
# Raw document formats that should never be committed
FORBIDDEN_EXTENSIONS: set[str] = {
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".odt", ".ods", ".odp", ".rtf", ".epub",
    # Apple iWork
    ".pages", ".numbers", ".key",
    # Images (unless in approved paths)
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg", ".ico", ".webp",
    # Audio / Video
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv", ".flv", ".wmv",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".xz",
    # Databases
    ".db", ".sqlite", ".sqlite3",
    # Large model files (handled by LFS, but guard against accidental adds)
    ".onnx", ".safetensors", ".bin", ".pt", ".pth", ".h5", ".tflite",
    # Compiled / bytecode
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    # Notebooks (raw) — optional, uncomment if desired
    # ".ipynb",
}

# ── Allowlisted paths (prefixes) ────────────────────────────────────
# These paths MAY contain forbidden extensions (e.g., LFS-tracked models)
ALLOWED_PATH_PREFIXES: list[str] = [
    "models/",
    "corpora/",          # Corpus metadata (.json, .md) is fine — extensions guard the rest
    ".github/",
    "docs/",
    "scripts/",
]

# Override: allow these specific extensions in allowlisted paths
ALLOWED_IN_MODELS: set[str] = {
    ".onnx", ".safetensors", ".bin", ".pt", ".pth", ".h5", ".tflite",
}


def get_staged_files() -> list[str]:
    """Get list of files staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, check=True,
    )
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


def is_forbidden(filepath: str) -> bool:
    """Check if a file is forbidden from being committed."""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext not in FORBIDDEN_EXTENSIONS:
        return False

    # Check allowlisted paths
    for prefix in ALLOWED_PATH_PREFIXES:
        if filepath.startswith(prefix):
            # Models dir has special allowances for ML files
            if filepath.startswith("models/") and ext in ALLOWED_IN_MODELS:
                return False
            # Other allowed prefixes: only allow non-binary common files
            if ext in {".png", ".svg", ".ico"} and filepath.startswith("docs/"):
                return False
            # Default: still forbidden even in allowed paths
            # (e.g., don't commit .pdf into docs/)

    return True


def main() -> int:
    """
    Check staged files (or CLI arguments) for forbidden types.

    Returns:
        0 if clean, 1 if forbidden files found.
    """
    # If file arguments provided, check those; otherwise check staged files
    if len(sys.argv) > 1 and sys.argv[1] != "--staged":
        files = sys.argv[1:]
    else:
        try:
            files = get_staged_files()
        except subprocess.CalledProcessError:
            print("⚠️  Not in a git repository or git not available.", file=sys.stderr)
            return 0

    if not files:
        return 0

    violations: list[str] = []
    for filepath in files:
        if is_forbidden(filepath):
            violations.append(filepath)

    if violations:
        print("🚫 Forbidden files detected! These should not be committed:\n", file=sys.stderr)
        for v in sorted(violations):
            ext = Path(v).suffix
            print(f"   ✗ {v}  ({ext})", file=sys.stderr)
        print(
            "\n   If these are intentional (e.g., test fixtures), add them to\n"
            "   ALLOWED_PATH_PREFIXES in scripts/check_forbidden_files.py.\n"
            "\n   For documents, use the ingestion pipeline instead:\n"
            "     1. Drop files in ingestion/<domain>/\n"
            "     2. Run: lfl ingest <domain>\n"
            "     3. Commit only the generated chunks and metadata.\n",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
