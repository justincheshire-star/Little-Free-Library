.. _modules:

API Reference
=============

This section contains the complete API reference for all modules in the Little Free Library Toolkit.

Core Modules
------------

.. toctree::
   :maxdepth: 2

   chunking
   corpus_validation
   embeddings
   retrieval
   profiles

Reference Implementations
-------------------------

.. toctree::
   :maxdepth: 2

   validation
   benchmark
   query_gen

CLI Modules
-----------

.. toctree::
   :maxdepth: 2

   cli
   cli_benchmark

Module Overview
---------------

Chunking Module
~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated

   lfl.chunking.chunk_document
   lfl.chunking.chunk_heading_aware
   lfl.chunking.chunk_sliding_window
   lfl.chunking.chunk_naive_paragraph
   lfl.chunking.save_chunk_to_markdown

Corpus Validation Module
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated

   lfl.corpus_validation.validate_corpus
   lfl.corpus_validation.validate_chunk
   lfl.corpus_validation.validate_sources_json
   lfl.corpus_validation.check_source_references

Embeddings Module
~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated

   lfl.embeddings.EmbeddingModel
   lfl.embeddings.cosine_similarity
   lfl.embeddings.save_embeddings
   lfl.embeddings.load_embeddings

Retrieval Module
~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated

   lfl.retrieval.HybridRetriever
   lfl.retrieval.RetrievalResult

Profiles Module
~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: generated

   lfl.profiles.load_profile
   lfl.profiles.list_profiles
   lfl.profiles.get_default_profile
