"""
P0 Week 1: Analyze Human Review Baseline
Compares LLM judge scores vs human scores, identifies edge cases, generates recommendations
"""

import json
import glob
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import statistics


def load_completed_reviews(pattern: str = "reports/human_review_batch_*_COMPLETED.json") -> List[Dict]:
    """Load all completed review batches"""
    reviews = []
    for file_path in glob.glob(pattern):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                batch = json.load(f)
                reviews.extend(batch.get('queries', []))
        except Exception as e:
            print(f"⚠️ Error loading {file_path}: {e}")
    
    return reviews


def calculate_correlation(reviews: List[Dict]) -> Tuple[float, List[Dict]]:
    """Calculate correlation between LLM judge and human scores"""
    comparisons = []
    
    for review in reviews:
        llm_score = review.get('llm_judge_score')
        human_score = review.get('human_score')
        
        if llm_score is not None and human_score is not None:
            diff = abs(llm_score - human_score)
            comparisons.append({
                'query': review.get('query', '')[:100],
                'llm_score': llm_score,
                'human_score': human_score,
                'difference': round(diff, 3),
                'discrepancy': diff > 0.15  # Flag if >15% difference
            })
    
    if not comparisons:
        return 0.0, []
    
    # Simple correlation: 1 - average absolute difference
    avg_diff = statistics.mean(c['difference'] for c in comparisons)
    correlation = max(0.0, 1.0 - avg_diff)
    
    return round(correlation, 3), comparisons


def extract_edge_cases(reviews: List[Dict]) -> Dict[str, int]:
    """Aggregate edge cases from all reviews"""
    edge_case_counts = {}
    
    for review in reviews:
        cases = review.get('edge_cases_identified', [])
        for case in cases:
            edge_case_counts[case] = edge_case_counts.get(case, 0) + 1
    
    # Sort by frequency
    return dict(sorted(edge_case_counts.items(), key=lambda x: x[1], reverse=True))


def generate_recommendations(comparisons: List[Dict], edge_cases: Dict[str, int]) -> List[str]:
    """Generate actionable recommendations based on findings"""
    recommendations = []
    
    # Check for systematic bias
    llm_higher = sum(1 for c in comparisons if c['llm_score'] > c['human_score'])
    human_higher = sum(1 for c in comparisons if c['human_score'] > c['llm_score'])
    
    if llm_higher > len(comparisons) * 0.6:
        recommendations.append({
            "type": "judge_bias",
            "priority": "P1",
            "finding": "LLM judge consistently scores higher than humans (length bias suspected)",
            "action": "Consider prompt adjustment: add 'Be strict. Penalize unsupported claims.'"
        })
    elif human_higher > len(comparisons) * 0.6:
        recommendations.append({
            "type": "judge_bias",
            "priority": "P2",
            "finding": "Humans consistently score higher (judge may be too strict)",
            "action": "Review judge prompt for overly critical phrasing"
        })
    
    # Check discrepancy rate
    discrepant = sum(1 for c in comparisons if c['discrepancy'])
    if discrepant > len(comparisons) * 0.3:
        recommendations.append({
            "type": "high_discrepancy",
            "priority": "P0",
            "finding": f"{discrepant}/{len(comparisons)} queries have >15% score difference",
            "action": "Increase weekly human review to 15 queries for more calibration data"
        })
    
    # Edge case recommendations
    if "missing_temporal_info" in edge_cases:
        recommendations.append({
            "type": "guardrail_gap",
            "priority": "P1",
            "finding": f"Temporal info missing in {edge_cases['missing_temporal_info']} queries",
            "action": "Add guardrail pattern: check if query asks 'berapa lama' and ensure answer includes timeframe"
        })
    
    if "out_of_scope_not_detected" in edge_cases:
        recommendations.append({
            "type": "guardrail_gap",
            "priority": "P0",
            "finding": f"Out-of-scope queries not caught: {edge_cases['out_of_scope_not_detected']} cases",
            "action": "Review OUT_OF_SCOPE_PATTERNS in guardrails.py, add missing patterns"
        })
    
    if "hallucination_judge_missed" in edge_cases:
        recommendations.append({
            "type": "judge_failure",
            "priority": "P0",
            "finding": f"Judge missed {edge_cases['hallucination_judge_missed']} hallucinations",
            "action": "Critical: Review judge prompt, consider specialized judge model (Lynx)"
        })
    
    return recommendations


