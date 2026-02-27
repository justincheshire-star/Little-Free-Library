# Little Free Library — Drop-Folder Ingestion System Specification

**Version:** 1.0.0  
**Date:** February 27, 2026  
**Status:** Implementation Ready  
**Owner:** Little Free Library Contributors

---

## Executive Summary

This specification defines a **drop-folder ingestion workflow** that extends the LFL toolkit to accept arbitrary document formats (PDF, DOCX, Pages, Excel, etc.) and automatically convert them into the canonical LFL corpus format (Markdown chunks + YAML frontmatter + provenance).

**Key principle:** One command from arbitrary docs → validated corpus.

```bash
# User workflow
mkdir -p ingestion/programming
# Drop files: PDFs, DOCX, Pages, etc.
lfl ingest programming --embed --profile baseline_cpu_onnx_small
# Output: corpora/programming/chunks/*.md + sources.json + embeddings/
```

---

## Goals

1. **Lower barrier to entry** — Accept documents in common formats without manual conversion
2. **Preserve existing architecture** — Wrap existing chunking/validation/embedding pipeline
3. **Maintain corpus quality** — Safe metadata defaults prevent accidental license violations
4. **Keep core lean** — Format support via optional dependency extras
5. **Prevent pollution** — Never commit raw ingestion inputs or generated artifacts

---

## Architecture

### Directory Contract

```
Repository Root:
├── ingestion/              # ⚠️ NEVER COMMITTED (user input drop-folder)
│   └── <domain>/
│       └── (user drops files here)
│
├── ingestion_out/          # ⚠️ NEVER COMMITTED (generated artifacts)
│   └── <domain>/
│       ├── converted/      # LibreOffice/Pandoc outputs
│       ├── extracted/      # Normalized pre-chunk text/JSON
│       └── manifest.json   # Per-run ingestion report
│
└── corpora/                # ✅ TRACKED (canonical corpus format)
    └── <domain>/
        ├── CORPUS.md
        ├── sources.json
        ├── chunks/
        │   └── *.md        # Markdown + YAML frontmatter
        └── embeddings/     # Optional
            └── vectors.npy
```

**Rules:**
- `ingestion/` and `ingestion_out/` are **always gitignored**
- Final corpus output follows existing schema (unchanged)
- Conversion intermediates are temporary and disposable

---

## CLI Design

### New Command: `lfl ingest DOMAIN`

**Purpose:** Convert arbitrary documents → validated corpus with optional embeddings

**Arguments:**
- `DOMAIN` (required) — Target corpus domain name

**Flags:**
```
--input PATH              Override input directory (default: ingestion/<domain>)
--corpus-dir PATH         Override output directory (default: corpora/<domain>)
--recursive / --no-recursive  Scan subdirectories (default: recursive)
--embed                   Generate embeddings after chunking (default: off)
--profile NAME            Embedding profile (default: baseline_cpu_onnx_small)
--on-duplicate skip|update    Handle existing chunks (default: update)
--strict                  Enable strict validation mode
--chunk-size INT          Token target per chunk (default: 512)
--overlap INT             Token overlap between chunks (default: 64)
--strategy STR            Chunking strategy (default: heading_aware)
--inventory               Dry-run: show what would be ingested without writing
```

**Examples:**
```bash
# Basic ingestion
lfl ingest programming

# With embeddings
lfl ingest programming --embed --profile quality_cpu_onnx_base

# Custom paths
lfl ingest business --input /tmp/docs --corpus-dir /tmp/corpus

# Inventory mode (dry-run)
lfl ingest programming --inventory
```

---

## Pipeline Stages

### Stage 1: Discovery & Type Detection

**Input:** Files in `ingestion/<domain>/`

**Process:**
1. Recursive scan (respects `--recursive` flag)
2. MIME type detection:
   - Primary: `python-magic` (Linux/macOS)
   - Fallback: `puremagic` (Windows)
   - Extension hint as last resort
3. Group by type for batching

**Output:** List of `DiscoveredFile` records

```python
@dataclass
class DiscoveredFile:
    path: Path
    mime_type: str
    detected_type: str  # pdf|docx|xlsx|pages|html|...
    size_bytes: int
    sha256: str
```

---

### Stage 2: Conversion (if needed)

**Conversion Matrix:**

| Input Format | Conversion Method | Target Format | Tool |
|--------------|-------------------|---------------|------|
| `.pages` | LibreOffice headless | PDF | `soffice` |
| `.numbers` | LibreOffice headless | XLSX | `soffice` |
| `.key` | LibreOffice headless | PDF | `soffice` |
| `.doc` (legacy) | LibreOffice headless | DOCX | `soffice` |
| `.ppt` (legacy) | LibreOffice headless | PDF | `soffice` |
| `.xls` (legacy) | LibreOffice headless | XLSX | `soffice` |
| Encrypted Office | Fail-fast with clear error | — | — |

