# Corpus Validation & Testing SOP

**Status**: Active  
**Owner**: Repository Maintainers  
**Version**: 2.0.0  
**Last Updated**: February 25, 2026  
**Trigger**: Before merging corpus contributions or script changes  
**RACI**: R=Contributor, A=Maintainer, C=Reviewers, I=Community

---

## 🎯 Purpose

Establish validation standards for Little Free Library corpora and infrastructure scripts. Ensures corpus quality, metadata completeness, licensing compliance, and provenance accuracy.

---

## 🔬 Quality-Driven Contribution

Frame every corpus contribution with validation criteria:

> **If** we add source S to corpus C, **then** validation metrics M will meet threshold T under checks V.

**Validation Flow**:

1. Verify license compliance (Tier 1/2/3)
2. Run metadata validation
3. Check chunk formatting
4. Validate provenance documentation
5. Test embedding dimensions (if applicable)
6. **Approve** when all validations pass

**Example**:

```
Contribution: Add Python asyncio docs to programming corpus
Validation: All chunks have complete metadata, source in sources.json
Threshold: 100% metadata completeness, 100% provenance
Result: Merge if all checks pass
```

---

## 🧪 Validation Architecture

```
scripts/
├── validate_corpus.py        # Corpus metadata & schema validation
├── validate_vectorset.py     # Embedding validation
└── ingest.py                 # Corpus ingestion with validation
```

---

## 📋 Validation Categories

| Category             | Script                     | Purpose                          | Speed  |
| -------------------- | -------------------------- | -------------------------------- | ------ |
| Metadata             | `validate_corpus.py`       | Check metadata completeness      | Fast   |
| Schema               | `validate_corpus.py`       | Validate YAML frontmatter        | Fast   |
| Licensing            | `validate_corpus.py`       | Check license documentation      | Fast   |
| Provenance           | `validate_corpus.py`       | Verify sources.json entries      | Fast   |
| Embeddings           | `validate_vectorset.py`    | Check embedding dimensions       | Medium |
| Integration          | `ingest.py --dry-run`      | Test full ingestion pipeline     | Medium |

---

## 1. Running Validations

### 1.1 Quick Commands

```bash
# Validate all corpora
python scripts/validate_corpus.py

# Validate specific corpus
python scripts/validate_corpus.py --corpus corpora/programming

# Strict mode (fail on warnings)
python scripts/validate_corpus.py --strict

# Validate embeddings
python scripts/validate_vectorset.py

# Dry-run ingestion test
python scripts/ingest.py --dry-run
```

### 1.2 Validation Markers

If using pytest for script tests:

```bash
# Run only validation tests
pytest -m validation

# Run only metadata tests
pytest -m metadata

# Skip slow tests
pytest -m "not slow"
```

---

## 2. Validation Requirements

### 2.1 Metadata Validation

**Required fields in every chunk**:

```yaml
---
title: "Required - descriptive title"
domain: "Required - matches corpus domain"
subdomain: "Required - organizational subdivision"
source: "Required - original source URL"
source_license: "Required - license identifier"
source_id: "Required - matches sources.json entry"
source_path: "Required - path within source"
retrieved_at: "Required - YYYY-MM-DD format"
verified: "Required - documented|automated|manual"
importance: "Optional - 0.0-1.0 quality signal"
---
```

**Validation checks**:

- [ ] All required fields present
- [ ] `domain` matches corpus domain
- [ ] `source_id` exists in sources.json
- [ ] `retrieved_at` is valid ISO date
- [ ] `verified` is one of allowed values
- [ ] `importance` is float 0.0-1.0 (if present)

### 2.2 Provenance Validation

**Required in sources.json**:

```json
{
  "source_id": "matching chunk metadata",
  "title": "Human-readable source name",
  "url": "https://accessible-url",
  "license": "Valid license identifier",
  "license_url": "https://license-text-url",
  "tier": 1|2|3,
  "retrieved_at": "YYYY-MM-DD",
  "verified": "documented|automated|manual",
  "notes": "Optional context"
}
```

**Validation checks**:

- [ ] All chunks reference sources in sources.json
- [ ] All source_ids in sources.json are used
- [ ] URLs are accessible (optional check)
- [ ] License is valid SPDX identifier
- [ ] Tier classification is correct

### 2.3 Licensing Validation

**Tier classification**:

- **Tier 1**: Source allows redistribution → chunks published
- **Tier 2**: Source restricts redistribution → recipe only
- **Tier 3**: Reference only → documentation only

**Validation checks**:

- [ ] Tier matches source license permissions
- [ ] Attribution requirements documented
- [ ] License compatibility verified
- [ ] No prohibited licenses (GPL, AGPL, SSPL)

### 2.4 Chunk Format Validation

**Structure**:

```markdown
---
[YAML metadata]
---

# Optional heading

Content paragraphs...
```

**Validation checks**:

- [ ] Valid YAML frontmatter
- [ ] Content after frontmatter
- [ ] No PII or sensitive data
- [ ] Reasonable content length (> 50 chars)
- [ ] UTF-8 encoding
- [ ] No binary content

### 2.5 Embedding Validation

If embeddings included:

- [ ] Consistent dimensions across corpus
- [ ] No NaN or infinite values
- [ ] Normalized vectors (if required)
- [ ] Matches expected embedding model

---

## 3. Validation Thresholds

### 3.1 Quality Gates

| Metric                  | Target | Gate          |
| ----------------------- | ------ | ------------- |
| Metadata completeness   | 100%   | Block merge   |
| Provenance coverage     | 100%   | Block merge   |
| License documentation   | 100%   | Block merge   |
| Schema validity         | 100%   | Block merge   |
| Source accessibility    | 95%    | Warn          |
| Embedding consistency   | 100%   | Block merge   |

