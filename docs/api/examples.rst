Examples
========

Advanced usage examples demonstrating the full capabilities of the Little Free Library Toolkit.

Example 1: Complete Corpus Pipeline
------------------------------------

Build a complete corpus from raw documents through validation and benchmarking.

.. code-block:: python

   from pathlib import Path from lfl.chunking import chunk_document, save_chunk_to_markdown
   from lfl.corpus_validation import validate_corpus
   from lfl.retrieval import HybridRetriever

   # Step 1: Prepare corpus metadata
   corpus_metadata = {
       "domain": "programming",
       "subdomain": "python",
       "source": "https://docs.python.org/3/tutorial/",
       "source_license": "PSF-2.0",
       "source_id": "python_docs",
   }

   # Step 2: Chunk multiple documents
   input_dir = Path("raw_documents/python")
   output_dir = Path("corpora/programming/chunks")
   output_dir.mkdir(parents=True, exist_ok=True)

   total_chunks = 0
   for doc_path in input_dir.glob("*.md"):
       with open(doc_path, "r", encoding="utf-8") as f:
           content = f.read()
       
       chunks = chunk_document(
           content=content,
           strategy="heading_aware",
           chunk_size=500,
           metadata=corpus_metadata
       )
       
       for chunk in chunks:
           save_chunk_to_markdown(chunk, output_dir)
       
       total_chunks += len(chunks)
       print(f"Processed {doc_path.name}: {len(chunks)} chunks")

   print(f"Total chunks created: {total_chunks}")

   # Step 3: Validate corpus
   is_valid, valid_count, invalid_count, source_errors, orphaned = \\
       validate_corpus("corpora/programming", strict=True)

   if is_valid:
       print(f"✓ Corpus valid: {valid_count} chunks")
   else:
       print(f"✗ Validation failed: {invalid_count} invalid chunks")
       for error in source_errors:
           print(f"  - {error}")

   # Step 4: Test retrieval
   retriever = HybridRetriever(
       corpus_dir="corpora/programming",
       mode="bm25"
   )

   test_queries = [
       "python list comprehension",
       "exception handling",
       "function decorators"
   ]

   for query in test_queries:
       results = retriever.retrieve(query, top_k=3)
       print(f"\\nQuery: {query}")
       for result in results:
           print(f"  {result.title} ({result.score:.3f})")

Example 2: Custom Chunking Strategy
------------------------------------

Implement a custom chunking strategy for specialized content.

.. code-block:: python

   from lfl.chunking import generate_chunk_id, save_chunk_to_markdown
   from pathlib import Path
   import re

   def chunk_by_code_blocks(content, metadata):
       """Custom strategy: Split at code blocks."""
       
       # Split on triple backticks
       parts = re.split(r'```[\\w]*\\n', content)
       
       chunks = []
       chunk_num = 1
       
       for part in parts:
           if not part.strip():
               continue
           
           # Extract title from first heading
           title_match = re.search(r'^#+ (.+)$', part, re.MULTILINE)
           title = title_match.group(1) if title_match else f"Code Example {chunk_num}"
           
           # Create chunk
           chunk = {
               "title": title,
               "text": part.strip(),
               "chunk_num": chunk_num,
               **metadata
           }
           
           # Generate deterministic chunk ID
           chunk["chunk_id"] = generate_chunk_id(chunk["text"])
           
           chunks.append(chunk)
           chunk_num += 1
       
       return chunks

   # Use custom strategy
   with open("code_tutorial.md") as f:
       content = f.read()

   metadata = {
       "domain": "programming",
       "subdomain": "examples",
       "source": "https://example.com/tutorial",
       "source_license": "MIT",
       "source_id": "example_code"
   }

   chunks = chunk_by_code_blocks(content, metadata)

   output_dir = Path("corpora/programming/chunks")
   for chunk in chunks:
       save_chunk_to_markdown(chunk, output_dir)

   print(f"Created {len(chunks)} code-block chunks")

Example 3: Multi-Backend Embedding Comparison
----------------------------------------------

Compare different embedding backends and models.

