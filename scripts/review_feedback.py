"""
Review Feedback Script
Analyze user feedback to identify improvement opportunities
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict


def load_feedback(filepath: str = "data/feedback.jsonl") -> List[Dict]:
    """Load all feedback entries"""
    path = Path(filepath)
    if not path.exists():
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def analyze_feedback(feedback_entries: List[Dict]):
    """Analyze feedback and generate insights"""
    
    if not feedback_entries:
        print("📊 No feedback data available yet")
        return
    
    # Basic stats
    total = len(feedback_entries)
    ratings = [e.get('rating', 0) for e in feedback_entries if e.get('rating')]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
    
    # Type breakdown
    types = defaultdict(int)
    for e in feedback_entries:
        types[e.get('feedback_type', 'unknown')] += 1
    
    # Low-rated queries
    low_rated = [e for e in feedback_entries if e.get('rating', 5) <= 2]
    
    # Print analysis
    print("=" * 60)
    print("📊 FEEDBACK ANALYSIS REPORT")
    print("=" * 60)
    
    print(f"\n📈 OVERVIEW:")
    print(f"   Total feedback: {total}")
    print(f"   Average rating: {avg_rating:.2f}/5.0")
    print(f"   Response breakdown:")
    for ftype, count in types.items():
        print(f"      {ftype}: {count} ({count/total*100:.1f}%)")
    
    print(f"\n🚨 LOW-RATED QUERIES ({len(low_rated)} queries ≤2 stars):")
    if low_rated:
        for i, entry in enumerate(low_rated[:10], 1):  # Top 10
            print(f"\n   #{i} Rating: {entry.get('rating')}/5")
            print(f"      Request ID: {entry.get('request_id')}")
            print(f"      Feedback type: {entry.get('feedback_type')}")
            if entry.get('comment'):
                print(f"      Comment: {entry.get('comment')[:100]}")
    else:
        print("   ✅ No low-rated queries!")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if avg_rating < 3.5:
        print("   ⚠️  CRITICAL: Average rating below 3.5")
        print("      → Investigate recent changes")
        print("      → Review last 24h deployment")
    
    if len(low_rated) > total * 0.20:  # >20% low-rated
        print("   ⚠️  WARNING: >20% of queries are low-rated")
        print("      → Add low-rated queries to golden set")
        print("      → Analyze retrieval quality")
    
    if types.get('report', 0) > 0:
        print(f"   ⚠️  {types['report']} queries reported")
        print("      → Review reported content immediately")
    
    print(f"\n📋 SUGGESTED GOLDEN SET ADDITIONS:")
    if low_rated:
        print("   Add these queries to golden test set:")
        for i, entry in enumerate(low_rated[:5], 1):
            print(f"   {i}. Request ID: {entry.get('request_id')}")
    
    print("\n" + "=" * 60)


def export_improvement_list(low_rated: List[Dict], output_file: str = "data/improvement_backlog.json"):
    """Export low-rated queries for improvement tracking"""
    backlog = {
        "generated_at": json.loads(json.dumps(datetime.now(), default=str)),
        "queries": [
            {
                "request_id": e.get('request_id'),
                "rating": e.get('rating'),
                "feedback_type": e.get('feedback_type'),
                "comment": e.get('comment'),
                "status": "pending"
            }
            for e in low_rated
        ]
    }
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(backlog, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Exported {len(low_rated)} queries to {output_file}")


if __name__ == "__main__":
    from datetime import datetime
    
    print("\n🔍 LOADING FEEDBACK DATA...")
    feedback = load_feedback()
    
    analyze_feedback(feedback)
    
    # Export low-rated for improvement
    low_rated = [e for e in feedback if e.get('rating', 5) <= 2]
    if low_rated:
        export_improvement_list(low_rated)
