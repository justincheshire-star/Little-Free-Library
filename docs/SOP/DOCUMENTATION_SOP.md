# Documentation SOP

**Status**: Active  
**Owner**: Repository Maintainers  
**Version**: 2.1.0  
**Last Updated**: February 27, 2026  
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
- Missing session summary → lost context between sessions → require session summary before commit

---

## 📊 Documentation Sweep

### Contribution Type → Document Matrix

Use this mapping to identify which documents require updates:

| Contribution Type              | Primary Docs                                | Secondary Docs                  | Conditional Docs           |
| ------------------------------ | ------------------------------------------- | ------------------------------- | -------------------------- |
| **New corpus domain**          | `README.md`, `corpora/<domain>/CORPUS.md`   | `contributors/CONTRIBUTING_GUIDE.md` | License tier documentation |
| **Add sources to corpus**      | `corpora/<domain>/CORPUS.md`, `sources.json`| `README.md` (update status table)| —                          |
| **Update chunk format**        | Chunk files, `CORPUS.md`                    | `README.md` (schema section)    | Migration notes            |
| **Licensing changes**          | `docs/licensing-guide.md`, `sources.json`   | `README.md`                     | Affected corpus CORPUS.md  |
| **Script/tooling changes**     | `README.md` (usage), script docstrings      | `docs/KB/tooling/`              | —                          |
| **Infrastructure changes**     | `README.md`, `CHANGELOG.md`                 | `contributors/ONBOARDING.md`    | `contributors/CONTRIBUTING_GUIDE.md` |
| **Dependency changes**         | `requirements.txt`, `README.md`             | `contributors/ONBOARDING.md`    | Setup instructions         |
| **Setup/installation changes** | `README.md`, `contributors/ONBOARDING.md`   | `contributors/CONTRIBUTING_GUIDE.md` | —                      |
| **SOP updates**                | Relevant `docs/SOP/*.md`                    | `docs/SOP/INDEX.md`             | —                          |
| **KB/documentation changes**   | Affected KB docs                            | `docs/KB/README.md`             | —                          |
| **Any commit (all types)**     | Session summary for current date            | —                               | —                          |

### Document Priority Tiers

When performing a documentation sweep, process documents in this order:

```
Tier 1 (Always Check):
├── README.md                    # Project overview & quick start
├── CONTRIBUTING.md              # Contribution guidelines
├── CHANGELOG.md                 # Version history
└── LICENSE                      # Repository license

Tier 2 (Corpus-Specific):
├── corpora/<domain>/CORPUS.md   # Corpus manifest
├── corpora/<domain>/sources.json # Source provenance
└── corpora/<domain>/chunks/      # Chunk metadata headers

Tier 3 (Contributor Documentation):
├── contributors/README.md       # Contributors hub navigation
├── contributors/ONBOARDING.md   # New contributor setup
├── contributors/CONTRIBUTING_GUIDE.md # Contribution workflows
├── contributors/ARCHITECTURE.md # System architecture
└── contributors/BENCHMARKING_GUIDE.md # Quality metrics

Tier 4 (Guides & Policies):
├── docs/licensing-guide.md      # Licensing tiers
├── docs/KB/architecture/        # Corpus architecture
└── docs/KB/tooling/             # Tooling documentation

Tier 5 (Reference & SOPs):
├── docs/SOP/INDEX.md            # SOP directory
└── docs/SOP/*.md                # Individual SOPs

Tier 6 (Session History — Required):
└── docs/Session Reviews/YYYY/MM-month/SESSION_SUMMARY_*.md  # Session work log
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
    3. Update or create today's session summary (Tier 6 — required)
       a. Path: docs/Session Reviews/YYYY/MM-month/SESSION_SUMMARY_<MMMDD>_<YYYY>.md
       b. One file per day — amend existing file if it exists
       c. Use SESSION_REVIEW_TEMPLATE.md format exactly
       d. Record: work completed, decisions, validation results, next steps
    4. Commit with comprehensive message listing all docs updated
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

### Contributors Directory Updates

Update when infrastructure, dependencies, or setup processes change.

**Contributors Hub (`contributors/README.md`)**

Update when:
- New contributor documentation added
- Documentation structure changes
- Quick reference needs updates

**Onboarding Guide (`contributors/ONBOARDING.md`)**

Update when:
- Prerequisites change (e.g., Git LFS required)
- Setup steps change (e.g., new dependencies)
- Installation process changes
- New tools or systems added (e.g., embedding models)
- Development environment requirements change

**Pattern**:
```markdown
### Prerequisites

