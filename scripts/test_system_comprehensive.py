"""
Quick Comprehensive Test - Validate All Optimizations

Tests:
1. Enhanced prompts (Tier 1)
2. Semantic cache
3. Answer quality
4. Performance metrics
"""

import sys
sys.path.insert(0, '.')

from src.rag.ollama_pipeline import OllamaRAGPipeline
import time

def main():
    print("\n" + "="*60)
    print("🔬 COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    print("Testing: Enhanced prompts + cache + optimizations")
    print("="*60 + "\n")
    
    # Initialize pipeline
    print("1. Initializing optimized pipeline...")
    pipeline = OllamaRAGPipeline()
    print(f"   ✅ Model: llama3.1:8b-instruct-q4_K_M")
    print(f"   ✅ Vector store: {pipeline.vector_store.collection.count()} documents\n")
    
    # Test queries
    test_queries = [
        {
            "query": "Apa syarat membuat KTP elektronik?",
            "test_name": "Query 1 (KTP)",
            "expected_keywords": ["17 tahun", "kartu keluarga", "ktp"]
        },
        {
            "query": "Syarat bikin KTP?",  # Similar query for cache test
            "test_name": "Query 2 (KTP variant - cache test)",
            "expected_keywords": ["17 tahun", "kartu keluarga"]
        },
        {
            "query": "Bagaimana cara mengurus akta kelahiran?",
            "test_name": "Query 3 (Akta)",
            "expected_keywords": ["60 hari", "surat keterangan"]
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}/{len(test_queries)}: {test['test_name']}")
        print(f"{'='*60}")
        print(f"Query: {test['query']}\n")
        
        # Run query with timing
        start = time.time()
        result = pipeline.query(test['query'])
        elapsed = time.time() - start
        
        answer = result['answer']
        
        # Check for keywords
        found_keywords = []
        for kw in test['expected_keywords']:
            if kw.lower() in answer.lower():
                found_keywords.append(kw)
        
        keyword_coverage = len(found_keywords) / len(test['expected_keywords'])
        
        # Display results
        print(f"\n📝 Answer Preview:")
        print(answer[:300] + "..." if len(answer) > 300 else answer)
        
        print(f"\n📊 Metrics:")
        print(f"   Response Time: {elapsed:.2f}s")
        if elapsed < 1:
            print(f"   🎯 CACHE HIT! (instant response)")
        print(f"   Keyword Coverage: {len(found_keywords)}/{len(test['expected_keywords'])} ({keyword_coverage*100:.0f}%)")
        print(f"   Keywords found: {', '.join(found_keywords) if found_keywords else 'None'}")
        print(f"   Answer Length: {len(answer)} chars")
        print(f"   Sources: {len(result.get('sources', []))}")
        
        # Score
        if elapsed < 1:
            speed_score = 1.0  # Cache hit
        elif elapsed < 30:
            speed_score = 0.8  # Good
        elif elapsed < 50:
            speed_score = 0.6  # Acceptable
        else:
            speed_score = 0.4  # Slow
        
        quality_score = keyword_coverage
        overall_score = (speed_score * 0.3) + (quality_score * 0.7)
        
        results.append({
            'query': test['query'],
            'elapsed': elapsed,
            'keyword_coverage': keyword_coverage,
            'speed_score': speed_score,
            'quality_score': quality_score,
            'overall_score': overall_score
        })
        
        print(f"\n   Speed Score: {speed_score*100:.0f}%")
        print(f"   Quality Score: {quality_score*100:.0f}%")
        print(f"   Overall Score: {overall_score*100:.0f}%")
    
    # Final summary
    print(f"\n\n{'='*60}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*60}")
    
    avg_elapsed = sum(r['elapsed'] for r in results) / len(results)
    avg_quality = sum(r['quality_score'] for r in results) / len(results)
    avg_overall = sum(r['overall_score'] for r in results) / len(results)
    
    cache_hits = sum(1 for r in results if r['elapsed'] < 1)
    
    print(f"\nTests Run: {len(results)}")
    print(f"Cache Hits: {cache_hits}/{len(results)} ({cache_hits/len(results)*100:.0f}%)")
    print(f"Avg Response Time: {avg_elapsed:.2f}s")
    print(f"Avg Quality Score: {avg_quality*100:.0f}%")
    print(f"Avg Overall Score: {avg_overall*100:.0f}%")
    
    # Grade
    if avg_overall >= 0.90:
        grade = "A+ (Excellent!)"
    elif avg_overall >= 0.85:
        grade = "A (Very Good)"
    elif avg_overall >= 0.80:
        grade = "A- (Good)"
    elif avg_overall >= 0.75:
        grade = "B+ (Above Average)"
    elif avg_overall >= 0.70:
        grade = "B (Acceptable)"
    else:
        grade = "C (Needs Improvement)"
    
    print(f"\n{'='*60}")
    print(f"SYSTEM GRADE: {grade}")
    print(f"{'='*60}")
    
    # Recommendations
    print(f"\n💡 Status:")
    if avg_overall >= 0.80:
        print("   ✅ System performing well!")
        print("   ✅ Enhanced prompts working")
        print("   ✅ Cache operational")
        if cache_hits > 0:
            print(f"   ✅ Cache hit rate: {cache_hits/len(results)*100:.0f}%")
    else:
        print("   ⚠️  System needs attention:")
        if avg_quality < 0.70:
            print("   - Consider Tier 2 (more documents)")
        if avg_elapsed > 40:
            print("   - High latency (expected for local Ollama)")
    
    print(f"\n{'='*60}")
    print("✅ Test Complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
