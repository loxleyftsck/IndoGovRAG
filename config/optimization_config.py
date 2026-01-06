"""
Optimization Configuration for Phase 1.5
Config #8: Compression 0.7 + Cache 0.95 + Single-Stage Retrieval

This config is DISABLED by default (rollout_percentage = 0).
Enable gradually via config updates: 0% → 10% → 50% → 100%
"""

OPTIMIZATION_CONFIG = {
    # Metadata
    "version": "1.5.0-beta",
    "config_name": "Config #8",
    "last_updated": "2026-01-27",
    
    # Master switch
    "enabled": True,  # Set to False to disable all optimizations
    
    # Compression settings (LLMLingua, ratio 0.7)
    "compression": {
        "enabled": True,
        "ratio": 0.7,  # Keep 70% of tokens, remove 30%
        "model": "llmlingua",  # or "llmlingua2" for newer version
        "timeout_ms": 1000,  # Max time for compression
        "fallback_on_error": True,  # If compression fails, use uncompressed
        "whitelist_keywords": [
            # Legal terms - never compress these
            "pasal", "ayat", "undang-undang", "peraturan", 
            "pemerintah", "presiden", "menteri",
            # Numbers and dates - preserve precision
            r"\d+",  # Any numbers
            r"\d{2}/\d{2}/\d{4}",  # Dates
        ],
    },
    
    # Semantic caching settings (Redis, threshold 0.95)
    "caching": {
        "enabled": True,
        "backend": "redis",  # "redis" or "memory" (for dev/test)
        "host": "localhost",  # Override with env var REDIS_HOST
        "port": 6379,
        "db": 0,
        "threshold": 0.95,  # Similarity threshold (0-1)
        "ttl_days": 7,  # Cache expiry
        "max_entries": 10000,  # Max cached items
        "eviction_policy": "LRU",  # Least Recently Used
        # Stricter threshold for high-risk queries
        "high_risk_threshold": 0.97,
        "high_risk_keywords": ["legal", "hukum", "pidana", "perdata"],
    },
    
    # Retrieval mode
    "retrieval": {
        "mode": "single_stage",  # "single_stage" or "multi_stage" (Config #17)
        "top_k": 5,
    },
    
    # Feature flags for gradual rollout
    "feature_flags": {
        "rollout_percentage": 0,  # START AT 0% (SAFE DEFAULT)
        # Will increase to: 10% (Week 1) → 50% (Week 2) → 100% (Week 3)
        
        "rollout_strategy": "deterministic_hash",  # Hash user_id for consistency
        "killswitch_enabled": True,  # Allow emergency disable
        
        # Per-feature toggles (advanced)
        "compression_enabled": True,
        "cache_enabled": True,
    },
    
    # Monitoring & logging
    "monitoring": {
        "log_compression_stats": True,  # Log tokens before/after
        "log_cache_hits": True,  # Log hit/miss
        "log_latency_breakdown": True,  # Per-stage timing
        "segment_by_query_type": True,  # Track simple/complex/legal separately
    },
    
    # Safety thresholds (automatic rollback triggers)
    "safety": {
        "max_error_rate": 0.10,  # Rollback if errors >10%
        "max_p95_latency_seconds": 15.0,  # Rollback if P95 >15s
        "min_faithfulness": 0.74,  # Rollback if quality <0.74
        "min_cache_hit_rate": 0.30,  # Alert if cache <30%
    }
}


def should_use_optimization(user_id: str) -> bool:
    """
    Deterministic traffic splitting based on user_id hash
    
    Args:
        user_id: User identifier (or IP if user_id unavailable)
        
    Returns:
        bool: True if user should get optimized pipeline
    """
    import hashlib
    
    # Check master switches
    if not OPTIMIZATION_CONFIG["enabled"]:
        return False
    
    if not OPTIMIZATION_CONFIG["feature_flags"]["killswitch_enabled"]:
        return False  # Killswitch activated
    
    # Check rollout percentage
    rollout_pct = OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"]
    
    if rollout_pct == 0:
        return False  # Not enabled yet
    elif rollout_pct == 100:
        return True  # Fully rolled out
    else:
        # Deterministic hashing for consistent assignment
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = hash_val % 100
        return bucket < rollout_pct


# Environment variable overrides (for production)
import os

if os.getenv("REDIS_HOST"):
    OPTIMIZATION_CONFIG["caching"]["host"] = os.getenv("REDIS_HOST")

if os.getenv("REDIS_PORT"):
    OPTIMIZATION_CONFIG["caching"]["port"] = int(os.getenv("REDIS_PORT"))

if os.getenv("OPTIMIZATION_ROLLOUT_PCT"):
    OPTIMIZATION_CONFIG["feature_flags"]["rollout_percentage"] = int(
        os.getenv("OPTIMIZATION_ROLLOUT_PCT")
    )
