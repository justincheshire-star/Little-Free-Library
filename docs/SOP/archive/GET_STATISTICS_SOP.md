# GET_STATISTICS_SOP v1.1.0

**Last Updated**: February 5, 2026  
**Status**: Active  
**Scope**: Project statistics collection, analysis, and reporting  
**Applies To**: LocalAgents repository

---

## 🎯 Purpose

This SOP defines the process for generating comprehensive project statistics reports covering quantity, quality, and velocity metrics. These reports provide stakeholders with data-driven insights into project health, progress, and sustainability for the LocalAgents application.

## 📋 When to Run

### Regular Schedule

- **Monthly**: First working day of each month (recommended)
- **Milestone**: At completion of major features or phases
- **On-Demand**: When requested by stakeholders or for portfolio presentation

### Triggers

- Major release or deployment
- Quarterly reviews
- Team scaling decisions
- Funding or investment discussions
- Annual planning cycles
- Significant architectural changes

## 🔍 Scope of Analysis

### Three Pillars

1. **Quantity Metrics** - What was built
2. **Quality Metrics** - How well it was built
3. **Velocity Metrics** - How fast it was built

---

## 📊 Data Collection Process

### Step 1: Collect Core Metrics

Run these commands from repository root (`/workspaces/LocalAgents`):

#### 1.1 Source Code Metrics

```bash
# Total Python source files (excluding tests)
find . -type f -name "*.py" \
  ! -path "*/node_modules/*" \
  ! -path "*/.venv/*" \
  ! -path "*/venv/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/tests/*" \
  ! -path "*/test_*.py" \
  ! -name "*_test.py" \
  ! -name "test_*.py" | wc -l

# Total Python source lines (excluding tests)
find . -type f -name "*.py" \
  ! -path "*/node_modules/*" \
  ! -path "*/.venv/*" \
  ! -path "*/venv/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/tests/*" \
  ! -path "*/test_*.py" \
  ! -name "*_test.py" \
  ! -name "test_*.py" \
  -exec wc -l {} + 2>/dev/null | tail -1

# Total TypeScript/JavaScript source files (frontend)
find apps/web apps/desktop -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/out/*" \
  ! -name "*.test.*" \
  ! -name "*.spec.*" 2>/dev/null | wc -l

# Total TypeScript/JavaScript source lines (frontend)
find apps/web apps/desktop -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  ! -path "*/build/*" \
  ! -path "*/out/*" \
  ! -name "*.test.*" \
  ! -name "*.spec.*" \
  -exec wc -l {} + 2>/dev/null | tail -1

# Backend services breakdown
find services -type f -name "*.py" ! -name "test_*.py" ! -path "*/__pycache__/*" | wc -l

# Frontend components breakdown
find apps/web/components -type f \( -name "*.tsx" -o -name "*.ts" \) 2>/dev/null | wc -l
```

#### 1.2 Test Metrics

```bash
# Python test files
find tests -type f -name "test_*.py" 2>/dev/null | wc -l

# Python test lines
find tests -type f -name "test_*.py" -exec wc -l {} + 2>/dev/null | tail -1

# TypeScript/JavaScript test files
find . -type f \( -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.spec.ts" -o -name "*.spec.tsx" \) \
  ! -path "*/node_modules/*" 2>/dev/null | wc -l

# Test lines
find . -type f \( -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.spec.ts" -o -name "*.spec.tsx" \) \
  ! -path "*/node_modules/*" \
  -exec wc -l {} + 2>/dev/null | tail -1

# Integration/E2E tests
find eval -type f -name "*.jsonl" -o -name "*.py" 2>/dev/null | wc -l
```

#### 1.3 Documentation Metrics

```bash
# Documentation files
find docs -type f -name "*.md" | wc -l

# Documentation lines
find docs -type f -name "*.md" -exec wc -l {} + | tail -1

# Session reviews
find docs/session-reviews -name "*.md" ! -name "INDEX.md" ! -name "*README*" 2>/dev/null | wc -l

# ADR (Architecture Decision Records)
find docs/ADR -type f -name "*.md" 2>/dev/null | wc -l

# SOP files
find docs/sop -type f -name "*.md" ! -name "INDEX.md" 2>/dev/null | wc -l

# Root documentation files
find . -maxdepth 1 -name "*.md" | wc -l
```

