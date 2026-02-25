# Corpus Ingestion & Usage SOP

**Status**: Active  
**Owner**: Repository Maintainers  
**Version**: 2.0.0  
**Last Updated**: February 25, 2026  
**Trigger**: Ingesting corpora or integrating with RAG pipelines

---

## 🎯 Purpose

Define the process for ingesting Little Free Library corpora into RAG systems and using them in production. Covers validation, ingestion patterns, and integration best practices.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│             Little Free Library → RAG Integration             │
├──────────────────┬──────────────────┬──────────────────────┤
│                  │                  │                      │
│   ┌──────────┐   │   ┌──────────┐   │   ┌──────────────┐   │
│   │  Corpus  │   │   │  Ingest  │   │   │  RAG System  │   │
│   │          │   │   │          │   │   │              │   │
│   │ • Chunks │───▶   │ • Parse  │───▶   │ • Index      │   │
│   │ • Meta   │   │   │ • Embed  │   │   │ • Retrieve   │   │
│   │ • License│   │   │ • Index  │   │   │ • Generate   │   │
│   └──────────┘   │   └──────────┘   │   └──────────────┘   │
│                  │                  │                      │
│        ▼         │        ▼         │          ▼           │
│   ┌──────────┐   │   ┌──────────┐   │   ┌──────────────┐   │
│   │ Markdown │   │   │Embeddings│   │   │   Context    │   │
│   │  Files   │   │   │ Vectors  │   │   │  to Agent    │   │
│   └──────────┘   │   └──────────┘   │   └──────────────┘   │
│                  │                  │                      │
└──────────────────┴──────────────────┴──────────────────────┘
```

---

## 📁 Corpus Structure

### Standard Format

```
corpora/
└── <domain>/
    ├── CORPUS.md           # Corpus manifest
    ├── sources.json        # Provenance documentation
    ├── chunks/             # Pre-chunked content
    │   ├── chunk_001.md
    │   ├── chunk_002.md
    │   └── ...
    └── embeddings/         # Optional pre-computed embeddings
        └── vectors.npy
```

### Metadata Schema

Each chunk has YAML frontmatter:

```yaml
---
title: "Content Title"
domain: domain_name
subdomain: subdomain_name
source: https://original-url
source_license: License-ID
source_id: matching_sources_json_id
source_path: path/within/source
retrieved_at: YYYY-MM-DD
verified: documented|automated|manual
importance: 0.0-1.0  # Optional quality signal
---

# Content

Chunk text content here...
```

---

## 1. Corpus Validation (Pre-Ingestion)

### 1.1 Prerequisites

Before ingesting any corpus:

```bash
# Verify corpus structure
ls corpora/<domain>/CORPUS.md
ls corpora/<domain>/sources.json
ls corpora/<domain>/chunks/

# Validate corpus quality
python scripts/validate_corpus.py --corpus corpora/<domain>

# Check embeddings (if provided)
python scripts/validate_vectorset.py --corpus corpora/<domain>
```

### 1.2 Validation Checklist

- [ ] CORPUS.md exists and is complete
- [ ] sources.json contains all referenced sources
- [ ] All chunks have valid YAML frontmatter
- [ ] All required metadata fields present
- [ ] License information documented
- [ ] No validation errors from `validate_corpus.py`

---

## 2. Corpus Ingestion Methods

### 2.1 Method A: Using pxctx (Recommended)

For systems using the pxctx RAG framework:

```bash
# Ingest entire corpus
python -m pxctx ingest corpora/programming \
  --recursive \
  --pattern "*.md" \
  --tier long_lived \
  --tags kb,programming \
  --on-duplicate update

# Ingest specific subdomain
python -m pxctx ingest corpora/programming/chunks \
  --pattern "chunk_*.md" \
  --tier long_lived \
  --tags programming,python \
  --metadata-source yaml_frontmatter
