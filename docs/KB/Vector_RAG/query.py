"""
query.py — Hybrid retrieval engine for pxctx.

Combines:
  - SQLite FTS5 (BM25) for lexical matching
  - Vector cosine similarity for semantic matching
  - Deterministic reranking with tier boost, recency, importance, verified, path, pin

Score formula:
    score = tier_boost
          + 2.0 × vector_similarity
          + 1.0 × fts_score          (normalized 0–1)
          + recency_boost × recency_score
          + 1.0 × importance
          + verified_bonus
          + path_match_bonus
          + pin_bonus

Retrieval priority: Treasure → Working → Long-lived
Token-budgeted packing: Treasure ≥25% budget, then Working+Long-lived by score.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from .db import Database, _normalize_tier, _parse_dt
from .embeddings import (
    deserialize_embedding,
    embedding_available,
    encode_query,
    vector_search,
)
from .chunking import estimate_tokens

# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------

TIER_BOOST = {"treasure": 10.0, "working": 5.0, "long_lived": 2.0}
RECENCY_BOOST_WORKING    = 0.3   # strong decay ~30d half-life
RECENCY_BOOST_LONG_LIVED = 0.1   # mild decay
RECENCY_BOOST_TREASURE   = 0.0   # timeless

VERIFIED_BONUS = {
    "documented": 0.3,
    "tested":     0.2,
    "observed":   0.1,
    "asserted":   0.05,
}

VECTOR_WEIGHT   = 2.0
FTS_WEIGHT      = 1.0
PIN_BONUS       = 0.5
PATH_BOOST      = 0.2

TREASURE_BUDGET_FRACTION = 0.25  # Guarantee ≥25% of token budget for Treasure

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HitRecord:
    """A single retrieved chunk with metadata and computed score."""
    chunk_id:   str
    doc_id:     str
    tier:       str
    score:      float
    title:      str
    snippet:    str
    heading:    str
    tags:       List[str]
    sources:    List[Dict]
    updated_at: str
    vec_score:  float = 0.0
    fts_score:  float = 0.0

    @property
    def ref(self) -> str:
        return f"memory://{self.doc_id}#{self.chunk_id}"

    def to_dict(self) -> Dict:
        return {
            "ref":        self.ref,
            "chunk_id":   self.chunk_id,
            "doc_id":     self.doc_id,
            "tier":       self.tier,
            "score":      round(self.score, 4),
            "vec_score":  round(self.vec_score, 4),
            "fts_score":  round(self.fts_score, 4),
            "title":      self.title,
            "heading":    self.heading,
            "snippet":    self.snippet,
            "tags":       self.tags,
            "sources":    self.sources,
            "updated_at": self.updated_at,
        }


@dataclass
class QueryResult:
    query_id: str
    packs: Dict[str, List[HitRecord]] = field(default_factory=lambda: {
        "treasure": [], "working": [], "long_lived": []
    })
    final: List[Dict] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Main query function
# ---------------------------------------------------------------------------

def query(
    db: Database,
    q: str,
    *,
    repo_id:    Optional[str] = None,
    session_id: Optional[str] = None,
    task_id:    Optional[str] = None,
    active_paths: Optional[List[str]] = None,
    treasure_k:   int = 12,
    working_k:    int = 18,
    long_lived_k: int = 18,
    final_n:      int = 12,
    max_tokens:   int = 1400,
    tags_any:     Optional[List[str]] = None,
) -> QueryResult:
    """
    Hybrid retrieval across all three tiers.

    Returns a QueryResult with per-tier hit lists and a token-budgeted
    final pack (Treasure-first).
    """
    query_id = f"Q-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"

    # Encode query vector (graceful degradation if model unavailable)
    query_emb = None
    if embedding_available() and q.strip():
        try:
            query_emb = encode_query(q)
        except Exception:
            query_emb = None

    stats: Dict[str, int] = {
        "vector_calls": 0,
        "fts_calls": 0,
        "deduped": 0,
        "returned": 0,
        "has_vectors": int(query_emb is not None),
    }

    # Retrieve per tier
    treasure_hits = _retrieve_tier(
        db, "treasure", q, query_emb,
        repo_id=repo_id, session_id=None, task_id=None,
        tags_any=tags_any, active_paths=active_paths or [],
        top_k=treasure_k,
        recency_boost=RECENCY_BOOST_TREASURE,
        verified_boost=False,
        stats=stats,
    )
    working_hits = _retrieve_tier(
        db, "working", q, query_emb,
        repo_id=repo_id, session_id=session_id, task_id=task_id,
        tags_any=tags_any, active_paths=active_paths or [],
        top_k=working_k,
        recency_boost=RECENCY_BOOST_WORKING,
        verified_boost=False,
        stats=stats,
    )
    long_lived_hits = _retrieve_tier(
        db, "long_lived", q, query_emb,
        repo_id=repo_id, session_id=None, task_id=None,
        tags_any=tags_any, active_paths=active_paths or [],
        top_k=long_lived_k,
        recency_boost=RECENCY_BOOST_LONG_LIVED,
        verified_boost=True,
        stats=stats,
    )

    # Token-budgeted packing: Treasure-first
    final, deduped = _pack_context(
        treasure_hits, working_hits, long_lived_hits,
        final_n=final_n,
        max_tokens=max_tokens,
    )

    stats["deduped"] = deduped
    stats["returned"] = len(final)

    return QueryResult(
        query_id=query_id,
        packs={
            "treasure":  treasure_hits,
            "working":   working_hits,
            "long_lived": long_lived_hits,
        },
        final=[h.to_dict() for h in final],
        stats=stats,
    )


# ---------------------------------------------------------------------------
# Per-tier retrieval
# ---------------------------------------------------------------------------

def _retrieve_tier(
    db: Database,
    tier: str,
    query_text: str,
    query_emb,
    *,
    repo_id:     Optional[str],
    session_id:  Optional[str],
    task_id:     Optional[str],
    tags_any:    Optional[List[str]],
    active_paths: List[str],
    top_k:        int,
    recency_boost: float,
    verified_boost: bool,
    stats:        Dict[str, int],
) -> List[HitRecord]:
    """
    Retrieve and score top_k candidates from a single tier.
    """
    tier = _normalize_tier(tier)

    # --- FTS search ---
    fts_raw = db.fts_search(query_text, tier=tier, limit=top_k * 2)
    stats["fts_calls"] += 1

    # Normalize FTS ranks (BM25 scores are negative; lower = better)
    raw_ranks = [abs(float(r.get("rank") or 0)) for r in fts_raw]
    max_rank = max(raw_ranks, default=0.0) or 1.0
    fts_scores: Dict[str, float] = {
        r["chunk_id"]: raw_ranks[i] / max_rank
        for i, r in enumerate(fts_raw)
    }

    # --- Candidate docs ---
    docs = db.get_docs_by_tier(
        tier,
        repo_id=repo_id,
        session_id=session_id,
        task_id=task_id,
        tags_any=tags_any,
        limit=top_k * 3,
    )

    # --- Collect chunks with vectors ---
    candidates = []
    for doc in docs:
        chunks = db.get_chunks(doc["doc_id"])
        for chunk in chunks:
            vec_data = db.get_vector(chunk["chunk_id"])
            candidates.append({
                "chunk_id":    chunk["chunk_id"],
                "doc_id":      doc["doc_id"],
                "chunk_text":  chunk["chunk_text"],
                "heading":     chunk.get("heading_path") or "",
                "vec_bytes":   vec_data,
                "doc":         doc,
            })

    # --- Vector search ---
    if query_emb is not None and candidates:
        stats["vector_calls"] += 1
        vec_pairs = [
            (c["chunk_id"], c["vec_bytes"])
            for c in candidates if c["vec_bytes"] is not None
        ]
        vec_results = vector_search(query_emb, vec_pairs, top_k=top_k * 2)
        vec_scores: Dict[str, float] = dict(vec_results)
    else:
        vec_scores = {}

    # --- Score each candidate ---
    now = datetime.now(timezone.utc)
    scored: List[HitRecord] = []

    for cand in candidates:
        chunk_id = cand["chunk_id"]
        doc      = cand["doc"]

        vec_score = vec_scores.get(chunk_id, 0.0)
        fts_score = fts_scores.get(chunk_id, 0.0)

        # Recency
        if recency_boost > 0:
            age_days = max(0.0, (now - _parse_dt(doc["created_at"])).total_seconds() / 86400)
            recency_score = 1.0 / (1.0 + age_days / 30.0)
        else:
            recency_score = 0.0

        # Verified bonus
        verified_score = 0.0
        if verified_boost and doc.get("verified"):
            verified_score = VERIFIED_BONUS.get(doc["verified"], 0.0)

        # Importance
        importance = float(doc.get("importance") or 0.5)

        # Active path boost
        path_boost = 0.0
        if active_paths:
            sources = doc.get("sources") or []
            if isinstance(sources, str):
                try:
                    sources = json.loads(sources)
                except Exception:
                    sources = []
            for src in sources:
                ref = str(src.get("ref", ""))
                if any(p in ref for p in active_paths):
                    path_boost = PATH_BOOST
                    break

        # Pin bonus
        pin_bonus = PIN_BONUS if doc.get("pin") else 0.0

        tier_boost = TIER_BOOST.get(tier, 0.0)

        score = (
            tier_boost
            + VECTOR_WEIGHT * vec_score
            + FTS_WEIGHT * fts_score
            + recency_boost * recency_score
            + importance
            + verified_score
            + path_boost
            + pin_bonus
        )

        tags = doc.get("tags") or []
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except Exception:
                tags = []

        srcs = doc.get("sources") or []
        if isinstance(srcs, str):
            try:
                srcs = json.loads(srcs)
            except Exception:
                srcs = []

        scored.append(HitRecord(
            chunk_id=chunk_id,
            doc_id=cand["doc_id"],
            tier=tier,
            score=score,
            title=doc.get("title") or "",
            snippet=cand["chunk_text"][:600],
            heading=cand["heading"],
            tags=tags,
            sources=srcs,
            updated_at=doc.get("updated_at") or doc.get("created_at") or "",
            vec_score=vec_score,
            fts_score=fts_score,
        ))

    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Context packing
# ---------------------------------------------------------------------------

def _pack_context(
    treasure_hits: List[HitRecord],
    working_hits:  List[HitRecord],
    long_lived_hits: List[HitRecord],
    *,
    final_n:    int,
    max_tokens: int,
) -> tuple[List[HitRecord], int]:
    """
    Pack a token-budgeted final context list.

    Rules:
      1. Treasure first; reserve ≥ TREASURE_BUDGET_FRACTION of max_tokens.
      2. Merge working + long_lived (sorted by score), fill remaining budget.
      3. Deduplicate by chunk_id.
      4. Hard cap: final_n items.

    Returns (final_pack, n_deduped).
    """
    seen_chunks: set[str] = set()
    final: List[HitRecord] = []
    total_tokens = 0
    deduped = 0

    min_treasure_tokens = int(max_tokens * TREASURE_BUDGET_FRACTION)

    # Pack Treasure (always include, up to min_treasure_tokens reservation)
    for hit in treasure_hits:
        if len(final) >= final_n:
            break
        if hit.chunk_id in seen_chunks:
            deduped += 1
            continue
        hit_tokens = estimate_tokens(hit.snippet)
        # Allow Treasure to always pack (ignore budget for Treasure)
        final.append(hit)
        seen_chunks.add(hit.chunk_id)
        total_tokens += hit_tokens

    # Merge remaining tiers by score
    remaining = sorted(
        working_hits + long_lived_hits,
        key=lambda h: h.score,
        reverse=True,
    )

    for hit in remaining:
        if len(final) >= final_n:
            break
        if hit.chunk_id in seen_chunks:
            deduped += 1
            continue
        hit_tokens = estimate_tokens(hit.snippet)
        if total_tokens + hit_tokens > max_tokens:
            continue  # Skip items that would blow the budget
        final.append(hit)
        seen_chunks.add(hit.chunk_id)
        total_tokens += hit_tokens

    return final, deduped


# ---------------------------------------------------------------------------
# Helper: format query result as human-readable string
# ---------------------------------------------------------------------------

def format_result(result: QueryResult, verbose: bool = False) -> str:
    lines = [
        f"Query ID: {result.query_id}",
        "",
        f"Treasure: {len(result.packs['treasure'])} hits",
        f"Working:  {len(result.packs['working'])} hits",
        f"Long-lived: {len(result.packs['long_lived'])} hits",
        f"Final packed: {len(result.final)} chunks",
        f"Stats: {json.dumps(result.stats)}",
        "",
        "Final Context Pack",
        "─" * 60,
    ]
    for i, item in enumerate(result.final, 1):
        tier_label = item["tier"].upper().replace("_", "-")
        lines.append(
            f"{i}. [{tier_label}] {item['title']}  "
            f"score={item['score']:.3f}"
        )
        if item.get("heading"):
            lines.append(f"   ↳ {item['heading']}")
        lines.append(f"   ref: {item['ref']}")
        snippet = item.get("snippet") or ""
        if verbose:
            lines.append(f"   {snippet}")
        else:
            lines.append(f"   {snippet[:120]}{'…' if len(snippet) > 120 else ''}")
        lines.append("")
    return "\n".join(lines)
