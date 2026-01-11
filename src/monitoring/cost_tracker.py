"""
Cost Tracking Module
Calculates and tracks cost savings from compression and caching

Part of Phase 1.5 BET-006
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CostMetrics:
    """Cost metrics tracking"""
    total_queries: int = 0
    compression_savings_tokens: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    baseline_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    
    def get_total_savings(self) -> float:
        """Calculate total cost savings in USD"""
        return self.baseline_cost_usd - self.actual_cost_usd
    
    def get_savings_percentage(self) -> float:
        """Calculate savings as percentage"""
        if self.baseline_cost_usd == 0:
            return 0.0
        return (self.get_total_savings() / self.baseline_cost_usd) * 100


class CostTracker:
    """
    Track and calculate cost savings from optimizations
    
    Pricing (Gemini):
    - Input: $0.00001 per token
    - Output: $0.00003 per token
    - Avg query: ~1000 input tokens, ~200 output tokens
    - Baseline cost: ~$0.003 per query
    """
    
    # Gemini pricing (as of 2026)
    COST_PER_INPUT_TOKEN = 0.00001
    COST_PER_OUTPUT_TOKEN = 0.00003
    
    # Average tokens from Phase 1.5 experiments
    AVG_INPUT_TOKENS_BASELINE = 1000
    AVG_OUTPUT_TOKENS = 200
    AVG_COST_PER_QUERY_BASELINE = 0.003
    
    def __init__(self):
        """Initialize cost tracker"""
        self.metrics = CostMetrics()
        self.session_start = datetime.now()
        logger.info("CostTracker initialized")
    
    def calculate_compression_savings(
        self,
        original_tokens: int,
        compressed_tokens: int
    ) -> float:
        """
        Calculate cost savings from compression
        
        Args:
            original_tokens: Original input token count
            compressed_tokens: Compressed token count
            
        Returns:
            Savings in USD
        """
        tokens_saved = original_tokens - compressed_tokens
        savings = tokens_saved * self.COST_PER_INPUT_TOKEN
        
        # Track metrics
        self.metrics.compression_savings_tokens += tokens_saved
        
        return savings
    
    def calculate_cache_savings(self, cache_hit: bool = True) -> float:
        """
        Calculate cost savings from cache hit
        
        Args:
            cache_hit: Whether cache was hit
            
        Returns:
            Savings in USD
        """
        if cache_hit:
            # Cache hit saves entire LLM call
            savings = self.AVG_COST_PER_QUERY_BASELINE
            self.metrics.cache_hits += 1
        else:
            savings = 0.0
            self.metrics.cache_misses += 1
        
        return savings
    
    def record_query_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        compression_ratio: float = 1.0,
        cache_hit: bool = False
    ) -> Dict:
        """
        Record cost for a query and calculate savings
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            compression_ratio: Compression ratio applied (1.0 = no compression)
            cache_hit: Whether query was served from cache
            
        Returns:
            Dict with cost breakdown
        """
        self.metrics.total_queries += 1
        
        # Calculate baseline cost (without optimizations)
        baseline_input = int(input_tokens / compression_ratio) if compression_ratio > 0 else input_tokens
        baseline_cost = (
            baseline_input * self.COST_PER_INPUT_TOKEN +
            output_tokens * self.COST_PER_OUTPUT_TOKEN
        )
        
        if cache_hit:
            # Cache hit: no LLM call, only cache lookup cost (negligible)
            actual_cost = 0.00001  # Minimal cache lookup cost
            compression_savings = 0.0
            cache_savings = baseline_cost
            # Track cache hit
            self.metrics.cache_hits += 1
        else:
            # No cache hit: calculate compression savings
            actual_cost = (
                input_tokens * self.COST_PER_INPUT_TOKEN +
                output_tokens * self.COST_PER_OUTPUT_TOKEN
            )
            compression_savings = self.calculate_compression_savings(
                baseline_input,
                input_tokens
            )
            cache_savings = 0.0
            # Track cache miss
            self.metrics.cache_misses += 1
        
        # Update metrics
        self.metrics.baseline_cost_usd += baseline_cost
        self.metrics.actual_cost_usd += actual_cost
        
        total_savings = baseline_cost - actual_cost
        
        return {
            "baseline_cost_usd": baseline_cost,
            "actual_cost_usd": actual_cost,
            "total_savings_usd": total_savings,
            "compression_savings_usd": compression_savings,
            "cache_savings_usd": cache_savings,
            "savings_percentage": (total_savings / baseline_cost * 100) if baseline_cost > 0 else 0.0
        }
    
    def get_metrics(self) -> Dict:
        """Get cost tracking metrics"""
        total_savings = self.metrics.get_total_savings()
        cache_hit_rate = (
            self.metrics.cache_hits / (self.metrics.cache_hits + self.metrics.cache_misses) * 100
            if (self.metrics.cache_hits + self.metrics.cache_misses) > 0
            else 0.0
        )
        
        # Calculate avg cost per query
        avg_baseline = (
            self.metrics.baseline_cost_usd / self.metrics.total_queries
            if self.metrics.total_queries > 0
            else 0.0
        )
        avg_actual = (
            self.metrics.actual_cost_usd / self.metrics.total_queries
            if self.metrics.total_queries > 0
            else 0.0
        )
        
        return {
            "total_queries": self.metrics.total_queries,
            "baseline_cost_usd": self.metrics.baseline_cost_usd,
            "actual_cost_usd": self.metrics.actual_cost_usd,
            "total_savings_usd": total_savings,
            "savings_percentage": self.metrics.get_savings_percentage(),
            "avg_cost_per_query_baseline": avg_baseline,
            "avg_cost_per_query_actual": avg_actual,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "compression_tokens_saved": self.metrics.compression_savings_tokens,
            "session_duration_seconds": (datetime.now() - self.session_start).total_seconds()
        }
    
    def reset(self):
        """Reset cost tracking metrics"""
        self.metrics = CostMetrics()
        self.session_start = datetime.now()
        logger.info("Cost metrics reset")


# Singleton instance
_cost_tracker = None


def get_cost_tracker() -> CostTracker:
    """Get global CostTracker instance (singleton)"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
