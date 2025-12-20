"""
Top-K Optimization Experiment

Tests different top-k values for retrieval to find optimal number of chunks.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_search import VectorStore

def run_topk_experiment():
    """Test different top-k values for retrieval."""
    
    print("="*70)
    print(" 🧪 TOP-K OPTIMIZATION EXPERIMENT")
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
        return
    
    print()
    
    # Test queries (Indonesian government topics)
    test_queries = [
        "Apa itu KTP elektronik?",
        "Bagaimana cara mendaftar BPJS Kesehatan?",
        "Siapa yang berhak menerima bantuan sosial?",
        "Apa perbedaan NIK dan NPWP?",
        "Bagaimana prosedur perpanjangan paspor?"
    ]
    
    # Test different top-k values
    top_k_values = [3, 5, 10, 15]
    
    results = []
    
    for top_k in top_k_values:
        print(f"\n🔬 Testing top_k = {top_k}")
        print("-" * 70)
        
        total_scores = []
        retrieval_times = []
        
        for query in test_queries:
            import time
            start = time.time()
            search_results = store.search(query, n_results=top_k)
            elapsed = time.time() - start
            
            retrieval_times.append(elapsed)
            
            if search_results:
                avg_score = sum(r.score for r in search_results) / len(search_results)
                total_scores.append(avg_score)
        
        avg_retrieval_time = sum(retrieval_times) / len(retrieval_times) if retrieval_times else 0
        avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
        
        result = {
            'top_k': top_k,
            'avg_score': round(avg_score, 4),
            'avg_retrieval_ms': round(avg_retrieval_time * 1000, 2),
            'queries_tested': len(test_queries)
        }
        
        results.append(result)
        
        print(f"  ✅ Avg relevance score: {avg_score:.4f}")
        print(f"  ⏱️  Avg retrieval time: {avg_retrieval_time*1000:.2f}ms")
        print(f"  📊 Queries tested: {len(test_queries)}")
    
    # Save results
    output_file = "experiments/results/topk_results.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'experiment': 'topk_optimization',
            'date': '2024-12-17',
            'results': results
        }, f, indent=2)
    
    print("\n" + "="*70)
    print(" 📊 EXPERIMENT SUMMARY")
    print("="*70)
    print()
    
    # Find best balance
    best = max(results, key=lambda x: x['avg_score'])
    
    print(f"🏆 Best Top-K Value:")
    print(f"   top_k: {best['top_k']}")
    print(f"   Avg score: {best['avg_score']}")
    print(f"   Avg retrieval: {best['avg_retrieval_ms']}ms")
    print()
    
    print("📈 Key Findings:")
    print(f"   - Higher k = more context, but slower")
    print(f"   - Lower k = faster, but might miss relevant info")
    print(f"   - Optimal k = {best['top_k']} (best score/speed balance)")
    print()
    
    # Cost analysis (approximate)
    print("💰 Token Cost Estimation (per query):")
    for r in results:
        approx_tokens = r['top_k'] * 512  # Assume ~512 tokens/chunk
        print(f"   top_k={r['top_k']}: ~{approx_tokens} tokens context")
    print()
    
    print(f"💾 Results saved to: {output_file}")
    print()
    
    print("✅ Experiment complete!")


if __name__ == "__main__":
    run_topk_experiment()
