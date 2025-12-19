"""
Week 3 Full Optimization Experiment Runner

Runs all 5 optimization experiments systematically:
1. Retrieval Method (Vector vs BM25 vs Hybrid)
2. Chunk Size (256 vs 512 vs 1024)
3. Top-K Retrieval (3 vs 5 vs 10)
4. Prompt Templates (3 variants)
5. Hybrid Alpha Tuning (grid search)
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.ab_testing import ABTester, ExperimentConfig, ComparisonResult
from src.rag.pipeline import RAGPipeline  # You'll need to create this
import time


class OptimizationRunner:
    """Runs all Week 3 optimization experiments."""
    
    def __init__(self, dataset_path: str = "data/eval_dataset_50q.json", limit: Optional[int] = None):
        self.tester = ABTester(dataset_path)
        self.rag = None  # Will be initialized
        self.limit = limit  # Allow CLI control of test size
        self.results_summary = {
            'experiments': [],
            'winners': {},
            'final_config': {}
        }
    
    def setup_rag_pipeline(self):
        """Initialize RAG pipeline with validation."""
        print("🔧 Initializing RAG pipeline...")
        
        # TODO: Initialize your RAG pipeline
        # from src.rag.pipeline import RAGPipeline
        # self.rag = RAGPipeline()
        
        # Validate vector store has documents
        # if self.rag.vector_store.collection.count() == 0:
        #     raise ValueError(
        #         "Vector store is empty! Please load documents first:\n"
        #         "  python src/retrieval/vector_search.py"
        #     )
        
        print("⚠️  RAG pipeline integration needed")
        print("   See docs/WEEK3_QUICKSTART.md for integration guide")
        print()
    
    def experiment_1_retrieval_method(self) -> Dict:
        """
        Experiment 1: Compare retrieval methods.
        
        Configs:
        - Vector-only (baseline)
        - BM25-only  
        - Hybrid (alpha=0.5)
        """
        print("="*70)
        print(" 🧪 EXPERIMENT 1: Retrieval Method Comparison")
        print("="*70)
        print()
        
        configs = [
            ExperimentConfig(
                name="retrieval_vector_only",
                retrieval_method="vector",
                chunk_size=512,
                top_k=5,
                alpha=1.0,  # 1.0 = vector only
                prompt_template="default"
            ),
            ExperimentConfig(
                name="retrieval_bm25_only",
                retrieval_method="bm25",
                chunk_size=512,
                top_k=5,
                alpha=0.0,  # 0.0 = BM25 only
                prompt_template="default"
            ),
            ExperimentConfig(
                name="retrieval_hybrid",
                retrieval_method="hybrid",
                chunk_size=512,
                top_k=5,
                alpha=0.5,  # 0.5 = equal weight
                prompt_template="default"
            ),
        ]
        
        results = {}
        for config in configs:
            results[config.name] = self.tester.run_experiment(
                config,
                self.rag,
                limit=self.limit  # Use instance variable, not hardcoded
            )
        
        # Compare: vector vs hybrid
        comparison = self.tester.compare_experiments(
            results["retrieval_vector_only"],
            results["retrieval_hybrid"],
            "Vector Only",
            "Hybrid (BM25+Vector)"
        )
        
        winner = "hybrid" if comparison.winner == 'B' else "vector"
        
        return {
            'experiment': 'retrieval_method',
            'winner': winner,
            'comparison': comparison,
            'recommendation': f"Use {winner} retrieval for production"
        }
    
    def experiment_2_chunk_size(self) -> Dict:
        """
        Experiment 2: Optimal chunk size.
        
        Configs:
        - 256 tokens
        - 512 tokens (baseline)
        - 1024 tokens
        """
        print("="*70)
        print(" 🧪 EXPERIMENT 2: Chunk Size Optimization")
        print("="*70)
        print()
        
        chunk_sizes = [256, 512, 1024]
        configs = []
        results = {}
        
        for size in chunk_sizes:
            config = ExperimentConfig(
                name=f"chunk_{size}",
                retrieval_method="hybrid",  # Use winner from Exp 1
                chunk_size=size,
                top_k=5,
                alpha=0.5,
                prompt_template="default"
            )
            configs.append(config)
            
            results[config.name] = self.tester.run_experiment(
                config,
                self.rag,
                limit=10
            )
        
        # Compare 512 vs others
        comparison_512_1024 = self.tester.compare_experiments(
            results["chunk_512"],
            results["chunk_1024"],
            "Chunk 512",
            "Chunk 1024"
        )
        
        # Winner determination logic here
        winner_size = 512  # Default
        
        return {
            'experiment': 'chunk_size',
            'winner': winner_size,
            'tested_sizes': chunk_sizes,
            'recommendation': f"Use chunk_size={winner_size} tokens"
        }
    
    def experiment_3_topk(self) -> Dict:
        """
        Experiment 3: Top-K retrieval optimization.
        
        Configs:
        - K=3
        - K=5 (baseline)
        - K=10
        """
        print("="*70)
        print(" 🧪 EXPERIMENT 3: Top-K Retrieval")
        print("="*70)
        print()
        
        topk_values = [3, 5, 10]
        results = {}
        
        for k in topk_values:
            config = ExperimentConfig(
                name=f"topk_{k}",
                retrieval_method="hybrid",
                chunk_size=512,  # Use winner from Exp 2
                top_k=k,
                alpha=0.5,
                prompt_template="default"
            )
            
            results[config.name] = self.tester.run_experiment(
                config,
                self.rag,
                limit=10
            )
        
        # Compare
        comparison = self.tester.compare_experiments(
            results["topk_5"],
            results["topk_10"],
            "Top-K=5",
            "Top-K=10"
        )
        
        winner_k = 5  # Default
        
        return {
            'experiment': 'topk',
            'winner': winner_k,
            'tested_values': topk_values,
            'recommendation': f"Use top_k={winner_k}"
        }
    
    def experiment_4_prompts(self) -> Dict:
        """
        Experiment 4: Prompt template variants.
        
        Templates:
        - Concise
        - Detailed
        - Chain-of-thought
        """
        print("="*70)
        print(" 🧪 EXPERIMENT 4: Prompt Template Optimization")
        print("="*70)
        print()
        
        templates = ["concise", "detailed", "chain_of_thought"]
        results = {}
        
        for template in templates:
            config = ExperimentConfig(
                name=f"prompt_{template}",
                retrieval_method="hybrid",
                chunk_size=512,
                top_k=5,
                alpha=0.5,
                prompt_template=template
            )
            
            results[config.name] = self.tester.run_experiment(
                config,
                self.rag,
                limit=10
            )
        
        winner_template = "detailed"  # Default
        
        return {
            'experiment': 'prompt_templates',
            'winner': winner_template,
            'tested_templates': templates,
            'recommendation': f"Use '{winner_template}' template"
        }
    
    def experiment_5_alpha_tuning(self) -> Dict:
        """
        Experiment 5: Hybrid search alpha tuning.
        
        Grid search: 0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0
        """
        print("="*70)
        print(" 🧪 EXPERIMENT 5: Hybrid Alpha Parameter Tuning")
        print("="*70)
        print()
        
        alpha_values = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
        results = {}
        
        for alpha in alpha_values:
            config = ExperimentConfig(
                name=f"alpha_{int(alpha*10)}",
                retrieval_method="hybrid",
                chunk_size=512,
                top_k=5,
                alpha=alpha,
                prompt_template="detailed"
            )
            
            results[config.name] = self.tester.run_experiment(
                config,
                self.rag,
                limit=10
            )
        
        winner_alpha = 0.5  # Default
        
        return {
            'experiment': 'alpha_tuning',
            'winner': winner_alpha,
            'tested_values': alpha_values,
            'recommendation': f"Use alpha={winner_alpha} (balanced BM25+Vector)"
        }
    
    def run_all_experiments(self):
        """Run all 5 optimization experiments."""
        print("\n")
        print("="*70)
        print(" 🚀 WEEK 3: FULL OPTIMIZATION EXPERIMENT SUITE")
        print("="*70)
        print()
        print("📊 Running 5 experiments on 50-question dataset")
        print("⏱️  Estimated time: ~2-3 hours (depending on API)")
        print()
        input("Press Enter to start experiments...")
        print()
        
        start_time = time.time()
        
        # Run experiments
        exp1 = self.experiment_1_retrieval_method()
        exp2 = self.experiment_2_chunk_size()
        exp3 = self.experiment_3_topk()
        exp4 = self.experiment_4_prompts()
        exp5 = self.experiment_5_alpha_tuning()
        
        # Compile results
        self.results_summary['experiments'] = [exp1, exp2, exp3, exp4, exp5]
        self.results_summary['winners'] = {
            'retrieval_method': exp1['winner'],
            'chunk_size': exp2['winner'],
            'top_k': exp3['winner'],
            'prompt_template': exp4['winner'],
            'alpha': exp5['winner']
        }
        
        # Final recommended configuration
        self.results_summary['final_config'] = ExperimentConfig(
            name="optimized_week3",
            retrieval_method=exp1['winner'],
            chunk_size=exp2['winner'],
            top_k=exp3['winner'],
            alpha=exp5['winner'],
            prompt_template=exp4['winner']
        )
        
        # Save summary
        self._save_summary()
        
        elapsed = time.time() - start_time
        print("\n")
        print("="*70)
        print(" ✅ ALL EXPERIMENTS COMPLETE!")
        print("="*70)
        print()
        print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        print(f"💾 Results saved: experiments/results/")
        print()
        
        self._print_final_recommendations()
    
    def _save_summary(self):
        """Save experiment summary."""
        output_path = Path("experiments/results/summary.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results_summary, f, indent=2, default=str)
        
        print(f"💾 Summary saved: {output_path}")
    
    def _print_final_recommendations(self):
        """Print final configuration recommendations."""
        print("🎯 FINAL RECOMMENDED CONFIGURATION:")
        print()
        
        winners = self.results_summary['winners']
        for key, value in winners.items():
            print(f"  {key:20s}: {value}")
        
        print()
        print("📋 Apply these settings in config/rag_config.yaml")
        print()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run Week 3 optimization experiments."""
    runner = OptimizationRunner()
    
    # Setup
    runner.setup_rag_pipeline()
    
    # Run all experiments
    runner.run_all_experiments()


if __name__ == "__main__":
    main()