.. code-block:: python

   from lfl.embeddings import EmbeddingModel
   from lfl.profiles import list_profiles, load_profile
   import time

   # Test queries
   queries = [
       "python list comprehension",
       "machine learning algorithms",
       "database indexing strategies"
   ]

   # Test multiple profiles
   profile_names = ["baseline_cpu_onnx_small", "quality_cpu_onnx_base"]

   for profile_name in profile_names:
       print(f"\\n{'='*60}")
       print(f"Testing profile: {profile_name}")
       print('='*60)
       
       profile = load_profile(profile_name)
       model = EmbeddingModel.from_profile(profile)
       
       # Benchmark embedding generation
       start = time.time()
       embeddings = model.embed_documents(queries)
       elapsed = time.time() - start
       
       print(f"Model: {profile['model_name']}")
       print(f"Dimensions: {profile['dimensions']}")
       print(f"Backend: {profile['backend']}")
       print(f"Time: {elapsed*1000:.2f}ms for {len(queries)} queries")
       print(f"Per-query: {elapsed*1000/len(queries):.2f}ms")
       print(f"Shape: {embeddings.shape}")

Example 4: Hybrid Retrieval with Custom Weighting
--------------------------------------------------

Experiment with different BM25/vector weight combinations.

.. code-block:: python

   from lfl.retrieval import HybridRetriever

   corpus_dir = "corpora/programming"
   query = "explain python decorators"

   # Test different alpha values
   alphas = [0.0, 0.3, 0.5, 0.7, 1.0]

   print(f"Query: {query}\\n")

   for alpha in alphas:
       retriever = HybridRetriever(
           corpus_dir=corpus_dir,
           mode="hybrid",
           alpha=alpha
       )
       
       results = retriever.retrieve(query, top_k=3)
       
       print(f"Alpha = {alpha} ({'BM25 only' if alpha == 1.0 else 'Vector only' if alpha == 0.0 else f'{alpha:.0%} BM25'})")
       
       for i, result in enumerate(results, 1):
           print(f"  {i}. {result.title} (score: {result.score:.3f})")
       print()

Example 5: Batch Validation with Error Reporting
-------------------------------------------------

Validate multiple corpora and generate detailed error reports.

.. code-block:: python

   from lfl.corpus_validation import validate_corpus, format_validation_report
   from pathlib import Path
   import json

   # Find all corpora
   corpora_dir = Path("corpora")
   corpus_paths = [p for p in corpora_dir.iterdir() if p.is_dir()]

   validation_results = {}

   for corpus_path in corpus_paths:
       corpus_name = corpus_path.name
       print(f"\\nValidating {corpus_name}...")
       
       is_valid, valid_count, invalid_count, source_errors, orphaned = \\
           validate_corpus(str(corpus_path), strict=False)
       
       validation_results[corpus_name] = {
           "valid": is_valid,
           "valid_chunks": valid_count,
           "invalid_chunks": invalid_count,
           "source_errors": source_errors,
           "orphaned_sources": orphaned
       }
       
       status = "✓" if is_valid else "✗"
       print(f"{status} {corpus_name}: {valid_count} valid, {invalid_count} invalid")

   # Save validation report
   report_path = Path("validation_report.json")
   with open(report_path, "w") as f:
       json.dump(validation_results, f, indent=2)

   print(f"\\nValidation report saved to {report_path}")

   # Show summary
   total_valid = sum(r["valid_chunks"] for r in validation_results.values())
   total_invalid = sum(r["invalid_chunks"] for r in validation_results.values())
   
   print(f"\\nSummary across all corpora:")
   print(f"  Total chunks: {total_valid + total_invalid}")
   print(f"  Valid: {total_valid}")
   print(f"  Invalid: {total_invalid}")

Example 6: Query Generation and Analysis
-----------------------------------------

Generate synthetic queries and analyze coverage.

.. code-block:: python

   from lfl.query_gen import generate_queries_heuristic
   from lfl.validation import load_corpus_with_frontmatter
   from collections import Counter

   # Load corpus
   corpus = load_corpus_with_frontmatter("corpora/programming")
   chunk_texts = [chunk["content"] for chunk in corpus]

   # Generate queries
   queries = generate_queries_heuristic(chunk_texts, num_queries=50)

   print(f"Generated {len(queries)} queries\\n")
   print("Sample queries:")
   for query in queries[:10]:
       print(f"  - {query}")

   # Analyze query characteristics
   query_lengths = [len(q.split()) for q in queries]
   
   print(f"\\nQuery statistics:")
   print(f"  Average length: {sum(query_lengths)/len(query_lengths):.1f} words")
   print(f"  Min length: {min(query_lengths)} words")
   print(f"  Max length: {max(query_lengths)} words")

   # Extract query terms
   all_terms = []
   for query in queries:
       all_terms.extend(query.lower().split())

   term_freq = Counter(all_terms)
   
   print(f"\\nTop 10 query terms:")
   for term, count in term_freq.most_common(10):
       print(f"  {term}: {count}")

Example 7: Incremental Corpus Updates
--------------------------------------

Update corpus incrementally while maintaining metadata consistency.

