# Corpus Quality Metrics & Standards

**Status**: Active  
**Owner**: Repository Maintainers  
**Version**: 2.0.0  
**Last Updated**: February 25, 2026

---

## 🎯 Purpose

Define quality metrics, target thresholds, and merge gates for Little Free Library corpora. Ensures consistent quality across all corpus contributions.

---

## 📊 Core Quality Metrics

| Domain              | Metric                      | Target | Tooling                   | Gate          |
| ------------------- | --------------------------- | ------ | ------------------------- | ------------- |
| **Metadata**        | Completeness                | 100%   | `validate_corpus.py`      | Block merge   |
| **Metadata**        | Schema validity             | 100%   | `validate_corpus.py`      | Block merge   |
| **Licensing**       | Documentation completeness  | 100%   | `validate_corpus.py`      | Block merge   |
| **Licensing**       | License compatibility       | 100%   | Manual review             | Block merge   |
| **Provenance**      | Source documentation        | 100%   | `validate_corpus.py`      | Block merge   |
| **Provenance**      | Orphan chunks               | 0      | `validate_corpus.py`      | Block merge   |
| **Embeddings**      | Dimension consistency       | 100%   | `validate_vectorset.py`   | Block merge   |
| **Content**         | Minimum chunk length        | >50char| `validate_corpus.py`      | Warn          |
| **Content**         | UTF-8 encoding              | 100%   | `validate_corpus.py`      | Block merge   |
| **Contribution**    | Validation pass rate        | 100%   | Validation scripts        | Block merge   |

---

## 🚦 Contribution Gates

### Merge to Prime Branch

| Check                          | Required | Blocks |
| ------------------------------ | -------- | ------ |
| All validation scripts pass    | ✅       | Yes    |
| Metadata 100% complete         | ✅       | Yes    |
| License documented             | ✅       | Yes    |
| Provenance documented          | ✅       | Yes    |
| 1+ maintainer approval         | ✅       | Yes    |
| Documentation updated          | ✅       | Yes    |
| No PII or sensitive data       | ✅       | Yes    |

### Corpus Version Release

| Check                  | Required | Blocks |
| ---------------------- | -------- | ------ |
| All merge gates passed | ✅       | Yes    |
| CORPUS.md up to date   | ✅       | Yes    |
| Version number bumped  | ✅       | Yes    |
| Quality spot-check     | ✅  | Yes    |
| README updated         | ✅       | Yes    |

---

## 📈 Corpus Quality Standards

### Tier 1: Redistributable Corpora

**Quality Requirements**:

| Metric                 | Standard                  | Validation                      |
| ---------------------- | ------------------------- | ------------------------------- |
| Metadata completeness  | 100% (all required fields)| Automated validation            |
| Source documentation   | 100% in sources.json      | Automated cross-reference       |
| License documentation  | Complete with URL         | Manual + automated verification |
| Chunk formatting       | Valid YAML + content      | Automated schema validation     |
| Content quality        | High relevance, accurate  | Manual review                   |
| Embedding consistency  | Same dimensions           | Automated if embeddings included|

### Tier 2: Recipe-Only Corpora

**Quality Requirements**:

| Metric                | Standard                   | Validation          |
| --------------------- | -------------------------- | ------------------- |
| Recipe completeness   | Runnable scripts + docs    | Manual test         |
| Source accessibility  | URLs valid and accessible  | Manual + URL check  |
| License documentation | Complete in manifest       | Manual review       |
| Build reproducibility | Can rebuild locally        | Test build          |

### Tier 3: Reference-Only Corpora

**Quality Requirements**:

| Metric               | Standard                     | Validation    |
| -------------------- | ---------------------------- | ------------- |
| Link validity        | All URLs accessible          | URL check     |
| Description accuracy | Matches actual source        | Manual review |
| License information  | Documented and accurate      | Manual review |

---

## 📊 Validation Thresholds

### Metadata Quality

**Required fields** (100% threshold):

- `title`
- `domain`
- `subdomain`
- `source`
- `source_license`
- `source_id`
- `source_path`
- `retrieved_at`
- `verified`

**Optional fields**:

- `importance` (0.0-1.0, if used must be valid float)
- Custom domain-specific fields

### License Compliance

**Allowed licenses** (Tier 1):

- CC0, CC-BY, CC-BY-SA
- MIT, Apache 2.0, BSD
- PSF (Python Software Foundation)
- Public Domain

**Prohibited for Tier 1**:

