#!/usr/bin/env python3
"""
Download FastEmbed ONNX models to local cache for offline use.
"""
import sys
from pathlib import Path

try:
    from fastembed import TextEmbedding
except ImportError:
    print("ERROR: fastembed not installed. Run: pip install fastembed")
    sys.exit(1)

# Models to download
MODELS = [
    "BAAI/bge-small-en-v1.5",  # 384-dim, ~130 MB, baseline
    "BAAI/bge-base-en-v1.5",   # 768-dim, ~400 MB, quality
]

def main():
    """Download and cache FastEmbed models locally."""
    models_dir = Path(__file__).parent.parent / "models" / "fastembed"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading FastEmbed ONNX models...")
    print(f"Cache directory: {models_dir}")
    print()
    
    for model_name in MODELS:
        print(f"Downloading {model_name}...")
        try:
            # Initialize model (downloads if not cached)
            model = TextEmbedding(
                model_name=model_name,
                cache_dir=str(models_dir),
            )
            
            # Test embedding
            test_vec = list(model.embed(["test"]))[0]
            dim = len(test_vec)
            
            print(f"  ✓ Downloaded and verified ({dim} dimensions)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue
        print()
    
    print("FastEmbed models ready for offline use.")

if __name__ == "__main__":
    main()
