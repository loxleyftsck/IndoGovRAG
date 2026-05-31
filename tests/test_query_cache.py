"""Tests for QueryCache module (mock file I/O)"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from src.retrieval.query_cache import QueryCache, CachedResult, CachedRAGPipeline


@pytest.fixture
def cache():
    return QueryCache(max_size=10, default_ttl=60)


class TestCachedResult:
    def test_creation(self):
        result = CachedResult(result="Test", timestamp=time.time(), ttl=3600)
        assert result.result == "Test"
        assert result.ttl == 3600

    def test_is_expired_false(self):
        result = CachedResult(result="Test", timestamp=time.time(), ttl=3600)
        assert result.is_expired() is False

    def test_is_expired_true(self):
        result = CachedResult(result="Test", timestamp=time.time() - 7200, ttl=3600)
        assert result.is_expired() is True


class TestQueryCache:
    def test_init(self):
        cache = QueryCache(max_size=100, default_ttl=7200)
        assert cache.max_size == 100
        assert cache.default_ttl == 7200
        assert len(cache) == 0

    def test_generate_key_consistency(self, cache):
        key1 = cache._generate_key("Test", {"top_k": 5})
        key2 = cache._generate_key("Test", {"top_k": 5})
        assert key1 == key2

    def test_generate_key_different_queries(self, cache):
        key1 = cache._generate_key("Query 1", None)
        key2 = cache._generate_key("Query 2", None)
        assert key1 != key2

    def test_generate_key_different_options(self, cache):
        key1 = cache._generate_key("Test", {"top_k": 5})
        key2 = cache._generate_key("Test", {"top_k": 10})
        assert key1 != key2

    def test_put_and_get(self, cache):
        cache.put("Test", "Result")
        result = cache.get("Test")
        assert result == "Result"

    def test_get_missing_key(self, cache):
        result = cache.get("Non-existent")
        assert result is None
        assert cache.misses == 1

    def test_cache_hit_increments_hits(self, cache):
        cache.put("Test", "Result")
        cache.get("Test")
        cache.get("Test")
        assert cache.hits == 2

    def test_cache_miss_increments_misses(self, cache):
        cache.get("Non-existent")
        assert cache.misses == 1

    def test_lru_eviction_on_max_size(self):
        cache = QueryCache(max_size=3)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        cache.put("key4", "value4")
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_access_moves_to_end(self):
        cache = QueryCache(max_size=3)
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        cache.get("key1")
        cache.put("key4", "value4")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None

    def test_expired_entry_returns_none(self, cache):
        cache.put("Test", "Result", ttl=1)
        time.sleep(1.1)
        result = cache.get("Test")
        assert result is None

    def test_expired_entry_increments_expirations(self, cache):
        cache.put("Test", "Result", ttl=1)
        time.sleep(1.1)
        cache.get("Test")
        assert cache.expirations == 1

    def test_put_with_custom_ttl(self, cache):
        cache.put("Test", "Result", ttl=1)
        time.sleep(0.5)
        result = cache.get("Test")
        assert result == "Result"

    def test_put_updates_existing_key(self, cache):
        cache.put("Test", "Value1")
        cache.put("Test", "Value2")
        result = cache.get("Test")
        assert result == "Value2"

    def test_clear(self, cache):
        cache.put("key1", "value1")
        cache.clear()
        assert len(cache) == 0
        assert cache.hits == 0

    def test_clear_expired(self, cache):
        cache.put("keep", "value", ttl=3600)
        cache.put("expire", "value", ttl=1)
        time.sleep(1.1)
        count = cache.clear_expired()
        assert count == 1
        assert cache.get("keep") == "value"
        assert cache.get("expire") is None

    def test_get_stats(self, cache):
        cache.put("key1", "value1")
        cache.get("key1")
        cache.get("key2")
        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_get_stats_empty_cache(self, cache):
        stats = cache.get_stats()
        assert stats["hit_rate"] == 0.0
        assert stats["size"] == 0

    def test_len(self, cache):
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        assert len(cache) == 2

    def test_repr(self, cache):
        repr_str = repr(cache)
        assert "QueryCache" in repr_str
        assert "hit_rate" in repr_str


class TestCachedRAGPipeline:
    def test_init(self):
        mock_rag = Mock()
        pipeline = CachedRAGPipeline(mock_rag, cache_size=50, ttl=3600)
        assert pipeline.rag_pipeline is mock_rag
        assert pipeline.cache.max_size == 50

    def test_query_caches_result(self):
        mock_rag = Mock()
        mock_rag.query.return_value = {"answer": "Test"}
        pipeline = CachedRAGPipeline(mock_rag)
        result = pipeline.query("Test")
        assert result["from_cache"] is False
        mock_rag.query.assert_called_once()

    def test_query_returns_cached_result(self):
        mock_rag = Mock()
        mock_rag.query.return_value = {"answer": "Fresh"}
        pipeline = CachedRAGPipeline(mock_rag)
        pipeline.query("Test")
        result = pipeline.query("Test")
        assert result["from_cache"] is True
        assert mock_rag.query.call_count == 1

    def test_different_queries_not_cached(self):
        mock_rag = Mock()
        mock_rag.query.return_value = {"answer": "Answer"}
        pipeline = CachedRAGPipeline(mock_rag)
        pipeline.query("Query 1")
        pipeline.query("Query 2")
        assert mock_rag.query.call_count == 2

    def test_get_cache_stats(self):
        mock_rag = Mock()
        pipeline = CachedRAGPipeline(mock_rag)
        stats = pipeline.get_cache_stats()
        assert "hit_rate" in stats
        assert "size" in stats

    def test_query_with_options(self):
        mock_rag = Mock()
        mock_rag.query.return_value = {"answer": "Answer"}
        pipeline = CachedRAGPipeline(mock_rag)
        pipeline.query("Test", top_k=5)
        result = pipeline.query("Test", top_k=10)
        assert result["from_cache"] is False
        assert mock_rag.query.call_count == 2
