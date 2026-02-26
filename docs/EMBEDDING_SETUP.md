# Embedding Models Setup Guide

## Overview

Little Free Library now includes **both** embedding systems embedded in the repository:

1. **FastEmbed (ONNX)** - Lightweight, cross-platform, no PyTorch required
2. **Sentence-Transformers (PyTorch)** - Full-featured, GPU-optimized, fine-tuning capable

**Total Size**: ~796 MB tracked with Git LFS

## Quick Start

### Option 1: FastEmbed (Recommended for Most Users)

```bash
# Already installed if you ran: pip install -r requirements.txt
python3 -c "
from fastembed import TextEmbedding
model = TextEmbedding('BAAI/bge-small-en-v1.5', cache_dir='models/fastembed')
print(list(model.embed(['Hello world']))[0][:5])
"
```

### Option 2: Sentence-Transformers (Power Users)

```bash
# Already installed if you ran: pip install -r requirements.txt
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('models/nomic-embed-text', trust_remote_code=True)
print(model.encode('Hello world')[:5])
"
```

## Usage in Little Free Library

### Environment Variables

Set these to control which embedding system is used:

```bash
# Use FastEmbed (default)
export PXCTX_EMBED_PROVIDER=fastembed
export PXCTX_EMBED_MODEL=BAAI/bge-small-en-v1.5

# Or use Sentence-Transformers
export PXCTX_EMBED_PROVIDER=sentence-transformers
export PXCTX_EMBED_MODEL=models/nomic-embed-text
```

### In Python Code

```python
# Option 1: FastEmbed
from fastembed import TextEmbedding
model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    cache_dir="models/fastembed"
)
embeddings = list(model.embed(["text1", "text2"]))

# Option 2: Sentence-Transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(
    "models/nomic-embed-text",
    trust_remote_code=True
)
embeddings = model.encode(["text1", "text2"])
```

## Model Comparison

| Feature | FastEmbed | Sentence-Transformers |
|---------|-----------|----------------------|
| **Models Included** | bge-small (384d), bge-base (768d) | nomic-embed-text-v1.5 (768d) |
| **Total Size** | ~273 MB | ~523 MB |
| **Dependencies** | ONNX Runtime (~100 MB) | PyTorch (~2 GB with CUDA) |
| **Cold Start** | Fast (<1s) | Slower (~3-5s) |
| **CPU Performance** | Excellent | Good |
| **GPU Support** | Yes (DirectML, CUDA) | Yes (CUDA, ROCm, MPS) |
| **Model Ecosystem** | Curated ONNX models | Full HuggingFace Hub |
| **Fine-tuning** | No | Yes |
| **License** | MIT/Apache 2.0 | Apache 2.0 |

## When to Use Each

### Use FastEmbed If:
- ✅ You want minimal dependencies
- ✅ You're on Windows and want GPU without CUDA
- ✅ You need fast cold start times
- ✅ You're deploying in containers/CI
- ✅ Cross-platform consistency matters

### Use Sentence-Transformers If:
- ✅ You need access to latest research models
- ✅ You want to fine-tune embeddings
- ✅ You have CUDA and want maximum GPU performance
- ✅ You're already using PyTorch in your stack
- ✅ You need specific model architectures

## Testing

Run the test suite to verify both systems work:

```bash
python3 scripts/test_embeddings.py
```

Expected output:
```
======================================================================
Testing Local Embedding Models
======================================================================

[1/2] Testing FastEmbed ONNX models...
  FastEmbed ONNX:
  ✓ BAAI/bge-small-en-v1.5: 384-dim embeddings OK
  ✓ BAAI/bge-base-en-v1.5: 768-dim embeddings OK

[2/2] Testing Sentence-Transformers PyTorch model...
  Sentence-Transformers PyTorch:
  ✓ nomic-ai/nomic-embed-text-v1.5: 768-dim embeddings OK
  ✓ Cosine similarity test: 0.471

======================================================================
✓ ALL TESTS PASSED
```

## Git LFS

Large model files (`.onnx`, `.bin`, `.safetensors`) are tracked with Git LFS.

After cloning the repo:
```bash
git lfs pull  # Download model files (~796 MB)
```

## Offline Usage

Both embedding systems work **completely offline** once models are downloaded:
- FastEmbed: Uses cached ONNX files in `models/fastembed/`
- Sentence-Transformers: Uses model files in `models/nomic-embed-text/`

No internet connection required after initial setup.

## Manual Download

If you need to re-download models:

```bash
# FastEmbed models
python3 scripts/download_fastembed_models.py

# Sentence-Transformers model
python3 scripts/download_sentence_transformers_model.py
```

## Troubleshooting

### "Module not found: fastembed"
```bash
pip install fastembed
```

### "Module not found: sentence_transformers"
```bash
pip install sentence-transformers einops
```

### "No module named 'einops'"
```bash
pip install einops
```

### Models downloading on first use
The models are already in the repo. Ensure you're pointing to the correct cache directory:
- FastEmbed: `cache_dir="models/fastembed"`
- Sentence-Transformers: Model path should be `"models/nomic-embed-text"`

### Git LFS files not downloaded
```bash
git lfs install
git lfs pull
```

## Performance Tips

### FastEmbed
- Use `bge-small-en-v1.5` for speed (384-dim)
- Use `bge-base-en-v1.5` for quality (768-dim)
- Set `batch_size=32` or higher for bulk encoding
- DirectML on Windows: `pip install onnxruntime-directml`

### Sentence-Transformers
- Use GPU if available: Model auto-detects CUDA
- Normalize embeddings: `normalize_embeddings=True`
- Mixed precision on GPU: `model.half()` (requires GPU)
- Batch encoding: `model.encode(texts, batch_size=32)`

## Related Documentation

- [Embedding Profiles](docs/KB/Reference/embedding-profiles.md) - Official profile configurations
- [Contributor Onboarding](contributors/ONBOARDING.md) - Setup guide for contributors
- [Benchmarking Guide](contributors/BENCHMARKING_GUIDE.md) - Measuring retrieval quality
