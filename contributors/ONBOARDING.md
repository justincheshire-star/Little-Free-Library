# Contributor Onboarding Guide

Welcome to the Little Free Library project! This guide will help you get started contributing to the toolkit.

## Table of Contents

1. [Welcome & Philosophy](#welcome--philosophy)
2. [Getting Started](#getting-started)
3. [Development Environment Setup](#development-environment-setup)
4. [Understanding the Codebase](#understanding-the-codebase)
5. [Your First Contribution](#your-first-contribution)
6. [Code Quality Standards](#code-quality-standards)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation Requirements](#documentation-requirements)
9. [Pull Request Process](#pull-request-process)
10. [Common Tasks](#common-tasks)
11. [Getting Help](#getting-help)

---

## Welcome & Philosophy

### Project Mission

Little Free Library exists to make high-quality knowledge accessible to everyone building AI systems. We believe:

- **Knowledge is a commons** — Not locked behind paywalls or APIs
- **Quality matters** — Vetted, well-structured, complete provenance
- **Transparency is key** — Open source, open data, open processes
- **Community-driven** — Built by contributors, for the community

**Completed datasets are published to:** [https://huggingface.co/LittleFreeLibrary](https://huggingface.co/LittleFreeLibrary)

### Core Values

1. **Openness** — All code, data, and processes are open
2. **Quality** — High standards for corpus content and code
3. **Accessibility** — Easy to use, well-documented, inclusive
4. **Collaboration** — Respectful, constructive communication

*Take what you need. Leave what you can.*

---

## Getting Started

### Prerequisites

**Required:**
- Python 3.8+ installed
- Git installed with **Git LFS** extension
- GitHub account
- Text editor (VS Code, PyCharm, etc.)
- ~1 GB free disk space (for embedded models)

**Recommended:**
- Familiarity with Python
- Basic understanding of RAG systems (helpful but not required)
- Command-line comfort

**Install Git LFS:**
```bash
# Debian/Ubuntu
sudo apt-get install git-lfs

# macOS
brew install git-lfs

# Windows (included with Git for Windows installer)
# Or download from: https://git-lfs.github.com/

# Initialize Git LFS
git lfs install
```

### Quick Start

```bash
# 1. Fork the repository on GitHub
# (Click "Fork" button at https://github.com/little-free-library/lfl)

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/Little-Free-Library.git
cd Little-Free-Library

# 3. Download embedded models (~796 MB via Git LFS)
git lfs pull

# 4. Add upstream remote
git remote add upstream https://github.com/little-free-library/lfl.git

# 5. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# 6. Install in development mode (includes both embedding systems)
pip install -r requirements.txt
pip install -e .

# 7. Test embedding models (optional but recommended)
python scripts/test_embeddings.py

# 8. Verify installation
lfl version

# 9. Create a branch for your work
git checkout -b feature/my-contribution
```

You're ready to contribute! 🎉

---

## Development Environment Setup

### Recommended Setup

**VS Code Extensions:**
- Python (Microsoft)
- Pylance (Microsoft)
- Black Formatter
- isort
- Markdown All in One

**Configuration (.vscode/settings.json):**

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### Install Development Dependencies

```bash
# Core dependencies + embedding libraries (included in requirements.txt)
pip install -r requirements.txt
pip install -e .

# Full development install (includes ingestion + dev tools)
pip install -e ".[all_ingest,dev]"

# Development tools (if not using the dev extra)
pip install black isort flake8 pytest pytest-cov

# Documentation tools (if contributing to docs)
pip install sphinx sphinx-rtd-theme myst-parser
```

### Embedded Models

The repository includes **two embedding systems** (~796 MB total, tracked via Git LFS):

**FastEmbed (ONNX)** - Lightweight, cross-platform (~273 MB)
- `bge-small-en-v1.5` (384-dim) - Fast baseline
- `bge-base-en-v1.5` (768-dim) - Better quality
- No PyTorch required, works on any CPU

**Sentence-Transformers (PyTorch)** - Full-featured, GPU-optimized (~523 MB)
- `nomic-embed-text-v1.5` (768-dim) - Apache 2.0 licensed
- Fine-tuning capable, CUDA optimization

Both are installed by default when you run `pip install -r requirements.txt`.

**Test your embedding setup:**
```bash
python scripts/test_embeddings.py
```

Expected output:
```
✓ ALL TESTS PASSED
Both embedding systems are working correctly with local models.
```

See **[docs/EMBEDDING_SETUP.md](../docs/EMBEDDING_SETUP.md)** for detailed usage, comparison, and troubleshooting.

### Verify Setup

```bash
# Check Python version
python --version  # Should be 3.8+

# Check installed packages
pip list | grep -E "(pyyaml|numpy|typer|black)"

# Run version command
lfl version

# Check import works
python -c "import lfl; print(lfl.__version__)"
```

---

## Understanding the Codebase

### Repository Structure

```
Little-Free-Library/
├── lfl/                          # Main package
│   ├── __init__.py              # Public API exports
│   ├── chunking.py              # Document chunking
│   ├── corpus_validation.py     # Corpus validation
│   ├── embeddings.py            # Vector embeddings
│   ├── retrieval.py             # Hybrid retrieval
│   ├── profiles.py              # Embedding profiles
│   ├── cli.py                   # Main CLI
│   ├── ingest/                  # Drop-folder ingestion pipeline
│   │   ├── types.py             # Dataclasses (DiscoveredFile, ExtractedDoc, etc.)
│   │   ├── detect.py            # MIME detection, SHA256 hashing, file discovery
│   │   ├── convert.py           # LibreOffice headless conversion
│   │   ├── extract.py           # Format extractors (PDF, DOCX, XLSX, HTML, TXT)
│   │   └── pipeline.py          # 9-stage orchestration
│   └── profiles/                # Profile configs
│
├── corpora/                     # Knowledge corpora
│   └── programming/             # Programming corpus
│       ├── CORPUS.md           # Corpus manifest
│       ├── sources.json        # Source provenance
│       └── chunks/             # Chunk files
│
├── ingestion/                   # Drop folder for raw documents (gitignored)
├── ingestion_out/               # Ingestion artifacts/manifests (gitignored)
│
├── docs/                        # Documentation
│   ├── KB/                     # Knowledge base
│   ├── SOP/                    # Standard operating procedures
│   ├── api/                    # Sphinx API docs
│   └── QUICKSTART.md           # Quick start guide
│
├── scripts/                     # Utility scripts
│   ├── check_forbidden_files.py # Pre-commit file guard
│   ├── validate_corpus.py      # Corpus validation
│   └── ingest.py               # HF export script
│
├── .github/workflows/           # CI workflows
│   └── validate-files.yml      # Forbidden files + corpus validation
│
├── tests/                       # Test suite (if exists)
├── setup.py                     # Package setup
├── requirements.txt             # Dependencies
├── CHANGELOG.md                # Version history
└── README.md                   # Project overview
```

### Key Modules Overview

| Module | Purpose | Lines | Complexity |
|--------|---------|-------|------------|
| `chunking.py` | Document → chunks | 591 | Medium |
| `corpus_validation.py` | Validate metadata | 351 | Medium |
| `embeddings.py` | Generate vectors | 287 | Low |
| `retrieval.py` | Hybrid search | 247 | Medium |
| `profiles.py` | Profile management | 130 | Low |
| `cli.py` | CLI interface | 273 | Medium |
| `ingest/detect.py` | MIME detection + discovery | 162 | Low |
| `ingest/convert.py` | LibreOffice wrappers | 114 | Low |
| `ingest/extract.py` | Format extractors | 284 | Medium |
| `ingest/pipeline.py` | Ingestion orchestration | 452 | High |

### Code Flow for Common Operations

**Chunking a Document:**

```
User runs: lfl chunk input.md output/
    ↓
cli.py:cmd_chunk()
    ↓
chunking.py:chunk_document()
    ↓
chunking.py:chunk_heading_aware()  # or other strategy
    ↓
chunking.py:save_chunk_to_markdown()
    ↓
Output: chunk_001.md with YAML frontmatter
```

**Validating a Corpus:**

```
User runs: lfl validate corpora/programming
    ↓
cli.py:cmd_validate()
    ↓
corpus_validation.py:validate_corpus()
    ↓
corpus_validation.py:validate_chunk()  # for each chunk
corpus_validation.py:validate_sources_json()
corpus_validation.py:check_source_references()
    ↓
Output: Validation report (pass/fail + errors)
```

**Ingesting Documents (Drop-Folder):**

```
User runs: lfl ingest programming
    ↓
cli.py:cmd_ingest()
    ↓
ingest/pipeline.py:ingest_directory()
    ↓
  Stage 1: ingest/detect.py:discover_files()      # Scan and classify files
  Stage 2: ingest/convert.py:convert_with_libreoffice()  # Convert if needed
  Stage 3: ingest/extract.py:extract_text()        # PDF/DOCX/XLSX/HTML/TXT
  Stage 4: chunking.py:chunk_document()            # Chunk with YAML frontmatter
  Stage 5: Write chunks to corpora/<domain>/chunks/
  Stage 6: Update sources.json with provenance
  Stage 7: corpus_validation.py:validate_corpus()  # Validate output
  Stage 8: embeddings.py (optional, if --embed)    # Generate vectors
  Stage 9: Write manifest to ingestion_out/<domain>/manifest.json
    ↓
Output: Corpus-ready chunks + sources.json + manifest
```

---

## Your First Contribution

### Good First Issues

Look for issues labeled:
- `good-first-issue` — Perfect for newcomers
- `documentation` — Improve docs
- `help-wanted` — Community input needed
- `bug` — Fix a bug

### Contribution Ideas

**Easy (1-2 hours):**
- Fix typos in documentation
- Add examples to docstrings
- Improve error messages
- Add tests for existing functions

**Medium (3-6 hours):**
- Implement new chunking strategy
- Add new embedding profile
- Improve validation checks
- Enhance CLI help text

**Advanced (1+ days):**
- Optimize retrieval performance
- Add new retrieval mode
- Implement cross-lingual support
- Build web UI for corpus exploration

### Step-by-Step: Your First PR

#### 1. Pick an Issue

Browse issues at https://github.com/little-free-library/lfl/issues

Comment: "I'd like to work on this!" to claim it.

#### 2. Create a Branch

```bash
git checkout -b feature/add-new-chunking-strategy
# or
git checkout -b fix/validation-error-message
# or
git checkout -b docs/improve-quickstart
```

Branch naming: `feature/` for features, `fix/` for bugs, `docs/` for documentation.

#### 3. Make Your Changes

Edit the relevant files. Keep changes focused on one issue.

```bash
# Example: Adding a new function to chunking.py
vim lfl/chunking.py

# Add your function with complete docstring
def chunk_by_sentences(content, metadata, max_sentences=5):
    """
    Chunk document by sentences.
    
    Parameters
    ----------
    content : str
        Document content
    metadata : dict
        Chunk metadata
    max_sentences : int, optional
        Maximum sentences per chunk (default: 5)
    
    Returns
    -------
    list of dict
        List of chunks with metadata
    """
    # Implementation here
    pass
```

#### 4. Format Your Code

```bash
# Auto-format with black
black lfl/chunking.py

# Sort imports with isort
isort lfl/chunking.py

# Check linting
flake8 lfl/chunking.py
```

#### 5. Test Your Changes

```bash
# Manual testing
python -c "from lfl.chunking import chunk_by_sentences; print('Import works!')"

# Run existing tests
python -m pytest tests/ -v

# Test CLI if relevant
lfl chunk test.md output/ --strategy sentence
```

#### 6. Update Documentation

If you added a feature, update:
- Docstrings (in code)
- README.md (if user-facing)
- CHANGELOG.md (add entry under "Unreleased")
- docs/api/ (if Sphinx docs exist)

#### 7. Commit Your Changes

```bash
git add lfl/chunking.py
git add CHANGELOG.md
git commit -m "feat: Add sentence-based chunking strategy

- Implement chunk_by_sentences() function
- Add configurable max_sentences parameter
- Include comprehensive docstring
- Update CHANGELOG.md

Closes #42"
```

Commit message format:
```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

#### 8. Push and Create PR

```bash
git push origin feature/add-new-chunking-strategy
```

Go to GitHub, click "Create Pull Request"

PR template:

```markdown
## Description
Brief description of changes.

## Motivation
Why is this change needed? What problem does it solve?

## Changes
- List of specific changes
- Each on its own line

## Testing
How did you test this? Include commands or code snippets.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Added/updated tests
- [ ] Added/updated documentation
- [ ] CHANGELOG.md updated
- [ ] All tests passing
- [ ] No merge conflicts

## Related Issues
Closes #42
```

#### 9. Respond to Feedback

Maintainers will review your PR. Address comments:

```bash
# Make requested changes
vim lfl/chunking.py

# Commit updates
git add lfl/chunking.py
git commit -m "refactor: Improve error handling per review"

# Push updates
git push origin feature/add-new-chunking-strategy
```

#### 10. Celebrate! 🎉

Once merged, your contribution is part of the project!

Update your fork:

```bash
git checkout main
git pull upstream main
git push origin main
```

---

## Code Quality Standards

### Python Style

- **PEP 8 compliant** — Use black formatter
- **Type hints** — Add type annotations where helpful
- **Docstrings** — NumPy or Google style for all public functions
- **Imports** — Sorted with isort

### Docstring Example

```python
def chunk_document(content, strategy="heading_aware", chunk_size=500, metadata=None):
    """
    Chunk document using specified strategy.
    
    Parameters
    ----------
    content : str
        Raw document content (markdown format)
    strategy : str, optional
        Chunking strategy (default: "heading_aware")
        Options: "naive_paragraph", "heading_aware", "sliding_window", "semantic"
    chunk_size : int, optional
        Target chunk size in tokens (default: 500)
    metadata : dict, optional
        Chunk metadata (domain, source, license, etc.)
    
    Returns
    -------
    list of dict
        List of chunks with complete metadata
    
    Raises
    ------
    ValueError
        If strategy is not recognized
    
    Examples
    --------
    >>> chunks = chunk_document(content, strategy="heading_aware", chunk_size=500)
    >>> print(f"Created {len(chunks)} chunks")
    Created 12 chunks
    
    See Also
    --------
    chunk_heading_aware : Heading-based chunking implementation
    chunk_sliding_window : Sliding window implementation
    """
    # Implementation
    pass
```

### Error Handling

```python
# Good: Specific exceptions with helpful messages
if strategy not in VALID_STRATEGIES:
    raise ValueError(
        f"Unknown chunking strategy: '{strategy}'. "
        f"Valid options: {', '.join(VALID_STRATEGIES)}"
    )

# Bad: Generic exception
if strategy not in VALID_STRATEGIES:
    raise Exception("Invalid strategy")
```

### Code Organization

```python
# File structure order:
# 1. Module docstring
# 2. Imports (stdlib, third-party, local)
# 3. Constants
# 4. Helper functions
# 5. Main functions
# 6. CLI bindings (if applicable)

"""
Chunking module for document segmentation.

This module provides multiple strategies for splitting documents
into corpus-ready chunks.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
import yaml

# Constants
DEFAULT_CHUNK_SIZE = 500
MIN_CHUNK_SIZE = 50
MAX_CHUNK_SIZE = 1000

# Helper functions (private)
def _extract_title(content: str) -> Optional[str]:
    """Extract title from content (private helper)."""
    pass

# Main functions (public API)
def chunk_document(content: str, strategy: str = "heading_aware") -> List[Dict]:
    """Chunk document (public API)."""
    pass
```

---

## Testing Guidelines

### Writing Tests

```python
# tests/test_chunking.py
import pytest
from lfl.chunking import chunk_document

def test_chunk_document_basic():
    """Test basic chunking functionality."""
    content = "# Heading 1\n\nParagraph 1.\n\n## Heading 2\n\nParagraph 2."
    metadata = {"domain": "test"}
    
    chunks = chunk_document(content, strategy="heading_aware", metadata=metadata)
    
    assert len(chunks) > 0
    assert all("title" in chunk for chunk in chunks)
    assert all("text" in chunk for chunk in chunks)

def test_chunk_document_invalid_strategy():
    """Test error handling for invalid strategy."""
    content = "Test content"
    
    with pytest.raises(ValueError, match="Unknown chunking strategy"):
        chunk_document(content, strategy="nonexistent")

def test_chunk_sliding_window_overlap():
    """Test sliding window with overlap."""
    content = "word " * 100  # 100 words
    
    chunks = chunk_document(
        content,
        strategy="sliding_window",
        chunk_size=200,
        overlap=50
    )
    
    assert len(chunks) > 1
    # Verify overlap exists between consecutive chunks
    for i in range(len(chunks) - 1):
        text1 = chunks[i]["text"]
        text2 = chunks[i+1]["text"]
        # Check for some overlap
        assert any(word in text2 for word in text1.split()[-10:])
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_chunking.py -v

# Run specific test
pytest tests/test_chunking.py::test_chunk_document_basic -v

# Run with coverage
pytest tests/ --cov=lfl --cov-report=html
```

### Manual Testing

```bash
# Test chunking
echo "# Test\\n\\nContent" > test.md
lfl chunk test.md output/
ls output/

# Test validation
lfl validate corpora/programming

# Test retrieval
python -c "
from lfl.retrieval import HybridRetriever
r = HybridRetriever('corpora/programming', mode='bm25')
results = r.retrieve('test query', top_k=3)
for res in results: print(res.title)
"
```

---

## Documentation Requirements

### What to Document

- **All public functions** — Complete docstrings
- **CLI commands** — Help text and examples
- **New features** — Update README.md
- **Changes** — Add to CHANGELOG.md
- **Complex logic** — Inline comments

### Documentation Checklist

When contributing code:

- [ ] Docstrings added/updated
- [ ] README.md updated (if user-facing feature)
- [ ] CHANGELOG.md updated (add entry under "Unreleased")
- [ ] Examples added (in docstring or examples.rst)
- [ ] API docs updated (if Sphinx docs exist)
- [ ] Architecture diagrams updated (if architecture changed)

### Building Sphinx Docs

```bash
cd docs/api
pip install -r requirements.txt
make html
make serve  # View at http://localhost:8000
```

---

## Pull Request Process

### Before Submitting

1. ✅ Code follows style guidelines (run black, isort, flake8)
2. ✅ Tests added/updated and passing
3. ✅ Documentation updated
4. ✅ CHANGELOG.md updated
5. ✅ No merge conflicts with main branch
6. ✅ Commits have clear messages

### PR Review Criteria

Reviewers will check:

- **Functionality** — Does it work as intended?
- **Code quality** — Is it clean, readable, maintainable?
- **Tests** — Are there sufficient tests?
- **Documentation** — Is it well-documented?
- **Consistency** — Does it match existing patterns?
- **Performance** — Does it introduce slowdowns?

### Typical Review Timeline

- **Initial review**: 1-3 days
- **Follow-up reviews**: 1-2 days per iteration
- **Merge**: After approval from maintainers

### After Merge

Your contribution is live! 🎉

Update your local copy:

```bash
git checkout main
git pull upstream main
git branch -d feature/your-branch  # Delete local branch
git push origin --delete feature/your-branch  # Delete remote branch
```

---

## Common Tasks

### Adding a New Chunking Strategy

1. **Add implementation** to `lfl/chunking.py`:

```python
def chunk_my_strategy(content, chunk_size, metadata):
    """Implement your strategy."""
    # Your implementation
    return chunks
```

2. **Register strategy** in `chunk_document()`:

```python
CHUNKING_STRATEGIES = {
    "naive_paragraph": chunk_naive_paragraph,
    "heading_aware": chunk_heading_aware,
    "sliding_window": chunk_sliding_window,
    "my_strategy": chunk_my_strategy,  # Add here
}
```

3. **Update CLI** in `lfl/cli.py`:

```python
@click.option("--strategy", type=click.Choice([
    "naive_paragraph", "heading_aware", "sliding_window", "my_strategy"
]), default="heading_aware")
```

4. **Add tests**, update docs, update CHANGELOG.md

### Adding a New Embedding Profile

1. **Create JSON** in `lfl/profiles/my_profile.json`:

```json
{
  "name": "my_profile",
  "model_name": "my-embedding-model",
  "dimensions": 768,
  "max_seq_len": 512,
  "backend": "fastembed",
  "hardware": "cpu",
  "description": "Description of profile"
}
```

2. **Test loading**:

```python
from lfl.profiles import load_profile
profile = load_profile("my_profile")
print(profile)
```

3. **Update docs**: Add to embedding profiles table in README.md

### Adding a Validation Check

1. **Add check** to `lfl/corpus_validation.py`:

```python
def validate_chunk(chunk_data, chunk_filename):
    """Validate chunk metadata."""
    errors = []
    
    # Existing checks...
    
    # Your new check
    if "my_field" not in chunk_data:
        errors.append("Missing required field: my_field")
    
    return errors
```

2. **Test validation**, update docs

---

## Getting Help

### Resources

- **Documentation**: [README.md](../../README.md), [QUICKSTART.md](QUICKSTART.md)
- **API Reference**: [docs/api/](api/)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Examples**: [docs/api/examples.rst](api/examples.rst)

### Ask Questions

- **GitHub Discussions**: https://github.com/little-free-library/lfl/discussions
- **GitHub Issues**: https://github.com/little-free-library/lfl/issues
- **Tag maintainers**: @username in issues/PRs

### Community Guidelines

- Be respectful and constructive
- Ask questions — there are no "dumb" questions
- Share what you learn
- Help others when you can

### Maintainer Contact

For urgent issues or questions, tag maintainers in GitHub.

---

## Congratulations! 🎉

You're now ready to contribute to Little Free Library!

**Next Steps:**
1. Browse [good-first-issue](https://github.com/little-free-library/lfl/labels/good-first-issue) tickets
2. Set up your development environment
3. Make your first contribution
4. Join discussions and help others

*Take what you need. Leave what you can.*

---

**Version**: 1.0.0  
**Last Updated**: February 26, 2026  
**Maintainers**: Little Free Library Contributors
