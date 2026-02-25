#!/usr/bin/env python3
"""
validate_vectorset.py — Validate vectorized document sets in the pxctx store.

Checks:
  1.  Database reachability and schema version
  2.  Overall vector coverage (chunks with embeddings / total chunks)
  3.  Per-document vector coverage (flags docs with partial / zero coverage)
  4.  Embedding model & dimension consistency
  5.  Orphaned vectors (vectors whose chunk row was deleted)
  6.  Orphaned chunks (chunks whose parent doc was deleted)
  7.  FTS5 integrity (rowcount parity between doc_chunks and FTS index)
  8.  Tier distribution sanity (at least one doc per active tier if expected)
  9.  Embedding dimension sanity-check via deserialization round-trip
 10.  Semantic round-trip (optional, requires sentence-transformers):
      encode a sample query → cosine_similarity with stored vectors → spot-check

Usage:
  python scripts/validate_vectorset.py [options]

Exit codes:
  0  — all checks passed
  1  — one or more checks FAILED
  2  — warnings only (no failures)

Options:
  --json               Output results as JSON
  --strict             Treat warnings as failures
  --min-coverage PCT   Coverage threshold (default: 80.0)
  --semantic-check     Run embedding round-trip (slow; requires model)
  --fix-orphans        DELETE orphaned vectors/chunks from DB
  --db PATH            Override default .pxctx/store.db path
  --quiet              Suppress progress output
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).parent
_REPO_ROOT  = Path(os.environ.get("PXCTX_ROOT", _SCRIPT_DIR.parent))
_KB_DIR     = _REPO_ROOT / "docs" / "KB"

# Add docs/KB to Python path so Vector_RAG is importable
sys.path.insert(0, str(_KB_DIR))

try:
    from Vector_RAG.db import Database, DEFAULT_DB_PATH
    _HAS_MODULE = True
except ImportError:
    _HAS_MODULE = False

try:
    import sqlite3
    _HAS_SQLITE = True
except ImportError:
    _HAS_SQLITE = False

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class Severity:
    PASS    = "PASS"
    WARN    = "WARN"
    FAIL    = "FAIL"
    SKIP    = "SKIP"
    INFO    = "INFO"


class CheckResult:
    def __init__(self, name: str, status: str, detail: str = "", data: Any = None):
        self.name   = name
        self.status = status
        self.detail = detail
        self.data   = data

    def to_dict(self) -> Dict:
        return {"check": self.name, "status": self.status, "detail": self.detail}


# ---------------------------------------------------------------------------
# ANSI color helpers (stripped when not a tty)
# ---------------------------------------------------------------------------

def _color(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def _green(t):  return _color(t, "32")
def _yellow(t): return _color(t, "33")
def _red(t):    return _color(t, "31")
def _cyan(t):   return _color(t, "36")
def _bold(t):   return _color(t, "1")


_STATUS_COLOR = {
    Severity.PASS: _green,
    Severity.WARN: _yellow,
    Severity.FAIL: _red,
    Severity.SKIP: _cyan,
    Severity.INFO: _cyan,
}


def _fmt(result: CheckResult) -> str:
    color = _STATUS_COLOR.get(result.status, str)
    badge = f"[{result.status:4s}]"
    detail = f"  {result.detail}" if result.detail else ""
    return f"  {color(badge)}  {result.name}{detail}"


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class VectorSetValidator:
    def __init__(
        self,
        db_path: Path,
        min_coverage_pct: float = 80.0,
        strict: bool = False,
        semantic_check: bool = False,
        fix_orphans: bool = False,
        quiet: bool = False,
    ):
        self.db_path          = db_path
        self.min_coverage_pct = min_coverage_pct
        self.strict           = strict
        self.semantic_check   = semantic_check
        self.fix_orphans      = fix_orphans
        self.quiet            = quiet

        self.results: List[CheckResult] = []
        self._db: Optional[Database]    = None
        self._conn = None  # raw sqlite3 fallback

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> List[CheckResult]:
        self._print_header()
        self._check_db_reachable()
        self._check_schema_version()
        self._check_overall_coverage()
        self._check_per_doc_coverage()
        self._check_embedding_consistency()
        self._check_orphaned_vectors()
        self._check_orphaned_chunks()
        self._check_fts_parity()
        self._check_tier_distribution()
        self._check_dim_round_trip()
        if self.semantic_check:
            self._check_semantic_round_trip()
        return self.results

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_db_reachable(self):
        if not self.db_path.exists():
            self._add(Severity.FAIL, "DB reachable",
                      f"Database not found: {self.db_path}")
            return

        try:
            if _HAS_MODULE:
                self._db = Database(self.db_path)
            else:
                import sqlite3 as _sqlite3
                self._conn = _sqlite3.connect(str(self.db_path))
                self._conn.row_factory = _sqlite3.Row
            self._add(Severity.PASS, "DB reachable", str(self.db_path))
        except Exception as e:
            self._add(Severity.FAIL, "DB reachable", str(e))

    def _check_schema_version(self):
        version = self._meta("schema_version")
        if version is None:
            self._add(Severity.WARN, "Schema version", "system_metadata table missing or empty")
        else:
            self._add(Severity.PASS, "Schema version", f"v{version}")

    def _check_overall_coverage(self):
        try:
            stats = self._stats()
            total_chunks = stats["total_chunks"]
            total_vectors = stats["total_vectors"]
            pct = stats["vector_coverage_pct"]

            detail = f"{total_vectors}/{total_chunks} chunks vectorized ({pct}%)"

            if total_chunks == 0:
                self._add(Severity.INFO, "Vector coverage", "No chunks in store yet")
                return

            if pct >= self.min_coverage_pct:
                self._add(Severity.PASS, "Vector coverage", detail)
            elif pct >= 0.1:
                self._add(Severity.WARN, "Vector coverage",
                          f"{detail}  (threshold: {self.min_coverage_pct}%)")
            else:
                self._add(Severity.FAIL, "Vector coverage",
                          f"{detail}  (threshold: {self.min_coverage_pct}%)")
        except Exception as e:
            self._add(Severity.FAIL, "Vector coverage", str(e))

    def _check_per_doc_coverage(self):
        try:
            if self._db:
                rows = self._db.vector_coverage_report()
            else:
                rows = self._sql(
                    """
                    SELECT d.doc_id, d.tier, d.title,
                      COUNT(c.chunk_id) AS total_chunks,
                      COUNT(v.chunk_id) AS vectorized_chunks,
                      ROUND(100.0 * COUNT(v.chunk_id) / MAX(COUNT(c.chunk_id), 1)) AS coverage_pct
                    FROM docs d
                    LEFT JOIN doc_chunks c ON d.doc_id = c.doc_id
                    LEFT JOIN vectors v    ON c.chunk_id = v.chunk_id
                    WHERE d.superseded_by IS NULL
                    GROUP BY d.doc_id
                    ORDER BY coverage_pct ASC
                    """
                )

            fully_covered = sum(1 for r in rows if float(r.get("coverage_pct") or 0) >= 100)
            partial       = sum(1 for r in rows if 0 < float(r.get("coverage_pct") or 0) < 100)
            zero          = sum(1 for r in rows if float(r.get("coverage_pct") or 0) == 0)

            detail = f"fully={fully_covered}  partial={partial}  zero={zero}"

            if zero > 0:
                sev = Severity.WARN if (zero / max(len(rows), 1)) < 0.1 else Severity.FAIL
                # List up to 5 zero-coverage docs
                zerodocs = [r for r in rows if float(r.get("coverage_pct") or 0) == 0][:5]
                names = ", ".join(r.get("title", r.get("doc_id", "?"))[:40] for r in zerodocs)
                self._add(sev, "Per-doc coverage",
                          f"{detail}  — zero-coverage docs: {names}{'…' if zero > 5 else ''}",
                          data={"zero_docs": [r.get("doc_id") for r in rows if float(r.get("coverage_pct") or 0) == 0]})
            else:
                self._add(Severity.PASS, "Per-doc coverage", detail)
        except Exception as e:
            self._add(Severity.FAIL, "Per-doc coverage", str(e))

    def _check_embedding_consistency(self):
        try:
            if self._db:
                info = self._db.embedding_model_consistency()
                models = info["models"]
                consistent = info["consistent"]
            else:
                rows = self._sql(
                    "SELECT embedding_model, embedding_dim, COUNT(*) AS cnt FROM vectors GROUP BY embedding_model, embedding_dim"
                )
                models = [dict(r) for r in rows]
                consistent = len(models) <= 1

            if not models:
                self._add(Severity.INFO, "Embedding consistency", "No vectors stored yet")
            elif consistent:
                m = models[0]
                self._add(Severity.PASS, "Embedding consistency",
                          f"model={m['embedding_model']}  dim={m['embedding_dim']}  count={m['cnt']}")
            else:
                summary = "  ".join(
                    f"{m['embedding_model']}(dim={m['embedding_dim']}, n={m['cnt']})"
                    for m in models
                )
                self._add(Severity.FAIL, "Embedding consistency",
                          f"Mixed models in store: {summary}")
        except Exception as e:
            self._add(Severity.FAIL, "Embedding consistency", str(e))

    def _check_orphaned_vectors(self):
        try:
            if self._db:
                orphans = self._db.orphaned_vectors()
            else:
                rows = self._sql(
                    "SELECT v.chunk_id FROM vectors v LEFT JOIN doc_chunks c ON v.chunk_id=c.chunk_id WHERE c.chunk_id IS NULL"
                )
                orphans = [r["chunk_id"] for r in rows]

            if not orphans:
                self._add(Severity.PASS, "Orphaned vectors", "none")
            else:
                if self.fix_orphans:
                    self._delete_orphaned_vectors(orphans)
                    self._add(Severity.WARN, "Orphaned vectors",
                              f"{len(orphans)} found and deleted (--fix-orphans)")
                else:
                    self._add(Severity.WARN, "Orphaned vectors",
                              f"{len(orphans)} vector(s) with no parent chunk  (run --fix-orphans to clean up)",
                              data={"orphaned_vector_ids": orphans[:20]})
        except Exception as e:
            self._add(Severity.FAIL, "Orphaned vectors", str(e))

    def _check_orphaned_chunks(self):
        try:
            if self._db:
                orphans = self._db.orphaned_chunks()
            else:
                rows = self._sql(
                    "SELECT c.chunk_id FROM doc_chunks c LEFT JOIN docs d ON c.doc_id=d.doc_id WHERE d.doc_id IS NULL"
                )
                orphans = [r["chunk_id"] for r in rows]

            if not orphans:
                self._add(Severity.PASS, "Orphaned chunks", "none")
            else:
                if self.fix_orphans:
                    self._delete_orphaned_chunks(orphans)
                    self._add(Severity.WARN, "Orphaned chunks",
                              f"{len(orphans)} found and deleted (--fix-orphans)")
                else:
                    self._add(Severity.WARN, "Orphaned chunks",
                              f"{len(orphans)} chunk(s) with no parent doc  (run --fix-orphans to clean up)",
                              data={"orphaned_chunk_ids": orphans[:20]})
        except Exception as e:
            self._add(Severity.FAIL, "Orphaned chunks", str(e))

    def _check_fts_parity(self):
        """FTS5 row count should match doc_chunks row count."""
        try:
            chunks_count = self._scalar("SELECT COUNT(*) FROM doc_chunks")
            # FTS5 content tables don't have a simple COUNT — use rowid scan
            try:
                fts_count = self._scalar("SELECT COUNT(*) FROM doc_chunks_fts")
            except Exception:
                fts_count = None

            if fts_count is None:
                self._add(Severity.WARN, "FTS5 parity", "Could not read FTS table row count")
                return

            if chunks_count == fts_count:
                self._add(Severity.PASS, "FTS5 parity", f"{chunks_count} rows in sync")
            else:
                delta = abs(chunks_count - fts_count)
                sev = Severity.WARN if delta < 10 else Severity.FAIL
                self._add(sev, "FTS5 parity",
                          f"doc_chunks={chunks_count}  fts_index={fts_count}  delta={delta}"
                          f"  (run `pxctx rebuild-fts` to fix)")
        except Exception as e:
            self._add(Severity.SKIP, "FTS5 parity", f"Could not check: {e}")

    def _check_tier_distribution(self):
        """Warn if Treasure tier is empty."""
        try:
            treasure_count = self._scalar(
                "SELECT COUNT(*) FROM docs WHERE tier='treasure' AND superseded_by IS NULL"
            )
            working_count = self._scalar(
                "SELECT COUNT(*) FROM docs WHERE tier='working' AND superseded_by IS NULL"
            )
            ll_count = self._scalar(
                "SELECT COUNT(*) FROM docs WHERE tier='long_lived' AND superseded_by IS NULL"
            )
            total = treasure_count + working_count + ll_count

            if total == 0:
                self._add(Severity.INFO, "Tier distribution", "Store is empty")
                return

            detail = f"treasure={treasure_count}  working={working_count}  long_lived={ll_count}"

            if treasure_count == 0:
                self._add(Severity.WARN, "Tier distribution",
                          f"{detail}  — Treasure is empty (no safety rules pinned)")
            else:
                self._add(Severity.PASS, "Tier distribution", detail)
        except Exception as e:
            self._add(Severity.FAIL, "Tier distribution", str(e))

    def _check_dim_round_trip(self):
        """
        Pick a sample vector and verify it deserializes to the expected dimension.
        Does NOT require sentence-transformers.
        """
        try:
            row = self._sql_one(
                "SELECT chunk_id, embedding, embedding_dim FROM vectors LIMIT 1"
            )
            if row is None:
                self._add(Severity.INFO, "Dim round-trip", "No vectors to sample")
                return

            raw: bytes = row["embedding"]
            expected_dim: int = int(row["embedding_dim"])
            actual_floats = len(raw) // 4

            if actual_floats == expected_dim:
                # Verify values are finite
                vals = struct.unpack(f"{actual_floats}f", raw)
                all_finite = all(-1e6 < v < 1e6 for v in vals)
                if all_finite:
                    self._add(Severity.PASS, "Dim round-trip",
                              f"sample chunk={row['chunk_id']}  dim={actual_floats}  values finite")
                else:
                    self._add(Severity.WARN, "Dim round-trip",
                              f"Some values out of range — possible corruption in {row['chunk_id']}")
            else:
                self._add(Severity.FAIL, "Dim round-trip",
                          f"Expected dim={expected_dim}  got {actual_floats} floats in {row['chunk_id']}")
        except Exception as e:
            self._add(Severity.FAIL, "Dim round-trip", str(e))

    def _check_semantic_round_trip(self):
        """
        Encode a synthetic query and find the top cosine match in the store.
        Validates that the retrieval pipeline returns a result with score > 0.
        Requires sentence-transformers + numpy.
        """
        probe_text = "Professor X context system three tier memory"
        try:
            from Vector_RAG.embeddings import (
                encode_query, deserialize_embedding, vector_search, embedding_available
            )
        except ImportError:
            self._add(Severity.SKIP, "Semantic round-trip", "Vector_RAG not importable")
            return

        if not embedding_available():
            self._add(Severity.SKIP, "Semantic round-trip",
                      "sentence-transformers not installed")
            return

        # Gather sample vectors (up to 50)
        rows = self._sql(
            "SELECT chunk_id, embedding FROM vectors LIMIT 50"
        )
        if not rows:
            self._add(Severity.INFO, "Semantic round-trip", "No vectors to search")
            return

        try:
            query_emb = encode_query(probe_text)
            candidates = [(r["chunk_id"], r["embedding"]) for r in rows]
            results = vector_search(query_emb, candidates, top_k=3)

            if results:
                top_id, top_score = results[0]
                if top_score > 0.0:
                    self._add(Severity.PASS, "Semantic round-trip",
                              f"top={top_id}  score={top_score:.4f}")
                else:
                    self._add(Severity.WARN, "Semantic round-trip",
                              f"Best score={top_score:.4f} is suspiciously low")
            else:
                self._add(Severity.FAIL, "Semantic round-trip", "vector_search returned no results")
        except Exception as e:
            self._add(Severity.FAIL, "Semantic round-trip", str(e))

    # ------------------------------------------------------------------
    # Fix helpers
    # ------------------------------------------------------------------

    def _delete_orphaned_vectors(self, ids: List[str]) -> None:
        for oid in ids:
            self._execute("DELETE FROM vectors WHERE chunk_id=?", (oid,))

    def _delete_orphaned_chunks(self, ids: List[str]) -> None:
        for oid in ids:
            self._execute("DELETE FROM doc_chunks WHERE chunk_id=?", (oid,))

    # ------------------------------------------------------------------
    # DB helper methods
    # ------------------------------------------------------------------

    def _meta(self, key: str) -> Optional[str]:
        try:
            row = self._sql_one("SELECT value FROM system_metadata WHERE key=?", (key,))
            return row["value"] if row else None
        except Exception:
            return None

    def _stats(self) -> Dict:
        if self._db:
            return self._db.get_stats()
        # Raw SQL fallback
        total_docs    = self._scalar("SELECT COUNT(*) FROM docs WHERE superseded_by IS NULL") or 0
        total_chunks  = self._scalar("SELECT COUNT(*) FROM doc_chunks") or 0
        total_vectors = self._scalar("SELECT COUNT(*) FROM vectors") or 0
        pct = round(100.0 * total_vectors / total_chunks, 1) if total_chunks else 0.0
        return {
            "schema_version": "?",
            "embedding_model": "?",
            "embedding_dim": 0,
            "total_docs": total_docs,
            "total_chunks": total_chunks,
            "total_vectors": total_vectors,
            "unvectorized_chunks": total_chunks - total_vectors,
            "vector_coverage_pct": pct,
            "docs_by_tier": {},
        }

    def _sql(self, query: str, params: tuple = ()) -> List[Any]:
        if self._db:
            with self._db._conn() as conn:
                return conn.execute(query, params).fetchall()
        elif self._conn:
            return self._conn.execute(query, params).fetchall()
        return []

    def _sql_one(self, query: str, params: tuple = ()) -> Optional[Any]:
        rows = self._sql(query, params)
        return rows[0] if rows else None

    def _scalar(self, query: str, params: tuple = ()) -> Any:
        row = self._sql_one(query, params)
        if row is None:
            return None
        # sqlite3.Row supports index access
        return row[0]

    def _execute(self, query: str, params: tuple = ()) -> None:
        if self._db:
            with self._db._conn() as conn:
                conn.execute(query, params)
        elif self._conn:
            self._conn.execute(query, params)
            self._conn.commit()

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _add(self, status: str, name: str, detail: str = "", data: Any = None) -> None:
        r = CheckResult(name, status, detail, data)
        self.results.append(r)
        if not self.quiet:
            print(_fmt(r))

    def _print_header(self) -> None:
        if self.quiet:
            return
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(_bold(f"\npxctx Vector Set Validator — {ts}"))
        print(f"  DB:      {self.db_path}")
        print(f"  Options: min_coverage={self.min_coverage_pct}%  strict={self.strict}  semantic={self.semantic_check}")
        print()


# ---------------------------------------------------------------------------
# Summary and exit code
# ---------------------------------------------------------------------------

def summarize(results: List[CheckResult], strict: bool = False) -> Tuple[int, str]:
    """Returns (exit_code, summary_line)."""
    passes  = sum(1 for r in results if r.status == Severity.PASS)
    warns   = sum(1 for r in results if r.status == Severity.WARN)
    fails   = sum(1 for r in results if r.status == Severity.FAIL)
    skips   = sum(1 for r in results if r.status in (Severity.SKIP, Severity.INFO))

    summary = f"PASS={passes}  WARN={warns}  FAIL={fails}  SKIP={skips}"

    if fails > 0:
        return 1, f"FAILED — {summary}"
    if warns > 0 and strict:
        return 1, f"FAILED (strict) — {summary}"
    if warns > 0:
        return 2, f"WARNINGS — {summary}"
    return 0, f"ALL CHECKS PASSED — {summary}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validate_vectorset",
        description="Validate pxctx vectorized document store integrity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--db",            type=str,   default=None,
                   help="Path to pxctx SQLite store (default: .pxctx/store.db)")
    p.add_argument("--min-coverage",  type=float, default=80.0, metavar="PCT",
                   help="Minimum vector coverage %% threshold (default: 80)")
    p.add_argument("--strict",        action="store_true",
                   help="Treat warnings as failures")
    p.add_argument("--semantic-check",action="store_true",
                   help="Run embedding round-trip check (requires sentence-transformers)")
    p.add_argument("--fix-orphans",   action="store_true",
                   help="Delete orphaned vectors/chunks")
    p.add_argument("--json",          action="store_true",
                   help="Output results as JSON")
    p.add_argument("--quiet",         action="store_true",
                   help="Suppress progress output (implies --json for useful output)")
    return p


def main() -> int:
    parser = build_parser()
    args   = parser.parse_args()

    if args.db:
        db_path = Path(args.db)
    elif _HAS_MODULE:
        db_path = DEFAULT_DB_PATH
    else:
        # Fallback: look for default location
        db_path = _REPO_ROOT / ".pxctx" / "store.db"

    validator = VectorSetValidator(
        db_path          = db_path,
        min_coverage_pct = args.min_coverage,
        strict           = args.strict,
        semantic_check   = args.semantic_check,
        fix_orphans      = args.fix_orphans,
        quiet            = args.quiet or args.json,
    )

    results = validator.run()
    exit_code, summary_line = summarize(results, strict=args.strict)

    if args.json:
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "db":        str(db_path),
            "checks":    [r.to_dict() for r in results],
            "summary":   summary_line,
            "exit_code": exit_code,
        }
        print(json.dumps(output, indent=2))
    else:
        print()
        print("─" * 60)
        color = _green if exit_code == 0 else (_yellow if exit_code == 2 else _red)
        print(color(_bold(f"Result: {summary_line}")))
        print()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
