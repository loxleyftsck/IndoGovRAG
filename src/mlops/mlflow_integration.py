"""
Integration layer between RAG pipeline and MLflow tracking
Automatically logs all queries to MLflow
"""

from typing import Dict, Any, Optional
from src.mlops.experiment_tracker import get_tracker
from src.mlops.metrics_logger import RAGMetricsLogger
import time


class MLflowRAGWrapper:
    """
    Wrapper around RAG pipeline that automatically logs to MLflow
    Drop-in replacement for production_pipeline.query()
    """
    
    def __init__(
        self,
        rag_pipeline,
        experiment_name: str = "indogov-rag-production",
        enable_logging: bool = True
    ):
        """
        Initialize MLflow RAG wrapper
        
        Args:
            rag_pipeline: ProductionRAGPipeline instance
            experiment_name: MLflow experiment name
            enable_logging: Toggle MLflow logging (for testing)
        """
        self.rag_pipeline = rag_pipeline
        self.enable_logging = enable_logging
        
        if enable_logging:
            self.tracker = get_tracker(experiment_name=experiment_name)
            self.metrics_logger = RAGMetricsLogger()
        else:
            self.tracker = None
            self.metrics_logger = None
        
        print(f"✅ MLflow RAG Wrapper initialized (logging={'ON' if enable_logging else 'OFF'})")
    
    def query(
        self,
        question: str,
        user_id: Optional[str] = None,
        force_evaluation: bool = False,
        relevant_doc_ids: Optional[list] = None  # For ground truth metrics
    ) -> Dict:
        """
        Query RAG pipeline with automatic MLflow logging
        
        Args:
            question: User question
            user_id: Optional user ID
            force_evaluation: Force faithfulness evaluation
            relevant_doc_ids: Ground truth doc IDs (for evaluation)
            
        Returns:
            Same as ProductionRAGPipeline.query()
        """
        # Execute query
        start_time = time.time()
        result = self.rag_pipeline.query(
            question=question,
            user_id=user_id,
            force_evaluation=force_evaluation
        )
        total_time_ms = (time.time() - start_time) * 1000
        
        # Log to MLflow if enabled
        if self.enable_logging and self.tracker:
            try:
                self._log_to_mlflow(
                    query=question,
                    result=result,
                    total_time_ms=total_time_ms,
                    relevant_doc_ids=relevant_doc_ids
                )
            except Exception as e:
                print(f"⚠️ MLflow logging failed: {e}")
                # Continue execution even if logging fails
        
        return result
    
    def _log_to_mlflow(
        self,
        query: str,
        result: Dict,
        total_time_ms: float,
        relevant_doc_ids: Optional[list] = None
    ):
        """Internal method to log query to MLflow"""
        
        # Extract data from result
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        contexts = result.get("contexts", [])
        faithfulness_score = result.get("faithfulness_score")
        
        # Calculate metrics
        metrics = {}
        
        # Retrieval metrics (if ground truth available)
        if relevant_doc_ids:
            retrieval_metrics = self.metrics_logger.calculate_retrieval_metrics(
                retrieved_docs=sources,
                relevant_doc_ids=relevant_doc_ids,
                k=len(sources)
            )
            metrics.update(retrieval_metrics)
        
        # Generation metrics
        combined_context = "\n\n".join(contexts) if contexts else ""
        generation_metrics = self.metrics_logger.calculate_generation_metrics(
            answer=answer,
            context=combined_context,
            faithfulness_score=faithfulness_score
        )
        metrics.update(generation_metrics)
        
        # Latency metrics
        latency_ms = result.get("latency_ms", total_time_ms)
        latency_metrics = self.metrics_logger.calculate_latency_metrics(
            retrieval_time_ms=0,  # Not tracked separately yet
            generation_time_ms=latency_ms,
            total_time_ms=total_time_ms
        )
        metrics.update(latency_metrics)
        
        # Additional custom metrics
        metrics["confidence"] = result.get("confidence", 0.0)
        metrics["num_sources"] = len(sources)
        metrics["is_hallucination"] = 1.0 if result.get("is_hallucination") else 0.0
        
        # Log to MLflow
        run_name = f"query_{int(time.time())}"
        self.tracker.log_query(
            query=query,
            response=answer,
            metrics=metrics,
            sources=sources,
            metadata={
                "model_used": result.get("model_used", "unknown"),
                "query_type": result.get("query_classification", {}).get("query_type") if result.get("query_classification") else "unknown",
                "guardrail_action": result.get("guardrail_action"),
                "sampled": result.get("sampled", False)
            },
            run_name=run_name
        )
    
    def get_stats(self) -> Dict:
        """Get pipeline stats (passthrough)"""
        return self.rag_pipeline.get_stats()
