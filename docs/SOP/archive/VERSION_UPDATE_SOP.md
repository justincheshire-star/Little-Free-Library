# Version Update SOP

**Status**: Active  
**Owner**: Development Team  
**Version**: 1.0.0  
**Created**: January 26, 2026  
**Last Updated**: January 26, 2026  
**Trigger**: Before major/minor releases or when transitioning development phases  
**RACI**: R=Tech Lead, A=Release Manager, C=Development Team, I=QA

---

## 🎯 Purpose

Systematic process for updating version numbers across the entire LocalAgent Studio codebase, ensuring no version references are missed in configuration files, documentation, build scripts, or SOPs.

**Failure Modes & Controls**:
- Missed version references → stale version inconsistencies → version audit scripts (Phase 1)
- Incorrect semantic versioning → broken dependencies → version strategy matrix (Phase 2)
- Build failures → missing sidecar updates → pre-build verification checklist (Phase 4)

---

## 📋 Semantic Versioning Strategy

LocalAgent Studio follows [Semantic Versioning 2.0.0](https://semver.org/):

**MAJOR.MINOR.PATCH** (e.g., 0.9.0)

| Component | When to Increment | Example Change |
|-----------|-------------------|----------------|
| **MAJOR** | Breaking API changes, architecture overhaul | 0.x.x → 1.0.0 (production ready), 1.x.x → 2.0.0 (IPC redesign) |
| **MINOR** | New features, non-breaking additions | 0.8.x → 0.9.0 (feature complete), 0.9.x → 0.10.0 (new subsystem) |
| **PATCH** | Bug fixes, minor improvements | 0.9.0 → 0.9.1 (UI fixes), 0.9.1 → 0.9.2 (performance) |

**Version Milestones**:
- **0.1.0 - 0.4.x**: Initial development (Prime branch)
- **0.5.0 - 0.6.x**: Rust transition, IPC implementation
- **0.7.0 - 0.8.x**: Phase 10 workbench features
- **0.9.0**: Feature complete, refinement phase ← CURRENT
- **1.0.0**: Production release candidate

---

## 🔍 Phase 1: Version Audit (Find All References)

### Step 1.1: Run Comprehensive Version Scan

**Script**: `scripts/audit-versions.ps1` (create if not exists)

```powershell
# audit-versions.ps1
# Finds all version references across the codebase

param(
    [string]$OldVersion = "0.6.1",
    [string]$NewVersion = "0.9.0"
)

$ErrorActionPreference = "Stop"

Write-Host "`n🔍 VERSION AUDIT REPORT" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Old Version: $OldVersion" -ForegroundColor Yellow
Write-Host "New Version: $NewVersion" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# Patterns to search for
$patterns = @(
    $OldVersion,                          # Exact version
    "v$OldVersion",                       # With 'v' prefix
    "version.*$OldVersion",               # In version fields
    "$($OldVersion -replace '\.', '\.')" # Escaped for regex
)

# File types to scan
$includes = @("*.md", "*.json", "*.toml", "*.ps1", "*.yml", "*.yaml", "*.rs", "*.ts", "*.tsx")

# Directories to exclude
$excludes = @("node_modules", "target", "dist", "out", ".next", "venv", "venv-win", ".git")

Write-Host "`n📁 Scanning file types: $($includes -join ', ')" -ForegroundColor Gray

$results = @()

foreach ($pattern in $patterns) {
    Get-ChildItem -Path . -Recurse -Include $includes -File | 
        Where-Object { 
            $path = $_.FullName
            -not ($excludes | Where-Object { $path -match $_ })
        } |
        Select-String -Pattern $pattern -AllMatches |
        ForEach-Object {
            $results += [PSCustomObject]@{
                File = $_.Path -replace [regex]::Escape($PWD), "."
                Line = $_.LineNumber
                Match = $_.Line.Trim()
            }
        }
}

# Remove duplicates
$results = $results | Sort-Object File, Line -Unique

# Group by file
$grouped = $results | Group-Object File

Write-Host "`n📊 RESULTS: Found $($results.Count) references in $($grouped.Count) files`n" -ForegroundColor Cyan

foreach ($group in $grouped | Sort-Object Name) {
    Write-Host "📄 $($group.Name)" -ForegroundColor Yellow
    foreach ($match in $group.Group) {
        Write-Host "   Line $($match.Line): $($match.Match)" -ForegroundColor Gray
    }
    Write-Host ""
}

# Category analysis
Write-Host "`n📂 FILES BY CATEGORY:" -ForegroundColor Cyan
@{
    "Configuration"    = $results | Where-Object { $_.File -match "\.json$|\.toml$|\.ya?ml$" }
    "Documentation"    = $results | Where-Object { $_.File -match "\.md$" }
    "Scripts"          = $results | Where-Object { $_.File -match "\.ps1$" }
    "Source Code"      = $results | Where-Object { $_.File -match "\.(rs|ts|tsx)$" }
} | ForEach-Object {
    $_.GetEnumerator() | ForEach-Object {
        $count = ($_.Value | Measure-Object).Count
        if ($count -gt 0) {
            Write-Host "  $($_.Key): $count files" -ForegroundColor Yellow
        }
    }
}

Write-Host "`n✅ Audit complete!`n" -ForegroundColor Green

# Export to file
$reportPath = "logs/version-audit-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
$results | Format-Table -AutoSize | Out-File $reportPath
Write-Host "📝 Full report saved to: $reportPath" -ForegroundColor Gray

return $results
```

**Usage**:
```powershell
.\scripts\audit-versions.ps1 -OldVersion "0.6.1" -NewVersion "0.9.0"
```

### Step 1.2: Review Critical Files Checklist

Manually verify these **MANDATORY** files always contain the current version:

**Core Configuration (CRITICAL - Build Failures)**:
- [ ] `package.json` - Root package version
- [ ] `apps/desktop/src-tauri/Cargo.toml` - Main application version
- [ ] `apps/desktop/src-tauri/tauri.conf.json` - Tauri config AND sidecar path
- [ ] `tests_integration/Cargo.toml` - Integration tests version

**Workspace Crates (CRITICAL - Compilation Errors)**:
- [ ] `apps/desktop/src-tauri/crates/localagent-types/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-config/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-db/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-tools/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-core/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-llm/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-llm-ipc/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-llm-runtime/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-llm-worker/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-design/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-hw/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-vector-sidecar/Cargo.toml`
- [ ] `apps/desktop/src-tauri/crates/localagent-eval/Cargo.toml`

**Build Scripts (CRITICAL - Incorrect Artifacts)**:
- [ ] `scripts/build_sidecar.ps1` - Sidecar version variable

**User-Facing Documentation (HIGH - User Confusion)**:
- [ ] `README.md` - Version number and status
- [ ] `TODO.md` - Current version header
- [ ] `CHANGELOG.md` - New release entry
- [ ] `TECH_STACK.md` - Version and last updated
- [ ] `docs/TROUBLESHOOTING.md` - Version header

**Tracking Documents (MEDIUM - Documentation Drift)**:
- [ ] `docs/status/BLOCKERS.md` - Current version
- [ ] `docs/tracking/NORMALIZATION_IMPLEMENTATION_TRACKER.md` - Version
- [ ] `docs/tracking/LLAMACPP_IMPLEMENTATION_TRACKER.md` - Version (if exists)
- [ ] `docs/tracking/DEPENDENCIES_TRACKER.md` - Version (if exists)

**SOPs (LOW - Operational Guidance)**:
- [ ] `docs/sop/BUILDOUT_SOP.md` - Example version references
- [ ] `docs/sop/BLOCKER_RESOLUTION_SOP.md` - Example version references

**Test Fixtures (LOW - Test Accuracy)**:
- [ ] `tests_integration/tests/sidecar_lifecycle.rs` - Version literals
- [ ] `tests_integration/tests/sidecar_vectors.rs` - Version literals

---

## 🔄 Phase 2: Execute Version Update

### Step 2.1: Update Core Configuration Files

**Manual Updates** (use multi_replace_string_in_file for efficiency):

```powershell
# PowerShell alternative for batch updates
$files = @(
    "package.json",
    "apps/desktop/src-tauri/Cargo.toml",
    "apps/desktop/src-tauri/tauri.conf.json",
    "tests_integration/Cargo.toml"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        (Get-Content $file -Raw) -replace '0\.6\.1', '0.9.0' | Set-Content $file
        Write-Host "✅ Updated: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Not found: $file" -ForegroundColor Red
    }
}
```

### Step 2.2: Update Workspace Crates (Batch)

```powershell
# Update all workspace crate versions
Get-ChildItem -Path "apps/desktop/src-tauri/crates/*/Cargo.toml" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $updated = $content -replace 'version = "0\.6\.1"', 'version = "0.9.0"'
    Set-Content -Path $_.FullName -Value $updated
    Write-Host "✅ Updated: $($_.FullName)" -ForegroundColor Green
}
```

### Step 2.3: Update Documentation

**Key Files to Edit**:

1. **README.md**:
   - Version number in header
   - Status (e.g., "In Development" → "Feature Complete")
   - Latest build line

2. **TODO.md**:
   - Current Version header
   - Latest Build line

3. **CHANGELOG.md**:
   - Add new `[X.Y.Z] - YYYY-MM-DD` section
   - Include release theme and key changes
   - Document breaking changes if MAJOR bump

4. **TECH_STACK.md**:
   - Version header
   - Last Updated date

5. **TROUBLESHOOTING.md**:
   - Version header
   - Last Updated date

### Step 2.4: Update Build Scripts

```powershell
# scripts/build_sidecar.ps1
# Update the $Version variable
$Version = "0.9.0"
```

### Step 2.5: Update Sidecar Path in tauri.conf.json

**CRITICAL**: Update BOTH version references:

```json
{
  "version": "0.9.0",
  // ...
  "bundle": {
    "resources": {
      "sidecar/current.txt": "sidecar/current.txt",
      "sidecar/0.9.0/vector_sidecar.exe": "sidecar/0.9.0/vector_sidecar.exe"
    }
  }
}
```

---

## 🧪 Phase 3: Update Test Fixtures

### Step 3.1: Update Integration Test Version Literals

**File**: `tests_integration/tests/sidecar_lifecycle.rs`

```rust
// Find and update hardcoded versions
let version = "0.9.0";  // Line ~52

