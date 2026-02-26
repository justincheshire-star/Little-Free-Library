Command-Line Interface
======================

The ``lfl`` command-line interface provides tools for chunking, validating, and benchmarking knowledge corpora.

Installation
------------

.. code-block:: bash

   # Install from source
   pip install -e .

   # Verify installation
   lfl version

Commands Overview
-----------------

.. code-block:: text

   lfl chunk        Convert documents to corpus chunks
   lfl validate     Validate corpus structure and metadata
   lfl benchmark    Test retrieval quality (run, sweep, compare)
   lfl version      Show toolkit version

lfl chunk
---------

Convert raw documents into corpus-ready markdown chunks with complete metadata.

Syntax
~~~~~~

.. code-block:: bash

   lfl chunk INPUT_FILE OUTPUT_DIR [OPTIONS]

Arguments
~~~~~~~~~

- ``INPUT_FILE`` — Path to input document (markdown format)
- ``OUTPUT_DIR`` — Directory to save generated chunks

Options
~~~~~~~

.. code-block:: text

   --strategy TEXT         Chunking strategy [default: heading_aware]
                          Choices: naive_paragraph, heading_aware,
                                   sliding_window, semantic

   --chunk-size INTEGER    Target chunk size in tokens [default: 500]

   --overlap INTEGER       Overlap between chunks (for sliding_window)
                          [default: 0]

   --min-chunk-size INTEGER  Minimum chunk size [default: 50]

   --max-chunk-size INTEGER  Maximum chunk size [default: 1000]

   --domain TEXT          Document domain (e.g., programming)

   --subdomain TEXT       Document subdomain (e.g., python)

   --source TEXT          Source URL

   --source-license TEXT  Source license (e.g., CC-BY-SA-4.0)

   --source-id TEXT       Source identifier matching sources.json

Examples
~~~~~~~~

.. code-block:: bash

   # Basic chunking with defaults (heading_aware, 500 tokens)
   lfl chunk document.md output/

   # Specify chunking strategy and chunk size
   lfl chunk document.md output/ --strategy heading_aware --chunk-size 600

   # Sliding window with overlap
   lfl chunk document.md output/ \\
     --strategy sliding_window \\
     --chunk-size 400 \\
     --overlap 50

   # Include metadata
   lfl chunk document.md output/ \\
     --domain programming \\
     --subdomain python \\
     --source "https://docs.python.org/3/tutorial/" \\
     --source-license PSF-2.0 \\
     --source-id python_docs

Strategy Guide
~~~~~~~~~~~~~~

**naive_paragraph**
   Split on double newlines, pack to target size. Fast and simple.

**heading_aware** (default)
   Split at markdown headings. Preserves document structure. Best for technical docs.

**sliding_window**
   Fixed-size windows with overlap. Good for dense content without clear structure.

**semantic** (experimental)
   Semantic boundary detection. Currently falls back to heading_aware.

lfl validate
------------

Validate corpus structure, metadata, and provenance.

Syntax
~~~~~~

.. code-block:: bash

   lfl validate CORPUS_DIR [OPTIONS]

Arguments
~~~~~~~~~

- ``CORPUS_DIR`` — Path to corpus directory (must contain chunks/ subdirectory)

Options
~~~~~~~

.. code-block:: text

   --strict    Fail on warnings (not just errors)

Validation Checks
~~~~~~~~~~~~~~~~~

✓ YAML frontmatter completeness
✓ Required metadata fields (title, domain, source, license, etc.)
✓ sources.json schema validation
✓ Cross-reference chunk source_ids with sources.json
✓ Detect orphaned sources (defined but never referenced)
✓ License compliance
✓ Content hash integrity

Examples
~~~~~~~~

.. code-block:: bash

   # Basic validation
   lfl validate corpora/programming

   # Strict mode (fail on warnings)
   lfl validate corpora/programming --strict

Output Example
~~~~~~~~~~~~~~

