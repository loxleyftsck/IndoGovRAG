"""
Data Drift Monitoring for RAG System
Detects distribution shifts in queries, answers, and quality metrics
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from scipy import stats
import json
from pathlib import Path


class DriftDetector:
    """
    Detect data drift in RAG system outputs
    
    Drift types monitored:
    - Query distribution drift (topic shifts)
    - Answer quality drift (degradation)
    - Latency drift (performance regression)
    - Retrieval quality drift (relevance drop)
    """
    
    def __init__(
        self,
        baseline_window_days: int = 7,
        detection_window_hours: int = 6,
        drift_threshold: float = 0.05  # p-value threshold
    ):
        """
        Initialize drift detector
        
        Args:
            baseline_window_days: Days of historical data for baseline
            detection_window_hours: Current window to detect drift
            drift_threshold: Statistical significance threshold (alpha)
        """
        self.baseline_window_days = baseline_window_days
        self.detection_window_hours = detection_window_hours
        self.drift_threshold = drift_threshold
        
        # Storage for metrics history
        self.metrics_history: List[Dict] = []
        
        print(f"✅ Drift Detector initialized")
        print(f"   Baseline: {baseline_window_days} days")
        print(f"   Detection window: {detection_window_hours} hours")
        print(f"   Threshold: {drift_threshold}")
    
    def add_metrics(self, metrics: Dict[str, float], timestamp: Optional[datetime] = None):
        """
        Add metrics sample to history
        
        Args:
            metrics: Dict of metric name -> value
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.metrics_history.append({
            "timestamp": timestamp,
            "metrics": metrics
        })
    
    def detect_drift(
        self,
        metric_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect drift across all or specified metrics
        
        Args:
            metric_names: Optional list of metrics to check (None = all)
            
        Returns:
            Drift report dict with p-values and alerts
        """
        if len(self.metrics_history) < 10:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 10 samples, have {len(self.metrics_history)}"
            }
        
        # Split into baseline and current windows
        baseline_data, current_data = self._get_baseline_and_current()
        
        if not baseline_data or not current_data:
            return {
                "status": "insufficient_data",
                "baseline_samples": len(baseline_data),
                "current_samples": len(current_data)
            }
        
        # Get metric names to check
        if metric_names is None:
            # Get all common metrics
            baseline_metrics = set(baseline_data[0]["metrics"].keys())
            current_metrics = set(current_data[0]["metrics"].keys())
            metric_names = list(baseline_metrics & current_metrics)
        
        # Run drift tests
        drift_results = {}
        alerts = []
        
        for metric_name in metric_names:
            result = self._test_metric_drift(
                metric_name,
                baseline_data,
                current_data
            )
            
            drift_results[metric_name] = result
            
            # Generate alert if drift detected
            if result["drift_detected"]:
                alerts.append({
                    "metric": metric_name,
                    "p_value": result["p_value"],
                    "direction": result["direction"],
                    "baseline_mean": result["baseline_mean"],
                    "current_mean": result["current_mean"],
                    "change_pct": result["change_pct"]
                })
        
        return {
            "status": "complete",
            "timestamp": datetime.now().isoformat(),
            "baseline_window": f"{self.baseline_window_days} days",
            "current_window": f"{self.detection_window_hours} hours",
            "baseline_samples": len(baseline_data),
            "current_samples": len(current_data),
            "metrics_checked": len(metric_names),
            "drifts_detected": len(alerts),
            "results": drift_results,
            "alerts": alerts
        }
    
    def _get_baseline_and_current(self) -> Tuple[List[Dict], List[Dict]]:
        """Split metrics history into baseline and current windows"""
        now = datetime.now()
        
        # Baseline: from X days ago to detection window start
        baseline_start = now - timedelta(days=self.baseline_window_days)
        baseline_end = now - timedelta(hours=self.detection_window_hours)
        
        # Current: last X hours
        current_start = baseline_end
        
        baseline_data = [
            m for m in self.metrics_history
            if baseline_start <= m["timestamp"] <= baseline_end
        ]
        
        current_data = [
            m for m in self.metrics_history
            if m["timestamp"] >= current_start
        ]
        
        return baseline_data, current_data
    
    def _test_metric_drift(
        self,
        metric_name: str,
        baseline_data: List[Dict],
        current_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Test single metric for drift using Kolmogorov-Smirnov test
        
        Args:
            metric_name: Name of metric to test
            baseline_data: Historical baseline samples
            current_data: Current window samples
            
        Returns:
            Test results dict
        """
        # Extract metric values
        baseline_values = [
            m["metrics"].get(metric_name)
            for m in baseline_data
            if metric_name in m["metrics"]
        ]
        
        current_values = [
            m["metrics"].get(metric_name)
            for m in current_data
            if metric_name in m["metrics"]
        ]
        
        # Filter None values
        baseline_values = [v for v in baseline_values if v is not None]
        current_values = [v for v in current_values if v is not None]
        
        if not baseline_values or not current_values:
            return {
                "drift_detected": False,
                "reason": "insufficient_samples",
                "baseline_n": len(baseline_values),
                "current_n": len(current_values)
            }
        
        # Calculate statistics
        baseline_mean = np.mean(baseline_values)
        current_mean = np.mean(current_values)
        baseline_std = np.std(baseline_values)
        current_std = np.std(current_values)
        
        # Perform Kolmogorov-Smirnov test
        ks_statistic, p_value = stats.ks_2samp(baseline_values, current_values)
        
        # Determine drift
        drift_detected = p_value < self.drift_threshold
        
        # Calculate change
        if baseline_mean != 0:
            change_pct = ((current_mean - baseline_mean) / abs(baseline_mean)) * 100
        else:
            change_pct = 0.0
        
        # Determine direction
        if drift_detected:
            if current_mean > baseline_mean:
                direction = "increase"
            elif current_mean < baseline_mean:
                direction = "decrease"
            else:
                direction = "unchanged"
        else:
            direction = None
        
        return {
            "drift_detected": drift_detected,
            "p_value": p_value,
            "ks_statistic": ks_statistic,
            "baseline_mean": baseline_mean,
            "current_mean": current_mean,
            "baseline_std": baseline_std,
            "current_std": current_std,
            "change_pct": change_pct,
            "direction": direction,
            "baseline_n": len(baseline_values),
            "current_n": len(current_values)
        }
    
    def calculate_psi(
        self,
        baseline_values: List[float],
        current_values: List[float],
        num_bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI)
        
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change (drift)
        
        Args:
            baseline_values: Historical values
            current_values: Current values
            num_bins: Number of bins for discretization
            
        Returns:
            PSI score
        """
        # Create bins based on baseline
        bins = np.linspace(
            min(baseline_values),
            max(baseline_values),
            num_bins + 1
        )
        
        # Calculate distributions
        baseline_hist, _ = np.histogram(baseline_values, bins=bins)
        current_hist, _ = np.histogram(current_values, bins=bins)
        
        # Normalize to percentages
        baseline_pct = baseline_hist / len(baseline_values)
        current_pct = current_hist / len(current_values)
        
        # Add small constant to avoid log(0)
        epsilon = 1e-10
        baseline_pct = baseline_pct + epsilon
        current_pct = current_pct + epsilon
        
        # Calculate PSI
        psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
        
        return psi
    
    def save_history(self, filepath: str):
        """Save metrics history to JSON file"""
        data = {
            "saved_at": datetime.now().isoformat(),
            "config": {
                "baseline_window_days": self.baseline_window_days,
                "detection_window_hours": self.detection_window_hours,
                "drift_threshold": self.drift_threshold
            },
            "history": [
                {
                    "timestamp": m["timestamp"].isoformat(),
                    "metrics": m["metrics"]
                }
                for m in self.metrics_history
            ]
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Saved {len(self.metrics_history)} samples to {filepath}")
    
    def load_history(self, filepath: str):
        """Load metrics history from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)
        
        self.metrics_history = [
            {
                "timestamp": datetime.fromisoformat(m["timestamp"]),
                "metrics": m["metrics"]
            }
            for m in data["history"]
        ]
        
        print(f"✅ Loaded {len(self.metrics_history)} samples from {filepath}")


# Singleton
_drift_detector = None

def get_drift_detector(**kwargs) -> DriftDetector:
    """Get or create global drift detector instance"""
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = DriftDetector(**kwargs)
    return _drift_detector
