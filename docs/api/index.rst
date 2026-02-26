.. Little Free Library Toolkit documentation master file

Little Free Library Toolkit API Reference
==========================================

**Version:** 1.0.0

The Little Free Library Toolkit (``lfl``) is a comprehensive Python package for building, validating, and benchmarking knowledge corpora for RAG (Retrieval-Augmented Generation) systems.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   quickstart
   modules/index
   cli
   examples

Features
--------

- **Document Chunking** — Convert raw documents into corpus-ready chunks with multiple strategies
- **Corpus Validation** — Comprehensive validation of structure, metadata, and provenance
- **Vector Embeddings** — Multi-backend support (FastEmbed, sentence-transformers)
- **Hybrid Retrieval** — BM25, vector, and hybrid retrieval modes
- **Benchmarking** — Automated quality assessment with synthetic queries
- **CLI Interface** — User-friendly command-line tools

Quick Links
-----------

- :doc:`quickstart` — Get started in 5 minutes
- :doc:`modules/chunking` — Document chunking module
- :doc:`modules/validation` — Corpus validation module
- :doc:`modules/retrieval` — Hybrid retrieval module
- :doc:`cli` — Command-line interface reference

Installation
------------

.. code-block:: bash

   # Install from source
   pip install -e .

   # Install with embedding support
   pip install -e ".[embeddings]"

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
