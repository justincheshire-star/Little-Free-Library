---
type: architecture
tags: [corpus, schema, chunks, frontmatter]
sources: [CORPUS.md, sources.json]
created: 2026-02-25
updated: 2026-02-25
never_expire: true
tier: long-lived
---

# Corpus Architecture

## Overview

Little Free Library stores educational text corpora as Markdown chunks under `corpora/<domain>/chunks/`.
Each corpus domain has a `CORPUS.md` (format spec) and a `sources.json` (provenance registry).

## Chunk Format

Each chunk is a `.md` file with YAML front-matter:

```yaml
---
source: <source-id or URL>
license: CC-BY-SA-4.0
chunk_id: <domain>-<index>
---
```

Body is plain Markdown prose.

## Source Registry (`sources.json`)

Each entry must include: `id`, `url`, `title`, `original_license`, `retrieval_date`.
The `source` field in chunk front-matter must match an `id` in `sources.json` (or be a full URL).

## Tooling

- `scripts/ingest.py` — adds new chunks / sources to a corpus domain.
- `scripts/validate_corpus.py` — validates chunk front-matter and source registry consistency.

## Constraints

- No AI-generated text as primary source material.
- All sources must be licensed compatible with CC-BY-SA 4.0.
- Chunks should be semantically coherent and not split mid-concept where avoidable.
