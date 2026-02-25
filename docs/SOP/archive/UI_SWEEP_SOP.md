# UI Sweep SOP

**Status**: Active  
**Owner**: UI/UX Lead  
**Version**: 1.0.0  
**Last Updated**: January 13, 2026  
**Trigger**: Scheduled quarterly, before major releases, or when UI debt exceeds threshold  
**RACI**: R=UI/UX Lead, A=Tech Lead, C=Developers, I=PM  
**SLA**: Sweep completed within 2 business days; all critical issues logged within 24h  
**Post-Requisite**: [DOCUMENTATION_SOP.md](DOCUMENTATION_SOP.md) MUST be run after this SOP

---

## 🎯 Purpose

Perform systematic audits of the UI/UX system to ensure compliance with design tokens, accessibility standards, interaction contracts, and performance budgets. This SOP catches drift, documents gaps, and generates actionable remediation tasks.

**Failure Modes & Controls**:

| Failure Mode | Impact | Control |
|--------------|--------|---------|
| Token drift | Visual inconsistency, theme breaks | Automated lint + manual sweep |
| A11y regressions | Blocked users, legal risk | axe-core CI + manual audit |
| Hydration mismatches | Flash of wrong content, SSR errors | Build checks + pattern review |
| Interaction gaps | Keyboard-only users blocked | Multi-input parity matrix |
| Performance regression | Slow UI, user churn | Bundle budget CI + Lighthouse |
| Stale documentation | Wrong implementation guidance | Doc sync check at sweep end |

---

## 🔗 Document System Overview

This SOP operates on the UI/UX documentation system:

```
docs/ui/
├── UI_UX_REFERENCE.md         # ← Master reference (source of truth)
├── UX_GOVERNANCE.md           # ← Change policies, PR workflows
├── INTERACTION_CONTRACTS.md   # ← Component interaction specs
├── PERSISTENCE_HYDRATION.md   # ← SSR/hydration patterns
├── UI_AUDIT_MATRIX.md         # ← Audit tracking (UPDATE THIS)
├── COMPONENTS.md              # ← Component API reference
├── IA.md                      # ← Information architecture
├── STATE_MATRIX.md            # ← Per-page state handling
└── WIREFLOW.mmd               # ← Navigation flows

docs/tracking/
├── DEPRECATION_LOG.md         # ← UI deprecations go here
└── UI_TRACKER.md              # ← Sprint-level UI task tracking (CREATE IF MISSING)

.github/
└── pull_request_template.md   # ← PR checklist with UX gates
```

---

## 🤖 AI Agent Instructions

**CRITICAL**: This SOP is a multi-step audit process. Complete ALL phases in order.

### Pre-Sweep Checklist

Before starting, verify:

- [ ] Access to `docs/ui/UI_AUDIT_MATRIX.md` (if missing, create from template)
- [ ] Ability to run `npm run build` in `apps/web/`
- [ ] Access to run axe-core or equivalent a11y scanner
- [ ] Current branch is up to date with `Prime` or `Rust`

---

## 📋 Phase 1: Token Drift Audit

**Goal**: Ensure no raw color/size values exist in app code.

### Automated Check

```bash
# Find raw hex colors in app code (should return empty)
grep -rn --include="*.tsx" --include="*.ts" "#[0-9A-Fa-f]\{3,8\}" apps/web/app/ apps/web/components/

# Find arbitrary Tailwind values (should return empty)
grep -rn --include="*.tsx" "bg-\[" apps/web/app/ apps/web/components/
grep -rn --include="*.tsx" "text-\[" apps/web/app/ apps/web/components/
```

### Manual Verification

1. Open `apps/web/tokens/design-tokens.json`
2. Open `apps/web/app/globals.css`
3. Verify all tokens in JSON have corresponding CSS variables
4. Verify all themes (Vaporwave, Cyberpunk, Middle Earth) define the same variables

### Record Results

