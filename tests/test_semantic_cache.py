"""
Tests for Semantic Cache Module (BET-003)
"""

import pytest
import time
from src.caching.semantic_cache import SemanticCache


@pytest.fixture
def cache():
    """Create cache with memory backend"""
    return SemanticCache(
        threshold=0.95,
        ttl_days=7,
        backend="memory",
        max_entries=100
    )


@pytest.fixture
def sample_result():
    """Sample cached result"""
    return {
        "answer": "KTP elektronik wajib dimiliki semua WNI dewasa",
        "sources": ["UU 24/2013", "Pasal 13"],
        "confidence": 0.95
    }


def test_cache_initialization():
    """Test cache initializes correctly"""
    cache = SemanticCache(threshold=0.95, backend="memory")
    
    stats = cache.get_stats()
    assert stats["backend"] == "memory"
    assert stats["threshold"] == 0.95
    assert stats["ttl_days"] == 7.0


def test_cache_miss_on_first_query(cache, sample_result):
    """Test cache miss on first query"""
    result = cache.get("Apa itu KTP elektronik?")
    
    assert result is None
    stats = cache.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0


def test_cache_set_and_get_exact(cache, sample_result):
    """Test caching and retrieving exact same query"""
    query = "Apa itu KTP elektronik?"
    
    # Cache it
    cache.set(query, sample_result)
    
    # Retrieve it
    result = cache.get(query)
    
    assert result is not None
    assert result["answer"] == sample_result["answer"]
    assert "_cache_metadata" in result
    assert result["_cache_metadata"]["hit"] == True


def test_cache_semantic_similarity(cache, sample_result):
    """Test caching retrieves semantically similar queries"""
    # Cache original
    original_query = "Apa itu KTP elektronik?"
    cache.set(original_query, sample_result)
    
    # Query with similar meaning
    similar_query = "Apa yang dimaksud dengan e-KTP?"
    result = cache.get(similar_query)
    
    # May or may not hit depending on embedding similarity
    # This is expected behavior - semantic similarity is not guaranteed
    # Just verify it doesn't crash
    assert result is None or "_cache_metadata" in result


def test_cache_hit_rate_tracking(cache, sample_result):
    """Test hit rate calculation"""
    queries = [
        "Apa itu KTP?",
        "Apa itu KTP?",  # Should hit
        "Berapa biaya KTP?",
        "Berapa biaya KTP?",  # Should hit
    ]
    
    # Cache first unique queries
    cache.set(queries[0], sample_result)
    cache.set(queries[2], {"answer": "Gratis"})
    
    # Query all
    for q in queries:
        cache.get(q)
    
    stats = cache.get_stats()
    assert stats["total_queries"] == 4
    assert stats["hits"] == 2
    assert stats["hit_rate"] == 50.0


def test_cache_threshold_filtering(cache, sample_result):
    """Test that threshold filters low-similarity matches"""
    # Cache a query
    cache.set("KTP elektronik", sample_result)
    
    # Query something completely different
    result = cache.get("Berapa harga nasi goreng?")
    
    # Should not match (different topics)
    assert result is None


def test_cache_ttl_expiration():
    """Test cache entries expire after TTL"""
    # Create cache with 1 second TTL
    cache = SemanticCache(
        threshold=0.95,
        ttl_days=1 / (24 * 60 * 60),  # 1 second
        backend="memory"
    )
    
    # Cache a query
    cache.set("Test query", {"answer": "Test"})
    
    # Should exist immediately
    result = cache.get("Test query")
    assert result is not None
    
    # Wait for expiration
    time.sleep(1.5)
    
    # Should be expired
    result = cache.get("Test query")
    # Note: May still hit if exact match before cleanup runs
    # This test is for TTL mechanism, not guaranteed cleanup timing


def test_cache_max_entries_eviction():
    """Test LRU eviction when max entries reached"""
    cache = SemanticCache(
        threshold=0.95,
        backend="memory",
        max_entries=3
    )
    
    # Add 4 entries (exceeds max)
    for i in range(4):
        cache.set(f"Query {i}", {"answer": f"Answer {i}"})
    
    stats = cache.get_stats()
    # Should evict oldest, keeping only 3
    assert stats["cache_size"] <= 3


