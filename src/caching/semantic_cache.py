"""
Semantic Cache Module using Query Embedding Similarity
Reduces redundant LLM calls by caching similar queries

Part of Phase 1.5 Cost & Latency Optimization (BET-003)
"""

import time
import logging
import hashlib
import json
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Semantic cache using query embedding similarity
    
    Config #8: threshold 0.95, TTL 7 days, Redis backend
    
    Features:
    - Embedding-based similarity matching
    - Redis backend (or in-memory for dev)
    - TTL-based expiration
    - Hit/miss tracking
    - False positive detection
    """
    
    def __init__(
        self,
        threshold: float = 0.95,
        ttl_days: int = 7,
        backend: str = "memory",
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        max_entries: int = 10000,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Initialize semantic cache
        
        Args:
            threshold: Similarity threshold (0-1). 0.95 = 95% similar
            ttl_days: Time-to-live in days
            backend: "redis" or "memory"
            host: Redis host
            port: Redis port
            db: Redis database number
            max_entries: Max cached entries (memory backend only)
            model_name: Sentence transformer model for embeddings
        """
        self.threshold = threshold
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        self.backend_type = backend
        self.max_entries = max_entries
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "false_positives": 0,
            "total_queries": 0
        }
        
        # Initialize embedding model
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        
        # Initialize backend
        if backend == "redis":
            self._init_redis(host, port, db)
        else:
            self._init_memory()
        
        logger.info(f"SemanticCache initialized: backend={backend}, threshold={threshold}, ttl={ttl_days}d")
    
    def _init_redis(self, host: str, port: int, db: int):
        """Initialize Redis backend"""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=False  # Store bytes for embeddings
            )
            # Test connection
            self.redis_client.ping()
            self.backend = "redis"
            logger.info(f"Connected to Redis: {host}:{port}/{db}")
        except ImportError:
            logger.error("redis-py not installed. Run: pip install redis")
            logger.warning("Falling back to memory backend")
            self._init_memory()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            logger.warning("Falling back to memory backend")
            self._init_memory()
    
    def _init_memory(self):
        """Initialize in-memory backend"""
        self.memory_cache = {}  # {query_hash: (embedding, result, timestamp)}
        self.backend = "memory"
        logger.info("Using in-memory cache (not persistent)")
    
    def get(self, query: str) -> Optional[Dict]:
        """
        Get cached result for query if similar query exists
        
        Args:
            query: User query string
            
        Returns:
            Cached result dict or None if no match
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # Encode query
            query_embedding = self._encode_query(query)
            
            # Find similar cached query
            similar = self._find_similar(query, query_embedding)
            
            if similar:
                cached_result, similarity_score = similar
                self.stats["hits"] += 1
                
                # Add cache metadata
                cached_result["_cache_metadata"] = {
                    "hit": True,
                    "similarity": similarity_score,
                    "threshold": self.threshold,
                    "latency_ms": (time.time() - start_time) * 1000
                }
                
                logger.info(f"Cache HIT (similarity={similarity_score:.3f})")
                return cached_result
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache MISS")
                return None
                
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            self.stats["misses"] += 1
            return None
    
    def set(self, query: str, result: Dict) -> bool:
        """
        Cache query result
        
        Args:
            query: User query string
            result: Result dict to cache
            
        Returns:
            True if successfully cached
        """
        try:
            # Encode query
            query_embedding = self._encode_query(query)
            
            # Generate cache key
            query_hash = self._hash_query(query)
            
            # Store based on backend
            if self.backend == "redis":
                self._set_redis(query_hash, query, query_embedding, result)
            else:
                self._set_memory(query_hash, query_embedding, result)
            
            logger.debug(f"Cached query (hash={query_hash[:8]}...)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
    
    def _encode_query(self, query: str) -> np.ndarray:
        """Encode query to embedding vector"""
        embedding = self.encoder.encode(query, convert_to_numpy=True)
        return embedding
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _find_similar(self, query: str, query_embedding: np.ndarray) -> Optional[Tuple[Dict, float]]:
        """
        Find similar cached query
        
        Returns:
            (cached_result, similarity_score) or None
        """
        if self.backend == "redis":
            return self._find_similar_redis(query_embedding)
        else:
            return self._find_similar_memory(query_embedding)
    
    def _find_similar_memory(self, query_embedding: np.ndarray) -> Optional[Tuple[Dict, float]]:
        """Find similar query in memory cache"""
        best_match = None
        best_similarity = 0.0
        
        current_time = time.time()
        
        for query_hash, (cached_embedding, cached_result, timestamp) in list(self.memory_cache.items()):
            # Check if expired
            if current_time - timestamp > self.ttl_seconds:
                del self.memory_cache[query_hash]
                continue
            
            # Calculate similarity
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity and similarity >= self.threshold:
                best_similarity = similarity
                best_match = cached_result
        
        if best_match:
            return (best_match, best_similarity)
        return None
    
    def _find_similar_redis(self, query_embedding: np.ndarray) -> Optional[Tuple[Dict, float]]:
        """Find similar query in Redis cache"""
        try:
            # Scan all keys with cache prefix
            keys = self.redis_client.keys("cache:*")
            
            best_match = None
            best_similarity = 0.0
            
            for key in keys:
                # Get cached data
                cached_data = self.redis_client.get(key)
                if not cached_data:
                    continue
                
                # Deserialize
                data = json.loads(cached_data.decode())
                cached_embedding = np.array(data["embedding"])
                cached_result = data["result"]
                
                # Calculate similarity
                similarity = self._cosine_similarity(query_embedding, cached_embedding)
                
                if similarity > best_similarity and similarity >= self.threshold:
                    best_similarity = similarity
                    best_match = cached_result
            
            if best_match:
                return (best_match, best_similarity)
            return None
            
        except Exception as e:
            logger.error(f"Redis find_similar failed: {e}")
            return None
    
    def _set_memory(self, query_hash: str, embedding: np.ndarray, result: Dict):
        """Set cache entry in memory"""
        # Check size limit
        if len(self.memory_cache) >= self.max_entries:
            # Evict oldest (LRU)
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k][2])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[query_hash] = (
            embedding,
            result,
            time.time()
        )
    
    def _set_redis(self, query_hash: str, query: str, embedding: np.ndarray, result: Dict):
        """Set cache entry in Redis"""
        try:
            key = f"cache:{query_hash}"
            
            # Serialize data
            data = {
                "query": query,
                "embedding": embedding.tolist(),
                "result": result,
                "timestamp": time.time()
            }
            
            # Store with TTL
            self.redis_client.setex(
                key,
                self.ttl_seconds,
                json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def report_false_positive(self, query: str):
        """Report a cache hit that was actually incorrect"""
        self.stats["false_positives"] += 1
        logger.warning(f"False positive reported for query: {query[:50]}...")
    
    def clear(self):
        """Clear all cache entries"""
        if self.backend == "redis":
            keys = self.redis_client.keys("cache:*")
            if keys:
                self.redis_client.delete(*keys)
        else:
            self.memory_cache.clear()
        
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.stats["total_queries"]
        hits = self.stats["hits"]
        
        hit_rate = (hits / total * 100) if total > 0 else 0.0
        false_positive_rate = (self.stats["false_positives"] / hits * 100) if hits > 0 else 0.0
        
        return {
            "backend": self.backend,
            "threshold": self.threshold,
            "ttl_days": self.ttl_seconds / (24 * 60 * 60),
            "total_queries": total,
            "hits": hits,
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "false_positives": self.stats["false_positives"],
            "false_positive_rate": false_positive_rate,
            "cache_size": len(self.memory_cache) if self.backend == "memory" else self._get_redis_size()
        }
    
    def _get_redis_size(self) -> int:
        """Get number of cached entries in Redis"""
        try:
            return len(self.redis_client.keys("cache:*"))
        except:
            return 0