```

**Options**:

| Option              | Description                    | Default          |
| ------------------- | ------------------------------ | ---------------- |
| `--tier`            | Context tier (working/long_lived/treasure) | `long_lived` |
| `--tags`            | Comma-separated tags           | —                |
| `--on-duplicate`    | How to handle duplicates       | `skip`           |
| `--pattern`         | File glob pattern              | `*.md`           |
| `--recursive`       | Recurse into subdirectories    | `false`          |
| `--metadata-source` | Metadata extraction method     | `yaml_frontmatter` |

### 2.2 Method B: LlamaIndex

```python
from llama_index import SimpleDirectoryReader, VectorStoreIndex

# Load corpus chunks
documents = SimpleDirectoryReader(
    "corpora/programming/chunks",
    file_extractor={".md": "UnstructuredReader"}
).load_data()

# Extract metadata from YAML frontmatter
for doc in documents:
    # Parse YAML frontmatter
    frontmatter = parse_yaml_frontmatter(doc.text)
    doc.metadata.update(frontmatter)

# Create index
index = VectorStoreIndex.from_documents(documents)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("How do Python async generators work?")
```

### 2.3 Method C: LangChain

```python
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import MarkdownTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Load corpus (already pre-chunked)
loader = DirectoryLoader(
    "corpora/programming/chunks",
    glob="**/*.md"
)
documents = loader.load()

# Parse metadata from YAML frontmatter
for doc in documents:
    frontmatter = parse_yaml_frontmatter(doc.page_content)
    doc.metadata.update(frontmatter)

# Create vector store
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=OpenAIEmbeddings()
)

# Query
retriever = vectorstore.as_retriever()
docs = retriever.get_relevant_documents("Python asyncio")
```

### 2.4 Method D: Custom Pipeline

```python
import yaml
import json
from pathlib import Path

def ingest_corpus(corpus_path: str):
    """Ingest Little Free Library corpus into custom RAG system."""
    corpus_path = Path(corpus_path)
    
    # Load sources.json for provenance
    with open(corpus_path / "sources.json") as f:
        sources = json.load(f)
    
    # Load all chunks
    chunks = []
    for chunk_file in (corpus_path / "chunks").glob("*.md"):
        with open(chunk_file) as f:
            content = f.read()
        
        # Parse YAML frontmatter
        if content.startswith("---"):
            _, frontmatter, text = content.split("---", 2)
            metadata = yaml.safe_load(frontmatter)
        else:
            metadata = {}
            text = content
        
        # Enrich with source provenance
        if "source_id" in metadata:
            source = next(s for s in sources if s["source_id"] == metadata["source_id"])
            metadata["source_license"] = source["license"]
            metadata["source_url"] = source["url"]
        
        chunks.append({
            "text": text.strip(),
            "metadata": metadata,
            "file": str(chunk_file)
        })
    
    return chunks

# Use in your system
chunks = ingest_corpus("corpora/programming")
# ... embed, index, etc.
```

---

## 3. Embedding Options

### 3.1 Using Pre-Computed Embeddings

If corpus includes `embeddings/vectors.npy`:

```python
import numpy as np

# Load pre-computed embeddings
embeddings = np.load("corpora/programming/embeddings/vectors.npy")
# Shape: (num_chunks, embedding_dim)

# Load corresponding chunks
chunks = load_chunks("corpora/programming/chunks")

# Use in your vector store
# Note: Verify embedding model compatibility!
```

### 3.2 Generating Fresh Embeddings

```python
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load chunks
chunks = load_chunks("corpora/programming/chunks")

# Generate embeddings
texts = [chunk["text"] for chunk in chunks]
embeddings = model.encode(texts)