// Update version arrays
let versions = vec!["0.8.0", "0.9.0", "0.10.0"];  // Line ~286

// Update current version references
std::fs::write(install_dir.join("current.txt"), "0.9.0").unwrap();  // Line ~297
```

**File**: `tests_integration/tests/sidecar_vectors.rs`

```rust
let version = "0.9.0";  // Line ~48
```

---

## 🏗️ Phase 4: Rebuild Sidecar and Verify

### Step 4.1: Update Sidecar Directory Structure

```powershell
# Rename old version directory (if exists)
$oldDir = "apps/desktop/src-tauri/sidecar/0.6.1"
$newDir = "apps/desktop/src-tauri/sidecar/0.9.0"

if (Test-Path $oldDir) {
    Rename-Item $oldDir $newDir
    Write-Host "✅ Renamed: $oldDir → $newDir" -ForegroundColor Green
}

# Update current.txt
"0.9.0" | Set-Content "apps/desktop/src-tauri/sidecar/current.txt"
Write-Host "✅ Updated: sidecar/current.txt" -ForegroundColor Green
```

### Step 4.2: Rebuild Sidecar Binary

```powershell
.\scripts\build_sidecar.ps1
```

**Verification**:
```powershell
# Verify sidecar structure
Test-Path "apps/desktop/src-tauri/sidecar/0.9.0/vector_sidecar.exe"
Get-Content "apps/desktop/src-tauri/sidecar/current.txt"  # Should show "0.9.0"
(Get-Item "apps/desktop/src-tauri/sidecar/0.9.0/vector_sidecar.exe").Length / 1MB
```

**Expected Output**:
```
True
0.9.0
2.29  # Size in MB
```

### Step 4.3: Regenerate Package Locks

```powershell
# Root package-lock.json
npm install

