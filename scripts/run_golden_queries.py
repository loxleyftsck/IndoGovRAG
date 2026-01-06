"""
Golden Queries Batch Runner
Automated evaluation of RAG system using predefined test queries

Usage:
    python scripts/run_golden_queries.py
    python scripts/run_golden_queries.py --output results.jsonl
    python scripts/run_golden_queries.py --with-judge
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.ollama_pipeline import OllamaRAGPipeline
from src.evaluation.faithfulness_judge import FaithfulnessJudge


def load_golden_queries(path: str = "tests/golden_queries.json") -> List[Dict]:
    """Load golden queries from JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['queries']


def run_evaluation(
    queries: List[Dict],
    pipeline: OllamaRAGPipeline,
    judge: FaithfulnessJudge = None,
    verbose: bool = True
) -> List[Dict]:
    """
    Run evaluation on all golden queries
    
    Args:
        queries: List of query dicts
        pipeline: RAG pipeline instance
        judge: Optional faithfulness judge
        verbose: Print progress
        
    Returns:
        List of result dicts
    """
    results = []
    total = len(queries)
    
    print(f"\n🚀 Running {total} golden queries...")
    print("=" * 60)
    
    for idx, query_data in enumerate(queries, 1):
        query_id = query_data['id']
        query = query_data['query']
        category = query_data['category']
        
        if verbose:
            print(f"\n[{idx}/{total}] {query_id} ({category})")
            print(f"Q: {query}")
        
        # Skip empty queries
        if not query or query.strip() == "":
            result = {
                "query_id": query_id,
                "query": query,
                "category": category,
                "error": "empty_query",
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            if verbose:
                print("⚠️  Skipped (empty query)")
            continue
        
        # Run RAG query
        try:
            rag_result = pipeline.query(query)
            
            # Build result
            result = {
                "query_id": query_id,
                "query": query,
                "category": category,
                "answer": rag_result['answer'],
                "model_used": rag_result['model_used'],
                "chunks_retrieved": len(rag_result['contexts']),
                "confidence": rag_result['confidence'],
                "tokens_used": rag_result['tokens_used'],
                "latency_ms": rag_result['latency_ms'],
                "timestamp": datetime.now().isoformat()
            }
            
            # Faithfulness evaluation (if judge provided)
            if judge and rag_result['model_used'] != 'error':
                context = "\n\n".join(rag_result['contexts'][:3])  # Top 3 chunks
                
                eval_result = judge.evaluate(
                    question=query,
                    context=context,
                    answer=rag_result['answer']
                )
                
                result["faithfulness_score"] = eval_result['score']
                result["is_hallucination"] = eval_result['is_hallucination']
                result["faithfulness_reasoning"] = eval_result['reasoning'][:100]  # Truncate
                
                if verbose:
                    print(f"✅ Faithfulness: {eval_result['score']:.2f} {'⚠️  HALLUCINATION' if eval_result['is_hallucination'] else ''}")
            
            # Check expected keywords (basic validation)
            if 'expected_context_keywords' in query_data:
                keywords = query_data['expected_context_keywords']
                answer_lower = rag_result['answer'].lower()
                matched = sum(1 for kw in keywords if kw.lower() in answer_lower)
                result["keywords_matched"] = matched
                result["keywords_total"] = len(keywords)
                
                if verbose:
                    print(f"📊 Keywords: {matched}/{len(keywords)}")
            
            if verbose:
                print(f"⏱️  Latency: {rag_result['latency_ms']:.0f}ms")
                print(f"A: {rag_result['answer'][:100]}...")
            
        except Exception as e:
            result = {
                "query_id": query_id,
                "query": query,
                "category": category,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            if verbose:
                print(f"❌ Error: {e}")
        
        results.append(result)
    
    return results


def save_results(results: List[Dict], output_path: str):
    """Save results to JSONL file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    print(f"\n✅ Results saved to: {output_path}")


def print_summary(results: List[Dict]):
    """Print evaluation summary"""
    total = len(results)
    errors = sum(1 for r in results if 'error' in r)
    successful = total - errors
    
    # Calculate averages
    if successful > 0:
        avg_latency = sum(r.get('latency_ms', 0) for r in results if 'latency_ms' in r) / successful
        avg_chunks = sum(r.get('chunks_retrieved', 0) for r in results if 'chunks_retrieved' in r) / successful
        
        # Faithfulness stats
        faithfulness_scores = [r.get('faithfulness_score') for r in results if 'faithfulness_score' in r]
        if faithfulness_scores:
            avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
            hallucinations = sum(1 for r in results if r.get('is_hallucination', False))
            hallucination_rate = hallucinations / len(faithfulness_scores) * 100
        else:
            avg_faithfulness = None
            hallucination_rate = None
    else:
        avg_latency = 0
        avg_chunks = 0
        avg_faithfulness = None
        hallucination_rate = None
    
    print("\n" + "=" * 60)
    print("📊 EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total queries: {total}")
    print(f"Successful: {successful}")
    print(f"Errors: {errors}")
    print(f"\nPerformance:")
    print(f"  Avg latency: {avg_latency:.0f}ms")
    print(f"  Avg chunks retrieved: {avg_chunks:.1f}")
    
    if avg_faithfulness is not None:
        print(f"\nQuality:")
        print(f"  Avg faithfulness: {avg_faithfulness:.2f}")
        print(f"  Hallucination rate: {hallucination_rate:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Run golden queries evaluation")
    parser.add_argument('--input', default='tests/golden_queries.json', help='Input JSON file')
    parser.add_argument('--output', default=f'golden_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl', help='Output JSONL file')
    parser.add_argument('--with-judge', action='store_true', help='Enable faithfulness evaluation')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    args = parser.parse_args()
    
    # Load queries
    print(f"📁 Loading queries from: {args.input}")
    queries = load_golden_queries(args.input)
    print(f"✅ Loaded {len(queries)} queries")
    
    # Initialize pipeline
    print("\n🤖 Initializing Ollama RAG pipeline...")
    pipeline = OllamaRAGPipeline()
    
    # Initialize judge (if requested)
    judge = None
    if args.with_judge:
        print("⚖️  Initializing faithfulness judge...")
        judge = FaithfulnessJudge()
    
    # Run evaluation
    results = run_evaluation(
        queries=queries,
        pipeline=pipeline,
        judge=judge,
        verbose=not args.quiet
    )
    
    # Save results
    save_results(results, args.output)
    
    # Print summary
    print_summary(results)
    
    # Print judge stats
    if judge:
        stats = judge.get_stats()
        print(f"\n📊 Judge Statistics:")
        print(f"  Total evaluations: {stats['total_evaluations']}")
        print(f"  Avg faithfulness: {stats['avg_faithfulness']:.2f}")
        print(f"  Hallucinations: {stats['hallucination_count']} ({stats['hallucination_rate_percent']:.1f}%)")


if __name__ == "__main__":
    main()
