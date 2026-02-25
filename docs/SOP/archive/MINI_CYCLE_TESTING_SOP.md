# Mini-Cycle Testing SOP

**Status**: Active  
**Owner**: Development Team  
**Version**: 1.0.0  
**Last Updated**: December 15, 2025  
**Trigger**: Small feature slices or bug fixes  
**RACI**: R=Implementer, A=Tech Lead, C=QA, I=Team  
**SLA**: One mini-cycle ≤2 hours for typical slice

---

## 🎯 Purpose

Run tight TDD-style loops to validate a slice end-to-end before widening scope. Prevents scope creep and ensures rapid feedback.

**Failure Modes & Controls**:

- Scope creep → enforce slice size limits
- Failing guard → fix before expanding

---

## 🔄 Mini-Cycle Workflow

```
┌─────────────┐
│ Select Slice │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Write Tests │ ← Unit + Integration
│    First    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Implement  │ ← Minimal code
│   Minimal   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Run Battery │ ← Unit → Integration → E2E
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Add Guards  │ ← Lint, type check
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Commit & PR │
└─────────────┘
```

---

## 📋 Procedure

### 1. Select Slice

Choose a narrow vertical:

- One API endpoint, or
- One agent behavior, or
- One RAG function

**Good Slices**:

- "Add `limit` parameter to `/v1/sprints`"
- "Router correctly routes to coder role"
- "Retriever handles empty results"

**Bad Slices**:

- "Implement pagination" (too broad)
- "Improve agent" (too vague)

### 2. Write Tests First

```python
# tests/test_router.py

def test_routes_coding_task_to_coder():
    """Given a coding task, router should assign coder role."""
    router = Router()
    task = {"goal": "Write a function to parse JSON"}

    result = router.route(task)

    assert result.role == "coder"
```

### 3. Implement Minimal

Code **only** what the test demands:

```python
# services/agent/router.py

class Router:
    def route(self, task: dict) -> RouteResult:
        # Minimal implementation
        if "write" in task["goal"].lower():
            return RouteResult(role="coder")
        return RouteResult(role="general")
```

### 4. Run Local Battery

```bash
# Run in order - stop if any fails
pytest tests/test_router.py -v          # Unit
pytest tests/test_api.py -v             # Integration
make lint                                # Guards
```

### 5. Add Guards

Ensure quality gates pass:

```bash
# Type checking
mypy services/agent/router.py

# Lint
ruff check services/agent/router.py
```

### 6. Commit & PR

```bash
git add .
git commit -m "feat(agent): route coding tasks to coder role

- Added routing logic based on task goal keywords
- Tests: test_routes_coding_task_to_coder

Closes #123"
```

---

## ⏱️ Time Boxing

| Phase        | Time Budget |
| ------------ | ----------- |
| Select slice | 5 min       |
| Write tests  | 20 min      |
| Implement    | 30 min      |
| Run battery  | 10 min      |
| Add guards   | 10 min      |
| Commit/PR    | 5 min       |
| **Total**    | **~80 min** |

If exceeding 2 hours:

1. Slice is too big → break it down
2. Scope crept → revert to original scope
3. Blocker hit → document and escalate

---

## 🔁 Iteration Rules

1. **Green before expanding**: Never add features until current tests pass
2. **One thing at a time**: Complete current slice before starting next
3. **Commit often**: Small, atomic commits
4. **Feature flags for risk**: Use flags if change is potentially breaking

---

## 📊 Mini-Cycle Metrics

Track per cycle:

| Metric              | Target                  |
| ------------------- | ----------------------- |
| Cycle time          | <2 hours                |
| Tests written       | ≥2 (unit + integration) |
| Rework after review | 0-1 iterations          |

---

## ✅ Mini-Cycle Checklist

- [ ] Slice is narrow and specific
- [ ] Tests written before implementation
- [ ] Minimal code satisfies tests
- [ ] All tests pass locally
- [ ] Lint/type checks pass
- [ ] Commit with conventional format
- [ ] PR created with context