def generate_baseline_report(reviews: List[Dict], output_file: str = "reports/human_review_baseline_week1.json"):
    """Generate comprehensive baseline report"""
    
    if not reviews:
        print("❌ No completed reviews found!")
        print("   Expected files: reports/human_review_batch_*_COMPLETED.json")
        return
    
    # Calculate metrics
    correlation, comparisons = calculate_correlation(reviews)
    edge_cases = extract_edge_cases(reviews)
    recommendations = generate_recommendations(comparisons, edge_cases)
    
    # Aggregate human scores
    human_scores = [r['human_score'] for r in reviews if r.get('human_score') is not None]
    llm_scores = [r['llm_judge_score'] for r in reviews if r.get('llm_judge_score') is not None]
    
    baseline = {
        "created_at": datetime.now().isoformat(),
        "week": 1,
        "total_reviews": len(reviews),
        
        "summary_statistics": {
            "human_avg_faithfulness": round(statistics.mean(human_scores), 3) if human_scores else None,
            "llm_avg_faithfulness": round(statistics.mean(llm_scores), 3) if llm_scores else None,
            "judge_human_correlation": correlation,
            "alignment_quality": "Excellent" if correlation > 0.85 else "Good" if correlation > 0.70 else "Needs Improvement"
        },
        
        "discrepancies": {
            "total_comparisons": len(comparisons),
            "high_discrepancy_count": sum(1 for c in comparisons if c['discrepancy']),
            "discrepancy_rate": round(sum(1 for c in comparisons if c['discrepancy']) / len(comparisons), 3) if comparisons else 0,
            "examples": [c for c in comparisons if c['discrepancy']][:5]  # Top 5 discrepancies
        },
        
        "edge_cases": {
            "total_unique": len(edge_cases),
            "top_cases": dict(list(edge_cases.items())[:10]),
            "all_cases": edge_cases
        },
        
        "recommendations": recommendations,
        
        "raw_comparisons": comparisons
    }
    
    # Save baseline
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 WEEK 1 BASELINE ANALYSIS")
    print("="*60 + "\n")
    
    print(f"✅ Analyzed {len(reviews)} human-reviewed queries\n")
    
    print("📈 SUMMARY STATISTICS:")
    print(f"   Human Avg Faithfulness:  {baseline['summary_statistics']['human_avg_faithfulness']}")
    print(f"   LLM Avg Faithfulness:    {baseline['summary_statistics']['llm_avg_faithfulness']}")
    print(f"   Judge-Human Correlation: {correlation} ({baseline['summary_statistics']['alignment_quality']})")
    
    if correlation > 0.70:
        print("   ✅ Judge alignment is acceptable (>0.70)")
    else:
        print("   ⚠️  Judge alignment needs improvement (<0.70)")
    
    print(f"\n🔍 DISCREPANCIES:")
    print(f"   High Discrepancy Rate: {baseline['discrepancies']['discrepancy_rate']} ({baseline['discrepancies']['high_discrepancy_count']}/{len(comparisons)} queries)")
    
    if baseline['discrepancies']['examples']:
        print(f"\n   Top Discrepancies:")
        for ex in baseline['discrepancies']['examples'][:3]:
            print(f"   - '{ex['query'][:60]}...'")
            print(f"     LLM: {ex['llm_score']:.2f} | Human: {ex['human_score']:.2f} | Diff: {ex['difference']:.2f}")
    
    print(f"\n🚨 EDGE CASES IDENTIFIED:")
    if edge_cases:
        for case, count in list(edge_cases.items())[:5]:
            print(f"   - {case}: {count} occurrences")
    else:
        print("   (No edge cases reported)")
    
    print(f"\n💡 RECOMMENDATIONS ({len(recommendations)} items):")
    for rec in recommendations:
        print(f"\n   [{rec['priority']}] {rec['type'].upper()}")
        print(f"   Finding: {rec['finding']}")
        print(f"   Action:  {rec['action']}")
    
    print(f"\n📁 Full report saved to: {output_file}")
    print("\n" + "="*60)
    print("✅ P0 WEEK 1 BASELINE COMPLETE!")
    print("="*60 + "\n")


def main():
    print("🔍 P0 Week 1: Analyzing Human Review Baseline\n")
    
    # Load completed reviews
    print("📂 Loading completed review batches...")
    reviews = load_completed_reviews()
    
    if not reviews:
        print("\n❌ No completed reviews found!")
        print("\nExpected workflow:")
        print("   1. Run: python scripts/extract_review_samples.py")
        print("   2. Fill in: reports/human_review_batch.json")
        print("   3. Save as: reports/human_review_batch_YYYYMMDD_COMPLETED.json")
        print("   4. Run this script again\n")
        return
    
    print(f"   Found {len(reviews)} reviewed queries\n")
    
    # Generate baseline
    print("📊 Generating baseline report...")
    generate_baseline_report(reviews)
    
    print("\n🎯 Next Steps:")
    print("   1. Review recommendations in baseline report")
    print("   2. Update guardrails or prompts if needed")
    print("   3. Continue weekly reviews for ongoing calibration")
    print("   4. Week 2: Implement P1 items (retrieval metrics + feedback)")


if __name__ == "__main__":
    main()
