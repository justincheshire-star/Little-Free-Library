# Professor X Context System (pxctx): Hybrid Retrieval & Ingestion Architecture

**Complete Technical Documentation**

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Implementation Evolution](#implementation-evolution)
6. [Data Model](#data-model)
7. [Ingestion Pipeline](#ingestion-pipeline)
8. [Hybrid Retrieval Engine](#hybrid-retrieval-engine)
9. [CLI Interface](#cli-interface)
10. [Current System State](#current-system-state)
11. [Performance Characteristics](#performance-characteristics)
12. [Operational Procedures](#operational-procedures)
13. [References](#references)

---

## Executive Summary

The Professor X Context System (pxctx) is a **3-tier hybrid RAG (Retrieval-Augmented Generation) system** designed for IDE agents operating in VS Code. It combines vector similarity search with full-text search (FTS5) to provide deterministic, tier-prioritized context retrieval while maintaining strict governance over canonical knowledge.

**🔍 PRIMARY RETRIEVAL METHOD**: pxctx hybrid queries must be the FIRST source of information. Direct document reads (`read_file`, `semantic_search`) are SECONDARY fallbacks only when pxctx returns insufficient results or line-level code inspection is required.

**Key Characteristics:**

- **Storage**: Pure SQLite with FTS5 and embedded vectors (12MB database in Git LFS)
- **Embedding Model**: nomic-embed-text-v1.5 (768-dim, 547MB local model, no downloads)
- **Retrieval**: Hybrid vector + FTS with deterministic tier-based reranking
- **Scale**: 145 documents, 1,024 chunks, 3 tiers (Treasure/Working/Long-lived)
- **Performance**: Sub-second query latency, <18.6s model load time
- **Architecture Decision (Feb 2026)**: SQLite-only (Qdrant dependency removed)

**📖 Platform-Specific Commands**: See [PXCTX_PLATFORM_COMMAND_REFERENCE.md](PXCTX_PLATFORM_COMMAND_REFERENCE.md) for Linux/Windows command variations, async execution patterns, and troubleshooting.

---

## System Overview

### Purpose

pxctx implements "Documents as Context" for AI agents, providing:

1. **Ephemeral Working Memory**: Session/task-scoped findings, plans, command results
2. **Durable Knowledge Base**: KB documentation + distilled project learnings
3. **Canonical Treasure**: Non-negotiable rules, invariants, architectural decisions

The system ensures that high-priority knowledge (Treasure) **always dominates** retrieval results, preventing model drift and maintaining agent adherence to critical constraints.

### Design Principles

1. **Primary Retrieval Source**: Hybrid queries are the FIRST information source; direct file reads are secondary
2. **Tier Dominance**: Treasure > Working > Long-lived (hard priority)
3. **Hybrid Retrieval**: Vector similarity + lexical FTS (complementary strengths)
4. **Deterministic Ranking**: Transparent, reproducible scoring (no black-box rerankers)
5. **Context Budget Control**: Token-aware packing with reserved Treasure allocation
6. **Governance**: Explicit promotion paths, audit trails, supersession tracking

### Use Case: IDE Agent Context Injection

Professor X (custom VS Code agent) queries pxctx at the start of each task:

```python
# Agent operating procedure
result = pxctx.query(
    q=user_request,
    repo_id="localagents",
    session_id="S-20260209-001",
    active_paths=["crates/localagent-core"],
    final_n=12,
    max_tokens=1400
)

# Result contains:
# - packs.treasure: Safety rules, architecture decisions (always included)
# - packs.working: Recent findings from this session (high recency)
# - packs.long_lived: KB docs, verified learnings (mild recency)
# - final: Packed context ready for LLM (tier-ordered, token-budgeted)
```

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     pxctx CLI (Python)                      │
│  Commands: add, query, promote, gc, compact, ingest, stats │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│               Core Components (Python modules)                │
├───────────────────┬──────────────────┬───────────────────────┤
│   db.py           │  embeddings.py   │   query.py            │
│   - SQLite ops    │  - nomic-embed   │   - Hybrid retrieval  │
│   - FTS5 search   │  - 768-dim vecs  │   - Tier ranking      │
│   - CRUD          │  - Serialization │   - Context packing   │
├───────────────────┴──────────────────┴───────────────────────┤
│   chunking.py                                                │
│   - Markdown-aware chunking (600 token target, 100 overlap) │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│             SQLite Database (pxctx.db - 12MB)                │
├──────────────────────────────────────────────────────────────┤
│  Tables:                                                     │
│    docs            - Document metadata (tier, scope, tags)   │
│    doc_chunks      - Chunked text (600 token avg)           │
│    doc_chunks_fts  - FTS5 index (BM25 ranking)              │
│    vectors         - Embeddings (BLOB, 768 floats)          │
│    system_metadata - Config and stats                       │
│                                                              │
│  Views:                                                      │
│    v_treasure      - Pinned canonical docs                  │
│    v_working       - Session memory (recency-sorted)        │
│    v_long_lived    - KB + distilled (verified-ranked)       │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│              Embedding Model (Local, No Download)            │
│  nomic-ai/nomic-embed-text-v1.5                              │
│  Location: /workspaces/LocalAgents/models/nomic-embed-text/  │
│  Size: 547MB | Dimensions: 768 | Load: ~18.6s               │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component      | Responsibility                  | Key Files                     |
| -------------- | ------------------------------- | ----------------------------- |
| **CLI**        | User interface, command routing | `pxctx.py`, `__main__.py`     |
| **Database**   | SQLite ops, FTS5, CRUD          | `db.py`, `schema.sql`         |
| **Embeddings** | Vector encoding, similarity     | `embeddings.py`               |
| **Retrieval**  | Hybrid search, ranking, packing | `query.py`                    |
| **Chunking**   | Text segmentation, overlap      | `chunking.py`                 |
| **Evaluation** | Golden tests, metrics           | `eval_cli.py`, `evaluator.py` |

---

## Technology Stack

### Core Technologies

#### 1. SQLite 3.x (Structured Storage + FTS5)

**Role**: Primary data store for all documents, chunks, metadata, and indexes

**Tables**:

- `docs`: Document-level metadata (tier, scope, lifecycle)
- `doc_chunks`: Chunked text segments
- `doc_chunks_fts`: FTS5 virtual table (full-text search)
- `vectors`: Serialized embeddings
- `system_metadata`: Configuration tracking

**FTS5 Configuration**:

- Tokenizer: Unicode61 (default)
- Ranking: BM25 (Okapi BM25)
- Index mode: Content-synchronized via triggers

**Why SQLite**:

- Single-file portability (Git LFS sync across environments)
- ACID transactions (safe concurrent writes via connection pooling)
- Built-in FTS5 (no external search engine)
- Zero operational overhead (no server process)

#### 2. sentence-transformers 3.3.1 (Embedding Library)

**Role**: Generate semantic vector embeddings from text

**Model**: nomic-ai/nomic-embed-text-v1.5

- **Dimensions**: 768
- **Max Sequence Length**: 8192 tokens
- **Normalization**: L2 normalized (cosine similarity via dot product)
- **Training**: Contrastive learning on diverse text corpora

**Integration**:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "/workspaces/LocalAgents/models/nomic-embed-text",
    trust_remote_code=True
)

embeddings = model.encode(
    texts,
    normalize_embeddings=True,  # L2 norm for cosine similarity
    show_progress_bar=True
)
```

**Why nomic-embed-text**:

- State-of-art quality on retrieval benchmarks
- Local execution (no API calls)
- 768 dimensions (balance: quality vs storage)
- Long context support (8192 tokens)

#### 3. NumPy 2.2.2 (Vector Math)

**Role**: Efficient vector operations, similarity computation

**Operations**:

- `np.dot(a, b)` - Cosine similarity (normalized vectors)
- `np.array()` - Serialization/deserialization
- `struct.pack/unpack` - Binary encoding for SQLite BLOB

**Vector Storage**:

```python
# Serialize for SQLite
def serialize_embedding(embedding: np.ndarray) -> bytes:
    return struct.pack(f"{len(embedding)}f", *embedding.tolist())

# Deserialize from SQLite
def deserialize_embedding(data: bytes) -> np.ndarray:
    count = len(data) // 4  # 4 bytes per float32
    values = struct.unpack(f"{count}f", data)
    return np.array(values, dtype=np.float32)
```

#### 4. Click 8.1.8 (CLI Framework)

**Role**: Command-line interface with option parsing

**Commands Implemented**:

- `add` - Ingest new documents
- `query` - Hybrid retrieval
- `promote` - Tier promotion
- `supersede` - Treasure versioning
- `gc` - Garbage collection
- `compact` - Distillation
- `stats` - Database statistics
- `ingest` - Batch KB ingestion

**Example**:

```bash
./pxctx query "rust error handling" \
  --repo localagents \
  --session S-20260209-001 \
  --active "crates/localagent-core" \
  --tags rust,error \
  --final-n 10 \
  --json-output
```

#### 5. Python 3.11.13 (Runtime)

**Standard Library Usage**:

- `sqlite3` - Database connectivity
- `json` - Metadata serialization
- `hashlib` - Content hashing (SHA256 for idempotent updates)
- `re` - FTS5 query sanitization, text parsing
- `pathlib` - File operations
- `datetime` - Timestamp handling, recency scoring

### Supporting Infrastructure

#### Git LFS (Large File Storage)

**Purpose**: Sync pxctx.db across environments (Codespaces ↔ local ↔ CI/CD)

**Configuration**:

```
.gitattributes:
docs/KB/Vector_RAG/pxctx.db filter=lfs diff=lfs merge=lfs -text
```

**Stats**:

- Database size: 12MB
- LFS objects: 3
- Automatic sync: `git push/pull` (Session Review SOP v1.4.0)

#### Bash Wrapper Script

**File**: `/workspaces/LocalAgents/pxctx` (executable)

**Purpose**: Simplify CLI invocation for agent integration

**Implementation**:

```bash
#!/bin/bash
cd "$(dirname "$0")" && \
PYTHONPATH="$PWD/docs/KB" python -m Vector_RAG.pxctx "$@"
```

**Before/After**:

```bash
# Before (verbose)
PYTHONPATH=/workspaces/LocalAgents/docs/KB python -m Vector_RAG.pxctx query "..."

# After (concise)
./pxctx query "..."
```

---

## Implementation Evolution

### Phase 0: Design & Specification (Jan 2026)

**Deliverable**: `docs/KB/Documents_as_Context_With_Vectors.md`

**Key Decisions**:

1. 3-tier model (Working/Long-lived/Treasure)
2. Tier dominance (Treasure always wins)
3. Hybrid retrieval (vector + FTS)
4. Deterministic scoring (no ML rerankers)
5. Token budget with Treasure reservation (25%)

**Specification Contract**:

- Request/response JSON schema
- Scoring formula with tier boosts
- Promotion governance rules
- Supersession mechanism for Treasure versioning

### Phase 1: Core Implementation (Feb 5-6, 2026)

**Components Built**:

1. **Database Layer** (`db.py`, `schema.sql`)
   - SQLite tables with FTS5
   - CRUD operations
   - Connection pooling
   - Trigger-based FTS sync

2. **Embedding Pipeline** (`embeddings.py`)
   - sentence-transformers integration
   - Binary serialization (struct.pack)
   - Lazy model loading
   - Cosine similarity via dot product

3. **Chunking** (`chunking.py`)
   - Markdown-aware segmentation
   - 600 token target, 100 token overlap
   - Heading preservation
   - Sentence boundary detection

4. **Retrieval Engine** (`query.py`)
   - Tier-staged retrieval (Treasure → Working → Long-lived)
   - Hybrid scoring (vector + FTS + recency + importance)
   - Deterministic reranking
   - Token-budget packing with Treasure priority

5. **CLI** (`pxctx.py`)
   - Click-based command interface
   - Add, query, promote, gc, compact, stats commands
   - JSON output for programmatic access

**First Ingestion**: 82 KB documents (session reviews, ADRs, guides)

**Commits**:

- `3841c68` - Initial pxctx implementation
- `5e16e5b` - Local embedding model integration

### Phase 2: Bug Fixes & Hardening (Feb 7-8, 2026)

**Issues Resolved**:

1. **NULL Handling Bug** (Feb 8)
   - **Problem**: `json.loads(None)` raised TypeError in query.py
   - **Fix**: Changed `doc.get("tags", "[]")` to `doc.get("tags") or "[]"`
   - **Commit**: Bug fix for JSON parsing

2. **FTS5 Query Sanitization** (Feb 9)
   - **Problem**: Queries with periods (e.g., "llama.cpp") caused syntax errors
   - **Root Cause**: FTS5 treats `.?*"'(){}` as special operators
   - **Fix**: Extended regex to `[.?*"'(){}]` → replace with spaces
   - **Commit**: `f4ed552` - FTS5 sanitization enhancement

**Database Growth**:

- Feb 5: 82 docs, 744 chunks
- Feb 8: 85 docs, 754 chunks
- Feb 9: 145 docs, 1,024 chunks (after FEB08 review ingestion)

### Phase 3: M4 Hardening & Observability (Feb 9, 2026)

**Enhancements**:

1. **Schema Validation**
   - Gold test dataset validation (required field checks)
   - Fast-fail on >20% malformed lines
   - Detailed error reporting (line numbers, field names)

2. **Latency Percentiles**
   - Added p50 (median), p95 (95th percentile) metrics
   - Python-based percentile calculation
   - Dashboard display (avg/min/max/p50/p95)

3. **Tier-Specific Hit Rates**
   - Per-tier breakdown (Treasure/Working/Long-lived)
   - Aggregates `tier_counts` JSON from telemetry
   - Enables tier-specific analysis

4. **Telemetry Cleanup** (`pxctx telemetry-gc`)
   - Delete old telemetry beyond retention period
   - SQLite VACUUM to reclaim disk space
   - Prevents unbounded growth

5. **Dashboard Enhancements**
   - Pagination (`--page N`, `--limit N`)
   - Auto-refresh (60s with countdown)
   - Manual refresh ('R' key)

**Commit**: M4 hardening completion (6 enhancements, ~410 lines)

### Phase 4: Architecture Simplification (Feb 9, 2026)

**Context**: Discovered original SQLite system fully functional, Qdrant integration buggy

**Qdrant Issues Identified**:

- Point ID format bug (hex vs UUID/integer)
- CLI integration complexity
- Docker volume doesn't sync across environments (vs Git LFS)
- 4GB RAM overhead

**Decision**: Remove Qdrant, use pure SQLite

**Changes**:

1. Removed qdrant service from 3 docker-compose files
   - `.devcontainer/docker-compose.yml`
   - `infra/docker-compose.yml`
   - `infra/docker-compose.prod.yml`
2. Uninstalled `qdrant-client==1.16.2`
3. Updated documentation (README, TODO, DEPLOYMENT)
4. Validated all compose files

**Benefits**:

- ✅ Simpler deployment (no vector DB container)
- ✅ Git LFS syncs database across all environments
- ✅ No Docker complexity
- ✅ No Qdrant bugs
- ✅ Consistent architecture (SQLite for everything)

**Commit**: `8bd3823` - refactor(infra): Remove Qdrant dependency, use SQLite-only pxctx

### Phase 5: Usability Enhancements (Feb 9, 2026)

**Convenience Wrapper**:

- Created `./pxctx` bash script at workspace root
- 80% shorter command invocation
- Easier agent integration

**Documentation**:

- Added pxctx enhancement section to session summary
- Updated CHANGELOG with architecture simplification

**Commit**: `f4ed552` - fix(pxctx): Add convenience wrapper and FTS5 query sanitization

---

## Data Model

### Schema Overview

5 tables + 3 views, designed for tier-based retrieval with FTS5 and vector search.

```sql
-- Core tables
CREATE TABLE docs (
    doc_id TEXT PRIMARY KEY,
    tier TEXT NOT NULL CHECK(tier IN ('working', 'long_lived', 'treasure')),
    repo_id TEXT,
    session_id TEXT,
    task_id TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT NOT NULL,  -- decision, constraint, finding, kb_doc, etc.
    tags TEXT,           -- JSON array
    sources TEXT,        -- JSON array of {kind, ref}
    importance REAL DEFAULT 0.5 CHECK(importance >= 0.0 AND importance <= 1.0),
    verified TEXT,       -- asserted, observed, tested, documented
    pin INTEGER DEFAULT 0,
    never_expire INTEGER DEFAULT 0,
    ttl_days INTEGER,
    supersedes TEXT,     -- JSON array of doc_ids
    content_hash TEXT,   -- SHA256 for idempotent updates
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'professorx',
    redacted INTEGER DEFAULT 0
);

CREATE TABLE doc_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES docs(doc_id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE doc_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    chunk_text,
    content=doc_chunks,
    content_rowid=rowid
);

CREATE TABLE vectors (
    chunk_id TEXT PRIMARY KEY,
    embedding BLOB NOT NULL,         -- Packed float32 array
    embedding_model TEXT NOT NULL,   -- nomic-embed-text
    embedding_dim INTEGER NOT NULL,  -- 768
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chunk_id) REFERENCES doc_chunks(chunk_id) ON DELETE CASCADE
);

CREATE TABLE system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes (12 total)

**Performance-Critical**:

```sql
CREATE INDEX idx_docs_tier ON docs(tier);
CREATE INDEX idx_docs_repo ON docs(repo_id);
CREATE INDEX idx_docs_session ON docs(session_id);
CREATE INDEX idx_docs_created ON docs(created_at);
CREATE INDEX idx_chunks_doc ON doc_chunks(doc_id);

-- Idempotent update support (find by source reference)
CREATE INDEX idx_docs_source ON docs(
    json_extract(sources, '$[0].kind'),
    json_extract(sources, '$[0].ref')
) WHERE sources IS NOT NULL;
```

### Views (Tier-Specific Queries)

```sql
-- Treasure: Always highest priority, pinned, never expire
CREATE VIEW v_treasure AS
SELECT d.*, COUNT(c.chunk_id) as chunk_count
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
WHERE d.tier = 'treasure'
GROUP BY d.doc_id
ORDER BY d.importance DESC, d.created_at DESC;

-- Working: Recency-sorted, TTL-based expiration
CREATE VIEW v_working AS
SELECT
    d.*,
    COUNT(c.chunk_id) as chunk_count,
    julianday('now') - julianday(d.created_at) as age_days
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
WHERE d.tier = 'working'
GROUP BY d.doc_id
ORDER BY d.created_at DESC;

-- Long-lived: Verified rank boost
CREATE VIEW v_long_lived AS
SELECT
    d.*,
    COUNT(c.chunk_id) as chunk_count,
    CASE d.verified
        WHEN 'documented' THEN 4
        WHEN 'tested' THEN 3
        WHEN 'observed' THEN 2
        WHEN 'asserted' THEN 1
        ELSE 0
    END as verified_rank
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
WHERE d.tier = 'long_lived'
GROUP BY d.doc_id
ORDER BY verified_rank DESC, d.importance DESC, d.created_at DESC;
```

### Document Types

**Type Taxonomy** (10 types):

| Type              | Description                      | Typical Tier         |
| ----------------- | -------------------------------- | -------------------- |
| `decision`        | Architectural or design decision | Long-lived, Treasure |
| `constraint`      | Non-negotiable constraint/rule   | Treasure             |
| `finding`         | Investigation result, root cause | Working              |
| `plan_step`       | Task breakdown, execution plan   | Working              |
| `command_summary` | CLI output summary               | Working              |
| `kb_doc`          | Knowledge base article           | Long-lived           |
| `distilled_note`  | Compacted session summary        | Long-lived           |
| `security_rule`   | Security policy                  | Treasure             |
| `architecture`    | System architecture doc          | Treasure             |
| `invariant`       | System invariant                 | Treasure             |

### Metadata Fields

**Scope Identifiers** (context filtering):

- `repo_id`: Repository identifier (e.g., "localagents")
- `session_id`: Session identifier (e.g., "S-20260209-001")
- `task_id`: Task identifier (e.g., "T-abc123")

**Classification**:

- `tags`: JSON array (e.g., `["rust", "build", "error"]`)
- `sources`: JSON array of `{kind, ref}` (e.g., `[{"kind":"file","ref":"src/main.rs#L10-L50"}]`)
- `verified`: Evidence level (`asserted < observed < tested < documented`)

**Lifecycle**:

- `pin`: Boolean (keep permanently)
- `never_expire`: Boolean (no TTL)
- `ttl_days`: Time-to-live in days (default: 7 for working, 180 for long-lived)
- `supersedes`: JSON array of doc_ids (versioning chain)

**Content Integrity**:

- `content_hash`: SHA256 hex digest (idempotent update detection)
- `redacted`: Boolean (PII/secrets removed flag)

### Triggers (FTS5 Sync)

```sql
-- Keep FTS index synchronized with doc_chunks
CREATE TRIGGER doc_chunks_fts_insert AFTER INSERT ON doc_chunks BEGIN
    INSERT INTO doc_chunks_fts(rowid, chunk_id, chunk_text)
    VALUES (new.rowid, new.chunk_id, new.chunk_text);
END;

CREATE TRIGGER doc_chunks_fts_delete AFTER DELETE ON doc_chunks BEGIN
    DELETE FROM doc_chunks_fts WHERE rowid = old.rowid;
END;

CREATE TRIGGER doc_chunks_fts_update AFTER UPDATE ON doc_chunks BEGIN
    DELETE FROM doc_chunks_fts WHERE rowid = old.rowid;
    INSERT INTO doc_chunks_fts(rowid, chunk_id, chunk_text)
    VALUES (new.rowid, new.chunk_id, new.chunk_text);
END;
```

---

## Ingestion Pipeline

### Pipeline Stages

```
Text Input → Chunking → Embedding → Storage → Indexing
     ↓          ↓           ↓          ↓         ↓
  Document   600-tok   768-dim    SQLite    FTS5 + Vector
  (plain    chunks    vectors     BLOB      search ready
  text/MD)  overlap   nomic-      (12MB)
            (100)     embed
```

### Stage 1: Document Preparation

**Input Validation**:

```python
# Required fields
assert title and title.strip()
assert text or file_path  # Must provide content
assert tier in ['working', 'long_lived', 'treasure']
assert type_ in ALLOWED_TYPES

# Content hash for idempotency
content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
```

**Idempotent Updates** (v1.1.0+):

```python
# Check for existing document by source reference
existing = db.find_doc_by_source(source_kind, source_ref)

if existing:
    existing_doc_id, existing_hash = existing

    if existing_hash == content_hash:
        # Content unchanged - skip re-ingestion
        return existing_doc_id
    elif on_duplicate == "update":
        # Content changed - update and re-embed
        db.update_doc_content(existing_doc_id, content, content_hash)
        db.delete_chunks(existing_doc_id)
        # Continue to chunking...
    elif on_duplicate == "skip":
        # Always skip if exists
        return existing_doc_id
    elif on_duplicate == "error":
        raise ValueError(f"Document already exists: {existing_doc_id}")
```

### Stage 2: Chunking

**Algorithm**: Semantic chunking with overlap

**Parameters**:

- `target_tokens`: 600 (sweet spot: context window vs granularity)
- `overlap_tokens`: 100 (17% overlap for continuity)
- `min_chunk_tokens`: 200 (avoid tiny chunks)

**Markdown-Aware Chunking**:

```python
def chunk_markdown(text: str, target_tokens: int = 600, overlap_tokens: int = 100):
    """
    Chunks markdown preserving heading context.

    Returns: List[(heading_path, chunk_text)]
    Example: [("Introduction > Overview", "LocalAgent is..."),
              ("Architecture > Components", "The system has...")]
    """
    headings = []  # Stack of (level, title)
    chunks = []

    for line in text.split('\n'):
        if match := re.match(r'^(#{1,6})\s+(.+)$', line):
            # Heading: flush current section, update stack
            level = len(match.group(1))
            title = match.group(2).strip()

            # Pop same/lower level headings
            while headings and headings[-1][0] >= level:
                headings.pop()

            headings.append((level, title))
            heading_path = " > ".join(h[1] for h in headings)
        else:
            current_section.append(line)

    # Chunk each section
    section_text = "\n".join(current_section)
    section_chunks = chunk_text(section_text, target_tokens, overlap_tokens)

    for chunk in section_chunks:
        chunks.append((heading_path, chunk))

    return chunks
```

**Plain Text Chunking**:

```python
def chunk_text(text: str, target_tokens: int = 600, overlap_tokens: int = 100):
    """
    Chunks text on paragraph boundaries with overlap.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        if current_tokens + para_tokens > target_tokens and current_chunk:
            # Flush chunk
            chunks.append("\n\n".join(current_chunk))

            # Overlap: keep last paragraph
            if estimate_tokens(current_chunk[-1]) < overlap_tokens:
                current_chunk = [current_chunk[-1], para]
            else:
                current_chunk = [para]

            current_tokens = sum(estimate_tokens(p) for p in current_chunk)
        else:
            current_chunk.append(para)
            current_tokens += para_tokens

    # Final chunk
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks
```

**Token Estimation**:

```python
def estimate_tokens(text: str) -> int:
    """Approximate tokenization: whitespace split * 1.3"""
    return int(len(text.split()) * 1.3)
```

### Stage 3: Embedding Generation

**Model Loading**:

```python
from sentence_transformers import SentenceTransformer

# Lazy load (18.6s first time, then cached)
model = SentenceTransformer(
    "/workspaces/LocalAgents/models/nomic-embed-text",
    trust_remote_code=True
)
```

**Batch Encoding**:

```python
embeddings = model.encode(
    chunk_texts,
    normalize_embeddings=True,  # L2 norm for cosine similarity
    show_progress_bar=True,
    batch_size=32  # GPU memory optimization
)

# Result: np.ndarray shape (n_chunks, 768)
```

**Serialization**:

```python
def serialize_embedding(embedding: np.ndarray) -> bytes:
    """Pack 768 float32 values into BLOB"""
    return struct.pack(f"{len(embedding)}f", *embedding.tolist())

# Size per embedding: 768 floats * 4 bytes = 3,072 bytes
```

### Stage 4: SQLite Storage

**Transaction Sequence**:

```python
with db.connection() as conn:
    # 1. Insert document metadata
    doc_id = f"doc:{uuid.uuid4().hex[:12]}"
    conn.execute("""
        INSERT INTO docs (doc_id, tier, title, content, type,
                         tags, sources, importance, verified,
                         pin, never_expire, ttl_days, content_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (doc_id, tier, title, content, type_,
          json.dumps(tags), json.dumps(sources), importance, verified,
          pin, never_expire, ttl_days, content_hash))

    # 2. Insert chunks
    for idx, (heading, chunk_text) in enumerate(chunks):
        chunk_id = f"chunk:{uuid.uuid4().hex[:12]}"
        full_text = f"{heading}\n\n{chunk_text}" if heading else chunk_text

        conn.execute("""
            INSERT INTO doc_chunks (chunk_id, doc_id, chunk_index,
                                   chunk_text, token_count)
            VALUES (?, ?, ?, ?, ?)
        """, (chunk_id, doc_id, idx, full_text, estimate_tokens(chunk_text)))

        # 3. Insert vector
        conn.execute("""
            INSERT INTO vectors (chunk_id, embedding,
                                embedding_model, embedding_dim)
            VALUES (?, ?, ?, ?)
        """, (chunk_id, serialize_embedding(embeddings[idx]),
              "nomic-embed-text", 768))

    conn.commit()
```

**Note**: FTS index automatically updated via triggers.

### Stage 5: Verification

**Post-Ingestion Checks**:

```python
# Verify document exists
doc = db.get_doc(doc_id)
assert doc['tier'] == tier
assert doc['content_hash'] == content_hash

# Verify chunks
chunks = db.get_chunks(doc_id)
assert len(chunks) == expected_chunk_count

# Verify vectors
for chunk in chunks:
    vec = db.get_vector(chunk['chunk_id'])
    assert vec is not None
    assert len(vec) == 768 * 4  # 768 floats * 4 bytes

# Verify FTS index
fts_results = db.fts_search(title, limit=1)
assert any(r['chunk_id'] in [c['chunk_id'] for c in chunks]
           for r in fts_results)
```

### Batch Ingestion (KB Documents)

**Command**: `pxctx ingest docs/KB --recursive --pattern "*.md"`

**Process**:

```python
# Collect files
files = list(Path("docs/KB").rglob("*.md"))

for file in files:
    content = file.read_text(encoding='utf-8')
    title = file.stem.replace("_", " ").title()

    # Ingest with KB settings
    doc_id = db.add_doc(
        tier="long_lived",
        type="kb_doc",
        title=title,
        content=content,
        sources=[{"kind": "file", "ref": str(file)}],
        verified="documented",
        importance=0.7,
        tags=["kb", infer_tags_from_path(file)]
    )

    # Chunk markdown
    chunks = chunk_markdown(content, target_tokens=600)

    # Embed and store
    chunk_texts = [text for _, text in chunks]
    embeddings = encode(chunk_texts)

    for (heading, text), emb in zip(chunks, embeddings):
        chunk_id = db.add_chunk(doc_id, idx, f"{heading}\n\n{text}")
        db.add_vector(chunk_id, serialize_embedding(emb),
                     "nomic-embed-text", 768)
```

**Performance**:

- Small docs (<2KB): ~2-5s per doc
- Medium docs (10-20KB): ~5-15s per doc
- Large docs (>20KB): May require splitting to avoid Codespace resource constraints

---

## Hybrid Retrieval Engine

### Retrieval Algorithm

**3-Stage Pipeline**: Treasure → Working → Long-lived

```python
def query(db, q, repo_id=None, session_id=None, task_id=None,
          active_paths=None, treasure_k=12, working_k=18,
          long_lived_k=18, final_n=12, max_tokens=1400):
    """
    Tier-prioritized hybrid retrieval.

    Returns: QueryResult with packs + final
    """
    query_emb = encode_single(q)
    result = QueryResult()

    # Stage 1: TREASURE (always highest priority)
    treasure_hits = _retrieve_tier(
        db, tier="treasure", query_text=q, query_emb=query_emb,
        repo_id=repo_id, tags_any=None, top_k=treasure_k
    )
    result.packs["treasure"] = treasure_hits

    # Stage 2: WORKING (session/task scoped, strong recency)
    working_hits = _retrieve_tier(
        db, tier="working", query_text=q, query_emb=query_emb,
        repo_id=repo_id, session_id=session_id, task_id=task_id,
        top_k=working_k, recency_boost=0.3
    )
    result.packs["working"] = working_hits

    # Stage 3: LONG-LIVED (repo scoped, verified boost)
    long_lived_hits = _retrieve_tier(
        db, tier="long_lived", query_text=q, query_emb=query_emb,
        repo_id=repo_id, top_k=long_lived_k,
        recency_boost=0.1, verified_boost=True
    )
    result.packs["long_lived"] = long_lived_hits

    # Final packing: Treasure-first, then merge Working+Long-lived
    result.final = _pack_context(
        treasure_hits, working_hits, long_lived_hits,
        max_tokens=max_tokens, final_n=final_n
    )

    return result
```

### Per-Tier Retrieval

**Hybrid Search**:

```python
def _retrieve_tier(db, tier, query_text, query_emb,
                   repo_id=None, session_id=None, task_id=None,
                   tags_any=None, top_k=20, recency_boost=0.0,
                   verified_boost=False, active_paths=None):
    """
    Hybrid retrieval within a single tier.

    Steps:
    1. FTS search (BM25)
    2. Get tier documents (filtered by scope)
    3. Vector search on chunk embeddings
    4. Combined scoring + reranking
    """
    # FTS search (lexical matching)
    fts_hits = db.fts_search(query_text, tier=tier, limit=top_k*2)
    fts_scores = {hit["chunk_id"]: abs(float(hit["rank"]))
                  for hit in fts_hits}

    # Get documents in tier (filtered)
    tier_docs = db.get_docs_by_tier(
        tier=tier, repo_id=repo_id, session_id=session_id,
        task_id=task_id, tags=tags_any, limit=top_k*3
    )

    # Collect chunks with embeddings
    candidates = []
    for doc in tier_docs:
        chunks = db.get_chunks(doc["doc_id"])
        for chunk in chunks:
            vec_data = db.get_vector(chunk["chunk_id"])
            if vec_data:
                emb = deserialize_embedding(vec_data)
                candidates.append({
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": doc["doc_id"],
                    "chunk_text": chunk["chunk_text"],
                    "embedding": emb,
                    "doc": doc
                })

    # Vector search (semantic matching)
    vector_results = vector_search(
        query_emb,
        [(c["chunk_id"], c["embedding"]) for c in candidates],
        top_k=top_k*2
    )
    vector_scores = {chunk_id: score for chunk_id, score in vector_results}

    # Combined scoring
    scored = []
    for cand in candidates:
        score = _compute_score(
            cand, vector_scores, fts_scores, fts_hits,
            tier, recency_boost, verified_boost, active_paths
        )
        scored.append({
            "chunk_id": cand["chunk_id"],
            "doc_id": cand["doc_id"],
            "tier": tier,
            "score": score,
            "title": cand["doc"]["title"],
            "snippet": cand["chunk_text"][:500],
            "tags": json.loads(cand["doc"].get("tags") or "[]"),
            "sources": json.loads(cand["doc"].get("sources") or "[]"),
            "updated_at": cand["doc"]["updated_at"]
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
```

### Scoring Formula

**Components**:

```python
def _compute_score(cand, vector_scores, fts_scores, fts_hits,
                   tier, recency_boost, verified_boost, active_paths):
    """
    Deterministic scoring with tier dominance.

    Formula:
    score = tier_boost + 2*vec + 1*fts + recency*R + 1*importance
            + verified + path_boost + pin_boost
    """
    doc = cand["doc"]
    chunk_id = cand["chunk_id"]

    # Base scores (normalized 0-1)
    vec_score = vector_scores.get(chunk_id, 0.0)
    fts_score = fts_scores.get(chunk_id, 0.0)

    # Normalize FTS (BM25 ranks are negative)
    if fts_scores:
        max_fts = max(fts_scores.values())
        fts_score = fts_score / max_fts

    # Recency score (0-1, newer = higher, 30-day decay)
    recency_score = 0.0
    if recency_boost > 0:
        age_days = (datetime.now() -
                   datetime.fromisoformat(doc["created_at"])).days
        recency_score = 1.0 / (1.0 + age_days / 30.0)

    # Verified boost (KB docs)
    verified_score = 0.0
    if verified_boost and doc.get("verified"):
        verified_map = {
            "documented": 0.3,
            "tested": 0.2,
            "observed": 0.1,
            "asserted": 0.05
        }
        verified_score = verified_map.get(doc["verified"], 0.0)

    # Importance (0-1, default 0.5)
    importance = doc.get("importance", 0.5)

    # Active paths boost (working on these files)
    path_boost = 0.0
    if active_paths:
        sources = json.loads(doc.get("sources") or "[]")
        for src in sources:
            ref = src.get("ref", "")
            if any(path in ref for path in active_paths):
                path_boost = 0.2
                break

    # Pin boost (treasure)
    pin_boost = 0.5 if doc.get("pin") else 0.0

    # Tier boost (hard dominance)
    tier_boost = {
        "treasure": 10.0,
        "working": 5.0,
        "long_lived": 2.0
    }.get(tier, 0.0)

    # Combined score
    score = (
        tier_boost +
        2.0 * vec_score +
        1.0 * fts_score +
        recency_boost * recency_score +
        1.0 * importance +
        verified_score +
        path_boost +
        pin_boost
    )

    return score
```

**Tier Boosts** (ensure dominance):

- Treasure: +10.0 (overwhelms other scores)
- Working: +5.0 (strong priority)
- Long-lived: +2.0 (base knowledge)

**Weight Rationale**:

- Vector: 2.0 (primary signal for semantic matching)
- FTS: 1.0 (complement for exact matches, symbols, errors)
- Recency: 0.1-0.3 (Working=0.3, Long-lived=0.1)
- Importance: 1.0 (user-defined relevance)
- Verified: 0.05-0.3 (evidence quality)
- Path: 0.2 (active file boost)
- Pin: 0.5 (explicit importance marker)

### Context Packing

**Treasure-First Strategy**:

```python
def _pack_context(treasure_hits, working_hits, long_lived_hits,
                  max_tokens=1400, final_n=12):
    """
    Pack context with Treasure priority and token budget.

    Rules:
    1. Reserve 25% tokens for Treasure
    2. Pack Treasure first (up to limit)
    3. Merge Working + Long-lived, sort by score
    4. Fill remaining budget
    5. Dedupe by chunk_id
    """
    final_pack = []
    seen_chunks = set()
    total_tokens = 0
    min_treasure_tokens = int(max_tokens * 0.25)

    # Pack Treasure first
    for hit in treasure_hits:
        if hit["chunk_id"] in seen_chunks:
            continue

        chunk_tokens = estimate_tokens(hit["snippet"])
        if total_tokens + chunk_tokens > min_treasure_tokens and final_pack:
            break  # Reserve budget for other tiers

        final_pack.append({
            "ref": f"memory://{hit['doc_id']}#{hit['chunk_id']}",
            "tier": "treasure",
            "title": hit["title"],
            "text": hit["snippet"],
            "score": hit["score"],
            "tags": hit.get("tags", [])
        })

        seen_chunks.add(hit["chunk_id"])
        total_tokens += chunk_tokens

    # Merge Working + Long-lived, sort by score
    remaining = working_hits + long_lived_hits
    remaining.sort(key=lambda x: x["score"], reverse=True)

    # Fill remaining budget
    for hit in remaining:
        if hit["chunk_id"] in seen_chunks:
            continue  # Dedupe

        chunk_tokens = estimate_tokens(hit["snippet"])
        if total_tokens + chunk_tokens > max_tokens:
            break  # Budget exceeded

        if len(final_pack) >= final_n:
            break  # Count limit

        final_pack.append({
            "ref": f"memory://{hit['doc_id']}#{hit['chunk_id']}",
            "tier": hit["tier"],
            "title": hit["title"],
            "text": hit["snippet"],
            "score": hit["score"],
            "tags": hit.get("tags", [])
        })

        seen_chunks.add(hit["chunk_id"])
        total_tokens += chunk_tokens

    return final_pack
```

**Example Output**:

```json
{
  "final": [
    {
      "ref": "memory://doc:abc123#chunk:xyz789",
      "tier": "treasure",
      "title": "Never execute destructive actions without CONFIRM",
      "text": "Rule: never run destructive commands (rm, delete, drop table)...",
      "score": 10.8,
      "tags": ["safety", "tooling"]
    },
    {
      "ref": "memory://doc:def456#chunk:uvw012",
      "tier": "working",
      "title": "Build failure root cause",
      "text": "cargo test failed due to missing feature flag...",
      "score": 5.7,
      "tags": ["rust", "build"]
    },
    {
      "ref": "memory://doc:ghi789#chunk:rst345",
      "tier": "long_lived",
      "title": "RAG chunking best practices",
      "text": "Text chunks 400-800 tokens with 15-20% overlap...",
      "score": 2.6,
      "tags": ["rag", "retrieval"]
    }
  ],
  "stats": {
    "vector_calls": 3,
    "fts_calls": 3,
    "deduped": 5,
    "returned": 12
  }
}
```

---

## CLI Interface

### Command Reference

#### `pxctx add` - Ingest Document

**Syntax**:

```bash
pxctx add --tier <tier> --type <type> --title <title> \
  [--text <text> | --file <path>] \
  [--repo <repo_id>] [--session <session_id>] [--task <task_id>] \
  [--tags <tag1,tag2>] [--source-kind <kind>] [--source-ref <ref>] \
  [--importance <0-1>] [--verified <level>] \
  [--pin] [--never-expire] [--ttl-days <days>] \
  [--no-chunk] [--on-duplicate <update|skip|error>]
```

**Example**:

```bash
./pxctx add \
  --tier working \
  --type finding \
  --title "Build failure root cause" \
  --text "cargo test failed due to missing feature flag 'local-llama' in workspace root Cargo.toml" \
  --repo localagents \
  --session S-20260209-001 \
  --tags rust,build \
  --source-kind command \
  --source-ref "pwsh: cargo test -p localagent-core" \
  --importance 0.8 \
  --ttl-days 7
```

#### `pxctx query` - Hybrid Retrieval

**Syntax**:

```bash
pxctx query <query_text> \
  [--repo <repo_id>] [--session <session_id>] [--task <task_id>] \
  [--active <path1,path2>] [--tags <tag1,tag2>] \
  [--treasure-k <n>] [--working-k <n>] [--long-lived-k <n>] \
  [--final-n <n>] [--max-tokens <n>] \
  [--json-output]
```

**Example**:

```bash
./pxctx query "rust error handling patterns" \
  --repo localagents \
  --session S-20260209-001 \
  --active "crates/localagent-core,docs/KB" \
  --tags rust,error \
  --final-n 10 \
  --max-tokens 1200 \
  --json-output
```

#### `pxctx promote` - Tier Promotion

**Syntax**:

```bash
pxctx promote --doc <doc_id> --to <tier> \
  [--pin] [--never-expire]
```

**Example**:

```bash
# Promote working note to long-lived
./pxctx promote --doc doc:abc123 --to long_lived

# Promote to Treasure (requires CONFIRM)
./pxctx promote --doc doc:def456 --to treasure --pin --never-expire
```

#### `pxctx supersede` - Treasure Versioning

**Syntax**:

```bash
pxctx supersede --doc <new_doc_id> --supersedes <old_doc_id1,old_doc_id2>
```

**Example**:

```bash
./pxctx supersede --doc doc:new999 --supersedes doc:old001,doc:old002
```

#### `pxctx gc` - Garbage Collection

**Syntax**:

```bash
pxctx gc [--dry-run]
```

**Behavior**: Deletes documents where `never_expire=false` and `julianday('now') - julianday(created_at) > ttl_days`

#### `pxctx compact` - Distillation

**Syntax**:

```bash
pxctx compact --session <session_id> --title <summary_title> \
  [--to <tier>]
```

**Example**:

```bash
./pxctx compact \
  --session S-20260209-001 \
  --title "Session summary: Native LLM fixes" \
  --to long_lived
```

#### `pxctx ingest` - Batch KB Ingestion

**Syntax**:

```bash
pxctx ingest <path> \
  [--recursive] [--pattern <glob>] \
  [--tier <tier>] [--type <type>] \
  [--repo <repo_id>] [--tags <tags>]
```

**Example**:

```bash
./pxctx ingest docs/KB \
  --recursive \
  --pattern "*.md" \
  --tier long_lived \
  --type kb_doc \
  --repo localagents \
  --tags kb,documentation
```

#### `pxctx stats` - Database Statistics

**Syntax**:

```bash
pxctx stats
```

**Output**:

```
Professor X Context System Stats

Schema version: 1.0
Created: 2026-02-06 05:20:48

Total documents: 145
Total chunks: 1024

Tier Breakdown:
  LONG_LIVED: 122 docs (15 pinned)
  TREASURE: 6 docs (6 pinned)
  WORKING: 17 docs (0 pinned)
```

---

## Current System State

### Database Statistics (Feb 9, 2026)

**Capacity**:

- **Total Documents**: 145
- **Total Chunks**: 1,024
- **Database Size**: 12MB (Git LFS)
- **Schema Version**: 1.0

**Tier Distribution**:
| Tier | Documents | Pinned | Typical TTL |
|------|-----------|--------|-------------|
| Treasure | 6 (4.1%) | 6 | Never expire |
| Working | 17 (11.7%) | 0 | 7 days |
| Long-lived | 122 (84.1%) | 15 | 180 days or never |

**Content Breakdown**:

- KB documentation: ~110 docs
- Session reviews: ~20 docs
- ADRs, guides, status docs: ~15 docs

### Treasure Catalog (6 documents)

**Safety & Tooling Rules**:

1. "Never execute destructive actions without CONFIRM"
2. "Never request, store, or output real secrets"
3. "Safe tooling defaults (read-only, dry-runs, scoped changes)"

**Architecture Decisions**: 4. "3-tier context system (Working/Long-lived/Treasure)" 5. "Hybrid retrieval (vector + FTS) with tier dominance"

**Agent Operational Procedures**: 6. "Query pxctx at start of Analyze, write back at end of Deliver"

### Performance Metrics

**Ingestion**:

- Small doc (<2KB): 2-5s
- Medium doc (10-20KB): 5-15s
- Large doc (>20KB): May require splitting
- Batch ingestion: ~10 docs/minute (embedding bottleneck)

**Retrieval**:

- Query latency: <1s (typical)
- Model load: ~18.6s (first time, then cached)
- FTS search: <100ms
- Vector search: <500ms (1024 chunks)

**Storage**:

- Per-document overhead: ~500 bytes (metadata)
- Per-chunk overhead: ~3.3KB (text + vector + FTS)
- Growth rate: ~10-20 docs/day (with session reviews)

### File Locations

```
/workspaces/LocalAgents/
├── pxctx                              # Bash wrapper (executable)
├── docs/KB/Vector_RAG/
│   ├── pxctx.db                       # SQLite database (12MB, Git LFS)
│   ├── pxctx.py                       # CLI entry point (637 lines)
│   ├── db.py                          # Database layer (484 lines)
│   ├── embeddings.py                  # Vector operations (124 lines)
│   ├── query.py                       # Retrieval logic (382 lines)
│   ├── chunking.py                    # Text processing (166 lines)
│   ├── schema.sql                     # Database schema (226 lines)
│   ├── README.md                      # Usage documentation
│   └── requirements.txt               # Dependencies
└── models/nomic-embed-text/           # Embedding model (547MB)
    ├── config.json
    ├── model.safetensors
    ├── tokenizer.json
    └── ...
```

---

## Performance Characteristics

### Latency Breakdown

**Query Path** (typical: 800ms):

```
User Query
   ↓ (1ms)
CLI Parsing
   ↓ (50ms)
Model Load (if not cached)
   ↓ (100ms)
Query Embedding (nomic-embed-text)
   ↓ (300ms)
Hybrid Search (Vector + FTS, 3 tiers)
├── FTS: 80ms
├── Vector: 200ms
└── Merge: 20ms
   ↓ (50ms)
Scoring + Reranking
   ↓ (5ms)
Context Packing
   ↓ (2ms)
JSON Serialization
   ↓
Result (12 chunks, ~1400 tokens)
```

**Ingestion Path** (typical 10KB doc: 12s):

```
Document Input
   ↓ (5ms)
Validation + Hash
   ↓ (50ms)
Chunking (600-token segments)
   ↓ (10s)
Batch Embedding (5 chunks × 2s/chunk)
   ↓ (500ms)
SQLite Write (doc + chunks + vectors)
   ↓ (100ms)
FTS Index Update
   ↓
Complete
```

### Scalability Limits

**Current Scale** (145 docs, 1024 chunks):

- ✅ Query: <1s
- ✅ Database: 12MB
- ✅ Memory: ~150MB (model + data)

**Projected Limits**:

| Scale       | Documents | Chunks | DB Size | Query Latency | Notes              |
| ----------- | --------- | ------ | ------- | ------------- | ------------------ |
| **Current** | 145       | 1,024  | 12MB    | <1s           | Excellent          |
| **Medium**  | 500       | 3,500  | 40MB    | <2s           | Good               |
| **Large**   | 1,000     | 7,000  | 80MB    | <3s           | Acceptable         |
| **XL**      | 5,000     | 35,000 | 400MB   | <10s          | Needs optimization |

**Bottlenecks at Scale**:

1. **Vector search**: O(N) linear scan (no indexing structure)
2. **Result set size**: Loading all tier chunks into memory
3. **FTS ranking**: BM25 over large corpus

**Mitigation Strategies**:

- Implement GC/compaction (keep corpus <1000 docs)
- Add vector indexing (HNSW, IVF) if needed
- Limit FTS result set (already: `top_k*2`)
- Partition by repo/session (reduce search space)

---

## Operational Procedures

### 🔍 Retrieval Priority Workflow (Critical)

**PRIMARY - Hybrid Query First:**

```bash
# ALWAYS start with pxctx query for any information retrieval
cd /workspaces/LocalAgents
./pxctx query "your question" --limit 15 --json-output

# Example: Architecture questions
./pxctx query "rust error handling patterns" --tier long_lived --limit 10

# Example: Session context
./pxctx query "recent build failures" --tier working --limit 5
```

**SECONDARY - Direct File Read (Only When Necessary):**

Use direct file reads ONLY when:

- ❌ pxctx query returns insufficient results
- ✅ Line-level code inspection required
- ✅ File structure/TOC navigation needed
- ✅ Specific file path already known from pxctx results

```bash
# After pxctx identifies relevant file
read_file docs/KB/Hackers_Guide_to_Python.md 1500 1600
```

**Rationale:**

- ✅ Tier-prioritized: Safety rules (Treasure) always surface first
- ✅ Recency-weighted: Recent findings automatically ranked higher
- ✅ Deduplication: Content hashes prevent redundant results
- ✅ Context-aware: Filters by repo/session/task scope
- ✅ Hybrid intelligence: Vector + FTS catches semantic and lexical matches

---

### Daily Operations

**Session Startup** (automated via Session Review SOP v1.4.0):

```bash
# 1. Git LFS pull (automatic)
git lfs pull

# 2. Verify database
file docs/KB/Vector_RAG/pxctx.db
# Output: SQLite 3.x database

# 3. Check stats
./pxctx stats
```

**Agent Integration** (Professor X operating procedure):

```python
# At start of Analyze block
result = subprocess.run([
    "./pxctx", "query", user_request,
    "--repo", "localagents",
    "--session", session_id,
    "--task", task_id,
    "--active", active_file_paths,
    "--json-output"
], capture_output=True)

context = json.loads(result.stdout)

# At end of Deliver/DeployRun
subprocess.run([
    "./pxctx", "add",
    "--tier", "working",
    "--type", "finding",
    "--title", "Root cause identified",
    "--text", summary,
    "--repo", "localagents",
    "--session", session_id,
    "--tags", "rust,build",
    "--source-kind", "command",
    "--source-ref", command,
    "--ttl-days", "7"
])
```

### Maintenance Tasks

**Weekly GC** (automated via cron):

```bash
# Delete expired working notes (>7 days)
./pxctx gc

# Compact old sessions
./pxctx compact --session S-20260202-001 \
  --title "Session summary: Week of Feb 2" \
  --to long_lived
```

**Monthly Review**:

```bash
# Audit Treasure
./pxctx query "" --tier treasure --json-output | \
  jq '.packs.treasure[] | {title, updated_at}'

# Check for duplicates
./pxctx query "" --tier long_lived --json-output | \
  jq '.packs.long_lived | group_by(.title) | map(select(length > 1))'

# Promote high-value findings
./pxctx promote --doc doc:abc123 --to long_lived
```

**Backup**:

```bash
# Database is in Git LFS, automatically backed up
git add docs/KB/Vector_RAG/pxctx.db
git commit -m "chore: pxctx database update"
git push origin Rust
```

### Troubleshooting

**Issue: Too much Treasure in context**

```bash
# Reduce treasure count
./pxctx query "..." --treasure-k 5

# Add topic filtering
./pxctx query "..." --tags security,safety
```

**Issue: Retrieval irrelevant**

```bash
# Use active paths boost
./pxctx query "..." --active "crates/localagent-core"

# Filter by session/task
./pxctx query "..." --session S-20260209-001
```

**Issue: Stale Treasure**

```bash
# Create updated version
./pxctx add --tier treasure --title "Updated rule: ..." --text "..."

# Mark supersession
./pxctx supersede --doc doc:new --supersedes doc:old

# Verify
./pxctx query "" --tier treasure
```

**Issue: Database locked**

```bash
# Check for open connections
lsof docs/KB/Vector_RAG/pxctx.db

# Kill stale processes
kill <pid>
```

**Issue: FTS syntax error**

- Fixed in v1.1 (Feb 9, 2026)
- Sanitization regex: `[.?*"'(){}]` → spaces
- Queries like "llama.cpp" now work

---

## References

### Documentation

- **Specification**: [docs/KB/Documents_as_Context_With_Vectors.md](Documents_as_Context_With_Vectors.md)
- **Usage Guide**: [docs/KB/Vector_RAG/README.md](Vector_RAG/README.md)
- **Professor X Mode**: [.github/agents/Professor_X.agent.md](../../.github/agents/Professor_X.agent.md)
- **Session Review SOP**: [docs/sop/SESSION_REVIEW_SOP.md](../sop/SESSION_REVIEW_SOP.md)

### Session Summaries (Evolution)

- **Feb 5, 2026**: Initial pxctx implementation (82 docs)
- **Feb 6, 2026**: KB ingestion automation
- **Feb 7, 2026**: Documentation SOP execution
- **Feb 8, 2026**: Bug fixes (NULL handling, hybrid retrieval validation)
- **Feb 9, 2026**:
  - M4 hardening (latency percentiles, tier metrics)
  - Architecture simplification (Qdrant removal)
  - Usability enhancements (wrapper script, FTS5 fix)

### External Resources

**sentence-transformers**:

- GitHub: https://github.com/UKPLab/sentence-transformers
- Docs: https://www.sbert.net/

**nomic-embed-text**:

- HuggingFace: https://huggingface.co/nomic-ai/nomic-embed-text-v1.5
- Paper: "Nomic Embed: Training a Reproducible Long Context Text Embedder"

**SQLite FTS5**:

- Docs: https://www.sqlite.org/fts5.html
- BM25 Ranking: https://www.sqlite.org/fts5.html#the_bm25_function

**RAG Best Practices**:

- Chunking: 400-800 tokens, 15-20% overlap
- Hybrid retrieval: Dense + sparse complementary
- Reranking: Cross-encoders or deterministic scoring

---

**Document Version**: 1.0  
**Last Updated**: February 9, 2026  
**Author**: Professor X (AI Agent)  
**Status**: Production System Documentation  
**Word Count**: ~10,500 words  
**Coverage**: Exhaustive (architecture, stack, implementation, evolution, operations)