#### 1.4 Git Metrics

```bash
# Total commits
git log --oneline --all | wc -l

# First commit date
git log --format="%ai" --all --reverse | head -1

# Last commit date
git log --format="%ai" --all | head -1

# Active development days
git log --all --format="%ai" | awk '{print $1}' | sort -u | wc -l

# Commits by date (for velocity analysis)
git log --all --format="%ai" | awk '{print $1}' | sort | uniq -c | sort -rn | head -10

# Contributors
git shortlog -sn --all

# Total changes
git log --shortstat --all | grep "files changed" | \
  awk '{files+=$1; inserted+=$4; deleted+=$6} END {print "Files: " files " Insertions: " inserted " Deletions: " deleted}'

# Commit type breakdown (if using conventional commits)
echo "Feature commits:" && git log --all --oneline --grep="^feat:" | wc -l
echo "Fix commits:" && git log --all --oneline --grep="^fix:" | wc -l
echo "Docs commits:" && git log --all --oneline --grep="^docs:" | wc -l
echo "Refactor commits:" && git log --all --oneline --grep="^refactor:" | wc -l
```

#### 1.5 Architecture Metrics

```bash
# Backend services
ls -d services/*/ 2>/dev/null | wc -l

# API routes/endpoints
find services/api -type f -name "*.py" ! -name "__init__.py" ! -name "test_*.py" 2>/dev/null | wc -l

# Agent implementations
find services/agent -type f -name "*.py" ! -name "__init__.py" ! -name "test_*.py" 2>/dev/null | wc -l

# Tools implemented
find services/tools -type f -name "*.py" ! -name "__init__.py" ! -name "test_*.py" 2>/dev/null | wc -l

# Frontend pages
find apps/web/app -type f \( -name "page.tsx" -o -name "layout.tsx" \) 2>/dev/null | wc -l

# React components
find apps/web/components -type f -name "*.tsx" 2>/dev/null | wc -l

# Configuration files
find config -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) 2>/dev/null | wc -l

# Docker/Infrastructure files
ls docker-compose*.yml infra/docker-compose*.yml 2>/dev/null | wc -l

# K8s manifests
find infra/k8s -type f -name "*.yaml" -o -name "*.yml" 2>/dev/null | wc -l

# Database migration scripts
find . -path "*/alembic/versions/*.py" -o -path "*/migrations/*.py" 2>/dev/null | wc -l
```

#### 1.6 Security & Quality Metrics

```bash
# Python security check (if safety is installed)
safety check --json 2>/dev/null | jq '.vulnerabilities | length' || echo "N/A"

# npm audit (for frontend dependencies)
cd apps/web && npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities // empty' && cd ../..

# Python type hints coverage (rough estimate)
find services -name "*.py" ! -name "test_*.py" -exec grep -l "def.*->" {} \; 2>/dev/null | wc -l

# Linting configuration files
ls .pylintrc .flake8 .ruff.toml pyproject.toml .eslintrc* 2>/dev/null | wc -l
```

#### 1.7 Dependency Metrics

```bash
# Python packages
cat pyproject.toml | grep -c "^[a-zA-Z].*=" 2>/dev/null || \
  cat requirements*.txt | grep -v "^#" | grep -v "^$" | wc -l

# Node packages (frontend)
cat apps/web/package.json 2>/dev/null | jq '.dependencies | length'

# Desktop app packages
cat apps/desktop/package.json 2>/dev/null | jq '.dependencies | length'

# Workspace packages
find . -name "package.json" ! -path "*/node_modules/*" | wc -l
```

### Step 2: Calculate Derived Metrics

Using collected data, calculate:

```
Documentation-to-Code Ratio = Doc Lines / (Python Lines + TS Lines)
Test-to-Code Ratio = Test Lines / Source Lines
Test Coverage % = (Test Lines / Source Lines) × 100
Code Churn % = (Deletions / Insertions) × 100
Commits per Day = Total Commits / Active Days
Lines per Day = (Source + Test + Doc Lines) / Active Days
Project Duration = Last Commit Date - First Commit Date
Active Rate = (Active Days / Total Days) × 100
Backend-to-Frontend Ratio = Python Lines / TS Lines
```

