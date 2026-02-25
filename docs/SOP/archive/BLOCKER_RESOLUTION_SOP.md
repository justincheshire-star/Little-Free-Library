# Blocker Resolution SOP

**Status**: Active  
**Owner**: Development Team  
**Version**: 1.0.0  
**Created**: January 15, 2026  
**Last Updated**: January 15, 2026  
**Trigger**: Discovery of critical blocker (B-XXX) affecting user functionality  
**RACI**: R=Developer, A=Tech Lead, C=Team, I=PM  
**SLA**: Initial triage within 1 hour, resolution plan within 4 hours

---

## 🎯 Purpose

Establish systematic, fact-driven approach to resolving critical blockers in LocalAgent Studio. Ensures consistent investigation, root cause analysis, and prevention of recurrence across cross-stack issues (YAML ↔ Rust ↔ IPC ↔ TypeScript ↔ React).

**Failure Modes & Controls**:

- Ad-hoc debugging → wasted effort → require layered localization before fixes
- Symptom fixes only → blocker recurs → mandate invariant tests per resolution
- Contract drift undetected → runtime crashes → enforce schema validation in CI

---

## 📋 Scope

This SOP applies to:

- **Critical Blockers (B-XXX)**: Issues preventing core user functionality
- **Cross-Stack Issues**: Problems spanning data/config, backend, IPC, frontend
- **Desktop App Crashes**: User-visible failures in Tauri desktop application
- **Data/Schema Failures**: YAML parse errors, IPC contract mismatches

This SOP does NOT apply to:

- Minor bugs or enhancements (use standard PR process)
- Performance optimizations (use separate performance SOP)
- Infrastructure/deployment issues (use deployment SOP)

---

## 🏗️ Architecture Layers Reference

All LocalAgent Studio blockers should be analyzed using this layer model:

| Layer  | Component     | Responsibility                          | Key Files/Dirs                         |
| ------ | ------------- | --------------------------------------- | -------------------------------------- |
| **L0** | Environment   | OS, runtime versions, dependencies      | `.venv/`, `Cargo.toml`, `package.json` |
| **L1** | Data/Config   | YAML configs, schemas, validation       | `config/*.yaml`, database schemas      |
| **L2** | Domain Logic  | Rust core services, business logic      | `crates/localagent-*/src/`             |
| **L3** | Transport/IPC | Tauri commands, API boundaries          | `commands/*.rs`, `lib/api.ts`          |
| **L4** | UI/Frontend   | React components, TypeScript, rendering | `app/**/*.tsx`, `components/`          |

**Debugging Rule**: Start from the layer closest to the symptom, then work backwards through dependencies.

---

## 📝 Blocker Resolution Process

### Phase A: Reproduce & Document (1-2 hours)

**Goal**: Create deterministic, minimal reproduction that anyone on team can execute.

#### A.1 Collect Blocker Metadata

Create or update entry in `docs/status/BLOCKERS.md`:

```markdown
### B-XXX: [Brief Title] (CRITICAL/HIGH/MEDIUM)

**Status**: 🔴 Active  
**Severity**: Critical  
**Affects**: [Specific feature/page]  
**Discovered**: [Date]  
**Branch**: [branch-name] (vX.X.X)

**Description**:
[1-2 sentence description of user-facing symptom]

**Root Cause**:
[TBD - fill after Phase B]
```

#### A.2 Capture Evidence

Required artifacts:

- [ ] **Error message**: Exact text user sees (screenshot if UI)
- [ ] **Logs**: Rust stderr/stdout from desktop app
- [ ] **Browser console**: JavaScript errors from webview (if applicable)
- [ ] **Reproduction steps**: Numbered list (3-5 steps maximum)
- [ ] **Environment**: OS, branch, commit SHA, clean vs dirty install

**Template**:

```markdown
**Reproduction Steps**:

1. [Step 1 - e.g., "Install MSI v0.6.1 on clean Windows 11"]
2. [Step 2 - e.g., "Launch LocalAgent Studio"]
3. [Step 3 - e.g., "Navigate to Models page"]
4. **Expected**: [What should happen]
5. **Actual**: [What actually happens - include error message]

**Logs**:
```

