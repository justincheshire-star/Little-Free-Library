# Models Directory

This directory contains local embedding models for the Little Free Library corpus system.

## Structure

```
models/
├── fastembed/          # FastEmbed ONNX models (cross-platform, no PyTorch)
│   ├── BAAI-bge-small-en-v1.5/
│   └── BAAI-bge-base-en-v1.5/
└── nomic-embed-text/   # Sentence-Transformers PyTorch model
    └── (model files)
```

## Embedding Systems

### 1. FastEmbed (ONNX) - Recommended for Most Users

**Pros:**
- No PyTorch/CUDA installation required
- Smaller dependencies (~100 MB vs ~2 GB)
- Faster cold start
- Official profiles validated
- Cross-platform (CPU, DirectML, CUDA)

**Models:**
- `bge-small-en-v1.5`: 384-dim, ~130 MB, fast
- `bge-base-en-v1.5`: 768-dim, ~400 MB, better quality

**Usage:**
```bash
pip install fastembed
export PXCTX_EMBED_PROVIDER=fastembed
export PXCTX_EMBED_MODEL=BAAI/bge-small-en-v1.5
```

### 2. Sentence-Transformers (PyTorch) - Power Users

**Pros:**
- Wider model ecosystem
- Latest research models
- Fine-tuning capability
- CUDA optimization (if available)

**Model:**
- `nomic-embed-text-v1.5`: 768-dim, ~550 MB, Apache 2.0

**Usage:**
```bash
pip install sentence-transformers
export PXCTX_EMBED_PROVIDER=sentence-transformers
export PXCTX_EMBED_MODEL=nomic-ai/nomic-embed-text-v1.5
```

## Auto-Detection

The system will automatically:
1. Check for local models first (this directory)
2. Fall back to downloading from HuggingFace if needed
3. Cache downloads for future use

## Model Download

Models are tracked with Git LFS. After cloning:

```bash
git lfs pull
```

This downloads all large model files (~1-2 GB total).

## Manual Download

If Git LFS is unavailable, manually download:

**FastEmbed:** Models auto-download on first use via fastembed library.

**Sentence-Transformers:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('nomic-ai/nomic-embed-text-v1.5')
model.save('models/nomic-embed-text/')
```