- GPL, AGPL, SSPL (copyleft)
- CC-BY-NC (non-commercial)
- Proprietary/Commercial
- "All Rights Reserved"

### Content Quality

**Minimum standards**:

- No PII (personally identifiable information)
- No offensive or inappropriate content
- No copyrighted material without permission
- Accurate representation of source
- Meaningful content (> 50 characters)
- UTF-8 encoding

---

##  🔬 Quality Measurement Process

### 1. Automated Validation

```bash
# Run validation suite
python scripts/validate_corpus.py --corpus corpora/<domain> --strict

# Expected output
✓ Metadata: 100% complete (N/N chunks)
✓ Provenance: 100% documented (M/M sources)
✓ Licensing: 100% compliant (M/M sources)
✓ Schema: 100% valid (N/N chunks)
✓ Embedding: Consistent dimensions (if applicable)

Summary: PASS - Ready for merge
```

### 2. Manual Quality Review

**Reviewer checklist**:

- [ ] Content is high-quality and relevant
- [ ] Sources are authoritative
- [ ] Chunking is appropriate
- [ ] Metadata is accurate
- [ ] License classification correct (Tier 1/2/3)
- [ ] No PII or sensitive data
- [ ] Attribution requirements clear

### 3. Spot-Check Sampling

For large contributions (>100 chunks):

- Sample 10-20 random chunks
- Verify metadata accuracy
- Review content quality
- Check source consistency

---

## 📈 Tracking Quality Over Time

### Per-Corpus Metrics

Track in CORPUS.md:

```yaml
---
domain: programming
version: 1.0.0
statistics:
  total_chunks: 142
  total_sources: 8
  metadata_completeness: 100%
  validation_pass_rate: 100%
  last_validated: 2026-02-25
---
```

### Repository-Wide Metrics

Track in README.md:

| Metric                      | Current |
| --------------------------- | ------- |
| Total corpora               | 1       |
| Total chunks                | 142     |
| Average metadata completeness | 100%  |
| License compliance          | 100%    |
| Validation pass rate        | 100%    |

---

## 🎯 Quality Improvement Process

### When Quality Falls Below Target

1. **Identify issues**: Run validation and review failures
2. **Categorize**: Metadata/licensing/content issues
3. **Prioritize**: Block merge issues first, then warnings
4. **Fix**: Address systematically
5. **Re-validate**: Run full validation suite
6. **Document**: Note improvements in commit message

### Continuous Quality

- **Quarterly review**: Spot-check random samples
- **Validation updates**: Keep scripts current with standards
- **Standard updates**: Document any changes to quality requirements
- **Feedback loop**: Incorporate community feedback on quality

---

## 🚨 Quality Gate Failures

### Common Failures and Remediation

| Failure                      | Reason                    | Fix                                |
| ---------------------------- | ------------------------- | ---------------------------------- |
| Metadata < 100%              | Missing required fields   | Add missing fields to chunks       |
| License documentation < 100% | Missing source in sources.json | Add source entry             |
| Orphan chunks > 0            | source_id doesn't match   | Fix source_id or add to sources.json |
| Schema validation failure    | Invalid YAML              | Fix YAML syntax                    |
| Embedding dimension mismatch | Mixed embedding models    | Regenerate with consistent model   |

---

## ✅ Quick Quality Checklist

Before submitting a contribution:

### Tier 1 Corpus Contribution

- [ ] Run `python scripts/validate_corpus.py --corpus <path> --strict`
- [ ] All validation checks pass (100%)
- [ ] sources.json includes all referenced sources
- [ ] License tier correctly classified
- [ ] No PII or sensitive data
- [ ] Manual quality spot-check on sample chunks
- [ ] CORPUS.md updated
- [ ] README.md updated (if needed)

### Tier 2/3 Contribution

- [ ] Recipe/documentation is complete
- [ ] Sources are accessible
- [ ] License information documented
- [ ] Instructions are clear
- [ ] Tested (for recipes)

---

## 📊 Quality Metrics Dashboard (Future)

Potential future enhancements:

- Automated quality dashboard
- Trend tracking over time
- Per-contributor quality metrics
- Automated quality regression detection
- Quality badges for corpora

---

## 🔍 References

- [Validation Scripts](../../scripts/)
- [TESTING_SOP.md](TESTING_SOP.md) - Validation procedures
- [licensing-guide.md](../../licensing-guide.md) - License tiers
- [contributing-guide.md](../../contributing-guide.md) - Contribution process

**Remember**: Quality is not negotiable. Every chunk, every source, every metadata field matters for trust and usability!