### Step 3: Analyze Quality Indicators

#### Test Pass Rates

```bash
# Run Python tests (if virtual environment is activated)
source .venv/bin/activate 2>/dev/null && \
  pytest tests/ -v --tb=short 2>&1 | grep -E "passed|failed|error" | tail -5

# Check test configuration
cat pyproject.toml | grep -A 10 "\[tool.pytest"

# Frontend tests (if available)
cd apps/web && npm test 2>&1 | grep -E "Tests|PASS|FAIL" | head -10 && cd ../..
```

#### Code Quality Checks

```bash
# Python linting status (if ruff is available)
ruff check services/ tests/ 2>&1 | grep -E "error|warning" | wc -l

# Python type checking (if mypy is available)
mypy services/ 2>&1 | grep -E "error" | wc -l

# Frontend linting (if available)
cd apps/web && npm run lint 2>&1 | grep -E "error|warning" | tail -5 && cd ../..

# Check for type definitions
find . -name "types.py" -o -name "*.d.ts" | wc -l
```

### Step 4: Identify Development Phases

Analyze git history to identify major phases:

```bash
# Commits per week
git log --all --format="%ai" | awk '{print $1}' | \
  xargs -I {} date -d {} +%Y-W%V 2>/dev/null | sort | uniq -c

# Commits per month
git log --all --format="%ai" | awk '{print $1}' | \
  cut -d'-' -f1,2 | sort | uniq -c

# Major feature commits
git log --all --oneline --grep="feat:" | wc -l

# Documentation commits
git log --all --oneline --grep="docs:" | wc -l

# Bug fix commits
git log --all --oneline --grep="fix:" | wc -l

# Recent activity (last 30 days)
git log --all --since="30 days ago" --oneline | wc -l
```

---

## 📝 Report Generation

### Step 5: Create Report Structure

Create new report file: `docs/statistics/STATISTICS_REPORT_MMMDD_YYYY.md`

**Naming Convention**: `STATISTICS_REPORT_DEC19_2025.md` (3-letter month, 2-digit day, 4-digit year)

### Step 6: Report Sections (Required)

All reports MUST include these sections:

#### 1. Executive Summary

- Report metadata (date, type, status)
- Project timeline table (start date, current date, duration, active days)
- Headline metrics table comparing to previous report
- Health score summary

#### 2. Quantity Analysis

- Source code distribution
  - Python backend (services/, by module)
  - TypeScript frontend (apps/web, apps/desktop)
  - Configuration and infrastructure files
- Documentation volume (files, lines, types)
- Architecture components
  - Backend services (API, Agent, Tools, Style Tracker)
  - Frontend components
  - Database models and migrations
  - Infrastructure (Docker, K8s)

#### 3. Quality Analysis

- Test coverage metrics (by category, pass rates)
  - Python unit tests (pytest)
  - Integration tests
  - Evaluation framework (eval/)
- Code quality standards
  - Python: type hints, linting (ruff, mypy)
  - TypeScript: strict mode, ESLint
- Security compliance (vulnerabilities, dependency audits)
- Documentation quality (coverage by type, completeness)
- Architectural quality (organization, patterns, separation of concerns)

#### 4. Pacing & Velocity Analysis

- Development timeline (phases with dates and outputs)
- Velocity metrics
  - Commits per day
  - Lines per day (by language)
  - Features per week/month
- Productivity patterns
  - Weekly rhythm
  - Burst vs sustained development
  - Consistency metrics
- Feature delivery rate (time per feature by complexity)
- Code churn analysis (insertions vs deletions)

#### 5. Quality Highlights

- Exceptional metrics (5-star ratings)
- Areas of excellence
  - Architecture (agent framework, API design)
  - Process (SOPs, documentation)
  - Security (dependency management)
  - DevOps (containerization, CI/CD readiness)
