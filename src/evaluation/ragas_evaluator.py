"""
RAGAS Evaluation Wrapper for Indonesian Government Documents

Implements RAGAS metrics:
- Faithfulness: Answer accuracy vs retrieved context
- Answer Relevancy: Answer quality vs question
- Context Precision: Retrieved chunks relevance
- Context Recall: Coverage of ground truth
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path
from datetime import datetime


@dataclass
class EvaluationResult:
    """Single question evaluation result."""
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str]
    faithfulness: Optional[float]
    answer_relevancy: Optional[float]
    context_precision: Optional[float]
    context_recall: Optional[float]
    response_time: float


class RAGASEvaluator:
    """
    RAGAS metrics evaluator for RAG systems.
    
    Optimized for Indonesian government documents.
    """
    
    def __init__(self, use_api: bool = True):
        """
        Initialize RAGAS evaluator.
        
        Args:
            use_api: Use LLM API for evaluation (requires API key)
        """
        self.use_api = use_api
        
        if use_api:
            self._init_ragas()
        
        self.results: List[EvaluationResult] = []
    
    def _init_ragas(self):
        """Initialize RAGAS with LLM."""
        try:
            from ragas import evaluate
            from ragas.metrics import (
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall
            )
            
            self.evaluate_func = evaluate
            self.metrics = {
                'faithfulness': faithfulness,
                'answer_relevancy': answer_relevancy,
                'context_precision': context_precision,
                'context_recall': context_recall,
            }
            
            print("✅ RAGAS initialized with metrics")
            
        except ImportError:
            print("⚠️  RAGAS not installed. Run: pip install ragas")
            self.use_api = False
        except Exception as e:
            print(f"⚠️  RAGAS initialization failed: {e}")
            self.use_api = False
    
    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        response_time: float = 0.0
    ) -> EvaluationResult:
        """
        Evaluate single RAG response.
        
        Args:
            question: User question
            answer: RAG system answer
            contexts: Retrieved context chunks
            ground_truth: Expected answer (optional)
            response_time: Time taken to generate answer
        
        Returns:
            EvaluationResult with metrics
        """
        if not self.use_api:
            # Return result without metrics if API not available
            return EvaluationResult(
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=ground_truth,
                faithfulness=None,
                answer_relevancy=None,
                context_precision=None,
                context_recall=None,
                response_time=response_time
            )
        
        try:
            from datasets import Dataset
            
            # Prepare data for RAGAS
            data = {
                'question': [question],
                'answer': [answer],
                'contexts': [contexts],
            }
            
            if ground_truth:
                data['ground_truth'] = [ground_truth]
            
            dataset = Dataset.from_dict(data)
            
            # Evaluate
            metrics_to_use = [
                self.metrics['faithfulness'],
                self.metrics['answer_relevancy'],
            ]
            
            if ground_truth:
                metrics_to_use.extend([
                    self.metrics['context_precision'],
                    self.metrics['context_recall'],
                ])
            
            result = self.evaluate_func(
                dataset,
                metrics=metrics_to_use
            )
            
            # Extract scores
            return EvaluationResult(
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=ground_truth,
                faithfulness=result.get('faithfulness'),
                answer_relevancy=result.get('answer_relevancy'),
                context_precision=result.get('context_precision') if ground_truth else None,
                context_recall=result.get('context_recall') if ground_truth else None,
                response_time=response_time
            )
        
        except Exception as e:
            print(f"⚠️  Evaluation failed: {e}")
            return EvaluationResult(
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=ground_truth,
                faithfulness=None,
                answer_relevancy=None,
                context_precision=None,
                context_recall=None,
                response_time=response_time
            )
    
    def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts_list: List[List[str]],
        ground_truths: Optional[List[str]] = None,
        response_times: Optional[List[float]] = None
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple RAG responses.
        
        Args:
            questions: List of questions
            answers: List of answers
            contexts_list: List of context lists
            ground_truths: List of ground truth answers (optional)
            response_times: List of response times (optional)
        
        Returns:
            List of EvaluationResult objects
        """
        from tqdm import tqdm
        
        if ground_truths is None:
            ground_truths = [None] * len(questions)
        
        if response_times is None:
            response_times = [0.0] * len(questions)
        
        results = []
        
        for i in tqdm(range(len(questions)), desc="Evaluating"):
            result = self.evaluate_single(
                question=questions[i],
                answer=answers[i],
                contexts=contexts_list[i],
                ground_truth=ground_truths[i],
                response_time=response_times[i]
            )
            results.append(result)
            self.results.append(result)
        
        return results
    
    def get_summary(self) -> Dict:
        """Get summary statistics of all evaluations."""
        if not self.results:
            return {'total': 0}
        
        total = len(self.results)
        
        # Calculate averages (excluding None values)
        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
        
        summary = {'total': total}
        
        for metric in metrics:
            values = [
                getattr(r, metric) 
                for r in self.results 
                if getattr(r, metric) is not None
            ]
            
            if values:
                summary[f'{metric}_avg'] = sum(values) / len(values)
                summary[f'{metric}_min'] = min(values)
                summary[f'{metric}_max'] = max(values)
                summary[f'{metric}_count'] = len(values)
        
        # Response time stats
        times = [r.response_time for r in self.results if r.response_time > 0]
        if times:
            summary['avg_response_time'] = sum(times) / len(times)
            summary['min_response_time'] = min(times)
            summary['max_response_time'] = max(times)
        
        return summary
    
    def save_results(self, filepath: str = "data/evaluations/ragas_eval.json"):
        """Save evaluation results to JSON."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert results to dict
        results_dict = {
            'timestamp': datetime.now().isoformat(),
            'total_evaluated': len(self.results),
            'summary': self.get_summary(),
            'results': [
                {
                    'question': r.question,
                    'answer': r.answer,
                    'contexts': r.contexts,
                    'ground_truth': r.ground_truth,
                    'faithfulness': r.faithfulness,
                    'answer_relevancy': r.answer_relevancy,
                    'context_precision': r.context_precision,
                    'context_recall': r.context_recall,
                    'response_time': r.response_time,
                }
                for r in self.results
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filepath}")
    
    def print_summary(self):
        """Print evaluation summary."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 RAGAS EVALUATION SUMMARY")
        print("="*60)
        print(f"Total Evaluated: {summary['total']}")
        
        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
        
        for metric in metrics:
            avg_key = f'{metric}_avg'
            if avg_key in summary:
                print(f"\n{metric.replace('_', ' ').title()}:")
                print(f"  Average: {summary[avg_key]:.3f}")
                print(f"  Min: {summary[f'{metric}_min']:.3f}")
                print(f"  Max: {summary[f'{metric}_max']:.3f}")
        
        if 'avg_response_time' in summary:
            print(f"\nResponse Time:")
            print(f"  Average: {summary['avg_response_time']:.2f}s")
            print(f"  Min: {summary['min_response_time']:.2f}s")
            print(f"  Max: {summary['max_response_time']:.2f}s")
        
        print("="*60 + "\n")


