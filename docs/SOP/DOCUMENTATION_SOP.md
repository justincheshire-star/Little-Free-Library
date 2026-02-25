# Documentation SOP

**Status**: Active  
**Owner**: Repository Maintainers  
**Version**: 2.0.0  
**Last Updated**: February 25, 2026  
**Trigger**: Before every commit  
**RACI**: R=Contributor, A=Maintainer, C=Reviewers, I=Community  
**SLA**: Docs updated before merge

---

## 🎯 Purpose

Keep documentation synchronized with corpus changes. Ensures that README, corpus manifests, and licensing docs accurately reflect the current state of the Little Free Library repository.

**Failure Modes & Controls**:

- Stale corpus docs → confusion → validation scripts enforce metadata
- Missing license info → legal risk → block merge on missing license
- Outdated README → poor onboarding → require README updates for new corpora
- Missing provenance → trust issues → require sources.json completeness

---

## 📊 Documentation Sweep

### Contribution Type → Document Matrix

Use this mapping to identify which documents require updates:

| Contribution Type              | Primary Docs                                | Secondary Docs                  | Conditional Docs           |
| ------------------------------ | ------------------------------------------- | ------------------------------- | -------------------------- |
| **New corpus domain**          | `README.md`, `corpora/<domain>/CORPUS.md`   | `docs/contributing-guide.md`    |License tier documentation |
| **Add sources to corpus**      | `corpora/<domain>/CORPUS.md`, `sources.json`| `README.md` (update status table)| —                          |
| **Update chunk format**        | Chunk files, `CORPUS.md`                    | `README.md` (schema section)    | Migration notes            |
| **Licensing changes**          | `docs/licensing-guide.md`, `sources.json`   | `README.md`                     | Affected corpus CORPUS.md  |
| **Script/tooling changes**     | `README.md` (usage), script docstrings      | `docs/KB/tooling/`              | —                          |
| **SOP updates**                | Relevant `docs/SOP/*.md`                    | `docs/SOP/INDEX.md`             | —                          |
| **KB/documentation changes**   | Affected KB docs                            | `docs/KB/README.md`             | —                          |

### Document Priority Tiers

When performing a documentation sweep, process documents in this order:

```
Tier 1 (Always Check):
├── README.md                    # Project overview & quick start
├── CONTRIBUTING.md              # Contribution guidelines
└── LICENSE                      # Repository license

Tier 2 (Corpus-Specific):
├── corpora/<domain>/CORPUS.md   # Corpus manifest
├── corpora/<domain>/sources.json # Source provenance
└── corpora/<domain>/chunks/      # Chunk metadata headers

Tier 3 (Guides & Policies):
├── docs/contributing-guide.md   # How to contribute
├── docs/licensing-guide.md      # Licensing tiers
└── docs/KB/architecture/        # Corpus architecture

Tier 4 (Reference & SOPs):
├── docs/SOP/INDEX.md            # SOP directory
└── docs/SOP/*.md                # Individual SOPs
```

### Sweep Execution Algorithm

```
FOR each contribution IN session_work:
    1. Look up contribution type in matrix
    2. Identify Primary, Secondary, and Conditional docs
    3. FOR each identified document:
        a. Read current state
        b. Determine required updates
        c. Apply updates
        d. Validate (run validation scripts if applicable)
        e. Track document in sweep log
    
AFTER all contributions processed:
    1. Verify all changes are consistent
    2. Run validation scripts
    3. Commit with comprehensive message listing all docs updated
```

---

## 📋 Document Update Patterns

### README.md Updates

Update when:
- New corpus domain added
- Corpus status changes
- Quick start instructions change
- Major feature added

**Pattern**:

```markdown
## The Library

| Domain | Status | Version | License |
|--------|--------|---------|---------|
| Programming | ✅ Stable | v1.0.0 | CC-BY-SA 4.0 |
| <NEW_DOMAIN> | 🚧 In Progress | v0.1.0 | CC-BY-SA 4.0 |
```

### CORPUS.md Updates

Update when:
- New sources added
- Corpus version bumped
- Domain/subdomain structure changes
- Citation requirements change

**Required sections**:

```markdown
---
domain: <domain_name>
version: <semver>
license: CC-BY-SA 4.0
source_tier: <1|2|3>
---

# <Domain> Corpus

## Overview
[Description]

## Sources
[List of sources with licenses]

## Structure
[Subdomain organization]

## Usage
[How to use this corpus]

## Attribution
[Citation requirements]
```

### sources.json Updates

Update when:
- New source added
- Source license clarified
- Retrieval metadata updated

**Required fields per source**:

```json
{
  "source_id": "unique_identifier",
  "title": "Source Title",
  "url": "https://...",
  "license": "License Name",
  "license_url": "https://...",
  "tier": 1,
  "retrieved_at": "2026-02-25",
  "verified": "documented|automated|manual",
  "notes": "Additional context"
}
```