**LibreOffice command:**
```bash
soffice --headless --convert-to <format> --outdir <dir> <input>
```

**Converted files stored at:**
```
ingestion_out/<domain>/converted/<original_stem>.<new_ext>
```

---

### Stage 3: Extraction

**Per-format extractors:**

#### PDF
```python
def extract_pdf(path: Path) -> ExtractedDoc:
    # 1. Try PyMuPDF (fast)
    text = extract_pymupdf(path)
    
    # 2. Fallback to pdfplumber (better tables)
    if not text.strip():
        text, tables = extract_pdfplumber(path)
    
    # 3. OCR fallback (if [ocr] installed and text still empty)
    if not text.strip() and pytesseract_available:
        text = extract_ocr(path)
        
    return ExtractedDoc(text=text, tables=tables, method=...)
```

#### DOCX
```python
def extract_docx(path: Path) -> ExtractedDoc:
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    tables = [extract_table(table) for table in doc.tables]
    return ExtractedDoc(text="\n\n".join(paragraphs), tables=tables)
```

#### XLSX / Numbers (converted)
```python
def extract_xlsx(path: Path) -> ExtractedDoc:
    sheets = pd.read_excel(path, sheet_name=None)
    tables = [
        ExtractedTable(
            sheet_name=name,
            data=df.to_dict('records'),
            markdown=df.to_markdown()
        )
        for name, df in sheets.items()
    ]
    return ExtractedDoc(tables=tables)
```

#### HTML
```python
def extract_html(path: Path) -> ExtractedDoc:
    soup = BeautifulSoup(path.read_text(), 'lxml')
    # Remove scripts, styles
    for tag in soup(['script', 'style']):
        tag.decompose()
    text = soup.get_text(separator='\n\n')
    return ExtractedDoc(text=text)
```

**Output:** `ExtractedDoc` dataclass

```python
@dataclass
class ExtractedDoc:
    text: str
    title: str | None
    source_path: Path
    detected_type: str
    extraction_method: str  # native|converted|ocr
    tables: list[ExtractedTable]
    warnings: list[str]
    
@dataclass
class ExtractedTable:
    sheet_name: str | None
    data: list[dict]  # Rows as dicts
    markdown: str     # Table as Markdown
```

---

### Stage 4: Chunking

**Call existing chunking module:**

```python
from lfl.chunking import chunk_document

for extracted_doc in extracted_docs:
    chunks = chunk_document(
        text=extracted_doc.text,
        strategy=args.strategy,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        title=extracted_doc.title,
    )
    
    # Add frontmatter to each chunk
    for chunk in chunks:
        chunk.metadata.update({
            'source': f'file://{extracted_doc.source_path.relative_to(repo_root)}',
            'source_license': 'unknown',  # ⚠️ User must fill
            'retrieved_at': datetime.now().isoformat(),
            'verified': 'unverified',
            'source_id': f'local_{sha256[:8]}',
            'content_hash': f'sha256:{sha256_full}',
            'extraction_method': extracted_doc.extraction_method,
        })
```

---

### Stage 5: Validation

**Call existing validation:**

```python
from lfl.corpus_validation import validate_corpus

validate_corpus(
    corpus_dir=corpus_dir,
    strict=args.strict,
)
```

**Validation always runs** — fail loudly if chunks are malformed.

---

### Stage 6: Embedding (Optional)

**Only if `--embed` flag set:**

```python
if args.embed:
    from lfl.embeddings import EmbeddingModel
    
    model = EmbeddingModel(profile=args.profile)
    vectors = model.embed_corpus(corpus_dir / 'chunks')
    
    np.save(corpus_dir / 'embeddings' / 'vectors.npy', vectors)
```

---

### Stage 7: Manifest Output

**Always write manifest:**

```json
{
  "run_id": "20260227_143022",
  "domain": "programming",
  "input_dir": "ingestion/programming",
  "output_dir": "corpora/programming",
  "timestamp": "2026-02-27T14:30:22Z",
  "stats": {
    "files_discovered": 45,
    "files_converted": 3,
    "files_extracted": 45,
    "chunks_created": 287,
    "chunks_updated": 12,
    "failures": 0
  },
  "files": [
    {
      "path": "ingestion/programming/python_guide.pdf",
      "sha256": "4b3a2f...",
      "detected_type": "pdf",
      "extraction_method": "native",
      "chunks_produced": 12,
      "status": "success"
    },
    {
      "path": "ingestion/programming/design_patterns.pages",
      "sha256": "8c5d1a...",
      "detected_type": "pages",
      "extraction_method": "converted",
      "conversion_target": "pdf",
      "chunks_produced": 8,
      "status": "success"
    }
  ],
  "warnings": [
    "File encrypted.docx failed: password-protected (not supported)"
  ]
}
```

