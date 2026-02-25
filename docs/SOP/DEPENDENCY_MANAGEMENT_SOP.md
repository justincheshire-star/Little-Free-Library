# Dependency Management SOP

**Status**: Active  
**Owner**: Repository Maintainers  
**Version**: 2.0.0  
**Last Updated**: February 25, 2026  
**Review Cycle**: Quarterly or when adding/updating dependencies

---

## 🎯 Purpose

Establish requirements for managing dependencies in Little Free Library Python scripts and RAG infrastructure to maintain security, stability, and compatibility.

---

## 📦 Scope

### Python Dependencies

- `docs/KB/Vector_RAG/requirements.txt` - RAG/pxctx dependencies
- Script-specific dependencies (as needed)

### Future: Node.js (if web tools added)

- Package.json for any web-based tools

---

## 🔐 Core Principles

1. **Security First**: Never compromise security for convenience
2. **Minimal Dependencies**: Prefer stdlib when possible
3. **Version Pinning**: Pin major versions, allow minor/patch updates
4. **Compatibility**: Ensure Python 3.10+ compatibility
5. **Documentation**: Document all dependency decisions

---

## 1. Before Adding Dependencies

### 1.1 Evaluation Checklist

Before adding any new dependency:

- [ ] **Security**: Check for known vulnerabilities (use `pip-audit`)
- [ ] **Maintenance**: Active maintenance (commits within 6 months)
- [ ] **License**: MIT, Apache 2.0, BSD, or ISC preferred
- [ ] **Size**: No unnecessary large dependencies
- [ ] **Alternatives**: Evaluated stdlib or lighter alternatives
- [ ] **Python Version**: Compatible with Python 3.10+
- [ ] **Type Hints**: Includes type stubs or inline types

### 1.2 Security Review

```bash
# Install pip-audit (if not already installed)
pip install pip-audit

# Check for vulnerabilities
pip-audit -r docs/KB/Vector_RAG/requirements.txt
```

### 1.3 License Verification

**Allowed Licenses**:

- MIT
- Apache 2.0
- BSD (2-Clause, 3-Clause)
- ISC
- PSF (Python Software Foundation)

**Prohibited Licenses**:

- GPL (copyleft)
- AGPL (copyleft + network clause)
- SSPL (server-side restrictions)
- Proprietary/Commercial

**Check license**:

```bash
# Using pip-licenses
pip install pip-licenses
pip-licenses --from=classifier --format=markdown
```

---

## 2. Installing Dependencies

### 2.1 Python Dependencies

**RAG/pxctx dependencies**:

```bash
# Add to requirements.txt
echo "package-name>=1.0.0,<2.0.0" >> docs/KB/Vector_RAG/requirements.txt

# Install in development
pip install -r docs/KB/Vector_RAG/requirements.txt
```

**Script-specific dependencies**:

If a script needs a specific dependency, document it at the top:

```python
#!/usr/bin/env python3
"""
Corpus validation script.

Dependencies:
    - PyYAML>=6.0,<7.0
    - jsonschema>=4.17,<5.0
    
Install: pip install PyYAML jsonschema
"""
```

### 2.2 Version Constraints

| Syntax           | Meaning            | When to Use                   |
| ---------------- | ------------------ | ----------------------------- |
| `>=1.0.0,<2.0.0` | Compatible range   | Most dependencies             |
| `~=1.0.0`        | Compatible release | Stable APIs                   |
| `==1.0.0`        | Exact version      | Security-sensitive or pinning |
| `>=1.0.0`        | Minimum only       | Very flexible deps            |

**Recommended**:

```txt
# Good: allows bug fixes, blocks breaking changes
requests>=2.31.0,<3.0.0
pyyaml>=6.0,<7.0

# Avoid: too restrictive
requests==2.31.0

# Avoid: too permissive
requests>=2.0.0
```

### 2.3 Post-Installation Verification

```bash
# 1. Verify installation
pip list | grep package-name

# 2. Run validation scripts
python scripts/validate_corpus.py --help

# 3. Check for conflicts
pip check
```

