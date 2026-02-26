Quick Start Guide
=================

Get started with the Little Free Library Toolkit in 5 minutes.

Installation
------------

.. code-block:: bash

   # From source
   git clone https://github.com/little-free-library/lfl
   cd lfl
   pip install -e .

   # With embedding support
   pip install -e ".[embeddings]"

   # Verify installation
   lfl version

Your First Corpus
-----------------

Step 1: Prepare Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a markdown document with your knowledge content:

.. code-block:: markdown

   # Python List Comprehensions

   List comprehensions provide a concise way to create lists...

   ## Syntax

   The basic syntax is:
   ```python
   [expression for item in iterable]
   ```

   ## Examples

   Simple list comprehension...

Step 2: Chunk the Document
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   lfl chunk document.md corpora/programming/chunks/ \\
     --domain programming \\
     --subdomain python \\
     --source "https://docs.python.org/3/tutorial/" \\
     --source-license PSF-2.0 \\
     --source-id python_docs

This creates corpus-ready chunks with complete YAML frontmatter metadata.

Step 3: Validate the Corpus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   lfl validate corpora/programming

Ensures all chunks have complete metadata and sources are documented.

Step 4: Test Retrieval Quality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   lfl benchmark run corpora/programming

Generates synthetic queries and measures retrieval quality with BM25.

Working with the API
--------------------

Chunking in Python
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lfl.chunking import chunk_document

   with open("document.md") as f:
       content = f.read()

   metadata = {
       "domain": "programming",
       "subdomain": "python",
       "source": "https://example.com",
       "source_license": "MIT",
       "source_id": "example_docs"
   }

   chunks = chunk_document(
       content=content,
       strategy="heading_aware",
       chunk_size=500,
       metadata=metadata
   )

   print(f"Created {len(chunks)} chunks")

Retrieval in Python
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lfl.retrieval import HybridRetriever

   retriever = HybridRetriever(
       corpus_dir="corpora/programming",
       mode="bm25"  # or "vector" or "hybrid"
   )

   results = retriever.retrieve("python list comprehension", top_k=5)

   for result in results:
       print(f"{result.title}: {result.score:.3f}")

Validation in Python
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lfl.corpus_validation import validate_corpus

   is_valid, valid_count, invalid_count, source_errors, orphaned = \\
       validate_corpus("corpora/programming", strict=False)

   if is_valid:
       print(f"✓ All {valid_count} chunks valid")
   else:
       print(f"✗ {invalid_count} invalid chunks")

Next Steps
----------

- Read the :doc:`modules/index` for complete API reference
- Explore :doc:`examples` for more advanced usage
- Check :doc:`cli` for all command-line options
- Review the `Contributors Documentation <../../contributors/>`_ for contribution guidelines
- Check the `CHANGELOG <../../CHANGELOG.md>`_ for latest features

Common Patterns
---------------

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from lfl.chunking import chunk_document, save_chunk_to_markdown

   input_dir = Path("raw_documents")
   output_dir = Path("corpora/programming/chunks")
   output_dir.mkdir(parents=True, exist_ok=True)

   for doc_path in input_dir.glob("*.md"):
       with open(doc_path) as f:
           content = f.read()
       
       chunks = chunk_document(content, strategy="heading_aware", metadata={...})
       
       for chunk in chunks:
           save_chunk_to_markdown(chunk, output_dir)
       
       print(f"Processed {doc_path.name}: {len(chunks)} chunks")

Custom Validation
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lfl.corpus_validation import validate_chunk

   chunk_data = {
       "title": "Python List Comprehensions",
       "domain": "programming",
       "source": "https://example.com",
       # ... other fields
   }

   errors = validate_chunk(chunk_data, "chunk_001.md")
   
   if not errors:
       print("✓ Chunk valid")
   else:
       for error in errors:
           print(f"✗ {error}")

Troubleshooting
---------------

Import Errors
~~~~~~~~~~~~~

If you see ``ModuleNotFoundError: No module named 'lfl'``:

.. code-block:: bash

   # Make sure you installed in editable mode
   pip install -e .

   # Or add to PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:/path/to/Little-Free-Library"

Embedding Backend Missing
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you see warnings about missing embedding backends:

.. code-block:: bash

   # Install FastEmbed (ONNX, works on CPU)
   pip install fastembed

   # Or sentence-transformers (PyTorch)
   pip install sentence-transformers

The toolkit will fall back to BM25-only mode if no embedding backend is available.

Validation Failures
~~~~~~~~~~~~~~~~~~~

If validation fails:

1. Check YAML frontmatter syntax (use ``---`` delimiters)
2. Ensure all required fields present (title, domain, source, license, etc.)
3. Verify source_id matches an entry in sources.json
4. Run with more verbose output to see specific errors

Getting Help
------------

- Check the `README <../../README.md>`_
- Review `QUICKSTART.md <../QUICKSTART.md>`_
- Open an issue on GitHub
- Join community discussions
