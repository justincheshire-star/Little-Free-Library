# Little Free Library — Quick Start Guide

**Last Updated**: February 27, 2026  
**Version**: 1.0.0

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/justincheshire-star/Little-Free-Library.git
cd Little-Free-Library

# Install the lfl package
pip install -e .
```

This installs the `lfl` command-line tool.

---

## Accessing Pre-built Datasets

Completed datasets from Little Free Library are published to Hugging Face after ingestion:

**Organization:** [https://huggingface.co/LittleFreeLibrary](https://huggingface.co/LittleFreeLibrary)

To use a pre-built dataset in your own RAG pipeline:

```python
from datasets import load_dataset

# Load a specific corpus
ds = load_dataset("LittleFreeLibrary/programming")

# Use directly with your RAG system
for item in ds:
    print(item["title"], item["content"])
```

The sections below explain how to **create and validate** your own corpora using the LFL toolkit.

---

## Usage

### 1. Validate a Corpus

Before ingesting or benchmarking, validate your corpus structure:

```bash
lfl validate corpora/programming
```

This checks:
- ✅ All chunks have valid YAML frontmatter
- ✅ Required metadata fields are present
- ✅ sources.json exists and is valid
- ✅ Chunk files are well-formed UTF-8

Add `--strict` to fail on warnings:
```bash
lfl validate corpora/programming --strict
```

### 2. Ingest Documents (Drop-Folder Workflow)

Build a corpus from your own documents (PDF, DOCX, XLSX, HTML, TXT, etc.):

```bash
# Install ingestion dependencies
pip install "lfl[all_ingest]"

# Create a drop folder for your domain
mkdir -p ingestion/my_domain

# Drop files in
cp ~/Documents/guide.pdf ingestion/my_domain/
cp ~/Documents/notes.txt ingestion/my_domain/

# Run ingestion (dry-run first)
lfl ingest my_domain --inventory

# Run for real
lfl ingest my_domain
```

This will:
1. Scan `ingestion/my_domain/` for supported files
2. Convert formats if needed (Pages → PDF via LibreOffice)
3. Extract text (with OCR fallback for scanned PDFs)
4. Chunk documents into `corpora/my_domain/chunks/`
5. Generate `sources.json` with SHA256 provenance
6. Validate the corpus structure
7. Write a manifest to `ingestion_out/my_domain/manifest.json`

**Re-running is idempotent** — duplicate chunks are skipped by default:

```bash
# Skip duplicates (default)
lfl ingest my_domain --on-duplicate skip

# Overwrite existing
lfl ingest my_domain --on-duplicate overwrite
```

**With embeddings:**

```bash
lfl ingest my_domain --embed --profile baseline_cpu_onnx_small
```

**Custom chunking:**

```bash
lfl ingest my_domain --strategy heading_aware --chunk-size 600 --overlap 80
```

**Supported formats:** PDF, DOCX, XLSX, HTML, TXT, Markdown. With LibreOffice installed: Pages, Numbers, Keynote, legacy Office (DOC, XLS, PPT).

### 3. Benchmark Retrieval Quality

Run a benchmark to measure how well your corpus performs in retrieval:

```bash
lfl benchmark run corpora/programming
```

This will:
1. Load all chunks from the corpus
2. Generate synthetic queries (2 per chunk by default)
3. Run BM25 retrieval
4. Calculate recall@1, recall@3, recall@5, and MRR
5. Score token efficiency
6. Save a timestamped report

**Output Example:**
```
============================================================
  LFL Retrieval Benchmark Report
============================================================
  Corpus       : corpora/programming
  Profile      : baseline_cpu_onnx_small
  Strategy     : naive_paragraph
  Chunk size   : 512 tokens  (overlap: 64)
  Chunks       : 142
  Queries      : 284
------------------------------------------------------------
  Recall@1     : 0.781
  Recall@3     : 0.912
  Recall@5     : 0.954
  MRR          : 0.834
------------------------------------------------------------
  Token cost   : 0.951
  Coverage pen : 0.961
  Efficiency   : 0.959
  FINAL SCORE  : 0.921  ★
------------------------------------------------------------
  Recommendations:
    → Excellent score. Consider publishing this profile + params
      as the recommended ingestion config for this corpus.
------------------------------------------------------------
  Elapsed      : 4.2s