[Paste relevant log excerpts]

```

```

#### A.3 Verify Reproducibility

- [ ] Reproduce on **clean environment** (fresh install, no user data)
- [ ] Reproduce on **development environment** (local build from same commit)
- [ ] Confirm **stability**: Does it fail 100% of time, or intermittently?

**Exit Criteria**: Any developer can follow reproduction steps and see same failure.

---

### Phase B: Localize by Layer (2-4 hours)

**Goal**: Identify which layer(s) are failing using systematic decomposition.

#### B.1 Layer Analysis Checklist

For each layer, ask: **"Is this layer behaving as expected?"**

Work **bottom-up** (data → domain → transport → UI) or **top-down** (UI → transport → domain → data) depending on symptom location.

##### L0: Environment Verification

- [ ] **Dependencies installed**: `cargo check`, `npm ci`, `pip install -r requirements-dev.txt`
- [ ] **Correct branch/commit**: `git log -1 --oneline`, compare to blocker metadata
- [ ] **Environment variables**: Check for missing/incorrect env vars
- [ ] **Build artifacts fresh**: `cargo clean`, rebuild to eliminate stale binaries

**Tests to Run**:

```bash
# Rust environment
cargo --version
cargo check --all-features

# Python environment
python --version
pip list | grep -E "(pytest|pydantic|fastapi)"

# Node environment
node --version
npm list --depth=0
```

##### L1: Data/Config Validation

- [ ] **YAML/JSON syntax valid**: Run linter (`yamllint`, `jsonlint`)
- [ ] **Schema compliance**: Deserialize config in isolation
- [ ] **Required fields present**: Check all expected keys exist
- [ ] **Value types correct**: Validate types match schema

**Tests to Run**:

```bash
# YAML validation
yamllint config/model_catalog.yaml

# Python schema test
pytest tests/test_config_schemas.py -v

# Rust deserialization test
cargo test --package localagent-config -- load_catalog
```

**If L1 fails**: Document missing/invalid fields, proceed to fix in Phase C.

##### L2: Domain Logic (Rust Core)

- [ ] **Service initializes**: `AppCore::new()` succeeds
- [ ] **Data loads correctly**: `core.model_catalog()` returns non-empty
- [ ] **Business logic sound**: Core methods return expected results
- [ ] **Error handling correct**: Failures produce structured errors, not panics

**Tests to Run**:

```bash
# Core service tests
cargo test --package localagent-core

# Integration tests
cargo test --package localagent-core --test integration_tests
```

**If L2 fails**: Check for logic errors, missing data, or incorrect error handling.

##### L3: Transport/IPC Boundary

- [ ] **IPC command registered**: Command listed in `main.rs` invoke handler
- [ ] **Response shape matches frontend**: Compare Rust struct to TS interface
- [ ] **Serialization works**: Can serialize response to JSON without errors
- [ ] **Error responses structured**: Errors follow consistent format

**Tests to Run**:

```bash
# IPC command tests
cargo test --package localagent-tauri -- commands

# Contract validation (if implemented)
cargo test -- ipc_contract
```

**Critical Check**: Capture raw JSON returned by IPC command:

```rust
// Temporary debug logging
let response = models_catalog(core).await?;
eprintln!("IPC Response JSON: {}", serde_json::to_string_pretty(&response)?);
```

Compare JSON structure to TypeScript interface definition.

**If L3 fails**: Document contract mismatch, proceed to contract alignment in Phase C.

##### L4: UI/Frontend

- [ ] **Component renders without crash**: Mock data produces valid JSX
- [ ] **Error states handled**: Component shows error UI, doesn't throw
- [ ] **Loading states handled**: Component shows loading UI during async ops
- [ ] **Null/undefined guarded**: All property accesses use optional chaining or fallbacks

**Tests to Run**:

```bash
# Component tests (if implemented)
npm test -- ModelsPage.test.tsx

# Type checking
npm run type-check
```

