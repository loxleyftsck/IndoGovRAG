"""
RAG-Specific Metrics Logger
Custom metrics for retrieval and generation quality
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np


class RAGMetricsLogger:
    """
    Calculate and format RAG-specific metrics for MLflow logging
    
    Metrics:
    - Retrieval: precision@k, recall@k, MRR, NDCG
    - Generation: faithfulness, relevance, coherence
    - Latency: retrieval_time, generation_time, total_time
    - Quality: answer_length, source_coverage
    """
    
    @staticmethod
    def calculate_retrieval_metrics(
        retrieved_docs: List[Dict],
        relevant_doc_ids: List[str],
        k: int = 5
    ) -> Dict[str, float]:
        """
        Calculate retrieval quality metrics
        
        Args:
            retrieved_docs: List of retrieved document dicts
            relevant_doc_ids: Ground truth relevant doc IDs
            k: Top-k cutoff
            
        Returns:
            Dict of retrieval metrics
        """
        retrieved_ids = [doc.get("doc_id", "") for doc in retrieved_docs[:k]]
        
        # Precision@k
        relevant_retrieved = len(set(retrieved_ids) & set(relevant_doc_ids))
        precision_at_k = relevant_retrieved / k if k > 0 else 0.0
        
        # Recall@k
        recall_at_k = relevant_retrieved / len(relevant_doc_ids) if len(relevant_doc_ids) > 0 else 0.0
        
        # F1@k
        if precision_at_k + recall_at_k > 0:
            f1_at_k = 2 * (precision_at_k * recall_at_k) / (precision_at_k + recall_at_k)
        else:
            f1_at_k = 0.0
        
        # Mean Reciprocal Rank (MRR)
        mrr = 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_doc_ids:
                mrr = 1 / (i + 1)
                break
        
        return {
            f"precision@{k}": precision_at_k,
            f"recall@{k}": recall_at_k,
            f"f1@{k}": f1_at_k,
            "mrr": mrr
        }
    
    @staticmethod
    def calculate_generation_metrics(
        answer: str,
        context: str,
        reference: Optional[str] = None,
        faithfulness_score: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate generation quality metrics
        
        Args:
            answer: Generated answer
            context: Retrieved context
            reference: Optional reference answer
            faithfulness_score: Pre-computed faithfulness (from judge)
            
        Returns:
            Dict of generation metrics
        """
        metrics = {}
        
        # Answer length
        metrics["answer_length"] = len(answer)
        metrics["answer_words"] = len(answer.split())
        
        # Context coverage (simple lexical overlap)
        answer_tokens = set(answer.lower().split())
        context_tokens = set(context.lower().split())
        
        if len(context_tokens) > 0:
            coverage = len(answer_tokens & context_tokens) / len(context_tokens)
            metrics["context_coverage"] = coverage
        else:
            metrics["context_coverage"] = 0.0
        
        # Faithfulness (if provided)
        if faithfulness_score is not None:
            metrics["faithfulness"] = faithfulness_score
        
        # Reference-based metrics (if reference available)
        if reference:
            reference_tokens = set(reference.lower().split())
            if len(reference_tokens) > 0:
                # Lexical overlap with reference
                overlap = len(answer_tokens & reference_tokens) / len(reference_tokens)
                metrics["reference_overlap"] = overlap
        
        return metrics
    
    @staticmethod
    def calculate_latency_metrics(
        retrieval_time_ms: float,
        generation_time_ms: float,
        total_time_ms: float
    ) -> Dict[str, float]:
        """
        Calculate latency metrics
        
        Args:
            retrieval_time_ms: Time for retrieval in ms
            generation_time_ms: Time for generation in ms
            total_time_ms: Total query time in ms
            
        Returns:
            Dict of latency metrics
        """
        return {
            "latency_retrieval_ms": retrieval_time_ms,
            "latency_generation_ms": generation_time_ms,
            "latency_total_ms": total_time_ms,
            "latency_retrieval_pct": (retrieval_time_ms / total_time_ms * 100) if total_time_ms > 0 else 0,
            "latency_generation_pct": (generation_time_ms / total_time_ms * 100) if total_time_ms > 0 else 0
        }
    
    @staticmethod
    def aggregate_batch_metrics(metric_dicts: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Aggregate metrics across multiple queries
        
        Args:
            metric_dicts: List of metric dicts from individual queries
            
        Returns:
            Dict of aggregated metrics (mean, std, min, max)
        """
        if not metric_dicts:
            return {}
        
        # Collect all metric names
        all_metrics = set()
        for m_dict in metric_dicts:
            all_metrics.update(m_dict.keys())
        
        aggregated = {}
        for metric_name in all_metrics:
            values = [m_dict.get(metric_name, np.nan) for m_dict in metric_dicts]
            values = [v for v in values if not np.isnan(v)]  # Filter NaNs
            
            if len(values) > 0:
                aggregated[f"{metric_name}_mean"] = np.mean(values)
                aggregated[f"{metric_name}_std"] = np.std(values)
                aggregated[f"{metric_name}_min"] = np.min(values)
                aggregated[f"{metric_name}_max"] = np.max(values)
        
        return aggregated
    
    @staticmethod
    def format_for_mlflow(
        retrieval_metrics: Dict[str, float],
        generation_metrics: Dict[str, float],
        latency_metrics: Dict[str, float],
        custom_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Combine all metrics into single dict for MLflow logging
        
        Args:
            retrieval_metrics: Retrieval quality metrics
            generation_metrics: Generation quality metrics
            latency_metrics: Latency metrics
            custom_metrics: Any additional custom metrics
            
        Returns:
            Combined metrics dict
        """
        all_metrics = {
            **retrieval_metrics,
            **generation_metrics,
            **latency_metrics
        }
        
        if custom_metrics:
            all_metrics.update(custom_metrics)
        
        return all_metrics