**Required:**
- List all required tools with versions
- Include installation instructions for each
- Note disk space requirements
- Specify platform-specific requirements

**Install Instructions:**
# Show commands for major platforms
# Include verification steps
```

**Contributing Guide (`contributors/CONTRIBUTING_GUIDE.md`)**

Update when:
- Local setup process changes
- New validation requirements added
- Workflow steps change
- New tools integrated

**Architecture Guide (`contributors/ARCHITECTURE.md`)**

Update when:
- System architecture changes
- New components added
- Data flow changes
- Integration points change

**Benchmarking Guide (`contributors/BENCHMARKING_GUIDE.md`)**

Update when:
- New metrics added
- Benchmarking process changes
- Quality thresholds updated
- Optimization strategies change

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

### For All Contributions (Required)

- [ ] Session summary exists for today (`SESSION_SUMMARY_<MMMDD>_<YYYY>.md`)
  - One file per day — amend if it already exists, never create a second
  - Must follow [SESSION_REVIEW_TEMPLATE.md](SESSION_REVIEW_TEMPLATE.md) format exactly
  - Work Completed, Key Decisions, and Validation Results sections are current
  - Next Steps and Session Metrics updated before final commit of the day

---

## � Session Summary Updates (Required)

A session summary is **mandatory** for every day that work is performed. Session summaries provide continuity across work sessions and serve as the authoritative record of what changed and why.

### Rules

1. **One file per day** — Exactly one summary file per calendar day, regardless of how many sessions occur that day.
2. **Strict nomenclature** — Files must follow the naming convention exactly. No variations.
3. **Amend as you go** — Do not wait until the end of the day. Update the summary incrementally as work progresses throughout each session. Every meaningful milestone, decision, or completion should be recorded immediately.
4. **Template required** — Every summary must use the format defined in [SESSION_REVIEW_TEMPLATE.md](SESSION_REVIEW_TEMPLATE.md). Do not improvise structure.

### File Naming Convention

```
SESSION_SUMMARY_<MMM><DD>_<YYYY>.md
```

- `<MMM>` — Three-letter month abbreviation, UPPERCASE (e.g., `FEB`, `MAR`, `APR`)
- `<DD>` — Two-digit day of month (e.g., `01`, `15`, `27`)
- `<YYYY>` — Four-digit year

**Examples:**
- `SESSION_SUMMARY_FEB27_2026.md` ✅
- `SESSION_SUMMARY_MAR01_2026.md` ✅
- `session_summary_feb27_2026.md` ❌ (wrong case)
- `SESSION_SUMMARY_2026-02-27.md` ❌ (wrong date format)
- `SESSION_SUMMARY_FEB27_2026_v2.md` ❌ (no versioned files — amend the original)

### Directory Structure

```
docs/Session Reviews/
└── YYYY/
    └── MM-month/            # e.g., 02-february (zero-padded, lowercase month)
        ├── SESSION_SUMMARY_FEB25_2026.md
        ├── SESSION_SUMMARY_FEB26_2026.md
        └── SESSION_SUMMARY_FEB27_2026.md
```

Directory naming: `<NN>-<month>` where `<NN>` is zero-padded month number and `<month>` is lowercase full month name.

### Amend-as-you-go Workflow

```
Session starts:
    1. Check if today's summary file exists
       - YES → Open it, continue amending
       - NO  → Create from SESSION_REVIEW_TEMPLATE.md
    2. Fill in session goals and initial context

During work:
    3. After each meaningful milestone → amend Work Completed section
    4. After each key decision → amend Key Decisions section
    5. After resolving an issue → amend Blockers & Issues section

Before commit:
    6. Update Validation Results with latest output
    7. Update Commits section
    8. Update Next Steps
    9. Update Session Metrics table
    10. Set session Status field

Multiple sessions in one day:
    - Use segment headings (e.g., "### Segment 1: ...", "### Segment 2: ...")
    - Append new segments — never overwrite earlier work from the same day