Update `docs/ui/UI_AUDIT_MATRIX.md` → Token column for each component.

| Finding | Action |
|---------|--------|
| Raw hex found | Create issue, add to Priority 2 list |
| Missing token | Add to `design-tokens.json` per governance rules |
| Theme mismatch | Fix in `globals.css`, log in CHANGELOG |

---

## 📋 Phase 2: Accessibility Audit

**Goal**: Zero critical/serious axe-core violations on gated routes.

### Gated Routes (Must Pass)

- `/workbench`
- `/projects`
- `/settings`
- `/pinboards`
- `/agents`
- `/sessions`

### Automated Check

```bash
# Run axe audit (requires axe-core setup)
npm run axe-audit

# Or manual with browser extension:
# 1. Navigate to each gated route
# 2. Run axe DevTools
# 3. Screenshot results
```

### Manual Verification

For each route, verify:

- [ ] **Skip link**: Press Tab, first focus is "Skip to main content"
- [ ] **Landmarks**: `<nav>`, `<main>`, `<aside>` present with labels
- [ ] **Focus visible**: Tab through all interactive elements
- [ ] **Keyboard operable**: All actions work without mouse
- [ ] **Color contrast**: Use contrast checker on text elements

### Record Results

Update `docs/ui/UI_AUDIT_MATRIX.md`:
- Route Audit Matrix → A11y column
- Component Audit Matrix → A11y column

| Finding | Priority | Action |
|---------|----------|--------|
| Critical violation | P1 | Block next release, fix immediately |
| Serious violation | P1 | Create issue, target current sprint |
| Moderate violation | P2 | Create issue, target next sprint |
| Minor violation | P3 | Log for backlog |

---

## 📋 Phase 3: Hydration Safety Audit

**Goal**: All persisted state uses `useHydrated()` pattern.

### Identify Persisted Stores

```bash
# Find all Zustand stores with persist middleware
grep -rn "persist(" apps/web/stores/ apps/web/hooks/
```

### Verify Pattern Usage

For each persisted store, verify consumers use `useHydrated()`:

```tsx
// ✅ CORRECT
function Component() {
  const hydrated = useHydrated();
  const value = usePersistedStore((s) => s.value);
  
  if (!hydrated) return <Skeleton />;
  return <Content value={value} />;
}

// ❌ INCORRECT (causes hydration mismatch)
function Component() {
  const value = usePersistedStore((s) => s.value);
  return <Content value={value} />;
}
```

### Check for Direct localStorage

```bash
# Should return empty (no direct localStorage in components)
grep -rn "localStorage\." apps/web/components/
grep -rn "sessionStorage\." apps/web/components/
```

### Record Results

Update `docs/ui/UI_AUDIT_MATRIX.md` → Route Audit Matrix → Hydration column.

| Finding | Action |
|---------|--------|
| Missing `useHydrated()` | Create issue, add pattern |
| Direct localStorage | Refactor to Zustand persist |
| Missing schema version | Add `version` to persist config |

---

## 📋 Phase 4: Multi-Input Parity Audit

**Goal**: Every action works via mouse, keyboard, touch, and assistive tech.

### Core Interactions to Test

| Feature | Mouse | Keyboard | Touch | Screen Reader |
|---------|-------|----------|-------|---------------|
| Navigation | Click | Tab+Enter | Tap | ✓ landmarks |
| Sidebar collapse | Click | ⌘/ | Tap | ✓ announces |
| Modal open/close | Click | Escape | Tap outside | ✓ focus trap |
| Form submission | Click | Enter | Tap | ✓ errors read |
| Tab switching | Click | ←→ | Tap | ✓ selected |
| Menu navigation | Click | ↑↓+Enter | Tap | ✓ menu role |
| Delete confirmation | Click | Enter | Tap | ✓ announced |

### Manual Testing