- Recent achievements (last 2 weeks)

#### 6. Comparative Analysis

- Industry benchmarks comparison table
  - Similar Python/FastAPI projects
  - AI agent frameworks
  - Full-stack applications
- Team size context (equivalent team size estimation)
- Rating vs averages
- Technology-specific comparisons
  - Backend API complexity
  - Frontend sophistication
  - Documentation completeness

#### 7. Project Health Score

- Overall health score (out of 100)
- Category breakdown table with weights
  - Code Quality (25%)
  - Test Coverage (20%)
  - Documentation (20%)
  - Architecture (15%)
  - Velocity (10%)
  - Security (10%)
- Grade and interpretation (A/B/C/D/F scale)
- Trend indication (improving/stable/declining)

#### 8. Projections & Trends

- Growth trajectory (30/60/90 day projections)
  - Code volume
  - Feature completion
  - Documentation coverage
- Sustainability analysis
  - Positive indicators
  - Risk factors
  - Technical debt tracking
- Mitigation recommendations

#### 9. Next Milestones

- Short-term (7 days)
  - Immediate priorities
  - Quick wins
- Medium-term (30 days)
  - Feature milestones
  - Infrastructure improvements
- Long-term (90 days)
  - Strategic objectives
  - Architectural evolution

#### 10. Critical Success Factors

- What's working well (5+ items)
  - Technical decisions paying off
  - Process improvements
  - Tool/framework choices
- Areas for continued focus (3-5 items)
  - Risk mitigation
  - Investment priorities
  - Quality maintenance

#### 11. Summary Dashboard

- Quick reference card (ASCII box format)
- Key metrics at a glance
- Status indicators
- Trend arrows

#### 12. Lessons Learned & Best Practices

- What made the project successful
- Practices to continue
  - Development workflows
  - Documentation habits
  - Testing approaches
- Practices to add
  - New tools to adopt
  - Process improvements
- Practices to change
  - Identified inefficiencies
  - Technical debt to address

#### 13. Verification Commands

- All commands used to collect metrics
- Instructions for independent verification
- Expected output ranges
- Common troubleshooting

### Step 7: Compare to Previous Report

When available, calculate deltas:

```bash
# Get previous report
PREV_REPORT=$(ls -t docs/statistics/STATISTICS_REPORT_*.md | head -2 | tail -1)

# Extract key metrics from previous report (requires consistent formatting)
grep -E "Total Commits|Source Lines|Test Lines|Doc Lines" "$PREV_REPORT"

# Calculate percentage changes
# Format: (New - Old) / Old × 100
```

---

## 🎨 Report Formatting Standards

### Required Elements

1. **Front Matter**

   ```markdown
   # LocalAgents - Comprehensive Statistics Report

   **Generated**: December 19, 2025, 14:30 UTC
   **Report Type**: Full Quantitative, Qualitative, and Velocity Analysis
   **Status**: ✅ ALL DATA VERIFIED - Real measurements from live repository
   **Repository**: justincheshire-star/LocalAgents
   **Branch**: Prime
   ```

2. **Tables**

   - Use Markdown tables for all tabular data
   - Include units in headers (e.g., "Lines", "Days", "Percentage")
   - Right-align numeric columns
   - Include "Change from [Previous Date]" column when applicable

3. **Metrics Presentation**

   - Bold primary metrics
   - Include percentages in parentheses
   - Use emojis for status (✅ ⚠️ 🚧 🟢 ⭐ 📈 📉)
   - Show trends with arrows (↑ ↓ →)
   - Include context for significant changes

4. **Code Blocks**

   - Verification commands in ```bash blocks
   - Expected output in comments
   - Include command location context
   - Document any prerequisites (activated venv, etc.)

5. **Visual Separators**
   - Use `---` between major sections
   - Use `###` for subsections
   - Use `####` for sub-subsections
   - Consistent heading hierarchy

### Quality Standards

- ✅ All metrics must be verifiable via commands
- ✅ Include percentage changes from previous report
- ✅ Provide context for all numbers (industry benchmarks)
- ✅ Include both absolute and relative metrics
- ✅ Explain significance of key findings
- ✅ No fabricated data - real measurements only
- ✅ Include date/time of data collection
- ✅ Document any estimation methods used
- ✅ Note any commands that failed or returned N/A

