"""
Test API Metrics Implementation
Quick validation script for Phase 2 completion
"""

import sys
sys.path.insert(0, '.')

from src.mlops.api_metrics import get_metrics_collector


def test_metrics_collector():
    """Test that metrics collector works correctly"""
    print("\n" + "="*60)
    print("TESTING API METRICS COLLECTOR")
    print("="*60 + "\n")
    
    # Get global instance
    collector = get_metrics_collector()
    
    # Reset to start fresh
    collector.reset()
    
    # Simulate some queries
    print("Simulating 10 queries...")
    for i in range(10):
        # Mix of successful and failed queries
        success = i % 5 != 0  # Every 5th query fails
        cache_hit = i % 3 == 0  # Every 3rd query is cache hit
        
        collector.record_query(
            success=success,
            latency_ms=100 + (i * 10),
            cache_hit=cache_hit and success,  # Only cache hits if successful
            input_tokens=700 + (i * 50) if not cache_hit else 0,
            output_tokens=200 if not cache_hit else 0,
            compression_ratio=0.7
        )
    
    # Get metrics
    metrics = collector.get_metrics()
    
    # Display results
    print("\n📊 METRICS RESULTS:")
    print("-" * 60)
    print(f"Total Queries: {metrics['total_queries']}")
    print(f"Successful: {metrics['successful_queries']}")
    print(f"Failed: {metrics['failed_queries']}")
    print(f"Success Rate: {metrics['success_rate_percent']}%")
    print()
    print(f"Avg Latency: {metrics['avg_latency_ms']} ms")
    print(f"P50 Latency: {metrics['p50_latency_ms']} ms")
    print(f"P95 Latency: {metrics['p95_latency_ms']} ms")
    print(f"P99 Latency: {metrics['p99_latency_ms']} ms")
    print()
    print(f"Cache Hits: {metrics['cache_hits']}")
    print(f"Cache Misses: {metrics['cache_misses']}")
    print(f"Cache Hit Rate: {metrics['cache_hit_rate_percent']}%")
    print()
    cost = metrics['cost_metrics']
    print(f"Baseline Cost: ${cost['baseline_cost_usd']:.4f}")
    print(f"Actual Cost: ${cost['actual_cost_usd']:.4f}")
    print(f"Total Savings: ${cost['total_savings_usd']:.4f}")
    print(f"Savings %: {cost['savings_percent']:.2f}%")
    
    # Persist metrics
    print("\n💾 Persisting metrics to disk...")
    collector.persist_metrics()
    print(f"✅ Metrics saved to: {collector.persist_path}")
    
    # Validation
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)
    
    assert metrics['total_queries'] == 10, "Should have 10 queries"
    assert metrics['successful_queries'] == 8, "Should have 8 successful"
    assert metrics['failed_queries'] == 2, "Should have 2 failed"
    assert metrics['cache_hits'] >= 2, f"Should have at least 2 cache hits, got {metrics['cache_hits']}"
    assert metrics['avg_latency_ms'] > 0, "Should have positive avg latency"
    assert cost['total_savings_usd'] >= 0, "Should have non-negative savings"
    
    print("✅ All validations passed!")
    print("\n" + "="*60)
    print("✅ API METRICS COLLECTOR TEST COMPLETE!")
    print("="*60 + "\n")
    
    return metrics


if __name__ == "__main__":
    try:
        metrics = test_metrics_collector()
        print("\n✅ Phase 2: API Metrics Implementation - COMPLETE!\n")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