1. **Keyboard-only session**: Unplug mouse, navigate entire app
2. **Screen reader session**: Enable VoiceOver/NVDA, complete key workflows
3. **Touch session**: Use touch device or browser emulation

### Record Results

Update `docs/ui/UI_AUDIT_MATRIX.md` → Interaction Method Audit section.

---

## 📋 Phase 5: Performance Budget Audit

**Goal**: All metrics within budget thresholds.

### Bundle Size Check

```bash
cd apps/web
npm run build

# Check output for chunk sizes
# Initial JS bundle must be ≤500KB gzip
```

### Lighthouse Audit

Run Lighthouse on key routes:

| Route | FCP Target | LCP Target | TTI Target |
|-------|------------|------------|------------|
| `/` | ≤1.5s | ≤2.5s | ≤3.0s |
| `/projects` | ≤1.5s | ≤2.5s | ≤3.0s |
| `/workbench` | ≤1.5s | ≤2.5s | ≤3.0s |

### Virtualization Check

Verify long lists use virtualization:

```bash
# Find lists that might need virtualization
grep -rn "\.map(" apps/web/app/ apps/web/components/ | head -50
```

Review each `.map()` call:
- If rendering >20 items → Should use `@tanstack/react-virtual`
- If tree structure >50 nodes → Should use `react-arborist`

### Record Results

Update `docs/ui/UI_AUDIT_MATRIX.md` → Performance Audit section.

---

## 📋 Phase 6: Component Contract Audit

**Goal**: All reusable components have documented interaction contracts.

### Inventory Check

```bash
# List all component files
find apps/web/components -name "*.tsx" | wc -l

# Check for contract documentation
grep -rn "@interaction-contract" apps/web/components/
```

### Contract Completeness

For each component in `apps/web/components/ui/`, verify:

- [ ] Has `@interaction-contract` JSDoc block
- [ ] Documents Focus, Keyboard, Mouse, Touch, ARIA
- [ ] Documents Motion + reduced-motion fallback
- [ ] Documents error/loading states if applicable

### Record Results

Update `docs/ui/UI_AUDIT_MATRIX.md` → Component Audit Matrix → Contract column.

Missing contracts → Create tasks in Priority 3 (Medium) section.

---

## 📋 Phase 7: Documentation Sync

**Goal**: Ensure all UI docs reflect current implementation.

### Cross-Reference Check

| Doc | Verify Against | Action if Stale |
|-----|----------------|-----------------|
| `UI_UX_REFERENCE.md` | Current tech stack, components | Update section |
| `COMPONENTS.md` | Actual component files | Add/remove entries |
| `IA.md` | Current routes in `apps/web/app/` | Update route map |
| `STATE_MATRIX.md` | Page implementations | Update state handling |
| `INTERACTION_CONTRACTS.md` | Component JSDoc | Sync contracts |
| `PERSISTENCE_HYDRATION.md` | Zustand stores | Update examples |

### Version Check

Verify `UI_UX_REFERENCE.md` version reflects recent changes:

```markdown
## Version History

| Version | Date | Changes |
|---------|------|---------|
| X.X.X | [today] | [what changed in this sweep] |
```

---

## 📋 Phase 8: Issue Generation

**Goal**: All findings become actionable issues.

### Issue Template

```markdown
## UI Sweep Finding: [Brief Description]

**Source**: UI Sweep SOP - Phase [X]
**Date**: [YYYY-MM-DD]
**Severity**: P1/P2/P3/P4

### Description
[What was found]

### Location
- File: `path/to/file.tsx`
- Line: [if applicable]

### Expected
[What should be]

### Actual
[What is]

### Remediation
[How to fix]

### Governance Reference
See: docs/ui/UI_UX_REFERENCE.md#[section]
```

### Priority Assignment

| Priority | Criteria | SLA |
|----------|----------|-----|
| P1 | A11y critical, hydration breaks, blocker | This sprint |
| P2 | A11y serious, token drift, contract missing | Next sprint |
| P3 | A11y moderate, performance warn, doc stale | 30 days |
| P4 | Minor polish, enhancement | Backlog |