.. code-block:: text

   ==================================================
   Corpus Validation: programming
   ==================================================
   Valid chunks    : 156
   Invalid chunks  : 0
   Total chunks    : 156
   ==================================================
   ✅ All checks passed
   ==================================================

   sources.json validation:
   ✓ 8 sources defined
   ⚠ 2 sources never referenced by any chunk (orphaned):
     - deprecated_guide
     - old_tutorial_v1

lfl benchmark
-------------

Test retrieval quality with synthetic queries and parameter sweeps.

Subcommands
~~~~~~~~~~~

.. code-block:: text

   lfl benchmark run      Run single benchmark
   lfl benchmark sweep    Test multiple parameter configurations
   lfl benchmark compare  Compare all saved benchmark reports

lfl benchmark run
~~~~~~~~~~~~~~~~~

Run a single benchmark with specified parameters.

**Syntax:**

.. code-block:: bash

   lfl benchmark run CORPUS_DIR [OPTIONS]

**Options:**

.. code-block:: text

   --num-queries INTEGER    Number of synthetic queries [default: 20]
   --top-k INTEGER         Number of results to retrieve [default: 5]
   --query-strategy TEXT   Query generation strategy [default: heuristic]
                          Choices: heuristic, extractive, llm
   --retrieval-mode TEXT   Retrieval mode [default: bm25]
                          Choices: bm25, vector, hybrid

**Example:**

.. code-block:: bash

   lfl benchmark run corpora/programming \\
     --num-queries 50 \\
     --top-k 10 \\
     --query-strategy heuristic \\
     --retrieval-mode hybrid

lfl benchmark sweep
~~~~~~~~~~~~~~~~~~~

Test multiple configurations to find optimal parameters.

**Syntax:**

.. code-block:: bash

   lfl benchmark sweep CORPUS_DIR [OPTIONS]

**Example:**

.. code-block:: bash

   lfl benchmark sweep corpora/programming

Tests configurations:
- Chunk sizes: 300, 500, 800
- Query counts: 10, 20, 50
- Top-k values: 3, 5, 10

Reports best configuration based on recall@k, MRR, and token efficiency.

lfl benchmark compare
~~~~~~~~~~~~~~~~~~~~~

Compare all saved benchmark reports for a corpus.

**Syntax:**

.. code-block:: bash

   lfl benchmark compare CORPUS_DIR

**Example:**

.. code-block:: bash

   lfl benchmark compare corpora/programming

Displays table comparing:
- Date/time of each run
- Recall@k scores
- MRR (Mean Reciprocal Rank)
- Token efficiency
- Final score

lfl version
-----------

Show toolkit version.

**Syntax:**

.. code-block:: bash

   lfl version

**Output:**

.. code-block:: text

   lfl version 1.0.0

Common Workflows
----------------

Workflow 1: Create and Validate Corpus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Chunk documents
   lfl chunk raw_docs/python_guide.md corpora/programming/chunks/ \\
     --domain programming \\
     --subdomain python \\
     --source-id python_docs

   # 2. Validate corpus structure
   lfl validate corpora/programming

   # 3. Run benchmark to test quality
   lfl benchmark run corpora/programming

Workflow 2: Optimize Chunking Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test multiple configurations
   lfl benchmark sweep corpora/programming

   # Find best parameters from output, then re-chunk:
   lfl chunk documents/ output/ --chunk-size 600  # Use optimal size

   # Validate new chunks
   lfl validate output/

Workflow 3: Monitor Quality Over Time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run benchmarks periodically
   lfl benchmark run corpora/programming

   # Compare all historical runs
   lfl benchmark compare corpora/programming

Exit Codes
----------

All commands use standard exit codes:

- ``0`` — Success
- ``1`` — General error (invalid arguments, file not found, etc.)
- ``2`` — Validation failure (for ``lfl validate``)

Environment Variables
---------------------

Currently no environment variables are used. Configuration is command-line only.

Getting Help
------------

.. code-block:: bash

   # General help
   lfl --help

   # Command-specific help
   lfl chunk --help
   lfl validate --help
   lfl benchmark run --help
