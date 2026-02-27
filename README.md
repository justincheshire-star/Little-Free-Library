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
ds = load_dataset("LittleFreeLibrary/programming")
```

**Completed datasets are available at:** [https://huggingface.co/LittleFreeLibrary](https://huggingface.co/LittleFreeLibrary)

### Creating Your Own Corpus (Drop-Folder Ingestion)

Want to build a custom corpus from your own documents? The `lfl` toolkit includes **drop-folder ingestion** for common document formats:

```bash
# 1. Install with ingestion support
pip install "lfl[all_ingest]"

# 2. Create a drop folder and add documents
mkdir -p ingestion/my_domain
cp ~/Documents/*.pdf ingestion/my_domain/
cp ~/Documents/*.docx ingestion/my_domain/

# 3. Run ingestion (converts → extracts → chunks → validates)
lfl ingest my_domain --embed --profile baseline_cpu_onnx_small

# 4. Your corpus is ready!
ls corpora/my_domain/chunks/
```

**Supported formats:** PDF, DOCX, XLSX, HTML, TXT, and with LibreOffice installed: Pages, Numbers, Keynote, legacy Office formats.

See [docs/KB/INGESTION_SYSTEM_SPEC.md](docs/KB/INGESTION_SYSTEM_SPEC.md) for complete ingestion documentation.

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

## The Toolkit

Little Free Library includes a comprehensive validation and benchmarking toolkit (`lfl`) to ensure corpus quality and optimize retrieval performance. The toolkit provides **document ingestion**, document chunking, corpus validation, hybrid retrieval testing, and benchmarking.

### Installation

```bash
# Minimal installation (core toolkit only)
pip install lfl

# With document ingestion support (PDF, DOCX, XLSX, HTML, etc.)
pip install "lfl[all_ingest]"

# With embeddings + ingestion (full-featured)
pip install "lfl[all_ingest]" fastembed sentence-transformers einops

# Development installation
git clone https://github.com/justincheshire-star/Little-Free-Library.git
cd Little-Free-Library
pip install -e ".[all_ingest,dev]"
```

**Optional extras:**
- `[ingest]` — Common document formats (DOCX, XLSX, HTML)
- `[pdf]` — PDF text extraction  
- `[ocr]` — OCR support for scanned documents
- `[all_ingest]` — All ingestion features

# Download embedded models (~796 MB via Git LFS)
git lfs pull
```

**Embedding Models Included:**
- ✅ **FastEmbed ONNX** - Cross-platform, no PyTorch (~273 MB)
  - `bge-small-en-v1.5` (384-dim) - Fast baseline
  - `bge-base-en-v1.5` (768-dim) - Better quality
- ✅ **Sentence-Transformers PyTorch** - Full-featured, GPU-optimized (~523 MB)
  - `nomic-embed-text-v1.5` (768-dim) - Apache 2.0 licensed

See **[Embedding Setup Guide](docs/EMBEDDING_SETUP.md)** for usage details and comparison.

### CLI Commands

#### `lfl ingest` — Drop-Folder Ingestion (NEW)

Automatically convert, extract, chunk, and validate documents from common formats:

```bash
# Basic ingestion
lfl ingest programming

# With embeddings
lfl ingest programming --embed --profile baseline_cpu_onnx_small

# Custom paths
lfl ingest business --input /tmp/docs --corpus-dir /tmp/corpus

# Dry-run (show what would be ingested)
lfl ingest programming --inventory
```

**What it does:**
1. Scans `ingestion/<domain>/` for documents
2. Converts formats if needed (Pages → PDF, Numbers → XLSX via LibreOffice)
3. Extracts text and tables (with OCR fallback for scanned PDFs)
4. Chunks documents using your preferred strategy
5. Generates metadata with safe defaults (`source_license: unknown`)
6. Validates corpus structure
7. Optionally generates embeddings
8. Writes manifest to `ingestion_out/<domain>/manifest.json`

**Supported formats:** PDF, DOCX, XLSX, HTML, TXT, MD, and with LibreOffice: Pages, Numbers, Keynote, legacy Office.

**System prerequisites:**
```bash
# macOS
brew install libreoffice tesseract

# Ubuntu/Debian
sudo apt install libreoffice tesseract-ocr
```

**Install dependencies:** `pip install "lfl[all_ingest]"`

#### `lfl chunk` — Convert Documents to Corpus Chunks

Transform raw documents into corpus-ready markdown chunks with complete metadata:

```bash
# Basic chunking with heading-aware strategy
lfl chunk document.md corpora/programming/chunks/

# Specify chunking strategy and chunk size
lfl chunk document.md output/ --strategy heading_aware --chunk-size 600

# Sliding window with overlap
lfl chunk document.md output/ --strategy sliding_window --chunk-size 500 --overlap 50

# All available strategies
lfl chunk document.md output/ --strategy naive_paragraph  # Split on paragraphs
lfl chunk document.md output/ --strategy heading_aware    # Split at headings (default)
lfl chunk document.md output/ --strategy sliding_window   # Fixed windows with overlap
lfl chunk document.md output/ --strategy semantic         # Semantic boundaries (experimental)
```

**Chunking strategies:**
- `naive_paragraph` — Split on double newlines, pack to target size
- `heading_aware` — Split at markdown headings, preserve document structure (default)
- `sliding_window` — Fixed-size windows with configurable overlap
- `semantic` — Semantic boundary detection (currently falls back to heading_aware)

**Generated metadata includes:**
- Title (auto-extracted or from frontmatter)
- Domain, subdomain, source URL
- License, source_id, timestamp
- Importance score (0.0-1.0)
- Tags array
- Content hash (SHA256 for idempotency)
- Token count (chunk_tokens field)

#### `lfl validate` — Validate Corpus Structure

Comprehensive validation of corpus structure, metadata, and provenance:

```bash
# Validate a corpus
lfl validate corpora/programming

# Strict mode (fail on warnings)
lfl validate corpora/programming --strict
```

**Validation checks:**
- YAML frontmatter completeness
- Required metadata fields (title, domain, source, license, etc.)
- sources.json schema validation
- Cross-reference chunk source_ids with sources.json
- Detect orphaned sources (defined but never referenced)
- License compliance
- Content hash integrity

**Output example:**
```
✓ Validated 156 chunks
✓ 156 valid, 0 invalid
✓ sources.json: 8 sources defined
⚠ 2 sources never referenced by any chunk (orphaned):
  - deprecated_guide
  - old_tutorial_v1
```

#### `lfl benchmark` — Test Retrieval Quality

Automatically generate synthetic queries and measure retrieval quality:

```bash
# Run a single benchmark
lfl benchmark run corpora/programming

# Test multiple parameter configurations (sweep)
lfl benchmark sweep corpora/programming

# Compare all saved benchmark reports
lfl benchmark compare corpora/programming
```

**The benchmarking system:**
- Generates synthetic queries automatically (no human annotation needed)
- Tests BM25 lexical retrieval as quality baseline
- Optionally tests vector and hybrid retrieval modes
- Measures recall@k, MRR (Mean Reciprocal Rank), and token efficiency
- Recommends optimal chunking parameters
- Tracks quality over time with versioned reports
- Saves reports to `corpus_dir/reports/YYYY-MM-DD_HH-MM-SS.json`

**Supported retrieval modes:**
- `bm25` — Lexical retrieval (always available, no dependencies)
- `vector` — Semantic vector search (requires fastembed/sentence-transformers)
- `hybrid` — Combines BM25 + vector with Reciprocal Rank Fusion (RRF)

#### `lfl version` — Show Toolkit Version

```bash
lfl version
```

### Embedding Profiles

The toolkit includes 5 official embedding profiles for reproducible corpus ingestion:

| Profile | Model | Dimensions | Hardware | Purpose |
|---------|-------|------------|----------|---------|
| `baseline_cpu_onnx_small` | nomic-embed-text-v1.5 | 384 | Any CPU | Default, fast, good quality |
| `quality_cpu_onnx_base` | BAAI/bge-base-en-v1.5 | 768 | Any CPU | Higher quality, slower |
| `power_user_cuda` | BAAI/bge-large-en-v1.5 | 1024 | NVIDIA GPU | Best quality, requires CUDA |
| `power_user_rocm` | BAAI/bge-large-en-v1.5 | 1024 | AMD GPU | Best quality, requires ROCm |
| `windows_gpu_directml` | BAAI/bge-base-en-v1.5 | 768 | Windows GPU | DirectML support |

**Same profile + same corpus = same vectors (reproducible builds).**

Profiles are stored in `lfl/profiles/*.json` and loaded automatically by the embeddings module.

### Quick Start Workflow

```bash
# 1. Create chunks from raw documents
lfl chunk raw_docs/python_guide.md corpora/programming/chunks/

# 2. Validate the corpus structure
lfl validate corpora/programming

# 3. Run retrieval benchmarks
lfl benchmark run corpora/programming

# 4. Optimize parameters with sweep
lfl benchmark sweep corpora/programming
```

### Documentation

**Getting Started:**
- [QUICKSTART.md](docs/QUICKSTART.md) — Step-by-step tutorials for first-time users
- [Embedding Setup Guide](docs/EMBEDDING_SETUP.md) — Configure and use embedded models
- [Contributors Guide](contributors/) — Complete contributor documentation hub

**For Contributors:**
- [Onboarding Guide](contributors/ONBOARDING.md) — New contributor setup and first PR
- [Architecture](contributors/ARCHITECTURE.md) — System architecture with Mermaid diagrams
- [Benchmarking Guide](contributors/BENCHMARKING_GUIDE.md) — Deep dive into metrics and optimization
- [Contributing Guide](contributors/CONTRIBUTING_GUIDE.md) — Contribution policies and workflows

**Technical Reference:**
- [API Reference](docs/api/) — Sphinx-generated API documentation
- [IMPLEMENTATION_REPORT_2026-02-26.md](docs/IMPLEMENTATION_REPORT_2026-02-26.md) — Implementation details
- [CHANGELOG.md](CHANGELOG.md) — Version history and features
- [Licensing Guide](docs/licensing-guide.md) — Licensing and attribution

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
- Hugging Face dataset pipelines ([LittleFreeLibrary datasets](https://huggingface.co/LittleFreeLibrary))
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