# Web app package-lock.json
cd apps/web
npm install
cd ../..
```

---

## ✅ Phase 5: Validation and Testing

### Step 5.1: Compilation Check

```powershell
# Verify Rust workspace compiles
cd apps/desktop/src-tauri
cargo check --workspace
cargo test --workspace --no-run

# Verify frontend builds
cd ../../web
npm run build
cd ../..
```

### Step 5.2: Run Version Verification Script

**Script**: `scripts/verify-versions.ps1`

```powershell
# verify-versions.ps1
# Verifies all version references match the target version

param(
    [Parameter(Mandatory=$true)]
    [string]$ExpectedVersion
)

$ErrorActionPreference = "Stop"

Write-Host "`n🔎 VERSION VERIFICATION" -ForegroundColor Cyan
Write-Host "Expected Version: $ExpectedVersion`n" -ForegroundColor Yellow

$checks = @(
    @{ File = "package.json"; Pattern = "`"version`":\s*`"$ExpectedVersion`"" },
    @{ File = "apps/desktop/src-tauri/Cargo.toml"; Pattern = "version\s*=\s*`"$ExpectedVersion`"" },
    @{ File = "apps/desktop/src-tauri/tauri.conf.json"; Pattern = "`"version`":\s*`"$ExpectedVersion`"" },
    @{ File = "apps/desktop/src-tauri/sidecar/current.txt"; Pattern = "^$ExpectedVersion$" },
    @{ File = "scripts/build_sidecar.ps1"; Pattern = "\`$Version\s*=\s*`"$ExpectedVersion`"" }
)

$passed = 0
$failed = 0

foreach ($check in $checks) {
    if (Test-Path $check.File) {
        $content = Get-Content $check.File -Raw
        if ($content -match $check.Pattern) {
            Write-Host "✅ $($check.File)" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "❌ $($check.File) - Version mismatch!" -ForegroundColor Red
            $failed++
        }
    } else {
        Write-Host "⚠️  $($check.File) - File not found!" -ForegroundColor Yellow
        $failed++
    }
}

# Check workspace crates
$crateFiles = Get-ChildItem -Path "apps/desktop/src-tauri/crates/*/Cargo.toml"
$cratePassed = 0
$crateFailed = 0

foreach ($crate in $crateFiles) {
    $content = Get-Content $crate.FullName -Raw
    if ($content -match "version\s*=\s*`"$ExpectedVersion`"") {
        $cratePassed++
    } else {
        Write-Host "❌ $($crate.FullName) - Version mismatch!" -ForegroundColor Red
        $crateFailed++
    }
}

if ($crateFailed -eq 0) {
    Write-Host "✅ All $cratePassed workspace crates" -ForegroundColor Green
    $passed += $cratePassed
} else {
    Write-Host "❌ $crateFailed/$($crateFiles.Count) workspace crates failed" -ForegroundColor Red
    $failed += $crateFailed
}

Write-Host "`n📊 RESULTS: $passed passed, $failed failed`n" -ForegroundColor Cyan

if ($failed -eq 0) {
    Write-Host "🎉 All version checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Some version checks failed. Review and fix before building." -ForegroundColor Red
    exit 1
}
```

**Usage**:
```powershell
.\scripts\verify-versions.ps1 -ExpectedVersion "0.9.0"
```

### Step 5.3: Pre-Build Checklist

Before running `npm run tauri build`:

- [ ] All version checks passed (verify-versions.ps1)
- [ ] Sidecar binary exists at `sidecar/0.9.0/vector_sidecar.exe`
- [ ] `sidecar/current.txt` contains correct version
- [ ] `cargo check --workspace` passes
- [ ] `npm run build` succeeds in `apps/web`
- [ ] CHANGELOG.md has new release entry
- [ ] README.md version updated

---

## 📦 Phase 6: Build and Release

### Step 6.1: Build MSI Installer

```powershell
cd apps/desktop
npm run tauri build
```

### Step 6.2: Verify Build Artifacts

**Expected Files**:
```
apps/desktop/src-tauri/target/release/bundle/msi/LocalAgent Studio_0.9.0_x64_en-US.msi
apps/desktop/src-tauri/target/release/bundle/nsis/LocalAgent Studio_0.9.0_x64-setup.exe
```

**Verification**:
```powershell
$msiPath = "target/release/bundle/msi/LocalAgent Studio_0.9.0_x64_en-US.msi"
if (Test-Path $msiPath) {
    $msi = Get-Item $msiPath
    Write-Host "✅ MSI built: $($msi.Length / 1MB) MB" -ForegroundColor Green
    
    # Extract MSI metadata
    $shell = New-Object -ComObject WindowsInstaller.Installer
    $database = $shell.GetType().InvokeMember("OpenDatabase", "InvokeMethod", $null, $shell, @($msi.FullName, 0))
    $view = $database.GetType().InvokeMember("OpenView", "InvokeMethod", $null, $database, "SELECT Value FROM Property WHERE Property='ProductVersion'")
    $view.GetType().InvokeMember("Execute", "InvokeMethod", $null, $view, $null)
    $record = $view.GetType().InvokeMember("Fetch", "InvokeMethod", $null, $view, $null)
    $version = $record.GetType().InvokeMember("StringData", "GetProperty", $null, $record, 1)
    
    Write-Host "MSI Product Version: $version" -ForegroundColor Cyan
    
    if ($version -eq "0.9.0") {
        Write-Host "✅ Version metadata correct" -ForegroundColor Green
    } else {
        Write-Host "❌ Version metadata mismatch!" -ForegroundColor Red
    }
}
```

---

## 📝 Phase 7: Documentation and Commit

### Step 7.1: Update CHANGELOG.md Template

```markdown
## [X.Y.Z] - YYYY-MM-DD

**Release Theme**: [Theme Name]

[Brief description of what this release represents]

### Added

- [New features]

### Changed

- **Version Bump**: X.Y.Z → X.Y.Z across all workspace crates
- **Status**: [Old Status] → [New Status]
- [Other changes]

### Fixed

- [Bug fixes]

### Breaking Changes

- [If MAJOR version bump, list breaking changes]
```

### Step 7.2: Commit Changes

```bash
git add .
git commit -m "chore: version bump to X.Y.Z

- Updated all workspace crates to version X.Y.Z
- Updated configuration files (package.json, Cargo.toml, tauri.conf.json)
- Updated sidecar path and build scripts
- Updated documentation (README, TODO, CHANGELOG, TECH_STACK)
- Regenerated package-lock.json
- Updated integration test fixtures

Release theme: [Theme]

Files changed: [count] files
- Configuration: [count] files
- Documentation: [count] files  
- Workspace crates: [count] files
- Scripts: [count] files

Verification:
- ✅ Cargo check passes
- ✅ Frontend builds successfully
- ✅ Sidecar binary built for v X.Y.Z
- ✅ All version checks passed

Ready for build and release."
```

---

## 📋 Complete File Reference

### Configuration Files (13)

| File | Version Location | Update Method |
|------|------------------|---------------|
| `package.json` | `"version": "X.Y.Z"` | Manual or regex replace |
| `package-lock.json` | Auto-generated | Run `npm install` |
| `apps/desktop/src-tauri/Cargo.toml` | `version = "X.Y.Z"` | Manual or regex replace |
| `apps/desktop/src-tauri/tauri.conf.json` | `"version": "X.Y.Z"` + sidecar path | Manual (2 locations) |
| `apps/desktop/src-tauri/sidecar/current.txt` | `X.Y.Z` (entire file) | Overwrite file |
| `tests_integration/Cargo.toml` | `version = "X.Y.Z"` | Manual or regex replace |
| All 13 workspace crate `Cargo.toml` files | `version = "X.Y.Z"` | Batch PowerShell script |

### Documentation Files (6)

| File | Version Location(s) | Notes |
|------|---------------------|-------|
| `README.md` | Header + status line | Update status too |
| `TODO.md` | Current Version line | May have multiple refs |
| `CHANGELOG.md` | New release section | Add new entry at top |
| `TECH_STACK.md` | Version header | Update date too |
| `docs/TROUBLESHOOTING.md` | Version header | Update date too |
| `docs/status/BLOCKERS.md` | Current Version line | Update date too |

### Tracking Documents (3)

| File | Version Location | Notes |
|------|------------------|-------|
| `docs/tracking/NORMALIZATION_IMPLEMENTATION_TRACKER.md` | Version header | Optional |
| `docs/tracking/LLAMACPP_IMPLEMENTATION_TRACKER.md` | Version header | If exists |
| `docs/tracking/DEPENDENCIES_TRACKER.md` | Version header | If exists |

### Build Scripts (1)

| File | Version Location | Notes |
|------|------------------|-------|
| `scripts/build_sidecar.ps1` | `$Version = "X.Y.Z"` | Line ~8 |

### Test Fixtures (2)

| File | Version References | Count |
|------|-------------------|-------|
| `tests_integration/tests/sidecar_lifecycle.rs` | Hardcoded strings | ~4 locations |
| `tests_integration/tests/sidecar_vectors.rs` | Hardcoded string | ~1 location |

### Historical Documents (Preserve As-Is)

**DO NOT UPDATE** version references in:
- `docs/session-reviews/**/*.md` - Historical session records
- `docs/postmortems/**/*.md` - Historical incident reports
- `logs/**/*.md` - Historical logs and resolutions
- `docs/status/IMPLEMENTATION_SUMMARY_*.md` - Historical implementation summaries

These documents are **historical artifacts** and should preserve the version numbers they reference for accuracy.

---

## 🔄 Version History

| Old Version | New Version | Date | Reason | Lead |
|-------------|-------------|------|--------|------|
| 0.6.1 | 0.9.0 | 2026-01-26 | Feature complete, transition to refinement | AI Agent |

---

## 🚨 Common Mistakes to Avoid

1. **❌ Forgetting sidecar path update**: `tauri.conf.json` has TWO version references (version field + sidecar path)
2. **❌ Not rebuilding sidecar**: Must run `build_sidecar.ps1` after version change
3. **❌ Skipping package-lock.json**: Always run `npm install` to regenerate
4. **❌ Missing workspace crates**: Use batch script, don't update manually (error-prone)
5. **❌ Updating historical documents**: Preserve version references in session reviews and postmortems
6. **❌ Not updating current.txt**: Sidecar loader reads this file to determine version
7. **❌ Inconsistent versioning**: All crates must have matching versions

---

## 📊 Success Criteria

Version update is complete when:

- ✅ All 13 workspace crates show same version in `Cargo.toml`
- ✅ `tauri.conf.json` version field matches
- ✅ `tauri.conf.json` sidecar path matches
- ✅ `sidecar/current.txt` matches
- ✅ `package.json` and `package-lock.json` match
- ✅ `scripts/build_sidecar.ps1` $Version variable matches
- ✅ CHANGELOG.md has new release entry
- ✅ README.md version updated
- ✅ `cargo check --workspace` passes
- ✅ `verify-versions.ps1` exits with code 0
- ✅ Sidecar binary exists at `sidecar/X.Y.Z/vector_sidecar.exe`
- ✅ MSI builds with correct product version metadata

---

## 🔗 Related Documents

- [BUILDOUT_SOP.md](BUILDOUT_SOP.md) - Build process after version update
- [DOCUMENTATION_SOP.md](DOCUMENTATION_SOP.md) - Documentation requirements
- [Semantic Versioning 2.0.0](https://semver.org/) - Official SemVer spec

---

## 📝 Notes

- **Automation Opportunity**: Consider creating a single PowerShell script that executes all phases
- **CI/CD Integration**: Version verification could run in pre-build CI checks
- **Version Rollback**: Keep old sidecar directories for rollback capability
- **Breaking Changes**: For MAJOR version bumps, update API documentation and migration guides

**Last SOP Execution**: January 26, 2026 (0.6.1 → 0.9.0)
