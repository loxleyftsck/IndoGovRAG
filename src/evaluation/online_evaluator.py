"""
Online Quality Evaluator
Samples and evaluates queries in production for real-time quality monitoring

Part of Phase 1.5 BET-008
"""

import random
import logging
import asyncio
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class OnlineEvaluator:
    """
    Sample and evaluate queries in production without blocking requests
    
    Features:
    - Configurable sampling rate (default: 10%)
    - Async evaluation (non-blocking)
    - Real-time faithfulness scoring
    - Metrics export to Prometheus
    """
    
    def __init__(self, sample_rate: float = 0.1,  enable_async: bool = True):
        """
        Initialize online evaluator
        
        Args:
            sample_rate: Sampling rate (0.0-1.0). 0.1 = evaluate 10% of queries
            enable_async: Run evaluation asynchronously
        """
        self.sample_rate = sample_rate
        self.enable_async = enable_async
        
        # Thread pool for async evaluation
        self.executor = ThreadPoolExecutor(max_workers=2) if enable_async else None
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "sampled_queries": 0,
            "avg_faithfulness": 0.0,
            "below_threshold_count": 0
        }
        
        # Try to import RAGAS evaluator
        try:
            from src.evaluation.ragas_evaluator import RAGASEvaluator
            self.ragas_evaluator = RAGASEvaluator()
            self.ragas_available = True
            logger.info(f"OnlineEvaluator initialized: sample_rate={sample_rate}, async={enable_async}")
        except ImportError as e:
            logger.warning(f"RAGAS evaluator not available: {e}")
            self.ragas_evaluator = None
            self.ragas_available = False
    
    def should_evaluate(self) -> bool:
        """Determine if this query should be sampled for evaluation"""
        self.stats["total_queries"] += 1
        should_sample = random.random() < self.sample_rate
        
        if should_sample:
            self.stats["sampled_queries"] += 1
        
        return should_sample
    
    def evaluate_query(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Evaluate query quality
        
        Args:
            question: User question
            answer: Generated answer
            contexts: Retrieved contexts
            ground_truth: Optional ground truth answer
            
        Returns:
            Evaluation metrics or None if evaluation skipped
        """
        if not self.should_evaluate():
            return None
        
        if not self.ragas_available:
            logger.debug("RAGAS not available, skipping evaluation")
            return None
        
        # Run evaluation
        if self.enable_async:
            # Submit to thread pool (non-blocking)
            future = self.executor.submit(
                self._run_evaluation,
                question, answer, contexts, ground_truth
            )
            # Don't wait for result (fire and forget)
            logger.debug("Submitted query for async evaluation")
            return {"status": "async_submitted"}
        else:
            # Synchronous evaluation
            return self._run_evaluation(question, answer, contexts, ground_truth)
    
    def _run_evaluation(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str]
    ) -> Dict:
        """Run actual evaluation (can be async)"""
        try:
            # Evaluate with RAGAS
            result = self.ragas_evaluator.evaluate_single(
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=ground_truth
            )
            
            faithfulness = result.get("faithfulness", 0.0)
            
            # Update running average
            prev_count = self.stats["sampled_queries"] - 1
            if prev_count > 0:
                self.stats["avg_faithfulness"] = (
                    (self.stats["avg_faithfulness"] * prev_count + faithfulness) /
                    self.stats["sampled_queries"]
                )
            else:
                self.stats["avg_faithfulness"] = faithfulness
            
            # Check thresholds
            if faithfulness < 0.74:
                self.stats["below_threshold_count"] += 1
                logger.warning(f"Query faithfulness below threshold: {faithfulness:.3f}")
            
            # Export metrics to Prometheus
            self._export_metrics(faithfulness)
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {"error": str(e)}
    
    def _export_metrics(self, faithfulness: float):
        """Export metrics to Prometheus"""
        try:
            from src.monitoring.metrics import (
                query_quality_score,
                quality_below_threshold_total,
                ragas_faithfulness_score
            )
            
            # Record quality score
            query_quality_score.observe(faithfulness)
            
            # Update gauge
            ragas_faithfulness_score.set(self.stats["avg_faithfulness"])
            
            # Count below threshold
            if faithfulness < 0.74:
                quality_below_threshold_total.labels(threshold="0.74").inc()
            
        except ImportError:
            logger.debug("Prometheus metrics not available")
    
    def get_stats(self) -> Dict:
        """Get evaluator statistics"""
        sample_rate_actual = (
            self.stats["sampled_queries"] / self.stats["total_queries"] * 100
            if self.stats["total_queries"] > 0
            else 0.0
        )
        
        return {
            **self.stats,
            "sample_rate_configured": self.sample_rate * 100,
            "sample_rate_actual": sample_rate_actual,
            "ragas_available": self.ragas_available,
            "async_enabled": self.enable_async
        }
    
    def shutdown(self):
        """Shutdown evaluator and cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("OnlineEvaluator shutdown complete")


# Singleton instance
_online_evaluator = None


def get_online_evaluator() -> OnlineEvaluator:
    """Get global OnlineEvaluator instance (singleton)"""
    global _online_evaluator
    if _online_evaluator is None:
        _online_evaluator = OnlineEvaluator()
    return _online_evaluator