---

## 📑 Index Management

### Step 8: Update Statistics Index

After creating report, update `docs/statistics/INDEX.md`:

```bash
# Run index generator
node scripts/gen-statistics-index.ts

# Or manually update with report entry
```

**Index Entry Format**:

```markdown
### [December 19, 2025](STATISTICS_REPORT_DEC19_2025.md)

**Health Score**: 92/100 (A - Excellent)  
**Commits**: 450 (+85 from Nov 19)  
**Python Lines**: 12,500 (+1,200)  
**TypeScript Lines**: 8,300 (+750)  
**Key Finding**: Strong multi-language development with comprehensive testing
```

### Step 9: Update Master Index

Add statistics section to `docs/INDEX.md`:

```markdown
## 📊 Statistics & Metrics

Comprehensive project statistics reports tracking quantity, quality, and velocity.

- **[Statistics Index](statistics/INDEX.md)** - All statistics reports
- Latest: [December 19, 2025](statistics/STATISTICS_REPORT_DEC19_2025.md)
```

### Step 10: Update README.md

Add or update statistics link in main README:

```markdown
## 📚 Documentation

- **Master Documentation Index**: See [docs/INDEX.md](docs/INDEX.md)
- **Statistics Reports**: [docs/statistics/INDEX.md](docs/statistics/INDEX.md) - Project metrics & analysis
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Session Reviews**: [docs/session-reviews/INDEX.md](docs/session-reviews/INDEX.md)
```

### Step 11: Update Historical Tracker

After completing current report, update `docs/statistics/HISTORICAL_TRACKER.md`:

**Purpose**: Maintain quantitative longitudinal tracking across all report checkpoints.

**Actions Required**:

1. **Add New Checkpoint to Over-Time Signal Table**
   - Extract core metrics from new report (commits, active days, source LOC, test LOC, docs LOC)
   - Calculate ratios (test/code %, docs/code ratio, commits/day)
   - Add as new column to main tracking table
   - Show all math explicitly (e.g., "344 ÷ 40 = 8.6 commits/day")

2. **Update Story of the Data Section**
   - Recalculate velocity deltas (new commits/day vs previous)
   - Recalculate documentation intensity growth
   - Recalculate test coverage changes
   - Show step-by-step arithmetic for all deltas

3. **Add New Inflection Point**
   - Document new checkpoint with context (e.g., "Mar 4 (Feature X completion)")
   - Include duration, commits, active rate, total output
   - Note key context (what was completed, architectural state)
   - Calculate deltas from previous checkpoint

4. **Update Derived Metrics Tables**
   - Add new row to Commit Velocity Trend table
   - Add new row to Documentation Intensity Trend table
   - Add new row to Test Coverage Trend table
   - Add new row to Total Output (Lines/Day) table
   - Recalculate all "Delta from prior" cells

5. **Add Verification Commands**
   - Document exact commands used for new report
   - Include expected output values
   - Maintain consistency with prior checkpoints

6. **Update Bottom-Line Narrative**
   - Extend trend descriptions to include new data point
   - Update momentum assessment
   - Refresh confidence/maintainability observations

**Example Update (March 2026 report)**:

```markdown
| Metric | Dec 19, 2025 | Jan 2, 2026 | Feb 4, 2026 | Mar 4, 2026 | What changed & why it matters |
|--------|-------------:|------------:|------------:|------------:|-------------------------------|
| **Commits (total)** | 29 | 101 | 344 | 520 | Continued acceleration to next milestone. |
| **Active days / Active rate** | 5 / **100%** | 13 / **68.4%** | 40 / **76.9%** | 60 / **80.0%** | Active rate recovering toward initial burst levels. |
| **Commits/day (on active days)** | **5.8** (29 ÷ 5) | **7.77** (101 ÷ 13) | **8.6** (344 ÷ 40) | **8.67** (520 ÷ 60) | Velocity stabilizing at high plateau. |
```

