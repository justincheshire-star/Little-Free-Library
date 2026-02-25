"""
pxctx.py — Click CLI entry point for the Professor X Context System.

Invoked via:
  python -m Vector_RAG <command> [options]   (PYTHONPATH=docs/KB)
  ./pxctx <command> [options]                (bash wrapper at repo root)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import click

from .db import Database, _make_id, _now, _repo_id, _normalize_tier, DEFAULT_DB_PATH
from .chunking import chunk_with_counts
from . import query as _query_mod
from .embeddings import (
    embedding_available,
    encode,
    serialize_embedding,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(os.environ.get("PXCTX_ROOT", Path(__file__).parent.parent.parent.parent))

VALID_TYPES = (
    "decision", "constraint", "finding", "plan_step",
    "command_summary", "kb_doc", "distilled_note",
    "security_rule", "architecture", "invariant", "checkpoint", "note",
)

VALID_TIERS = ("treasure", "working", "long_lived", "long-lived")


def _db() -> Database:
    return Database(DEFAULT_DB_PATH)


def _env_repo() -> str:
    return os.environ.get("PXCTX_REPO_ID", _repo_id(_REPO_ROOT))


def _env_session() -> Optional[str]:
    return os.environ.get("PXCTX_SESSION_ID")


def _env_task() -> Optional[str]:
    return os.environ.get("PXCTX_TASK_ID")


def _index_doc(db: Database, doc_id: str, content: str, is_markdown: bool = False) -> int:
    """Chunk and embed a document. Returns number of chunks created."""
    from .embeddings import embedding_available, encode, serialize_embedding

    chunks_data = chunk_with_counts(content, is_markdown=is_markdown)

    chunk_ids = []
    texts = []
    for heading, chunk_text, tokens in chunks_data:
        cid = db.add_chunk(doc_id, len(chunk_ids), chunk_text, tokens, heading)
        chunk_ids.append(cid)
        texts.append(chunk_text)

    # Embed if available
    if embedding_available() and texts:
        try:
            embeddings = encode(texts, show_progress=False)
            for cid, emb in zip(chunk_ids, embeddings):
                db.add_vector(cid, serialize_embedding(emb))
        except Exception as e:
            click.echo(f"  [warn] Embedding failed (FTS only): {e}", err=True)

    return len(chunk_ids)


# ---------------------------------------------------------------------------
# CLI root
# ---------------------------------------------------------------------------

@click.group()
@click.version_option("1.0.0", prog_name="pxctx")
def cli():
    """Professor X Context System — 3-tier RAG memory for AI agents."""
    pass


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

@cli.command("add")
@click.option("--tier",     required=True,  type=click.Choice(["treasure","working","long_lived","long-lived"]))
@click.option("--type",     "type_",        default="note", show_default=True,
              type=click.Choice(VALID_TYPES))
@click.option("--title",    default="",     help="Document title (auto-generated from content if empty)")
@click.option("--text",     default="",     help="Content text")
@click.option("--file",     "file_path",    default=None, type=click.Path(exists=True),
              help="Read content from file (overrides --text)")
@click.option("--summary",  default=None)
@click.option("--repo",     default=None)
@click.option("--session",  default=None)
@click.option("--task",     default=None)
@click.option("--tags",     default="",     help="Comma-separated tags")
@click.option("--source-kind", default="", help="Source type (file, command, manual, ...)")
@click.option("--source-ref",  default="", help="Source reference (path, URL, command, ...)")
@click.option("--importance", default=0.5, type=float, show_default=True)
@click.option("--verified",   default=None,
              type=click.Choice(["asserted","observed","tested","documented"]))
@click.option("--pin/--no-pin",             default=False)
@click.option("--never-expire/--ttl",       default=False)
@click.option("--ttl-days",  default=None,  type=float)
@click.option("--on-duplicate", default="update",
              type=click.Choice(["update","skip","error"]), show_default=True)
@click.option("--no-chunk",  is_flag=True,  default=False,
              help="Store as a single chunk (no splitting)")
def cmd_add(tier, type_, title, text, file_path, summary, repo, session, task,
            tags, source_kind, source_ref, importance, verified, pin,
            never_expire, ttl_days, on_duplicate, no_chunk):
    """Add a document to the context store (with chunking + embedding)."""
    if file_path:
        text = Path(file_path).read_text(encoding="utf-8")
        if not title:
            title = Path(file_path).name

    if not text.strip():
        raise click.UsageError("Provide --text or --file")

    if not title:
        title = text.strip()[:60].replace("\n", " ") + ("…" if len(text) > 60 else "")

    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    sources_list = []
    if source_kind or source_ref:
        sources_list = [{"kind": source_kind, "ref": source_ref}]

    is_md = (file_path or "").endswith(".md") or "# " in text[:200]

    db = _db()
    doc_id = db.add_doc(
        tier=tier,
        title=title,
        content=text,
        type_=type_,
        repo_id=repo or _env_repo(),
        session_id=session or _env_session(),
        task_id=task or _env_task(),
        tags=tags_list,
        sources=sources_list,
        importance=importance,
        verified=verified,
        pin=pin,
        never_expire=never_expire,
        ttl_days=ttl_days,
        on_duplicate=on_duplicate,
    )

    n_chunks = 0
    if not no_chunk:
        n_chunks = _index_doc(db, doc_id, text, is_markdown=is_md)

    click.echo(json.dumps({
        "ok": True,
        "id": doc_id,
        "tier": tier,
        "chunks": n_chunks,
        "vectors": n_chunks if embedding_available() else 0,
    }))


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------

@cli.command("query")
@click.argument("query_text", default="")
@click.option("--repo",         default=None)
@click.option("--session",      default=None)
@click.option("--task",         default=None)
@click.option("--active",       default="",    help="Comma-separated active file paths")
@click.option("--treasure-k",   default=12,    type=int, show_default=True)
@click.option("--working-k",    default=18,    type=int, show_default=True)
@click.option("--long-lived-k", default=18,    type=int, show_default=True)
@click.option("--final-n",      default=12,    type=int, show_default=True)
@click.option("--max-tokens",   default=1400,  type=int, show_default=True)
@click.option("--tags",         default="",    help="Filter by tags (comma-separated)")
@click.option("--json-output",  is_flag=True,  default=False)
@click.option("--verbose",      is_flag=True,  default=False)
def cmd_query(query_text, repo, session, task, active, treasure_k, working_k,
              long_lived_k, final_n, max_tokens, tags, json_output, verbose):
    """Hybrid retrieval: vector + FTS, tier-ordered context packing."""
    db = _db()
    active_paths = [p.strip() for p in active.split(",") if p.strip()]
    tags_any = [t.strip() for t in tags.split(",") if t.strip()] or None

    result = _query_mod.query(
        db,
        query_text,
        repo_id=repo or _env_repo(),
        session_id=session or _env_session(),
        task_id=task or _env_task(),
        active_paths=active_paths,
        treasure_k=treasure_k,
        working_k=working_k,
        long_lived_k=long_lived_k,
        final_n=final_n,
        max_tokens=max_tokens,
        tags_any=tags_any,
    )

    if json_output:
        out = {
            "query_id": result.query_id,
            "packs": {
                k: [h.to_dict() for h in v] for k, v in result.packs.items()
            },
            "final": result.final,
            "stats": result.stats,
        }
        click.echo(json.dumps(out, indent=2))
    else:
        click.echo(_query_mod.format_result(result, verbose=verbose))


# ---------------------------------------------------------------------------
# promote
# ---------------------------------------------------------------------------

@cli.command("promote")
@click.option("--doc",  "doc_id", required=True, help="Document ID to promote")
@click.option("--to",   "to_tier", required=True,
              type=click.Choice(["treasure","working","long_lived","long-lived"]))
@click.option("--pin/--no-pin",           default=False)
@click.option("--never-expire/--expire",  default=False)
def cmd_promote(doc_id, to_tier, pin, never_expire):
    """Promote (or demote) a document to a different tier."""
    if to_tier == "treasure":
        click.echo("⚠  Promoting to Treasure requires user CONFIRM.", err=True)
        if not click.confirm("Are you sure? (CONFIRM)"):
            raise click.Abort()

    db = _db()
    ok = db.promote_to_tier(doc_id, to_tier, pin=pin, never_expire=never_expire)
    if ok:
        click.echo(json.dumps({"ok": True, "doc_id": doc_id, "to_tier": to_tier}))
    else:
        click.echo(json.dumps({"ok": False, "error": f"doc not found: {doc_id}"}))
        sys.exit(1)


# ---------------------------------------------------------------------------
# supersede
# ---------------------------------------------------------------------------

@cli.command("supersede")
@click.option("--doc",        "doc_id",  required=True, help="New document ID")
@click.option("--supersedes", "old_ids", required=True,
              help="Comma-separated doc_ids that this document supersedes")
def cmd_supersede(doc_id, old_ids):
    """Mark one or more old documents as superseded by a new one."""
    old_list = [x.strip() for x in old_ids.split(",") if x.strip()]
    db = _db()
    ok = db.supersede_doc(doc_id, old_list)
    click.echo(json.dumps({"ok": ok, "doc_id": doc_id, "supersedes": old_list}))


# ---------------------------------------------------------------------------
# gc
# ---------------------------------------------------------------------------

@cli.command("gc")
@click.option("--dry-run", is_flag=True, default=False)
def cmd_gc(dry_run):
    """Garbage collect expired documents (by TTL)."""
    db = _db()
    if dry_run:
        # Replicate the logic without deleting
        from datetime import timedelta, timezone
        from .db import _parse_dt
        from datetime import datetime
        now = datetime.now(timezone.utc)
        with db._conn() as conn:
            rows = conn.execute(
                "SELECT doc_id, created_at, ttl_days FROM docs WHERE never_expire=0 AND ttl_days IS NOT NULL"
            ).fetchall()
        would_delete = []
        for row in rows:
            created = _parse_dt(row["created_at"])
            if now > created + timedelta(days=row["ttl_days"]):
                would_delete.append(row["doc_id"])
        click.echo(json.dumps({"dry_run": True, "would_delete": would_delete, "count": len(would_delete)}))
    else:
        deleted = db.gc_expired()
        click.echo(json.dumps({"ok": True, "deleted": deleted, "count": len(deleted)}))


# ---------------------------------------------------------------------------
# compact
# ---------------------------------------------------------------------------

@cli.command("compact")
@click.option("--session", default=None, help="Session ID (or $PXCTX_SESSION_ID)")
@click.option("--title",   default="",   help="Title for the distilled note")
@click.option("--to",      "to_tier", default="long_lived",
              type=click.Choice(["long_lived","long-lived","working"]))
@click.option("--repo",    default=None)
def cmd_compact(session, title, to_tier, repo):
    """Compact Working docs from a session into a single Long-lived distilled note."""
    session_id = session or _env_session()
    if not session_id:
        raise click.UsageError("Provide --session or set $PXCTX_SESSION_ID")

    db = _db()
    docs = db.get_docs_by_tier("working", session_id=session_id)

    if not docs:
        click.echo(json.dumps({"ok": True, "message": "No working docs to compact", "session_id": session_id}))
        return

    combined = "\n\n---\n\n".join(
        f"## [{d['type']}] {d['title']}\n\n{d['content']}" for d in docs
    )
    auto_title = title or f"Compacted session {session_id[:20]} ({len(docs)} items)"
    full_text = f"# Distilled Note\n\nCompacted {len(docs)} working items from session `{session_id}`.\n\n---\n\n{combined}"

    new_id = db.add_doc(
        tier=_normalize_tier(to_tier),
        title=auto_title,
        content=full_text,
        type_="distilled_note",
        repo_id=repo or _env_repo(),
        session_id=session_id,
        tags=["compacted", f"session:{session_id[:12]}"],
    )
    n_chunks = _index_doc(db, new_id, full_text, is_markdown=True)

    # Supersede the originals
    orig_ids = [d["doc_id"] for d in docs]
    db.supersede_doc(new_id, orig_ids)

    click.echo(json.dumps({
        "ok": True,
        "compacted_id": new_id,
        "source_count": len(docs),
        "chunks": n_chunks,
        "session_id": session_id,
    }))


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------

@cli.command("ingest")
@click.argument("path", type=click.Path(exists=True))
@click.option("--tier",       default="long_lived",
              type=click.Choice(["treasure","working","long_lived","long-lived"]))
@click.option("--type",       "type_",  default="kb_doc",
              type=click.Choice(VALID_TYPES))
@click.option("--repo",       default=None)
@click.option("--tags",       default="kb", help="Comma-separated tags")
@click.option("--recursive",  is_flag=True, default=False)
@click.option("--pattern",    default="*.md", show_default=True)
@click.option("--on-duplicate", default="update",
              type=click.Choice(["update","skip","error"]), show_default=True)
@click.option("--importance", default=0.6, type=float, show_default=True)
@click.option("--verified",   default="documented",
              type=click.Choice(["asserted","observed","tested","documented"]))
def cmd_ingest(path, tier, type_, repo, tags, recursive, pattern, on_duplicate,
               importance, verified):
    """Bulk ingest KB markdown (or other text) files."""
    root = Path(path)
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    if root.is_file():
        files = [root]
    else:
        glob_fn = root.rglob if recursive else root.glob
        files = sorted(glob_fn(pattern))

    db = _db()
    results = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            doc_id = db.add_doc(
                tier=tier,
                title=f.name,
                content=text,
                type_=type_,
                repo_id=repo or _env_repo(),
                tags=tags_list + ["ingested"],
                sources=[{"kind": "file", "ref": str(f.relative_to(_REPO_ROOT))}],
                importance=importance,
                verified=verified,
                never_expire=(tier == "treasure"),
                on_duplicate=on_duplicate,
            )
            is_md = f.suffix == ".md"
            n = _index_doc(db, doc_id, text, is_markdown=is_md)
            results.append({"file": str(f), "doc_id": doc_id, "chunks": n})
            click.echo(f"  ✓  {f.relative_to(_REPO_ROOT)}  → {doc_id}  [{n} chunks]")
        except Exception as exc:
            click.echo(f"  ✗  {f}: {exc}", err=True)
            results.append({"file": str(f), "error": str(exc)})

    click.echo(f"\nIngested {sum(1 for r in results if 'error' not in r)}/{len(results)} files.")


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

@cli.command("stats")
@click.option("--json-output", is_flag=True, default=False)
def cmd_stats(json_output):
    """Show context store statistics."""
    db = _db()
    s = db.get_stats()

    if json_output:
        click.echo(json.dumps(s, indent=2))
        return

    click.echo("Professor X Context System Stats")
    click.echo("─" * 40)
    click.echo(f"Schema version:    {s['schema_version']}")
    click.echo(f"Embedding model:   {s['embedding_model']}")
    click.echo(f"Embedding dim:     {s['embedding_dim']}")
    click.echo(f"Vector embeddings: {'✓ available' if embedding_available() else '✗ unavailable (FTS-only mode)'}")
    click.echo("")
    click.echo(f"Total docs:        {s['total_docs']}")
    click.echo(f"Total chunks:      {s['total_chunks']}")
    click.echo(f"Total vectors:     {s['total_vectors']}")
    click.echo(f"Unvectorized:      {s['unvectorized_chunks']}")
    click.echo(f"Vector coverage:   {s['vector_coverage_pct']}%")
    click.echo("")
    click.echo("Tier Breakdown:")
    for tier in ("treasure", "working", "long_lived"):
        cnt = s["docs_by_tier"].get(tier, 0)
        click.echo(f"  {tier.upper():<12} {cnt} doc(s)")


# ---------------------------------------------------------------------------
# get / list / session commands
# ---------------------------------------------------------------------------

@cli.command("get")
@click.argument("doc_id")
def cmd_get(doc_id):
    """Get a document by ID."""
    db = _db()
    doc = db.get_doc(doc_id)
    if doc is None:
        click.echo(json.dumps({"error": f"not found: {doc_id}"}))
        sys.exit(1)
    click.echo(json.dumps(doc, indent=2, default=str))


@cli.command("list")
@click.option("--tier",    default=None, type=click.Choice(["treasure","working","long_lived","long-lived"]))
@click.option("--session", default=None)
@click.option("--limit",   default=20, type=int, show_default=True)
def cmd_list(tier, session, limit):
    """List documents (newest first)."""
    db = _db()
    docs = db.get_docs_by_tier(
        tier or "working",
        session_id=session,
        limit=limit,
    ) if tier or session else []

    if not tier and not session:
        # All tiers
        all_docs = []
        for t in ("treasure", "working", "long_lived"):
            all_docs.extend(db.get_docs_by_tier(t, limit=limit))
        all_docs.sort(key=lambda d: d.get("created_at") or "", reverse=True)
        docs = all_docs[:limit]

    out = [
        {
            "doc_id": d["doc_id"],
            "tier":   d["tier"],
            "type":   d["type"],
            "title":  d["title"][:80],
            "tags":   d.get("tags") or [],
            "created_at": d.get("created_at"),
        }
        for d in docs
    ]
    click.echo(json.dumps(out, indent=2, default=str))


@cli.command("session-new")
@click.argument("description", default="")
@click.option("--repo", default=None)
def cmd_session_new(description, repo):
    """Create a new session and print session/task IDs."""
    session_id = _make_id("sess")
    task_id    = _make_id("task")
    repo_id    = repo or _env_repo()
    db = _db()
    db.create_session(session_id, task_id, description, repo_id)
    click.echo(json.dumps({
        "session_id":  session_id,
        "task_id":     task_id,
        "repo_id":     repo_id,
        "description": description,
    }))


@cli.command("session-update")
@click.option("--session-id",   default=None)
@click.option("--state",        default=None, type=click.Choice(["active","wrapped"]))
@click.option("--description",  default=None)
def cmd_session_update(session_id, state, description):
    """Update a session's state or description."""
    sid = session_id or _env_session()
    if not sid:
        raise click.UsageError("Provide --session-id or set $PXCTX_SESSION_ID")
    db = _db()
    db.update_session(sid, state=state, description=description)
    click.echo(json.dumps({"ok": True, "session_id": sid}))


if __name__ == "__main__":
    cli()
