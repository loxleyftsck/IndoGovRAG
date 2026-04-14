"""
MLflow Experiment Tracker for RAG System
Tracks queries, responses, metrics, and model performance
"""

import mlflow
import mlflow.pyfunc
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import os


class ExperimentTracker:
    """
    Production MLflow experiment tracker for RAG queries
    
    Tracks:
    - Query/response pairs
    - Retrieval metrics (precision, recall)
    - Generation metrics (faithfulness, relevance)
    - Latency metrics
    - Model versions
    """
    
    def __init__(
        self,
        experiment_name: str = "indogov-rag-production",
        tracking_uri: Optional[str] = None,
        artifact_location: Optional[str] = None
    ):
        """
        Initialize MLflow experiment tracker
        
        Args:
            experiment_name: Name of MLflow experiment
            tracking_uri: MLflow tracking server URI (None = local)
            artifact_location: Where to store artifacts
        """
        # Set tracking URI (default: local ./mlruns)
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        elif os.getenv("MLFLOW_TRACKING_URI"):
            mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
        
        # Set or create experiment
        mlflow.set_experiment(experiment_name)
        self.experiment = mlflow.get_experiment_by_name(experiment_name)
        
        # Artifact location
        self.artifact_location = artifact_location or "./mlflow_artifacts"
        Path(self.artifact_location).mkdir(parents=True, exist_ok=True)
        
        print(f"✅ MLflow Experiment: {experiment_name}")
        print(f"   Tracking URI: {mlflow.get_tracking_uri()}")
        print(f"   Experiment ID: {self.experiment.experiment_id}")
    
    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Start a new MLflow run
        
        Args:
            run_name: Optional run name
            tags: Optional tags dict
            
        Returns:
            Run ID
        """
        run = mlflow.start_run(run_name=run_name, tags=tags)
        return run.info.run_id
    
    def end_run(self):
        """End current MLflow run"""
        mlflow.end_run()
    
    def log_query(
        self,
        query: str,
        response: str,
        metrics: Dict[str, float],
        sources: List[Dict],
        metadata: Optional[Dict[str, Any]] = None,
        run_name: Optional[str] = None
    ) -> str:
        """
        Log a complete RAG query with all metrics
        
        Args:
            query: User question
            response: Generated answer
            metrics: Performance metrics dict
            sources: Retrieved source documents
            metadata: Additional metadata
            run_name: Optional run name
            
        Returns:
            Run ID
        """
        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            mlflow.log_param("query", query[:100])  # Truncate for display
            mlflow.log_param("query_length", len(query))
            mlflow.log_param("response_length", len(response))
            mlflow.log_param("num_sources", len(sources))
            
            # Log metrics
            for metric_name, metric_value in metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            # Log artifacts
            query_artifact = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "response": response,
                "sources": sources,
                "metadata": metadata or {}
            }
            
            artifact_path = Path(self.artifact_location) / f"query_{run.info.run_id}.json"
            with open(artifact_path, "w", encoding="utf-8") as f:
                json.dump(query_artifact, f, ensure_ascii=False, indent=2)
            
            mlflow.log_artifact(str(artifact_path), "queries")
            
            # Log tags
            mlflow.set_tag("query_type", metadata.get("query_type", "unknown") if metadata else "unknown")
            mlflow.set_tag("model", metadata.get("model_used", "unknown") if metadata else "unknown")
            
            return run.info.run_id
    
    def log_model_metrics(
        self,
        model_name: str,
        model_version: str,
        metrics: Dict[str, float],
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Log model-level metrics (for evaluation runs)
        
        Args:
            model_name: LLM model name
            model_version: Model version/quantization
            metrics: Aggregate metrics
            params: Model parameters
        """
        with mlflow.start_run(run_name=f"eval_{model_name}_{model_version}") as run:
            # Log model info
            mlflow.log_param("model_name", model_name)
            mlflow.log_param("model_version", model_version)
            
            if params:
                for param_name, param_value in params.items():
                    mlflow.log_param(param_name, param_value)
            
            # Log metrics
            for metric_name, metric_value in metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            # Tag
            mlflow.set_tag("run_type", "model_evaluation")
            mlflow.set_tag("model", f"{model_name}:{model_version}")
    
    def log_batch_evaluation(
        self,
        evaluation_name: str,
        queries: List[Dict[str, Any]],
        aggregate_metrics: Dict[str, float]
    ):
        """
        Log batch evaluation results (e.g., RAGAS evaluation)
        
        Args:
            evaluation_name: Name of evaluation run
            queries: List of query dicts with results
            aggregate_metrics: Averaged metrics across all queries
        """
        with mlflow.start_run(run_name=evaluation_name) as run:
            # Log aggregate metrics
            for metric_name, metric_value in aggregate_metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            # Save full results as artifact
            results_path = Path(self.artifact_location) / f"{evaluation_name}_results.json"
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "queries": queries,
                    "metrics": aggregate_metrics
                }, f, ensure_ascii=False, indent=2)
            
            mlflow.log_artifact(str(results_path), "evaluations")
            mlflow.set_tag("run_type", "batch_evaluation")
            
            print(f"✅ Logged batch evaluation: {evaluation_name}")
            print(f"   Queries: {len(queries)}")
            print(f"   Run ID: {run.info.run_id}")
    
    def get_best_run(self, metric_name: str = "faithfulness_score", ascending: bool = False) -> Optional[Dict]:
        """
        Get best run by metric
        
        Args:
            metric_name: Metric to optimize
            ascending: True if lower is better
            
        Returns:
            Best run info dict or None
        """
        runs = mlflow.search_runs(
            experiment_ids=[self.experiment.experiment_id],
            order_by=[f"metrics.{metric_name} {'ASC' if ascending else 'DESC'}"],
            max_results=1
        )
        
        if len(runs) > 0:
            return runs.iloc[0].to_dict()
        return None
    
    def compare_models(self, metric_names: List[str]) -> List[Dict]:
        """
        Compare all model evaluation runs
        
        Args:
            metric_names: List of metrics to compare
            
        Returns:
            List of run dicts with metrics
        """
        runs = mlflow.search_runs(
            experiment_ids=[self.experiment.experiment_id],
            filter_string="tags.run_type = 'model_evaluation'"
        )
        
        comparison = []
        for _, run in runs.iterrows():
            run_data = {
                "run_id": run["run_id"],
                "model": run.get("tags.model", "unknown"),
                "start_time": run["start_time"]
            }
            
            for metric_name in metric_names:
                metric_col = f"metrics.{metric_name}"
                run_data[metric_name] = run.get(metric_col, None)
            
            comparison.append(run_data)
        
        return comparison


# Singleton instance
_tracker_instance = None

def get_tracker(
    experiment_name: str = "indogov-rag-production",
    tracking_uri: Optional[str] = None
) -> ExperimentTracker:
    """Get or create global experiment tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ExperimentTracker(
            experiment_name=experiment_name,
            tracking_uri=tracking_uri
        )
    return _tracker_instance
