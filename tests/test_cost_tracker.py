"""
Tests for Cost Tracker (BET-006)
"""

import pytest
from src.monitoring.cost_tracker import CostTracker, CostMetrics, get_cost_tracker


def test_cost_tracker_initialization():
    """Test cost tracker initializes correctly"""
    tracker = CostTracker()
    
    assert tracker.metrics.total_queries == 0
    assert tracker.metrics.baseline_cost_usd == 0.0
    assert tracker.metrics.actual_cost_usd == 0.0


def test_calculate_compression_savings():
    """Test compression savings calculation"""
    tracker = CostTracker()
    
    savings = tracker.calculate_compression_savings(
        original_tokens=1000,
        compressed_tokens=700
    )
    
    # 300 tokens saved * $0.00001 per token
    expected = 300 * 0.00001
    assert abs(savings - expected) < 0.000001
    assert tracker.metrics.compression_savings_tokens == 300


def test_calculate_cache_savings_hit():
    """Test cache hit savings calculation"""
    tracker = CostTracker()
    
    savings = tracker.calculate_cache_savings(cache_hit=True)
    
    assert savings == tracker.AVG_COST_PER_QUERY_BASELINE
    assert tracker.metrics.cache_hits == 1
    assert tracker.metrics.cache_misses == 0


def test_calculate_cache_savings_miss():
    """Test cache miss savings calculation"""
    tracker = CostTracker()
    
    savings = tracker.calculate_cache_savings(cache_hit=False)
    
    assert savings == 0.0
    assert tracker.metrics.cache_hits == 0
    assert tracker.metrics.cache_misses == 1


def test_record_query_cost_baseline():
    """Test recording baseline query cost"""
    tracker = CostTracker()
    
    result = tracker.record_query_cost(
        input_tokens=1000,
        output_tokens=200,
        compression_ratio=1.0,
        cache_hit=False
    )
    
    # Baseline cost: 1000*0.00001 + 200*0.00003 = 0.016
    expected_baseline = 1000 *  0.00001 + 200 * 0.00003
    assert abs(result["baseline_cost_usd"] - expected_baseline) < 0.000001
    assert result["savings_percentage"] == 0.0  # No savings


def test_record_query_cost_compressed():
    """Test recording compressed query cost"""
    tracker = CostTracker()
    
    result = tracker.record_query_cost(
        input_tokens=700,  # 30% reduced
        output_tokens=200,
        compression_ratio=0.7,
        cache_hit=False
    )
    
    # Baseline would be 1000 tokens (700 / 0.7)
    # Savings from compression
    assert result["compression_savings_usd"] > 0
    assert result["savings_percentage"] > 0


def test_record_query_cost_cache_hit():
    """Test recording cache hit (minimal cost)"""
    tracker = CostTracker()
    
    result = tracker.record_query_cost(
        input_tokens=0,  # No LLM call
        output_tokens=0,
        compression_ratio=1.0,
        cache_hit=True
    )
    
    # Cache hit saves entire LLM call
    assert result["cache_savings_usd"] > 0
    assert result["actual_cost_usd"] < 0.0001  # Minimal cache lookup cost
    assert result["savings_percentage"] > 99  # Almost 100% savings


def test_get_metrics():
    """Test getting cost metrics"""
    tracker = CostTracker()
    
    # Record some queries
    for i in range(10):
        tracker.record_query_cost(
            input_tokens=700,
            output_tokens=200,
            compression_ratio=0.7,
            cache_hit=False
        )
    
    metrics = tracker.get_metrics()
    
    assert metrics["total_queries"] == 10
    assert metrics["baseline_cost_usd"] > 0
    assert metrics["actual_cost_usd"] > 0
    assert metrics["total_savings_usd"] >= 0
    assert metrics["cache_hit_rate"] == 0  # No cache hits


def test_get_metrics_with_cache():
    """Test metrics with cache hits"""
    tracker = CostTracker()
    
    # 5 cache hits, 5 misses
    for i in range(5):
        tracker.record_query_cost(1000, 200, 1.0, cache_hit=True)
    for i in range(5):
        tracker.record_query_cost(1000, 200, 1.0, cache_hit=False)
    
    metrics = tracker.get_metrics()
    
    assert metrics["total_queries"] == 10
    assert metrics["cache_hits"] == 5
    assert metrics["cache_misses"] == 5
    assert metrics["cache_hit_rate"] == 50.0


def test_cost_savings_percentage():
    """Test savings percentage calculation"""
    tracker = CostTracker()
    
    # Record compressed query
    tracker.record_query_cost(
        input_tokens=700,
        output_tokens=200,
        compression_ratio=0.7,
        cache_hit=False
    )
    
    metrics = tracker.get_metrics()
    
    # Should have some savings
    assert 0 < metrics["savings_percentage"] < 50


def test_reset():
    """Test resetting cost tracker"""
    tracker = CostTracker()
    
    # Record some data
    tracker.record_query_cost(1000, 200, 1.0, False)
    assert tracker.metrics.total_queries == 1
    
    # Reset
    tracker.reset()
    assert tracker.metrics.total_queries == 0
    assert tracker.metrics.baseline_cost_usd == 0.0


def test_singleton():
    """Test global singleton instance"""
    tracker1 = get_cost_tracker()
    tracker2 = get_cost_tracker()
    
    assert tracker1 is tracker2


def test_multiple_queries_accumulation():
    """Test cost accumulates over multiple queries"""
    tracker = CostTracker()
    
    # Record 100 queries
    for i in range(100):
        tracker.record_query_cost(
            input_tokens=700,
            output_tokens=200,
            compression_ratio=0.7,
            cache_hit=False
        )
    
    metrics = tracker.get_metrics()
    
    assert metrics["total_queries"] == 100
    assert metrics["baseline_cost_usd"] > 0.1  # At least $0.1
    assert metrics["total_savings_usd"] > 0


def test_cost_metrics_dataclass():
    """Test CostMetrics dataclass"""
    metrics = CostMetrics(
        total_queries=10,
        baseline_cost_usd=1.0,
        actual_cost_usd=0.7
    )
    
    assert metrics.get_total_savings() == pytest.approx(0.3)
    assert metrics.get_savings_percentage() == pytest.approx(30.0)


@pytest.mark.parametrize("compression_ratio", [0.5, 0.7, 0.9, 1.0])
def test_various_compression_ratios(compression_ratio):
    """Test cost tracking with various compression ratios"""
    tracker = CostTracker()
    
    result = tracker.record_query_cost(
        input_tokens=int(1000 * compression_ratio),
        output_tokens=200,
        compression_ratio=compression_ratio,
        cache_hit=False
    )
    
    # Lower ratio = more savings
    if compression_ratio < 1.0:
        assert result["compression_savings_usd"] > 0
    else:
        assert result["compression_savings_usd"] == 0
