# Contribution Review & Merge Control SOP

**Status**: Active  
**Owner**: Repository Maintainers  
**Version**: 2.0.0  
**Last Updated**: February 25, 2026  
**Trigger**: All PRs contributing to corpora or infrastructure  
**RACI**: R=Reviewer(s), A=Maintainer, C=License Curator, I=Community  
**SLA**: Review ≤2 business days; Critical fix ≤4 hours

---

## 🎯 Purpose

Ensure quality, licensing compliance, and provenance before corpus content or code lands. Standardize the review process for both corpus contributions and infrastructure changes.

**Failure Modes & Controls**:

- Missing license documentation → block merge
- Incomplete metadata → block merge
- Failed validation → block merge
- Missing provenance → block merge

---

## 📋 Review Rubric

### For Corpus Contributions

Score each area (✅ Pass / ⚠️ Concern / ❌ Fail):

| Area                    | Check                                              | Weight |
| ----------------------- | -------------------------------------------------- | ------ |
| **Licensing**           | Source license documented, tier classified         | High   |
| **Provenance**          | Source URL, retrieval date, verification recorded  | High   |
| **Metadata**            | All required fields complete and valid             | High   |
| **Quality**             | Content relevant, accurate, well-formatted         | High   |
| **Chunking**            | Proper chunk boundaries, metadata headers          | Medium |
| **Documentation**       | CORPUS.md and sources.json updated                 | Medium |

### For Code/Infrastructure Contributions

| Area                | Check                                         | Weight |
| ------------------- | --------------------------------------------- | ------ |
| **Correctness**     | Logic correct, validation passes              | High   |
| **Documentation**   | README/scripts documented                     | Medium |
| **Maintainability** | Clear code, good names, DRY principles        | Medium |

---

## 🔄 Review Procedure

### 1. PR Preparation (Contributor)

#### For Corpus Contributions

Before requesting review:

- [ ] Source license verified and tier classified (Tier 1/2/3)
- [ ] Provenance documented in `sources.json`
- [ ] Metadata headers complete in all chunks
- [ ] Validation scripts pass (`validate_corpus.py`)
- [ ] CORPUS.md updated with new sources
- [ ] Self-reviewed chunk quality
- [ ] Conventional commit message prepared

#### For Code Contributions

Before requesting review:

- [ ] Validation/tests pass
- [ ] Code follows repository conventions
- [ ] Documentation updated
- [ ] Self-reviewed diff

### 2. Automated Gates (CI)

Required checks before human review:

```yaml
Corpus Contributions:
  - validate_corpus.py (metadata + schema)
  - validate_vectorset.py (if embeddings included)
  - License compliance check

Code Contributions:
  - Python syntax validation
  - Script functionality tests
```

### 3. Triage (Reviewer)

- [ ] Identify contribution type (corpus/code/docs)
- [ ] Check contribution scope and size
- [ ] Verify tier classification if corpus content
- [ ] Identify areas of concern

### 4. Review Gates

#### License Compliance Gate

For all corpus contributions:

- [ ] Source license allows intended use (redistribution/recipe/reference)
- [ ] License documented in `sources.json`
- [ ] Tier classification correct (Tier 1/2/3)
- [ ] Attribution requirements met

#### Provenance Gate

For all corpus contributions:

- [ ] Source URL documented and accessible
- [ ] Retrieval date recorded
- [ ] Source verification method noted
- [ ] Original license preserved

#### Quality Gate

For corpus contributions:

- [ ] Content is high-quality and relevant
- [ ] Metadata complete (title, domain, subdomain, etc.)
- [ ] Chunk boundaries appropriate
- [ ] No PII or sensitive data
- [ ] Validation scripts pass

### 5. Feedback Style

**Do**:

- Be specific with suggestions
- Offer code snippets
- Praise good patterns
- Separate blocking vs non-blocking

**Don't**:

- Nitpick style (use linters)
- Be vague ("this is wrong")
- Block on preferences

### 6. Approvals

| PR Type                  | Required Approvals              |
| ------------------------ | ------------------------------- |
| Corpus (Tier 1)          | 1 maintainer + license check    |
| Corpus (Tier 2/3)        | 1 maintainer                    |
| Code/infrastructure      | 1 maintainer or 2 contributors  |
| Critical fix             | 1 maintainer (expedited)        |

### 7. Merge

```bash
# Squash merge with conventional commit
git merge --squash feature-branch

# Commit message format
<type>(<scope>): <description>

# Examples
feat(programming): add Python asyncio documentation
feat(web-dev): add React hooks corpus
fix(corpus): correct metadata headers in chunk_042.md
docs(sop): update contribution review SOP
chore(scripts): improve validation error messages
```

---

## 📊 Review Metrics

Track weekly:

| Metric               | Target   |
| -------------------- | -------- |
| Time to first review | <4 hours |
| Time to merge        | <1 day   |
| Review iterations    | <3       |
| Rework rate          | <20%     |

---

## 🚨 Escalation

If review SLA breached:

1. Auto-ping in team channel
2. Escalate to tech lead at 2× SLA
3. Document blockers

---

## ✅ Pre-Merge Checklist

### For Corpus Contributions

- [ ] All validation checks pass
- [ ] License compliance verified
- [ ] Provenance documented
- [ ] Required approvals obtained
- [ ] No unresolved conversations
- [ ] CORPUS.md and sources.json updated
- [ ] Branch is up-to-date with Prime

### For Code Contributions

- [ ] All validation/tests pass
- [ ] Required approvals obtained
- [ ] No unresolved conversations
- [ ] Documentation updated
- [ ] Branch is up-to-date with Prime
