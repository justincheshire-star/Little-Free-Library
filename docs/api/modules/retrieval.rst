Retrieval Module
================

.. automodule:: lfl.retrieval
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The retrieval module provides hybrid retrieval combining BM25 lexical search with vector semantic search using Reciprocal Rank Fusion (RRF).

Retrieval Modes
---------------

BM25 (Lexical)
~~~~~~~~~~~~~~

Classic lexical retrieval using BM25 algorithm.

**Strengths:**
- Fast (no embedding inference needed)
- Works well for keyword/entity queries
- No external dependencies
- Deterministic results

**Weaknesses:**
- Misses semantic similarity
- Vocabulary mismatch issues
- No understanding of synonyms

Vector (Semantic)
~~~~~~~~~~~~~~~~~

Dense vector retrieval using embeddings.

**Strengths:**
- Captures semantic similarity
- Handles synonyms and paraphrases
- Works for conceptual queries
- Multi-lingual support

**Weaknesses:**
- Slower (requires embedding generation)
- Needs embedding backend installed
- Can miss exact keyword matches

Hybrid (Best of Both)
~~~~~~~~~~~~~~~~~~~~~

Combines BM25 + Vector using Reciprocal Rank Fusion.

**Strengths:**
- Balanced keyword + semantic matching
- Robust to different query types
- Often outperforms either alone
- Configurable BM25/vector weighting

**Weaknesses:**
- Requires embedding backend
- Slightly slower than BM25 alone
- More complex configuration

Example Usage
-------------

Basic Retrieval
~~~~~~~~~~~~~~~

.. code-block:: python

   from lfl.retrieval import HybridRetriever

   # Initialize retriever
   retriever = HybridRetriever(
       corpus_dir="corpora/programming",
       mode="hybrid",
       alpha=0.5,  # Equal weight to BM25 and vector
       profile_name="baseline_cpu_onnx_small"
   )

   # Search
   results = retriever.retrieve("python list comprehension", top_k=5)

   # Display results
   for i, result in enumerate(results, 1):
       print(f"{i}. {result.title} (score: {result.score:.3f})")
       print(f"   {result.snippet}...")
       print()

BM25-Only Retrieval
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # No embedding backend needed
   retriever = HybridRetriever(
       corpus_dir="corpora/programming",
       mode="bm25"  # Lexical only
   )

   results = retriever.retrieve("git branching strategy", top_k=10)

Vector-Only Retrieval
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Requires embedding backend (fastembed or sentence-transformers)
   retriever = HybridRetriever(
       corpus_dir="corpora/programming",
       mode="vector",
       profile_name="quality_cpu_onnx_base"  # Higher quality model
   )

   results = retriever.retrieve("explain big O notation", top_k=5)

Custom Alpha Weighting
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Favor BM25 (keyword matching)
   retriever_keyword = HybridRetriever(
       corpus_dir="corpora/programming",
       mode="hybrid",
       alpha=0.7  # 70% BM25, 30% vector
   )

   # Favor vector (semantic matching)
   retriever_semantic = HybridRetriever(
       corpus_dir="corpora/programming",
       mode="hybrid",
       alpha=0.3  # 30% BM25, 70% vector
   )

Advanced Usage
--------------

Batch Retrieval
~~~~~~~~~~~~~~~

.. code-block:: python

   queries = [
       "python list comprehension",
       "git branching best practices",
       "RESTful API design principles"
   ]

   retriever = HybridRetriever(corpus_dir="corpora/programming", mode="hybrid")

   for query in queries:
       results = retriever.retrieve(query, top_k=3)
       print(f"Query: {query}")
       for result in results:
           print(f"  - {result.title} ({result.score:.3f})")
       print()

Access Retrieval Scores
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   results = retriever.retrieve("python exceptions", top_k=5)

   for result in results:
       print(f"Chunk: {result.chunk_id}")
       print(f"  Final score: {result.score:.4f}")
       print(f"  BM25 score: {result.bm25_score:.4f}")
       print(f"  Vector score: {result.vector_score:.4f}")
       print(f"  Path: {result.file_path}")
       print()

Filter by Metadata
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Load corpus chunks first
   from lfl.validation import load_corpus_with_frontmatter

   corpus = load_corpus_with_frontmatter("corpora/programming")

   # Filter by domain/subdomain
   python_chunks = [
       chunk for chunk in corpus
       if chunk.get("subdomain") == "python"
   ]

   # Create retriever from filtered chunks
   # (Note: Would need to save filtered chunks to temp directory)

Embedding Profiles
------------------

The retrieval module uses embedding profiles for reproducible vector generation:

.. code-block:: python

   from lfl.profiles import list_profiles, load_profile

   # List available profiles
   profiles = list_profiles()
   print("Available profiles:", profiles)

   # Load specific profile
   profile = load_profile("power_user_cuda")
   print(f"Model: {profile['model_name']}")
   print(f"Dimensions: {profile['dimensions']}")

   # Use in retrieval
   retriever = HybridRetriever(
       corpus_dir="corpora/programming",
       mode="hybrid",
       profile_name="power_user_cuda"
   )

Performance Tips
----------------

1. **Cache embeddings**: Generate corpus embeddings once, reuse for multiple queries
2. **Use BM25 for keyword queries**: Faster and often sufficient
3. **Use hybrid for mixed queries**: Best overall performance
4. **Tune alpha parameter**: Test different BM25/vector weights for your domain
5. **Choose profile wisely**: Smaller models (384d) are often sufficient

Class Reference
---------------

.. autoclass:: lfl.retrieval.HybridRetriever
   :members:
   :special-members: __init__

.. autoclass:: lfl.retrieval.RetrievalResult
   :members:

.. autofunction:: lfl.retrieval.reciprocal_rank_fusion
