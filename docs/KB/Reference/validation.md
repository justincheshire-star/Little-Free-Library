# Retrieval Validation & Parameter Tuning

Little Free Library includes an automated retrieval validation system that scores
corpus quality and helps tune ingestion parameters for the best possible retrieval
performance. No human annotation required.

---

## The Core Idea

After ingesting a corpus, you want to know: **if I ask a question that this corpus
should answer, do I actually get the right chunk back?**

The validation system answers this by:

1. **Generating synthetic queries** from each chunk automatically
2. **Running retrieval** against those queries
3. **Scoring recall and token efficiency** to produce a single comparable score
4. **Recommending parameter adjustments** based on the results

The primary optimization target is:

> **Higher recall + lower tokens = best score**

A corpus that retrieves accurately with small, focused chunks is strictly better
than one that needs large chunks to achieve the same recall.

---

## The Levers

These ingestion parameters directly affect retrieval quality. They are the things
you tune based on benchmark results:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `chunk_size` | 512 | Target tokens per chunk |
| `chunk_overlap` | 64 | Token overlap between consecutive chunks |
| `chunking_strategy` | `naive_paragraph` | How text is split (see strategies below) |
| `embedding_profile` | `baseline_cpu_onnx_small` | Which model + runtime |
| `text_normalization` | `true` | Strip noise before embedding |
| `min_chunk_tokens` | 32 | Discard chunks shorter than this |
| `max_chunk_tokens` | 1024 | Hard cap per chunk |

### Chunking Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `naive_paragraph` | Split on double newlines, pack to chunk_size | General prose, mixed content |
| `heading_aware` | Split at markdown headings first, then fill | Structured docs with clear sections |
| `sliding_window` | Fixed-size windows with overlap | Dense technical content, code-heavy |
| `semantic` | Split at semantic boundaries (requires model) | Long-form narrative, research papers |

---

## Scoring Formula

### Recall Metrics

```
Recall@k = chunks retrieved in top-k / total queries tested
MRR      = mean(1 / rank_of_expected_chunk)
```

### Efficiency Score

```
normalized_token_cost = avg_chunk_tokens / target_chunk_tokens
efficiency_score      = recall@3 / normalized_token_cost
```

A corpus with recall@3 of 0.85 using 300-token chunks scores higher than one
with the same recall using 600-token chunks, because it achieves the same quality
at half the context cost.

### Coverage Penalty

```
context_budget = context_window * 0.25   (default: 4096 * 0.25 = 1024 tokens)
coverage_penalty = min(1.0, context_budget / avg_chunk_tokens)
```

Penalizes corpora where chunks are so large they crowd out the context window.

### Final Score

```
final_score = efficiency_score * coverage_penalty
```

Higher is always better. Scores above 0.8 are excellent. Below 0.5 indicates
the ingestion parameters need adjustment.

---

## Score Interpretation

| Final Score | Meaning |
|-------------|---------|
| > 0.90 | Excellent — consider publishing these params as recommended config |
| 0.75 – 0.90 | Good — minor tuning may help |
| 0.50 – 0.75 | Acceptable — review recommendations |
| < 0.50 | Poor — significant parameter adjustment needed |

---

## Query Generation Strategies

Synthetic queries are generated automatically. Three strategies are available:

### `heuristic` (default)
No model required. Extracts key sentences by term frequency and converts them
to questions using pattern matching. Fast and always available.

```bash
lfl benchmark run corpora/programming --query-strategy heuristic
```

### `extractive`
Identifies technical terms and capitalized phrases, builds targeted questions
around them. Better for technical corpora with consistent terminology.

```bash
lfl benchmark run corpora/programming --query-strategy extractive
```

### `llm`
Uses a local LLM via a HTTP endpoint to generate high-quality, natural
questions. Best quality but requires a running inference server.

```bash
lfl benchmark run corpora/programming \
  --query-strategy llm \
  --llm-endpoint http://localhost:8080/completion
```

Queries are cached after first generation. Re-runs reuse the cache unless
`--no-reuse` is passed.

---

## Usage

### Run a Single Benchmark

```bash
# Default params, default profile
lfl benchmark run corpora/programming

# Custom params
lfl benchmark run corpora/programming \
  --chunk-size 256 \
  --overlap 32 \
  --strategy heading_aware \
  --profile quality_cpu_onnx_base
```

### Run a Parameter Sweep

Automatically tests 8 configurations across chunk sizes, overlaps, and
strategies. Prints a ranked comparison table and identifies the best config.

```bash
lfl benchmark sweep corpora/programming
```

Example output:

```
LFL Benchmark Comparison
--------------------------------------------------------------------
Strategy             Size  Ovlp    R@1    R@3    R@5    MRR   Score
--------------------------------------------------------------------
heading_aware         512    64  0.781  0.912  0.954  0.834   0.921 ★ BEST
heading_aware         256    32  0.743  0.889  0.941  0.801   0.887
naive_paragraph       512    64  0.712  0.867  0.932  0.778   0.854
sliding_window        512   128  0.698  0.851  0.921  0.762   0.831
naive_paragraph       256    32  0.671  0.834  0.908  0.741   0.812
naive_paragraph       768    64  0.689  0.845  0.916  0.754   0.789
sliding_window        768   128  0.654  0.821  0.897  0.728   0.754
naive_paragraph       512   128  0.641  0.809  0.884  0.714   0.741
--------------------------------------------------------------------

Best configuration:
  chunk_size=512  overlap=64  strategy=heading_aware
  final_score=0.921  recall@3=0.912

Recommendations:
  → Excellent score. Consider publishing this profile + params as the
    recommended ingestion config for this corpus.
```

### Compare Saved Reports

```bash
lfl benchmark compare corpora/programming
```

All reports are saved as JSON in `corpora/<domain>/benchmarks/` so you can
track improvements over time as you update the corpus.

---

## Tuning Workflow

The recommended workflow for a new corpus:

```
1. Ingest with default params
   lfl chunk-file ... (or bulk ingest)

2. Run a sweep to find the best starting config
   lfl benchmark sweep corpora/<domain>

3. Apply the recommended params and re-ingest
   lfl chunk-file ... --chunk-size <best> --overlap <best>

4. Re-run benchmark to confirm improvement
   lfl benchmark run corpora/<domain> --no-reuse

5. Lock the params in CORPUS.md
   (document them so re-ingestion is reproducible)
```

### What to Tune First

| Symptom | Try This |
|---------|----------|
| Recall@1 < 0.50 | Reduce chunk_size. Chunks may be too large and dilute signal. |
| Recall@3 < 0.75 | Increase overlap. Context is being lost at chunk boundaries. |
| Score < 0.50 | Switch chunking strategy. naive_paragraph may not suit this content. |
| Coverage penalty low | Reduce chunk_size. Chunks are crowding the context window. |
| Token cost high | Check for documents bypassing the chunker (very large single chunks). |
| Everything high | Publish the params. You're done. |

---

## Report Format

Every benchmark saves a JSON report to `corpora/<domain>/benchmarks/`:

```json
{
  "corpus_path": "corpora/programming",
  "profile": "baseline_cpu_onnx_small",
  "params": {
    "chunk_size": 512,
    "chunk_overlap": 64,
    "chunking_strategy": "heading_aware",
    "embedding_profile": "baseline_cpu_onnx_small",
    "text_normalization": true,
    "min_chunk_tokens": 32,
    "max_chunk_tokens": 1024
  },
  "chunk_count": 312,
  "query_count": 624,
  "avg_chunk_tokens": 487.3,
  "target_chunk_tokens": 512,
  "recall_at_1": 0.781,
  "recall_at_3": 0.912,
  "recall_at_5": 0.954,
  "mrr": 0.834,
  "normalized_token_cost": 0.951,
  "efficiency_score": 0.959,
  "coverage_penalty": 0.961,
  "final_score": 0.921,
  "recommendations": [
    "Excellent score. Consider publishing this profile + params as the recommended ingestion config for this corpus."
  ],
  "elapsed_seconds": 4.2,
  "generated_at": "2026-02-25 14:30:00"
}
```

Reports are versioned by timestamp in the filename so you never lose history.

---

## CORPUS.md — Locking Recommended Params

Once you have a validated configuration, document it in the corpus `CORPUS.md`:

```markdown
## Recommended Ingestion Parameters

| Parameter | Value |
|-----------|-------|
| chunk_size | 512 |
| chunk_overlap | 64 |
| chunking_strategy | heading_aware |
| embedding_profile | baseline_cpu_onnx_small |
| benchmark_score | 0.921 |
| benchmarked_at | 2026-02-25 |
```

This makes re-ingestion reproducible and gives contributors a verified baseline
to compare against when they propose corpus updates.

---

## Architecture

```
lfl/
├── validation.py     # Core: BM25, scoring, report structures
├── query_gen.py      # Synthetic query generation (3 strategies)
├── benchmark.py      # Runner: corpus load → query gen → retrieval → score
└── cli_benchmark.py  # CLI commands: run, sweep, compare
```

The retrieval engine in `validation.py` uses **BM25** as a fast, dependency-free
baseline. BM25 is a strong proxy for retrieval quality — if a chunk cannot be
retrieved by keyword overlap, it will likely struggle with vector retrieval too.
For vector-augmented scoring, the system is designed to accept embedding arrays
on each `Chunk` object and can be extended with cosine similarity retrieval
alongside BM25 for hybrid scoring.

---

*The best corpus is the one that retrieves the right knowledge with the fewest tokens.*
