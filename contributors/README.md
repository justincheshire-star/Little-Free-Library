# Contributors Documentation

Welcome to the Little Free Library contributor documentation! This directory contains all the resources you need to contribute to the project.

**Completed datasets:** [https://huggingface.co/LittleFreeLibrary](https://huggingface.co/LittleFreeLibrary)

## Quick Links

### Getting Started
- **[Onboarding Guide](ONBOARDING.md)** — Complete guide from setup to your first PR
- **[Contributing Guide](CONTRIBUTING_GUIDE.md)** — Contribution policies and workflows
- **[Main CONTRIBUTING.md](../CONTRIBUTING.md)** — High-level contribution overview

### Ingestion & Tooling
- **[Ingestion System Spec](../docs/KB/INGESTION_SYSTEM_SPEC.md)** — Drop-folder ingestion design and usage
- **[QUICKSTART.md](../docs/QUICKSTART.md)** — Full CLI tutorial (validate, ingest, benchmark)
- **[Embedding Setup Guide](../docs/EMBEDDING_SETUP.md)** — Configure and use embedded models

### Technical Documentation
- **[Architecture](ARCHITECTURE.md)** — System architecture with diagrams
- **[Benchmarking Guide](BENCHMARKING_GUIDE.md)** — Understanding and optimizing corpus quality
- **[API Documentation](../docs/api/)** — Sphinx-generated API reference

### Standard Operating Procedures (SOPs)
- **[Code Review SOP](../docs/SOP/CODE_REVIEW_SOP.md)** — Code review standards
- **[Documentation SOP](../docs/SOP/DOCUMENTATION_SOP.md)** — Documentation requirements
- **[Testing SOP](../docs/SOP/TESTING_SOP.md)** — Testing standards
- **[Session Review SOP](../docs/SOP/SESSION_REVIEW_SOP.md)** — Session review process
- **[All SOPs](../docs/SOP/INDEX.md)** — Complete SOP index

---

## Documentation Overview

### 📘 [Onboarding Guide](ONBOARDING.md)

**Start here if you're new!** This comprehensive guide covers:
- Development environment setup
- Understanding the codebase
- Your first contribution (step-by-step)
- Code quality standards
- Testing guidelines
- Pull request process
- Common tasks (adding chunking strategies, profiles, etc.)

**Length:** ~780 lines  
**Time to read:** 30-45 minutes

### 🏗️ [Architecture](ARCHITECTURE.md)

**Visual guide to system design.** Includes:
- 8 comprehensive Mermaid diagrams
- System overview and data pipeline
- Chunking strategies comparison
- Hybrid retrieval architecture
- Validation and benchmarking flows
- Design principles and patterns

**Length:** ~860 lines  
**Time to read:** 45-60 minutes

### 📊 [Benchmarking Guide](BENCHMARKING_GUIDE.md)

**Deep dive into corpus quality metrics.** Learn:
- How benchmarking works (synthetic queries)
- Metrics explained (Recall@k, MRR, Token Efficiency)
- Interpreting results and diagnostics
- 6 concrete optimization strategies
- Troubleshooting common issues
- 2 detailed case studies

**Length:** ~1,250 lines  
**Time to read:** 60-90 minutes

### 📝 [Contributing Guide](CONTRIBUTING_GUIDE.md)

**Contribution policies and workflows.** Covers:
- Types of contributions (corpora, code, documentation)
- Quality standards for each contribution type
- Licensing requirements (critical!)
- Review process and expectations
- Community guidelines

**Length:** Varies  
**Time to read:** 20-30 minutes

---

## Recommended Reading Path

### Path 1: Quick Start (New Contributors)
1. [Onboarding Guide](ONBOARDING.md) — Setup and first PR
2. [Contributing Guide](CONTRIBUTING_GUIDE.md) — Policies
3. Pick an issue and start contributing!

### Path 2: Technical Deep Dive (Code Contributors)
1. [Onboarding Guide](ONBOARDING.md) — Setup
2. [Architecture](ARCHITECTURE.md) — System design
3. [API Documentation](../docs/api/) — Module reference
4. [Code Review SOP](../docs/SOP/CODE_REVIEW_SOP.md) — Standards
5. Start coding!

### Path 3: Corpus Contributor (Content Contributors)
1. [Contributing Guide](CONTRIBUTING_GUIDE.md) — Licensing requirements
2. [Ingestion System Spec](../docs/KB/INGESTION_SYSTEM_SPEC.md) — Drop-folder workflow
3. [Benchmarking Guide](BENCHMARKING_GUIDE.md) — Quality metrics
3. [Documentation SOP](../docs/SOP/DOCUMENTATION_SOP.md) — Metadata requirements
4. Create your corpus!

### Path 4: Maintainer/Reviewer (Advanced)
1. All of the above
2. [Session Review SOP](../docs/SOP/SESSION_REVIEW_SOP.md)
3. [All SOPs](../docs/SOP/INDEX.md)

---

## Quick Reference

### Common Tasks

**Set up development environment:**
```bash
git clone https://github.com/YOUR_USERNAME/Little-Free-Library.git
cd Little-Free-Library
python -m venv venv
source venv/bin/activate
pip install -e ".[all_ingest,dev]"
lfl version
```

**Run tests:**
```bash
pytest tests/ -v
lfl validate corpora/programming
lfl benchmark run corpora/programming
```

**Ingest documents:**
```bash
mkdir -p ingestion/my_domain
cp ~/Documents/*.pdf ingestion/my_domain/
lfl ingest my_domain --inventory   # dry-run
lfl ingest my_domain               # full run
```

**Build documentation:**
```bash
cd docs/api
pip install -r requirements.txt
make html
make serve
```

**Create a contribution:**
```bash
git checkout -b feature/my-contribution
# Make changes...
black lfl/
isort lfl/
pytest tests/ -v
git add .
git commit -m "feat: Add cool feature"
git push origin feature/my-contribution
# Open PR on GitHub
```

### Getting Help

- **Questions?** Open a [Discussion](https://github.com/little-free-library/lfl/discussions)
- **Bug found?** Open an [Issue](https://github.com/little-free-library/lfl/issues)
- **Need guidance?** Tag maintainers in your issue/PR
- **Community:** Join discussions, help others, share learnings

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Be respectful, constructive, and helpful. See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

## Project Structure

```
Little-Free-Library/
├── contributors/              # 📍 You are here
│   ├── README.md             # This file
│   ├── ONBOARDING.md         # New contributor guide
│   ├── ARCHITECTURE.md       # System architecture
│   ├── BENCHMARKING_GUIDE.md # Quality metrics guide
│   └── CONTRIBUTING_GUIDE.md # Contribution policies
│
├── lfl/                      # Main package
│   ├── chunking.py           # Document chunking
│   ├── corpus_validation.py  # Corpus validation
│   ├── embeddings.py         # Vector embeddings
│   ├── retrieval.py          # Hybrid retrieval
│   └── ingest/               # Drop-folder ingestion pipeline
│       ├── detect.py         # MIME detection + discovery
│       ├── convert.py        # LibreOffice conversion
│       ├── extract.py        # PDF/DOCX/XLSX/HTML/TXT extractors
│       └── pipeline.py       # 9-stage ingestion orchestration
│
├── corpora/                  # Knowledge corpora
│   └── programming/          # Programming corpus
│
├── ingestion/                # Drop folder for raw documents (gitignored)
├── ingestion_out/            # Ingestion artifacts (gitignored)
│
├── docs/                     # Documentation
│   ├── api/                  # Sphinx API docs
│   ├── KB/                   # Knowledge base
│   ├── SOP/                  # Standard operating procedures
│   └── QUICKSTART.md         # User quick start
│
├── scripts/                  # Utility scripts
├── tests/                    # Test suite
├── CONTRIBUTING.md           # High-level contribution guide
├── CHANGELOG.md              # Version history
└── README.md                 # Project overview
```

---

## Statistics

**Documentation volume:**
- Onboarding Guide: ~780 lines
- Architecture: ~860 lines
- Benchmarking Guide: ~1,250 lines
- Total contributor docs: ~4,400 lines

**Repository size:**
- Production code: ~3,500 lines (lfl/ including ingest/)
- Documentation: ~8,000+ lines
- Test coverage: Growing

---

## Version

**Documentation Version:** 1.1.0  
**Last Updated:** February 27, 2026  
**Maintained By:** Little Free Library Contributors

---

*Take what you need. Leave what you can.*

**Ready to contribute? Start with the [Onboarding Guide](ONBOARDING.md)!**