---

## 📋 Phase 9: Tracker Updates

**Goal**: All findings recorded in tracking documents.

### Required Updates

1. **`docs/ui/UI_AUDIT_MATRIX.md`**
   - Update all audit columns with ✅/🔶/⬜/❌
   - Add new action items to Priority sections
   - Update Audit History table

2. **`docs/tracking/DEPRECATION_LOG.md`** (if applicable)
   - Add any deprecated UI patterns
   - Include migration path

3. **`docs/tracking/UI_TRACKER.md`** (create if missing)
   - Log sweep date and scope
   - List all issues created
   - Track remediation status

### UI_TRACKER.md Template (if creating)

```markdown
# UI Tracker

**Created**: [Date]
**Status**: Active
**Purpose**: Track UI sweep findings and remediation progress.

---

## Sweep History

| Date | Scope | Issues Found | Issues Resolved | Next Sweep |
|------|-------|--------------|-----------------|------------|
| YYYY-MM-DD | Quarterly | X | 0 | YYYY-MM-DD |

---

## Active Issues

| ID | Description | Priority | Owner | Status | Due |
|----|-------------|----------|-------|--------|-----|
| | | | | | |

---

## Resolved Issues

| ID | Description | Resolution | Resolved Date |
|----|-------------|------------|---------------|
| | | | |
```

---

## 📋 Phase 10: Run Documentation SOP

**MANDATORY**: After completing the UI Sweep, run the Documentation SOP.

```
⚠️  POST-REQUISITE: DOCUMENTATION_SOP.md

The UI Sweep modifies multiple documents:
- UI_AUDIT_MATRIX.md
- UI_UX_REFERENCE.md (version bump)
- UI_TRACKER.md
- DEPRECATION_LOG.md (possibly)

The Documentation SOP ensures:
- CHANGELOG.md updated with sweep findings
- Session summary includes sweep results
- Index files updated if new docs created
- Cross-references validated
```

### Documentation SOP Trigger

When invoking Documentation SOP, specify:

- **Development Action**: "UI sweep completed"
- **Primary Docs**: `CHANGELOG.md`, `docs/ui/UI_AUDIT_MATRIX.md`
- **Secondary Docs**: `docs/ui/UI_UX_REFERENCE.md`, `docs/tracking/UI_TRACKER.md`

---

## ✅ Sweep Completion Checklist

Before marking sweep complete:

- [ ] Phase 1: Token drift audit complete
- [ ] Phase 2: Accessibility audit complete (0 critical/serious on gated routes)
- [ ] Phase 3: Hydration safety audit complete
- [ ] Phase 4: Multi-input parity audit complete
- [ ] Phase 5: Performance budget audit complete
- [ ] Phase 6: Component contract audit complete
- [ ] Phase 7: Documentation sync complete
- [ ] Phase 8: All findings logged as issues
- [ ] Phase 9: Tracker documents updated
- [ ] Phase 10: Documentation SOP triggered and complete

---

## 📅 Sweep Schedule

| Sweep Type | Frequency | Scope |
|------------|-----------|-------|
| **Full Sweep** | Quarterly | All phases |
| **Pre-Release Sweep** | Before major release | Phases 1-5 (critical) |
| **Focused Sweep** | After major UI change | Affected phases only |
| **A11y Micro-Sweep** | Monthly | Phase 2 only |

---

## 🔄 Continuous Enforcement

Between sweeps, these automated checks run:

| Check | When | Action on Fail |
|-------|------|----------------|
| axe-core | Every PR | Block merge |
| Bundle size | Every build | Warn at 450KB, block at 500KB |
| Token lint | Every PR | Block merge |
| TypeScript | Every PR | Block merge |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-13 | Initial UI Sweep SOP |
