Chunking Module
===============

.. automodule:: lfl.chunking
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The chunking module provides strategies for converting raw documents into corpus-ready markdown chunks with complete metadata.

Chunking Strategies
-------------------

naive_paragraph
~~~~~~~~~~~~~~~

Split on double newlines (paragraphs), then pack to target chunk size.

**Use when:**
- Simple, unstructured text
- No clear hierarchical structure
- Fast processing needed

heading_aware (default)
~~~~~~~~~~~~~~~~~~~~~~~

Split at markdown headings to preserve document structure.

**Use when:**
- Technical documentation with headings
- Hierarchical content (h1, h2, h3)
- Semantic coherence important

sliding_window
~~~~~~~~~~~~~~

Fixed-size windows with configurable overlap.

**Use when:**
- Uniform chunk sizes needed
- Cross-sentence context important
- Dense information with no clear structure

semantic (experimental)
~~~~~~~~~~~~~~~~~~~~~~~

Semantic boundary detection using sentence embeddings.

**Use when:**
- Topic-based segmentation needed
- Content has subtle semantic shifts
- Quality over speed

Example Usage
-------------

Basic Chunking
~~~~~~~~~~~~~~

.. code-block:: python

   from lfl.chunking import chunk_document

   # Read document
   with open("document.md", "r") as f:
       content = f.read()

   # Define metadata
   metadata = {
       "domain": "programming",
       "subdomain": "python",
       "source": "https://docs.python.org/3/tutorial/",
       "source_license": "PSF-2.0",
       "source_id": "python_docs",
   }

   # Chunk with heading-aware strategy
   chunks = chunk_document(
       content=content,
       strategy="heading_aware",
       chunk_size=500,
       overlap=0,
       metadata=metadata
   )

   print(f"Created {len(chunks)} chunks")

Save Chunks to Disk
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lfl.chunking import chunk_document, save_chunk_to_markdown
   from pathlib import Path

   # Create chunks
   chunks = chunk_document(content, strategy="heading_aware", metadata=metadata)

   # Save to output directory
   output_dir = Path("corpora/programming/chunks")
   output_dir.mkdir(parents=True, exist_ok=True)

   for chunk in chunks:
       save_chunk_to_markdown(chunk, output_dir)

   print(f"Saved {len(chunks)} chunks to {output_dir}")

Custom Chunk Sizes
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Smaller chunks for precise retrieval
   small_chunks = chunk_document(
       content=content,
       strategy="heading_aware",
       chunk_size=300,
       min_chunk_size=50,
       max_chunk_size=400,
       metadata=metadata
   )

   # Larger chunks for more context
   large_chunks = chunk_document(
       content=content,
       strategy="sliding_window",
       chunk_size=800,
       overlap=100,
       metadata=metadata
   )

CLI Usage
---------

.. code-block:: bash

   # Basic chunking
   lfl chunk document.md output/

   # Specify strategy and chunk size
   lfl chunk document.md output/ --strategy heading_aware --chunk-size 600

   # Sliding window with overlap
   lfl chunk document.md output/ --strategy sliding_window --overlap 50

Function Reference
------------------

.. autofunction:: lfl.chunking.chunk_document

.. autofunction:: lfl.chunking.chunk_heading_aware

.. autofunction:: lfl.chunking.chunk_sliding_window

.. autofunction:: lfl.chunking.chunk_naive_paragraph

.. autofunction:: lfl.chunking.save_chunk_to_markdown

.. autofunction:: lfl.chunking.extract_title

.. autofunction:: lfl.chunking.generate_chunk_id
