"""
Tests for Rollout Manager and Circuit Breaker (BET-010)
"""

import pytest
import time
import os
from src.safety.rollout_manager import RolloutManager, CircuitBreaker, CircuitState, get_rollout_manager


# === CIRCUIT BREAKER TESTS ===

def test_circuit_breaker_initialization():
    """Test circuit breaker initializes in CLOSED state"""
    cb = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
    
    assert cb.get_state() == "CLOSED"
    assert cb.failures == 0
    assert cb.is_open() == False


def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after threshold failures"""
    cb = CircuitBreaker(failure_threshold=3)
    
    # Record failures
    cb.record_failure(Exception("Error 1"))
    assert cb.get_state() == "CLOSED"
    
    cb.record_failure(Exception("Error 2"))
    assert cb.get_state() == "CLOSED"
    
    cb.record_failure(Exception("Error 3"))
    assert cb.get_state() == "OPEN"
    assert cb.is_open() == True


def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker goes to HALF_OPEN after timeout"""
    cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)
    
    # Trigger OPEN
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open() == True
    
    # Wait for timeout
    time.sleep(1.1)
    
    # Should transition to HALF_OPEN
    assert cb.is_open() == False
    assert cb.get_state() == "HALF_OPEN"


def test_circuit_breaker_closes_from_half_open():
    """Test circuit breaker closes after successes in HALF_OPEN"""
    cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1, success_threshold=2)
    
    # Trigger OPEN
    cb.record_failure()
    cb.record_failure()
    
    # Wait and transition to HALF_OPEN
    time.sleep(1.1)
    cb.is_open()  # Trigger state transition
    
    # Record successes
    cb.record_success()
    assert cb.get_state() == "HALF_OPEN"
    
    cb.record_success()
    assert cb.get_state() == "CLOSED"
    assert cb.failures == 0


def test_circuit_breaker_decay_on_success():
    """Test failures decay on success in CLOSED state"""
    cb = CircuitBreaker(failure_threshold=5)
    
    cb.record_failure()
    cb.record_failure()
    assert cb.failures == 2
    
    cb.record_success()
    assert cb.failures == 1


def test_circuit_breaker_manual_reset():
    """Test manual reset of circuit breaker"""
    cb = CircuitBreaker(failure_threshold=2)
    
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open() == True
    
    cb.reset()
    assert cb.get_state() == "CLOSED"
    assert cb.failures == 0


# === ROLLOUT MANAGER TESTS ===

def test_rollout_manager_initialization():
    """Test rollout manager initializes correctly"""
    os.environ["ROLLOUT_PERCENTAGE"] = "0"
    
    manager = RolloutManager()
    assert manager.rollout_percentage == 0
    assert manager.circuit_breaker is not None
    
    del os.environ["ROLLOUT_PERCENTAGE"]


def test_rollout_0_percent():
    """Test 0% rollout blocks all optimization"""
    os.environ["ROLLOUT_PERCENTAGE"] = "0"
    manager = RolloutManager()
    
    for i in range(100):
        assert manager.should_use_optimization(f"user_{i}") == False
    
    stats = manager.get_rollout_stats()
    assert stats["optimization_used"] == 0
    
    del os.environ["ROLLOUT_PERCENTAGE"]


def test_rollout_100_percent():
    """Test 100% rollout allows all optimization"""
    os.environ["ROLLOUT_PERCENTAGE"] = "100"
    manager = RolloutManager()
    
    for i in range(100):
        assert manager.should_use_optimization(f"user_{i}") == True
    
    stats = manager.get_rollout_stats()
    assert stats["optimization_used"] == 100
    
    del os.environ["ROLLOUT_PERCENTAGE"]


def test_rollout_50_percent():
    """Test 50% rollout distributes roughly 50/50"""
    os.environ["ROLLOUT_PERCENTAGE"] = "50"
    manager = RolloutManager()
    
   # Test with deterministic user IDs
    used_count = 0
    for i in range(100):
        if manager.should_use_optimization(f"user_{i}"):
            used_count += 1
    
    # Allow 40-60% range (statistical variance)
    assert 40 <= used_count <= 60
    
    stats = manager.get_rollout_stats()
    assert 40 <= stats["actual_usage_rate"] <= 60
    
    del os.environ["ROLLOUT_PERCENTAGE"]


def test_rollout_consistent_user_assignment():
    """Test same user gets consistent assignment"""
    os.environ["ROLLOUT_PERCENTAGE"] = "50"
    manager = RolloutManager()
    
    user_id = "test_user_123"
    
    # Query 10 times with same user_id
    results = [manager.should_use_optimization(user_id) for _ in range(10)]
    
    # All results should be identical
    assert len(set(results)) == 1
    
    del os.environ["ROLLOUT_PERCENTAGE"]


def test_rollout_circuit_breaker_blocks():
    """Test circuit breaker blocks optimization when open"""
    os.environ["ROLLOUT_PERCENTAGE"] = "100"
    manager = RolloutManager()
    
    # Trigger circuit breaker
    for i in range(5):
        manager.record_failure(Exception(f"Error {i}"))
    
    # Circuit should be open
    assert manager.circuit_breaker.is_open() == True
    
    # Should block optimization
    assert manager.should_use_optimization("user_1") == False
    
    stats = manager.get_rollout_stats()
    assert stats["circuit_breaker_state"] == "OPEN"
    
    del os.environ["ROLLOUT_PERCENTAGE"]


def test_rollout_set_percentage():
    """Test updating rollout percentage"""
    manager = RolloutManager()
    
    manager.set_rollout_percentage(25)
    assert manager.rollout_percentage == 25
    
    manager.set_rollout_percentage(75)
    assert manager.rollout_percentage == 75


def test_rollout_set_percentage_invalid():
    """Test invalid rollout percentage raises error"""
    manager = RolloutManager()
    
    with pytest.raises(ValueError):
        manager.set_rollout_percentage(150)
    
    with pytest.raises(ValueError):
        manager.set_rollout_percentage(-10)


def test_rollout_stats():
    """Test rollout statistics"""
    os.environ["ROLLOUT_PERCENTAGE"] = "50"
    manager = RolloutManager()
    
    for i in range(100):
        manager.should_use_optimization(f"user_{i}")
    
    stats = manager.get_rollout_stats()
    
    assert stats["total_requests"] == 100
    assert stats["rollout_percentage"] == 50
    assert "actual_usage_rate" in stats
    assert "circuit_breaker_state" in stats
    
    del os.environ["ROLLOUT_PERCENTAGE"]


def test_rollout_success_and_failure_tracking():
    """Test success and failure tracking"""
    manager = RolloutManager()
    
    manager.record_success()
    manager.record_success()
    manager.record_failure(Exception("Test error"))
    
    assert manager.circuit_breaker.failures == 1


def test_rollout_singleton():
    """Test global singleton instance"""
    manager1 = get_rollout_manager()
    manager2 = get_rollout_manager()
    
    assert manager1 is manager2


@pytest.mark.parametrize("percentage", [0, 10, 25, 50, 75, 100])
def test_various_rollout_percentages(percentage):
    """Test rollout works at various percentages"""
    os.environ["ROLLOUT_PERCENTAGE"] = str(percentage)
    manager = RolloutManager()
    
    # Should not crash
    for i in range(10):
        manager.should_use_optimization(f"user_{i}")
    
    stats = manager.get_rollout_stats()
    assert 0 <= stats["actual_usage_rate"] <= 100
    
    del os.environ["ROLLOUT_PERCENTAGE"]
