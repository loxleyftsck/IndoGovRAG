"""
Lightweight Experiment Tracker - 100% FREE
Local JSON-based tracking, no external services needed

Alternative to Weights & Biases for RAG experiments
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class ExperimentConfig:
    """Configuration for an experiment."""
    # Model config
    embedding_model: str
    llm_model: str
    chunk_size: int
    chunk_overlap: int
    
    # Retrieval config
    retrieval_strategy: str  # "vector", "bm25", "hybrid"
    top_k: int
    rerank: bool
    
    # Prompt config
    prompt_template: str
    temperature: float
    max_tokens: int
    
    # Other
    notes: str = ""


@dataclass
class ExperimentResult:
    """Results from an experiment run."""
    # Metrics
    hit_at_1: float
    hit_at_5: float
    mrr: float
    context_precision: float
    context_recall: float
    faithfulness: float
    answer_relevancy: float
    
    # Performance
    avg_latency_ms: float
    p95_latency_ms: float
    avg_cost_per_query: float
    cache_hit_rate: float
    
    # System
    total_queries: int
    failed_queries: int
    error_rate: float


class ExperimentTracker:
    """Track RAG experiments locally."""
    
    def __init__(self, project_name: str = "rag-indonesian-gov", storage_dir: str = "experiments"):
        """
        Initialize experiment tracker.
        
        Args:
            project_name: Name of the project
            storage_dir: Directory to store experiment data
        """
        self.project_name = project_name
        self.storage_path = Path(storage_dir)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.current_experiment = None
        self.experiment_log = []
    
    def _generate_experiment_id(self, config: ExperimentConfig) -> str:
        """Generate unique experiment ID based on config."""
        config_str = json.dumps(asdict(config), sort_keys=True)
        hash_obj = hashlib.md5(config_str.encode())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"exp_{timestamp}_{hash_obj.hexdigest()[:8]}"
    
    def start_experiment(
        self, 
        config: ExperimentConfig,
        experiment_name: Optional[str] = None
    ) -> str:
        """
        Start tracking a new experiment.
        
        Args:
            config: Experiment configuration
            experiment_name: Optional human-readable name
        
        Returns:
            Experiment ID
        """
        exp_id = self._generate_experiment_id(config)
        
        self.current_experiment = {
            "id": exp_id,
            "name": experiment_name or exp_id,
            "project": self.project_name,
            "config": asdict(config),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "results": None,
            "metrics_history": [],
            "logs": [],
        }
        
        print(f"🧪 Started experiment: {experiment_name or exp_id}")
        print(f"   ID: {exp_id}")
        
        return exp_id
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """
        Log metrics for current experiment.
        
        Args:
            metrics: Dict of metric_name -> value
            step: Optional step number
        """
        if not self.current_experiment:
            raise ValueError("No active experiment. Call start_experiment() first.")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "metrics": metrics
        }
        
        self.current_experiment["metrics_history"].append(log_entry)
        
        # Print key metrics
        print(f"📊 Step {step}: " + ", ".join(f"{k}={v:.3f}" for k, v in metrics.items()))
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message for current experiment."""
        if not self.current_experiment:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        self.current_experiment["logs"].append(log_entry)
        print(f"[{level}] {message}")
    
    def finish_experiment(self, results: ExperimentResult):
        """
        Finish current experiment and save results.
        
        Args:
            results: Final experiment results
        """
        if not self.current_experiment:
            raise ValueError("No active experiment to finish.")
        
        self.current_experiment["end_time"] = datetime.now().isoformat()
        self.current_experiment["results"] = asdict(results)
        
        # Calculate duration
        start = datetime.fromisoformat(self.current_experiment["start_time"])
        end = datetime.fromisoformat(self.current_experiment["end_time"])
        duration = (end - start).total_seconds()
        self.current_experiment["duration_seconds"] = duration
        
        # Save experiment
        self._save_experiment(self.current_experiment)
        
        # Add to log
        self.experiment_log.append(self.current_experiment)
        
        print(f"\n✅ Experiment finished: {self.current_experiment['name']}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Hit@1: {results.hit_at_1:.2%}")
        print(f"   MRR: {results.mrr:.3f}")
        print(f"   Faithfulness: {results.faithfulness:.2%}")
        
        # Clear current
        exp_id = self.current_experiment["id"]
        self.current_experiment = None
        
        return exp_id
    
    def _save_experiment(self, experiment: Dict):
        """Save experiment to JSON file."""
        exp_id = experiment["id"]
        filepath = self.storage_path / f"{exp_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(experiment, f, indent=2, ensure_ascii=False)
        
        # Also update index
        self._update_index(experiment)
    
    def _update_index(self, experiment: Dict):
        """Update experiments index file."""
        index_path = self.storage_path / "experiments_index.json"
        
        # Load existing index
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {"experiments": []}
        
        # Add or update experiment summary
        summary = {
            "id": experiment["id"],
            "name": experiment["name"],
            "start_time": experiment["start_time"],
            "end_time": experiment.get("end_time"),
            "config_summary": {
                "embedding_model": experiment["config"]["embedding_model"],
                "retrieval_strategy": experiment["config"]["retrieval_strategy"],
                "top_k": experiment["config"]["top_k"],
            },
            "key_metrics": experiment.get("results", {}),
        }
        
        # Remove if exists (update)
        index["experiments"] = [e for e in index["experiments"] if e["id"] != experiment["id"]]
        index["experiments"].append(summary)
        
        # Sort by start time (newest first)
        index["experiments"].sort(key=lambda x: x["start_time"], reverse=True)
        
        # Save index
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def list_experiments(self, limit: int = 10) -> List[Dict]:
        """
        List recent experiments.
        
        Args:
            limit: Max number to return
        
        Returns:
            List of experiment summaries
        """
        index_path = self.storage_path / "experiments_index.json"
        
        if not index_path.exists():
            return []
        
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        return index["experiments"][:limit]
    
    def load_experiment(self, exp_id: str) -> Dict:
        """Load a specific experiment by ID."""
        filepath = self.storage_path / f"{exp_id}.json"
        
        if not filepath.exists():
            raise ValueError(f"Experiment {exp_id} not found")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def compare_experiments(self, exp_ids: List[str]) -> Dict:
        """
        Compare multiple experiments.
        
        Args:
            exp_ids: List of experiment IDs to compare
        
        Returns:
            Comparison dict with metrics side-by-side
        """
        experiments = [self.load_experiment(exp_id) for exp_id in exp_ids]
        
        comparison = {
            "experiments": [],
            "best_on_metric": {}
        }
        
        # Collect data
        for exp in experiments:
            if not exp.get("results"):
                continue
            
            comparison["experiments"].append({
                "id": exp["id"],
                "name": exp["name"],
                "config": exp["config"],
                "results": exp["results"]
            })
        
        # Find best on each metric
        if comparison["experiments"]:
            results = [e["results"] for e in comparison["experiments"]]
            for metric in results[0].keys():
                values = [(e["id"], e["results"][metric]) for e in comparison["experiments"]]
                best = max(values, key=lambda x: x[1])
                comparison["best_on_metric"][metric] = {
                    "experiment_id": best[0],
                    "value": best[1]
                }
        
        return comparison
    
    def print_comparison(self, exp_ids: List[str]):
        """Print side-by-side comparison of experiments."""
        comp = self.compare_experiments(exp_ids)
        
        if not comp["experiments"]:
            print("No experiments with results to compare")
            return
        
        print("\n" + "="*90)
        print("📊 EXPERIMENT COMPARISON")
        print("="*90)
        
        # Print configs
        print("\n🔧 Configurations:")
        for exp in comp["experiments"]:
            print(f"\n  {exp['name']} ({exp['id']}):")
            config = exp["config"]
            print(f"    Embedding: {config['embedding_model']}")
            print(f"    Retrieval: {config['retrieval_strategy']} (top-k={config['top_k']})")
            print(f"    Rerank: {config['rerank']}")
            print(f"    Chunk size: {config['chunk_size']}")
        
        # Print metrics table
        print("\n📈 Results:")
        print(f"\n{'Metric':<25}", end="")
        for exp in comp["experiments"]:
            print(f"{exp['name'][:15]:<20}", end="")
        print()
        print("-" * 90)
        
        # Key metrics
        key_metrics = ["hit_at_1", "mrr", "faithfulness", "answer_relevancy", "avg_latency_ms"]
        
        for metric in key_metrics:
            print(f"{metric:<25}", end="")
            for exp in comp["experiments"]:
                value = exp["results"].get(metric, 0)
                
                # Format based on metric
                if "rate" in metric or "hit" in metric or "faithfulness" in metric or "relevancy" in metric:
                    formatted = f"{value:.2%}"
                elif "latency" in metric or "cost" in metric:
                    formatted = f"{value:.3f}"
                else:
                    formatted = f"{value:.3f}"
                
                # Highlight best
                best_exp = comp["best_on_metric"].get(metric, {}).get("experiment_id")
                if exp["id"] == best_exp:
                    formatted = f"⭐ {formatted}"
                
                print(f"{formatted:<20}", end="")
            print()
        
        print("\n" + "="*90)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_experiment_config(
    embedding_model: str = "multilingual-e5-base",
    retrieval_strategy: str = "vector",
    chunk_size: int = 512,
    top_k: int = 5,
    **kwargs
) -> ExperimentConfig:
    """Quickly create experiment config with defaults."""
    defaults = {
        "llm_model": "gemini-pro",
        "chunk_overlap": chunk_size // 4,
        "rerank": False,
        "prompt_template": "default",
        "temperature": 0.7,
        "max_tokens": 500,
        "notes": ""
    }
    defaults.update(kwargs)
    
    return ExperimentConfig(
        embedding_model=embedding_model,
        retrieval_strategy=retrieval_strategy,
        chunk_size=chunk_size,
        top_k=top_k,
        **defaults
    )


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing Experiment Tracker\n")
    
    # Initialize tracker
    tracker = ExperimentTracker()
    
    # Experiment 1: Baseline
    config1 = create_experiment_config(
        embedding_model="multilingual-e5-base",
        retrieval_strategy="vector",
        chunk_size=512,
        top_k=5,
        notes="Baseline experiment"
    )
    
    exp1_id = tracker.start_experiment(config1, "Baseline Vector Search")
    tracker.log_metrics({"hit_at_1": 0.75, "mrr": 0.82}, step=1)
    tracker.log("Completed evaluation on 10 queries")
    
    results1 = ExperimentResult(
        hit_at_1=0.75,
        hit_at_5=0.90,
        mrr=0.82,
        context_precision=0.85,
        context_recall=0.78,
        faithfulness=0.88,
        answer_relevancy=0.83,
        avg_latency_ms=120.5,
        p95_latency_ms=180.2,
        avg_cost_per_query=0.002,
        cache_hit_rate=0.0,
        total_queries=10,
        failed_queries=0,
        error_rate=0.0
    )
    
    tracker.finish_experiment(results1)
    
    # Experiment 2: Hybrid search
    config2 = create_experiment_config(
        embedding_model="multilingual-e5-base",
        retrieval_strategy="hybrid",
        chunk_size=512,
        top_k=5,
        rerank=True,
        notes="Hybrid search with reranking"
    )
    
    exp2_id = tracker.start_experiment(config2, "Hybrid Search + Rerank")
    tracker.log_metrics({"hit_at_1": 0.85, "mrr": 0.89}, step=1)
    
    results2 = ExperimentResult(
        hit_at_1=0.85,
        hit_at_5=0.95,
        mrr=0.89,
        context_precision=0.90,
        context_recall=0.85,
        faithfulness=0.92,
        answer_relevancy=0.88,
        avg_latency_ms=150.3,
        p95_latency_ms=210.5,
        avg_cost_per_query=0.003,
        cache_hit_rate=0.0,
        total_queries=10,
        failed_queries=0,
        error_rate=0.0
    )
    
    tracker.finish_experiment(results2)
    
    # List experiments
    print("\n📋 Recent Experiments:")
    recent = tracker.list_experiments(limit=5)
    for exp in recent:
        print(f"  - {exp['name']} ({exp['id']})")
    
    # Compare
    print()
    tracker.print_comparison([exp1_id, exp2_id])
    
    print("\n✅ Experiment tracking demo complete!")
    print(f"📁 Data saved to: {tracker.storage_path}")
