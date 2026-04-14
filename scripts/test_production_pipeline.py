"""
Test script for production pipeline with guardrails
Demonstrates different query scenarios

Usage:
    python scripts/test_production_pipeline.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.production_pipeline import ProductionRAGPipeline


def print_result(title: str, result: dict):
    """Pretty print query result"""
    print(f"\n{'='*70}")
    print(f"🔍 {title}")
    print('='*70)
    print(f"\n**Answer:**\n{result['answer']}\n")
    print(f"**Metadata:**")
    print(f"  - Model: {result['model_used']}")
    print(f"  - Latency: {result['latency_ms']:.0f}ms")
    print(f"  - Sources: {len(result.get('sources', []))}")
    
    if result.get('guardrail_action'):
        print(f"  - ⚠️ Guardrail: {result['guardrail_action']}")
    
    if result.get('faithfulness_score') is not None:
        print(f"  - 📊 Faithfulness: {result['faithfulness_score']:.2f}")
        if result.get('is_hallucination'):
            print(f"  - 🚨 HALLUCINATION DETECTED")
    
    if result.get('sampled'):
        print(f"  - 🎲 Sampled for evaluation")


def main():
    print("\n🚀 Testing Production RAG Pipeline with Guardrails\n")
    
    # Initialize pipeline (10% sampling, guardrails enabled)
    pipeline = ProductionRAGPipeline(
        sampling_rate=1.0,  # 100% for testing (normally 0.10)
        enable_guardrails=True
    )
    
    # Test cases
    test_queries = [
        # 1. Normal query
        {
            "title": "Normal Query (Definition)",
            "query": "Apa itu KTP elektronik?"
        },
        
        # 2. Ambiguous query
        {
            "title": "Ambiguous Query (Should request clarification)",
            "query": "Berapa lama waktu yang dibutuhkan?"
        },
        
        # 3. Legal query (should add disclaimer)
        {
            "title": "Legal Query (Should add disclaimer)",
            "query": "Apa dasar hukum KTP elektronik dan sanksinya?"
        },
        
        # 4. Out-of-scope query
        {
            "title": "Out-of-Scope Query (Pricing)",
            "query": "Berapa biaya pembuatan KTP elektronik?"
        },
        
        # 5. Cross-domain query
        {
            "title": "Cross-Domain Query",
            "query": "Dokumen apa yang diperlukan untuk mengurus paspor?"
        }
    ]
    
    # Run tests
    for test in test_queries:
        result = pipeline.query(
            question=test["query"],
            force_evaluation=True  # Force evaluation for testing
        )
        print_result(test["title"], result)
    
    # Print stats
    print(f"\n{'='*70}")
    print("📊 PIPELINE STATISTICS")
    print('='*70)
    
    stats = pipeline.get_stats()
    print(f"\nTotal queries: {stats['total_queries']}")
    print(f"Sampled for evaluation: {stats['sampled_queries']} ({stats['evaluation_coverage']:.1f}%)")
    print(f"\nGuardrail Triggers:")
    print(f"  - Ambiguous: {stats['ambiguous_queries']}")
    print(f"  - Legal: {stats['legal_queries']}")
    print(f"  - Out-of-scope: {stats['out_of_scope_queries']}")
    
    print(f"\n✅ Production pipeline test complete!\n")


if __name__ == "__main__":
    main()
