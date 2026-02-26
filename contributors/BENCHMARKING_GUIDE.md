# Benchmarking Guide: Understanding and Interpreting Corpus Quality Metrics

A comprehensive guide to using the Little Free Library benchmarking system to measure, optimize, and improve corpus quality.

## Table of Contents

1. [Introduction](#introduction)
2. [Benchmarking Fundamentals](#benchmarking-fundamentals)
3. [Metrics Explained](#metrics-explained)
4. [Running Benchmarks](#running-benchmarks)
5. [Interpreting Results](#interpreting-results)
6. [Optimization Strategies](#optimization-strategies)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Advanced Topics](#advanced-topics)
9. [Case Studies](#case-studies)
10. [Best Practices](#best-practices)

---

## Introduction

### What is Benchmarking?

Benchmarking measures **retrieval quality** — how well your corpus answers questions. Good retrieval means:

- **Relevant results** — Correct chunks appear in top results
- **High ranking** — Best chunks appear first (not buried on page 3)
- **Efficient recall** — Find answers without massive token overhead

### Why Benchmark?

1. **Quality assurance** — Know if your corpus works before deploying
2. **Parameter tuning** — Find optimal chunk size, overlap, retrieval mode
3. **Regression detection** — Catch quality degradation over time
4. **Comparison** — Compare different chunking strategies or corpora

### The Challenge

How do you measure quality without human annotation? Solution: **synthetic queries**.

Generate test queries from chunk content, then measure if retrieval finds the source chunk. If it can't find content it created, retrieval quality is poor.

---

## Benchmarking Fundamentals

### The Benchmark Loop

```
For each test query:
  1. Generate query from chunk N
  2. Run retrieval (pretend we don't know which chunk it came from)
  3. Check: Does chunk N appear in top-k results?
  4. Record: Position (rank) where chunk N appears
  
After all queries:
  Calculate metrics (Recall@k, MRR, efficiency)
```

### Synthetic Query Generation

Three strategies for generating test queries:

#### 1. Heuristic (Default)

**Method**: Extract keywords using TF-IDF-style weighting

**Pros**:
- Fast (no external dependencies)
- Deterministic (same input = same queries)
- Works offline

**Cons**:
- Queries may be keyword salads (e.g., "python list comprehension syntax example")
- Not natural language

**Example**:
```python
from lfl.query_gen import generate_queries_heuristic

chunks = [...] # Your corpus chunks
queries = generate_queries_heuristic(chunks, num_queries=20)

# Result: ["python list comprehension", "error handling exception", ...]
```

#### 2. Extractive

**Method**: Extract representative sentences from chunks

**Pros**:
- Natural language queries
- No external dependencies
- Fast

**Cons**:
- Queries are verbatim text (may be too easy to match)
- Not diverse

**Example**:
```python
from lfl.query_gen import generate_queries_extractive

queries = generate_queries_extractive(chunks, num_queries=20)

# Result: ["List comprehensions provide a concise way to create lists.", ...]
```

#### 3. LLM-Based

**Method**: Use LLM to generate realistic user queries

**Pros**:
- Most realistic queries
- Diverse phrasing
- Tests semantic understanding

**Cons**:
- Requires LLM API access
- Slower
- Non-deterministic

**Example**:
```python
from lfl.query_gen import generate_queries_llm

queries = generate_queries_llm(
    chunks,
    num_queries=20,
    inference_url="http://localhost:8000/v1"
)

# Result: ["How do I use list comprehensions in Python?", ...]
```

**Recommendation**: Start with heuristic (fast, no dependencies), upgrade to LLM for final validation.

---

## Metrics Explained

### 1. Recall@k

**Definition**: Percentage of queries where the source chunk appears in top-k results.

**Formula**:
```
Recall@k = (# queries with source chunk in top-k) / (total queries)
```

**Interpretation**:

| Score | Quality | Meaning |
|-------|---------|---------|
| 1.0 | Perfect | Every query found its source chunk in top-k |
| 0.8-0.99 | Excellent | Most queries successful |
| 0.6-0.79 | Good | Decent retrieval, room for improvement |
| 0.4-0.59 | Fair | Many queries failing, needs optimization |
| <0.4 | Poor | Retrieval not working well |

**Example**:
```
20 test queries
18 found source chunk in top-5 results
Recall@5 = 18/20 = 0.90 (Excellent)
```

**Why it matters**: If recall is low, your RAG system won't find relevant context.

### 2. MRR (Mean Reciprocal Rank)

**Definition**: Average of reciprocal ranks — rewards chunks that appear higher in results.

**Formula**:
```
MRR = mean(1 / rank_position)

where rank_position is 1 for first place, 2 for second, etc.
```

**Interpretation**:

| MRR | Quality | Meaning |
|-----|---------|---------|
| 0.9-1.0 | Exceptional | Source chunks almost always rank #1 |
| 0.7-0.89 | Very Good | Source chunks typically in top 2-3 |
| 0.5-0.69 | Good | Source chunks usually in top-5 |
| 0.3-0.49 | Fair | Source chunks buried deeper (position 6-10) |
| <0.3 | Poor | Source chunks rarely highly ranked |

**Example**:
```
Query 1: Source chunk at position 1 → 1/1 = 1.0
Query 2: Source chunk at position 2 → 1/2 = 0.5
Query 3: Source chunk at position 1 → 1/1 = 1.0
Query 4: Source chunk at position 5 → 1/5 = 0.2

MRR = (1.0 + 0.5 + 1.0 + 0.2) / 4 = 0.675 (Good)
```

**Why it matters**: High MRR means the *best* chunks appear first (users see them sooner).

### 3. Token Efficiency

**Definition**: Quality score adjusted for token count overhead.

**Formula**:
```
Token Efficiency = (Recall@k * ideal_tokens) / actual_tokens

where:
  ideal_tokens = baseline chunk size (e.g., 500)
  actual_tokens = average chunk size in corpus
```

**Interpretation**:

Higher efficiency = better quality per token spent. Smaller chunks have lower overhead but may fragment context.

**Example**:
```
Recall@5 = 0.85
Average chunk size = 600 tokens
Ideal size = 500 tokens

Efficiency = (0.85 * 500) / 600 = 0.708

If we used 800-token chunks:
Efficiency = (0.85 * 500) / 800 = 0.531  (worse)
```

**Why it matters**: LLM context windows are limited. Efficient chunks maximize quality per token.

### 4. Final Score

**Definition**: Weighted combination of all metrics.

**Formula**:
```
Final Score = (Recall@k * 2 + MRR + Token Efficiency) / 4
```

Recall is weighted 2x because it's the primary quality metric.

**Interpretation**:

| Score | Quality |
|-------|---------|
| >0.9 | Excellent |
| 0.7-0.9 | Good |
| 0.5-0.7 | Fair |
| <0.5 | Poor |

**Example**:
```
Recall@5 = 0.85
MRR = 0.72
Token Efficiency = 0.68

Final = (0.85*2 + 0.72 + 0.68) / 4
      = (1.70 + 0.72 + 0.68) / 4
      = 3.10 / 4
      = 0.775 (Good)
```

---

## Running Benchmarks

### Basic Benchmark Run

```bash
lfl benchmark run corpora/programming
```

**Output**:
```
==================================================
Benchmark Report: programming
==================================================
Date: 2026-02-26 14:32:15
Corpus: corpora/programming
Chunks: 156
Queries: 20

Metrics:
  Recall@1: 0.75
  Recall@3: 0.90
  Recall@5: 0.95
  MRR: 0.82
  Token Efficiency: 0.74
  Final Score: 0.856

Grade: Excellent ✅

Saved to: corpora/programming/reports/2026-02-26_14-32-15.json
==================================================
```

### Benchmark with Custom Parameters

```bash
lfl benchmark run corpora/programming \\
  --num-queries 50 \\
  --top-k 10 \\
  --query-strategy heuristic \\
  --retrieval-mode bm25
```

**Options**:
- `--num-queries` — More queries = more reliable metrics (default: 20)
- `--top-k` — How many results to retrieve (default: 5)
- `--query-strategy` — heuristic, extractive, or llm (default: heuristic)
- `--retrieval-mode` — bm25, vector, or hybrid (default: bm25)

### Parameter Sweep

Test multiple configurations automatically:

```bash
lfl benchmark sweep corpora/programming
```

Sweeps:
- Chunk sizes: 300, 500, 800 tokens
- Query counts: 10, 20, 50 queries
- Top-k values: 3, 5, 10 results

Reports best configuration.

**Output**:
```
Testing 9 configurations...

Configuration 1: chunk_size=300, queries=10, top_k=3
  Final Score: 0.723

Configuration 2: chunk_size=300, queries=20, top_k=5
  Final Score: 0.756

...

Best Configuration:
  Chunk Size: 500
  Queries: 20
  Top-k: 5
  Final Score: 0.856 ✅
```

### Compare Historical Runs

```bash
lfl benchmark compare corpora/programming
```

Shows table of all saved benchmark reports:

```
Date                Recall@5  MRR    Token Eff  Final Score
2026-02-20 10:15    0.82      0.74   0.69       0.767
2026-02-23 15:42    0.88      0.79   0.72       0.817
2026-02-26 14:32    0.95      0.82   0.74       0.856 ⭐
```

Useful for tracking quality over time.

---

## Interpreting Results

### What Makes a Good Score?

**General Guidelines**:

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Recall@5 | >0.85 | >0.70 | <0.70 |
| MRR | >0.75 | >0.60 | <0.60 |
| Token Efficiency | >0.70 | >0.55 | <0.55 |
| Final Score | >0.80 | >0.65 | <0.65 |

**But**: Domain matters! Technical docs often score higher than creative writing.

### Score Patterns & Diagnostics

#### Pattern 1: High Recall, Low MRR

```
Recall@5: 0.92 ✅
MRR: 0.58 ❌
```

**Diagnosis**: Correct chunks are found but ranked poorly (positions 4-5 instead of 1-2).

**Likely causes**:
- Chunks are too similar (retrieval can't distinguish)
- Weak discriminative features

**Solutions**:
- Use hybrid retrieval (add vector search)
- Increase chunk diversity
- Add more metadata (domain, subdomain)

#### Pattern 2: Low Recall, High MRR

```
Recall@5: 0.63 ❌
MRR: 0.85 ✅
```

**Diagnosis**: When chunks are found, they rank well. But many queries fail to find anything.

**Likely causes**:
- Corpus coverage gaps (missing content)
- Queries generated from atypical chunks

**Solutions**:
- Expand corpus (add more content)
- Review failed queries to identify gaps
- Adjust query generation strategy

#### Pattern 3: Both Low

```
Recall@5: 0.54 ❌
MRR: 0.51 ❌
```

**Diagnosis**: Retrieval isn't working.

**Likely causes**:
- Poor chunking (context fragmented)
- Irrelevant content in chunks
- Metadata missing/incorrect

**Solutions**:
- Try different chunking strategy (heading_aware vs sliding_window)
- Reduce chunk size (may be too large)
- Validate corpus structure
- Check query quality (are queries realistic?)

#### Pattern 4: Great Recall, Poor Efficiency

```
Recall@5: 0.95 ✅
Token Efficiency: 0.42 ❌
```

**Diagnosis**: Quality is good but chunks are too large (wasting tokens).

**Likely causes**:
- Chunk size too large (>800 tokens)
- Not packing efficiently

**Solutions**:
- Reduce chunk size to 400-600 tokens
- Use sliding window with overlap
- Split on more granular boundaries

### Corpus-Specific Considerations

**Technical Documentation** (e.g., programming, science):
- Expect high scores (0.85+ recall, 0.75+ MRR)
- Well-structured with headings
- Clear topics

**General Knowledge** (e.g., encyclopedia):
- Moderate scores (0.70-0.85 recall, 0.60-0.75 MRR)
- Broader topics
- More ambiguity

**Creative Writing** (e.g., fiction, essays):
- Lower scores acceptable (0.60-0.75 recall)
- Concepts are subjective
- Less keyword-driven

**Reference Material** (e.g., API docs, specs):
- Should have highest scores (0.90+ recall, 0.80+ MRR)
- Precise terminology
- Clear structure

---

## Optimization Strategies

### Strategy 1: Tune Chunk Size

**Problem**: Poor recall or efficiency.

**Test chunk sizes**:

```bash
# Small chunks (300 tokens)
lfl chunk docs.md output_300/ --chunk-size 300
lfl validate output_300/
lfl benchmark run output_300/

# Medium chunks (500 tokens) - recommended starting point
lfl chunk docs.md output_500/ --chunk-size 500
lfl validate output_500/
lfl benchmark run output_500/

# Large chunks (800 tokens)
lfl chunk docs.md output_800/ --chunk-size 800
lfl validate output_800/
lfl benchmark run output_800/
```

**Compare scores**: Choose size with best final score.

**Heuristics**:
- **Small (200-400)**: Precision over recall, dense content
- **Medium (400-600)**: Balanced, most use cases
- **Large (600-1000)**: Complex topics needing more context

### Strategy 2: Choose Chunking Strategy

**Test strategies**:

```bash
# Heading-aware (preserves structure)
lfl chunk docs.md output_heading/ --strategy heading_aware
lfl benchmark run output_heading/

# Sliding window (uniform sizes, with overlap)
lfl chunk docs.md output_sliding/ --strategy sliding_window --overlap 50
lfl benchmark run output_sliding/

# Naive paragraph (simple, fast)
lfl chunk docs.md output_naive/ --strategy naive_paragraph
lfl benchmark run output_naive/
```

**When to use each**:

| Strategy | Best For | Avoid For |
|----------|----------|-----------|
| **heading_aware** | Technical docs, tutorials, structured content | Prose without headings, unstructured text |
| **sliding_window** | Dense info, uniform chunks needed | Strongly hierarchical content |
| **naive_paragraph** | Simple text, blog posts, Q&A | Complex technical docs |

### Strategy 3: Add Overlap (Sliding Window Only)

**Problem**: Context gets cut off at chunk boundaries.

```bash
# No overlap
lfl chunk docs.md output_0/ --strategy sliding_window --overlap 0
lfl benchmark run output_0/

# Small overlap (50 tokens ~10%)
lfl chunk docs.md output_50/ --strategy sliding_window --overlap 50
lfl benchmark run output_50/

# Large overlap (100 tokens ~20%)
lfl chunk docs.md output_100/ --strategy sliding_window --overlap 100
lfl benchmark run output_100/
```

**Trade-off**: Overlap increases redundancy (more tokens) but preserves context. Usually 10-20% overlap is optimal.

### Strategy 4: Use Hybrid Retrieval

**Problem**: BM25 misses semantic matches, vector misses keyword matches.

```bash
# BM25 only (lexical)
lfl benchmark run corpus/ --retrieval-mode bm25

# Vector only (semantic)
lfl benchmark run corpus/ --retrieval-mode vector

# Hybrid (best of both, usually best)
lfl benchmark run corpus/ --retrieval-mode hybrid
```

**Expected improvements**:
- Hybrid often improves MRR by 10-20%
- Recall improvement varies (0-10%)

**Requirement**: Embedding backend installed (fastembed or sentence-transformers).

### Strategy 5: Increase Test Queries

**Problem**: Metrics unstable across runs (high variance).

```bash
# Small sample (fast but noisy)
lfl benchmark run corpus/ --num-queries 10

# Medium sample (balanced)
lfl benchmark run corpus/ --num-queries 20  # Default

# Large sample (slow but reliable)
lfl benchmark run corpus/ --num-queries 50

# Very large (for production validation)
lfl benchmark run corpus/ --num-queries 100
```

**Rule of thumb**: Use 20 queries for development, 50+ for production validation.

### Strategy 6: Improve Corpus Quality

**If scores remain low**, problem may be corpus content:

1. **Check metadata** — Run validation:
   ```bash
   lfl validate corpus/ --strict
   ```
   Fix all errors and warnings.

2. **Review chunk content** — Are chunks self-contained?
   ```python
   # Load and inspect random chunks
   from lfl.validation import load_corpus_with_frontmatter
   import random
   
   corpus = load_corpus_with_frontmatter("corpus/")
   sample = random.sample(corpus, 5)
   
   for chunk in sample:
       print(f"Title: {chunk['title']}")
       print(f"Length: {len(chunk['content'])} chars")
       print(f"Content: {chunk['content'][:200]}...")
       print("---")
   ```

3. **Check for duplicates** — Remove near-duplicate chunks:
   ```python
   from lfl.embeddings import EmbeddingModel, cosine_similarity
   
   # Generate embeddings
   model = EmbeddingModel.from_profile_name("baseline_cpu_onnx_small")
   texts = [chunk["content"] for chunk in corpus]
   embeddings = model.embed_documents(texts)
   
   # Find near-duplicates (cosine similarity > 0.95)
   for i in range(len(embeddings)):
       for j in range(i+1, len(embeddings)):
           sim = cosine_similarity(embeddings[i], embeddings[j])
           if sim > 0.95:
               print(f"Similar: {corpus[i]['title']} <-> {corpus[j]['title']} ({sim:.3f})")
   ```

4. **Add missing content** — Check failed queries:
   ```bash
   lfl benchmark run corpus/ --num-queries 50 > report.txt
   # Review report.txt for failed queries
   # Add content for missing topics
   ```

---

## Common Issues & Solutions

### Issue 1: "No embedding backend available"

**Symptom**:
```
⚠️ Warning: No embedding backend available
   Install: pip install fastembed
   Continuing with BM25-only mode
```

**Cause**: Neither fastembed nor sentence-transformers installed.

**Solution**:
```bash
# Option 1: FastEmbed (ONNX, works on CPU)
pip install fastembed

# Option 2: sentence-transformers (PyTorch)
pip install sentence-transformers

# Verify
python -c "import fastembed; print('FastEmbed installed')"
```

**Workaround**: Use BM25-only mode (still works, just no vector retrieval).

### Issue 2: Low Recall (<0.6)

**Symptoms**:
- Recall@5 below 0.6
- Many queries find nothing relevant

**Likely causes**:
1. Poor chunking (context fragmented)
2. Corpus gaps (missing content)
3. Query generation mismatch

**Diagnosis**:
```python
# Check which queries failed
from lfl.benchmark import run_benchmark

report = run_benchmark("corpus/", num_queries=20, top_k=5)

# Inspect failed queries (where source chunk not in top-5)
for i, result in enumerate(report["queries"]):
    if not result["found_in_top_k"]:
        print(f"Failed query #{i}: {result['query']}")
        print(f"  Expected chunk: {result['source_chunk_id']}")
        print(f"  Got chunks: {[r['chunk_id'] for r in result['results'][:5]]}")
```

**Solutions**:
1. **Try heading_aware strategy** (preserves context better)
2. **Increase chunk size** to 600-800 tokens (more context)
3. **Check corpus coverage** (are failed queries about missing topics?)
4. **Use hybrid retrieval** (semantic search may help)

### Issue 3: High Recall but Low MRR

**Symptoms**:
- Recall@5 > 0.8
- MRR < 0.6
- Correct chunks found but ranked low

**Likely causes**:
- All chunks too similar (retrieval can't discriminate)
- Weak signals (need better features)

**Diagnosis**:
```python
# Check chunk similarity distribution
from lfl.embeddings import EmbeddingModel, cosine_similarity
import numpy as np

model = EmbeddingModel.from_profile_name("baseline_cpu_onnx_small")
texts = [chunk["content"] for chunk in corpus]
embeddings = model.embed_documents(texts)

# Compute pairwise similarities
sims = []
for i in range(len(embeddings)):
    for j in range(i+1, len(embeddings)):
        sim = cosine_similarity(embeddings[i], embeddings[j])
        sims.append(sim)

print(f"Mean similarity: {np.mean(sims):.3f}")
print(f"Median similarity: {np.median(sims):.3f}")

# If mean > 0.7, chunks are very similar (problem!)
```

**Solutions**:
1. **Use hybrid retrieval** (vector search better at ranking)
2. **Add metadata diversity** (domain, subdomain, tags)
3. **Reduce chunk size** (smaller = more distinctive)
4. **Remove near-duplicates** (deduplicate corpus)

### Issue 4: Low Token Efficiency

**Symptoms**:
- Token Efficiency < 0.5
- Final score dragged down even with good recall

**Likely cause**: Chunks too large (wasting tokens).

**Diagnosis**:
```python
# Check average chunk size
from lfl.validation import load_corpus_with_frontmatter

corpus = load_corpus_with_frontmatter("corpus/")
sizes = [chunk.get("chunk_tokens", len(chunk["content"])//4) for chunk in corpus]

print(f"Average chunk size: {np.mean(sizes):.0f} tokens")
print(f"Min: {min(sizes)}, Max: {max(sizes)}")

# If average > 700 tokens, too large
```

**Solutions**:
1. **Reduce chunk size** to 400-600 tokens
2. **Use heading_aware** (splits more granularly)
3. **Set max_chunk_size** parameter:
   ```bash
   lfl chunk docs.md output/ --chunk-size 500 --max-chunk-size 600
   ```

### Issue 5: Unstable Metrics (High Variance)

**Symptoms**:
- Scores vary widely across runs
- Can't reliably compare configurations

**Likely cause**: Too few test queries (high variance).

**Solution**:
```bash
# Use more queries (50-100 for reliable metrics)
lfl benchmark run corpus/ --num-queries 50
```

**Verification**:
```bash
# Run benchmark 3 times, check variance
lfl benchmark run corpus/ --num-queries 20  # Run 1
lfl benchmark run corpus/ --num-queries 20  # Run 2
lfl benchmark run corpus/ --num-queries 20  # Run 3

# Compare final scores (should be within ±0.05)
```

---

## Advanced Topics

### Custom Evaluation Metrics

Extend benchmark system with custom metrics:

```python
from lfl.benchmark import run_benchmark

def custom_metric(results):
    """Calculate custom metric from benchmark results."""
    # Example: Weighted recall favoring higher ranks
    weighted_sum = 0
    for query_result in results["queries"]:
        rank = query_result.get("rank", None)
        if rank:
            weight = 1.0 / rank  # Higher weight for rank 1, 2, etc.
            weighted_sum += weight
    
    return weighted_sum / len(results["queries"])

# Run benchmark
report = run_benchmark("corpus/", num_queries=20)

# Add custom metric
report["custom_metric"] = custom_metric(report)

print(f"Custom Metric: {report['custom_metric']:.3f}")
```

### Query Quality Analysis

Analyze quality of generated queries:

```python
from lfl.query_gen import generate_queries_heuristic
from collections import Counter
import numpy as np

queries = generate_queries_heuristic(chunks, num_queries=50)

# Query length distribution
lengths = [len(q.split()) for q in queries]
print(f"Avg query length: {np.mean(lengths):.1f} words")
print(f"Length range: {min(lengths)}-{max(lengths)} words")

# Term frequency analysis
all_terms = []
for q in queries:
    all_terms.extend(q.lower().split())

term_counts = Counter(all_terms)
print("\\nTop 10 query terms:")
for term, count in term_counts.most_common(10):
    print(f"  {term}: {count}")

# Diversity: unique queries / total
print(f"\\nUnique queries: {len(set(queries))}/{len(queries)}")
```

### Cross-Corpus Comparison

Compare quality across multiple corpora:

```python
import json
from pathlib import Path

corpora = ["programming", "mathematics", "web-dev"]

results = {}
for corpus_name in corpora:
    report = run_benchmark(f"corpora/{corpus_name}", num_queries=20)
    results[corpus_name] = {
        "recall@5": report["recall@5"],
        "mrr": report["mrr"],
        "final_score": report["final_score"]
    }

# Print comparison table
print(f"{'Corpus':<15} {'Recall@5':<10} {'MRR':<10} {'Final Score':<12}")
print("-" * 50)
for corpus, metrics in results.items():
    print(f"{corpus:<15} {metrics['recall@5']:<10.3f} {metrics['mrr']:<10.3f} {metrics['final_score']:<12.3f}")
```

###A/B Testing Configurations

Statistically compare two configurations:

```python
from scipy import stats  # pip install scipy
import numpy as np

# Run configuration A multiple times
scores_A = []
for _ in range(10):
    report = run_benchmark("corpus_A/", num_queries=20)
    scores_A.append(report["final_score"])

# Run configuration B multiple times
scores_B = []
for _ in range(10):
    report = run_benchmark("corpus_B/", num_queries=20)
    scores_B.append(report["final_score"])

# Statistical test (t-test)
t_stat, p_value = stats.ttest_ind(scores_A, scores_B)

print(f"Configuration A: mean={np.mean(scores_A):.3f}, std={np.std(scores_A):.3f}")
print(f"Configuration B: mean={np.mean(scores_B):.3f}, std={np.std(scores_B):.3f}")
print(f"t-statistic: {t_stat:.3f}")
print(f"p-value: {p_value:.4f}")

if p_value < 0.05:
    winner = "A" if np.mean(scores_A) > np.mean(scores_B) else "B"
    print(f"\\n✅ Configuration {winner} is statistically significantly better (p<0.05)")
else:
    print("\\n❌ No statistically significant difference (p≥0.05)")
```

---

## Case Studies

### Case Study 1: Python Documentation Corpus

**Initial Results**:
```
Chunks: 87
Chunk Size: 800 tokens (naive_paragraph)
Recall@5: 0.68 (Fair)
MRR: 0.54 (Fair)
Token Efficiency: 0.38 (Poor)
Final Score: 0.56 (Fair)
```

**Diagnosis**: Poor efficiency (chunks too large), moderate recall.

**Optimization Steps**:

1. **Reduce chunk size**:
   ```bash
   lfl chunk docs/ output_500/ --chunk-size 500 --strategy heading_aware
   lfl benchmark run output_500/
   ```
   Result: Recall@5 → 0.79, Efficiency → 0.61

2. **Try hybrid retrieval**:
   ```bash
   lfl benchmark run output_500/ --retrieval-mode hybrid
   ```
   Result: MRR → 0.71 (+0.17!)

3. **Add 50 more test queries** (verify stability):
   ```bash
   lfl benchmark run output_500/ --num-queries 50 --retrieval-mode hybrid
   ```
   Result: Metrics stable (variance <0.02)

**Final Results**:
```
Chunks: 124 (from 87, more granular)
Chunk Size: 500 tokens (heading_aware)
Retrieval: Hybrid (BM25 + vector)
Recall@5: 0.88 (Excellent) [+0.20]
MRR: 0.77 (Very Good) [+0.23]
Token Efficiency: 0.72 (Good) [+0.34]
Final Score: 0.81 (Excellent) [+0.25]
```

**Key Takeaways**:
- Smaller chunks → better efficiency
- heading_aware → better structure preservation
- Hybrid retrieval → significant MRR boost

### Case Study 2: Mathematics Encyclopedia

**Initial Results**:
```
Chunks: 432
Chunk Size: 600 tokens (heading_aware)
Recall@5: 0.74 (Good)
MRR: 0.82 (Very Good)
Token Efficiency: 0.66 (Fair)
Final Score: 0.73 (Good)
```

**Diagnosis**: Good overall but low recall. MRR surprisingly high (when chunks found, they rank well).

**Investigation**:
```python
# Check failed queries
report = run_benchmark("math_corpus/", num_queries=50)
failed = [q for q in report["queries"] if not q["found_in_top_k"]]

print(f"Failed queries: {len(failed)}/50")
for q in failed[:5]:
    print(f"  - {q['query']}")
```

**Output**:
```
Failed queries: 13/50
  - complex number polar form
  - eigenvector computation steps
  - taylor series convergence test
  - matrix determinant calculation
  - fourier transform properties
```

**Findings**: Failed queries are about procedural/computational topics (underrepresented in corpus).

**Solution**: Add more procedural content.

**After adding 80 new chunks** (focused on computational procedures):
```
Chunks: 512 (from 432)
Recall@5: 0.89 (Excellent) [+0.15]
MRR: 0.84 (Very Good) [+0.02]
Token Efficiency: 0.68 (Good) [+0.02]
Final Score: 0.82 (Excellent) [+0.09]
```

**Key Takeaways**:
- Failed queries reveal content gaps
- Balanced corpus (concepts + procedures) improves recall
- MRR stays high (good chunking strategy)

---

## Best Practices

### 1. Benchmark Early and Often

- **Before deploying**: Always benchmark before going to production
- **After changes**: Re-benchmark after any corpus modification
- **Periodically**: Benchmark monthly to catch quality drift

### 2. Use Multiple Metrics

Don't optimize for one metric:
- High recall but low MRR → users see irrelevant results
- High efficiency but low recall → missing content
- Use final score (balanced) as primary metric

### 3. Test with Realistic Queries

If possible, supplement synthetic queries with real user queries:

```python
# Mix synthetic and real queries
synthetic_queries = generate_queries_heuristic(chunks, num_queries=30)
real_queries = ["How do I use Python decorators?", "Explain recursion", ...]

all_queries = synthetic_queries + real_queries

# Run benchmark with mixed queries
# (Custom benchmark code needed)
```

### 4. Document Your Configuration

Always save benchmark configuration in reports:

```json
{
  "corpus": "programming",
  "date": "2026-02-26",
  "chunk_strategy": "heading_aware",
  "chunk_size": 500,
  "retrieval_mode": "hybrid",
  "alpha": 0.5,
  "num_queries": 20,
  "metrics": {...}
}
```

### 5. Version Control Your Corpus

- Tag corpus versions in git
- Keep benchmark reports with version info
- Track quality over time

```bash
git tag -a v1.0 -m "Initial programming corpus release"
lfl benchmark run corpora/programming
git add corpora/programming/reports/
git commit -m "Add v1.0 benchmark results"
```

### 6. Set Quality Gates

Define minimum thresholds for deployment:

```yaml
quality_gates:
  recall@5: 0.75  # Must find 75% of queries
  mrr: 0.65       # Must rank well
  final_score: 0.70  # Overall quality

If any metric below threshold → FAIL BUILD
```

Integrate into CI/CD:

```bash
# In CI script
lfl benchmark run corpora/programming --num-queries 50 > report.json

python check_quality_gates.py report.json  # Exit 1 if fails

# Deploy only if passed
```

### 7. Monitor Production Quality

If possible, log retrieval metrics in production:

- Track query-level recall (are users finding answers?)
- A/B test retrieval configurations
- Collect user feedback (thumbs up/down)

---

## Summary

### Quick Reference

| Scenario | Recommendation |
|----------|----------------|
| **Starting new corpus** | heading_aware @ 500 tokens, BM25 retrieval, 20 queries |
| **Optimizing parameters** | Run sweep, test 3 chunk sizes, compare final scores |
| **Low recall (<0.7)** | Try heading_aware, increase chunk size, check content gaps |
| **Low MRR (<0.6)** | Use hybrid retrieval, reduce chunk similarity, add metadata |
| **Low efficiency (<0.5)** | Reduce chunk size to 400-600, set max_chunk_size |
| **Production validation** | 50+ queries, hybrid retrieval, document configuration |
| **Ongoing monitoring** | Monthly benchmarks, track trends, set quality gates |

### Metrics Target Summary

| Corpus Type | Recall@5 Target | MRR Target | Final Score Target |
|-------------|----------------|------------|-------------------|
| **Technical Docs** | >0.85 | >0.75 | >0.80 |
| **General Knowledge** | >0.75 | >0.65 | >0.70 |
| **Reference Material** | >0.90 | >0.80 | >0.85 |
| **Creative Writing** | >0.65 | >0.55 | >0.60 |

### Optimization Checklist

When optimizing a corpus:

1. ☐ Run baseline benchmark (BM25, default parameters)
2. ☐ Test 3 chunk sizes (300, 500, 800)
3. ☐ Test 2-3 chunking strategies
4. ☐ Try hybrid retrieval (if embedding backend available)
5. ☐ Increase to 50 queries for final validation
6. ☐ Document best configuration
7. ☐ Save benchmark report
8. ☐ Track quality over time (compare monthly)

---

**Version**: 1.0.0  
**Last Updated**: February 26, 2026  
**Author**: Little Free Library Contributors

**Related Documentation**:
- [ARCHITECTURE.md](ARCHITECTURE.md) — System architecture diagrams
- [QUICKSTART.md](QUICKSTART.md) — Getting started guide
- [docs/api/cli.rst](api/cli.rst) — CLI reference
- [docs/api/examples.rst](api/examples.rst) — Code examples
