# Corpus Manifest — Programming

## Metadata

| Field | Value |
|---|---|
| **Domain** | `programming` |
| **Version** | `1.0.0` |
| **Status** | `draft` |
| **License (corpus data)** | CC-BY-SA 4.0 |
| **Maintainer** | Little Free Library Contributors |
| **Last Updated** | <!-- YYYY-MM-DD --> |

---

## Description

The `programming` corpus covers foundational and advanced programming concepts, language references, algorithmic patterns, and software engineering best practices. It is intended for use in LLM-powered coding assistants, RAG pipelines, and agentic development tools.

---

## Subdomains

| Subdomain | Description |
|---|---|
| `general` | Language-agnostic programming concepts |
| `python` | Python language reference and idioms |
| `javascript` | JavaScript / TypeScript reference |
| `algorithms` | Algorithm descriptions and complexity analysis |
| `data-structures` | Data structure descriptions and usage patterns |
| `design-patterns` | Software design patterns |

*(Extend this table as new subdomains are added.)*

---

## Sources

See [`sources.json`](sources.json) for full provenance details.

---

## Chunk Frontmatter Fields Used

Every chunk file in this corpus uses the following YAML frontmatter:

```yaml
---
title: ""
domain: "programming"
subdomain: ""
source: ""
source_license: ""
verified: ""
importance: 0.0
tags: []
version: "1.0.0"
---
```

---

## Validation

Run the corpus validator before submitting changes:

```bash
python scripts/validate_corpus.py corpora/programming/chunks/
```

---

## Notes

- No AI-generated source material is permitted. AI may only be used as a transcription or description layer for images/diagrams, documented in provenance metadata.
- All content must be verifiable against the cited source.