**Critical Check**: Review component code for unsafe property access:

```typescript
// ❌ UNSAFE - will crash if catalog is null/undefined
const models = catalog.core_models;

// ✅ SAFE - degrades gracefully
const models = catalog?.core_models ?? [];
```

**If L4 fails**: Fix null/undefined handling, add defensive guards.

#### B.2 Create Layer Failure Matrix

Document findings in `BLOCKERS.md`:

```markdown
**Layer Analysis**:

| Layer             | Status     | Finding                                                 |
| ----------------- | ---------- | ------------------------------------------------------- |
| L0: Environment   | ✅ Pass    | All dependencies installed, correct commit              |
| L1: Data/Config   | ❌ FAIL    | `model_catalog.yaml` missing `sizing` field on 7 models |
| L2: Domain Logic  | ⚠️ Blocked | Cannot proceed - data invalid                           |
| L3: Transport/IPC | ✅ Pass    | Response structure correct (verified JSON)              |
| L4: UI/Frontend   | ⚠️ Blocked | Cannot test - backend returns error                     |

**Primary Failure**: L1 (Data/Config)
**Secondary Issues**: None identified
```

**Exit Criteria**: Identified which layer(s) failed and documented specific findings.

---

### Phase C: Define Invariants & Fix (4-8 hours)

**Goal**: For each failing layer, define testable invariants and implement fixes that enforce them.

#### C.1 Invariant Definition Template

For each failing layer, document invariants:

```markdown
**Layer**: L1 (Data/Config)

**Invariants**:

1. Every `core_models[i]` must have `id: string` field
2. Every `core_models[i]` must have `sizing` object with:
   - `disk_gb: float`
   - `memory_gb_min: int`
   - `memory_gb_recommended: int`
3. `catalog_version` must be positive integer
4. `core_models` array must have length > 0

**Test Implementation**: `tests/test_model_catalog_schema.py`
```

#### C.2 Layer-Specific Fix Guidelines

##### L1 Fixes: Data/Config

1. **Add schema validation test** (Python example):

```python
# tests/test_config_schemas.py
import yaml
from pathlib import Path

REQUIRED_SIZING_KEYS = {"disk_gb", "memory_gb_min", "memory_gb_recommended"}

def test_model_catalog_has_sizing_for_all_core_models():
    """Validate all models in catalog have required sizing field."""
    data = yaml.safe_load(Path("config/model_catalog.yaml").read_text())
    core_models = data.get("core_models", [])
    assert core_models, "core_models must not be empty"

    missing = []
    for i, model in enumerate(core_models):
        mid = model.get("id", f"<index {i}>")
        sizing = model.get("sizing")
        if not isinstance(sizing, dict):
            missing.append(f"{mid}: sizing field missing")
        elif not REQUIRED_SIZING_KEYS.issubset(sizing.keys()):
            missing_keys = REQUIRED_SIZING_KEYS - set(sizing.keys())
            missing.append(f"{mid}: sizing missing keys {missing_keys}")

    assert not missing, f"Schema violations:\n  " + "\n  ".join(missing)
```

2. **Fix data issues**: Add missing fields, correct types, validate syntax

3. **Add pre-commit hook** (optional):

```bash
# .git/hooks/pre-commit
#!/bin/bash
if git diff --cached --name-only | grep -q "config/.*\.yaml"; then
    echo "Validating YAML schemas..."
    pytest tests/test_config_schemas.py -v || exit 1
fi
```

##### L2 Fixes: Domain Logic (Rust)

1. **Add integration test**:

```rust
// crates/localagent-core/tests/catalog_tests.rs
#[test]
fn loads_default_model_catalog() {
    let core = AppCore::new_default().expect("core init failed");
    let catalog = core.model_catalog().expect("catalog must load");

    assert!(!catalog.core_models.is_empty(),
            "catalog.core_models must not be empty");

    // Validate each model has required fields
    for model in &catalog.core_models {
        assert!(!model.id.is_empty(), "model.id cannot be empty");
        assert!(model.sizing.is_some(),
                "model {} missing sizing", model.id);
    }
}
```

