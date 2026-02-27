# Changelog

All notable changes to Little Free Library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Drop-Folder Document Ingestion System

- **New `lfl ingest` CLI command** - Full end-to-end workflow for arbitrary document formats
  - Supports PDF, DOCX, XLSX, HTML, TXT, Markdown
  - Apple iWork support (Pages, Numbers, Keynote) via LibreOffice conversion
  - Legacy Office format support (DOC, XLS, PPT) via LibreOffice
  - OCR fallback for scanned PDFs (requires Tesseract)
  - Integrated with `lfl.chunking` for YAML-frontmatter chunks
  - Integrated with `lfl.corpus_validation` for post-ingestion validation
  - Optional embedding generation via `--embed` flag
  - SHA256-based idempotency (`--on-duplicate skip|overwrite|error`)
  - Inventory dry-run mode (`--inventory`)
  - Auto-generates `sources.json` and `CORPUS.md`
  - Writes manifest to `ingestion_out/<domain>/manifest.json`
  
- **`lfl/ingest/` module** - Modular ingestion pipeline
  - `types.py` - Dataclasses for ingestion workflow
  - `detect.py` - MIME type detection with fallback (python-magic / puremagic)
  - `convert.py` - LibreOffice headless conversion wrappers
  - `extract.py` - Format-specific text/table extractors
  - `pipeline.py` - Main ingestion orchestration
  
- **Optional dependency extras** in `setup.py`
  - `[ingest]` - Common document formats (DOCX, XLSX, HTML)
  - `[pdf]` - PDF extraction (PyMuPDF, pdfplumber)
  - `[ocr]` - OCR support (pytesseract, Pillow)
  - `[convert]` - Universal converters (pypandoc)
  - `[office_crypto]` - Encrypted Office files (msoffcrypto-tool)
  - `[all_ingest]` - Complete ingestion bundle
  - `[dev]` - Development dependencies
  
- **Drop-folder structure** (`ingestion/` and `ingestion_out/`)
  - `ingestion/<domain>/` - User input directory (gitignored)
  - `ingestion_out/<domain>/` - Generated artifacts (gitignored)
  - Manifest generation for ingestion run tracking
  
- **Documentation**
  - `docs/KB/INGESTION_SYSTEM_SPEC.md` - Complete 2,000+ line specification
  - `ingestion/README.md` - User guide for drop-folder usage
  - `ingestion_out/README.md` - Artifacts and manifest documentation
  - Updated `README.md` with ingestion quick start
  - Updated CLI commands documentation

#### Enhanced Git Hygiene

- **Comprehensive `.gitignore`** updates
  - Gitignore `ingestion/` and `ingestion_out/` directories
  - Block common document formats (PDF, DOCX, XLSX, Pages, etc.)
  - Block generated databases and vector stores

- **CI workflow** (`.github/workflows/validate-files.yml`)
  - Checks staged files for forbidden extensions on every push/PR
  - Validates ingestion directories stay clean
  - Runs `lfl validate` against all corpora

- **Pre-commit guard** (`scripts/check_forbidden_files.py`)
  - Blocks ~50 forbidden file extensions from being committed
  - Path-based allowlist for models/, docs/, corpora/
  - Directs users to `lfl ingest` workflow
  - Block images and archives (often ingestion input)
  - Preserve tracked model files (LFS) and curated corpora

#### Structured Error Code System