# Store in your vector DB
```

**Recommended Models**:

- **nomic-embed-text-v1.5** (768d) - Used for LFL v1.0.0
- **all-MiniLM-L6-v2** (384d) - Fast, lightweight
- **text-embedding-ada-002** (OpenAI) - High quality
- **text-embedding-3-small** (OpenAI) - Balance of quality/cost

---

## 4. Integration Patterns

### 4.1 Pattern: Domain-Specific RAG

Load only relevant corpus:

```python
# For Python development assistant
programming_chunks = ingest_corpus("corpora/programming")

# Filter to Python subdomain
python_chunks = [
    c for c in programming_chunks 
    if c["metadata"].get("subdomain") == "python"
]

# Build specialized index
python_index = build_index(python_chunks)
```

### 4.2 Pattern: Multi-Corpus RAG

Combine multiple corpora:

```python
# Load multiple domains
programming = ingest_corpus("corpora/programming")
web_dev = ingest_corpus("corpora/web-development")
math = ingest_corpus("corpora/mathematics")

# Combine
all_chunks = programming + web_dev + math

# Build unified index with domain filtering
index = build_index(all_chunks, enable_filtering=True)

# Query with domain filter
results = index.query(
    "How to build a React component?",
    filter={"domain": "web-development"}
)
```

### 4.3 Pattern: Tiered Retrieval

Use importance scores for ranking:

```python
def retrieve_with_importance(query, top_k=5):
    """Retrieve chunks, boosting by importance score."""
    results = semantic_search(query, top_k=top_k*2)
    
    # Re-rank using importance
    for result in results:
        importance = result["metadata"].get("importance", 0.5)
        result["score"] *= (0.5 + importance)  # Boost by importance
    
    # Return top-k after re-ranking
    return sorted(results, key=lambda r: r["score"], reverse=True)[:top_k]
```

---

## 5. Best Practices

### 5.1 Metadata Usage

**Do**:
- Use `domain` and `subdomain` for filtering
- Use `importance` for result ranking (if available)
- Include `source` in citations
- Respect `source_license` in outputs

**Don't**:
- Ignore license requirements
- Strip provenance metadata
- Assume all chunks have equal quality

### 5.2 Chunking

**Little Free Library chunks are pre-chunked**, but you may want to re-chunk:

```python
# Re-chunk if needed for your use case
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load pre-chunked content
original_chunks = load_chunks("corpora/programming/chunks")

# Re-chunk for different window size
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Smaller than default
    chunk_overlap=50
)

new_chunks = []
for chunk in original_chunks:
    sub_chunks = splitter.split_text(chunk["text"])
    for sub_chunk in sub_chunks:
        new_chunks.append({
            "text": sub_chunk,
            "metadata": chunk["metadata"]  # Preserve metadata
        })
```

### 5.3 License Compliance

**Always respect source licenses**:

```python
def format_response_with_attribution(response: str, sources: list) -> str:
    """Add proper attribution to AI responses."""
    citations = []
    for source in sources:
        license_name = source["metadata"]["source_license"]
        source_url = source["metadata"]["source"]
        citations.append(f"- {source_url} ({license_name})")
    
    attribution = "\n\n**Sources:**\n" + "\n".join(citations)
    return response + attribution
```

---

## 6. Troubleshooting

### Issue: Embedding dimension mismatch

**Symptom**: `Dimension mismatch: expected 768, got 384`  
**Cause**: Pre-computed embeddings use different model than your system  
**Fix**: Generate fresh embeddings with your model

### Issue: Missing metadata fields

**Symptom**: `KeyError: 'domain'` when filtering  
**Cause**: Chunk missing required metadata  
**Fix**: Run `validate_corpus.py` and fix flagged chunks

### Issue: Poor retrieval quality

**Symptom**: Irrelevant results for queries  
**Check**:
1. Embedding model quality
2. Query preprocessing
3. Retrieval top-k parameter
4. Consider hybrid search (semantic + keyword)

### Issue: License information not preserved

**Symptom**: Citations missing license info  
**Fix**: Ensure metadata is propagated through pipeline:

```python
# Bad: metadata lost
texts = [chunk["text"] for chunk in chunks]