2. **Improve error messages**: Make failures descriptive

```rust
// Before (cryptic)
Err("failed to load catalog")

// After (descriptive)
Err(format!(
    "Failed to load model catalog from {}: {}. \
     Check YAML syntax and required fields.",
    catalog_path.display(),
    err
))
```

##### L3 Fixes: Transport/IPC Contract

1. **Lock in contract with snapshot test**:

```rust
// apps/desktop/src-tauri/src/commands/tests.rs
#[test]
fn models_catalog_response_matches_contract() {
    let core = create_test_core();
    let response = tokio_test::block_on(models_catalog(core))
        .expect("command should succeed");

    // Serialize to JSON
    let json = serde_json::to_value(&response).unwrap();

    // Assert required top-level keys
    assert!(json.get("catalog_version").is_some(),
            "missing catalog_version");
    assert!(json.get("core_models").and_then(|v| v.as_array()).is_some(),
            "core_models must be array");
    assert!(json.get("model_families").is_some(),
            "missing model_families");
    assert!(json.get("runtimes").is_some(),
            "missing runtimes");

    // Validate core_models structure
    let models = json["core_models"].as_array().unwrap();
    assert!(!models.is_empty(), "core_models cannot be empty");

    let first_model = &models[0];
    assert!(first_model.get("id").is_some(), "model missing id");
    assert!(first_model.get("sizing").is_some(), "model missing sizing");
}
```

2. **Add TS-side contract test** (Jest):

```typescript
// lib/api/__tests__/models-contract.test.ts
import { ModelCatalog } from "../api";

describe("models_catalog IPC contract", () => {
  it("validates mock response matches interface", () => {
    const mockResponse: ModelCatalog = {
      catalog_version: 1,
      core_models: [
        {
          id: "test-model",
          role: "coder",
          modality: "text",
          description: "Test model",
          installed: false,
          source_type: "huggingface",
          size_bytes: 1000000,
          path: null,
          detailed_description: "Detailed description",
          strengths: ["strength1"],
          watchouts: ["watchout1"],
          when_to_pick: "When testing",
          sizing: {
            disk_gb: 1.0,
            memory_gb_min: 2,
            memory_gb_recommended: 4,
            notes: "Test notes",
          },
          required: false,
          quantization: "Q4_K_M",
        },
      ],
      model_families: [],
      runtimes: {},
      runtimes_available: {},
      installed_models: [],
    };

    // If this compiles, contract is valid
    expect(mockResponse.catalog_version).toBe(1);
    expect(mockResponse.core_models).toHaveLength(1);
  });
});
```

##### L4 Fixes: UI/Frontend

1. **Add defensive guards**:

```typescript
// Before (unsafe)
const models = catalog.core_models;
const loadedIds = llmStatus.local_runtime.loaded_models.map((m) => m.model_id);

// After (safe)
const models = catalog?.core_models ?? [];
const loadedIds = new Set(
  llmStatus?.local_runtime?.loaded_models?.map((m) => m.model_id) ?? []
);
```

2. **Handle error states explicitly**:

```typescript
if (error) {
  return <ErrorNotice message={error.message} onRetry={loadData} />;
}

if (!catalog || !llmStatus) {
  return <PageLoading />;
}

// Now safe to access catalog.core_models
```

3. **Add component test**:

```typescript
// app/models/__tests__/ModelsPage.test.tsx
describe("ModelsPage", () => {
  it("handles missing catalog gracefully", () => {
    const { container } = render(<ModelsPage />);

    // Should show loading state, not crash
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("handles error state", () => {
    // Mock error response
    vi.mocked(modelsApi.getCatalog).mockResolvedValue({
      error: { message: "Catalog not loaded", code: "E001" },
    });

    render(<ModelsPage />);

    expect(screen.getByText(/catalog not loaded/i)).toBeInTheDocument();
  });
});
```

#### C.3 Implementation Checklist

For each fix:

