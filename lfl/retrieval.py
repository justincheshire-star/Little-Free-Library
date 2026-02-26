"""
lfl.retrieval — Hybrid retrieval combining BM25 and vector similarity.

Supports:
- BM25 (lexical retrieval)
- Vector similarity (semantic retrieval)
- Hybrid (BM25 + vector with reciprocal rank fusion)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .validation import BM25, Chunk
from .embeddings import EmbeddingModel, cosine_similarity


RetrievalMode = Literal["bm25", "vector", "hybrid"]


@dataclass
class RetrievalResult:
    """Single retrieval result with score."""
    chunk_id: str
    chunk_idx: int
    score: float
    bm25_score: float = 0.0
    vector_score: float = 0.0
    rank: int = 0


class HybridRetriever:
    """
    Hybrid retrieval combining BM25 and vector similarity.
    
    Falls back to BM25-only if embeddings are not available.
    """
    
    def __init__(
        self,
        chunks: list[Chunk],
        profile_id: str = "baseline_cpu_onnx_small",
        mode: RetrievalMode = "hybrid",
    ):
        """
        Initialize retriever.
        
        Parameters
        ----------
        chunks : list[Chunk]
            Corpus chunks
        profile_id : str
            Embedding profile ID
        mode : RetrievalMode
            Retrieval mode (bm25, vector, or hybrid)
        """
        self.chunks = chunks
        self.mode = mode
        self.profile_id = profile_id
        
        # Initialize BM25
        self.bm25 = BM25([c.body for c in chunks])
        
        # Initialize embeddings if needed
        self.embedding_model = None
        self.chunk_embeddings = None
        
        if mode in ("vector", "hybrid"):
            try:
                self.embedding_model = EmbeddingModel(profile_id)
                if self.embedding_model.is_available:
                    self._embed_chunks()
                else:
                    # Fall back to BM25-only
                    if mode == "vector":
                        raise RuntimeError(
                            "Vector mode requires embeddings. Install 'fastembed' or 'sentence-transformers'."
                        )
                    self.mode = "bm25"
            except Exception as e:
                if mode == "vector":
                    raise RuntimeError(f"Failed to initialize embeddings: {e}") from e
                # For hybrid, fall back to BM25-only
                self.mode = "bm25"
    
    def _embed_chunks(self) -> None:
        """Pre-compute embeddings for all chunks."""
        texts = [c.body for c in self.chunks]
        self.chunk_embeddings = self.embedding_model.encode(texts, show_progress=True)
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.5,
    ) -> list[RetrievalResult]:
        """
        Retrieve top-k chunks for a query.
        
        Parameters
        ----------
        query : str
            Query text
        k : int
            Number of results to return
        alpha : float
            Weighting for hybrid mode (0 = BM25 only, 1 = vector only)
        
        Returns
        -------
        list[RetrievalResult]
            Top-k results sorted by score (descending)
        """
        if self.mode == "bm25":
            return self._retrieve_bm25(query, k)
        elif self.mode == "vector":
            return self._retrieve_vector(query, k)
        else:  # hybrid
            return self._retrieve_hybrid(query, k, alpha)
    
    def _retrieve_bm25(self, query: str, k: int) -> list[RetrievalResult]:
        """BM25 retrieval."""
        scores = self.bm25.get_scores(query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append(RetrievalResult(
                chunk_id=self.chunks[idx].chunk_id,
                chunk_idx=idx,
                score=float(scores[idx]),
                bm25_score=float(scores[idx]),
                rank=rank,
            ))
        
        return results
    
    def _retrieve_vector(self, query: str, k: int) -> list[RetrievalResult]:
        """Vector similarity retrieval."""
        # Encode query
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Compute similarities
        similarities = cosine_similarity(query_embedding, self.chunk_embeddings)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append(RetrievalResult(
                chunk_id=self.chunks[idx].chunk_id,
                chunk_idx=idx,
                score=float(similarities[idx]),
                vector_score=float(similarities[idx]),
                rank=rank,
            ))
        
        return results
    
    def _retrieve_hybrid(self, query: str, k: int, alpha: float) -> list[RetrievalResult]:
        """
        Hybrid retrieval using reciprocal rank fusion.
        
        Combines BM25 and vector rankings using RRF:
        score = alpha * vector_rrf + (1 - alpha) * bm25_rrf
        """
        # Get BM25 scores
        bm25_scores = self.bm25.get_scores(query)
        bm25_ranking = np.argsort(bm25_scores)[::-1]
        
        # Get vector scores
        query_embedding = self.embedding_model.encode([query])[0]
        vector_scores = cosine_similarity(query_embedding, self.chunk_embeddings)
        vector_ranking = np.argsort(vector_scores)[::-1]
        
        # Reciprocal Rank Fusion (RRF)
        k_rrf = 60  # RRF parameter
        rrf_scores = np.zeros(len(self.chunks))
        
        # Add BM25 RRF scores
        for rank, idx in enumerate(bm25_ranking):
            rrf_scores[idx] += (1 - alpha) / (k_rrf + rank + 1)
        
        # Add vector RRF scores
        for rank, idx in enumerate(vector_ranking):
            rrf_scores[idx] += alpha / (k_rrf + rank + 1)
        
        # Get top-k by RRF score
        top_indices = np.argsort(rrf_scores)[::-1][:k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append(RetrievalResult(
                chunk_id=self.chunks[idx].chunk_id,
                chunk_idx=idx,
                score=float(rrf_scores[idx]),
                bm25_score=float(bm25_scores[idx]),
                vector_score=float(vector_scores[idx]),
                rank=rank,
            ))
        
        return results
    
    @property
    def has_embeddings(self) -> bool:
        """Check if embeddings are available."""
        return self.chunk_embeddings is not None
