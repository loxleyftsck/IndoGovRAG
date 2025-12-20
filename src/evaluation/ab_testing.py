"""
A/B Testing Framework for RAG Optimization

Provides systematic comparison of RAG configurations with statistical significance testing.
Used for Week 3 optimization experiments.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import time
from pathlib import Path
from datetime import datetime
import statistics
from scipy import stats


@dataclass
class ExperimentConfig:
    """RAG configuration for A/B testing."""
    name: str
    retrieval_method: str  # 'vector', 'bm25', 'hybrid'
    chunk_size: int
    top_k: int
    alpha: float  # For hybrid search (0.0=BM25 only, 1.0=vector only)
    prompt_template: str
    metadata: Dict = None


@dataclass
class ExperimentResult:
    """Single query result from experiment."""
    query_id: str
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str]
    
    # Metrics
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    
    # Performance
    latency_ms: float = 0.0
    tokens_used: int = 0


@dataclass
class ComparisonResult:
    """Result of A/B comparison."""
    config_a_name: str
    config_b_name: str
    
    # Metrics comparison
    metric_improvements: Dict[str, float]  # % improvement
    
    # Statistical significance
    p_values: Dict[str, float]
    is_significant: Dict[str, bool]  # p < 0.05
    
    # Winner
    winner: str  # 'A', 'B', or 'tie'
    confidence: float  # 0-1
    
    # Details
    sample_size: int
    timestamp: str


class ABTester:
    """
    A/B testing framework for RAG optimization.
    
    Features:
    - Run experiments with different configs
    - Statistical significance testing (t-test)
    - Confidence intervals
    - Winner determination
    """
    
    def __init__(self, dataset_path: str):
        """
        Initialize A/B tester.
        
        Args:
            dataset_path: Path to evaluation dataset JSON
        """
        self.dataset = self._load_dataset(dataset_path)
        self.results_dir = Path("experiments/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_dataset(self, path: str) -> List[Dict]:
        """Load evaluation dataset with validation."""
        from pathlib import Path
        
        # Validate path
        dataset_path = Path(path)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        
        # Load JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in dataset: {e}")
        
        # Validate structure
        questions = data.get('questions')
        if not questions:
            raise ValueError(f"No 'questions' field found in {path}")
        
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError(f"'questions' must be non-empty list in {path}")
        
        # Validate first question has required fields
        required_fields = ['id', 'question']
        first_q = questions[0]
        missing = [f for f in required_fields if f not in first_q]
        if missing:
            raise ValueError(f"Questions missing required fields: {missing}")
        
        print(f"✅ Dataset validated: {len(questions)} questions loaded")
        return questions
    
    def run_experiment(
        self,
        config: ExperimentConfig,
        rag_pipeline,
        limit: Optional[int] = None
    ) -> List[ExperimentResult]:
        """
        Run RAG pipeline with given config on dataset.
        
        Args:
            config: RAG configuration
            rag_pipeline: RAG pipeline instance
            limit: Optional limit on number of questions
        
        Returns:
            List of experiment results
        """
        print(f"\n🧪 Running experiment: {config.name}")
        print(f"   Config: retrieval={config.retrieval_method}, chunk={config.chunk_size}, top_k={config.top_k}")
        print(f"   Questions: {limit or len(self.dataset)}")
        print()
        
        # Apply configuration
        rag_pipeline.configure(config)
        
        results = []
        dataset_subset = self.dataset[:limit] if limit else self.dataset
        
        for i, question_data in enumerate(dataset_subset, 1):
            print(f"  [{i}/{len(dataset_subset)}] {question_data['question'][:50]}...")
            
            # Run RAG query
            start_time = time.time()
            
            try:
                response = rag_pipeline.query(
                    question=question_data['question'],
                    top_k=config.top_k
                )
                
                latency = (time.time() - start_time) * 1000
                
                result = ExperimentResult(
                    query_id=question_data['id'],
                    question=question_data['question'],
                    answer=response['answer'],
                    contexts=response['contexts'],
                    ground_truth=question_data.get('ground_truth_answer'),
                    latency_ms=latency,
                    tokens_used=response.get('tokens_used', 0)
                )
                
                # Add RAGAS metrics if available
                if 'metrics' in response:
                    result.faithfulness = response['metrics'].get('faithfulness')
                    result.answer_relevancy = response['metrics'].get('answer_relevancy')
                    result.context_precision = response['metrics'].get('context_precision')
                    result.context_recall = response['metrics'].get('context_recall')
                
                results.append(result)
                
            except Exception as e:
                print(f"    ⚠️ Error: {e}")
                continue
        
        # Save results
        self._save_experiment_results(config, results)
        
        print(f"\n✅ Experiment complete: {len(results)} results")
        return results
    
    def compare_experiments(
        self,
        results_a: List[ExperimentResult],
        results_b: List[ExperimentResult],
        config_a_name: str,
        config_b_name: str
    ) -> ComparisonResult:
        """
        Compare two experiment results with statistical testing.
        
        Args:
            results_a: Results from config A
            results_b: Results from config B
            config_a_name: Name of config A
            config_b_name: Name of config B
        
        Returns:
            Comparison result with statistical analysis
        """
        print(f"\n📊 Comparing: {config_a_name} vs {config_b_name}")
        print(f"   Sample size: {len(results_a)} questions")
        print()
        
        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
        
        metric_improvements = {}
        p_values = {}
        is_significant = {}
        
        for metric in metrics:
            # Extract metric values
            values_a = [getattr(r, metric) for r in results_a if getattr(r, metric) is not None]
            values_b = [getattr(r, metric) for r in results_b if getattr(r, metric) is not None]
            
            if not values_a or not values_b:
                continue
            
            # Calculate means
            mean_a = statistics.mean(values_a)
            mean_b = statistics.mean(values_b)
            
            # Calculate improvement
            improvement = ((mean_b - mean_a) / mean_a * 100) if mean_a > 0 else 0
            metric_improvements[metric] = round(improvement, 2)
            
            # T-test for significance
            if len(values_a) > 1 and len(values_b) > 1:
                try:
                    t_stat, p_value = stats.ttest_ind(values_a, values_b)
                    p_values[metric] = round(p_value, 4)
                    is_significant[metric] = p_value < 0.05
                except Exception as e:
                    print(f"    Warning: t-test failed for {metric}: {e}")
                    p_values[metric] = 1.0
                    is_significant[metric] = False
            else:
                print(f"    Warning: Insufficient data for {metric} t-test (need n>1)")
                p_values[metric] = 1.0
                is_significant[metric] = False
            
            # Print results
            direction = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
            sig_marker = "✅ SIGNIFICANT" if is_significant.get(metric) else "⚠️ not significant"
            
            print(f"  {metric}:")
            print(f"    A: {mean_a:.3f} → B: {mean_b:.3f}  {direction} {improvement:+.1f}%")
            print(f"    p-value: {p_values.get(metric, 'N/A')}  {sig_marker}")
            print()
        
        # Determine winner
        winner, confidence = self._determine_winner(metric_improvements, is_significant)
        
        comparison = ComparisonResult(
            config_a_name=config_a_name,
            config_b_name=config_b_name,
            metric_improvements=metric_improvements,
            p_values=p_values,
            is_significant=is_significant,
            winner=winner,
            confidence=confidence,
            sample_size=len(results_a),
            timestamp=datetime.now().isoformat()
        )
        
        print(f"🏆 Winner: {winner} (confidence: {confidence:.1%})")
        print()
        
        return comparison
    
    def _determine_winner(
        self,
        improvements: Dict[str, float],
        significance: Dict[str, bool]
    ) -> Tuple[str, float]:
        """Determine winner based on improvements and significance."""
        # Count wins (positive improvement + significant)
        wins_b = sum(1 for metric, imp in improvements.items() 
                     if imp > 0 and significance.get(metric, False))
        wins_a = sum(1 for metric, imp in improvements.items() 
                     if imp < 0 and significance.get(metric, False))
        
        total_metrics = len(improvements)
        
        if wins_b > wins_a:
            winner = 'B'
            confidence = wins_b / total_metrics if total_metrics > 0 else 0
        elif wins_a > wins_b:
            winner = 'A'
            confidence = wins_a / total_metrics if total_metrics > 0 else 0
        else:
            winner = 'tie'
            confidence = 0.5
        
        return winner, confidence
    
    def _save_experiment_results(self, config: ExperimentConfig, results: List[ExperimentResult]):
        """Save experiment results to JSON."""
        output = {
            'experiment_name': config.name,
            'config': asdict(config),
            'timestamp': datetime.now().isoformat(),
            'num_results': len(results),
            'results': [asdict(r) for r in results],
            'summary': self._calculate_summary(results)
        }
        
        filename = f"{config.name.lower().replace(' ', '_')}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {filepath}")
    
    def _calculate_summary(self, results: List[ExperimentResult]) -> Dict:
        """Calculate summary statistics."""
        metrics = {}
        
        for metric_name in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']:
            values = [getattr(r, metric_name) for r in results if getattr(r, metric_name) is not None]
            if values:
                metrics[metric_name] = {
                    'mean': round(statistics.mean(values), 3),
                    'std': round(statistics.stdev(values), 3) if len(values) > 1 else 0,
                    'min': round(min(values), 3),
                    'max': round(max(values), 3),
                    'count': len(values)
                }
        
        # Latency stats
        latencies = [r.latency_ms for r in results if r.latency_ms > 0]
        if latencies:
            metrics['latency_ms'] = {
                'mean': round(statistics.mean(latencies), 2),
                'p50': round(statistics.median(latencies), 2),
                'p95': round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if len(latencies) > 1 else latencies[0],
            }
        
        return metrics


# =============================================================================
# DEMO
# =============================================================================

def demo_ab_testing():
    """Demo A/B testing framework."""
    print("🧪 A/B Testing Framework Demo\n")
    
    # This is a demo - in real usage, you'd pass actual RAG pipeline
    print("📋 Framework Features:")
    print("  ✅ Run experiments with different configs")
    print("  ✅ Statistical significance testing (t-test)")
    print("  ✅ Automatic winner determination")
    print("  ✅ Results persistence")
    print()
    
    print("📝 Usage Example:")
    print("""
    tester = ABTester('data/eval_dataset_50q.json')
    
    config_baseline = ExperimentConfig(
        name='baseline',
        retrieval_method='vector',
        chunk_size=512,
        top_k=5,
        alpha=1.0,
        prompt_template='default'
    )
    
    config_hybrid = ExperimentConfig(
        name='hybrid',
        retrieval_method='hybrid',
        chunk_size=512,
        top_k=5,
        alpha=0.5,
        prompt_template='default'
    )
    
    results_baseline = tester.run_experiment(config_baseline, rag_pipeline)
    results_hybrid = tester.run_experiment(config_hybrid, rag_pipeline)
    
    comparison = tester.compare_experiments(
        results_baseline,
        results_hybrid,
        'Baseline (Vector Only)',
        'Hybrid (BM25+Vector)'
    )
    
    print(f"Winner: {comparison.winner}")
    """)
    
    print("\n✅ Framework ready for Week 3 experiments!")


if __name__ == "__main__":
    demo_ab_testing()
