"""
Tests for Online Evaluator (BET-008)
"""

import pytest
from src.evaluation.online_evaluator import OnlineEvaluator, get_online_evaluator


def test_online_evaluator_initialization():
    """Test online evaluator initializes correctly"""
    evaluator = OnlineEvaluator(sample_rate=0.1, enable_async=False)
    
    assert evaluator.sample_rate == 0.1
    assert evaluator.enable_async == False
    assert evaluator.stats["total_queries"] == 0


def test_should_evaluate_sampling():
    """Test sampling rate works correctly"""
    evaluator = OnlineEvaluator(sample_rate=1.0, enable_async=False)  # 100% sampling
    
    # All should be evaluated
    for i in range(10):
        assert evaluator.should_evaluate() == True
    
    assert evaluator.stats["sampled_queries"] == 10


def test_should_evaluate_no_sampling():
    """Test 0% sampling rate"""
    evaluator = OnlineEvaluator(sample_rate=0.0, enable_async=False)
    
    # None should be evaluated
    for i in range(10):
        assert evaluator.should_evaluate() == False
    
    assert evaluator.stats["sampled_queries"] == 0


def test_evaluate_query_skipped():
    """Test evaluation skipped when not sampled"""
    evaluator = OnlineEvaluator(sample_rate=0.0, enable_async=False)
    
    result = evaluator.evaluate_query(
        question="Test?",
        answer="Test answer",
        contexts=["Context 1"],
        ground_truth=None
    )
    
    assert result is None


def test_evaluate_query_without_ragas():
    """Test evaluation without RAGAS (should skip gracefully)"""
    evaluator = OnlineEvaluator(sample_rate=1.0, enable_async=False)
    evaluator.ragas_available = False
    
    result = evaluator.evaluate_query(
        question="Test?",
        answer="Test answer",
        contexts=["Context 1"]
    )
    
    assert result is None


def test_get_stats():
    """Test getting evaluator statistics"""
    evaluator = OnlineEvaluator(sample_rate=0.5, enable_async=False)
    
    # Sample some queries
    for i in range(100):
        evaluator.should_evaluate()
    
    stats = evaluator.get_stats()
    
    assert stats["total_queries"] == 100
    assert "sample_rate_configured" in stats
    assert "sample_rate_actual" in stats
    assert "ragas_available" in stats


def test_sample_rate_actual():
    """Test actual sample rate calculation"""
    evaluator = OnlineEvaluator(sample_rate=0.5, enable_async=False)
    
    for i in range(100):
        evaluator.should_evaluate()
    
    stats = evaluator.get_stats()
    
    # Should be close to 50% (allow variance)
    assert 30 <= stats["sample_rate_actual"] <= 70


def test_async_evaluation():
    """Test async evaluation mode"""
    evaluator = OnlineEvaluator(sample_rate=1.0, enable_async=True)
    
    result = evaluator.evaluate_query(
        question="Test?",
        answer="Test answer",
        contexts=["Context 1"]
    )
    
    # Async returns status, not full result
    if result:
        assert result.get("status") == "async_submitted"


def test_singleton():
    """Test global singleton instance"""
    evaluator1 = get_online_evaluator()
    evaluator2 = get_online_evaluator()
    
    assert evaluator1 is evaluator2


def test_evaluator_shutdown():
    """Test evaluator shutdown"""
    evaluator = OnlineEvaluator(sample_rate=0.1, enable_async=True)
    
    # Should not crash
    evaluator.shutdown()


@pytest.mark.parametrize("sample_rate", [0.0, 0.1, 0.5, 1.0])
def test_various_sample_rates(sample_rate):
    """Test evaluator works with various sample rates"""
    evaluator = OnlineEvaluator(sample_rate=sample_rate, enable_async=False)
    
    count = 0
    for i in range(100):
        if evaluator.should_evaluate():
            count += 1
    
    # Allow statistical variance
    expected = sample_rate * 100
    assert abs(count - expected) < 30  # Within 30% variance
