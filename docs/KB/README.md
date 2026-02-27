# Knowledge Base

This directory is the authoritative Knowledge Base (KB) for the Professor X agent operating in this repository.

## Purpose

Professor X uses this KB as part of its **Long-lived** context tier. Documents here are durable, repo-scoped, and loaded with mild recency weighting during `pxctx query` operations.

## Structure

```
docs/KB/
├── README.md          ← this file (index)
├── INGESTION_SYSTEM_SPEC.md  ← drop-folder ingestion specification (2,300+ lines)
├── architecture/      ← system-level design decisions
├── corpus/            ← domain knowledge about the corpus format and tooling
├── tooling/           ← scripting, CI, and pxctx usage notes
└── treasure/          ← promoted Treasure-tier documents (managed by pxctx promote)
```

## Retrieval Priority

Documents in this KB are ingested by `pxctx add --tier long-lived`. Treasure docs (in `treasure/`) receive the highest priority tier and are always packed first into context.

## KB Document Format

Each KB Markdown file should begin with a YAML front-matter block:

```yaml
---
type: kb-note         # kb-note | architecture | constraint | decision | finding
tags: [tag1, tag2]
sources: []            # optional list of source references
created: YYYY-MM-DD
updated: YYYY-MM-DD
never_expire: false
tier: long-lived       # long-lived | treasure
---
```

## Adding Notes

Use `pxctx add` to index a note from the session, or manually create a `.md` file here and
run `pxctx add --file docs/KB/path/to/note.md --tier long-lived`.

## Governance

- **Treasure** docs require explicit user `CONFIRM` to create or modify.
- All other KB docs can be added freely during work sessions.
- Run `pxctx gc` periodically to remove expired Working-tier items.