**Stored at:** `ingestion_out/<domain>/manifest.json`

---

## Dependency Strategy

### Core Dependencies (unchanged)
```
pyyaml>=6.0
numpy>=1.21
typer>=0.9.0
```

### Optional Extras

```python
# setup.py or pyproject.toml
extras_require = {
    # Common formats (no ML)
    'ingest': [
        'python-magic>=0.4.27; platform_system!="Windows"',
        'puremagic>=1.15; platform_system=="Windows"',
        'charset-normalizer>=3.2',
        'beautifulsoup4>=4.12',
        'lxml>=4.9',
        'python-docx>=1.1.0',
        'openpyxl>=3.1.0',
        'pandas>=2.0.0',
    ],
    
    # PDF support
    'pdf': [
        'pymupdf>=1.23.0',
        'pdfplumber>=0.11.0',
    ],
    
    # OCR (scanned docs)
    'ocr': [
        'pytesseract>=0.3.10',
        'Pillow>=10.0.0',
    ],
    
    # Conversion utilities
    'convert': [
        'pypandoc>=1.12',
    ],
    
    # Encrypted Office files
    'office_crypto': [
        'msoffcrypto-tool>=5.0.0',
    ],
    
    # Everything
    'all_ingest': [
        'lfl[ingest,pdf,ocr,convert,office_crypto]',
    ],
}
```

**User install options:**
```bash
# Minimal (existing)
pip install lfl

# With ingestion support
pip install "lfl[all_ingest]"

# Embeddings + ingestion
pip install "lfl[all_ingest]" fastembed sentence-transformers einops
```

---

## System Prerequisites

| Tool | Purpose | Install Command | Required For |
|------|---------|-----------------|--------------|
| **LibreOffice** | Convert Pages/Numbers/Keynote | `brew install libreoffice` (macOS)<br>`sudo apt install libreoffice` (Ubuntu) | Pages, Numbers, Keynote, legacy Office |
| **Tesseract** | OCR for scanned PDFs | `brew install tesseract`<br>`sudo apt install tesseract-ocr` | Scanned documents |
| **Pandoc** | Universal doc converter | `brew install pandoc`<br>`sudo apt install pandoc` | Optional (enhanced conversions) |
| **Poppler** | PDF utilities | `brew install poppler`<br>`sudo apt install poppler-utils` | Optional (PDF tooling) |

**Check availability:**
```bash
lfl ingest --check-system
# Output:
# ✓ LibreOffice found: /usr/bin/soffice
# ✓ Tesseract found: /usr/bin/tesseract
# ✓ Pandoc found: /usr/local/bin/pandoc
# ⚠ Poppler not found (optional)
```

---

## Metadata Defaults (Safe & Conservative)

**Problem:** Ingested documents don't have explicit license/provenance.

**Solution:** Default to "unknown/unverified" to prevent accidental publishing:

```yaml
---
title: "Extracted from document_name.pdf"
domain: "programming"  # From ingest command
subdomain: ""          # User must categorize
source: "file://ingestion/programming/document_name.pdf"
source_license: "unknown"  # ⚠️ User must verify before publishing
source_id: "local_4b3a2f8c"
retrieved_at: "2026-02-27"
verified: "unverified"  # ⚠️ Must verify content accuracy
importance: 0.5        # Neutral default
tags: []               # User must tag
version: "1.0.0"
content_hash: "sha256:4b3a2f8c..."
extraction_method: "native"  # or "converted" or "ocr"
---
```

**Publishing gate:**
- CI check: fail if any chunk has `source_license: unknown` or `verified: unverified`
- Force users to review and update metadata before publishing to Hugging Face

---

## Git Hygiene

### .gitignore Rules

Add to repository `.gitignore`:

```gitignore
############################
# Ingestion System
############################
# User input (never commit)
ingestion/

# Generated artifacts (never commit)
ingestion_out/

# Temporary conversions
converted/
tmp_ingest/
.cache_ingest/

############################
# Document Formats (prevent accidental commits)
############################
# Office
*.doc
*.docx
*.xls
*.xlsx
*.ppt
*.pptx

# Apple iWork
*.pages
*.numbers
*.key

# PDFs (unless explicitly tracked in docs/)
*.pdf

# Ebooks
*.epub
*.mobi

# Archives
*.zip
*.tar
*.gz
*.7z
*.rar

# Images (often ingestion input)
*.png
*.jpg
*.jpeg
*.tif
*.tiff

############################
# Generated Indexes & Databases
############################
*.db
*.sqlite
*.sqlite3
*.duckdb
*.npy  # Unless under corpora/ (tracked embeddings)
*.npz

# Vector stores
chroma/
.chroma/
qdrant/
weaviate_data/
lancedb/
*.faiss
*.index
*.lance
*.parquet

############################
# Python / Environment
############################
__pycache__/
*.py[cod]
.venv/
venv/
.env
dist/
build/
*.egg-info/
```

**Exception:** Curated corpora under `corpora/` ARE tracked.

---

### Pre-commit Hook (Recommended)

Add `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: block-ingestion-artifacts
        name: Block ingestion artifacts
        entry: Prevent committing ingestion inputs/outputs
        language: system
        pass_filenames: true
        files: ^(ingestion/|ingestion_out/)
        always_run: false
        
      - id: block-large-binaries
        name: Block large binaries outside LFS
        entry: python scripts/check_large_files.py
        language: system
        pass_filenames: true
        files: '\.(pdf|docx|xlsx|pages|db|sqlite|npy)$'
```

**CI enforcement:**
```yaml
# .github/workflows/validate.yml
- name: Check for forbidden files
  run: |
    if git ls-files | grep -E '^(ingestion/|ingestion_out/)'; then
      echo "::error::Ingestion artifacts must not be committed"
      exit 1
    fi
```

---

## Implementation Modules

### New Package Structure

```
lfl/ingest/
├── __init__.py           # Public API
├── types.py              # Dataclasses (DiscoveredFile, ExtractedDoc, etc.)
├── detect.py             # MIME detection & type routing
├── convert.py            # LibreOffice/Pandoc wrappers
├── extract.py            # Format-specific extractors
│   ├── pdf.py
│   ├── docx.py
│   ├── xlsx.py
│   └── html.py
├── pipeline.py           # Main ingestion orchestration
└── manifest.py           # Manifest generation & reporting
```

### Core Contracts

```python
# lfl/ingest/types.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

@dataclass
class DiscoveredFile:
    path: Path
    mime_type: str
    detected_type: str
    size_bytes: int
    sha256: str

@dataclass
class ExtractedTable:
    sheet_name: str | None
    data: list[dict]
    markdown: str
    
@dataclass
class ExtractedDoc:
    text: str
    title: str | None
    source_path: Path
    detected_type: str
    extraction_method: Literal['native', 'converted', 'ocr']
    tables: list[ExtractedTable] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class IngestionResult:
    file_path: Path
    sha256: str
    detected_type: str
    extraction_method: str
    chunks_produced: int
    status: Literal['success', 'failed']
    error: str | None = None
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_ingest_detect.py
def test_detect_pdf():
    assert detect_type("test.pdf") == "pdf"

def test_detect_pages():
    assert detect_type("test.pages") == "pages"

# tests/test_ingest_extract.py
def test_extract_docx_with_tables():
    doc = extract_docx(fixture_path("sample.docx"))
    assert len(doc.text) > 100
    assert len(doc.tables) == 2

def test_extract_pdf_fallback_to_ocr():
    # Scanned PDF with no text layer
    doc = extract_pdf(fixture_path("scanned.pdf"))
    assert doc.extraction_method == "ocr"
    assert len(doc.text) > 50
```

### Integration Tests

```python
# tests/test_ingest_pipeline.py
def test_full_pipeline_docx_to_corpus(tmp_path):
    # Setup
    input_dir = tmp_path / "ingestion" / "test"
    input_dir.mkdir(parents=True)
    shutil.copy("fixtures/python_guide.docx", input_dir)
    
    # Run
    ingest(
        domain="test",
        input_dir=input_dir,
        corpus_dir=tmp_path / "corpora" / "test",
    )
    
    # Assert
    chunks_dir = tmp_path / "corpora" / "test" / "chunks"
    assert chunks_dir.exists()
    assert len(list(chunks_dir.glob("*.md"))) > 0
    
    # Check frontmatter
    chunk = Chunk.load(list(chunks_dir.glob("*.md"))[0])
    assert chunk.metadata['source_license'] == 'unknown'
    assert 'sha256:' in chunk.metadata['content_hash']
```

### Fixture Matrix

