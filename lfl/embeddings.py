"""
lfl.embeddings — Vector embedding generation and management.

Supports multiple embedding backends with graceful fallbacks:
1. FastEmbed (ONNX-based, lightweight, recommended)
2. sentence-transformers (fallback)
3. None (BM25-only mode)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal
import warnings

import numpy as np

from .profiles import EmbeddingProfile, load_profile


EmbeddingBackend = Literal["fastembed", "sentence-transformers", "none"]


class EmbeddingModel:
    """
    Wrapper for embedding models with multiple backend support.
    
    Gracefully degrades if embedding libraries are not available.
    """
    
    def __init__(
        self,
        profile_id: str = "baseline_cpu_onnx_small",
        backend: EmbeddingBackend | None = None,
    ):
        """
        Initialize embedding model.
        
        Parameters
        ----------
        profile_id : str
            Embedding profile ID
        backend : EmbeddingBackend, optional
            Force specific backend (auto-detects if None)
        """
        self.profile = load_profile(profile_id)
        self.backend = backend or self._detect_backend()
        self.model = None
        
        if self.backend != "none":
            self._load_model()
    
    def _detect_backend(self) -> EmbeddingBackend:
        """Detect available embedding backend."""
        try:
            import fastembed
            return "fastembed"
        except ImportError:
            pass
        
        try:
            import sentence_transformers
            return "sentence-transformers"
        except ImportError:
            pass
        
        warnings.warn(
            "No embedding library found. Install 'fastembed' or 'sentence-transformers'. "
            "Falling back to BM25-only mode.",
            RuntimeWarning
        )
        return "none"
    
    def _load_model(self) -> None:
        """Load the embedding model based on backend."""
        if self.backend == "fastembed":
            self._load_fastembed()
        elif self.backend == "sentence-transformers":
            self._load_sentence_transformers()
    
    def _load_fastembed(self) -> None:
        """Load model using FastEmbed."""
        try:
            from fastembed import TextEmbedding
            
            # FastEmbed uses model names directly
            model_name = self.profile.model_name
            if hasattr(self.profile, 'fastembed_model_id'):
                model_name = getattr(self.profile, 'fastembed_model_id')
            
            self.model = TextEmbedding(
                model_name=model_name,
                max_length=self.profile.max_seq_len,
            )
        except Exception as e:
            warnings.warn(f"Failed to load FastEmbed model: {e}. Falling back to BM25-only.", RuntimeWarning)
            self.backend = "none"
            self.model = None
    
    def _load_sentence_transformers(self) -> None:
        """Load model using sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            
            self.model = SentenceTransformer(self.profile.model_name)
        except Exception as e:
            warnings.warn(f"Failed to load sentence-transformers model: {e}. Falling back to BM25-only.", RuntimeWarning)
            self.backend = "none"
            self.model = None
    
    def encode(
        self,
        texts: list[str] | str,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode texts to vectors.
        
        Parameters
        ----------
        texts : list[str] or str
            Text(s) to encode
        batch_size : int
            Batch size for encoding
        show_progress : bool
            Show progress bar
        
        Returns
        -------
        np.ndarray
            Embeddings array of shape (n_texts, dimensions)
        
        Raises
        ------
        RuntimeError
            If no embedding backend is available
        """
        if self.backend == "none":
            raise RuntimeError(
                "No embedding model available. Install 'fastembed' or 'sentence-transformers'."
            )
        
        if isinstance(texts, str):
            texts = [texts]
        
        if self.backend == "fastembed":
            return self._encode_fastembed(texts, batch_size)
        elif self.backend == "sentence-transformers":
            return self._encode_sentence_transformers(texts, batch_size, show_progress)
        
        raise RuntimeError(f"Unknown backend: {self.backend}")
    
    def _encode_fastembed(self, texts: list[str], batch_size: int) -> np.ndarray:
        """Encode using FastEmbed."""
        # FastEmbed returns generator, collect results
        embeddings = list(self.model.embed(texts, batch_size=batch_size))
        return np.array(embeddings)
    
    def _encode_sentence_transformers(
        self,
        texts: list[str],
        batch_size: int,
        show_progress: bool,
    ) -> np.ndarray:
        """Encode using sentence-transformers."""
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
    
    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self.profile.dimensions
    
    @property
    def is_available(self) -> bool:
        """Check if embedding model is available."""
        return self.backend != "none"


def embed_chunks(
    chunks: list[str],
    profile_id: str = "baseline_cpu_onnx_small",
    batch_size: int = 32,
    show_progress: bool = True,
) -> np.ndarray:
    """
    Convenience function to embed a list of chunks.
    
    Parameters
    ----------
    chunks : list[str]
        Texts to embed
    profile_id : str
        Embedding profile ID
    batch_size : int
        Batch size for encoding
    show_progress : bool
        Show progress bar
    
    Returns
    -------
    np.ndarray
        Embeddings array of shape (n_chunks, dimensions)
    """
    model = EmbeddingModel(profile_id)
    return model.encode(chunks, batch_size=batch_size, show_progress=show_progress)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between vectors.
    
    Parameters
    ----------
    a : np.ndarray
        First vector(s), shape (n, d) or (d,)
    b : np.ndarray
        Second vector(s), shape (m, d) or (d,)
    
    Returns
    -------
    np.ndarray
        Similarity matrix of shape (n, m) or scalar
    """
    # Ensure 2D
    if a.ndim == 1:
        a = a.reshape(1, -1)
    if b.ndim == 1:
        b = b.reshape(1, -1)
    
    # Normalize
    a_norm = a / np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    
    # Compute similarity
    similarity = np.dot(a_norm, b_norm.T)
    
    # Return scalar if both inputs were 1D
    if similarity.shape == (1, 1):
        return similarity[0, 0]
    
    return similarity


def save_embeddings(embeddings: np.ndarray, output_path: Path) -> None:
    """
    Save embeddings to disk.
    
    Parameters
    ----------
    embeddings : np.ndarray
        Embeddings array
    output_path : Path
        Output file path (will be saved as .npy)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, embeddings)


def load_embeddings(input_path: Path) -> np.ndarray:
    """
    Load embeddings from disk.
    
    Parameters
    ----------
    input_path : Path
        Input file path (.npy file)
    
    Returns
    -------
    np.ndarray
        Loaded embeddings
    """
    return np.load(input_path)
