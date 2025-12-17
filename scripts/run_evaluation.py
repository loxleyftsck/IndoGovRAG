"""
Run RAGAS Evaluation on Dataset
Batch evaluation script for RAG system
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.ragas_evaluator import RAGASEvaluator
from src.rag.pipeline import RAGPipeline
from src.retrieval.vector_search import VectorStore


def load_dataset(filepath: str) -> List[Dict]:
    """Load evaluation dataset."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('questions', data.get('documents', []))


def run_evaluation(
    dataset_path: str = "data/baseline_eval_dataset.json",
    output_path: str = "data/evaluations/eval_results.json",
    use_ragas: bool = False
):
    """
    Run complete evaluation pipeline.
    
    Args:
        dataset_path: Path to evaluation dataset
        output_path: Path to save results
        use_ragas: Enable RAGAS metrics (requires API key)
    """
    print("="*70)
    print(" 🧪 RAG EVALUATION PIPELINE")
    print("="*70)
    print()
    
    # Load dataset
    print(f"📂 Loading dataset: {dataset_path}")
    dataset = load_dataset(dataset_path)
    print(f"✅ Loaded {len(dataset)} questions")
    print()
    
   # Initialize RAG pipeline
    print("🔧 Initializing RAG pipeline...")
    try:
        vector_store = VectorStore()
        
        if vector_store.collection.count() == 0:
            print("⚠️  Vector store is empty!")
            print("   Run vector_search.py demo first to add sample data")
            return
        
        rag = RAGPipeline(vector_store=vector_store)
        print(f"✅ RAG pipeline ready ({vector_store.collection.count()} chunks)")
    except Exception as e:
        print(f"❌ Failed to initialize RAG: {e}")
        return
    
    print()
    
    # Initialize RAGAS evaluator
    print("📊 Initializing RAGAS evaluator...")
    evaluator = RAGASEvaluator(use_api=use_ragas)
    print()
    
    # Run evaluation
    print("🚀 Starting evaluation...")
    print("="*70)
    
    questions = []
    answers = []
    contexts_list = []
    ground_truths = []
    response_times = []
    
    for i, item in enumerate(dataset, 1):
        question = item.get('question', '')
        print(f"\n[{i}/{len(dataset)}] {question[:60]}...")
        
        # Query RAG
        start_time = time.time()
        try:
            result = rag.query(question)
            elapsed = time.time() - start_time
            
            answer = result['answer']
            contexts = [c['text'] for c in result['retrieved_chunks']]
            ground_truth = item.get('ground_truth_answer')
            
            questions.append(question)
            answers.append(answer)
            contexts_list.append(contexts)
            ground_truths.append(ground_truth)
            response_times.append(elapsed)
            
            print(f"   ✅ Answered in {elapsed:.2f}s")
            print(f"   Answer: {answer[:80]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            questions.append(question)
            answers.append(f"Error: {e}")
            contexts_list.append([])
            ground_truths.append(item.get('ground_truth_answer'))
            response_times.append(0.0)
    
    print("\n" + "="*70)
    print("📊 Running RAGAS evaluation...")
    
    # Evaluate with RAGAS
    results = evaluator.evaluate_batch(
        questions=questions,
        answers=answers,
        contexts_list=contexts_list,
        ground_truths=ground_truths,
        response_times=response_times
    )
    
    # Print summary
    evaluator.print_summary()
    
    # Save results
    evaluator.save_results(output_path)
    
    print("\n✅ Evaluation complete!")
    print(f"📄 Results saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG evaluation")
    parser.add_argument(
        '--dataset',
        default='data/baseline_eval_dataset.json',
        help='Path to evaluation dataset'
    )
    parser.add_argument(
        '--output',
        default='data/evaluations/eval_results.json',
        help='Path to save results'
    )
    parser.add_argument(
        '--use-ragas',
        action='store_true',
        help='Enable RAGAS metrics (requires API key)'
    )
    
    args = parser.parse_args()
    
    run_evaluation(
        dataset_path=args.dataset,
        output_path=args.output,
        use_ragas=args.use_ragas
    )
