#!/usr/bin/env python3
"""
Download Sentence-Transformers model to local directory for offline use.
"""
import sys
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed. Run: pip install sentence-transformers")
    sys.exit(1)

MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"

def main():
    """Download and save Sentence-Transformers model locally."""
    models_dir = Path(__file__).parent.parent / "models" / "nomic-embed-text"
    
    print(f"Downloading Sentence-Transformers model: {MODEL_NAME}")
    print(f"Target directory: {models_dir}")
    print()
    
    try:
        # Download model (caches automatically in HF cache)
        print("Downloading from HuggingFace...")
        model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
        
        # Save to local directory
        print(f"Saving to {models_dir}...")
        models_dir.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(models_dir))
        
        # Test embedding
        print("Testing model...")
        test_vec = model.encode("test", convert_to_numpy=True)
        dim = test_vec.shape[0] if hasattr(test_vec, 'shape') else len(test_vec)
        
        print()
        print(f"✓ Model downloaded and verified ({dim} dimensions)")
        print(f"✓ Saved to: {models_dir}")
        
        # Show directory size
        import subprocess
        result = subprocess.run(
            ["du", "-sh", str(models_dir)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            size = result.stdout.split()[0]
            print(f"✓ Model size: {size}")
        
    except Exception as e:
        print(f"✗ Failed to download model: {e}")
        sys.exit(1)
    
    print()
    print("Sentence-Transformers model ready for offline use.")

if __name__ == "__main__":
    main()