- **`lfl/ingest/errors.py`** — 38 structured error codes across 7 categories
  - `LFL-D1xx` Detection (4 codes): Input directory, file type, empty directory, hidden files
  - `LFL-C2xx` Conversion (4 codes): LibreOffice missing/timeout/failure/output
  - `LFL-E1xx` Extraction (14 codes): Corrupt PDF, zlib streams, OCR fallback, encoding
  - `LFL-K3xx` Chunking (6 codes): YAML frontmatter, missing fields, type mismatches
  - `LFL-V4xx` Validation (5 codes): sources.json, cross-references, orphaned sources
  - `LFL-M5xx` Embedding (4 codes): Model loading, dimension mismatch, encoding failure
  - `LFL-P6xx` Pipeline (4 codes): Empty extraction, zero chunks, dedup, unexpected errors
  - `IngestionError` frozen dataclass with `cli_message()`, `verbose_message()`, `to_dict()`
  - `ERROR_CATALOGUE` registry with `lookup_error_code()` and `format_error_reference()`
  - Integrated into all pipeline stages (extract, convert, pipeline, validation)

- **New CLI commands** for error diagnostics
  - `lfl error-codes` — List all 38 codes in a formatted table
  - `lfl explain-error <code>` — Look up a specific code with summary + resolution

- **`docs/ERROR_CODES.md`** — User-facing error code reference documentation
  - All 38 codes with descriptions, causes, and fixes
  - CLI usage examples and manifest JSON examples
  - `jq` search commands for filtering error codes in manifests

- **Structured error propagation in ingestion manifests**
  - `IngestionResult` and `ExtractedDoc` now carry `error_code` and `structured_errors`
  - Manifest JSON includes full error details with resolution steps
  - Validation errors prefixed with `[LFL-K3xx]` codes

#### Programming Corpus — PDF Ingestion

- **22 PDF sources** ingested into `corpora/programming/`
  - 18/19 PDFs succeeded → 590 chunks generated
  - 1 PDF failed (corrupt zlib streams) → diagnosed with `LFL-E101`
  - Sources added to `corpora/programming/sources.json`
  - 594 total chunks validated (0 invalid)
  - 594 embeddings generated (384-dim, float32, unit-normalized, 0.9 MB)

#### Documentation SOP v2.1.0 — Session Summary Requirements

- **Mandatory session summaries** added to Documentation SOP
  - Session summaries elevated from optional to **required** (Tier 6)
  - One file per day rule — exactly one `SESSION_SUMMARY_<MMMDD>_<YYYY>.md` per calendar day
  - Strict nomenclature enforced with valid/invalid examples
  - Amend-as-you-go workflow — update incrementally during session, not just at end
  - Template required — must use `SESSION_REVIEW_TEMPLATE.md` format exactly
  - Added to Contribution Type matrix as "Any commit (all types)" row
  - Added to sweep algorithm as step 3 (before commit)
  - Added to pre-commit checklist as "For All Contributions (Required)" section
  - Failure mode defined: missing session summary = blocking documentation gap

### Fixed

- **Embedding integration in `lfl ingest --embed`** — Three bugs in `pipeline.py` Stage 8:
  - `EmbeddingModel` received `EmbeddingProfile` object instead of `profile_id` string
  - `load_corpus()` received `str` path instead of `Path` (caused `str / str` TypeError)
  - Called `model.embed()` instead of correct `model.encode()` method
  - All three verified fixed via end-to-end test (TXT + HTML → 384-dim vectors)

- **YAML frontmatter double-quote escaping** in `lfl/chunking.py`
  - `save_chunk_to_markdown()` now escapes `\` and `"` in double-quoted YAML fields via `_esc()` helper
  - Fixed 6 existing chunks with titles containing internal double quotes
  - All 594 chunks validate cleanly after patch

---

#### Embedded Models (~796 MB)

- **FastEmbed ONNX Models** (~273 MB)
  - `BAAI/bge-small-en-v1.5` - 384-dim baseline model
  - `BAAI/bge-base-en-v1.5` - 768-dim quality model
  - Cross-platform support (CPU, DirectML, CUDA)
  - No PyTorch dependency required
  - Fast cold start (<1s)

- **Sentence-Transformers PyTorch Model** (~523 MB)
  - `nomic-ai/nomic-embed-text-v1.5` - 768-dim Apache 2.0 licensed
  - Full PyTorch model with fine-tuning capability
  - GPU optimization support (CUDA, ROCm, MPS)
  - Access to wider HuggingFace ecosystem