============================================================
```

### 4. Tune Parameters with Sweep

Want to find the best chunking configuration? Run a parameter sweep:

```bash
lfl benchmark sweep corpora/programming
```

This automatically tests 8 configurations:
- 4 chunk sizes (256, 512, 768 tokens)
- 2 overlap settings (32, 64, 128 tokens)
- 3 chunking strategies (naive_paragraph, heading_aware, sliding_window)

The sweep will rank all configurations by final score and recommend the best one.

**Output Example:**
```
LFL Benchmark Comparison
--------------------------------------------------------------------
Strategy             Size  Ovlp    R@1    R@3    R@5    MRR   Score
--------------------------------------------------------------------
heading_aware         512    64  0.781  0.912  0.954  0.834   0.921 ★ BEST
heading_aware         256    32  0.743  0.889  0.941  0.801   0.887
naive_paragraph       512    64  0.712  0.867  0.932  0.778   0.854
...
--------------------------------------------------------------------

Best configuration:
  chunk_size=512  overlap=64  strategy=heading_aware
  final_score=0.921  recall@3=0.912
```

### 5. Compare Historical Reports

All benchmark reports are saved to `corpora/<domain>/benchmarks/`. Compare them:

```bash
lfl benchmark compare corpora/programming
```

This shows all saved reports ranked by score, letting you track quality improvements over time.

### 6. Custom Benchmark Parameters

Fine-tune your benchmark run:

```bash
lfl benchmark run corpora/programming \
  --chunk-size 768 \
  --overlap 128 \
  --strategy heading_aware \
  --profile quality_cpu_onnx_base \
  --query-strategy heuristic
```

**Available Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--chunk-size` | Target tokens per chunk | 512 |
| `--overlap` | Token overlap between chunks | 64 |
| `--strategy` | Chunking strategy | naive_paragraph |
| `--profile` | Embedding profile | baseline_cpu_onnx_small |
| `--query-strategy` | Query generation method | heuristic |
| `--qpc` | Queries per chunk | 2 |
| `--top-k` | Top-k for retrieval | 5 |
| `--no-reuse` | Regenerate queries | false |

**Chunking Strategies:**
- `naive_paragraph` — Split on double newlines, pack to chunk_size
- `heading_aware` — Split at markdown headings first
- `sliding_window` — Fixed-size windows with overlap
- `semantic` — Split at semantic boundaries (future)

**Query Strategies:**
- `heuristic` — Fast, pattern-based (default)
- `extractive` — TF-IDF key phrases (future)
- `llm` — Use local LLM endpoint (future)

---

## Understanding Scores

### Metrics Explained