- [ ] **Narrow scope**: Change only what violates the invariant
- [ ] **Add test first**: Write failing test, then fix
- [ ] **Verify test passes**: Run new test, confirm green
- [ ] **Run full suite**: Check for regressions (`cargo test`, `npm test`, `pytest`)
- [ ] **Manual verification**: Re-run Phase A reproduction steps

**Exit Criteria**: All invariant tests pass, blocker no longer reproduces.

---

### Phase D: Document & Prevent Recurrence (1-2 hours)

**Goal**: Ensure blocker cannot recur and learnings are captured.

#### D.1 Update Blocker Tracker

Update `docs/status/BLOCKERS.md`:

```markdown
**Resolution**:

1. **Data Fix** (L1):
   - Added `sizing` field to 7 models in `model_catalog.yaml`
   - Added schema validation test: `test_model_catalog_has_sizing_for_all_core_models`
2. **Contract Verification** (L3):
   - Added IPC contract test: `test_models_catalog_response_matches_contract`
   - Verified Rust struct matches TypeScript interface

**Files Changed**:

- `config/model_catalog.yaml` - Added sizing to 7 models
- `tests/test_config_schemas.py` - New schema validation test
- `apps/desktop/src-tauri/src/commands/tests.rs` - New contract test

**Workaround**:
[If temporary workaround exists, document here]

**Prevention**:

- [ ] Schema validation runs in CI
- [ ] Pre-commit hook validates YAML (optional)
- [ ] Contract tests run in Rust test suite
```

#### D.2 Add CI Validation (if not exists)

Ensure tests run automatically:

```yaml
# .github/workflows/tests.yml
- name: Validate config schemas
  run: pytest tests/test_config_schemas.py -v

- name: Rust contract tests
  run: cargo test --package localagent-tauri -- commands
```

#### D.3 Create Postmortem (for Critical blockers)

Add to `docs/postmortems/B-XXX_YYYY-MM-DD.md`:

```markdown
# B-XXX Postmortem: [Brief Title]

**Date**: YYYY-MM-DD  
**Duration**: [Hours from discovery to resolution]  
**Severity**: Critical  
**Impact**: [Number of users affected, features blocked]

## What Happened

[1-2 paragraphs: symptom, user impact, timeline]

## Root Cause

**Primary**: [Layer + specific issue]  
**Secondary**: [Contributing factors]

## Why It Happened

- [Systemic reason 1: e.g., "No schema validation in CI"]
- [Systemic reason 2: e.g., "Manual contract maintenance"]
- [Systemic reason 3: e.g., "Insufficient test coverage"]

## Resolution

[Brief summary of fix + tests added]

## Lessons Learned

**What Worked**:

- [Positive aspect of resolution process]

**What Didn't Work**:

- [Challenges encountered]

**Action Items**:

- [ ] [Preventive measure 1 - owner - due date]
- [ ] [Preventive measure 2 - owner - due date]
```

#### D.4 Update Documentation

- [ ] Update `CHANGELOG.md` with fix details
- [ ] Update `README.md` if blocker was architecture-related
- [ ] Update relevant SOPs if process failed
- [ ] Link blocker to related documentation

**Exit Criteria**: Blocker documented, tests in CI, recurrence prevented.

---

## 📊 Blocker Resolution Template

Copy this template when starting a new blocker resolution:

