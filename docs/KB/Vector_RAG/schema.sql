-- Professor X Context System — 3-Tier Memory (Working / Long-lived / Treasure)
-- Schema Version: 1.0

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA synchronous=NORMAL;

-- ============================================================================
-- DOCS: Core document/memory storage
-- ============================================================================

CREATE TABLE IF NOT EXISTS docs (
    doc_id        TEXT PRIMARY KEY,
    tier          TEXT NOT NULL CHECK(tier IN ('working', 'long_lived', 'treasure')),

    -- Scope identifiers
    repo_id       TEXT,
    session_id    TEXT,
    task_id       TEXT,

    -- Content
    title         TEXT NOT NULL,
    content       TEXT NOT NULL,

    -- Classification
    type          TEXT NOT NULL DEFAULT 'finding' CHECK(type IN (
        'decision', 'constraint', 'finding', 'plan_step',
        'command_summary', 'kb_doc', 'distilled_note',
        'security_rule', 'architecture', 'invariant', 'checkpoint', 'note'
    )),

    -- Metadata
    tags          TEXT DEFAULT '[]',       -- JSON array
    sources       TEXT DEFAULT '[]',       -- JSON array of {kind, ref}
    importance    REAL DEFAULT 0.5 CHECK(importance >= 0.0 AND importance <= 1.0),
    verified      TEXT CHECK(verified IN ('asserted', 'observed', 'tested', 'documented')),

    -- Lifecycle
    pin           INTEGER DEFAULT 0,
    never_expire  INTEGER DEFAULT 0,
    ttl_days      REAL,
    supersedes    TEXT DEFAULT '[]',       -- JSON array of doc_ids this supersedes
    superseded_by TEXT,                    -- doc_id that supersedes this

    -- Content hash for idempotent updates (SHA256)
    content_hash  TEXT,

    -- Timestamps
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
    created_by    TEXT DEFAULT 'professorx',

    -- Redaction flag
    redacted      INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_docs_tier       ON docs(tier);
CREATE INDEX IF NOT EXISTS idx_docs_repo       ON docs(repo_id);
CREATE INDEX IF NOT EXISTS idx_docs_session    ON docs(session_id);
CREATE INDEX IF NOT EXISTS idx_docs_task       ON docs(task_id);
CREATE INDEX IF NOT EXISTS idx_docs_type       ON docs(type);
CREATE INDEX IF NOT EXISTS idx_docs_created    ON docs(created_at);
CREATE INDEX IF NOT EXISTS idx_docs_pin        ON docs(pin);
CREATE INDEX IF NOT EXISTS idx_docs_superseded ON docs(superseded_by);

-- Index for fast source-ref lookup (idempotent updates)
CREATE INDEX IF NOT EXISTS idx_docs_source ON docs(
    json_extract(sources, '$[0].kind'),
    json_extract(sources, '$[0].ref')
) WHERE sources IS NOT NULL AND sources != '[]';

-- ============================================================================
-- DOC_CHUNKS: Chunked text for embedding
-- ============================================================================

CREATE TABLE IF NOT EXISTS doc_chunks (
    chunk_id     TEXT PRIMARY KEY,
    doc_id       TEXT NOT NULL,
    chunk_index  INTEGER NOT NULL,
    chunk_text   TEXT NOT NULL,
    token_count  INTEGER,
    heading_path TEXT,   -- Markdown heading context, e.g. "# Top > ## Sub"
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (doc_id) REFERENCES docs(doc_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc       ON doc_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_index ON doc_chunks(doc_id, chunk_index);

-- ============================================================================
-- DOC_CHUNKS_FTS: Full-text search index (BM25 via FTS5)
-- ============================================================================

CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunks_fts USING fts5(
    chunk_id   UNINDEXED,
    chunk_text,
    content='doc_chunks',
    content_rowid='rowid'
);

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
-- VECTORS: Embedding storage (packed float32)
-- ============================================================================

CREATE TABLE IF NOT EXISTS vectors (
    chunk_id        TEXT PRIMARY KEY,
    embedding       BLOB NOT NULL,    -- struct.pack(f"{dim}f", *values)
    embedding_model TEXT NOT NULL,
    embedding_dim   INTEGER NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (chunk_id) REFERENCES doc_chunks(chunk_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_vectors_chunk ON vectors(chunk_id);

-- ============================================================================
-- SESSIONS: Session state tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    session_id    TEXT PRIMARY KEY,
    repo_id       TEXT,
    task_id       TEXT,
    description   TEXT,
    record_count  INTEGER DEFAULT 0,
    state         TEXT NOT NULL DEFAULT 'active' CHECK(state IN ('active', 'wrapped')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================================
-- SYSTEM_METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_metadata (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO system_metadata (key, value) VALUES
    ('schema_version',  '1.0'),
    ('created_at',      datetime('now')),
    ('embedding_model', 'nomic-embed-text-v1.5'),
    ('embedding_dim',   '768'),
    ('total_docs',      '0'),
    ('total_chunks',    '0'),
    ('total_vectors',   '0');

-- ============================================================================
-- VIEWS
-- ============================================================================

CREATE VIEW IF NOT EXISTS v_treasure AS
SELECT d.*, COUNT(c.chunk_id) AS chunk_count
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
WHERE d.tier = 'treasure' AND d.superseded_by IS NULL
GROUP BY d.doc_id
ORDER BY d.importance DESC, d.created_at DESC;

CREATE VIEW IF NOT EXISTS v_working AS
SELECT d.*, COUNT(c.chunk_id) AS chunk_count,
       (julianday('now') - julianday(d.created_at)) AS age_days
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
WHERE d.tier = 'working' AND d.superseded_by IS NULL
GROUP BY d.doc_id
ORDER BY d.created_at DESC;

CREATE VIEW IF NOT EXISTS v_long_lived AS
SELECT d.*, COUNT(c.chunk_id) AS chunk_count,
       CASE d.verified
           WHEN 'documented' THEN 4
           WHEN 'tested'     THEN 3
           WHEN 'observed'   THEN 2
           WHEN 'asserted'   THEN 1
           ELSE 0
       END AS verified_rank
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
WHERE d.tier = 'long_lived' AND d.superseded_by IS NULL
GROUP BY d.doc_id
ORDER BY verified_rank DESC, d.importance DESC, d.created_at DESC;

-- Vector coverage view (for validation)
CREATE VIEW IF NOT EXISTS v_vector_coverage AS
SELECT
    d.doc_id,
    d.tier,
    d.title,
    COUNT(c.chunk_id)                                             AS total_chunks,
    COUNT(v.chunk_id)                                             AS vectorized_chunks,
    ROUND(100.0 * COUNT(v.chunk_id) / MAX(COUNT(c.chunk_id), 1)) AS coverage_pct
FROM docs d
LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
LEFT JOIN vectors    v ON c.chunk_id = v.chunk_id
WHERE d.superseded_by IS NULL
GROUP BY d.doc_id;

-- ============================================================================
-- METADATA MAINTENANCE TRIGGERS
-- ============================================================================

CREATE TRIGGER IF NOT EXISTS trg_doc_count_insert AFTER INSERT ON docs BEGIN
    UPDATE system_metadata
    SET value = (SELECT COUNT(*) FROM docs), updated_at = datetime('now')
    WHERE key = 'total_docs';
END;

CREATE TRIGGER IF NOT EXISTS trg_doc_count_delete AFTER DELETE ON docs BEGIN
    UPDATE system_metadata
    SET value = (SELECT COUNT(*) FROM docs), updated_at = datetime('now')
    WHERE key = 'total_docs';
END;

CREATE TRIGGER IF NOT EXISTS trg_chunk_count_insert AFTER INSERT ON doc_chunks BEGIN
    UPDATE system_metadata
    SET value = (SELECT COUNT(*) FROM doc_chunks), updated_at = datetime('now')
    WHERE key = 'total_chunks';
END;

CREATE TRIGGER IF NOT EXISTS trg_chunk_count_delete AFTER DELETE ON doc_chunks BEGIN
    UPDATE system_metadata
    SET value = (SELECT COUNT(*) FROM doc_chunks), updated_at = datetime('now')
    WHERE key = 'total_chunks';
END;

CREATE TRIGGER IF NOT EXISTS trg_vector_count_insert AFTER INSERT ON vectors BEGIN
    UPDATE system_metadata
    SET value = (SELECT COUNT(*) FROM vectors), updated_at = datetime('now')
    WHERE key = 'total_vectors';
END;

CREATE TRIGGER IF NOT EXISTS trg_vector_count_delete AFTER DELETE ON vectors BEGIN
    UPDATE system_metadata
    SET value = (SELECT COUNT(*) FROM vectors), updated_at = datetime('now')
    WHERE key = 'total_vectors';
END;
