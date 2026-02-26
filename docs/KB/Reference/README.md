# Reference Directory

This directory contains reference implementations, configuration profiles, and technical documentation for the Little Free Library toolkit.

## Contents

### Reference Implementations

Python reference implementations that demonstrate core functionality:

- **[validation.py](validation.py)** - BM25 implementation, vector stores, frontmatter parsing
- **[benchmark.py](benchmark.py)** - Benchmark runner with Recall@k and MRR metrics
- **[cli_benchmark.py](cli_benchmark.py)** - CLI interface for benchmarking
- **[query_gen.py](query_gen.py)** - Query generation strategies (heuristic, extractive, LLM-based)

These reference implementations are integrated into the production `lfl` package.

### Embedding Profiles

JSON configuration profiles for reproducible embeddings:

- **[baseline_cpu_onnx_small.json](baseline_cpu_onnx_small.json)** - Default CPU profile (384-dim)
- **[quality_cpu_onnx_base.json](quality_cpu_onnx_base.json)** - Higher quality CPU (768-dim)
- **[power_user_cuda.json](power_user_cuda.json)** - NVIDIA GPU optimized (1024-dim)
- **[power_user_rocm.json](power_user_rocm.json)** - AMD GPU optimized (1024-dim)
- **[windows_gpu_directml.json](windows_gpu_directml.json)** - Windows GPU support (768-dim)

See **[embedding-profiles.md](embedding-profiles.md)** for complete profile specifications.

### Documentation

- **[validation.md](validation.md)** - Corpus validation system documentation
- **[embedding-profiles.md](embedding-profiles.md)** - Embedding profile specifications and hardware requirements

## Standard Operating Procedures

SOPs have been relocated to **[docs/SOP/](../../SOP/)**:

- [SOP Index](../../SOP/INDEX.md)
- [All SOPs](../../SOP/)
