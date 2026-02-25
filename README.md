# 📚 Little Free Library

> *Take what you need. Leave what you can.*

A community-maintained, open collection of LLM-ready knowledge bases for use in agentic systems, RAG pipelines, and AI-assisted development. Free to use. Free to contribute. No walls, no gates, no paywalls.

---

## What Is This?

Little Free Library is two things at once:

- **A library** — like the little wooden boxes in front yards where neighbors share books freely
- **A knowledge library** — curated, domain-specific corpora ready to drop into any RAG pipeline

The goal is simple: vetted, high-quality knowledge bases that any developer — well-funded or not — can use to build better agentic systems.

---

## The Library

Corpora are organized by domain. Each is pre-chunked, pre-embedded, and ready to ingest.

| Domain | Status | Version | License |
|--------|--------|---------|---------|
| Programming | ✅ Stable | v1.0.0 | CC-BY-SA 4.0 |
| Web Development | 🚧 In Progress | v0.2.0 | CC-BY-SA 4.0 |
| Business | 🗂️ Planned | — | CC-BY-SA 4.0 |
| Art History | 🗂️ Planned | — | CC-BY-SA 4.0 |
| Mathematics | 🗂️ Planned | — | CC-BY-SA 4.0 |

> Corpora are published under a tiered model based on source licensing. See the [Licensing Guide](docs/licensing-guide.md) for details.
>
> | Tier | Description |
> |------|-------------|
> | **Tier 1 — Redistributable** | Source allows redistribution. Chunks + embeddings published openly under CC-BY-SA 4.0. |
> | **Tier 2 — Recipe Only** | Source restricts redistribution. Manifests, scrapers, and chunking rules published. You build locally. |
> | **Tier 3 — Reference Only** | Pointers and guidance only. No automation or redistribution. |

---

## Quick Start

### Using a Corpus with pxctx

```bash
# Clone the library
git clone https://github.com/little-free-library/lfl

# Ingest a corpus into your local pxctx instance
python -m pxctx ingest lfl/corpora/programming \
  --recursive \
  --pattern "*.md" \
  --tier long_lived \
  --tags kb,programming \
  --on-duplicate update
```

### Using a Corpus Without pxctx

Every corpus is plain markdown with a standardized metadata header. Drop it into any RAG pipeline — LlamaIndex, LangChain, or your own system.

```bash
# Pull just the corpus you need from Hugging Face
from datasets import load_dataset
ds = load_dataset("little-free-library/programming")
```

---

## Corpus Structure

Each corpus follows a standard schema so any RAG framework can consume it with minimal configuration.

```
corpora/
└── programming/
    ├── CORPUS.md           # Corpus manifest (domain, version, sources, license)
    ├── sources.json        # Provenance — where content came from, original licenses
    ├── chunks/             # Pre-chunked content
    │   ├── chunk_001.md
    │   └── ...
    └── embeddings/         # Optional pre-computed embeddings (nomic-embed-text-v1.5)
        └── vectors.npy
```

### Metadata Header (per chunk)

```yaml
---
title: "Python Exception Handling"
domain: programming
subdomain: python
source: https://docs.python.org/3/tutorial/errors.html
source_license: PSF-2.0
source_id: python_docs
source_path: tutorial/errors.md
retrieved_at: 2026-02-24
verified: documented
importance: 0.8
tags: [python, exceptions, error-handling]
version: 1.0.0
content_hash: sha256:4b3a2f...
---
```

---

## The Reference Engine

Little Free Library is designed to work out of the box with **[pxctx](https://github.com/little-free-library/pxctx)** — a 3-tier hybrid RAG engine with vector + full-text search, deterministic reranking, and a built-in local embedding model.

You don't have to use pxctx. Any RAG system works. But pxctx is what the corpora are built and validated against.

---

## Contributing a Corpus

The library grows because people add to it. If you have expertise in a domain and want to contribute:

1. Fork this repo
2. Create a new directory under `corpora/your-domain/`
3. Follow the corpus structure above
4. Populate `CORPUS.md` and `sources.json` with provenance
5. Open a PR — community review will validate quality before merge

**Before contributing, check that your sources are compatible with the tier system.** See `docs/licensing-guide.md` for a breakdown of common source licenses, tier assignment, and attribution requirements.

LFL never relicenses third-party content. Every corpus packages content with its original license terms, attribution, and provenance intact. The compliance gate in CI will reject any source with an ambiguous or missing license.

### Quality Standards

- Sources must be authoritative (official docs, peer-reviewed work, established references)
- No AI-generated content as source material — corpora must originate from authoritative human sources. AI may be used as a transcription or description layer (e.g. converting diagrams or images to text) provided the underlying source remains authoritative and is documented in provenance metadata
- Every chunk must have complete provenance metadata including `content_hash: sha256:...` for idempotency
- Every source must have an explicit `sources/<source_id>.json` with license, redistribution tier, and attribution fields — CI will hard-fail on missing or ambiguous entries
- Chunks should be self-contained and meaningful out of context

---

## Community Ratings

Every corpus and chunk can be rated by the community. Ratings live in `ratings/` as plain JSON so they're transparent, auditable, and not locked into any platform.

```json
{
  "corpus": "programming",
  "chunk": "chunk_042",
  "rating": 4.7,
  "votes": 23,
  "flags": [],
  "last_updated": "2026-02-24"
}
```

Low-rated or flagged chunks are reviewed and pruned in each version release.

---

## Put This Knowledge to Work

Little Free Library corpora are format-agnostic and framework-agnostic. Use them with whatever you're building:

- Any RAG pipeline — LlamaIndex, LangChain, or your own
- Local hybrid retrieval with **[pxctx](https://github.com/little-free-library/pxctx)**
- Hugging Face dataset pipelines
- Custom agentic systems, IDE agents, or local tooling

The knowledge belongs to you. Use it however you see fit.

> 🪟 Building on Windows? **[LocalAgent Studio](https://github.com/little-free-library/localagent-studio)** — coming soon to the Windows App Store — is a native multi-agent environment built to work with LFL out of the box.

---

## Philosophy

Most knowledge resources for AI are either paywalled, buried inside commercial products, or require expensive API keys just to access. Little Free Library exists because good knowledge should be a commons — maintained by the community, available to everyone, and not extractable for private profit.

This is not a startup. There is no Series A. The only goal is a growing, well-maintained collection of knowledge that makes everyone's agentic systems better.

*Take what you need. Leave what you can.*

---

## License

| Component | License |
|-----------|---------|
| Tier 1 Corpora (redistributable data) | [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Tier 2 Recipes (manifests + scripts) | [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) + [Commons Clause](https://commonsclause.com/) |
| Tooling & CLI | [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) + [Commons Clause](https://commonsclause.com/) |

LFL never relicenses third-party content. Each source retains its original license terms. Per-source license metadata is captured in `sources/<source_id>.json` and propagated into every chunk's frontmatter.

The Commons Clause means you are free to use, modify, and build with this project. You may not sell it or offer it as a paid service without permission.

---

## Acknowledgments

Inspired by the [Little Free Library](https://littlefreelibrary.org/) movement — neighbors sharing books freely, one box at a time.

---

*Little Free Library — knowledge for everyone.*
