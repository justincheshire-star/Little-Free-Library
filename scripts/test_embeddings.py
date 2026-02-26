#!/usr/bin/env python3
"""
Test both embedding systems (FastEmbed and Sentence-Transformers) to verify
they work with the locally downloaded models.
"""
import sys
from pathlib import Path
from typing import List, Tuple

# Test sentences
TEST_SENTENCES = [
    "Python is a high-level programming language.",
    "Machine learning models require training data.",
    "The quick brown fox jumps over the lazy dog.",
]

def test_fastembed() -> Tuple[bool, str]:
    """Test FastEmbed ONNX embeddings."""
    try:
        from fastembed import TextEmbedding
        import numpy as np
    except ImportError as e:
        return False, f"Import error: {e}"
    
    models_dir = Path(__file__).parent.parent / "models" / "fastembed"
    
    # Test both models
    model_names = [
        "BAAI/bge-small-en-v1.5",
        "BAAI/bge-base-en-v1.5",
    ]
    
    results = []
    for model_name in model_names:
        try:
            model = TextEmbedding(
                model_name=model_name,
                cache_dir=str(models_dir),
            )
            
            # Generate embeddings
            embeddings = list(model.embed(TEST_SENTENCES))
            
            if len(embeddings) != len(TEST_SENTENCES):
                return False, f"{model_name}: Wrong number of embeddings"
            
            # Check dimensions
            first_emb = embeddings[0]
            dim = len(first_emb)
            expected_dim = 384 if "small" in model_name else 768
            
            if dim != expected_dim:
                return False, f"{model_name}: Wrong dimensions ({dim} != {expected_dim})"
            
            # Check embeddings are different
            if np.allclose(embeddings[0], embeddings[1]):
                return False, f"{model_name}: Embeddings are identical (model not working)"
            
            results.append(f"✓ {model_name}: {dim}-dim embeddings OK")
            
        except Exception as e:
            return False, f"{model_name}: {e}"
    
    return True, "\n  ".join(["FastEmbed ONNX:"] + results)

def test_sentence_transformers() -> Tuple[bool, str]:
    """Test Sentence-Transformers PyTorch embeddings."""
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError as e:
        return False, f"Import error: {e}"
    
    models_dir = Path(__file__).parent.parent / "models" / "nomic-embed-text"
    
    if not models_dir.exists():
        return False, f"Model directory not found: {models_dir}"
    
    try:
        # Load model from local directory
        model = SentenceTransformer(str(models_dir), trust_remote_code=True)
        
        # Generate embeddings
        embeddings = model.encode(TEST_SENTENCES, convert_to_numpy=True)
        
        if len(embeddings) != len(TEST_SENTENCES):
            return False, "Wrong number of embeddings"
        
        # Check dimensions
        dim = embeddings.shape[1]
        if dim != 768:
            return False, f"Wrong dimensions ({dim} != 768)"
        
        # Check embeddings are different
        if np.allclose(embeddings[0], embeddings[1]):
            return False, "Embeddings are identical (model not working)"
        
        # Test similarity
        from numpy.linalg import norm
        sim = np.dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
        
        result = [
            "Sentence-Transformers PyTorch:",
            f"✓ nomic-ai/nomic-embed-text-v1.5: {dim}-dim embeddings OK",
            f"✓ Cosine similarity test: {sim:.3f}",
        ]
        
        return True, "\n  ".join(result)
        
    except Exception as e:
        return False, f"Model error: {e}"

def main():
    """Run all embedding tests."""
    print("=" * 70)
    print("Testing Local Embedding Models")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Test FastEmbed
    print("[1/2] Testing FastEmbed ONNX models...")
    success, message = test_fastembed()
    if success:
        print(f"  {message}")
    else:
        print(f"  ✗ FAILED: {message}")
        all_passed = False
    print()
    
    # Test Sentence-Transformers
    print("[2/2] Testing Sentence-Transformers PyTorch model...")
    success, message = test_sentence_transformers()
    if success:
        print(f"  {message}")
    else:
        print(f"  ✗ FAILED: {message}")
        all_passed = False
    print()
    
    # Summary
    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print()
        print("Both embedding systems are working correctly with local models.")
        print("Total model size: ~796 MB")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print()
        print("Check error messages above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
