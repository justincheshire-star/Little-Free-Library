# Embedding Profiles

Little Free Library uses a **profile-based embedding system** — a small set of named, versioned, and tested configurations that pair a model with a runtime. Profiles are reproducible by design: same profile + same corpus = same vectors.

---

## Why Profiles?

Embedding quality and performance vary significantly across hardware. Rather than exposing raw model and runtime configuration to every contributor, LFL ships a small set of **official profiles** that have been validated for determinism, retrieval quality, and cross-platform behavior.

- **Official profiles** are tested, benchmarked, and supported.
- **Custom profiles** are allowed but marked non-official. Reproducibility is your responsibility.

---

## The Default Runner: FastEmbed

All official profiles use **[FastEmbed](https://github.com/qdrant/fastembed)** as the embedding runner. FastEmbed is ONNX-based, ships curated model weights, handles the download + execution lifecycle cleanly, and has bindings in Python, Rust, Go, and JavaScript — which matters as LFL tooling expands beyond Python.

You do not need to install PyTorch or manage CUDA drivers to use most profiles. FastEmbed handles it.

```bash
pip install fastembed        # CPU profiles
pip install fastembed-gpu    # GPU profiles (CUDA or DirectML)
```

---

## Official Profiles

### 1. `baseline_cpu_onnx_small`

The default. Works on any machine with no GPU required. Fast enough for most corpora.

| Field | Value |
|-------|-------|
| Model | `BAAI/bge-small-en-v1.5` |
| Format | ONNX |
| Runtime | ONNX Runtime CPU |
| Dimensions | 384 |
| Max sequence length | 512 tokens |
| Pooling | CLS |
| Normalize | true |
| Hardware | Any (CPU) |
| Status | ✅ Official |

**When to use**: Default for all contributors. CI validation runs on this profile.

---

### 2. `quality_cpu_onnx_base`

Better retrieval quality at the cost of speed. Still CPU-only, no GPU required.

| Field | Value |
|-------|-------|
| Model | `BAAI/bge-base-en-v1.5` |
| Format | ONNX |
| Runtime | ONNX Runtime CPU |
| Dimensions | 768 |
| Max sequence length | 512 tokens |
| Pooling | CLS |
| Normalize | true |
| Hardware | Any (CPU) |
| Status | ✅ Official |

**When to use**: When retrieval quality matters more than ingestion speed. Recommended for final corpus releases.

---

### 3. `windows_gpu_directml`

ONNX Runtime with the DirectML execution provider. Covers a broad range of Windows GPUs — NVIDIA, AMD, and integrated — without requiring CUDA or ROCm drivers.

| Field | Value |
|-------|-------|
| Model | `BAAI/bge-base-en-v1.5` |
| Format | ONNX |
| Runtime | ONNX Runtime DirectML EP |
| Dimensions | 768 |
| Max sequence length | 512 tokens |
| Pooling | CLS |
| Normalize | true |
| Hardware | Windows GPU (NVIDIA / AMD / integrated via DirectML) |
| Status | ✅ Official |

**When to use**: Windows users who want GPU acceleration without managing CUDA or ROCm. Falls back gracefully to CPU if DirectML is slower on your specific hardware.

```bash
pip install fastembed-gpu
pip install onnxruntime-directml
```

> ⚠️ If DirectML is slower than CPU on your machine (common on some integrated GPUs), switch to `baseline_cpu_onnx_small`.

---

### 4. `power_user_cuda`

Maximum quality and speed for NVIDIA GPU users. Uses SentenceTransformers with CUDA.

| Field | Value |
|-------|-------|
| Model | `BAAI/bge-large-en-v1.5` |
| Format | PyTorch |
| Runtime | SentenceTransformers + CUDA |
| Dimensions | 1024 |
| Max sequence length | 512 tokens |
| Pooling | CLS |
| Normalize | true |
| Hardware | NVIDIA GPU (CUDA 11.8+) |
| Status | ✅ Official |

**When to use**: Power users building high-quality corpora with NVIDIA hardware. Best retrieval quality of any official profile.

```bash
pip install sentence-transformers
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

> ⚠️ PyTorch vectors are not guaranteed bit-identical across different CUDA versions or driver versions. Treat embeddings built with this profile as tied to a specific build environment. Lock your torch version in `requirements.txt`.

---

### 5. `power_user_rocm`

AMD GPU support via ROCm. Best-effort — validated hardware only.

| Field | Value |
|-------|-------|
| Model | `BAAI/bge-base-en-v1.5` |
| Format | PyTorch |
| Runtime | SentenceTransformers + ROCm |
| Dimensions | 768 |
| Max sequence length | 512 tokens |
| Pooling | CLS |
| Normalize | true |
| Hardware | AMD GPU (ROCm 5.6+, validated hardware) |
| Status | ⚠️ Best-effort / Community |

**When to use**: AMD GPU users willing to manage ROCm installation. Consumer AMD GPUs have varying ROCm support — check the [ROCm supported hardware list](https://rocm.docs.amd.com/en/latest/release/gpu_os_support.html) before committing.

```bash
pip install sentence-transformers
pip install torch --index-url https://download.pytorch.org/whl/rocm5.6
```

> ⚠️ This profile is community-maintained. Reproducibility across machines is best-effort. If ROCm is flaky on your hardware, use `baseline_cpu_onnx_small`.

---

## Profile Comparison

| Profile | Model | Dims | Hardware | Quality | Speed | Reproducibility |
|---------|-------|------|----------|---------|-------|-----------------|
| `baseline_cpu_onnx_small` | BGE small | 384 | Any CPU | Good | Fast | ✅ Deterministic |
| `quality_cpu_onnx_base` | BGE base | 768 | Any CPU | Better | Medium | ✅ Deterministic |
| `windows_gpu_directml` | BGE base | 768 | Windows GPU | Better | Fast | ✅ Deterministic |
| `power_user_cuda` | BGE large | 1024 | NVIDIA CUDA | Best | Fastest | ⚠️ Version-locked |
| `power_user_rocm` | BGE base | 768 | AMD ROCm | Better | Fast | ⚠️ Best-effort |

---

## Using a Profile

```bash
# Embed a corpus using the default profile
lfl embed corpora/programming --profile baseline_cpu_onnx_small

# Embed with a higher quality profile
lfl embed corpora/programming --profile quality_cpu_onnx_base

# Embed on Windows with GPU acceleration
lfl embed corpora/programming --profile windows_gpu_directml
```

The profile is recorded in the corpus `manifest.json` so consumers know exactly how the embeddings were produced.

---

## Custom Profiles

You can define a custom profile by creating a file in `profiles/custom/<your_profile_id>.json` following the same schema as official profiles. Custom profiles are ignored by CI validation and not guaranteed to be reproducible across machines.

---

## Benchmark Harness

Each official profile is validated against a standard benchmark before release:

- **Determinism**: same corpus built twice produces identical vector hashes (within fp32 tolerance for ONNX, version-locked for PyTorch)
- **Retrieval sanity**: a fixed query set returns expected top-k documents
- **Speed**: throughput (chunks/sec) and peak memory recorded
- **Cross-platform**: Windows + Linux nearest-neighbor agreement checked for ONNX profiles

Run the benchmark locally:

```bash
lfl benchmark --profile baseline_cpu_onnx_small --corpus corpora/programming
```

---

## Profile Manifest Schema

Each profile is defined as a JSON manifest in `profiles/<profile_id>.json`. See the [profiles/](../profiles/) directory for all official manifests.

Key fields:

```json
{
  "id": "baseline_cpu_onnx_small",
  "model_name": "BAAI/bge-small-en-v1.5",
  "format": "onnx",
  "runtime": "onnxruntime-cpu",
  "dimensions": 384,
  "max_seq_len": 512,
  "pooling": "cls",
  "normalize": true,
  "runner": "fastembed",
  "status": "official",
  "hardware": ["cpu"],
  "onnx_model_sha256": "",
  "tokenizer_sha256": "",
  "fastembed_model_id": "BAAI/bge-small-en-v1.5",
  "chunking_version": "1.0.0",
  "text_normalization_version": "1.0.0"
}
```

---

*Profile decisions are versioned. Changing a profile's model or runtime is a breaking change and requires a new profile ID.*
