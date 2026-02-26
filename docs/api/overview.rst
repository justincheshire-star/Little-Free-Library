Overview
========

Little Free Library Toolkit (``lfl``) provides a complete solution for building, validating, and benchmarking knowledge corpora for Retrieval-Augmented Generation (RAG) systems.

Architecture
------------

The toolkit consists of five main components:

1. **Chunking Engine** — Convert documents into corpus-ready chunks
2. **Validation System** — Ensure corpus quality and metadata completeness
3. **Embedding Manager** — Generate and manage vector embeddings
4. **Retrieval Engine** — Multi-mode retrieval (BM25, vector, hybrid)
5. **Benchmarking Suite** — Automated quality assessment

Design Principles
-----------------

Modularity
~~~~~~~~~~

Each component is independent and can be used standalone or combined.

.. code-block:: python

   # Use just chunking
   from lfl.chunking import chunk_document

   # Use just retrieval
   from lfl.retrieval import HybridRetriever

   # Use full pipeline
   from lfl import chunk_document, validate_corpus, HybridRetriever

Reproducibility
~~~~~~~~~~~~~~~

Same inputs + same configuration = same outputs.

- Deterministic chunk IDs (content-based hashing)
- Profile-based embedding configuration
- Versioned corpus metadata
- Reproducible benchmark reports

Graceful Degradation
~~~~~~~~~~~~~~~~~~~~

Optional dependencies fail gracefully with helpful messages.

- BM25 works without embedding backends
- Validation works without external tools
- CLI provides clear fallback guidance

Format Agnostic
~~~~~~~~~~~~~~~

Works with any RAG framework.

- Standard markdown + YAML frontmatter
- Plain .npy embeddings (NumPy format)
- JSON benchmark reports
- No vendor lock-in

Core Concepts
-------------

Corpus
~~~~~~

A corpus is a domain-specific collection of knowledge chunks:

.. code-block:: text

   corpora/programming/
   ├── CORPUS.md          # Manifest (domain, version, sources)
   ├── sources.json       # Provenance (where content came from)
   ├── chunks/            # Pre-chunked content
   │   ├── chunk_001.md
   │   └── ...
   └── embeddings/        # Optional pre-computed embeddings
       └── vectors.npy

Chunk
~~~~~

A chunk is a self-contained unit of knowledge with complete metadata:

.. code-block:: yaml

   ---
   title: "Python List Comprehensions"
   domain: programming
   subdomain: python
   source: https://docs.python.org/3/tutorial/
   source_license: PSF-2.0
   source_id: python_docs
   chunk_tokens: 487
   content_hash: sha256:4b3a2f...
   ---

   # Python List Comprehensions

   List comprehensions provide a concise way...

Embedding Profile
~~~~~~~~~~~~~~~~~

A profile defines reproducible embedding configuration:

.. code-block:: json

   {
     "name": "baseline_cpu_onnx_small",
     "model_name": "nomic-embed-text-v1.5",
     "dimensions": 384,
     "max_seq_len": 512,
     "backend": "fastembed",
     "hardware": "cpu"
   }

Same profile = same vectors = reproducible builds.

Retrieval Mode
~~~~~~~~~~~~~~

Three retrieval modes with different trade-offs:

**BM25** (lexical)
   - Fast, no dependencies
   - Good for keyword queries
   - Misses semantic similarity

**Vector** (semantic)
   - Captures meaning
   - Handles synonyms
   - Requires embedding backend

**Hybrid** (combined)
   - Best of both worlds
   - Reciprocal Rank Fusion (RRF)
   - Configurable BM25/vector weighting

Data Flow
---------

Complete pipeline from raw documents to retrieval:

.. code-block:: text

   Raw Document
        ↓
   [Chunking] → metadata + chunk_id + frontmatter
        ↓
   Corpus Chunks (markdown)
        ↓
   [Validation] → check metadata completeness
        ↓
   Validated Corpus
        ↓
   [Embeddings] → generate vectors (optional)
        ↓
   Corpus + Embeddings
        ↓
   [Retrieval] → BM25 / vector / hybrid
        ↓
   Query Results

