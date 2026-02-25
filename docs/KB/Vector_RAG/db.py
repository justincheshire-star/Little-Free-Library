"""
db.py — Database operations for pxctx 3-tier context system.

Manages SQLite with WAL mode, FTS5, and vector storage.
All public methods handle their own connection lifecycle.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = Path(os.environ.get("PXCTX_ROOT", _THIS_DIR.parent.parent.parent))
_STORE_DIR = _REPO_ROOT / ".pxctx"
_SCHEMA_SQL = _THIS_DIR / "schema.sql"

DEFAULT_DB_PATH = _STORE_DIR / "store.db"

TIERS = ("treasure", "working", "long_lived")
VALID_TYPES = (
    "decision", "constraint", "finding", "plan_step",
    "command_summary", "kb_doc", "distilled_note",
    "security_rule", "architecture", "invariant", "checkpoint", "note",
)


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def _make_id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex[:12]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_id(root: Path) -> str:
    return "repo:" + hashlib.sha1(str(root).encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Database class
# ---------------------------------------------------------------------------

class Database:
    """
    Thin wrapper around SQLite providing all pxctx CRUD operations.

    Usage::

        db = Database()          # uses default .pxctx/store.db
        db = Database(":memory:")  # in-memory (tests)
    """

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path) if db_path != ":memory:" else Path(":memory:")
        if self.db_path != Path(":memory:"):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Apply schema (idempotent — all CREATE IF NOT EXISTS)."""
        if _SCHEMA_SQL.exists():
            schema = _SCHEMA_SQL.read_text(encoding="utf-8")
        else:
            # Minimal embedded schema if schema.sql not found
            schema = _MINIMAL_SCHEMA

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            for stmt in _split_statements(schema):
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError:
                    pass  # already exists

    # ------------------------------------------------------------------
    # Document operations
    # ------------------------------------------------------------------

    def add_doc(
        self,
        tier: str,
        title: str,
        content: str,
        type_: str = "note",
        *,
        repo_id: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sources: Optional[List[Dict]] = None,
        importance: float = 0.5,
        verified: Optional[str] = None,
        pin: bool = False,
        never_expire: bool = False,
        ttl_days: Optional[float] = None,
        on_duplicate: str = "update",  # update | skip | error
    ) -> str:
        """
        Add a document.  Returns doc_id.

        ``on_duplicate`` applies when a doc with the same (source_kind, source_ref)
        already exists:
          - "update": skip if content unchanged, re-chunk/embed if changed
          - "skip": always skip
          - "error": raise ValueError
        """
        tier = _normalize_tier(tier)
        type_ = type_ if type_ in VALID_TYPES else "note"

        content_hash = self.compute_content_hash(content)
        sources_list = sources or []

        # Idempotent path
        if sources_list:
            sk = sources_list[0].get("kind", "")
            sr = sources_list[0].get("ref", "")
            existing = self.find_doc_by_source(sk, sr)
            if existing:
                existing_id, existing_hash = existing
                if on_duplicate == "error":
                    raise ValueError(f"Doc already exists: {existing_id}")
                if on_duplicate == "skip" or existing_hash == content_hash:
                    return existing_id
                # "update" with changed content: update and return existing id
                self.update_doc_content(existing_id, content, content_hash)
                return existing_id

        doc_id = _make_id("doc")
        if tier == "treasure":
            never_expire = True
            pin = True

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO docs
                  (doc_id, tier, repo_id, session_id, task_id, title, content,
                   type, tags, sources, importance, verified, pin, never_expire,
                   ttl_days, content_hash, created_at, updated_at, created_by)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    doc_id, tier,
                    repo_id or _repo_id(_REPO_ROOT),
                    session_id or os.environ.get("PXCTX_SESSION_ID"),
                    task_id or os.environ.get("PXCTX_TASK_ID"),
                    title, content, type_,
                    json.dumps(tags or []),
                    json.dumps(sources_list),
                    max(0.0, min(1.0, importance)),
                    verified,
                    int(pin), int(never_expire), ttl_days,
                    content_hash, _now(), _now(), "professorx",
                ),
            )
        return doc_id

    def get_doc(self, doc_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM docs WHERE doc_id=?", (doc_id,)).fetchone()
        return _row_to_dict(row) if row else None

    def update_doc_content(self, doc_id: str, new_content: str, new_hash: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE docs SET content=?, content_hash=?, updated_at=? WHERE doc_id=?",
                (new_content, new_hash, _now(), doc_id),
            )

    def delete_doc(self, doc_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM docs WHERE doc_id=?", (doc_id,))

    def find_doc_by_source(self, source_kind: str, source_ref: str) -> Optional[Tuple[str, str]]:
        """Return (doc_id, content_hash) for first doc whose sources[0] matches."""
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT doc_id, content_hash FROM docs
                WHERE json_extract(sources, '$[0].kind') = ?
                  AND json_extract(sources, '$[0].ref')  = ?
                  AND superseded_by IS NULL
                LIMIT 1
                """,
                (source_kind, source_ref),
            ).fetchone()
        if row:
            return (row["doc_id"], row["content_hash"] or "")
        return None

    def get_docs_by_tier(
        self,
        tier: str,
        *,
        repo_id: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        tags_any: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Return non-superseded, non-expired docs for a tier."""
        tier = _normalize_tier(tier)
        clauses = ["tier=?", "superseded_by IS NULL", "redacted=0"]
        params: List[Any] = [tier]

        if repo_id:
            clauses.append("repo_id=?")
            params.append(repo_id)
        if session_id:
            clauses.append("session_id=?")
            params.append(session_id)
        if task_id:
            clauses.append("task_id=?")
            params.append(task_id)

        sql = f"SELECT * FROM docs WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        docs = [_row_to_dict(r) for r in rows]

        # TTL filter and optional tag filter in Python
        now = datetime.now(timezone.utc)
        result = []
        for d in docs:
            if not d["never_expire"] and d["ttl_days"] is not None:
                created = _parse_dt(d["created_at"])
                if now > created + timedelta(days=d["ttl_days"]):
                    continue
            if tags_any:
                doc_tags = set(d.get("tags") or [])
                if not doc_tags.intersection(tags_any):
                    continue
            result.append(d)

        return result

    # ------------------------------------------------------------------
    # Chunk operations
    # ------------------------------------------------------------------

    def add_chunk(
        self,
        doc_id: str,
        chunk_index: int,
        chunk_text: str,
        token_count: int = 0,
        heading_path: str = "",
    ) -> str:
        chunk_id = _make_id("chunk")
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO doc_chunks (chunk_id, doc_id, chunk_index, chunk_text, token_count, heading_path)
                VALUES (?,?,?,?,?,?)
                """,
                (chunk_id, doc_id, chunk_index, chunk_text, token_count, heading_path),
            )
        return chunk_id

    def get_chunks(self, doc_id: str) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM doc_chunks WHERE doc_id=? ORDER BY chunk_index",
                (doc_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_chunks(self, doc_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM doc_chunks WHERE doc_id=?", (doc_id,))

    def rebuild_fts(self) -> None:
        """Rebuild the FTS5 content table if it drifts from doc_chunks."""
        with self._conn() as conn:
            conn.execute("INSERT INTO doc_chunks_fts(doc_chunks_fts) VALUES('rebuild')")

    # ------------------------------------------------------------------
    # Vector operations
    # ------------------------------------------------------------------

    def add_vector(
        self,
        chunk_id: str,
        embedding: bytes,
        model: str = "nomic-embed-text-v1.5",
        dim: int = 768,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO vectors (chunk_id, embedding, embedding_model, embedding_dim)
                VALUES (?,?,?,?)
                """,
                (chunk_id, embedding, model, dim),
            )

    def get_vector(self, chunk_id: str) -> Optional[bytes]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT embedding FROM vectors WHERE chunk_id=?", (chunk_id,)
            ).fetchone()
        return row["embedding"] if row else None

    def get_vector_meta(self, chunk_id: str) -> Optional[Dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT chunk_id, embedding_model, embedding_dim, created_at FROM vectors WHERE chunk_id=?",
                (chunk_id,),
            ).fetchone()
        return dict(row) if row else None

    def delete_vectors_for_doc(self, doc_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM vectors WHERE chunk_id IN (SELECT chunk_id FROM doc_chunks WHERE doc_id=?)",
                (doc_id,),
            )

    # ------------------------------------------------------------------
    # FTS search
    # ------------------------------------------------------------------

    def fts_search(
        self,
        query_text: str,
        tier: Optional[str] = None,
        limit: int = 40,
    ) -> List[Dict]:
        """
        BM25 full-text search over doc_chunks.
        Returns list of {chunk_id, doc_id, chunk_text, rank, tier}.
        rank is raw BM25 (negative; lower = better match).
        """
        if not query_text.strip():
            return []

        # Build FTS query: OR across all meaningful words
        words = [w for w in query_text.split() if len(w) > 1]
        if not words:
            return []
        fts_q = " OR ".join(f'"{w}"' for w in words)

        sql = """
            SELECT f.chunk_id, f.rank, c.doc_id, c.chunk_text
            FROM doc_chunks_fts f
            JOIN doc_chunks c ON c.chunk_id = f.chunk_id
            JOIN docs d ON d.doc_id = c.doc_id
            WHERE doc_chunks_fts MATCH ?
              AND d.superseded_by IS NULL
              AND d.redacted = 0
        """
        params: List[Any] = [fts_q]

        if tier:
            sql += " AND d.tier = ?"
            params.append(_normalize_tier(tier))

        sql += " ORDER BY f.rank LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                return []

        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Lifecycle operations
    # ------------------------------------------------------------------

    def promote_to_tier(
        self,
        doc_id: str,
        to_tier: str,
        *,
        pin: bool = False,
        never_expire: bool = False,
    ) -> bool:
        to_tier = _normalize_tier(to_tier)
        if to_tier == "treasure":
            pin = True
            never_expire = True

        with self._conn() as conn:
            row = conn.execute("SELECT doc_id FROM docs WHERE doc_id=?", (doc_id,)).fetchone()
            if not row:
                return False
            conn.execute(
                "UPDATE docs SET tier=?, pin=?, never_expire=?, ttl_days=NULL, updated_at=? WHERE doc_id=?",
                (to_tier, int(pin), int(never_expire), _now(), doc_id),
            )
        return True

    def supersede_doc(self, doc_id: str, old_ids: Sequence[str]) -> bool:
        """Mark old_ids as superseded by doc_id."""
        with self._conn() as conn:
            row = conn.execute("SELECT doc_id FROM docs WHERE doc_id=?", (doc_id,)).fetchone()
            if not row:
                return False
            for oid in old_ids:
                conn.execute(
                    "UPDATE docs SET superseded_by=?, updated_at=? WHERE doc_id=?",
                    (doc_id, _now(), oid),
                )
            conn.execute(
                "UPDATE docs SET supersedes=?, updated_at=? WHERE doc_id=?",
                (json.dumps(list(old_ids)), _now(), doc_id),
            )
        return True

    def gc_expired(self) -> List[str]:
        """Delete expired (TTL) non-Treasure docs. Returns list of deleted doc_ids."""
        now = datetime.now(timezone.utc)
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT doc_id, created_at, ttl_days FROM docs WHERE never_expire=0 AND ttl_days IS NOT NULL"
            ).fetchall()

            deleted = []
            for row in rows:
                created = _parse_dt(row["created_at"])
                if now > created + timedelta(days=row["ttl_days"]):
                    conn.execute("DELETE FROM docs WHERE doc_id=?", (row["doc_id"],))
                    deleted.append(row["doc_id"])
        return deleted

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(
        self,
        session_id: str,
        task_id: str,
        description: str = "",
        repo_id: Optional[str] = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, repo_id, task_id, description, created_at, updated_at)
                VALUES (?,?,?,?,?,?)
                """,
                (session_id, repo_id or _repo_id(_REPO_ROOT), task_id, description, _now(), _now()),
            )

    def update_session(
        self,
        session_id: str,
        *,
        state: Optional[str] = None,
        description: Optional[str] = None,
        record_count_delta: int = 0,
    ) -> None:
        with self._conn() as conn:
            if state:
                conn.execute(
                    "UPDATE sessions SET state=?, updated_at=? WHERE session_id=?",
                    (state, _now(), session_id),
                )
            if description:
                conn.execute(
                    "UPDATE sessions SET description=?, updated_at=? WHERE session_id=?",
                    (description, _now(), session_id),
                )
            if record_count_delta:
                conn.execute(
                    "UPDATE sessions SET record_count=record_count+?, updated_at=? WHERE session_id=?",
                    (record_count_delta, _now(), session_id),
                )

    def get_sessions(self, limit: int = 10) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Stats / validation helpers
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict:
        with self._conn() as conn:
            meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM system_metadata").fetchall()}
            tier_counts = {
                r["tier"]: r["cnt"]
                for r in conn.execute(
                    "SELECT tier, COUNT(*) AS cnt FROM docs WHERE superseded_by IS NULL GROUP BY tier"
                ).fetchall()
            }
            coverage = conn.execute(
                """
                SELECT
                  COUNT(DISTINCT d.doc_id)          AS total_docs,
                  COUNT(DISTINCT c.chunk_id)         AS total_chunks,
                  COUNT(DISTINCT v.chunk_id)         AS total_vectors,
                  COUNT(DISTINCT CASE WHEN v.chunk_id IS NULL AND c.chunk_id IS NOT NULL
                                      THEN c.chunk_id END) AS unvectorized_chunks
                FROM docs d
                LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
                LEFT JOIN vectors     v ON c.chunk_id = v.chunk_id
                WHERE d.superseded_by IS NULL
                """
            ).fetchone()
        return {
            "schema_version": meta.get("schema_version", "unknown"),
            "embedding_model": meta.get("embedding_model", "unknown"),
            "embedding_dim": int(meta.get("embedding_dim", 0)),
            "docs_by_tier": dict(tier_counts),
            "total_docs": coverage["total_docs"],
            "total_chunks": coverage["total_chunks"],
            "total_vectors": coverage["total_vectors"],
            "unvectorized_chunks": coverage["unvectorized_chunks"],
            "vector_coverage_pct": (
                round(100.0 * coverage["total_vectors"] / coverage["total_chunks"], 1)
                if coverage["total_chunks"] > 0 else 0.0
            ),
        }

    def vector_coverage_report(self) -> List[Dict]:
        """Per-doc vector coverage — used by validate_vectorset."""
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM v_vector_coverage ORDER BY coverage_pct ASC").fetchall()
        return [dict(r) for r in rows]

    def orphaned_vectors(self) -> List[str]:
        """Chunk IDs with vectors but no parent chunk row."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT v.chunk_id FROM vectors v LEFT JOIN doc_chunks c ON v.chunk_id=c.chunk_id WHERE c.chunk_id IS NULL"
            ).fetchall()
        return [r["chunk_id"] for r in rows]

    def orphaned_chunks(self) -> List[str]:
        """Chunk IDs whose parent doc no longer exists."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT c.chunk_id FROM doc_chunks c LEFT JOIN docs d ON c.doc_id=d.doc_id WHERE d.doc_id IS NULL"
            ).fetchall()
        return [r["chunk_id"] for r in rows]

    def embedding_model_consistency(self) -> Dict:
        """Check that all vectors use the same model and dimension."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT embedding_model, embedding_dim, COUNT(*) AS cnt FROM vectors GROUP BY embedding_model, embedding_dim"
            ).fetchall()
        models = [dict(r) for r in rows]
        return {
            "consistent": len(models) <= 1,
            "models": models,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def compute_content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _normalize_tier(tier: str) -> str:
    """Accept 'long-lived' → 'long_lived', etc."""
    return tier.replace("-", "_")


def _row_to_dict(row: sqlite3.Row) -> Dict:
    d = dict(row)
    for field in ("tags", "sources", "supersedes"):
        if isinstance(d.get(field), str):
            try:
                d[field] = json.loads(d[field])
            except Exception:
                d[field] = []
    return d


def _parse_dt(value: str) -> datetime:
    """Parse ISO datetime; add UTC tz if missing."""
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def _split_statements(sql: str) -> List[str]:
    """Split SQL on semicolons, skipping empty statements and comments."""
    stmts = []
    for raw in sql.split(";"):
        s = raw.strip()
        if s and not s.startswith("--"):
            stmts.append(s)
    return stmts


# ---------------------------------------------------------------------------
# Minimal embedded schema (fallback if schema.sql not found)
# ---------------------------------------------------------------------------

_MINIMAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
    doc_id TEXT PRIMARY KEY,
    tier TEXT NOT NULL CHECK(tier IN ('treasure','working','long_lived')),
    repo_id TEXT, session_id TEXT, task_id TEXT,
    title TEXT NOT NULL, content TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'note',
    tags TEXT DEFAULT '[]', sources TEXT DEFAULT '[]',
    importance REAL DEFAULT 0.5,
    verified TEXT,
    pin INTEGER DEFAULT 0, never_expire INTEGER DEFAULT 0, ttl_days REAL,
    supersedes TEXT DEFAULT '[]', superseded_by TEXT,
    content_hash TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_by TEXT DEFAULT 'professorx', redacted INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS doc_chunks (
    chunk_id TEXT PRIMARY KEY, doc_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL, chunk_text TEXT NOT NULL,
    token_count INTEGER, heading_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (doc_id) REFERENCES docs(doc_id) ON DELETE CASCADE
);
CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunks_fts USING fts5(
    chunk_id UNINDEXED, chunk_text, content='doc_chunks', content_rowid='rowid'
);
CREATE TRIGGER IF NOT EXISTS doc_chunks_fts_insert AFTER INSERT ON doc_chunks BEGIN
    INSERT INTO doc_chunks_fts(rowid, chunk_id, chunk_text) VALUES (new.rowid, new.chunk_id, new.chunk_text);
END;
CREATE TRIGGER IF NOT EXISTS doc_chunks_fts_delete AFTER DELETE ON doc_chunks BEGIN
    DELETE FROM doc_chunks_fts WHERE rowid = old.rowid;
END;
CREATE TRIGGER IF NOT EXISTS doc_chunks_fts_update AFTER UPDATE ON doc_chunks BEGIN
    DELETE FROM doc_chunks_fts WHERE rowid = old.rowid;
    INSERT INTO doc_chunks_fts(rowid, chunk_id, chunk_text) VALUES (new.rowid, new.chunk_id, new.chunk_text);
END;
CREATE TABLE IF NOT EXISTS vectors (
    chunk_id TEXT PRIMARY KEY, embedding BLOB NOT NULL,
    embedding_model TEXT NOT NULL, embedding_dim INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (chunk_id) REFERENCES doc_chunks(chunk_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY, repo_id TEXT, task_id TEXT,
    description TEXT, record_count INTEGER DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY, value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
INSERT OR IGNORE INTO system_metadata(key,value) VALUES
    ('schema_version','1.0'),('embedding_model','nomic-embed-text-v1.5'),
    ('embedding_dim','768'),('total_docs','0'),('total_chunks','0'),('total_vectors','0');
"""
