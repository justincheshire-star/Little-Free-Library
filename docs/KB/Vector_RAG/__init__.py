"""
Professor X Context System — 3-Tier Memory with Hybrid RAG Retrieval
=====================================================================

Tiers:
  treasure   — canonical truths; highest priority; never expire; requires CONFIRM to change
  working    — ephemeral session/task memory; strong recency weighting; default TTL 7d
  long-lived — durable KB + distilled notes; mild recency; repo-scoped

Retrieval:
  Hybrid FTS5 (BM25) + vector cosine similarity + deterministic reranking
"""

__version__ = "1.0.0"
__all__ = ["db", "embeddings", "chunking", "query"]
