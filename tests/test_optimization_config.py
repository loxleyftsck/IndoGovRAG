"""
Tests for optimization config (BET-001)
"""

import pytest
from config.optimization_config import OPTIMIZATION_CONFIG, should_use_optimization


def test_config_structure():
    """Verify config has all required keys"""
    assert "version" in OPTIMIZATION_CONFIG
    assert "enabled" in OPTIMIZATION_CONFIG
    assert "compression" in OPTIMIZATION_CONFIG
    assert "caching" in OPTIMIZATION_CONFIG
    assert "feature_flags" in OPTIMIZATION_CONFIG
    assert "monitoring" in OPTIMIZATION_CONFIG
    assert "safety" in OPTIMIZATION_CONFIG


def test_default_rollout_is_zero():
    """Safety: default rollout must be 0%"""
    assert OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] == 0


def test_compression_ratio():
    """Config #8 must use ratio 0.7"""
    assert OPTIMIZATION_CONFIG["compression"]["ratio"] == 0.7


def test_cache_threshold():
    """Config #8 must use threshold 0.95"""
    assert OPTIMIZATION_CONFIG["caching"]["threshold"] == 0.95


def test_retrieval_mode():
    """Config #8 must use single_stage"""
    assert OPTIMIZATION_CONFIG["retrieval"]["mode"] == "single_stage"


def test_traffic_splitting_deterministic():
    """Same user_id should always get same result"""
    user1 = "user_123"
    
    # Save original rollout
    original = OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"]
    
    # Set to 50%
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = 50
    
    result1 = should_use_optimization(user1)
    result2 = should_use_optimization(user1)
    result3 = should_use_optimization(user1)
    
    assert result1 == result2 == result3  # Deterministic
    
    # Restore
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = original


def test_traffic_splitting_percentage():
    """Roughly 50% should be assigned when rollout=50"""
    # Save original
    original = OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"]
    
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = 50
    
    # Test 1000 users
    users = [f"user_{i}" for i in range(1000)]
    optimized_count = sum(1 for u in users if should_use_optimization(u))
    
    # Should be ~500 ± 50 (5% margin)
    assert 450 <= optimized_count <= 550
    
    # Restore
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = original


def test_rollout_zero_returns_false():
    """When rollout=0, no users should get optimization"""
    assert OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] == 0
    assert should_use_optimization("any_user") == False


def test_rollout_hundred_returns_true():
    """When rollout=100, all users should get optimization"""
    # Save original
    original = OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"]
    
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = 100
    
    assert should_use_optimization("any_user") == True
    
    # Restore
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = original


def test_killswitch():
    """Killswitch disables all optimization"""
    # Save originals
    original_rollout = OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"]
    original_killswitch = OPTIMIZATION_CONFIG["feature_flags"]["killswitch_enabled"]
    
    # Set to 100% but killswitch disabled
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = 100
    OPTIMIZATION_CONFIG["feature_flags"]["killswitch_enabled"] = False
    
    assert should_use_optimization("any_user") == False
    
    # Restore
    OPTIMIZATION_CONFIG["feature_flags"]["killswitch_enabled"] = original_killswitch
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = original_rollout


def test_master_switch():
    """Master enabled=False disables everything"""
    # Save originals
    original_enabled = OPTIMIZATION_CONFIG["enabled"]
    original_rollout = OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"]
    
    # Disable master switch
    OPTIMIZATION_CONFIG["enabled"] = False
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = 100
    
    assert should_use_optimization("any_user") == False
    
    # Restore
    OPTIMIZATION_CONFIG["enabled"] = original_enabled
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = original_rollout


def test_safety_thresholds_exist():
    """Verify safety thresholds are configured"""
    safety = OPTIMIZATION_CONFIG["safety"]
    assert safety["max_error_rate"] == 0.10
    assert safety["max_p95_latency_seconds"] == 15.0
    assert safety["min_faithfulness"] == 0.74
    assert safety["min_cache_hit_rate"] == 0.30