# =============================================================================
# DEMO & TESTING
# =============================================================================

def demo_ragas():
    """Demo RAGAS evaluation."""
    
    print("🧪 RAGAS Evaluator Demo\n")
    
    # Initialize evaluator (without API for demo)
    evaluator = RAGASEvaluator(use_api=False)
    
    # Sample evaluation data
    sample_data = [
        {
            'question': "Apa itu KTP elektronik?",
            'answer': "KTP elektronik adalah Kartu Tanda Penduduk yang dilengkapi dengan chip elektronik untuk menyimpan data penduduk.",
            'contexts': [
                "KTP elektronik adalah identitas resmi penduduk dengan chip.",
                "Data yang tersimpan dalam chip meliputi NIK dan biodata."
            ],
            'ground_truth': "KTP elektronik adalah kartu identitas dengan chip elektronik",
            'response_time': 1.5
        }
    ]
    
    print("📋 Sample Data:")
    print(f"   Question: {sample_data[0]['question']}")
    print(f"   Answer: {sample_data[0]['answer'][:60]}...")
    print(f"   Contexts: {len(sample_data[0]['contexts'])} chunks")
    
    # Evaluate
    result = evaluator.evaluate_single(**sample_data[0])
    
    print(f"\n📊 Evaluation Result:")
    print(f"   Faithfulness: {result.faithfulness or 'N/A (API required)'}")
    print(f"   Answer Relevancy: {result.answer_relevancy or 'N/A (API required)'}")
    print(f"   Response Time: {result.response_time}s")
    
    print("\n✅ Demo complete!")
    print("\n📝 Note: Full RAGAS metrics require LLM API (Gemini/OpenAI)")
    print("   Set GEMINI_API_KEY in .env to enable complete evaluation")


if __name__ == "__main__":
    demo_ragas()
