---
type: kb-note
tags: [treasure, governance, pxctx]
created: 2026-02-25
updated: 2026-02-25
never_expire: true
tier: treasure
---

# Treasure Governance

Treasure documents are the highest-priority context tier. They are:

- **Always packed first** into every Professor X context window.
- **Never expired** (no TTL).
- **Never modified** without explicit user `CONFIRM`.

## What Belongs Here

- Hard rules and non-negotiable constraints.
- Locked architectural decisions (e.g., "This repo uses CC-BY-SA 4.0 only").
- Security/compliance policies.
- Canonical schema definitions.

## Modifying Treasure

To update a Treasure doc:

1. Professor X proposes the replacement text + rationale.
2. User explicitly says **CONFIRM**.
3. `pxctx promote <new_doc_id>` or `pxctx supersede <old_id> <new_id>` is run.

## Current Treasure Docs

| File | Topic |
|------|-------|
| (none yet — promote a doc with `pxctx promote`) | — |

---

*Add Treasure docs to this directory only via `pxctx promote` after user CONFIRM.*