.. code-block:: python

   from pathlib import Path
   from lfl.chunking import chunk_document, save_chunk_to_markdown
   from lfl.corpus_validation import validate_chunk
   import json

   def update_corpus_incremental(new_doc_path, corpus_dir, metadata):
       """Add new document to existing corpus with validation."""
       
       corpus_dir = Path(corpus_dir)
       chunks_dir = corpus_dir / "chunks"
       
       # Load existing chunk IDs to avoid duplicates
       existing_ids = set()
       for chunk_file in chunks_dir.glob("*.md"):
           # Extract chunk_id from filename or frontmatter
           existing_ids.add(chunk_file.stem)
       
       # Chunk new document
       with open(new_doc_path) as f:
           content = f.read()
       
       chunks = chunk_document(
           content=content,
           strategy="heading_aware",
           chunk_size=500,
           metadata=metadata
       )
       
       # Validate and save new chunks
       new_chunks = 0
       skipped_chunks = 0
       
       for chunk in chunks:
           # Check for duplicates
           if chunk["chunk_id"] in existing_ids:
               skipped_chunks += 1
               continue
           
           # Validate before saving
           chunk_file_name = f"chunk_{len(existing_ids) + new_chunks + 1:03d}.md"
           errors = validate_chunk(chunk, chunk_file_name)
           
           if errors:
               print(f"✗ Validation failed for chunk: {', '.join(errors)}")
               continue
           
           # Save chunk
           save_chunk_to_markdown(chunk, chunks_dir)
           existing_ids.add(chunk["chunk_id"])
           new_chunks += 1
       
       print(f"Added {new_chunks} new chunks")
       print(f"Skipped {skipped_chunks} duplicate chunks")
       
       return new_chunks, skipped_chunks

   # Usage
   corpus_dir = "corpora/programming"
   metadata = {
       "domain": "programming",
       "subdomain": "python",
       "source": "https://docs.python.org/3/",
       "source_license": "PSF-2.0",
       "source_id": "python_docs"
   }

   new_chunks, skipped = update_corpus_incremental(
       "new_docs/python_async.md",
       corpus_dir,
       metadata
   )

Example 8: Performance Profiling
---------------------------------

Profile chunking and retrieval performance.

.. code-block:: python

   import time
   from pathlib import Path
   from lfl.chunking import chunk_document
   from lfl.retrieval import HybridRetriever

   def profile_chunking(content, strategies, chunk_sizes):
       """Profile different chunking configurations."""
       
       results = []
       
       for strategy in strategies:
           for chunk_size in chunk_sizes:
               start = time.time()
               
               chunks = chunk_document(
                   content=content,
                   strategy=strategy,
                   chunk_size=chunk_size,
                   metadata={}
               )
               
               elapsed = time.time() - start
               
               results.append({
                   "strategy": strategy,
                   "chunk_size": chunk_size,
                   "num_chunks": len(chunks),
                   "time_ms": elapsed * 1000,
                   "throughput_kb_s": len(content.encode()) / 1024 / elapsed
               })
       
       return results

   # Load test document
   test_doc = Path("test_documents/large_doc.md").read_text()

   # Profile chunking
   strategies = ["naive_paragraph", "heading_aware", "sliding_window"]
   chunk_sizes = [300, 500, 800]

   print("Chunking Performance\\n")
   print(f"{'Strategy':<20} {'Size':<6} {'Chunks':<8} {'Time (ms)':<12} {'Throughput (KB/s)'}")
   print("-" * 70)

   results = profile_chunking(test_doc, strategies, chunk_sizes)

   for result in results:
       print(f"{result['strategy']:<20} "
             f"{result['chunk_size']:<6} "
             f"{result['num_chunks']:<8} "
             f"{result['time_ms']:<12.2f} "
             f"{result['throughput_kb_s']:.2f}")

   # Profile retrieval
   print("\\nRetrieval Performance\\n")
   
   retriever = HybridRetriever(corpus_dir="corpora/programming", mode="bm25")
   
   queries = [
       "python list comprehension",
       "error handling best practices",
       "asynchronous programming"
   ]
   
   for query in queries:
       start = time.time()
       results = retriever.retrieve(query, top_k=10)
       elapsed = time.time() - start
       
       print(f"Query: {query}")
       print(f"  Time: {elapsed*1000:.2f}ms")
       print(f"  Results: {len(results)}")
       print()

See Also
--------

- :doc:`quickstart` — Getting started guide
- :doc:`modules/index` — Complete API reference
- :doc:`cli` — Command-line interface
- `GitHub Repository <https://github.com/little-free-library/lfl>`_ — Source code and more examples