### 3.2 Per-Contribution Targets

- **New corpus**: All validations at 100%
- **Add sources**: Incremental validations at 100%
- **Update chunks**: Affected chunks at 100%
- **Infrastructure**: Scripts pass tests

---

## 4. Writing Validation Tests

### 4.1 Test Structure (if using pytest)

```python
"""Corpus validation tests."""
import pytest
from scripts.validate_corpus import validate_metadata, validate_sources

class TestCorpusValidation:
    """Corpus validation test suite."""

    def test_metadata_completeness(self):
        """All chunks should have complete metadata."""
        result = validate_metadata("corpora/programming")
        assert result.completeness == 1.0

    def test_source_provenance(self):
        """All source_ids should exist in sources.json."""
        result = validate_sources("corpora/programming")
        assert result.orphan_chunks == []

    def test_license_compliance(self):
        """All sources should have valid licenses."""
        result = validate_sources("corpora/programming")
        assert all(s.license for s in result.sources)
```

### 4.2 Validation Script Output

**Expected format**:

```
Validating corpus: programming
✓ Metadata: 100% complete (42/42 chunks)
✓ Provenance: 100% documented (5/5 sources)
✓ Licensing: 100% compliant (5/5 sources)
✓ Schema: 100% valid (42/42 chunks)
✓ Embeddings: Consistent dimensions (768)

Summary: PASS - All validations successful
```

**Error format**:

```
Validating corpus: programming
✗ Metadata: 95% complete (40/42 chunks)
  - Missing 'source_path' in chunk_012.md
  - Missing 'retrieved_at' in chunk_027.md
✓ Provenance: 100% documented (5/5 sources)
✗ Licensing: 80% compliant (4/5 sources)
  - Unknown license 'Custom' for source python_stdlib

Summary: FAIL - Fix 3 issues before merge
```

---

## 5. Pre-Merge Validation Checklist

### For Corpus Contributions

- [ ] Run `python scripts/validate_corpus.py --corpus <path>`
- [ ] All metadata fields complete
- [ ] All sources in sources.json
- [ ] All licenses documented
- [ ] No validation errors
- [ ] Warnings reviewed and justified

### For Script Contributions

- [ ] Script runs without errors
- [ ] Help text complete (`--help`)
- [ ] Error handling for invalid input
- [ ] Docstrings complete
- [ ] Test cases added (if applicable)

---

## 6. Continuous Validation

### 6.1 CI Integration (Future)

```yaml
# .github/workflows/validate.yml
name: Validate Corpora
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Validate corpora
        run: python scripts/validate_corpus.py --strict
```

### 6.2 Pre-Commit Hooks (Optional)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-corpus
        name: Validate corpus changes
        entry: python scripts/validate_corpus.py
        language: system
        pass_filenames: false
```

---

## 7. Common Validation Failures

### Issue: Missing metadata field

**Error**: `Missing 'source_license' in chunk_042.md`  
**Fix**: Add required field to YAML frontmatter  
**Prevention**: Use chunk template when creating chunks

### Issue: Orphan source_id

**Error**: `source_id 'python_docs' not found in sources.json`  
**Fix**: Add missing source entry to sources.json  
**Prevention**: Run validation before commit

### Issue: Invalid license

**Error**: `Unknown license 'Custom' for source X`  
**Fix**: Use valid SPDX license identifier  
**Prevention**: Check license against SPDX list

### Issue: Inconsistent embedding dimensions

**Error**: `Embedding dimension mismatch: expected 768, got 384`  
**Fix**: Regenerate embeddings with correct model  
**Prevention**: Document embedding model in CORPUS.md

### Issue: Unicode encoding error

**Error**: `Invalid UTF-8 in chunk_123.md`  
**Fix**: Re-save file with UTF-8 encoding  
**Prevention**: Configure editor for UTF-8

---

## 8. Validation Metrics Tracking

Track over time (optional):

| Metric                     | Target | Current |
| -------------------------- | ------ | ------- |
| Metadata completeness      | 100%   | —       |
| Source documentation       | 100%   | —       |
| License compliance         | 100%   | —       |
| Validation pass rate       | 100%   | —       |
| Average validation time    | <10s   | —       |

---

## 9. Troubleshooting

### Validation script not finding corpus

**Symptom**: `Corpus not found: corpora/programming`  
**Check**:
1. Verify path is correct
2. Ensure CORPUS.md exists in directory
3. Check working directory

### sources.json parse error

**Symptom**: `JSON decode error in sources.json`  
**Check**:
1. Validate JSON syntax (use JSON linter)
2. Check for trailing commas
3. Ensure UTF-8 encoding

### Validation extremely slow

**Symptom**: Validation takes > 1 minute  
**Check**:
1. Corpus size (thousands of chunks?)
2. Network check for URL validation
3. Consider validating changed files only

---

## 10. Validation Best Practices

1. **Validate early**: Run validation during development, not just before PR
2. **Incremental validation**: Validate only changed files during iteration
3. **Complete validation**: Run full validation before submitting PR
4. **Fix upstream**: If source data is wrong, fix it at the source
5. **Document exceptions**: If validation warning is acceptable, document why
6. **Automate**: Use pre-commit hooks or CI for consistent validation
7. **Test scripts**: If modifying validation scripts, test thoroughly

---

## ✅ Quick Reference

```bash
# Standard validation workflow
python scripts/validate_corpus.py --corpus corpora/programming
python scripts/validate_vectorset.py  # if embeddings included
python scripts/ingest.py --dry-run    # test ingestion

# Fix issues, then re-validate
python scripts/validate_corpus.py --strict

# When all pass, ready to commit
git add corpora/
git commit -m "feat(programming): add asyncio documentation"
```

**Remember**: Validation ensures quality and trust in the corpus!
