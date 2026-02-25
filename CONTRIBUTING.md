# Contributing to Little Free Library

Thank you for contributing to the Little Free Library (LFL)! This document describes the standards and processes for contributing corpus data and tooling improvements.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Licensing](#licensing)
- [Corpus Quality Standards](#corpus-quality-standards)
- [Provenance Requirements](#provenance-requirements)
- [Chunk Frontmatter Standard](#chunk-frontmatter-standard)
- [Submitting a Corpus](#submitting-a-corpus)
- [Tooling Contributions](#tooling-contributions)

---

## Code of Conduct

Be respectful. Contributions that are abusive, plagiarized, or submitted in bad faith will be rejected and may result in a ban.

---

## Licensing

**Corpus data** (everything under `corpora/`) is licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0)**.

By contributing corpus data you agree that:
- Your contribution is either original work you own, or properly attributed material with a license compatible with CC-BY-SA 4.0.
- You have verified the original source license allows redistribution and derivative works under CC-BY-SA 4.0.

**Tooling and scripts** (everything under `scripts/`, `.github/`, etc.) are licensed under **Apache License 2.0 with Commons Clause**. See [LICENSE](LICENSE) for details.

---

## Corpus Quality Standards

All corpus chunks must meet the following quality bar before being accepted:

1. **Accuracy** — Content must be factually correct and verifiable against the cited source.
2. **Clarity** — Chunks should be self-contained and comprehensible in isolation where possible.
3. **Relevance** — Content must be relevant to the declared `domain` and `subdomain`.
4. **Chunking** — Each chunk file should represent a logically coherent unit (e.g., a single concept, function signature + description, or FAQ entry). Avoid splitting mid-sentence or mid-concept.
5. **Size** — Aim for chunks between 100 and 1000 tokens. Extremely short or extremely long chunks should be split or merged accordingly.
6. **No duplicates** — Do not submit content that already exists in the corpus.

### What Is NOT Accepted

- AI-generated source material. AI may only be used as a **transcription or description layer** for images/diagrams, and this must be clearly documented in the provenance metadata.
- Content behind a paywall or under a restrictive license that does not permit redistribution.
- Content that is not in English (unless the corpus explicitly targets another language).
- Personal opinions or editorialized content presented as fact.

---

## Provenance Requirements

Every corpus must include a `sources.json` file at its root that documents the provenance of all source material. Each entry must contain:

| Field | Description |
|---|---|
| `id` | A unique identifier for this source within the corpus |
| `url` | The canonical URL of the source |
| `title` | Human-readable title of the source |
| `original_license` | The SPDX identifier or name of the source's original license |
| `retrieval_date` | ISO 8601 date when the content was retrieved (YYYY-MM-DD) |
| `notes` | Any additional provenance notes (optional) |

---

## Chunk Frontmatter Standard

Every chunk file (`.md`) must begin with the following YAML frontmatter block:

```yaml
---
title: ""
domain: ""
subdomain: ""
source: ""
source_license: ""
verified: ""
importance: 0.0
tags: []
version: ""
---
```

| Field | Required | Description |
|---|---|---|
| `title` | Yes | Short descriptive title for this chunk |
| `domain` | Yes | Top-level domain (e.g., `programming`) |
| `subdomain` | No | More specific area (e.g., `python`, `algorithms`) |
| `source` | Yes | Source ID from `sources.json` or a full URL |
| `source_license` | Yes | SPDX identifier of the source's license |
| `verified` | Yes | ISO 8601 date of last human verification (YYYY-MM-DD) |
| `importance` | Yes | Float 0.0–1.0 indicating relevance/quality weight |
| `tags` | Yes | List of descriptive tags for retrieval |
| `version` | Yes | Corpus version string (e.g., `1.0.0`) |

---

## Submitting a Corpus

1. Fork the repository and create a new branch.
2. Create a new directory under `corpora/<domain>/` (or add to an existing one).
3. Add a `CORPUS.md` manifest describing the corpus.
4. Add a `sources.json` with full provenance for all sources.
5. Add chunk files under `corpora/<domain>/chunks/` with valid YAML frontmatter.
6. Run the validation script to ensure all chunks pass:
   ```bash
   python scripts/validate_corpus.py corpora/<domain>/chunks/
   ```
7. Open a Pull Request using the provided PR template.

---

## Tooling Contributions

Tooling contributions (scripts, CI workflows, etc.) should:
- Follow PEP 8 for Python code.
- Include docstrings for all public functions.
- Not introduce new dependencies without discussion in an issue first.
- Be covered by tests where practical.