| Fixture File | Purpose |
|--------------|---------|
| `sample.docx` | DOCX with headings + tables |
| `sample.xlsx` | Excel with 2 sheets |
| `sample.pdf` | PDF with selectable text |
| `scanned.pdf` | Image-only PDF (OCR test) |
| `sample.pages` | Pages doc (conversion test) |
| `encrypted.docx` | Password-protected (failure test) |
| `sample.html` | HTML with metadata |

---

## Error Handling

### Graceful Degradation

| Scenario | Behavior |
|----------|----------|
| LibreOffice not found | Log warning; skip Pages conversion; continue with other files |
| Tesseract not found | Skip OCR fallback; mark PDF as "extraction_failed" |
| Encrypted file | Log error; add to manifest warnings; continue |
| Empty extraction | Mark file as "no_content"; continue |
| Conversion timeout | Timeout after 5min; mark as "conversion_timeout"; continue |

**Never silent failure** — every file produces a manifest entry.

---

## Performance Characteristics

| Stage | Expected Speed | Bottleneck |
|-------|---------------|------------|
| Discovery | ~10,000 files/sec | Filesystem |
| Type detection | ~500 files/sec | MIME sniffing |
| Conversion (Pages) | ~5 sec/file | LibreOffice startup |
| PDF extraction | ~50 pages/sec | Text extraction |
| OCR | ~1 page/sec | Tesseract |
| Chunking | ~100 docs/sec | Already optimized |
| Validation | ~1000 chunks/sec | Already optimized |
| Embedding | ~50 chunks/sec | Model inference |

**Optimization opportunities:**
- Batch conversions (multiple files → one LibreOffice instance)
- Parallel extraction (multiprocessing pool)
- Streaming chunking (avoid loading all docs in memory)

---

## Security Considerations

1. **No stored credentials** — Never accept passwords for encrypted files
2. **Path traversal prevention** — Validate all input paths stay within workspace
3. **File size limits** — Default max 100MB per file (configurable)
4. **Conversion timeouts** — Kill hung LibreOffice processes after 5min
5. **Sandbox conversions** — Consider Docker/Podman wrapper for untrusted inputs

---

## Migration Path (Existing Users)

**No breaking changes** — existing workflows unchanged:

```bash
# Old workflow (still works)
lfl chunk document.md output/
lfl validate corpora/programming
lfl benchmark run corpora/programming

# New workflow (additive)
lfl ingest programming
```

Users who don't install `[all_ingest]` extras won't see any new dependencies.

---

## Future Enhancements

### v1.1
- **Table handling policies:** `--tables (inline|separate|json|skip)`
- **Batch mode:** `lfl ingest --watch` (monitor folder, auto-ingest on file add)
- **Cloud storage:** `lfl ingest --input s3://bucket/docs/`

### v1.2
- **LLM-enhanced extraction:** Use GPT-4V for complex layouts, diagrams
- **Multi-language support:** Detect language, route to appropriate chunker
- **Incremental updates:** `--incremental` (skip unchanged files via hash)

### v2.0
- **Web scraping:** `lfl ingest --url https://docs.python.org/3/`
- **Email ingestion:** `lfl ingest --imap user@host`
- **Git repo ingestion:** `lfl ingest --git https://github.com/org/repo`

---

## Acceptance Criteria

**Definition of Done:**

✅ `lfl ingest <domain>` command works with PDF, DOCX, XLSX, HTML  
✅ Pages/Numbers/Keynote support (with LibreOffice installed)  
✅ OCR fallback for scanned PDFs (with Tesseract installed)  
✅ Generated chunks have valid frontmatter  
✅ `sources.json` updated correctly  
✅ Manifest written to `ingestion_out/<domain>/manifest.json`  
✅ `--embed` flag generates embeddings  
✅ `--inventory` dry-run mode works  
✅ `.gitignore` prevents committing artifacts  
✅ Documentation updated (README, Quickstart, contributor guides)  
✅ Integration tests pass  
✅ CI enforces "no binaries" rule  

---

## Documentation Deliverables

1. **README.md** — Add "Drop-Folder Ingestion" section
2. **docs/QUICKSTART.md** — Add ingestion tutorial
3. **docs/INGESTION_GUIDE.md** — Comprehensive user guide (NEW)
4. **contributors/ARCHITECTURE.md** — Add ingestion pipeline diagram
5. **Installation guide** — Document system prerequisites

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-27 | Initial specification |

---

## Approval

**Specification Status:** ✅ Ready for Implementation  
**Estimated Effort:** 4-6 development days  
**Risk Level:** Low (additive, no breaking changes)

---

*This specification is a living document. Updates should be tracked via version number.*