**Recall@k**: Percentage of queries where the correct chunk appears in the top k results.
- Recall@1 is strictest (chunk must be #1)
- Recall@3 is the primary optimization target
- Recall@5 shows broader coverage

**MRR (Mean Reciprocal Rank)**: Average of 1/rank for correct chunks.
- MRR of 1.0 means every query's correct chunk is rank #1
- Higher is better

**Token Cost**: Average chunk size / target chunk size
- Normalized to chunk_size parameter
- Lower is better (more efficient)

**Efficiency Score**: recall@3 / token_cost
- Rewards high accuracy with compact chunks

**Coverage Penalty**: Penalizes chunks that exceed 25% of context window
- Ensures chunks fit comfortably in retrieval context

**Final Score**: efficiency_score × coverage_penalty
- **Higher is always better**
- Target: > 0.8 for production corpora

### Score Interpretation

| Score | Quality | Action |
|-------|---------|--------|
| > 0.90 | Excellent | Publish this config |
| 0.75–0.90 | Good | Minor tuning may help |
| 0.50–0.75 | Acceptable | Review recommendations |
| < 0.50 | Poor | Significant adjustment needed |

---

## Tuning Workflow

When creating or updating a corpus:

```
1. Create chunks with initial parameters
2. Run validation to ensure structure is correct
   lfl validate corpora/<domain>
3. Run benchmark sweep to find best config
   lfl benchmark sweep corpora/<domain>
4. Apply recommended parameters and re-create chunks
5. Run validation again to ensure quality baseline
6. Document final parameters in CORPUS.md
```

### What to Tune First

| Symptom | Try This |
|---------|----------|
| Recall@1 < 0.50 | Reduce chunk_size (chunks too large, dilute signal) |
| Recall@3 < 0.75 | Increase overlap (context lost at boundaries) |
| Score < 0.50 | Switch chunking strategy |
| Coverage penalty low | Reduce chunk_size (chunks crowding context window) |
| Token cost high | Check for very large unchunked documents |

---

## Embedding Profiles

The toolkit ships with 5 official profiles:

### baseline_cpu_onnx_small (Default)
- **Model**: BAAI/bge-small-en-v1.5
- **Dimensions**: 384
- **Hardware**: Any CPU
- **Use**: Default for all contributors, CI validation

### quality_cpu_onnx_base
- **Model**: BAAI/bge-base-en-v1.5
- **Dimensions**: 768
- **Hardware**: Any CPU (slower)
- **Use**: Higher quality embeddings when CPU is sufficient

### power_user_cuda
- **Model**: BAAI/bge-large-en-v1.5
- **Dimensions**: 1024
- **Hardware**: NVIDIA GPU
- **Use**: Maximum quality with GPU acceleration

### power_user_rocm
- **Model**: BAAI/bge-large-en-v1.5
- **Dimensions**: 1024
- **Hardware**: AMD GPU (ROCm)
- **Use**: Maximum quality on AMD hardware

### windows_gpu_directml
- **Model**: BAAI/bge-base-en-v1.5
- **Dimensions**: 768
- **Hardware**: Windows DirectML GPU
- **Use**: GPU acceleration on Windows

All profiles are deterministic and reproducible.

---

## Report Format

Benchmark reports are saved as JSON in `corpora/<domain>/benchmarks/`:

```json
{
  "corpus_path": "corpora/programming",
  "profile": "baseline_cpu_onnx_small",
  "params": {
    "chunk_size": 512,
    "chunk_overlap": 64,
    "chunking_strategy": "heading_aware",
    "embedding_profile": "baseline_cpu_onnx_small"
  },
  "chunk_count": 142,
  "query_count": 284,
  "recall_at_1": 0.781,
  "recall_at_3": 0.912,
  "recall_at_5": 0.954,
  "mrr": 0.834,
  "final_score": 0.921,
  "recommendations": [
    "Excellent score. Consider publishing..."
  ],
  "generated_at": "2026-02-26 14:30:00"
}
```

Reports are timestamped and versioned so you never lose history.

---

## Examples

### Simple Validation

```bash
lfl validate corpora/programming
```

### Quick Benchmark

```bash
lfl benchmark run corpora/programming
```

### Full Parameter Sweep

```bash
lfl benchmark sweep corpora/programming
```

### Custom Configuration Test

```bash
lfl benchmark run corpora/programming \
  --chunk-size 1024 \
  --overlap 128 \
  --strategy sliding_window
```

### Compare All Reports

```bash
lfl benchmark compare corpora/programming
```

---

## Troubleshooting

### Error: "No chunks found"

Your corpus directory must have a `chunks/` subdirectory with `.md` files:
```
corpora/programming/
└── chunks/
    ├── chunk_001.md
    └── chunk_002.md
```

### Error: "Missing required field"

All chunks need complete YAML frontmatter. Run validation to see which fields are missing:
```bash
lfl validate corpora/programming
```

### Low Recall Scores

If recall@3 < 0.75:
1. Try reducing chunk_size (smaller, more focused chunks)
2. Increase overlap to reduce boundary losses
3. Switch to heading_aware strategy for structured docs

### High Token Cost

If normalized_token_cost > 1.2:
- Check for very large documents that aren't being chunked
- Reduce max_chunk_tokens parameter
- Verify chunking strategy is appropriate for content type

---

## Further Reading

- [validation.md](docs/KB/Reference/validation.md) — Complete system specification
- [embedding-profiles.md](docs/KB/Reference/embedding-profiles.md) — Profile documentation
- [MEASUREMENT_MODEL.md](docs/KB/Reference/MEASUREMENT_MODEL.md) — Quality metrics explained
- [IMPLEMENTATION_REPORT_2026-02-26.md](docs/IMPLEMENTATION_REPORT_2026-02-26.md) — Implementation details

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/justincheshire-star/Little-Free-Library/issues
- Discussions: https://github.com/justincheshire-star/Little-Free-Library/discussions

---

**Little Free Library — Take what you need. Leave what you can.**
