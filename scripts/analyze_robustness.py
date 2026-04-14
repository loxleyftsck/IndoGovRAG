"""
Enhanced Result Analysis for Level 2 Queries
Analyzes robustness patterns across query complexity levels

Usage:
    python scripts/analyze_robustness.py golden_results_level2.jsonl
"""

import json
import sys
from collections import defaultdict
from typing import List, Dict


def load_results(filepath: str) -> List[Dict]:
    """Load JSONL results"""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def analyze_by_category(results: List[Dict]) -> Dict:
    """Analyze results grouped by category"""
    by_category = defaultdict(list)
    
    for r in results:
        category = r.get('category', 'unknown')
        by_category[category].append(r)
    
    analysis = {}
    for category, items in by_category.items():
        # Calculate metrics
        faithfulness_scores = [i.get('faithfulness_score', 0.5) for i in items if 'faithfulness_score' in i]
        latencies = [i.get('latency_ms', 0) for i in items if 'latency_ms' in i]
        hallucinations = sum(1 for i in items if i.get('is_hallucination', False))
        
        analysis[category] = {
            "count": len(items),
            "avg_faithfulness": sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0,
            "min_faithfulness": min(faithfulness_scores) if faithfulness_scores else 0,
            "max_faithfulness": max(faithfulness_scores) if faithfulness_scores else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "hallucination_count": hallucinations,
            "hallucination_rate": (hallucinations / len(items) * 100) if items else 0
        }
    
    return analysis


def analyze_by_complexity(results: List[Dict]) -> Dict:
    """Analyze results by complexity level"""
    by_complexity = defaultdict(list)
    
    # Load original queries to get complexity
    try:
        with open('tests/golden_queries_level2.json', 'r', encoding='utf-8') as f:
            query_data = json.load(f)
            complexity_map = {q['id']: q.get('complexity', 'unknown') for q in query_data['queries']}
    except:
        complexity_map = {}
    
    for r in results:
        query_id = r.get('query_id', '')
        complexity = complexity_map.get(query_id, 'unknown')
        by_complexity[complexity].append(r)
    
    analysis = {}
    for complexity, items in by_complexity.items():
        faithfulness_scores = [i.get('faithfulness_score', 0.5) for i in items if 'faithfulness_score' in i]
        
        analysis[complexity] = {
            "count": len(items),
            "avg_faithfulness": sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0,
            "hallucination_rate": sum(1 for i in items if i.get('is_hallucination', False)) / len(items) * 100 if items else 0
        }
    
    return analysis


def identify_failure_patterns(results: List[Dict]) -> List[Dict]:
    """Identify common failure patterns"""
    failures = []
    
    for r in results:
        # Define failure conditions
        is_failure = False
        failure_reasons = []
        
        if r.get('is_hallucination', False):
            is_failure = True
            failure_reasons.append("hallucination")
        
        if r.get('faithfulness_score', 1.0) < 0.5:
            is_failure = True
            failure_reasons.append("low_faithfulness")
        
        if r.get('confidence', 1.0) < 0.3 and r.get('chunks_retrieved', 0) > 0:
            is_failure = True
            failure_reasons.append("low_confidence_despite_retrieval")
        
        if r.get('error'):
            is_failure = True
            failure_reasons.append(f"error: {r['error']}")
        
        if is_failure:
            failures.append({
                "query_id": r.get('query_id'),
                "query": r.get('query'),
                "category": r.get('category'),
                "failure_reasons": failure_reasons,
                "faithfulness": r.get('faithfulness_score', 0),
                "answer_snippet": r.get('answer', '')[:100]
            })
    
    return failures


def print_analysis(results: List[Dict]):
    """Print comprehensive analysis"""
    print("\n" + "=" * 70)
    print("📊 LEVEL 2 ROBUSTNESS ANALYSIS")
    print("=" * 70)
    
    # Overall stats
    print(f"\nTotal queries: {len(results)}")
    faithfulness_scores = [r.get('faithfulness_score', 0.5) for r in results if 'faithfulness_score' in r]
    if faithfulness_scores:
        print(f"Overall avg faithfulness: {sum(faithfulness_scores)/len(faithfulness_scores):.2f}")
        print(f"Overall hallucination rate: {sum(1 for r in results if r.get('is_hallucination'))/len(results)*100:.1f}%")
    
    # By category
    print("\n" + "-" * 70)
    print("📁 ANALYSIS BY CATEGORY")
    print("-" * 70)
    category_analysis = analyze_by_category(results)
    for category, stats in sorted(category_analysis.items()):
        print(f"\n{category.upper()}:")
        print(f"  Queries: {stats['count']}")
        print(f"  Avg Faithfulness: {stats['avg_faithfulness']:.2f}")
        print(f"  Range: {stats['min_faithfulness']:.2f} - {stats['max_faithfulness']:.2f}")
        print(f"  Hallucination Rate: {stats['hallucination_rate']:.1f}%")
        print(f"  Avg Latency: {stats['avg_latency_ms']:.0f}ms")
    
    # By complexity
    print("\n" + "-" * 70)
    print("⚡ ANALYSIS BY COMPLEXITY")
    print("-" * 70)
    complexity_analysis = analyze_by_complexity(results)
    for complexity, stats in sorted(complexity_analysis.items()):
        print(f"\n{complexity.upper()}:")
        print(f"  Queries: {stats['count']}")
        print(f"  Avg Faithfulness: {stats['avg_faithfulness']:.2f}")
        print(f"  Hallucination Rate: {stats['hallucination_rate']:.1f}%")
    
    # Failure patterns
    print("\n" + "-" * 70)
    print("⚠️  FAILURE PATTERNS")
    print("-" * 70)
    failures = identify_failure_patterns(results)
    print(f"\nTotal failures: {len(failures)} ({len(failures)/len(results)*100:.1f}%)")
    
    if failures:
        print("\nTop failures:")
        for i, failure in enumerate(failures[:5], 1):
            print(f"\n{i}. [{failure['query_id']}] {failure['category']}")
            print(f"   Q: {failure['query']}")
            print(f"   Reasons: {', '.join(failure['failure_reasons'])}")
            print(f"   Faithfulness: {failure['faithfulness']:.2f}")
            print(f"   A: {failure['answer_snippet']}...")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)
    
    if category_analysis.get('adversarial', {}).get('hallucination_rate', 0) > 40:
        print("⚠️  HIGH: Adversarial queries have high hallucination")
        print("   → Improve 'no information' detection")
        print("   → Add explicit out-of-scope filtering")
    
    if category_analysis.get('fuzzy_ambiguous', {}).get('hallucination_rate', 0) > 30:
        print("⚠️  HIGH: Fuzzy queries cause hallucinations")
        print("   → Add clarification request templates")
        print("   → Reduce temperature for ambiguous cases")
    
    if complexity_analysis.get('high', {}).get('hallucination_rate', 0) > complexity_analysis.get('medium', {}).get('hallucination_rate', 100):
        print("⚠️  MEDIUM: Complex queries degrade quality")
        print("   → Consider hybrid approach (Ollama → Gemini for complex)")
        print("   → Improve multi-document retrieval")
    
    if sum(faithfulness_scores)/len(faithfulness_scores) < 0.70:
        print("⚠️  CRITICAL: Overall faithfulness below threshold")
        print("   → Review system prompt")
        print("   → Consider better base model")
        print("   → Add retrieval quality checks")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_robustness.py <results.jsonl>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    results = load_results(filepath)
    print_analysis(results)


if __name__ == "__main__":
    main()