```

### Required Content

Every session summary must include (per [SESSION_REVIEW_TEMPLATE.md](SESSION_REVIEW_TEMPLATE.md)):

| Section | Required | When to Update |
|---------|----------|----------------|
| Date, Contributor, Duration, Status | Yes | Session start + end |
| Session Goals | Yes | Session start |
| Work Completed | Yes | After each milestone |
| Key Decisions | Yes (if any) | Immediately when decided |
| Blockers & Issues | Yes (if any) | As encountered / resolved |
| Validation Results | Yes | Before commit |
| Commits | Yes | After each commit |
| Next Steps | Yes | Before ending session |
| Session Metrics | Yes | Before ending session |

### Failure Mode

A commit without a corresponding session summary for the current date breaks the project's historical record and makes it harder for future contributors (or future sessions) to understand context. Treat this the same as committing without updating CHANGELOG.md — it is a **blocking documentation gap**.

---

## �🔍 Documentation Validation

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
docs(contributors): update onboarding for Git LFS requirement
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
**Scopes**: `readme`, `corpus`, `sop`, `license`, `contributors`, domain names  

---

## 🔄 Contributors Directory Update Scenarios

### Scenario 1: Adding New Dependencies

**Trigger**: New library added to `requirements.txt`

**Actions**:
- [ ] Update `contributors/ONBOARDING.md` → Prerequisites or Install Dependencies section
- [ ] Update `contributors/CONTRIBUTING_GUIDE.md` → Setting Up Locally section
- [ ] Update `README.md` → Installation section if user-facing
- [ ] Update `CHANGELOG.md` with dependency change

**Example**: Adding embedding libraries (fastembed, sentence-transformers)

### Scenario 2: Infrastructure Changes

**Trigger**: New infrastructure requirement (e.g., Git LFS, Docker, database)

**Actions**:
- [ ] Update `contributors/ONBOARDING.md` → Prerequisites section
- [ ] Add installation instructions with platform-specific guidance
- [ ] Update Quick Start steps to include new setup
- [ ] Update `contributors/CONTRIBUTING_GUIDE.md` → Setting Up Locally
- [ ] Update `README.md` if user-facing
- [ ] Document in `CHANGELOG.md`

**Example**: Adding Git LFS for model files

### Scenario 3: New Models or Large Assets

**Trigger**: Embedding models, datasets, or other large files added

**Actions**:
- [ ] Update `contributors/ONBOARDING.md`:
  - Prerequisites (disk space, Git LFS)
  - Quick Start (download steps)
  - Add dedicated section explaining the assets
  - Add verification/testing instructions
- [ ] Update `contributors/CONTRIBUTING_GUIDE.md` → Setup section
- [ ] Create dedicated guide in `docs/` (e.g., `EMBEDDING_SETUP.md`)
- [ ] Update `README.md` → Installation section
- [ ] Update `CHANGELOG.md`

**Example**: Embedding 796 MB of ONNX and PyTorch models

### Scenario 4: Development Workflow Changes

**Trigger**: New testing requirements, validation steps, or development processes

**Actions**:
- [ ] Update `contributors/CONTRIBUTING_GUIDE.md` → Relevant workflow sections
- [ ] Update `contributors/ONBOARDING.md` → Development Environment Setup
- [ ] Update relevant SOP if process-related
- [ ] Update `README.md` if user-facing

**Example**: Adding mandatory pre-commit hooks

### Scenario 5: Architecture Changes

**Trigger**: New modules, refactored structure, or system design changes

**Actions**:
- [ ] Update `contributors/ARCHITECTURE.md` → Relevant diagrams and descriptions
- [ ] Update `contributors/ONBOARDING.md` → Understanding the Codebase section
- [ ] Update `README.md` if user-facing
- [ ] Document in `CHANGELOG.md`

**Example**: Adding hybrid retrieval system

---

## 📋 Contributors Documentation Checklist

When making infrastructure, dependency, or setup changes:

### Quick Check

- [ ] Does this change affect how contributors set up their environment?
- [ ] Does this change add new prerequisites?
- [ ] Does this change modify installation steps?
- [ ] Does this change add new tools or systems?
- [ ] Does this change affect development workflow?

### If YES to any, update:

**Always Update**:
- [ ] `contributors/ONBOARDING.md` (if setup-related)
- [ ] `CHANGELOG.md` (document the change)

**Conditionally Update**:
- [ ] `contributors/CONTRIBUTING_GUIDE.md` (if workflow-related)
- [ ] `contributors/ARCHITECTURE.md` (if architecture-related)
- [ ] `contributors/README.md` (if navigation structure changes)
- [ ] `README.md` (if user-facing)

### After Update

- [ ] Test instructions on fresh clone
- [ ] Verify all links work
- [ ] Check cross-references are consistent
- [ ] Run validation scripts if applicable

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