---

## 3. Updating Dependencies

### 3.1 Update Frequency

| Type             | Frequency         | Process       |
| ---------------- | ----------------- | ------------- |
| Security patches | Immediate         | Direct update |
| Minor versions   | Quarterly         | Test first    |
| Major versions   | As needed         | Full review   |

### 3.2 Update Procedure

**Security update**:

```bash
# 1. Check for vulnerabilities
pip-audit -r docs/KB/Vector_RAG/requirements.txt

# 2. Update specific package
pip install --upgrade package-name

# 3. Test
python scripts/validate_corpus.py
python scripts/validate_vectorset.py

# 4. Update requirements.txt
pip freeze | grep package-name >> docs/KB/Vector_RAG/requirements.txt
```

**Routine update**:

```bash
# 1. Check what's outdated
pip list --outdated

# 2. Review changelog for breaking changes
# (Visit package repository)

# 3. Update in requirements.txt
# Change: package>=1.0.0,<2.0.0
# To:     package>=1.5.0,<2.0.0

# 4. Install and test
pip install -r docs/KB/Vector_RAG/requirements.txt
python scripts/validate_corpus.py
python scripts/validate_vectorset.py

# 5. Document in commit message
git add docs/KB/Vector_RAG/requirements.txt
git commit -m "chore(deps): update package to 1.5.0 for security fixes"
```

---

## 4. Current Dependencies

### 4.1 RAG/pxctx Dependencies

Document current dependencies here (update as needed):

| Package         | Version   | Purpose                      | License    |
| --------------- | --------- | ---------------------------- | ---------- |
| PyYAML          | >=6.0     | YAML parsing for metadata   | MIT        |
| numpy           | >=1.24    | Vector operations            | BSD        |
| sentence-transformers | >=2.2 | Embeddings generation  | Apache 2.0 |
| hnswlib         | >=0.7     | Vector search                | Apache 2.0 |

### 4.2 Script Dependencies

| Script                | Dependencies               | Purpose                |
| --------------------- | -------------------------- | ---------------------- |
| `validate_corpus.py`  | PyYAML, jsonschema         | Metadata validation    |
| `validate_vectorset.py` | numpy                    | Embedding validation   |
| `ingest.py`           | PyYAML, sentence-transformers | Corpus ingestion   |

---

## 5. Dependency Troubleshooting

### Issue: Version conflict

**Symptom**: `pip check` reports conflicts  
**Fix**:

```bash
# Identify conflict
pip check

# Review dependency tree
pip install pipdeptree
pipdeptree

# Resolve by adjusting version constraints
```

### Issue: Missing dependency

**Symptom**: `ModuleNotFoundError: No module named 'X'`  
**Fix**:

```bash
# Install from requirements.txt
pip install -r docs/KB/Vector_RAG/requirements.txt

# Or install specific package
pip install package-name
```

### Issue: Incompatible Python version

**Symptom**: `ERROR: Package requires Python >=3.11, but you have 3.10`  
**Fix**: Upgrade Python or find compatible package version

### Issue: Security vulnerability reported

**Symptom**: `pip-audit` shows vulnerability  
**Fix**:

```bash
# Check severity
pip-audit -r docs/KB/Vector_RAG/requirements.txt

# Update to patched version
pip install --upgrade vulnerable-package

# Update requirements.txt
```

---

## 6. Best Practices

### 6.1 Requirements File Maintenance

**Keep requirements.txt clean**:

```txt
# Good: organized, commented, version-pinned
# Core dependencies
PyYAML>=6.0,<7.0  # Metadata parsing
numpy>=1.24,<2.0  # Vector operations

# RAG dependencies
sentence-transformers>=2.2,<3.0  # Embeddings
hnswlib>=0.7,<1.0  # Vector search
```

**Bad**:

```txt
# Bad: no versions, no organization
PyYAML
numpy
sentence-transformers
hnswlib
```

### 6.2 Virtual Environments

