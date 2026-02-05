"""
Answer Quality Metrics Monitoring
Tracks degradation in RAG answer quality over time
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import numpy as np


class QualityMetricsMonitor:
    """
    Monitor answer quality metrics with sliding windows
    Alerts on degradation trends
    """
    
    def __init__(
        self,
        window_size: int = 100,  # Number of queries to track
        alert_threshold: float = 0.15  # 15% degradation triggers alert
    ):
        """
        Initialize quality monitor
        
        Args:
            window_size: Sliding window size for metrics
            alert_threshold: % degradation to trigger alert
        """
        self.window_size = window_size
        self.alert_threshold = alert_threshold
        
        # Sliding windows for each metric
        self.faithfulness_window = deque(maxlen=window_size)
        self.relevance_window = deque(maxlen=window_size)
        self.latency_window = deque(maxlen=window_size)
        self.confidence_window = deque(maxlen=window_size)
        
        # Baseline metrics (first N queries)
        self.baseline_metrics: Optional[Dict[str, float]] = None
        self.baseline_queries = 0
        self.total_queries = 0
        
        print(f"✅ Quality Monitor initialized (window={window_size})")
    
    def record_query(
        self,
        faithfulness: Optional[float] = None,
        relevance: Optional[float] = None,
        latency_ms: Optional[float] = None,
        confidence: Optional[float] = None
    ):
        """
        Record metrics for a single query
        
        Args:
            faithfulness: Faithfulness score (0-1)
            relevance: Relevance score (0-1)
            latency_ms: Query latency in milliseconds
            confidence: Retrieval confidence (0-1)
        """
        if faithfulness is not None:
            self.faithfulness_window.append(faithfulness)
        
        if relevance is not None:
            self.relevance_window.append(relevance)
        
        if latency_ms is not None:
            self.latency_window.append(latency_ms)
        
        if confidence is not None:
            self.confidence_window.append(confidence)
        
        self.total_queries += 1
        
        # Set baseline after first window is full
        if self.baseline_metrics is None and len(self.faithfulness_window) >= self.window_size:
            self._set_baseline()
    
    def _set_baseline(self):
        """Set baseline metrics from current windows"""
        self.baseline_metrics = {
            "faithfulness": np.mean(self.faithfulness_window) if self.faithfulness_window else None,
            "relevance": np.mean(self.relevance_window) if self.relevance_window else None,
            "latency_ms": np.mean(self.latency_window) if self.latency_window else None,
            "confidence": np.mean(self.confidence_window) if self.confidence_window else None
        }
        self.baseline_queries = self.total_queries
        
        print(f"📊 Baseline set at query {self.total_queries}")
        print(f"   Faithfulness: {self.baseline_metrics['faithfulness']:.3f}")
        print(f"   Latency: {self.baseline_metrics['latency_ms']:.1f}ms")
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current average metrics from sliding window"""
        return {
            "faithfulness_mean": np.mean(self.faithfulness_window) if self.faithfulness_window else None,
            "faithfulness_std": np.std(self.faithfulness_window) if self.faithfulness_window else None,
            "relevance_mean": np.mean(self.relevance_window) if self.relevance_window else None,
            "relevance_std": np.std(self.relevance_window) if self.relevance_window else None,
            "latency_mean": np.mean(self.latency_window) if self.latency_window else None,
            "latency_std": np.std(self.latency_window) if self.latency_window else None,
            "confidence_mean": np.mean(self.confidence_window) if self.confidence_window else None,
            "confidence_std": np.std(self.confidence_window) if self.confidence_window else None,
            "window_size": len(self.faithfulness_window),
            "total_queries": self.total_queries
        }
    
    def check_quality_degradation(self) -> Dict[str, any]:
        """
        Check if quality has degraded compared to baseline
        
        Returns:
            Alert dict with degradation info
        """
        if self.baseline_metrics is None:
            return {
                "status": "no_baseline",
                "message": "Baseline not yet established"
            }
        
        current = self.get_current_metrics()
        alerts = []
        
        # Check each metric for degradation
        metrics_to_check = [
            ("faithfulness", "mean", "lower_is_worse"),
            ("relevance", "mean", "lower_is_worse"),
            ("confidence", "mean", "lower_is_worse"),
            ("latency", "mean", "higher_is_worse")
        ]
        
        for metric_name, stat_type, direction in metrics_to_check:
            baseline_key = f"{metric_name}_ms" if metric_name == "latency" else metric_name
            current_key = f"{metric_name}_{stat_type}"
            
            baseline_value = self.baseline_metrics.get(baseline_key)
            current_value = current.get(current_key)
            
            if baseline_value is None or current_value is None:
                continue
            
            # Calculate % change
            if baseline_value != 0:
                change_pct = ((current_value - baseline_value) / abs(baseline_value))
            else:
                change_pct = 0.0
            
            # Check if degraded
            degraded = False
            if direction == "lower_is_worse" and change_pct < -self.alert_threshold:
                degraded = True
            elif direction == "higher_is_worse" and change_pct > self.alert_threshold:
                degraded = True
            
            if degraded:
                alerts.append({
                    "metric": metric_name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "change_pct": change_pct * 100,
                    "severity": "high" if abs(change_pct) > 0.3 else "medium"
                })
        
        return {
            "status": "complete",
            "timestamp": datetime.now().isoformat(),
            "baseline_set_at": self.baseline_queries,
            "current_queries": self.total_queries,
            "degradations_detected": len(alerts),
            "alerts": alerts,
            "current_metrics": current
        }
    
    def reset_baseline(self):
        """Reset baseline to current metrics"""
        self._set_baseline()
        print("🔄 Baseline reset to current metrics")


# Singleton
_quality_monitor = None

def get_quality_monitor(**kwargs) -> QualityMetricsMonitor:
    """Get or create global quality monitor instance"""
    global _quality_monitor
    if _quality_monitor is None:
        _quality_monitor = QualityMetricsMonitor(**kwargs)
    return _quality_monitor
