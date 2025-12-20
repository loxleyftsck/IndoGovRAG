"""
Test Query Expansion Impact on Retrieval

Compares search results with and without query expansion.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_search import VectorStore
from src.retrieval.query_expander import QueryExpander


def test_query_expansion_impact():
    """Test impact of query expansion on retrieval."""
    
    print("="*70)
    print(" 🧪 QUERY EXPANSION IMPACT TEST")
    print("="*70)
    print()
    
    # Initialize
    store = VectorStore()
    expander = QueryExpander()
    
    doc_count = store.collection.count()
    print(f"✅ Documents indexed: {doc_count}")
    
    if doc_count == 0:
        print()
        print("⚠️  No documents in vector store!")
        return
    
    print()
    
    # Test queries
    queries = [
        "Apa itu KTP elektronik?",
        "Bagaimana mendaftar BPJS?",
        "Syarat mendapat beasiswa"
    ]
    
    for query in queries:
        print("="*70)
        print(f"📝 Query: '{query}'")
        print("="*70)
        
        # Expand query
        expanded = expander.expand(query)
        
        print(f"\n🔍 Original: {expanded.original}")
        print(f"🔍 Expanded: {expanded.expanded}")
        print(f"   Added terms: {', '.join(expanded.added_terms) if expanded.added_terms else 'none'}")
        
        print("\n**Without Expansion:**")
        results_no_exp = store.search(query, n_results=3, use_query_expansion=False)
        for i, r in enumerate(results_no_exp, 1):
            print(f"  {i}. Score: {r.score:.3f} - {r.text[:60]}...")
        
        print("\n**With Expansion:**")
        results_with_exp = store.search(query, n_results=3, use_query_expansion=True)
        for i, r in enumerate(results_with_exp, 1):
            print(f"  {i}. Score: {r.score:.3f} - {r.text[:60]}...")
        
        # Compare
        avg_no_exp = sum(r.score for r in results_no_exp) / len(results_no_exp) if results_no_exp else 0
        avg_with_exp = sum(r.score for r in results_with_exp) / len(results_with_exp) if results_with_exp else 0
        
        improvement = ((avg_with_exp - avg_no_exp) / avg_no_exp * 100) if avg_no_exp > 0 else 0
        
        print(f"\n📊 Average Score:")
        print(f"   Without: {avg_no_exp:.3f}")
        print(f"   With: {avg_with_exp:.3f}")
        print(f"   Change: {improvement:+.1f}%")
        print()
    
    print("="*70)
    print("✅ Test complete!")
    print()
    
    print("📈 Key Insight:")
    print("   Query expansion helps find relevant docs even when")
    print("   exact terms don't match by adding synonyms/acronyms.")


if __name__ == "__main__":
    test_query_expansion_impact()