```markdown
# B-XXX Resolution: [Title]

**Blocker ID**: B-XXX  
**Discovered**: YYYY-MM-DD  
**Branch**: [branch-name]  
**Commit**: [SHA]  
**Assigned**: [Developer Name]

---

## Phase A: Reproduce (Target: 1-2 hours)

### A.1 Metadata ✅/❌

- [ ] Entry created in BLOCKERS.md
- [ ] Error message captured
- [ ] Logs collected (Rust + Browser)
- [ ] Screenshots/recordings obtained

### A.2 Reproduction Steps

1. [Step 1]
2. [Step 2]
3. [Step 3]
4. **Expected**: [...]
5. **Actual**: [...]

### A.3 Reproducibility ✅/❌

- [ ] Reproduced on clean environment
- [ ] Reproduced on dev environment
- [ ] Confirmed stable (100% failure rate)

---

## Phase B: Localize (Target: 2-4 hours)

### Layer Analysis

| Layer             | Status | Finding | Test Command |
| ----------------- | ------ | ------- | ------------ |
| L0: Environment   | ⬜     | [TBD]   | `[command]`  |
| L1: Data/Config   | ⬜     | [TBD]   | `[command]`  |
| L2: Domain Logic  | ⬜     | [TBD]   | `[command]`  |
| L3: Transport/IPC | ⬜     | [TBD]   | `[command]`  |
| L4: UI/Frontend   | ⬜     | [TBD]   | `[command]`  |

**Primary Failure Layer**: [TBD]

---

## Phase C: Fix & Test (Target: 4-8 hours)

### Invariants Defined

**Layer**: [L1/L2/L3/L4]

**Invariants**:

1. [Invariant 1]
2. [Invariant 2]
3. [Invariant 3]

**Test File**: [path/to/test]

### Changes Made

- [ ] Fix 1: [description] - [file path]
- [ ] Fix 2: [description] - [file path]
- [ ] Test 1: [description] - [file path]
- [ ] Test 2: [description] - [file path]

### Verification

- [ ] New tests pass: `[test command]`
- [ ] Full test suite passes
- [ ] Manual reproduction steps no longer fail

---

## Phase D: Document (Target: 1-2 hours)

- [ ] BLOCKERS.md updated with resolution
- [ ] CHANGELOG.md entry added
- [ ] CI validation added (if applicable)
- [ ] Postmortem created (if critical)

---

**Resolution Date**: YYYY-MM-DD  
**Total Time**: [X hours]  
**Status**: ✅ Resolved / 🚧 In Progress
```

---

## 🔍 Example: B-006 Resolution Walkthrough

This section shows the SOP applied to B-006 (Desktop Models page crash).

### Phase A: Reproduce

**Blocker Metadata**:

- **ID**: B-006
- **Discovered**: January 14, 2026
- **Branch**: Rust (v0.6.1)
- **Severity**: Critical

**Reproduction Steps**:

1. Install MSI v0.6.1 on Windows 11
2. Launch LocalAgent Studio
3. Click "Models" in sidebar
4. **Expected**: Models page loads with catalog
5. **Actual**: Error banner: "Failed to query model catalog: Model catalog not loaded"

**Evidence Collected**:

- Screenshot of error banner
- Rust logs showing YAML parse error
- Browser console showing no JavaScript errors (backend issue)

**Reproducibility**: 100% failure rate on clean install

### Phase B: Localize

**Layer Analysis Results**:

| Layer             | Status      | Finding                                           | Test Command                         |
| ----------------- | ----------- | ------------------------------------------------- | ------------------------------------ |
| L0: Environment   | ✅ Pass     | All dependencies correct                          | `cargo --version`                    |
| L1: Data/Config   | ❌ **FAIL** | `model_catalog.yaml` missing `sizing` on 7 models | `yamllint config/model_catalog.yaml` |
| L2: Domain Logic  | ⚠️ Blocked  | Cannot test - data invalid                        | `cargo test -p localagent-core`      |
| L3: Transport/IPC | ✅ Pass     | Response structure verified correct               | `cargo test -p localagent-tauri`     |
| L4: UI/Frontend   | ⚠️ Blocked  | Cannot test - backend returns error               | `npm test`                           |

**Primary Failure**: L1 (Data/Config)

**Root Cause**: YAML parser fails because models at lines 342, 357, 372, 384, 396, 414, 429 lack required `sizing` field.

### Phase C: Fix & Test

**Invariants Defined** (L1):

1. Every `core_models[i]` must have `sizing` object
2. `sizing` must contain: `disk_gb`, `memory_gb_min`, `memory_gb_recommended`
3. All sizing values must be positive numbers

**Changes Made**:

1. **Data Fix** (`config/model_catalog.yaml`):

   - Added `sizing` blocks to 7 models
   - Values based on model size and quantization