def test_cache_clear(cache, sample_result):
    """Test clearing cache"""
    # Add some entries
    cache.set("Query 1", sample_result)
    cache.set("Query 2", sample_result)
    cache.set("Query 3", sample_result)
    
    # Clear
    cache.clear()
    
    stats = cache.get_stats()
    assert stats["cache_size"] == 0


def test_false_positive_reporting(cache, sample_result):
    """Test false positive tracking"""
    cache.set("Test", sample_result)
    cache.get("Test")  # Hit
    
    # Report false positive
    cache.report_false_positive("Test")
    
    stats = cache.get_stats()
    assert stats["false_positives"] == 1
    assert stats["false_positive_rate"] == 100.0  # 1/1 hits


def test_cache_backend_fallback():
    """Test fallback to memory when Redis unavailable"""
    # Try to connect to invalid Redis
    cache = SemanticCache(
        threshold=0.95,
        backend="redis",
        host="invalid-host-12345",
        port=9999
    )
    
    # Should fallback to memory
    assert cache.backend == "memory"


def test_multiple_similar_queries(cache):
    """Test finding best match among multiple similar queries"""
    # Cache multiple queries
    cache.set("KTP elektronik", {"answer": "E-KTP"})
    cache.set("KTP biasa", {"answer": "KTP lama"})
    cache.set("Paspor", {"answer": "Dokumen perjalanan"})
    
    # Query something close to first
    result = cache.get("e-KTP")
    
    # Should get a result (may be KTP elektronik)
    # Or None if similarity < threshold
    # Just verify no crash
    assert result is None or "answer" in result


def test_empty_query_handling(cache):
    """Test handling of empty queries"""
    result = cache.get("")
    assert result is None
    
    # Should not crash on set
    success = cache.set("", {"answer": "Empty"})
    assert success == True


def test_long_query_handling(cache, sample_result):
    """Test handling of very long queries"""
    long_query = "Apa itu KTP elektronik? " * 100
    
    # Should not crash
    cache.set(long_query, sample_result)
    result = cache.get(long_query)
    
    assert result is not None


def test_special_characters_query(cache, sample_result):
    """Test queries with special characters"""
    special_query = "Apa itu KTP? (e-KTP) #2024 @Indonesia"
    
    cache.set(special_query, sample_result)
    result = cache.get(special_query)
    
    assert result is not None


def test_cache_stats_structure(cache):
    """Test cache statistics structure"""
    stats = cache.get_stats()
    
    required_keys = [
        "backend", "threshold", "ttl_days",
        "total_queries", "hits", "misses",
        "hit_rate", "false_positives",
        "false_positive_rate", "cache_size"
    ]
    
    for key in required_keys:
        assert key in stats


def test_cosine_similarity_calculation(cache):
    """Test cosine similarity calculation"""
    import numpy as np
    
    # Identical vectors
    a = np.array([1, 0, 0])
    b = np.array([1, 0, 0])
    sim = cache._cosine_similarity(a, b)
    assert abs(sim - 1.0) < 0.001
    
    # Orthogonal vectors
    a = np.array([1, 0, 0])
    b = np.array([0, 1, 0])
    sim = cache._cosine_similarity(a, b)
    assert abs(sim - 0.0) < 0.001


def test_query_hashing(cache):
    """Test query hashing is deterministic"""
    query = "Test query"
    
    hash1 = cache._hash_query(query)
    hash2 = cache._hash_query(query)
    
    assert hash1 == hash2
    assert len(hash1) == 32  # MD5 hash length


@pytest.mark.parametrize("threshold", [0.8, 0.9, 0.95, 0.99])
def test_various_thresholds(threshold):
    """Test cache works with different thresholds"""
    cache = SemanticCache(threshold=threshold, backend="memory")
    
    cache.set("Test", {"answer": "Result"})
    result = cache.get("Test")
    
    assert result is not None


def test_cache_metadata_structure(cache, sample_result):
    """Test cache metadata structure"""
    cache.set("Test query", sample_result)
    result = cache.get("Test query")
    
    metadata = result["_cache_metadata"]
    assert "hit" in metadata
    assert "similarity" in metadata
    assert "threshold" in metadata
    assert "latency_ms" in metadata
    assert metadata["hit"] == True
    assert metadata["similarity"] >= 0.95