Always use virtual environments:

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r docs/KB/Vector_RAG/requirements.txt
```

### 6.3 Reproducible Installs

For exact reproducibility:

```bash
# Generate lock file
pip freeze > requirements-lock.txt

# Install from lock file
pip install -r requirements-lock.txt
```

### 6.4 Documentation

Document dependency decisions:

```markdown
# In docs/ or commit messages

## Dependency Decision: sentence-transformers

**Date**: 2026-02-25
**Decision**: Add sentence-transformers for embedding generation
**Rationale**: Industry-standard library, good model selection, Apache 2.0 license
**Trade-offs**: ~500MB download for models, but necessary for RAG
**Alternatives Considered**: OpenAI API (cost), custom embeddings (complexity)
```

---

## 7. Security Monitoring

### 7.1 Regular Audits

```bash
# Run quarterly or before releases
pip-audit -r docs/KB/Vector_RAG/requirements.txt

# Check for high-severity issues
pip-audit -r docs/KB/Vector_RAG/requirements.txt --severity high
```

### 7.2 Automated Monitoring (GitHub Dependabot)

Consider enabling Dependabot (future):

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/docs/KB/Vector_RAG"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

---

## 8. Minimal Dependency Philosophy

### 8.1 When to Avoid Dependencies

Consider alternatives before adding dependencies for:

- **Simple tasks**: Use stdlib (`json`, `pathlib`, `re`, etc.)
- **Oneliners**: Don't add a package for a single function
- **Active development**: Avoid unmaintained packages
- **Niche use**: Don't add dependency used by single script

### 8.2 Stdlib Alternatives

| Task                | Instead of                | Use stdlib          |
| ------------------- | ------------------------- | ------------------- |
| File operations     | `pathlib2`                | `pathlib`           |
| HTTP requests (basic) | `requests`              | `urllib.request`    |
| JSON parsing        | `ujson`, `orjson`         | `json`              |
| Date/time           | `arrow`, `pendulum`       | `datetime`          |
| Argument parsing    | `click`, `typer`          | `argparse`          |
| Configuration       | `python-decouple`         | `os.environ`, `configparser` |

**Trade-off**: stdlib is less ergonomic but has zero dependencies and is always available.

---

## 9. Contribution Guidelines

### 9.1 Adding Dependencies in PRs

When adding a dependency:

1. Add to appropriate requirements.txt
2. Document in PR description:
   - Why needed
   - License verified
   - Security audit passed
   - Alternatives considered
3. Update this SOP if it's a major dependency

### 9.2 PR Checklist

- [ ] Dependency necessity justified
- [ ] License compatible (MIT/Apache/BSD)
- [ ] No known vulnerabilities (`pip-audit`)
- [ ] Added to requirements.txt with version constraint
- [ ] Tested locally
- [ ] Documentation updated

---

## 10. Migration Plan (Future)

If dependencies become problematic:

```bash
# 1. Audit current dependencies
pip-licenses --format=markdown > docs/dependency-audit.md
pip-audit -r docs/KB/Vector_RAG/requirements.txt

# 2. Identify replacements
# - Heavy dependencies → lighter alternatives
# - Unmaintained → maintained forks
# - Incompatible licenses → compatible alternatives

# 3. Test migration
# ... create test branch ...

# 4. Document migration
# ... update docs/ARCHITECTURE.md ...
```

---

## ✅ Quick Reference

```bash
# Before adding dependency
pip-audit -r docs/KB/Vector_RAG/requirements.txt  # Check security
pip-licenses --from=classifier                     # Check licenses

# Add dependency
echo "package>=1.0.0,<2.0.0" >> docs/KB/Vector_RAG/requirements.txt
pip install -r docs/KB/Vector_RAG/requirements.txt

# Test
python scripts/validate_corpus.py
pip check

# Update dependency
pip install --upgrade package-name
pip freeze | grep package-name  # Note new version
# Update requirements.txt manually

# Audit dependencies
pip-audit -r docs/KB/Vector_RAG/requirements.txt
pip list --outdated
```

**Remember**: Fewer dependencies = less surface area for vulnerabilities and compatibility issues!
