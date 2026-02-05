"""
Unit tests for MLOps components
Tests experiment tracker, metrics logger, and integration
"""

import pytest
import mlflow
from src.mlops.experiment_tracker import ExperimentTracker, get_tracker
from src.mlops.metrics_logger import RAGMetricsLogger
import tempfile
import shutil
from pathlib import Path


class TestExperimentTracker:
    """Test MLflow experiment tracker"""
    
    @pytest.fixture
    def temp_mlflow_dir(self):
        """Create temporary MLflow tracking directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def tracker(self, temp_mlflow_dir):
        """Create tracker with temp directory"""
        tracking_uri = f"file://{temp_mlflow_dir}/mlruns"
        artifact_location = f"{temp_mlflow_dir}/artifacts"
        
        tracker = ExperimentTracker(
            experiment_name="test_experiment",
            tracking_uri=tracking_uri,
            artifact_location=artifact_location
        )
        return tracker
    
    def test_tracker_initialization(self, tracker):
        """Test tracker initializes correctly"""
        assert tracker.experiment is not None
        assert tracker.experiment.name == "test_experiment"
        assert Path(tracker.artifact_location).exists()
    
    def test_log_query(self, tracker):
        """Test logging a single query"""
        run_id = tracker.log_query(
            query="Apa syarat KTP?",
            response="Persyaratan KTP: fotokopi KK, akta lahir...",
            metrics={
                "faithfulness": 0.95,
                "latency_ms": 1500,
                "confidence": 0.88
            },
            sources=[
                {"doc_id": "doc1", "title": "Perpres 26/2009"},
                {"doc_id": "doc2", "title": "UU Adminduk"}
            ],
            metadata={"query_type": "legal", "model_used": "llama3.1"}
        )
        
        # Verify run was created
        assert run_id is not None
        
        # Verify artifact was created
        artifact_file = Path(tracker.artifact_location) / f"query_{run_id}.json"
        assert artifact_file.exists()
    
    def test_log_model_metrics(self, tracker):
        """Test logging model-level metrics"""
        tracker.log_model_metrics(
            model_name="llama3.1",
            model_version="8b-instruct-q4",
            metrics={
                "avg_faithfulness": 0.92,
                "avg_latency_ms": 1800,
                "throughput_qpm": 4.5
            },
            params={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 512
            }
        )
        
        # Should complete without error
        assert True
    
    def test_log_batch_evaluation(self, tracker):
        """Test logging batch evaluation results"""
        queries = [
            {"query": "Q1", "answer": "A1", "faithfulness": 0.9},
            {"query": "Q2", "answer": "A2", "faithfulness": 0.85},
            {"query": "Q3", "answer": "A3", "faithfulness": 0.95}
        ]
        
        tracker.log_batch_evaluation(
            evaluation_name="ragas_eval_01",
            queries=queries,
            aggregate_metrics={
                "avg_faithfulness": 0.90,
                "avg_relevance": 0.88
            }
        )
        
        # Verify evaluation artifact exists
        eval_file = Path(tracker.artifact_location) / "ragas_eval_01_results.json"
        assert eval_file.exists()


class TestRAGMetricsLogger:
    """Test RAG metrics logger"""
    
    def test_calculate_retrieval_metrics(self):
        """Test retrieval metrics calculation"""
        retrieved_docs = [
            {"doc_id": "doc1"},
            {"doc_id": "doc2"},
            {"doc_id": "doc3"}
        ]
        relevant_doc_ids = ["doc2", "doc4"]
        
        metrics = RAGMetricsLogger.calculate_retrieval_metrics(
            retrieved_docs=retrieved_docs,
            relevant_doc_ids=relevant_doc_ids,
            k=3
        )
        
        # Should have precision, recall, f1, mrr
        assert "precision@3" in metrics
        assert "recall@3" in metrics
        assert "f1@3" in metrics
        assert "mrr" in metrics
        
        # Check values
        assert metrics["precision@3"] == pytest.approx(1/3)  # 1 relevant out of 3
        assert metrics["recall@3"] == pytest.approx(1/2)  # 1 found out of 2 relevant
        assert metrics["mrr"] == pytest.approx(1/2)  # First relevant at position 2
    
    def test_calculate_generation_metrics(self):
        """Test generation metrics calculation"""
        metrics = RAGMetricsLogger.calculate_generation_metrics(
            answer="KTP requires fotokopi KK and akta lahir",
            context="Requirements for KTP include fotokopi KK, akta lahir, and surat pengantar",
            faithfulness_score=0.95
        )
        
        # Should have basic metrics
        assert "answer_length" in metrics
        assert "answer_words" in metrics
        assert "context_coverage" in metrics
        assert "faithfulness" in metrics
        
        # Check values
        assert metrics["answer_words"] == 7
        assert metrics["faithfulness"] == 0.95
        assert metrics["context_coverage"] > 0  # Some overlap
    
    def test_calculate_latency_metrics(self):
        """Test latency metrics calculation"""
        metrics = RAGMetricsLogger.calculate_latency_metrics(
            retrieval_time_ms=500,
            generation_time_ms=1500,
            total_time_ms=2000
        )
        
        # Should have all latency metrics
        assert "latency_retrieval_ms" in metrics
        assert "latency_generation_ms" in metrics
        assert "latency_total_ms" in metrics
        assert "latency_retrieval_pct" in metrics
        assert "latency_generation_pct" in metrics
        
        # Check percentages
        assert metrics["latency_retrieval_pct"] == pytest.approx(25.0)
        assert metrics["latency_generation_pct"] == pytest.approx(75.0)
    
    def test_aggregate_batch_metrics(self):
        """Test batch metrics aggregation"""
        metric_dicts = [
            {"faithfulness": 0.9, "latency_ms": 1500},
            {"faithfulness": 0.85, "latency_ms": 1800},
            {"faithfulness": 0.95, "latency_ms": 1200}
        ]
        
        aggregated = RAGMetricsLogger.aggregate_batch_metrics(metric_dicts)
        
        # Should have mean, std, min, max for each metric
        assert "faithfulness_mean" in aggregated
        assert "faithfulness_std" in aggregated
        assert "faithfulness_min" in aggregated
        assert "faithfulness_max" in aggregated
        
        # Check values
        assert aggregated["faithfulness_mean"] == pytest.approx(0.90)
        assert aggregated["faithfulness_min"] == pytest.approx(0.85)
        assert aggregated["faithfulness_max"] == pytest.approx(0.95)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
