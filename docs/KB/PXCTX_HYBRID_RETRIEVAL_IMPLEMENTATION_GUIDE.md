# pxctx Hybrid Retrieval System Implementation Guide

**Complete Guide for Recreating the Professor X Context System in a New Repository**

Version: 1.0  
Date: February 25, 2026

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Database Schema](#database-schema)
4. [Core Modules](#core-modules)
5. [Hybrid Retrieval Algorithm](#hybrid-retrieval-algorithm)
6. [CLI Interface](#cli-interface)
7. [Shell Middleware](#shell-middleware)
8. [Integration Patterns](#integration-patterns)
9. [Implementation Steps](#implementation-steps)
10. [Testing Strategy](#testing-strategy)
11. [Performance Considerations](#performance-considerations)

---

## Architecture Overview

### System Purpose

The pxctx (Professor X Context) system is a **3-tier memory system with hybrid RAG retrieval** designed for IDE AI agents to maintain and query operational context across sessions.

### 3-Tier Memory Model

```
┌─────────────────────────────────────────────────────────────┐
│                         TREASURE                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Canonical truths • Always highest priority           │  │
│  │ • Pinned, never expire                               │  │
│  │ • Safety rules, invariants, architectural decisions  │  │
│  │ • Authoritative, requires CONFIRM to modify          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                         WORKING                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Ephemeral session/task memory                        │  │
│  │ • Current findings, plans, command results           │  │
│  │ • Strong recency weighting                           │  │
│  │ • TTL-based expiration (default: 7 days)             │  │
│  │ • Session/task scoped                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                       LONG-LIVED                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Durable knowledge base                               │  │
│  │ • KB documentation + distilled learnings            │  │
│  │ • Verified rank boost (documented > tested)          │  │
│  │ • Optional TTL (default: 180 days)                   │  │
│  │ • Repo scoped                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Retrieval Strategy

**Hybrid Search**: Vector similarity (cosine) + Full-text search (SQLite FTS5)

**Deterministic Reranking**:
```
score = tier_boost + 
        2.0 × vector_similarity + 
        1.0 × fts_score + 
        recency_boost × recency_score +
        1.0 × importance +
        verified_bonus +
        path_match_bonus +
        pin_bonus
```

Where:
- `tier_boost`: Treasure=10, Working=5, Long-lived=2
- `vector_similarity`: 0..1 (cosine similarity, normalized embeddings)
- `fts_score`: 0..1 (normalized BM25 rank)
- `recency_score`: 1.0 / (1.0 + age_days/30.0)
- `importance`: 0..1 (user-defined)
- `verified_bonus`: documented=0.3, tested=0.2, observed=0.1, asserted=0.05
- `path_match_bonus`: 0.2 if source matches active paths
- `pin_bonus`: 0.5 if pinned

**Context Packing** (tier-ordered, token-budgeted):
1. Pack Treasure first (reserve ≥25% of token budget)
2. Merge Working + Long-lived, sort by score descending
3. Pack remaining budget, deduplicate chunks
4. Limit to `final_n` items and `max_tokens` budget

### Hard Rules

1. **Treasure Dominance**: Treasure always wins conflicts with Working/Long-lived
2. **Treasure Governance**: Creating/modifying Treasure requires explicit user CONFIRM
3. **No Direct File Reads**: Agents must query pxctx FIRST, direct file reads are SECONDARY fallback
4. **Session Persistence**: Session state persists in `.pxctx-session` (gitignored)
5. **Idempotent Updates**: Documents identified by `(source_kind, source_ref)`, content-hash checked

---

## Technology Stack

### Required Dependencies

**Python 3.9+**

```txt
# Core
click>=8.0
numpy>=1.21
sentence-transformers>=2.2.0

# Database (stdlib)
# sqlite3 (built-in)

# Optional: Progress bars
tqdm>=4.60
```

### File: `requirements.txt`

```txt
click==8.1.7
numpy==1.24.3
sentence-transformers==2.3.1
tqdm==4.66.1
```

### Embedding Model

**nomic-ai/nomic-embed-text-v1.5**
- Dimension: 768
- License: Apache 2.0
- Download: ~547 MB
- Local path: `models/nomic-embed-text/` (optional, will auto-download from HuggingFace)

### Directory Structure

```
your-repo/
├── docs/
│   └── KB/
│       └── Vector_RAG/           # pxctx implementation root
│           ├── __init__.py
│           ├── __main__.py
│           ├── pxctx.py          # CLI entry point
│           ├── db.py             # Database operations
│           ├── query.py          # Hybrid retrieval
│           ├── embeddings.py     # Embedding model wrapper
│           ├── chunking.py       # Text chunking
│           ├── schema.sql        # SQLite schema
│           ├── requirements.txt
│           ├── pxctx.db          # Created on first use
│           └── README.md
├── scripts/
│   └── pxctx-auto.sh             # Shell middleware
├── pxctx                         # Bash wrapper script
└── .pxctx-session                # Session state (gitignored)
```

---

## Database Schema

### File: `docs/KB/Vector_RAG/schema.sql`

```sql
-- Professor X Context System - 3-Tier Memory (Working / Long-lived / Treasure)
-- Schema Version: 1.0

-- ============================================================================
-- DOCS: Core document/memory storage
-- ============================================================================

CREATE TABLE IF NOT EXISTS docs (
    doc_id TEXT PRIMARY KEY,
    tier TEXT NOT NULL CHECK(tier IN ('working', 'long_lived', 'treasure')),
    
    -- Scope identifiers
    repo_id TEXT,
    session_id TEXT,
    task_id TEXT,
    
    -- Content
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    
    -- Classification
    type TEXT NOT NULL CHECK(type IN (
        'decision', 'constraint', 'finding', 'plan_step', 
        'command_summary', 'kb_doc', 'distilled_note', 
        'security_rule', 'architecture', 'invariant'
    )),
    
    -- Metadata
    tags TEXT, -- JSON array
    sources TEXT, -- JSON array of {kind, ref}
    importance REAL DEFAULT 0.5 CHECK(importance >= 0.0 AND importance <= 1.0),
    verified TEXT CHECK(verified IN ('asserted', 'observed', 'tested', 'documented')),
    
    -- Lifecycle
    pin INTEGER DEFAULT 0,
    never_expire INTEGER DEFAULT 0,
    ttl_days INTEGER,
    supersedes TEXT, -- JSON array of doc_ids
    
    -- Content hash for idempotent updates (SHA256)
    content_hash TEXT,
    
    -- Timestamps
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'professorx',
    
    -- Redaction flag
    redacted INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_docs_tier ON docs(tier);
CREATE INDEX IF NOT EXISTS idx_docs_repo ON docs(repo_id);
CREATE INDEX IF NOT EXISTS idx_docs_session ON docs(session_id);
CREATE INDEX IF NOT EXISTS idx_docs_task ON docs(task_id);
CREATE INDEX IF NOT EXISTS idx_docs_type ON docs(type);
CREATE INDEX IF NOT EXISTS idx_docs_created ON docs(created_at);
CREATE INDEX IF NOT EXISTS idx_docs_pin ON docs(pin);

-- Index for fast source-ref lookup (idempotent updates)
CREATE INDEX IF NOT EXISTS idx_docs_source ON docs(
    json_extract(sources, '$[0].kind'),
    json_extract(sources, '$[0].ref')
) WHERE sources IS NOT NULL;

-- ============================================================================
-- DOC_CHUNKS: Chunked text for embedding
-- ============================================================================

CREATE TABLE IF NOT EXISTS doc_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INTEGER,
    
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (doc_id) REFERENCES docs(doc_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON doc_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_index ON doc_chunks(doc_id, chunk_index);

-- ============================================================================
-- DOC_CHUNKS_FTS: Full-text search index
-- ============================================================================

CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    chunk_text,
    content=doc_chunks,
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS doc_chunks_fts_insert AFTER INSERT ON doc_chunks BEGIN
    INSERT INTO doc_chunks_fts(rowid, chunk_id, chunk_text)
    VALUES (new.rowid, new.chunk_id, new.chunk_text);
END;

CREATE TRIGGER IF NOT EXISTS doc_chunks_fts_delete AFTER DELETE ON doc_chunks BEGIN
    DELETE FROM doc_chunks_fts WHERE rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS doc_chunks_fts_update AFTER UPDATE ON doc_chunks BEGIN
    DELETE FROM doc_chunks_fts WHERE rowid = old.rowid;
    INSERT INTO doc_chunks_fts(rowid, chunk_id, chunk_text)
    VALUES (new.rowid, new.chunk_id, new.chunk_text);
END;

-- ============================================================================
-- VECTORS: Embedding storage
-- ============================================================================

CREATE TABLE IF NOT EXISTS vectors (
    chunk_id TEXT PRIMARY KEY,
    embedding BLOB NOT NULL, -- Serialized numpy array (packed floats)
    embedding_model TEXT NOT NULL,
    embedding_dim INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (chunk_id) REFERENCES doc_chunks(chunk_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_vectors_chunk ON vectors(chunk_id);

-- ============================================================================
-- SYSTEM_METADATA: Configuration and stats
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Initial metadata
INSERT OR IGNORE INTO system_metadata (key, value) VALUES
    ('schema_version', '1.0'),
    ('created_at', datetime('now')),
    ('embedding_model', 'nomic-embed-text'),
    ('embedding_dim', '768'),
    ('total_docs', '0'),
    ('total_chunks', '0');

-- ============================================================================
-- VIEWS: Convenient access patterns
-- ============================================================================

-- Treasure documents (always highest priority)
CREATE VIEW IF NOT EXISTS v_treasure AS
SELECT 
    d.*,
    COUNT(c.chunk_id) as chunk_count
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
WHERE d.tier = 'treasure'
GROUP BY d.doc_id
ORDER BY d.importance DESC, d.created_at DESC;

-- Working memory (recency-weighted)
CREATE VIEW IF NOT EXISTS v_working AS
SELECT 
    d.*,
    COUNT(c.chunk_id) as chunk_count,
    julianday('now') - julianday(d.created_at) as age_days
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
WHERE d.tier = 'working'
GROUP BY d.doc_id
ORDER BY d.created_at DESC;

-- Long-lived knowledge
CREATE VIEW IF NOT EXISTS v_long_lived AS
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

-- ============================================================================
-- CLEANUP TRIGGERS
-- ============================================================================

-- Update system_metadata counts on doc changes
CREATE TRIGGER IF NOT EXISTS update_doc_count_insert AFTER INSERT ON docs BEGIN
    UPDATE system_metadata 
    SET value = (SELECT COUNT(*) FROM docs), 
        updated_at = CURRENT_TIMESTAMP
    WHERE key = 'total_docs';
END;

CREATE TRIGGER IF NOT EXISTS update_doc_count_delete AFTER DELETE ON docs BEGIN
    UPDATE system_metadata 
    SET value = (SELECT COUNT(*) FROM docs),
        updated_at = CURRENT_TIMESTAMP
    WHERE key = 'total_docs';
END;

CREATE TRIGGER IF NOT EXISTS update_chunk_count_insert AFTER INSERT ON doc_chunks BEGIN
    UPDATE system_metadata 
    SET value = (SELECT COUNT(*) FROM doc_chunks),
        updated_at = CURRENT_TIMESTAMP
    WHERE key = 'total_chunks';
END;

CREATE TRIGGER IF NOT EXISTS update_chunk_count_delete AFTER DELETE ON doc_chunks BEGIN
    UPDATE system_metadata 
    SET value = (SELECT COUNT(*) FROM doc_chunks),
        updated_at = CURRENT_TIMESTAMP
    WHERE key = 'total_chunks';
END;
```

---

## Core Modules

### 1. Database Module (`db.py`)

**Purpose**: SQLite connection management, schema initialization, CRUD operations

**Key Components**:

```python
class Database:
    def __init__(self, db_path: Path = DB_PATH)
    
    # Document operations
    def add_doc(tier, title, content, type_, ...) -> str
    def get_doc(doc_id: str) -> Optional[Dict]
    def update_doc_content(doc_id, new_content, new_content_hash)
    def delete_doc(doc_id: str)
    def find_doc_by_source(source_kind, source_ref) -> Optional[Tuple[str, str]]
    
    # Chunk operations
    def add_chunk(doc_id, chunk_index, chunk_text, token_count) -> str
    def get_chunks(doc_id: str) -> List[Dict]
    
    # Vector operations
    def add_vector(chunk_id, embedding: bytes, model, dim)
    def get_vector(chunk_id: str) -> Optional[bytes]
    
    # Query operations
    def get_docs_by_tier(tier, repo_id, session_id, task_id, tags, limit) -> List[Dict]
    def fts_search(query_text, tier, limit) -> List[Dict]
    
    # Lifecycle operations
    def promote_to_tier(doc_id, to_tier, pin, never_expire) -> bool
    def supersede_doc(doc_id, old_ids: List[str]) -> bool
    def gc_expired() -> int
    
    # Stats
    def get_stats() -> Dict
    
    # Utilities
    def compute_content_hash(content: str) -> str
```

**Implementation Notes**:
- Use `contextlib.contextmanager` for connection handling
- Enable WAL mode: `PRAGMA journal_mode=WAL`
- Row factory: `sqlite3.Row` for dict-like access
- Content hash: SHA256 for idempotent updates
- Cascading deletes via FOREIGN KEY constraints

### 2. Embeddings Module (`embeddings.py`)

**Purpose**: Embedding model wrapper, vector serialization

**Key Components**:

```python
def get_model() -> SentenceTransformer
    # Lazy load nomic-embed-text
    # Check local path first: repo_root/models/nomic-embed-text/
    # Fallback to HuggingFace download
    
def encode(texts: List[str], show_progress=False) -> np.ndarray
    # Returns (len(texts), 768) normalized embeddings
    
def encode_single(text: str) -> np.ndarray
    # Single text convenience wrapper
    
def serialize_embedding(embedding: np.ndarray) -> bytes
    # Pack as floats: struct.pack(f"{len}f", *values)
    
def deserialize_embedding(data: bytes) -> np.ndarray
    # Unpack floats: struct.unpack(f"{count}f", data)
    
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float
    # Assumes normalized: np.dot(a, b)
    
def vector_search(query_emb, candidates, top_k) -> List[Tuple[str, float]]
    # Returns [(chunk_id, similarity_score), ...]
```

**Model Configuration**:
- Model: `nomic-ai/nomic-embed-text-v1.5`
- Dimension: 768
- Normalization: True (for cosine similarity via dot product)
- Trust remote code: True

### 3. Chunking Module (`chunking.py`)

**Purpose**: Text segmentation with overlap, markdown-aware chunking

**Key Components**:

```python
def estimate_tokens(text: str) -> int
    # Rough: len(text.split()) * 1.3
    
def chunk_text(
    text: str,
    target_tokens: int = 600,
    overlap_tokens: int = 100,
    min_chunk_tokens: int = 200
) -> List[str]
    # Split on paragraphs (\n\n)
    # Overlap: keep last paragraph in new chunk
    # Handle large paragraphs: split by sentences
    
def split_sentences(text: str) -> List[str]
    # Regex: r'([.!?]+\s+)(?=[A-Z])'
    
def chunk_markdown(
    text: str,
    target_tokens: int = 600,
    overlap_tokens: int = 100
) -> List[Tuple[str, str]]
    # Returns [(heading_path, chunk_text), ...]
    # Heading path: "# Top > ## Sub > ### Subsub"
    # Preserves context hierarchy
```

**Chunking Strategy**:
- Target: 600 tokens (~450 words)
- Overlap: 100 tokens (~75 words)
- Minimum: 200 tokens (merge small tail chunks)
- Paragraph boundaries preferred
- Sentence boundaries for forced splits

### 4. Query Module (`query.py`)

**Purpose**: Hybrid retrieval, tier-ordered packing

**Key Components**:

```python
class QueryResult:
    query_id: str
    packs: Dict[str, List[Dict]]  # treasure, working, long_lived
    final: List[Dict]              # Token-budgeted pack
    stats: Dict
    
def query(
    db: Database,
    q: str,
    repo_id, session_id, task_id,
    active_paths: List[str],
    treasure_k=12, working_k=18, long_lived_k=18,
    final_n=12, max_tokens=1400,
    tags_any: List[str]
) -> QueryResult

def _retrieve_tier(
    db, tier, query_text, query_emb,
    repo_id, session_id, task_id, tags_any, top_k,
    active_paths, recency_boost=0.0, verified_boost=False
) -> List[Dict]
```

**Retrieval Algorithm** (see below for details)

### 5. CLI Entry Point (`pxctx.py`)

**Purpose**: Click-based CLI tool

**Commands**:
- `add` - Add document with chunking + embedding
- `query` - Hybrid retrieval with tier packing
- `promote` - Move document to different tier
- `supersede` - Mark Treasure versioning
- `gc` - Garbage collect expired docs
- `compact` - Distill working notes into long-lived
- `ingest` - Bulk ingest KB markdown files
- `stats` - System statistics

---

## Hybrid Retrieval Algorithm

### High-Level Flow

```
User Query ──> Encode Query
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   Vector Search          FTS Search
   (cosine sim)           (BM25)
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
            Merge + Deduplicate
                    │
                    ▼
          Deterministic Reranking
          (tier + vector + fts + 
           recency + importance +
           verified + path + pin)
                    │
            ┌───────┴───────┐
            │               │
            ▼               ▼
        Treasure       Working + Long-lived
        (pack first)   (sorted by score)
            │               │
            └───────┬───────┘
                    ▼
          Token-Budgeted Packing
          (Treasure ≥25% budget)
                    │
                    ▼
              Final Pack
          (max final_n items)
```

### Detailed Algorithm

**Step 1: Per-Tier Retrieval**

For each tier (Treasure, Working, Long-lived):

```python
def _retrieve_tier(db, tier, query_text, query_emb, ...):
    # 1. FTS search (SQLite FTS5)
    fts_hits = db.fts_search(query_text, tier=tier, limit=top_k * 2)
    # Returns: [(chunk_id, rank), ...]  # rank is BM25 score
    
    # 2. Get candidate documents from tier
    tier_docs = db.get_docs_by_tier(
        tier=tier, repo_id=repo_id, session_id=session_id,
        task_id=task_id, tags=tags_any, limit=top_k * 3
    )
    
    # 3. Collect chunks with vectors
    candidates = []
    for doc in tier_docs:
        chunks = db.get_chunks(doc["doc_id"])
        for chunk in chunks:
            vec_data = db.get_vector(chunk["chunk_id"])
            if vec_data:
                candidates.append({
                    "chunk_id": chunk["chunk_id"],
                    "doc_id": doc["doc_id"],
                    "chunk_text": chunk["chunk_text"],
                    "embedding": deserialize_embedding(vec_data),
                    "doc": doc
                })
    
    # 4. Vector search (cosine similarity)
    vector_results = vector_search(
        query_emb,
        [(c["chunk_id"], c["embedding"]) for c in candidates],
        top_k=top_k * 2
    )
    # Returns: [(chunk_id, similarity_score), ...]
    
    # 5. Normalize FTS scores (BM25 ranks are negative)
    vector_scores = {chunk_id: score for chunk_id, score in vector_results}
    fts_scores = {hit["chunk_id"]: abs(float(hit["rank"])) for hit in fts_hits}
    
    if fts_scores:
        max_fts = max(fts_scores.values())
        fts_scores = {k: v / max_fts for k, v in fts_scores.items()}
    
    # 6. Compute combined scores
    scored_candidates = []
    
    for cand in candidates:
        chunk_id = cand["chunk_id"]
        doc = cand["doc"]
        
        # Base scores
        vec_score = vector_scores.get(chunk_id, 0.0)
        fts_score = fts_scores.get(chunk_id, 0.0)
        
        # Recency score (0..1, newer = higher)
        if recency_boost > 0:
            age_days = (datetime.now() - datetime.fromisoformat(doc["created_at"])).days
            recency_score = 1.0 / (1.0 + age_days / 30.0)  # ~30-day half-life
        else:
            recency_score = 0.0
        
        # Verified boost (long-lived KB)
        verified_score = 0.0
        if verified_boost and doc.get("verified"):
            verified_map = {
                "documented": 0.3,
                "tested": 0.2,
                "observed": 0.1,
                "asserted": 0.05
            }
            verified_score = verified_map.get(doc["verified"], 0.0)
        
        # Importance
        importance = doc.get("importance", 0.5)
        
        # Active paths boost
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
        
        # Tier boost (treasure >> working >> long-lived)
        tier_boost = {
            "treasure": 10.0,
            "working": 5.0,
            "long_lived": 2.0
        }.get(tier, 0.0)
        
        # COMBINED SCORE
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
        
        scored_candidates.append({
            "chunk_id": chunk_id,
            "doc_id": cand["doc_id"],
            "tier": tier,
            "score": score,
            "title": doc["title"],
            "snippet": cand["chunk_text"][:500],
            "tags": json.loads(doc.get("tags") or "[]"),
            "sources": json.loads(doc.get("sources") or "[]"),
            "updated_at": doc["updated_at"]
        })
    
    # 7. Sort by score descending
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    return scored_candidates[:top_k]
```

**Step 2: Tier-Ordered Context Packing**

```python
def query(db, q, treasure_k=12, working_k=18, long_lived_k=18, 
          final_n=12, max_tokens=1400, ...):
    
    # Encode query
    query_emb = encode_single(q)
    
    # Retrieve from each tier
    treasure_hits = _retrieve_tier(
        db, "treasure", q, query_emb, 
        recency_boost=0.0,  # Treasure doesn't decay
        top_k=treasure_k
    )
    
    working_hits = _retrieve_tier(
        db, "working", q, query_emb,
        recency_boost=0.3,  # Strong recency
        top_k=working_k,
        session_id=session_id, task_id=task_id
    )
    
    long_lived_hits = _retrieve_tier(
        db, "long_lived", q, query_emb,
        recency_boost=0.1,  # Mild recency
        verified_boost=True,
        top_k=long_lived_k
    )
    
    # Pack Treasure first (reserve ≥25% budget)
    final_pack = []
    seen_chunks = set()
    total_tokens = 0
    min_treasure_tokens = int(max_tokens * 0.25)
    
    for hit in treasure_hits:
        chunk_id = hit["chunk_id"]
        if chunk_id in seen_chunks:
            continue
        
        chunk_tokens = estimate_tokens(hit["snippet"])
        if total_tokens + chunk_tokens > min_treasure_tokens and final_pack:
            break  # Reserve budget for working/long-lived
        
        final_pack.append({
            "ref": f"memory://{hit['doc_id']}#{chunk_id}",
            "tier": "treasure",
            "title": hit["title"],
            "text": hit["snippet"],
            "score": hit["score"],
            "tags": hit.get("tags", [])
        })
        
        seen_chunks.add(chunk_id)
        total_tokens += chunk_tokens
    
    # Merge working + long-lived, sort by score
    remaining_hits = working_hits + long_lived_hits
    remaining_hits.sort(key=lambda x: x["score"], reverse=True)
    
    # Pack remaining budget
    for hit in remaining_hits:
        chunk_id = hit["chunk_id"]
        if chunk_id in seen_chunks:
            continue  # Deduplicate
        
        chunk_tokens = estimate_tokens(hit["snippet"])
        if total_tokens + chunk_tokens > max_tokens:
            break  # Budget exhausted
        
        if len(final_pack) >= final_n:
            break  # Count limit
        
        final_pack.append({
            "ref": f"memory://{hit['doc_id']}#{chunk_id}",
            "tier": hit["tier"],
            "title": hit["title"],
            "text": hit["snippet"],
            "score": hit["score"],
            "tags": hit.get("tags", [])
        })
        
        seen_chunks.add(chunk_id)
        total_tokens += chunk_tokens
    
    return QueryResult(
        packs={
            "treasure": treasure_hits,
            "working": working_hits,
            "long_lived": long_lived_hits
        },
        final=final_pack,
        stats={...}
    )
```

**Score Weighting Rationale**:
- **Tier boost (10/5/2)**: Ensures Treasure dominates, Working outranks Long-lived
- **Vector 2.0×**: Semantic similarity is primary signal
- **FTS 1.0×**: Exact matches important but secondary
- **Recency**: Working=0.3 (strong), Long-lived=0.1 (mild), Treasure=0 (timeless)
- **Importance 1.0×**: User-controlled boost
- **Verified**: Rewards KB documentation quality
- **Path/Pin**: Small boosts for active context and treasure pins

---

## CLI Interface

### Commands Reference

#### `add` — Add Document

```bash
pxctx add \
  --tier {working|long_lived|treasure} \
  --type {decision|constraint|finding|plan_step|command_summary|kb_doc|distilled_note|security_rule|architecture|invariant} \
  --title "Document title" \
  --text "Content text" \
  [--file PATH]              # Alt to --text, read from file
  [--repo REPO_ID] \
  [--session SESSION_ID] \
  [--task TASK_ID] \
  [--tags "tag1,tag2"] \
  [--source-kind file|command|...] \
  [--source-ref "path/to/file.md"] \
  [--importance 0.0-1.0]     # Default: 0.5
  [--verified {asserted|observed|tested|documented}] \
  [--pin]                    # Pin document
  [--never-expire]           # Never expire (Treasure)
  [--ttl-days N]             # Expire in N days
  [--no-chunk]               # Store as single chunk
  [--on-duplicate {update|skip|error}]  # Idempotent re-ingestion
```

**Idempotent Updates**:
- Documents identified by `(source_kind, source_ref)` identity key
- Content changes detected via SHA256 hash
- `--on-duplicate update`: Skip if unchanged, re-embed if changed
- `--on-duplicate skip`: Always skip if exists
- `--on-duplicate error`: Fail if exists

#### `query` — Hybrid Retrieval

```bash
pxctx query "your search query" \
  [--repo REPO_ID] \
  [--session SESSION_ID] \
  [--task TASK_ID] \
  [--active "path1,path2"]   # Boost matching sources
  [--treasure-k 12]          # Max treasure results
  [--working-k 18]           # Max working results
  [--long-lived-k 18]        # Max long-lived results
  [--final-n 12]             # Max final pack items
  [--max-tokens 1400]        # Token budget
  [--tags "tag1,tag2"]       # Filter by tags (OR)
  [--json-output]            # Full JSON output
```

**Output (Human-Friendly)**:
```
Querying: how does the build work?

Query Results
Query ID: Q-20260225120000

Treasure: 2 hits
Working: 5 hits
Long-lived: 8 hits
Final packed: 12 chunks

Stats: {"vector_calls": 3, "fts_calls": 3, "deduped": 3, "returned": 12}

Final Context Pack

1. [TREASURE] Never execute destructive actions without CONFIRM
   Score: 10.850 | memory://doc:abc123#chunk:xyz789
   Rule: Never execute destructive commands...

2. [WORKING] Build error: missing feature flag
   Score: 7.420 | memory://doc:def456#chunk:uvw123
   cargo test failed due to...
```

**Output (JSON)**:
```json
{
  "query_id": "Q-20260225120000",
  "packs": {
    "treasure": [...],
    "working": [...],
    "long_lived": [...]
  },
  "final": [
    {
      "ref": "memory://doc:abc123#chunk:xyz789",
      "tier": "treasure",
      "title": "Never execute destructive actions",
      "text": "...",
      "score": 10.85,
      "tags": ["safety", "tooling"]
    }
  ],
  "stats": {
    "vector_calls": 3,
    "fts_calls": 3,
    "deduped": 3,
    "returned": 12
  }
}
```

#### `promote` — Change Tier

```bash
pxctx promote \
  --doc doc:abc123 \
  --to {working|long_lived|treasure} \
  [--pin] \
  [--never-expire]
```

**Treasure Governance**: Demoting Treasure requires confirmation.

#### `supersede` — Treasure Versioning

```bash
pxctx supersede \
  --doc doc:new123 \
  --supersedes doc:old111,doc:old222
```

#### `gc` — Garbage Collection

```bash
pxctx gc [--dry-run]
```

Deletes docs where:
- `never_expire = 0` AND
- `ttl_days` is set AND
- `created_at + ttl_days < now`

#### `compact` — Distill Session

```bash
pxctx compact \
  --session SESSION_ID \
  --title "Session summary: Task XYZ" \
  [--to {working|long_lived}]  # Default: long_lived
```

Merges all working docs from session into single distilled note.

#### `ingest` — Bulk KB Import

```bash
pxctx ingest PATH \
  [--tier long_lived] \
  [--type kb_doc] \
  [--repo REPO_ID] \
  [--tags "kb,rag"] \
  [--recursive] \
  [--pattern "*.md"]
```

#### `stats` — System Stats

```bash
pxctx stats
```

Output:
```
Professor X Context System Stats

Schema version: 1.0
Created: 2026-02-05 12:00:00

Total documents: 42
Total chunks: 156

Tier Breakdown:
  TREASURE: 5 docs (5 pinned)
  WORKING: 18 docs (0 pinned)
  LONG-LIVED: 19 docs (0 pinned)
```

---

## Shell Middleware

### Purpose

Provide high-level convenience functions for AI agents:
- Session bootstrap with stable IDs
- Simplified recording (`pxctx-record` vs raw `pxctx add`)
- Auto-context retrieval
- Session verification and wrap-up

### File: `scripts/pxctx-auto.sh`

```bash
#!/usr/bin/env bash
# pxctx-auto.sh — Automatic Context Middleware for AI Agents

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PXCTX_CLI="${REPO_ROOT}/pxctx"
SESSION_FILE="${REPO_ROOT}/.pxctx-session"
REPO_ID="your-repo-name"

# ========================================
# CORE FUNCTIONS
# ========================================

# pxctx-boot — Start session
# Usage: pxctx-boot "Fix chat pipeline"
pxctx-boot() {
    local task_summary="${1:?Usage: pxctx-boot \"<task description>\"}"
    local date_prefix="$(date +%Y%m%d)"
    local sanitized="$(echo "$task_summary" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 ]//g' | tr ' ' '-' | cut -c1-32)"
    local session_id="session:${date_prefix}-${sanitized}"
    local task_id="task:${date_prefix}-${sanitized}"
    
    # Persist session state
    cat > "$SESSION_FILE" <<EOF
export PXCTX_SESSION_ID="${session_id}"
export PXCTX_TASK_ID="${task_id}"
export PXCTX_REPO_ID="${REPO_ID}"
export PXCTX_TASK_SUMMARY="${task_summary}"
export PXCTX_BOOT_TIME="$(date -Iseconds)"
export PXCTX_RECORD_COUNT=0
EOF
    source "$SESSION_FILE"
    
    # Query initial context
    "${PXCTX_CLI}" query "$task_summary" \
        --repo "$REPO_ID" \
        --session "$session_id" \
        --final-n 8 \
        --max-tokens 1200
    
    # Record boot
    "${PXCTX_CLI}" add \
        --tier working \
        --type plan_step \
        --title "Session start: ${task_summary}" \
        --text "Session ${session_id} started. Task: ${task_summary}." \
        --repo "$REPO_ID" \
        --session "$session_id" \
        --task "$task_id" \
        --tags "session,boot" \
        --source-kind "auto" \
        --source-ref "pxctx-auto:boot:${session_id}" \
        --ttl-days 7 \
        --on-duplicate skip >/dev/null 2>&1
}

# pxctx-context — Query context
# Usage: pxctx-context "routing engine design"
pxctx-context() {
    source "$SESSION_FILE"
    local query_text="${1:-${PXCTX_TASK_SUMMARY}}"
    shift 2>/dev/null || true
    
    "${PXCTX_CLI}" query "$query_text" \
        --repo "$PXCTX_REPO_ID" \
        --session "$PXCTX_SESSION_ID" \
        --final-n 10 \
        --max-tokens 1400 \
        "$@"
}

# pxctx-record — Simplified add
# Usage: pxctx-record decision "Use petgraph for DAG"
pxctx-record() {
    source "$SESSION_FILE"
    
    local type_="${1:?Usage: pxctx-record <type> \"<text>\"}"
    local text="${2:?Usage: pxctx-record <type> \"<text>\"}"
    shift 2
    
    local title="${text:0:60}"
    local tier="working"
    local extra_args=()
    local tags_set=false
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --tier)       tier="$2"; shift 2 ;;
            --tags)       extra_args+=(--tags "$2"); tags_set=true; shift 2 ;;
            --importance) extra_args+=(--importance "$2"); shift 2 ;;
            --source-kind) extra_args+=(--source-kind "$2"); shift 2 ;;
            --source-ref)  extra_args+=(--source-ref "$2"); shift 2 ;;
            *)            shift ;;
        esac
    done
    
    if [[ "$tags_set" == false ]]; then
        extra_args+=(--tags "${type_},auto")
    fi
    
    "${PXCTX_CLI}" add \
        --tier "$tier" \
        --type "$type_" \
        --title "$title" \
        --text "$text" \
        --repo "$PXCTX_REPO_ID" \
        --session "$PXCTX_SESSION_ID" \
        --task "$PXCTX_TASK_ID" \
        --ttl-days 7 \
        "${extra_args[@]}"
    
    # Increment count
    export PXCTX_RECORD_COUNT=$((${PXCTX_RECORD_COUNT:-0} + 1))
    sed -i "s/PXCTX_RECORD_COUNT=.*/PXCTX_RECORD_COUNT=${PXCTX_RECORD_COUNT}/" "$SESSION_FILE"
}

# pxctx-checkpoint — Progress snapshot
# Usage: pxctx-checkpoint "Completed Phase 1: CRUD + schema"
pxctx-checkpoint() {
    source "$SESSION_FILE"
    local summary="${1:?Usage: pxctx-checkpoint \"<summary>\"}"
    
    local checkpoint_text="CHECKPOINT [$(date '+%H:%M')] Session: ${PXCTX_SESSION_ID}
Task: ${PXCTX_TASK_SUMMARY}
Records: ${PXCTX_RECORD_COUNT:-0}

Progress: ${summary}"
    
    "${PXCTX_CLI}" add \
        --tier working \
        --type plan_step \
        --title "Checkpoint: ${summary:0:50}" \
        --text "$checkpoint_text" \
        --repo "$PXCTX_REPO_ID" \
        --session "$PXCTX_SESSION_ID" \
        --task "$PXCTX_TASK_ID" \
        --tags "checkpoint,progress" \
        --importance 0.7 \
        --ttl-days 14 >/dev/null 2>&1
}

# pxctx-verify — Check session has records
pxctx-verify() {
    source "$SESSION_FILE"
    local count="${PXCTX_RECORD_COUNT:-0}"
    
    if [[ "$count" -eq 0 ]]; then
        echo "⚠ No records stored this session!"
        return 1
    else
        echo "✓ ${count} record(s) stored"
        
        "${PXCTX_CLI}" query "${PXCTX_SESSION_ID}" \
            --repo "$PXCTX_REPO_ID" \
            --session "$PXCTX_SESSION_ID" \
            --final-n 5
    fi
}

# pxctx-wrap-up — End session
pxctx-wrap-up() {
    source "$SESSION_FILE"
    
    pxctx-verify || true
    
    "${PXCTX_CLI}" gc 2>&1 || true
    
    "${PXCTX_CLI}" stats
}

# Auto-resume on source
if [[ -f "$SESSION_FILE" ]]; then
    source "$SESSION_FILE"
fi
```

### File: `pxctx` (Bash Wrapper)

```bash
#!/bin/bash
# pxctx - Convenience wrapper for Professor X Context System

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Activate venv if present
if [[ -z "${VIRTUAL_ENV:-}" ]] && [[ -f "${SCRIPT_DIR}/.venv/bin/activate" ]]; then
    source "${SCRIPT_DIR}/.venv/bin/activate"
fi

cd "$SCRIPT_DIR" && PYTHONPATH="$PWD/docs/KB" python -m Vector_RAG.pxctx "$@"
```

Make executable: `chmod +x pxctx`

---

## Integration Patterns

### Agent Workflow (Python Example)

```python
import subprocess
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent
PXCTX_CLI = REPO_ROOT / "pxctx"

def pxctx_query(query: str, **kwargs) -> dict:
    """Query pxctx, return JSON."""
    cmd = [str(PXCTX_CLI), "query", query, "--json-output"]
    
    for k, v in kwargs.items():
        if isinstance(v, bool):
            if v:
                cmd.append(f"--{k.replace('_', '-')}")
        else:
            cmd.extend([f"--{k.replace('_', '-')}", str(v)])
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)

def pxctx_add(tier: str, type_: str, title: str, text: str, **kwargs):
    """Add document to pxctx."""
    cmd = [
        str(PXCTX_CLI), "add",
        "--tier", tier,
        "--type", type_,
        "--title", title,
        "--text", text
    ]
    
    for k, v in kwargs.items():
        if isinstance(v, bool):
            if v:
                cmd.append(f"--{k.replace('_', '-')}")
        elif isinstance(v, list):
            cmd.extend([f"--{k.replace('_', '-')}", ",".join(v)])
        else:
            cmd.extend([f"--{k.replace('_', '-')}", str(v)])
    
    subprocess.run(cmd, check=True)

# === USAGE IN AGENT ===

def handle_user_request(user_request: str, repo_id: str, session_id: str):
    # 1. Query context FIRST
    context = pxctx_query(
        user_request,
        repo=repo_id,
        session=session_id,
        final_n=12,
        max_tokens=1400
    )
    
    # 2. Summarize retrieved context
    print(f"Retrieved {len(context['final'])} context items:")
    print(f"- Treasure: {len(context['packs']['treasure'])} rules")
    print(f"- Working: {len(context['packs']['working'])} recent")
    print(f"- Long-lived: {len(context['packs']['long_lived'])} KB")
    
    # 3. Use context in reasoning
    for item in context["final"]:
        # Check if treasure rules apply
        if item["tier"] == "treasure":
            print(f"⚠ Treasure rule: {item['title']}")
    
    # 4. Do work...
    # ...
    
    # 5. Record findings
    pxctx_add(
        tier="working",
        type_="finding",
        title="Root cause: Missing feature flag",
        text="Build failed because feature flag 'xyz' is missing...",
        repo=repo_id,
        session=session_id,
        tags=["rust", "build"],
        source_kind="command",
        source_ref="cargo test",
        ttl_days=7
    )
```

### Agent Workflow (Shell Example)

```bash
#!/bin/bash
# agent-task.sh — Example agent task with pxctx

source scripts/pxctx-auto.sh

# 1. Bootstrap session
pxctx-boot "Fix Rust build error"

# 2. Query context
pxctx-context "cargo build error" --json-output > /tmp/context.json

# 3. Do work
cargo test 2>&1 | tee /tmp/test-output.txt

# 4. Record findings
pxctx-record finding "cargo test failed: missing feature flag 'xyz' in localagent-core" \
    --source-kind command \
    --source-ref "cargo test"

# 5. Record command summary
pxctx-record command_summary "$(cat /tmp/test-output.txt)" \
    --tags "rust,test"

# 6. Checkpoint
pxctx-checkpoint "Identified missing feature flag; added to Cargo.toml"

# 7. Wrap-up
pxctx-wrap-up
```

---

## Implementation Steps

### Phase 1: Core Infrastructure (Days 1-2)

**Step 1.1**: Set up directory structure

```bash
mkdir -p docs/KB/Vector_RAG
mkdir -p scripts
mkdir -p models  # Optional: for local embedding model
```

**Step 1.2**: Create database schema

Copy `schema.sql` to `docs/KB/Vector_RAG/schema.sql` (see above)

**Step 1.3**: Create Python package structure

```bash
cd docs/KB/Vector_RAG
touch __init__.py
touch __main__.py
```

`__init__.py`:
```python
"""Professor X Context System - 3-Tier Memory with Hybrid RAG"""

__version__ = "1.0.0"
```

`__main__.py`:
```python
"""Entry point for: python -m Vector_RAG.pxctx"""

from .pxctx import cli

if __name__ == "__main__":
    cli()
```

**Step 1.4**: Install dependencies

```bash
cd docs/KB/Vector_RAG
python3 -m venv ../../../.venv
source ../../../.venv/bin/activate
pip install click numpy sentence-transformers tqdm
pip freeze > requirements.txt
```

### Phase 2: Core Modules (Days 3-5)

**Step 2.1**: Implement `db.py`
- Connection manager with WAL mode
- Schema initialization
- CRUD operations for docs/chunks/vectors
- FTS search wrapper
- Content hashing for idempotent updates

**Step 2.2**: Implement `embeddings.py`
- Lazy model loading
- Encode functions
- Serialization (struct.pack floats)
- Vector search (cosine similarity)

**Step 2.3**: Implement `chunking.py`
- Text chunking with overlap
- Sentence splitting
- Markdown-aware chunking with heading context
- Token estimation

**Step 2.4**: Test core modules

```python
# test_core.py
from Vector_RAG.db import Database
from Vector_RAG.embeddings import encode_single, serialize_embedding
from Vector_RAG.chunking import chunk_text

# Test DB
db = Database(Path("test.db"))
doc_id = db.add_doc(
    tier="working",
    title="Test",
    content="Test content",
    type_="finding"
)
print(f"Created doc: {doc_id}")

# Test embeddings
emb = encode_single("hello world")
print(f"Embedding shape: {emb.shape}, dim: {len(emb)}")

# Test chunking
chunks = chunk_text("Lorem ipsum " * 500, target_tokens=600)
print(f"Created {len(chunks)} chunks")
```

### Phase 3: Hybrid Retrieval (Days 6-8)

**Step 3.1**: Implement `query.py`
- `QueryResult` class
- `query()` function
- `_retrieve_tier()` helper
- Scoring algorithm
- Token-budgeted packing

**Step 3.2**: Test retrieval

```python
# test_query.py
from Vector_RAG.db import Database
from Vector_RAG.query import query
from Vector_RAG.embeddings import encode, serialize_embedding

db = Database()

# Add test documents
for i in range(10):
    doc_id = db.add_doc(
        tier=["treasure", "working", "long_lived"][i % 3],
        title=f"Doc {i}",
        content=f"This is test document {i} about topic X",
        type_="kb_doc",
        importance=0.5
    )
    
    chunk_id = db.add_chunk(doc_id, 0, f"Content {i}", 100)
    
    emb = encode([f"Content {i}"])[0]
    db.add_vector(chunk_id, serialize_embedding(emb), "nomic", 768)

# Query
result = query(db, "topic X", final_n=5)
print(f"Treasure: {len(result.packs['treasure'])}")
print(f"Working: {len(result.packs['working'])}")
print(f"Long-lived: {len(result.packs['long_lived'])}")
print(f"Final: {len(result.final)}")
```

### Phase 4: CLI Interface (Days 9-10)

**Step 4.1**: Implement `pxctx.py`
- Click CLI group
- `add` command with idempotent updates
- `query` command with JSON/human output
- `promote`, `supersede`, `gc`, `compact`, `ingest`, `stats`

**Step 4.2**: Create wrapper script

```bash
cat > pxctx <<'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -z "${VIRTUAL_ENV:-}" ]] && [[ -f "${SCRIPT_DIR}/.venv/bin/activate" ]]; then
    source "${SCRIPT_DIR}/.venv/bin/activate"
fi
cd "$SCRIPT_DIR" && PYTHONPATH="$PWD/docs/KB" python -m Vector_RAG.pxctx "$@"
EOF

chmod +x pxctx
```

**Step 4.3**: Test CLI

```bash
./pxctx stats
./pxctx add --tier working --type finding --title "Test" --text "Test content" --repo test --session S-001 --tags test
./pxctx query "test" --json-output
```

### Phase 5: Shell Middleware (Days 11-12)

**Step 5.1**: Implement `scripts/pxctx-auto.sh`
- Session bootstrap
- Context queries
- Simplified recording
- Checkpoints & verification

**Step 5.2**: Test workflow

```bash
source scripts/pxctx-auto.sh
pxctx-boot "Test task"
pxctx-record finding "Test finding"
pxctx-checkpoint "Phase 1 done"
pxctx-verify
pxctx-wrap-up
```

### Phase 6: KB Ingestion (Days 13-14)

**Step 6.1**: Ingest existing documentation

```bash
./pxctx ingest docs/KB \
    --recursive \
    --pattern "*.md" \
    --tier long_lived \
    --repo your-repo \
    --tags kb \
    --on-duplicate update
```

**Step 6.2**: Create Treasure seeds

```bash
# Example: Safety rules
./pxctx add \
    --tier treasure \
    --type security_rule \
    --title "Never execute destructive actions without CONFIRM" \
    --file docs/KB/SAFETY_RULES.md \
    --tags safety,tooling \
    --pin \
    --never-expire \
    --importance 1.0
```

### Phase 7: Integration & Testing (Days 15-16)

**Step 7.1**: Integrate with agent
- Add pxctx queries to agent workflow
- Record findings/decisions/constraints automatically
- Test session continuity

**Step 7.2**: Golden test suite

Create `eval/gold_pxctx.jsonl`:
```jsonl
{"query": "how to handle secrets", "expected_treasure": true, "expected_min_score": 10.0}
{"query": "rust build process", "expected_tiers": ["working", "long_lived"]}
{"query": "session review format", "expected_tags": ["session", "review"]}
```

Run eval:
```python
import json
from Vector_RAG.query import query
from Vector_RAG.db import Database

db = Database()
gold = [json.loads(line) for line in open("eval/gold_pxctx.jsonl")]

for case in gold:
    result = query(db, case["query"])
    
    if "expected_treasure" in case:
        has_treasure = any(h["tier"] == "treasure" for h in result.final)
        assert has_treasure == case["expected_treasure"]
    
    if "expected_min_score" in case:
        max_score = max(h["score"] for h in result.final)
        assert max_score >= case["expected_min_score"]
    
    print(f"✓ {case['query']}")
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_db.py
def test_add_doc():
    db = Database(Path(":memory:"))
    doc_id = db.add_doc("working", "Test", "Content", "finding")
    assert doc_id.startswith("doc:")
    
def test_idempotent_update():
    db = Database(Path(":memory:"))
    ref = "file:test.md"
    
    # First add
    doc_id1 = db.add_doc("working", "Test", "Content v1", "finding", 
                         sources=[{"kind": "file", "ref": ref}])
    
    # Find by source
    found = db.find_doc_by_source("file", ref)
    assert found[0] == doc_id1
    
    # Update with changed content
    db.update_doc_content(doc_id1, "Content v2", db.compute_content_hash("Content v2"))
    
# tests/test_embeddings.py
def test_encode():
    emb = encode_single("hello world")
    assert emb.shape == (768,)
    assert -1.0 <= emb[0] <= 1.0  # Normalized

def test_serialization():
    emb = encode_single("test")
    serialized = serialize_embedding(emb)
    deserialized = deserialize_embedding(serialized)
    assert np.allclose(emb, deserialized)

# tests/test_chunking.py
def test_chunk_text():
    text = "Lorem ipsum. " * 1000
    chunks = chunk_text(text, target_tokens=600, overlap_tokens=100)
    assert len(chunks) > 1
    assert all(estimate_tokens(c) <= 700 for c in chunks)  # Some tolerance

# tests/test_query.py
def test_tier_priority():
    db = setup_test_db()  # Helper: adds treasure/working/long-lived
    result = query(db, "test query", final_n=10)
    
    # Treasure should always rank first
    if result.packs["treasure"]:
        assert result.final[0]["tier"] == "treasure"
```

### Integration Tests

```bash
#!/bin/bash
# tests/integration_test.sh

set -euo pipefail

source scripts/pxctx-auto.sh

# Test session workflow
pxctx-boot "Integration test"

# Add documents
pxctx-record finding "Integration test finding"
pxctx-record decision "Use SQLite for storage"

# Query
result=$(pxctx-context "integration test" --json-output)
count=$(echo "$result" | jq '.final | length')

if [[ "$count" -lt 1 ]]; then
    echo "❌ Query failed: expected results"
    exit 1
fi

# Verify
if ! pxctx-verify; then
    echo "❌ Verification failed"
    exit 1
fi

# Wrap-up
pxctx-wrap-up

echo "✓ Integration test passed"
```

### Performance Tests

```python
# tests/perf_test.py
import time
from Vector_RAG.db import Database
from Vector_RAG.query import query

db = Database()

# Measure query latency
queries = ["test query"] * 100
start = time.time()

for q in queries:
    result = query(db, q, final_n=10)

elapsed = time.time() - start
avg_latency = elapsed / len(queries)

print(f"Avg query latency: {avg_latency*1000:.1f}ms")
assert avg_latency < 0.5  # <500ms per query
```

---

## Performance Considerations

### Database Optimization

**WAL Mode**:
```python
# In db.py _init_db()
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA wal_autocheckpoint=1000")
conn.execute("PRAGMA synchronous=NORMAL")
```

**Indexes**:
- `idx_docs_tier`, `idx_docs_session`, `idx_docs_created` for filtering
- `idx_docs_source` for idempotent updates
- `idx_chunks_doc`, `idx_chunks_doc_index` for chunk lookups
- FTS5 index for full-text search

**Query Limits**:
- Limit candidate docs per tier: `top_k * 3`
- Limit FTS results: `top_k * 2`
- Limit vector candidates: `top_k * 2`

### Embedding Optimization

**Batch Encoding**:
```python
# Good: Batch encode
embeddings = encode(chunks, show_progress=True)

# Bad: Loop encode
for chunk in chunks:
    emb = encode_single(chunk)  # Inefficient
```

**Model Caching**:
- Lazy load model (first query incurs ~2s startup)
- Keep model in memory (global `_model`)

**Local Model**:
- Store model in `models/nomic-embed-text/` to avoid HuggingFace download
- ~547 MB, one-time cost

### Retrieval Optimization

**Token Budget**:
- Default: 1400 tokens (~1050 words, ~7-10 chunks)
- Adjust based on LLM context window

**Tier Limits**:
- Treasure: 12 (small, always pack)
- Working: 18 (session-scoped, high relevance)
- Long-lived: 18 (large KB, filter aggressively)

**Deduplication**:
- Track `seen_chunks` set during packing
- Skip duplicate chunks across tiers

### Scalability

**10K Documents**:
- SQLite: <100MB database
- Vectors: ~30MB (10K docs × 600 tokens/doc × 1 chunk/doc × 768 dim × 4 bytes)
- Query latency: ~200-300ms (vector + FTS + rerank)

**100K Documents**:
- SQLite: <1GB database
- Vectors: ~300MB
- Query latency: ~500ms-1s
- Consider: PostgreSQL + pgvector, Qdrant, or Weaviate

**Concurrency**:
- SQLite WAL: supports concurrent reads + single writer
- For multi-agent: use connection pooling or upgrade to Postgres

---

## Appendix: File Checklist

**Python Modules** (in `docs/KB/Vector_RAG/`):
- [x] `__init__.py`
- [x] `__main__.py`
- [x] `pxctx.py` (CLI)
- [x] `db.py`
- [x] `query.py`
- [x] `embeddings.py`
- [x] `chunking.py`
- [x] `schema.sql`
- [x] `requirements.txt`
- [x] `README.md`

**Scripts**:
- [x] `pxctx` (bash wrapper at repo root)
- [x] `scripts/pxctx-auto.sh`

**Git**:
- [x] `.gitignore`: Add `.pxctx-session`, `pxctx.db`, `__pycache__`, `.venv`

**Documentation**:
- [x] This guide
- [x] System README in `docs/KB/Vector_RAG/README.md`
- [x] Agent instructions referencing pxctx

---

## Summary

This guide provides a complete blueprint for recreating the pxctx hybrid retrieval system:

1. **3-tier memory model**: Treasure > Working > Long-lived
2. **Hybrid search**: Vector (cosine) + FTS (BM25)
3. **Deterministic reranking**: Tier boost + similarity + recency + importance + verified + path + pin
4. **Token-budgeted packing**: Treasure-first (≥25% budget), then Working/Long-lived by score
5. **Idempotent updates**: Content-hash based de-duplication
6. **Shell middleware**: Simplified agent workflow (boot, context, record, checkpoint, verify, wrap-up)
7. **Integration patterns**: Python/shell examples for AI agents

**Key Design Principles**:
- Treasure is authoritative (always highest priority, requires CONFIRM to modify)
- Query pxctx FIRST (primary retrieval), direct file reads SECONDARY
- Session persistence enables continuity across agent invocations
- Hybrid retrieval combines semantic (vector) + lexical (FTS) signals
- Deterministic scoring enables tuning and debugging

**Implementation Roadmap**: 16 days from zero to production-ready system with KB ingestion, agent integration, and testing.

---

**End of Guide**
