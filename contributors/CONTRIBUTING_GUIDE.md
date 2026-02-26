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
├── ratings/                  # Community quality ratings
├── docs/                     # Documentation
├── scripts/                  # Tooling (Apache 2.0 + Commons Clause)
│   ├── ingest.py
│   └── validate_corpus.py
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md
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

# Install dependencies (includes embedding libraries)
pip install -r requirements.txt

# Optional: Test embedding models
python scripts/test_embeddings.py
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

Before opening a PR, run the validation script:

```bash
python scripts/validate_corpus.py corpora/<domain>/chunks/
```

This will check that all chunk files have the required frontmatter fields and valid values. Fix any reported errors before submitting.

---

## Running the Ingestion Script

To generate a Hugging Face-compatible dataset from a corpus:

```bash
python scripts/ingest.py corpora/<domain>/chunks/ --output /tmp/dataset
```

This outputs a directory compatible with `datasets.load_from_disk()`.

---

## Submitting a Pull Request

1. Push your branch to your fork.
2. Open a PR against the `main` branch.
3. Fill in the PR template completely — incomplete templates will be returned.
4. A maintainer will review your corpus for quality and license compliance.

PRs that include AI-generated source material, missing provenance, or invalid frontmatter will be closed without merge.
