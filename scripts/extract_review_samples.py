"""
Week 1 P0: Human Spot-Check Helper
Extracts production queries for manual review based on priority criteria
"""

import json
import glob
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta
import random


def load_query_logs(log_dir: str = "logs", days_back: int = 7) -> List[Dict]:
    """Load production query logs from JSONL files"""
    logs = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    pattern = f"{log_dir}/ollama_queries_*.jsonl"
    for log_file in sorted(glob.glob(pattern), reverse=True):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        # Parse timestamp
                        ts = datetime.fromisoformat(entry.get('timestamp', ''))
                        if ts >= cutoff_date:
                            logs.append(entry)
        except Exception as e:
            print(f"⚠️ Error reading {log_file}: {e}")
    
    return logs


def filter_for_review(logs: List[Dict], sample_size: int = 10) -> List[Dict]:
    """
    Select queries for human review based on priority:
    1. Faithfulness < 0.8 (if evaluated)
    2. Guardrail triggered (ambiguous/legal/out-of-scope)
    3. High latency (>10s, potential issue)
    4. Random sample from remainder
    """
    priority_1 = []  # Low faithfulness
    priority_2 = []  # Guardrail triggered
    priority_3 = []  # High latency
    normal = []
    
    for log in logs:
        # Skip non-evaluated queries
        if 'faithfulness_score' in log:
            score = log.get('faithfulness_score', 1.0)
            if score < 0.8:
                priority_1.append(log)
                continue
        
        # Check guardrail
        guardrail_action = log.get('guardrail_action')
        if guardrail_action and guardrail_action != 'none':
            priority_2.append(log)
            continue
        
        # Check latency
        latency = log.get('latency_seconds', 0)
        if latency > 10:
            priority_3.append(log)
            continue
        
        normal.append(log)
    
    # Weighted sampling
    samples = []
    
    # Take all P1 (up to 4)
    samples.extend(priority_1[:4])
    remaining = sample_size - len(samples)
    
    # Take some P2 (up to 3)
    if remaining > 0:
        samples.extend(priority_2[:min(3, remaining)])
        remaining = sample_size - len(samples)
    
    # Take some P3 (up to 2)
    if remaining > 0:
        samples.extend(priority_3[:min(2, remaining)])
        remaining = sample_size - len(samples)
    
    # Fill with random normal
    if remaining > 0 and normal:
        samples.extend(random.sample(normal, min(remaining, len(normal))))
    
    return samples


def export_for_review(samples: List[Dict], output_file: str = "reports/human_review_batch.json"):
    """Export selected queries to review template"""
    review_template = {
        "batch_date": datetime.now().isoformat(),
        "total_samples": len(samples),
        "queries": []
    }
    
    for idx, log in enumerate(samples, 1):
        review_template["queries"].append({
            "id": idx,
            "timestamp": log.get('timestamp'),
            "query": log.get('query'),
            "answer": log.get('answer', '')[:500] + "..." if len(log.get('answer', '')) > 500 else log.get('answer', ''),
            "context_snippets": [c[:200] + "..." for c in log.get('context', [])[:3]],
            "llm_judge_score": log.get('faithfulness_score'),
            "is_hallucination": log.get('is_hallucination', False),
            "guardrail_action": log.get('guardrail_action'),
            "latency_seconds": log.get('latency_seconds'),
            
            # Fields for human review
            "human_score": None,  # To be filled: 0.0 - 1.0
            "human_is_hallucination": None,  # To be filled: true/false
            "review_notes": "",  # To be filled
            "edge_cases_identified": []  # To be filled
        })
    
    # Create reports dir if needed
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(review_template, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported {len(samples)} queries to {output_file}")
    print(f"\n📋 Distribution:")
    print(f"   - Low faithfulness (<0.8): {len([s for s in samples if s.get('faithfulness_score', 1.0) < 0.8])}")
    print(f"   - Guardrail triggered: {len([s for s in samples if s.get('guardrail_action') and s.get('guardrail_action') != 'none'])}")
    print(f"   - High latency (>10s): {len([s for s in samples if s.get('latency_seconds', 0) > 10])}")


def main():
    print("🔍 Week 1 P0: Human Spot-Check Helper\n")
    
    # Load recent logs
    print("📂 Loading production logs (past 7 days)...")
    logs = load_query_logs(log_dir="logs", days_back=7)
    print(f"   Found {len(logs)} queries\n")
    
    # Filter for review
    print("🎯 Selecting priority queries for review...")
    samples = filter_for_review(logs, sample_size=10)
    
    # Export
    export_for_review(samples, output_file="reports/human_review_batch.json")
    
    print("\n📝 Next steps:")
    print("   1. Open reports/human_review_batch.json")
    print("   2. For each query, fill in:")
    print("      - human_score (0.0 - 1.0)")
    print("      - human_is_hallucination (true/false)")
    print("      - review_notes (your observations)")
    print("      - edge_cases_identified (array of strings)")
    print("   3. Save as reports/human_review_batch_COMPLETED.json")
    print("\n🎯 Target: 5-10 queries per week for ground truth calibration")


if __name__ == "__main__":
    main()