#### Infrastructure

- **Git LFS Configuration** (`.gitattributes`)
  - Tracks large model files (`.onnx`, `.safetensors`, `.bin`)
  - Tracks FastEmbed blob storage
  - 11 files totaling ~796 MB tracked with LFS

- **Model Management Scripts**
  - `scripts/download_fastembed_models.py` - Download FastEmbed ONNX models
  - `scripts/download_sentence_transformers_model.py` - Download PyTorch model
  - `scripts/test_embeddings.py` - Comprehensive test suite for both systems

#### Documentation

- **`models/README.md`** - Model directory overview
  - Structure explanation
  - System comparison (FastEmbed vs Sentence-Transformers)
  - Auto-detection behavior
  - Manual download instructions

- **`docs/EMBEDDING_SETUP.md`** - Complete embedding setup guide
  - Quick start for both systems
  - Usage in Little Free Library
  - Model comparison table
  - When to use each system
  - Testing procedures
  - Performance optimization tips
  - Troubleshooting guide

- **`contributors/` Directory Organization**
  - Created centralized contributor documentation hub
  - Moved and renamed documentation files:
    - `ONBOARDING.md` (formerly `docs/CONTRIBUTOR_ONBOARDING.md`)
    - `ARCHITECTURE.md` (formerly `docs/ARCHITECTURE.md`)
    - `BENCHMARKING_GUIDE.md` (formerly `docs/BENCHMARKING_GUIDE.md`)
    - `CONTRIBUTING_GUIDE.md` (formerly `docs/contributing-guide.md`)
  - `contributors/README.md` - Navigation hub with 4 reading paths

- **Contributor Onboarding Updates** (`contributors/ONBOARDING.md`, `contributors/CONTRIBUTING_GUIDE.md`)
  - Added Git LFS as required prerequisite with installation instructions
  - Updated Quick Start with `git lfs pull` step (~796 MB download)
  - Added "Embedded Models" section explaining both FastEmbed and Sentence-Transformers
  - Added embedding test verification step
  - Clarified disk space requirement (~1 GB)
  - Updated local setup instructions in Contributing Guide
  - Linked to comprehensive EMBEDDING_SETUP.md guide

- **Documentation SOP Enhancement** (`docs/SOP/DOCUMENTATION_SOP.md`)
  - Added 3 new contribution types: Infrastructure, Dependency, Setup/Installation changes
  - Elevated contributors/ to Tier 3 in documentation priority
  - Added detailed "Contributors Directory Updates" section
  - Added 5 update scenarios with checklists
  - Added Contributors Documentation Checklist
  - Restructured document priority tiers (now 5 tiers)
  - Added 175 lines of guidance for maintaining contributor documentation

### Changed

- **`requirements.txt`** - Updated embedding dependencies
  - Uncommented `fastembed>=0.2.0` (recommended, cross-platform)
  - Uncommented `sentence-transformers>=2.2.0` (PyTorch-based)
  - Added `einops>=0.8.0` (required by nomic-embed-text)
  - Both systems now installed by default for flexibility

- **Project Structure**
  - Added `models/` directory at repository root
  - Added `models/fastembed/` for ONNX models cache
  - Added `models/nomic-embed-text/` for PyTorch model

### Technical Details

- **Offline Usage**
  - Both embedding systems work completely offline after initial setup
  - Models cached locally in `models/` directory
  - No internet required after `git lfs pull`

- **Testing**
  - Comprehensive test suite verifies both systems
  - Tests embedding generation (384-dim and 768-dim)
  - Validates cosine similarity computation
  - Ensures embeddings differ for different inputs

- **Model Sizes**
  - FastEmbed small model: ~64 MB (ONNX blob)
  - FastEmbed base model: ~208 MB (ONNX blob)
  - Sentence-Transformers model: ~522 MB (SafeTensors)
  - Total with metadata: ~796 MB

