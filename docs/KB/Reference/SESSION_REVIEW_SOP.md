# Session Review SOP

**Status**: Active  
**Owner**: Repository Maintainers  
**Version**: 2.0.0  
**Last Updated**: February 25, 2026  
**Trigger**: Start of every work session  
**RACI**: R=Contributor, A=Maintainer, C=Team, I=Community  
**SLA**: Complete review within 5 minutes of session start

---

## 🎯 Purpose

Establish project baseline and next steps at the start of every work session. Ensures continuity across sessions and provides a clear understanding of current repository state and priorities.

---

## 📋 Review Process

### Phase 1: Git Status

**Purpose**: Understand current working state

```bash
# Check git status
git status

# View recent commits
git log --oneline -5

# Check current branch
git branch -v

# Ensure up-to-date with remote
git fetch
git pull
```

**Check**:

- [ ] Current branch (usually `Prime`)
- [ ] Any uncommitted changes
- [ ] Recent activity
- [ ] Up-to-date with remote

---

### Phase 2: Corpus Status

**Purpose**: Review current corpora and their status

```bash
# List corpora
ls -la corpora/

# Check each corpus
for dir in corpora/*/; do
    echo "=== $(basename $dir) ==="
    if [ -f "$dir/CORPUS.md" ]; then
        head -20 "$dir/CORPUS.md"
    fi
    echo ""
done
```

**Review**:

- [ ] Which corpora exist
- [ ] Status of each (versions, completeness)
- [ ] Any in-progress work

---

### Phase 3: Validation Status

**Purpose**: Check quality and validation status

```bash
# Validate all corpora
python scripts/validate_corpus.py

# Check for specific issues
python scripts/validate_corpus.py --strict
```

**Check**:

- [ ] All validations passing
- [ ] Any warnings to address
- [ ] Any blockers

---

### Phase 4: Documentation Status

**Purpose**: Ensure documentation is current

**Review**:

- [ ] README.md reflects current corpus status
- [ ] CONTRIBUTING.md is up-to-date
- [ ] licensing-guide.md is current
- [ ] KB documentation is accurate

```bash
# Quick check
cat README.md | grep "Status"
ls docs/KB/Reference/
```

---

### Phase 5: Issue & PR Status

**Purpose**: Review open issues and PRs

```bash
# View status (if using GitHub CLI)
gh issue list
gh pr list
```

**Check**:

- [ ] Open issues (prioritize)
- [ ] Open PRs (needs review?)
- [ ] Your assignments

---

### Phase 6: Session Goals

**Purpose**: Define what you'll accomplish this session

**Template**:

```markdown
## Session Goals - [DATE]

### Primary Goal
[Main objective for this session]

### Secondary Goals
- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

### Blockers
[Any current blockers or dependencies]

### Notes
[Relevant context or decisions]
```

**Example**:

```markdown
## Session Goals - 2026-02-25

### Primary Goal
Add Python asyncio documentation to programming corpus

### Secondary Goals
- [ ] Extract asyncio docs from Python docs
- [ ] Create chunks with proper metadata
- [ ] Update sources.json
- [ ] Run validation
- [ ] Submit PR

### Blockers
None

### Notes
Python docs are PSF-2.0 licensed (Tier 1 compatible)
```

---

## 📝 Session Summary (Optional)

For significant work sessions, create a summary:

**Location**: `docs/session-reviews/YYYY/MM-month/SESSION_SUMMARY_MONDD_YYYY.md`

**Template**: See [SESSION_REVIEW_TEMPLATE.md](SESSION_REVIEW_TEMPLATE.md)

---

## ✅ Quick Checklist

Before starting work:

- [ ] Git status reviewed
- [ ] Latest changes pulled
- [ ] Corpus status understood
- [ ] Validations checked
- [ ] Session goals defined
- [ ] Ready to contribute

---

## 🔄 Session Close

At end of session:

1. **Run validation**:
   ```bash
   python scripts/validate_corpus.py
   ```

2. **Review changes**:
   ```bash
   git status
   git diff
   ```

3. **Commit work**:
   ```bash
   git add <files>
   git commit -m "<conventional-commit-message>"
   git push
   ```

4. **Update goals** (if using session doc):
   - Mark completed goals
   - Note any new blockers
   - Plan next session

---

## 📊 Session Metrics (Optional)

Track your contributions:

| Metric                | Count |
| --------------------- | ----- |
| Chunks added          | —     |
| Sources documented    | —     |
| Validations fixed     | —     |
| PRs submitted         | —     |
| Issues resolved       | —     |

---

## 🚨 Common Session Start Issues

### Issue: Validation failures

**Symptom**: `validate_corpus.py` reports errors  
**Action**: Review and fix before new work

### Issue: Merge conflicts

**Symptom**: `git pull` shows conflicts  
**Action**: Resolve conflicts before proceeding

### Issue: Unclear priorities

**Symptom**: Don't know what to work on  
**Action**: Review open issues, check README roadmap

---

## 💡 Tips for Effective Sessions

1. **Start with review**: Don't skip the review process
2. **Set clear goals**: Know what "done" looks like
3. **Validate early**: Run validation before committing
4. **Commit often**: Small, atomic commits
5. **Document decisions**: Note why, not just what
6. **End cleanly**: Ensure work is committed or stashed

---

## 🔗 Related SOPs

- [DOCUMENTATION_SOP.md](DOCUMENTATION_SOP.md) - Documentation requirements
- [TESTING_SOP.md](TESTING_SOP.md) - Validation procedures
- [CODE_REVIEW_SOP.md](CODE_REVIEW_SOP.md) - PR review process

**Remember**: A good session starts with a good review!
