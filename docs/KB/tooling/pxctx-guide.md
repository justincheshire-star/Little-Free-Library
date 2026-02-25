---
type: kb-note
tags: [pxctx, tooling, context-system, RAG]
sources: [.github/agents/Professor_X.agent.md]
created: 2026-02-25
updated: 2026-02-25
never_expire: true
tier: long-lived
---

# pxctx Tooling Guide

## What Is pxctx

`pxctx` is the context management CLI for Professor X. It implements a 3-tier RAG system:

| Tier | Scope | TTL | Priority |
|------|-------|-----|----------|
| `treasure` | repo | never | 1st (always) |
| `working` | session/task | configurable | 2nd |
| `long-lived` | repo | configurable | 3rd |

## Storage

All state lives in `.pxctx/` at the repo root (gitignored). Uses SQLite + FTS5.

## Common Commands

```bash
# Bootstrap session
source scripts/pxctx-auto.sh
pxctx-boot "Task description"

# Add a context item
pxctx add --tier working --type finding --tags corpus,schema \
  --text "Chunk IDs must match sources.json entries"

# Query context
pxctx query "corpus validation rules" --budget 4000

# Record during work (shorthand via pxctx-auto.sh)
pxctx-record decision "Used SQLite FTS5 for hybrid retrieval — no external deps"
pxctx-record finding "validate_corpus.py checks source id consistency"

# Checkpoint milestone
pxctx-checkpoint "Phase 1 complete: ingest pipeline verified"

# Compact many working items into a long-lived note
pxctx compact --session <session_id>

# Promote a doc to Treasure (requires user CONFIRM)
pxctx promote <doc_id>

# Garbage collect expired items
pxctx gc
```

## Session Lifecycle

1. `pxctx-boot` at start of every session
2. `pxctx-record` / `pxctx-checkpoint` throughout work
3. `pxctx-wrap-up` before ending session

## Failure Fallback

If `pxctx` fails (Python env issue, DB corruption): note the failure, continue work,
record decisions manually as KB notes in `docs/KB/`.
