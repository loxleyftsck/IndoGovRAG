"""
API Metrics Module
Centralized metrics management with thread-safe operations and persistence

Integrated with Phase 1.5 BET-006 Cost Tracker
"""

import json
import threading
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from collections import defaultdict, deque

from src.monitoring.cost_tracker import get_cost_tracker


class APIMetricsCollector:
    """
    Thread-safe API metrics collector with persistence
    
    Tracks:
    - Query statistics (total count, success/failure rates)
    - Latency metrics (avg, p50, p95, p99)
    - Cache hit rates
    - Cost tracking (via CostTracker integration)
    """
    
    def __init__(self, persist_path: str = "data/metrics/api_metrics.json"):
        """
        Initialize metrics collector
        
        Args:
            persist_path: Path to persist metrics JSON
        """
        self.persist_path = Path(persist_path)
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-safe lock
        self.lock = threading.Lock()
        
        # Metrics storage
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        
        # Latency tracking (keep last 1000 queries for percentile calculation)
        self.latency_history = deque(maxlen=1000)
        self.total_latency_ms = 0.0
        
        # Cache tracking
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Integration with cost tracker
        self.cost_tracker = get_cost_tracker()
        
        # Session start time
        self.session_start = datetime.now()
        
        # Try to load previous metrics if exists
        self._load_metrics()
    
    def record_query(
        self,
        success: bool,
        latency_ms: float,
        cache_hit: bool = False,
        input_tokens: int = 0,
        output_tokens: int = 0,
        compression_ratio: float = 1.0
    ):
        """
        Record a query and its metrics
        
        Args:
            success: Whether query succeeded
            latency_ms: Query latency in milliseconds
            cache_hit: Whether cache was hit
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            compression_ratio: Compression ratio applied
        """
        with self.lock:
            self.total_queries += 1
            
            if success:
                self.successful_queries += 1
            else:
                self.failed_queries += 1
            
            # Record latency
            self.latency_history.append(latency_ms)
            self.total_latency_ms += latency_ms
            
            # Record cache
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
            
            # Record cost (integrate with CostTracker)
            if input_tokens > 0 or output_tokens > 0:
                self.cost_tracker.record_query_cost(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    compression_ratio=compression_ratio,
                    cache_hit=cache_hit
                )
    
    def get_metrics(self) -> Dict:
        """
        Get current metrics snapshot
        
        Returns:
            Dict with all metrics
        """
        with self.lock:
            # Calculate latency metrics
            if self.total_queries > 0:
                avg_latency = self.total_latency_ms / self.total_queries
            else:
                avg_latency = 0.0
            
            # Calculate percentiles
            if self.latency_history:
                sorted_latencies = sorted(self.latency_history)
                n = len(sorted_latencies)
                p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0.0
                p95 = sorted_latencies[int(n * 0.95)] if n > 0 else 0.0
                p99 = sorted_latencies[int(n * 0.99)] if n > 0 else 0.0
            else:
                p50 = p95 = p99 = 0.0
            
            # Calculate cache hit rate
            total_cache_queries = self.cache_hits + self.cache_misses
            cache_hit_rate = (
                self.cache_hits / total_cache_queries * 100
                if total_cache_queries > 0
                else 0.0
            )
            
            # Calculate success rate
            success_rate = (
                self.successful_queries / self.total_queries * 100
                if self.total_queries > 0
                else 100.0
            )
            
            # Get cost metrics from CostTracker
            cost_metrics = self.cost_tracker.get_metrics()
            
            return {
                # Query statistics
                "total_queries": self.total_queries,
                "successful_queries": self.successful_queries,
                "failed_queries": self.failed_queries,
                "success_rate_percent": round(success_rate, 2),
                
                # Latency metrics
                "avg_latency_ms": round(avg_latency, 2),
                "p50_latency_ms": round(p50, 2),
                "p95_latency_ms": round(p95, 2),
                "p99_latency_ms": round(p99, 2),
                
                # Cache metrics
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                
                # Cost metrics (from CostTracker)
                "cost_metrics": {
                    "total_savings_usd": round(cost_metrics.get("total_savings_usd", 0.0), 4),
                    "baseline_cost_usd": round(cost_metrics.get("baseline_cost_usd", 0.0), 4),
                    "actual_cost_usd": round(cost_metrics.get("actual_cost_usd", 0.0), 4),
                    "savings_percent": round(cost_metrics.get("savings_percentage", 0.0), 2),
                },
                
                # Session info
                "session_duration_seconds": (datetime.now() - self.session_start).total_seconds(),
                "session_start": self.session_start.isoformat(),
                "last_updated": datetime.now().isoformat()
            }
    
    def persist_metrics(self):
        """Save metrics to disk"""
        with self.lock:
            metrics = self.get_metrics()
            try:
                with open(self.persist_path, 'w') as f:
                    json.dump(metrics, f, indent=2)
            except Exception as e:
                print(f"Warning: Failed to persist metrics: {e}")
    
    def _load_metrics(self):
        """Load previous metrics from disk if available"""
        if self.persist_path.exists():
            try:
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                    # Note: We load for reference but start fresh session
                    # Could implement full restoration if needed
                    print(f"📊 Previous metrics loaded from {self.persist_path}")
            except Exception as e:
                print(f"Warning: Could not load previous metrics: {e}")
    
    def reset(self):
        """Reset all metrics"""
        with self.lock:
            self.total_queries = 0
            self.successful_queries = 0
            self.failed_queries = 0
            self.latency_history.clear()
            self.total_latency_ms = 0.0
            self.cache_hits = 0
            self.cache_misses = 0
            self.session_start = datetime.now()
            self.cost_tracker.reset()
            print("📊 Metrics reset")


# Global singleton instance
_metrics_collector = None


def get_metrics_collector() -> APIMetricsCollector:
    """Get global APIMetricsCollector instance (singleton)"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = APIMetricsCollector()
    return _metrics_collector
