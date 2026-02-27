# Corpus Manifest — Programming

## Metadata

| Field | Value |
|---|---|
| **Domain** | `programming` |
| **Version** | `1.0.0` |
| **Status** | `stable` |
| **License (corpus data)** | CC-BY-SA 4.0 |
| **Maintainer** | Little Free Library Contributors |
| **Last Updated** | 2026-02-27 |

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

## Statistics

| Metric | Value |
|---|---|
| **Sources** | 22 |
| **Chunks** | 594 |
| **Embeddings** | 594 vectors (384-dim, float32) |
| **Embedding Profile** | `baseline_cpu_onnx_small` (bge-small-en-v1.5) |

---

## Sources

See [`sources.json`](sources.json) for full provenance details.

---

## Access

Once ingestion is complete, the processed dataset will be available at:  
**[https://huggingface.co/LittleFreeLibrary/programming](https://huggingface.co/LittleFreeLibrary/programming)**

```python
from datasets import load_dataset
ds = load_dataset("LittleFreeLibrary/programming")
```

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

# Or using the lfl CLI
lfl validate corpora/programming
```

Validation errors are reported with structured [LFL error codes](../../docs/ERROR_CODES.md) (e.g., `[LFL-K300]` for missing frontmatter).

---

## Notes

- No AI-generated source material is permitted. AI may only be used as a transcription or description layer for images/diagrams, documented in provenance metadata.
- All content must be verifiable against the cited source.