### Chunk Metadata Headers

Update when:
- New chunks created
- Metadata schema updated
- Source attribution changes

**Required metadata per chunk**:

```yaml
---
title: "Chunk Title"
domain: domain_name
subdomain: subdomain_name
source: https://original-url
source_license: License-Name
source_id: matching_sources_json_id
source_path: path/within/source
retrieved_at: YYYY-MM-DD
verified: documented|automated|manual
importance: 0.0-1.0  # Optional quality signal
---
```

### Contributing Guide Updates

Update when:
- Contribution process changes
- New corpus standards added
- Validation requirements change

### Licensing Guide Updates

Update when:
- New license tier added
- Tier definitions refined
- Compliance requirements change

---

## ✅ Pre-Commit Documentation Checklist

Before committing:

### For Corpus Contributions

- [ ] `CORPUS.md` updated with new sources
- [ ] `sources.json` includes all new sources
- [ ] All chunks have complete metadata headers
- [ ] `README.md` updated if new domain or status change
- [ ] Validation scripts pass

### For Code/Script Contributions

- [ ] `README.md` updated if user-facing changes
- [ ] Script docstrings complete
- [ ] Usage examples updated
- [ ] Dependencies documented if changed

### For SOP/Documentation Contributions

- [ ] `INDEX.md` updated if new SOP
- [ ] Cross-references verified
- [ ] Examples updated

---

## 🔍 Documentation Validation

### Automated Checks

Run before commit:

```bash
# Validate corpus manifests
python scripts/validate_corpus.py

# Validate sources.json schema
python scripts/validate_corpus.py --check-sources

# Check for broken cross-references
grep -r "\[.*\](.*\.md)" docs/ | # (manual review)
```

### Manual Checks

- [ ] Links resolve correctly
- [ ] Consistent terminology
- [ ] No PII or sensitive data
- [ ] License information accurate
- [ ] Code examples runnable

---

## 📝 Commit Message Format

Use conventional commits for documentation changes:

```bash
# Examples
docs(programming): add Python asyncio sources to CORPUS.md
docs(readme): update status table with web-dev corpus
docs(sop): refine documentation sweep procedure
feat(corpus): add new mathematics corpus
chore(license): clarify tier 2 redistribution rules
```

**Format**:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**: `docs`, `feat`, `fix`, `chore`, `refactor`  
**Scopes**: `readme`, `corpus`, `sop`, `license`, domain names  

---

## 🚨 Common Documentation Issues

### Issue: Stale corpus status in README

**Detection**: Manual review or contributor report  
**Fix**: Update status table with current state  
**Prevention**: Include README check in contribution checklist

### Issue: Missing source in sources.json

**Detection**: Validation script error  
**Fix**: Add complete source entry with all required fields  
**Prevention**: Run validation before commit

### Issue: Incomplete chunk metadata

**Detection**: Validation script error  
**Fix**: Add missing metadata fields to chunk headers  
**Prevention**: Use chunk template when creating new chunks

### Issue: Broken cross-references

**Detection**: Manual link check  
**Fix**: Update links to correct paths  
**Prevention**: Use relative paths, verify links before commit

---

## 📚 Documentation Standards

### Style Guide

- **Tone**: Clear, welcoming, educational
- **Voice**: Second person ("you") for guides, third person for specs
- **Format**: Markdown with YAML frontmatter where applicable
- **Line length**: Soft limit 100 characters (except code blocks)
- **Headings**: Sentence case (capitalize first word only)

### Terminology

Use consistent terms:

- **Corpus** (not "dataset" or "collection")
- **Chunk** (not "fragment" or "piece")  
- **Domain** (not "category" or "topic")
- **Source** (not "reference" or "origin")
- **Tier** (not "level" or "class") for licensing
- **Provenance** (not "source" or "history") for attribution chain

### File Naming

- **SOPs**: `UPPERCASE_WITH_UNDERSCORES_SOP.md`
- **Guides**: `lowercase-with-hyphens-guide.md`
- **Corpus manifests**: `CORPUS.md` (uppercase, standardized)
- **Chunks**: `chunk_NNN.md` (zero-padded numbers)

---

## 🔄 Documentation Review Cycle

- **Frequency**: Review docs quarterly or when processes change
- **Owner**: Repository Maintainers
- **Process**:
  1. Audit existing docs for accuracy
  2. Identify stale or missing content
  3. Update or deprecate as needed
  4. Update INDEX.md if structure changes
  5. Announce changes to community

---

## 📞 Questions or Issues

If uncertain about documentation requirements:

1. Check this SOP and [INDEX.md](INDEX.md)
2. Review [contributing-guide.md](../../contributing-guide.md)
3. Ask in discussions or open an issue
4. Tag maintainers for guidance

**Remember**: Good documentation is as valuable as good corpus content!