---

## [1.0.0] - 2026-02-26

### Added

#### Core Package (`lfl/`)
- **Chunking Strategies Module** (`lfl/chunking.py`)
  - `naive_paragraph` - Split on double newlines, pack to target size
  - `heading_aware` - Split at markdown headings, preserve structure
  - `sliding_window` - Fixed-size windows with configurable overlap
  - `semantic` - Semantic boundary detection (placeholder, falls back to heading_aware)
  - Automatic title extraction from content
  - Deterministic chunk IDs with content hashing
  - Complete metadata generation with YAML frontmatter

- **Corpus Validation Module** (`lfl/corpus_validation.py`)
  - Validate YAML frontmatter completeness
  - Check required metadata fields (title, domain, source, license, etc.)
  - Validate sources.json structure and schema
  - Cross-reference source_id fields with sources.json
  - Detect orphaned sources (no chunks reference them)
  - Human-readable validation reports with actionable errors

- **Vector Embeddings Module** (`lfl/embeddings.py`)
  - Multi-backend support (FastEmbed, sentence-transformers)
  - Graceful fallback to BM25-only mode if embeddings unavailable
  - Profile-based embedding configuration (reproducible builds)
  - Cosine similarity utilities
  - Save/load embeddings to disk (.npy format)
  - Backend auto-detection with clear error messages

- **Hybrid Retrieval Module** (`lfl/retrieval.py`)
  - BM25 lexical retrieval (always available, no dependencies)
  - Vector semantic retrieval (requires embedding backend)
  - Hybrid mode with Reciprocal Rank Fusion (RRF)
  - Configurable alpha parameter for BM25/vector weighting
  - Automatic fallback to BM25-only if embeddings unavailable
  - Detailed result objects with per-metric scores

#### CLI Commands

- **`lfl chunk`** - Document chunking command
  - Convert raw documents to corpus-ready markdown chunks
  - Support for all chunking strategies
  - Configurable chunk size, overlap, min/max tokens
  - Automatic YAML frontmatter generation
  - Complete metadata with content hashing
  - Tags, importance scoring, and verification dates
  
- **`lfl validate`** - Enhanced corpus validation
  - Now validates sources.json schema
  - Cross-references chunk source_ids with sources.json
  - Detects orphaned sources
  - Comprehensive validation reports with warnings and errors
  - Structuredoutput format for automation

- **`lfl benchmark run|sweep|compare`** - Retrieval benchmarking (already existed)
  - BM25 baseline testing
  - Synthetic query generation
  - Recall@k, MRR scoring
  - Token efficiency metrics
  - Parameter sweeps for optimization

- **`lfl version`** - Show package version

#### Embedding Profiles

- 5 official embedding profiles in `lfl/profiles/`:
  - `baseline_cpu_onnx_small` - Default, works on any CPU
  - `quality_cpu_onnx_base` - Higher quality, slower
  - `power_user_cuda` - NVIDIA GPU optimized
  - `power_user_rocm` - AMD GPU optimized
  - `windows_gpu_directml` - Windows GPU support
- Profile-based system ensures reproducibility

#### Documentation

- **`docs/QUICKSTART.md`** - Comprehensive quick start guide
  - Installation instructions
  - Command usage examples
  - Chunking workflow
  - Validation workflow
  - Benchmark workflow
  - Score interpretation guide
  - Troubleshooting section

- **`docs/IMPLEMENTATION_REPORT_2026-02-26.md`** - Complete implementation report
  - System architecture overview
  - Design decisions and rationale
  - File changes and additions
  - Testing results
  - Next steps and enhancements

- **Updated `README.md`**
  - Added "The Toolkit" section documenting lfl CLI
  - Benchmarking system overview
  - Embedding profiles table
  - Installation instructions
  - Link to implementation report

#### Dependencies