# Good: maintain metadata linkage
chunks_with_metadata = [
    {"text": c["text"], "metadata": c["metadata"]}
    for c in chunks
]
```

---

## 7. Performance Optimization

### 7.1 Lazy Loading

For large corpora:

```python
from typing import Iterator

def lazy_load_corpus(corpus_path: str) -> Iterator[dict]:
    """Load chunks one at a time to reduce memory."""
    for chunk_file in Path(corpus_path).glob("chunks/*.md"):
        yield load_chunk(chunk_file)

# Use in batched ingestion
for batch in batched(lazy_load_corpus("corpora/programming"), batch_size=100):
    ingest_batch(batch)
```

### 7.2 Caching

```python
import pickle
from pathlib import Path

def get_cached_embeddings(corpus_path: str, model_name: str):
    """Load or generate embeddings with caching."""
    cache_file = Path(corpus_path) / f"embeddings_{model_name}.pkl"
    
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    
    # Generate and cache
    chunks = load_chunks(corpus_path)
    embeddings = generate_embeddings(chunks, model_name)
    
    with open(cache_file, "wb") as f:
        pickle.dump(embeddings, f)
    
    return embeddings
```

---

## 8. Example: Complete Integration

```python
"""Complete example: Ingest LFL corpus into production RAG system."""
import json
import yaml
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 1. Validate corpus
import subprocess
result = subprocess.run(
    ["python", "scripts/validate_corpus.py", "--corpus", "corpora/programming"],
    capture_output=True
)
if result.returncode != 0:
    raise ValueError("Corpus validation failed!")

# 2. Load corpus
def load_lfl_corpus(corpus_path: str):
    """Load Little Free Library corpus with full metadata."""
    corpus_path = Path(corpus_path)
    
    # Load provenance
    with open(corpus_path / "sources.json") as f:
        sources = {s["source_id"]: s for s in json.load(f)}
    
    # Load chunks
    chunks = []
    for i, chunk_file in enumerate(sorted((corpus_path / "chunks").glob("*.md"))):
        with open(chunk_file) as f:
            content = f.read()
        
        # Parse frontmatter
        if content.startswith("---"):
            _, fm, text = content.split("---", 2)
            metadata = yaml.safe_load(fm)
        else:
            metadata, text = {}, content
        
        # Enrich with source info
        if "source_id" in metadata and metadata["source_id"] in sources:
            metadata["source_info"] = sources[metadata["source_id"]]
        
        chunks.append({
            "id": i,
            "text": text.strip(),
            "metadata": metadata
        })
    
    return chunks

# 3. Generate embeddings
chunks = load_lfl_corpus("corpora/programming")
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode([c["text"] for c in chunks])

# 4. Ingest into Qdrant
client = QdrantClient("localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="lfl_programming",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Upload points
points = [
    PointStruct(
        id=chunk["id"],
        vector=embeddings[i].tolist(),
        payload=chunk["metadata"]
    )
    for i, chunk in enumerate(chunks)
]

client.upload_points(
    collection_name="lfl_programming",
    points=points
)

print(f"Ingested {len(chunks)} chunks into Qdrant")

# 5. Query
results = client.search(
    collection_name="lfl_programming",
    query_vector=model.encode("How do async generators work in Python?").tolist(),
    limit=5
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Source: {result.payload.get('source', 'N/A')}")
    print(f"License: {result.payload.get('source_license', 'N/A')}")
    print()
```

---

## ✅ Quick Reference

```bash
# 1. Validate corpus
python scripts/validate_corpus.py --corpus corpora/<domain>

# 2. Ingest with pxctx (if available)
python -m pxctx ingest corpora/<domain> \
  --recursive \
  --tier long_lived \
  --tags <domain>

# 3. Or use in custom pipeline
# See examples above
```

**Remember**: Always validate before ingesting, respect licenses in outputs, and preserve provenance!