2. **Schema Test** (`tests/test_config_schemas.py`):

   ```python
   def test_model_catalog_has_sizing_for_all_core_models():
       # [Full test code from C.2]
   ```

3. **Rust Integration Test** (`crates/localagent-core/tests/catalog_tests.rs`):
   ```rust
   #[test]
   fn loads_default_model_catalog() {
       // [Full test code from C.2]
   }
   ```

**Verification**:

- ✅ `pytest tests/test_config_schemas.py -v` - PASS
- ✅ `cargo test -p localagent-core` - PASS
- ✅ Manual test: Models page loads successfully

### Phase D: Document

**BLOCKERS.md** updated with:

- Resolution details
- Files changed
- Prevention measures (CI tests added)

**CHANGELOG.md** entry:

```markdown
### Fixed - Model Catalog Schema Validation (B-006)

- Added `sizing` field to 7 models missing required data
- Added schema validation test to prevent recurrence
- Added Rust integration test for catalog loading
```

**CI Updated** (`.github/workflows/tests.yml`):

```yaml
- name: Validate config schemas
  run: pytest tests/test_config_schemas.py -v
```

**Result**: Blocker resolved in ~8 hours total (including investigation, fix, testing, documentation).

---

## 🚀 Quick Reference

### When to Use This SOP

- ✅ User reports crash or broken functionality
- ✅ Feature completely non-functional
- ✅ Error spans multiple layers (data → backend → frontend)
- ✅ Issue assigned B-XXX blocker ID

### When NOT to Use This SOP

- ❌ Minor bugs (use normal PR process)
- ❌ Performance issues (use performance profiling SOP)
- ❌ UI polish / enhancements
- ❌ Documentation updates

### Phase Time Estimates

| Phase         | Target Time | Can Skip If              |
| ------------- | ----------- | ------------------------ |
| A: Reproduce  | 1-2 hours   | Already have clear repro |
| B: Localize   | 2-4 hours   | Root cause obvious       |
| C: Fix & Test | 4-8 hours   | Never skip tests         |
| D: Document   | 1-2 hours   | Never skip for Critical  |

**Total**: 8-16 hours for typical critical blocker

### Common Pitfalls

❌ **Skipping layer analysis** → Fix wrong layer, blocker recurs  
❌ **No invariant tests** → Blocker recurs in different form  
❌ **Vague documentation** → Team can't learn from issue  
❌ **No CI validation** → Same mistake repeated

✅ **Do this instead**: Follow all phases, write tests, document learnings

---

## 📚 Related Documentation

- [SESSION_REVIEW_SOP.md](SESSION_REVIEW_SOP.md) - Session baseline and context
- [TESTING_SOP.md](TESTING_SOP.md) - Test strategy and patterns
- [DOCUMENTATION_SOP.md](DOCUMENTATION_SOP.md) - Documentation standards
- [docs/status/BLOCKERS.md](../status/BLOCKERS.md) - Active blocker tracker
- [docs/ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture reference

---

## 📋 Checklist Summary

**Phase A: Reproduce**

- [ ] Create BLOCKERS.md entry
- [ ] Capture error message + logs + screenshots
- [ ] Write reproduction steps (3-5 steps)
- [ ] Verify reproducibility (clean + dev environment)

**Phase B: Localize**

- [ ] Test L0: Environment
- [ ] Test L1: Data/Config
- [ ] Test L2: Domain Logic
- [ ] Test L3: Transport/IPC
- [ ] Test L4: UI/Frontend
- [ ] Document findings in layer matrix

**Phase C: Fix & Test**

- [ ] Define invariants per failing layer
- [ ] Write failing tests for invariants
- [ ] Implement fixes (narrow scope)
- [ ] Verify tests pass
- [ ] Run full test suite
- [ ] Manual reproduction verification

**Phase D: Document**

- [ ] Update BLOCKERS.md with resolution
- [ ] Update CHANGELOG.md
- [ ] Add/update CI validation
- [ ] Create postmortem (if critical)
- [ ] Link related documentation

---

**Version History**:

- v1.0.0 (2026-01-15): Initial version with B-006 example
