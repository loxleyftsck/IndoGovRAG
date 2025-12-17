"""
Test Hybrid Search vs Semantic-Only

Compares BM25+Semantic hybrid search against semantic-only search.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_search import VectorStore

def test_hybrid_vs_semantic():
    """Compare hybrid vs semantic-only search."""
    
    print("="*70)
    print(" 🧪 HYBRID SEARCH VS SEMANTIC-ONLY COMPARISON")
    print("="*70)
    print()
    
    # Initialize vector store
    print("🔧 Initializing vector store...")
    store = VectorStore()
    
    doc_count = store.collection.count()
    print(f"✅ Documents indexed: {doc_count}")
    
    if doc_count == 0:
        print()
        print("⚠️  No documents in vector store!")
        print("   Run: python src/retrieval/vector_search.py")
        print("   to add sample documents first.")
        return
    
    print()
    
    # Test queries
    queries = [
        "KTP elektronik",
        "nomor identitas penduduk",
        "jaminan kesehatan nasional",
    ]
    
    for query in queries:
        print("="*70)
        print(f"📝 Query: '{query}'")
        print("="*70)
       
        print()
        
        # Semantic-only search
        print("🔍 Semantic Search (vector-only):")
        semantic_results = store.search(query, n_results=3)
        
        for i, result in enumerate(semantic_results, 1):
            print(f"  {i}. Score: {result.score:.3f}")
            print(f"     Text: {result.text[:60]}...")
        
        print()
        
        # Hybrid search (alpha=0.5, equal weight)
        print("🔀 Hybrid Search (BM25 + Semantic, alpha=0.5):")
        hybrid_results = store.hybrid_search(query, n_results=3, alpha=0.5)
        
        for i, result in enumerate(hybrid_results, 1):
            sem_score = result.metadata.get('semantic_score', 0)
            bm25_score = result.metadata.get('bm25_score', 0)
            print(f"  {i}. Fused: {result.score:.3f} (Sem: {sem_score:.3f}, BM25: {bm25_score:.3f})")
            print(f"     Text: {result.text[:60]}...")
        
        print()
    
    print("="*70)
    print("✅ Comparison complete!")
    print()
    
    print("📊 Key Insights:")
    print("  - Hybrid search combines keyword matching (BM25) + semantic similarity")
    print("  - Alpha=0.5 gives equal weight to both approaches")
    print("  - Alpha=0.0 = BM25 only, Alpha=1.0 = Semantic only")
    print("  - Hybrid typically improves precision for keyword-heavy queries")


if __name__ == "__main__":
    test_hybrid_vs_semantic()
