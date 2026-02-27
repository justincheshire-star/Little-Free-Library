# Contributing Guide

This is a detailed guide for contributors to the Little Free Library (LFL). For a quick overview, see [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Table of Contents

- [Repository Structure](#repository-structure)
- [Setting Up Locally](#setting-up-locally)
- [Adding a New Corpus](#adding-a-new-corpus)
- [Adding Chunks to an Existing Corpus](#adding-chunks-to-an-existing-corpus)
- [Chunk Frontmatter Reference](#chunk-frontmatter-reference)
- [Validating Your Contribution](#validating-your-contribution)
- [Running the Ingestion Script](#running-the-ingestion-script)
- [Submitting a Pull Request](#submitting-a-pull-request)

---

## Repository Structure

```
little-free-library/
├── corpora/                  # Corpus data (CC-BY-SA 4.0)
│   └── <domain>/
│       ├── CORPUS.md         # Corpus manifest
│       ├── sources.json      # Provenance tracking
│       └── chunks/           # Individual knowledge chunks
├── lfl/                      # Main package (Apache 2.0 + Commons Clause)
│   ├── cli.py                # CLI entry point (lfl command)
│   ├── chunking.py           # Document chunking (4 strategies)
│   ├── corpus_validation.py  # Corpus validation
│   ├── embeddings.py         # Vector embeddings
│   ├── retrieval.py          # Hybrid retrieval
│   └── ingest/               # Drop-folder ingestion pipeline
│       ├── detect.py         # MIME detection, SHA256 hashing
│       ├── convert.py        # LibreOffice conversion wrappers
│       ├── extract.py        # PDF/DOCX/XLSX/HTML/TXT extractors
│       └── pipeline.py       # 9-stage ingestion orchestration
├── ratings/                  # Community quality ratings
├── ingestion/                # Drop folder for raw documents (gitignored)
├── ingestion_out/            # Ingestion artifacts/manifests (gitignored)
├── scripts/                  # Tooling (Apache 2.0 + Commons Clause)
│   ├── check_forbidden_files.py  # Pre-commit file guard
│   ├── ingest.py
│   └── validate_corpus.py
├── .github/
│   └── workflows/
│       └── validate-files.yml  # CI: forbidden files + corpus validation
├── docs/                     # Documentation
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## Setting Up Locally

```bash
# Clone the repository
git clone https://github.com/justincheshire-star/Little-Free-Library.git
cd Little-Free-Library

# Download embedded models (~796 MB via Git LFS)
git lfs pull

# Install core dependencies (includes embedding libraries)
pip install -r requirements.txt

# Install in development mode with ingestion support
pip install -e ".[all_ingest,dev]"

# Optional: Test embedding models
python scripts/test_embeddings.py

# Verify CLI
lfl version
```

**Note:** Git LFS is required to download the embedded models. See the [Onboarding Guide](ONBOARDING.md#prerequisites) for Git LFS installation instructions.

---

## Adding a New Corpus

1. Create a new directory under `corpora/<domain>/`:
   ```bash
   mkdir -p corpora/<domain>/chunks
   ```
2. Copy and fill in the corpus manifest:
   ```bash
   cp corpora/programming/CORPUS.md corpora/<domain>/CORPUS.md
   ```
3. Create a `sources.json` based on the template in `corpora/programming/sources.json`.
4. Add chunk files (see [Adding Chunks](#adding-chunks-to-an-existing-corpus)).
5. Validate and submit a PR.

---

## Adding Chunks to an Existing Corpus

Each chunk is a Markdown file with YAML frontmatter. Place it under `corpora/<domain>/chunks/`.

### Naming Convention

Use descriptive, slug-style filenames:
```
corpora/programming/chunks/python-list-comprehension.md
corpora/programming/chunks/binary-search-algorithm.md
```

### File Format

```markdown
---
title: "Binary Search Algorithm"
domain: "programming"
subdomain: "algorithms"
source: "example-source-1"
source_license: "CC-BY-4.0"
verified: "2026-01-15"
importance: 0.85
tags: ["algorithms", "search", "binary-search", "complexity"]
version: "1.0.0"
---

Binary search is a search algorithm that finds the position of a target value
within a sorted array. It compares the target value to the middle element of
the array and eliminates half of the remaining search space on each iteration.

**Time complexity:** O(log n)  
**Space complexity:** O(1) iterative, O(log n) recursive
```

---

## Chunk Frontmatter Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Short descriptive title |
| `domain` | string | Yes | Top-level domain (matches corpus directory name) |
| `subdomain` | string | No | More specific area within the domain |
| `source` | string | Yes | Source ID from `sources.json` or full URL |
| `source_license` | string | Yes | SPDX license identifier of the original source |
| `verified` | string | Yes | ISO 8601 date of last human verification (YYYY-MM-DD) |
| `importance` | float | Yes | Relevance/quality weight, 0.0–1.0 |
| `tags` | list | Yes | Descriptive tags for retrieval and filtering |
| `version` | string | Yes | Corpus version string (e.g., `1.0.0`) |

---

## Validating Your Contribution

Before opening a PR, validate your corpus:

```bash
# Using the lfl CLI (recommended)
lfl validate corpora/<domain>

# Strict mode (fail on warnings)
lfl validate corpora/<domain> --strict
```

This checks YAML frontmatter, required metadata fields, sources.json schema, and cross-references between chunk source_ids and sources.json. Fix any reported errors before submitting.

---

## Using Drop-Folder Ingestion

The recommended way to add documents to a corpus is via `lfl ingest`:

```bash
# 1. Place documents in the ingestion drop folder
mkdir -p ingestion/<domain>
cp ~/Documents/*.pdf ingestion/<domain>/

# 2. Preview what would be ingested (dry-run)
lfl ingest <domain> --inventory

# 3. Run full ingestion
lfl ingest <domain>

# 4. With embeddings
lfl ingest <domain> --embed --profile baseline_cpu_onnx_small
```

**Supported formats:** PDF, DOCX, XLSX, HTML, TXT, Markdown. With LibreOffice: Pages, Numbers, Keynote, legacy Office.

**Install ingestion dependencies:** `pip install -e ".[all_ingest]"`

> **Never commit raw documents.** The CI workflow and pre-commit guard will block PDF, DOCX, and other binary formats. Always use `lfl ingest` to convert documents to chunks first.

---

## Running the HF Export Script

To generate a Hugging Face-compatible dataset from a corpus:

```bash
python scripts/ingest.py corpora/<domain>/chunks/ --output /tmp/dataset
```

This outputs a directory compatible with `datasets.load_from_disk()`.

**Published datasets:** Once reviewed and approved, completed datasets are published to the [LittleFreeLibrary Hugging Face organization](https://huggingface.co/LittleFreeLibrary) where they can be loaded with `load_dataset("LittleFreeLibrary/<corpus-name>")`.

---

## Submitting a Pull Request

1. Push your branch to your fork.
2. Open a PR against the `main` branch.
3. Fill in the PR template completely — incomplete templates will be returned.
4. A maintainer will review your corpus for quality and license compliance.

PRs that include AI-generated source material, missing provenance, or invalid frontmatter will be closed without merge.
