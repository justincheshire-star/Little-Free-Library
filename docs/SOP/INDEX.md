# Little Free Library — Standard Operating Procedures

**Last Updated**: February 27, 2026  
**Status**: Active  
**Scope**: Corpus curation, contribution, validation, and maintenance  
**Repository**: [Little-Free-Library](https://github.com/justincheshire-star/Little-Free-Library)

---

## 📋 SOP Directory

### Core Contribution SOPs

| SOP                                             | Purpose                                    | When to Use                         | RACI                      |
| ----------------------------------------------- | ------------------------------------------ | ----------------------------------- | ------------------------- |
| [Session Review](SESSION_REVIEW_SOP.md)         | Establish baseline at session start        | Beginning of every work session     | R=Contributor, A=Lead     |
| [Documentation](DOCUMENTATION_SOP.md)           | Maintain docs in sync with corpus changes  | Before every commit                 | R=Author, A=Maintainer    |
| [Code Review](CODE_REVIEW_SOP.md)               | Review corpus contributions and PRs        | All PRs to protected branches       | R=Reviewer, A=Maintainer  |
| [Testing](TESTING_SOP.md)                       | Validate corpus quality and metadata       | Before merging corpus contributions | R=Author, A=Maintainer    |

### Corpus Management SOPs

| SOP                                                   | Purpose                              | When to Use                        | RACI                   |
| ----------------------------------------------------- | ------------------------------------ | ---------------------------------- | ---------------------- |
| [RAG Pipeline](RAG_PIPELINE_SOP.md)                   | Ingest and validate corpus content   | Adding/updating corpora            | R=Contributor, A=Lead  |
| [Dependency Management](DEPENDENCY_MANAGEMENT_SOP.md) | Manage Python script dependencies    | Adding or updating dependencies    | R=Contributor, A=Lead  |

### Reference Documents

| Document                                              | Purpose                                  |
| ----------------------------------------------------- | ---------------------------------------- |
| [Measurement Model](MEASUREMENT_MODEL.md)             | Quality metrics and validation thresholds |
| [Session Review Template](SESSION_REVIEW_TEMPLATE.md) | Template for session summaries           |

---

## 🎯 Quick Reference

### Quality-Driven Contribution

Frame every corpus contribution with quality validation:

> **If** we add source S to corpus C, **then** quality metrics M will meet threshold T under validation V.

1. **Source**: Verify license compatibility and provenance
2. **Chunk**: Apply standardized chunking strategy
3. **Validate**: Run validation scripts
4. **Measure**: Check quality thresholds
5. **Approve**: Merge when quality ≥target

### Daily Contribution Flow

```
1. Start Session     → Run Session Review SOP
2. Select Source     → Identify content to add
3. Verify License    → Check compatibility (Tier 1/2/3)
4. Ingest/Chunk      → Use lfl ingest (drop folder) or lfl chunk (manual)
5. Validate          → Run Testing SOP (lfl validate)
6. Review            → Code Review SOP
7. Update Docs       → Documentation SOP
8. Commit            → Use commit checklist (CI guards check forbidden files)
9. End Session       → Create session summary
```

### Key Commands

| Task                   | Command                                   |
| ---------------------- | ----------------------------------------- |
| Validate corpus        | `lfl validate corpora/<domain>`           |
| Validate (strict)      | `lfl validate corpora/<domain> --strict`  |
| Ingest documents       | `lfl ingest <domain>`                     |
| Ingest dry-run         | `lfl ingest <domain> --inventory`         |
| List error codes       | `lfl error-codes`                         |
| Diagnose error code    | `lfl explain-error <code>`                |
| Validate embeddings    | `python scripts/validate_vectorset.py`    |
| Export for Hugging Face| `python scripts/ingest.py`                |
| Test pxctx integration | `python -m docs.KB.Vector_RAG.pxctx test` |
| Check forbidden files  | `python scripts/check_forbidden_files.py` |

### Quality Thresholds

| Metric                  | Target    | Gate          |
| ----------------------- | --------- | ------------- |
| Metadata completeness   | 100%      | Block merge   |
| Licensing documentation | 100%      | Block merge   |
| Source provenance       | 100%      | Block merge   |
| Chunk format compliance | 100%      | Block merge   |
| Broken cross-references | 0         | Block merge   |
| Embedding dimensions    | Consistent| Block merge   |

See [Measurement Model](MEASUREMENT_MODEL.md) for complete metrics.

---

## 📁 Documentation Structure

```
docs/
├── KB/
│   ├── Reference/              # Standard Operating Procedures (this folder)
│   │   ├── INDEX.md            # This file
│   │   ├── SESSION_REVIEW_SOP.md
│   │   ├── DOCUMENTATION_SOP.md
│   │   ├── CODE_REVIEW_SOP.md
│   │   ├── TESTING_SOP.md
│   │   ├── RAG_PIPELINE_SOP.md
│   │   ├── DEPENDENCY_MANAGEMENT_SOP.md
│   │   ├── MEASUREMENT_MODEL.md
│   │   └── SESSION_REVIEW_TEMPLATE.md
│   ├── architecture/           # Architecture documentation
│   │   └── corpus-overview.md
│   ├── tooling/                # Tool guides
│   │   └── pxctx-guide.md
│   └── Vector_RAG/             # RAG implementation
├── contributing-guide.md       # Contribution guidelines
└── licensing-guide.md          # Licensing tier documentation
```

---

## 📊 Contribution Lifecycle

```
Discover Source → Verify License → Extract Content → Chunk → Validate → PR → Review → Merge
                ↓
         (Check tier: Redistributable / Recipe / Reference)
```

**Per Contribution**:

- **Discover**: Identify high-quality source content
- **Verify**: Confirm license compatibility (Tier 1/2/3)
- **Extract**: Pull content following ethical guidelines
- **Chunk**: Apply standardized chunking with metadata
- **Validate**: Run validation scripts for quality
- **PR**: Submit with complete provenance documentation
- **Review**: Maintainer reviews quality and licensing
- **Merge**: Add to corpus with version tracking

---

## 🔄 SOP Maintenance

- **Review Cycle**: Quarterly or when processes change
- **Owner**: Repository Maintainers
- **Version Control**: All SOPs are versioned with dates
- **Updates**: Document changes in session summaries
- **Validation**: SOPs should have RACI, SLAs, and failure modes

---

## 📚 Corpus Quality Standards

### Tier 1 — Redistributable Corpora

- **Requirement**: Source license allows redistribution
- **Published**: Chunks + embeddings + metadata
- **License**: CC-BY-SA 4.0
- **Validation**: Full quality validation required

### Tier 2 — Recipe-Only Corpora

- **Requirement**: Source restricts redistribution
- **Published**: Manifests + scripts + chunking rules
- **License**: CC-BY-SA 4.0 (for manifests/scripts)
- **Validation**: Recipe validation + local build test

### Tier 3 — Reference-Only Corpora

- **Requirement**: Guidance and pointers only
- **Published**: Documentation + source links
- **License**: CC-BY-SA 4.0 (for documentation)
- **Validation**: Link validity + description accuracy

---

## 🔍 Key Principles

1. **Quality First**: Only high-quality, vetted sources
2. **License Compliance**: Strict adherence to source licenses
3. **Provenance**: Complete documentation of source origin
4. **Accessibility**: Make knowledge freely available
5. **Community**: Collaborative improvement and curation