Each step is independent and can be run separately.

Package Structure
-----------------

.. code-block:: text

   lfl/
   ├── __init__.py              # Public API exports
   ├── chunking.py              # Document chunking strategies
   ├── corpus_validation.py     # Corpus validation engine
   ├── embeddings.py            # Vector embedding generation
   ├── retrieval.py             # Hybrid retrieval engine
   ├── profiles.py              # Embedding profile management
   ├── validation.py            # BM25 + validation utilities
   ├── benchmark.py             # Benchmark runner
   ├── query_gen.py             # Synthetic query generation
   ├── cli.py                   # Main CLI entry point
   ├── cli_benchmark.py         # Benchmark CLI commands
   └── profiles/                # Official embedding profiles
       ├── baseline_cpu_onnx_small.json
       ├── quality_cpu_onnx_base.json
       ├── power_user_cuda.json
       ├── power_user_rocm.json
       └── windows_gpu_directml.json

Dependencies
------------

Core (Required)
~~~~~~~~~~~~~~~

- **pyyaml** — YAML frontmatter parsing
- **numpy** — BM25 scoring, vector operations
- **typer** — CLI framework

Optional
~~~~~~~~

- **fastembed** — ONNX embeddings (CPU/GPU)
- **sentence-transformers** — PyTorch embeddings
- **tiktoken** — Accurate token counting (future)

Development
~~~~~~~~~~~

- **pytest** — Testing framework
- **black** — Code formatting
- **isort** — Import sorting
- **sphinx** — Documentation generation

Use Cases
---------

RAG Pipeline Development
~~~~~~~~~~~~~~~~~~~~~~~~

Build and validate knowledge bases for RAG systems.

IDE Agent Integration
~~~~~~~~~~~~~~~~~~~~~

Provide contextual code knowledge to IDE agents.

Documentation Search
~~~~~~~~~~~~~~~~~~~~

Create searchable documentation corpora.

Research Knowledge Bases
~~~~~~~~~~~~~~~~~~~~~~~~

Curate domain-specific research collections.

LLM Fine-tuning Data
~~~~~~~~~~~~~~~~~~~~

Prepare high-quality training data from validated corpora.

Performance
-----------

Typical performance on modern hardware:

- **Chunking**: 50-100 MB/s (heading_aware strategy)
- **Validation**: 1000-2000 chunks/s
- **BM25 retrieval**: <10ms for 1000 chunks
- **Vector retrieval**: 10-50ms depending on model/hardware
- **Hybrid retrieval**: 20-60ms (BM25 + vector)

Memory usage scales linearly with corpus size. For large corpora (>10K chunks), consider:

- Incremental validation
- Batch embedding generation
- Disk-based vector storage (future enhancement)

Versioning
----------

The toolkit follows `Semantic Versioning 2.0.0 <https://semver.org/>`_:

- **Major** (1.x.x) — Breaking API changes
- **Minor** (x.1.x) — New features, backward compatible
- **Patch** (x.x.1) — Bug fixes, backward compatible

Current version: **1.0.0**

See `CHANGELOG.md <../../CHANGELOG.md>`_ for detailed version history.

License
-------

The toolkit is licensed under **Apache 2.0 + Commons Clause**.

- **Free to use** for personal and commercial projects
- **Free to modify** and distribute
- **Cannot sell** as a standalone service without permission
- **Corpora** have separate licenses (see per-corpus CORPUS.md)

Community
---------

The Little Free Library project is community-driven:

- **Philosophy**: Knowledge as a commons
- **Values**: Openness, quality, accessibility
- **Goals**: Build the best free knowledge bases for AI

*Take what you need. Leave what you can.*

Next Steps
----------

- :doc:`quickstart` — Get started in 5 minutes
- :doc:`modules/index` — Complete API reference
- :doc:`cli` — Command-line interface
- `Contributors Guide <../../contributors/>`_ — Comprehensive contributor documentation
- `Contributing Guide <../../contributors/CONTRIBUTING_GUIDE.md>`_ — How to contribute