**Quality Standards**:
- ✅ All math shown explicitly (no calculated-only values)
- ✅ Maintain consistent measurement definitions (note any changes)
- ✅ Cross-reference source report for accuracy
- ✅ Update all derived metrics tables
- ✅ Extend trends narratives (don't just append)
- ✅ Document any reality checks (measurement drift, definition changes)

**Commit Message**:
```
docs: Update historical tracker with [Month] [Year] checkpoint

Add [Month] [Year] statistics to HISTORICAL_TRACKER.md:
- New checkpoint to over-time signal table
- Updated velocity/docs/test trend calculations
- Extended inflection points with [feature/milestone] context
- Recalculated all derived metrics tables
```

---

## 🔧 Automation Scripts

### statistics-index-generator.ts (To Be Created)

Location: `scripts/gen-statistics-index.ts`

```typescript
// Auto-generates docs/statistics/INDEX.md from report files
// Scans docs/statistics/STATISTICS_REPORT_*.md files
// Extracts front matter (date, health score, key metrics)
// Sorts by date (newest first)
// Generates markdown with links and summary table
```

**Requirements**:

1. Scan `docs/statistics/STATISTICS_REPORT_*.md` files
2. Extract front matter and key metrics
3. Sort by date (newest first)
4. Generate markdown with links
5. Include summary table at top
6. Handle missing or malformed files gracefully

### Quick Statistics Script (To Be Created)

Location: `scripts/quick-stats.sh` or `scripts/quick-stats.ts`

```bash
#!/bin/bash
# Runs core metrics commands and outputs to console
# Useful for quick health checks without full report

echo "=== LocalAgents Quick Statistics ==="
echo "Generated: $(date)"
echo ""

echo "Python Source Files: $(find services -name '*.py' ! -name 'test_*.py' | wc -l)"
echo "Python Test Files: $(find tests -name 'test_*.py' | wc -l)"
echo "TypeScript Files: $(find apps -name '*.tsx' -o -name '*.ts' | wc -l)"
echo "Documentation Files: $(find docs -name '*.md' | wc -l)"
echo "Total Commits: $(git log --oneline --all | wc -l)"
echo "Active Days: $(git log --all --format='%ai' | awk '{print $1}' | sort -u | wc -l)"
```

---

## 📋 Checklist

When running this SOP, complete these tasks:

### Data Collection ✅

- [ ] Activate Python virtual environment (`source .venv/bin/activate`)
- [ ] Run all core metrics commands (Section 1.1-1.7)
- [ ] Record outputs in temporary file or note-taking app
- [ ] Calculate derived metrics (Section 2)
- [ ] Analyze quality indicators (Section 3)
- [ ] Identify development phases (Section 4)
- [ ] Note any commands that failed or need adjustment

### Report Generation ✅

- [ ] Create report file with standard naming convention
- [ ] Include all 13 required sections
- [ ] Add verification commands section with LocalAgents-specific commands
- [ ] Compare to previous report (if available)
- [ ] Include percentage changes with context
- [ ] Verify all metrics are accurate and reproducible

### Formatting ✅

- [ ] Front matter with date, status, and repository info
- [ ] Tables formatted consistently with right-aligned numbers
- [ ] Code blocks with syntax highlighting and comments
- [ ] Visual separators between major sections
- [ ] Emojis for status indicators (✅ ⚠️ 📈)
- [ ] Quick reference card (ASCII box format)
- [ ] Links properly formatted (not in backticks)

### Quality Checks ✅

- [ ] All numbers verifiable via documented commands
- [ ] No fabricated or estimated data (unless explicitly documented)
- [ ] Industry comparisons included with sources
- [ ] Significance explained for key findings
- [ ] Previous report deltas calculated correctly
- [ ] Health score justified with clear methodology
- [ ] Trends supported by data

### Index Updates ✅

- [ ] Update `docs/statistics/INDEX.md` with new report entry
- [ ] Update `docs/INDEX.md` (master documentation index)
- [ ] Update `README.md` if first statistics report
- [ ] **Update `docs/statistics/HISTORICAL_TRACKER.md` with new checkpoint**
  - [ ] Add new column to over-time signal table
  - [ ] Recalculate all velocity/docs/test trend deltas
  - [ ] Add new inflection point with context
  - [ ] Update all derived metrics tables
  - [ ] Extend bottom-line narrative
  - [ ] Add verification commands for new checkpoint
- [ ] Verify all links work (test in GitHub preview)
- [ ] Run index generator script (when available)

### Git Operations ✅

- [ ] Stage new report file
- [ ] Stage index updates (statistics, master, README)
- [ ] **Stage historical tracker updates**
- [ ] Commit with descriptive message (e.g., "docs: add statistics report for Dec 19, 2025")
- [ ] Commit historical tracker separately or together (use separate commit for clarity)
- [ ] Push to remote repository
- [ ] Verify report renders correctly on GitHub

---

## 🎯 Success Criteria

A statistics report is considered complete when:

1. ✅ All 13 required sections present and complete
2. ✅ All metrics verifiable via documented commands
3. ✅ Commands adapted for LocalAgents structure (Python + TypeScript)
4. ✅ Comparison to previous report included (if applicable)
5. ✅ Health score calculated and justified with clear methodology
6. ✅ Projections and trends provided with supporting data
7. ✅ Lessons learned documented with specific examples
8. ✅ Indexes updated (statistics, master, README as needed)
9. ✅ **Historical tracker updated with new checkpoint data**
10. ✅ Committed and pushed to repository (branch: Prime or Rust)
11. ✅ Links verified working in GitHub rendering
12. ✅ Report accessible to all stakeholders
13. ✅ All verification commands tested and working

---

## 🚨 Common Issues & Solutions

### Issue: Python Commands Return Empty

**Symptoms**: `find` commands for `.py` files return 0 results

**Solutions**:

1. Verify working directory is repository root (`/workspaces/LocalAgents`)
2. Check if `.venv` is properly excluded in paths
3. Verify `services/` directory exists and contains Python files
4. Check file permissions (files should be readable)

### Issue: Virtual Environment Not Activated

**Symptoms**: `pytest` or `ruff` commands not found

**Solutions**:

1. Activate venv: `source .venv/bin/activate`
2. Verify venv exists: `ls -la .venv/`
3. Install dependencies if needed: `pip install -r requirements-dev.txt`
4. Check `pyproject.toml` for correct tool configurations

### Issue: Node Commands Fail

**Symptoms**: `npm` commands in apps/web or apps/desktop fail

**Solutions**:

1. Check if `node_modules` exists: `ls apps/web/node_modules`
2. Install dependencies: `cd apps/web && npm install`
3. Verify Node.js is installed: `node --version`
4. Check `package.json` exists in target directory

### Issue: Git Statistics Incomplete

**Symptoms**: Commit count seems low, missing dates

**Solutions**:

1. Use `--all` flag: `git log --all --oneline | wc -l`
2. Fetch all branches: `git fetch --all`
3. Verify repository is not shallow clone: `git log --all | head -20`
4. Check `.git` folder is intact: `ls -la .git/`

### Issue: Percentages Don't Match Expected

**Symptoms**: Calculated growth rates seem incorrect

**Solutions**:

1. Verify previous report metrics are accurate
2. Check date ranges align (comparing same timeframe)
3. Recalculate manually: `(New - Old) / Old × 100`
4. Document methodology for complex calculations
5. Consider if major refactoring affected line counts

### Issue: Large File Counts Slow Down

**Symptoms**: Commands taking >30 seconds

**Solutions**:

1. Increase `find` efficiency: use `-maxdepth` where appropriate
2. Exclude more paths: add `! -path "*/target/*"` for any build dirs
3. Run metrics collection in background or off-hours
4. Cache intermediate results in temp files
5. Consider using `fd` instead of `find` for better performance

### Issue: Test Commands Fail

**Symptoms**: `pytest` or `npm test` returns errors

**Solutions**:

1. Don't let test failures block report generation
2. Document test status as "Tests Failed - See Details"
3. Include test error summary in report
4. Still collect other metrics
5. Mark test section as "⚠️ Needs Investigation"

---

## 📚 Related Documentation

- [DOCUMENTATION_SOP.md](DOCUMENTATION_SOP.md) - Documentation maintenance standards
- [SESSION_REVIEW_SOP.md](SESSION_REVIEW_SOP.md) - Session summary process
- [DEPENDENCY_MANAGEMENT_SOP.md](DEPENDENCY_MANAGEMENT_SOP.md) - Package management
- [MEASUREMENT_MODEL.md](MEASUREMENT_MODEL.md) - Metrics and thresholds
- [docs/ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture overview
- [docs/statistics/INDEX.md](../statistics/INDEX.md) - Statistics reports index
- [docs/statistics/HISTORICAL_TRACKER.md](../statistics/HISTORICAL_TRACKER.md) - Longitudinal metrics tracking

---

## 🔄 Version History

### v1.1.0 (February 5, 2026)

**Added Historical Tracker Integration**

- Added Step 11: Update Historical Tracker after report generation
- Integrated HISTORICAL_TRACKER.md maintenance into standard workflow
- Updated checklist to include historical tracker updates
- Updated success criteria to require tracker updates
- Documented process for adding new checkpoints
- Added example showing how to extend over-time signal table
- Specified quality standards for tracker updates
- Added commit message template for tracker updates

**Changes**:
- New Step 11 with detailed instructions for updating HISTORICAL_TRACKER.md
- Expanded "Index Updates" checklist with historical tracker sub-tasks
- Updated success criteria (9 items → 13 items)
- Modified Git Operations checklist to include historical tracker staging

**Rationale**: Historical tracking enables longitudinal analysis across all report checkpoints. By integrating tracker updates into the SOP, we ensure consistent quantitative trend documentation without qualitative supposition.

---

### v1.0.0 (December 19, 2025)

**Initial Release - Adapted for LocalAgents**

- Adapted from Project Universe template
- Modified for Python + TypeScript stack
- Added LocalAgents-specific directory structure
- Customized commands for:
  - Python backend (services/, tests/)
  - Next.js frontend (apps/web/)
  - Tauri desktop app (apps/desktop/)
  - Docker/K8s infrastructure
- Updated metrics for AI agent framework context
- Added evaluation framework tracking (eval/)
- Included session reviews and ADRs in documentation metrics
- Adapted for monorepo structure with multiple package.json files

**Based On**: GET_STATISTICS_SOP v1.0.0 (Project Universe template)

**Commands Verified**: All commands tested and adapted for LocalAgents structure

**Technology Stack**:

- Backend: Python 3.x, FastAPI (assumed)
- Frontend: TypeScript, React, Next.js
- Desktop: Tauri, Rust + TypeScript
- Infrastructure: Docker, Kubernetes
- Testing: pytest, Jest/Vitest (assumed)
- Documentation: Markdown, comprehensive SOP system

---

## 📞 Support

For questions or improvements to this SOP:

1. Check Related Documentation section for context
2. Review previous statistics reports for examples (when available)
3. Verify commands work in LocalAgents repository
4. Test commands in development container environment
5. Create issue with label `sop:statistics` or `documentation`
6. Document any discovered patterns or improvements
7. Submit PR for SOP enhancements

---

## 🔍 LocalAgents-Specific Notes

### Virtual Environment

Always activate the Python virtual environment before running Python-related commands:

```bash
source .venv/bin/activate
```

### Multi-Language Nature

LocalAgents is a hybrid Python/TypeScript project:

- Backend services in Python
- Web frontend in TypeScript/React
- Desktop app in TypeScript/Rust
- Report should cover both ecosystems equally

### Agent Framework Context

When analyzing architecture:

- Track agent implementations separately
- Count tool implementations
- Monitor RAG pipeline components
- Document conversation/session management

### Development Container

Commands are designed to work in the Debian-based dev container environment.

---

**Next Review**: January 19, 2026 (after first usage)  
**Update Frequency**: As needed based on process improvements  
**Owner**: Development Team  
**Status**: ✅ Active and ready for use

---

_This SOP enables any IDE agent or developer to generate comprehensive, verifiable, stakeholder-ready statistics reports following the LocalAgents project standards._