- Updated `requirements.txt`:
  - Core dependencies: pyyaml, numpy, typer (all installed)
  - Optional: fastembed or sentence-transformers for embeddings
  - Optional: tiktoken for accurate tokenization
  - Development dependencies listed

- `setup.py` for package installation
  - Entry point for `lfl` CLI command
  - Package metadata and classifiers
  - Dependency specification

### Changed

- **`lfl/__init__.py`** - Expanded exports
  - Added chunking module exports
  - Added embeddings module exports
  - Added retrieval module exports
  - Added validation module exports
  - Added profiles module exports

- **Validation module** - Enhanced functionality
  - Now supports sources.json validation
  - Cross-reference checking
  - Better error messages

### Fixed

- **Variable shadowing bug** in `lfl/chunking.py`
  - Fixed `chunk_text` variable conflict in `chunk_document()`
  - Changed loop variable from `chunk_text` to `text_content`

### Testing

- **End-to-end integration tests**
  - Document chunking (heading_aware strategy)
  - Corpus validation (chunks + sources.json)
  - BM25 retrieval
  - Benchmark system (run, sweep, compare)
  - All CLI commands verified functional

- **Test corpus**
  - Added 4 sample chunks to `corpora/programming/chunks/`:
    - `python_list_comprehension.md`
    - `big_o_notation.md`
    - `git_branching_strategy.md`
    - `restful_api_design.md`
  - All chunks have complete YAML frontmatter
  - Used for benchmark testing

### Technical Debt

- **Tiktoken integration** - Not yet implemented
  - Currently using naive token counting (~4 chars/token)
  - Accurate for most use cases but not precise
  - Consider adding tiktoken support for OpenAI-accurate counts

- **Semantic chunking** - Placeholder implementation
  - Currently falls back to heading_aware
  - Could implement using sentence-transformers for boundary detection

- **Query generation strategies** - Extractive and LLM modes exist but not fully tested
  - Heuristic mode is tested and working
  - Extractive mode implemented but needs validation
  - LLM mode requires external inference server

### Statistics

- **New code**: ~1,476 lines of production Python
  - `lfl/chunking.py`: 591 lines
  - `lfl/corpus_validation.py`: 351 lines (enhanced from existing)
  - `lfl/embeddings.py`: 287 lines
  - `lfl/retrieval.py`: 247 lines

- **Package exports**: 40+ public API functions and classes
- **CLI commands**: 5 main commands (validate, chunk, benchmark, version, compare)
- **Chunking strategies**: 4 implemented (1 placeholder)
- **Embedding backends**: 2 supported (FastEmbed, sentence-transformers)
- **Retrieval modes**: 3 (BM25, vector, hybrid)

---

## [0.1.0] - 2026-02-25 (Pre-release)

### Initial Release

- Basic corpus structure
- Validation scripts
- Benchmark reference implementations in `docs/KB/Reference/`
- Programming corpus (draft)
- Documentation SOPs
- Contributing guidelines

---

## Future Roadmap

### Planned Features

- **vectorset validation** - Integrate existing `validate_vectorset.py` script
- **Ingestion pipeline** - Convert chunks to Hugging Face datasets
- **Tiktoken integration** - Accurate token counting
- **CI/CD integration** - Automated benchmarks on PR
- **Enhanced reporting** - HTML reports with visualizations
- **Query strategy validation** - Test extractive and LLM modes
- **Cross-lingual support** - Multi-language corpora
- **Reranking** - Cross-encoder support
- **Dashboard** - Web UI for corpus exploration

### Under Consideration

- **pxctx integration** - Direct integration with pxctx RAG system
- **Automated hyperparameter tuning** - ML-based parameter optimization
- **Knowledge graph** - Entity linking and relationship extraction
- **Quality scoring** - ML-based chunk quality prediction
- **Deduplication** - Detect and merge duplicate/similar chunks

---

[1.0.0]: https://github.com/justincheshire-star/Little-Free-Library/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/justincheshire-star/Little-Free-Library/releases/tag/v0.1.0
