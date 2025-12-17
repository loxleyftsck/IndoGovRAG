"""
Baseline Evaluation Dataset Validator & Previewer
Validates dataset structure and shows question previews
"""

import json
from pathlib import Path
from typing import Dict, List


def load_dataset(filepath: str = "data/baseline_eval_dataset.json") -> Dict:
    """Load the baseline evaluation dataset."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_dataset(dataset: Dict) -> Dict:
    """
    Validate dataset structure and content.
    
    Returns:
        Dict with validation results
    """
    issues = []
    warnings = []
    stats = {
        "total_questions": 0,
        "categories": {},
        "difficulties": {},
        "avg_answer_length": 0,
    }
    
    # Check metadata
    if "metadata" not in dataset:
        issues.append("Missing metadata section")
    else:
        meta = dataset["metadata"]
        required_meta = ["version", "created_date", "description", "total_questions"]
        for field in required_meta:
            if field not in meta:
                issues.append(f"Missing metadata field: {field}")
    
    # Validate questions
    if "questions" not in dataset:
        issues.append("Missing questions array")
        return {"valid": False, "issues": issues, "warnings": warnings, "stats": stats}
    
    questions = dataset["questions"]
    stats["total_questions"] = len(questions)
    
    # Check if matches metadata
    if dataset.get("metadata", {}).get("total_questions") != len(questions):
        warnings.append(f"Metadata says {dataset['metadata']['total_questions']} questions but found {len(questions)}")
    
    required_fields = ["id", "category", "difficulty", "question", "ground_truth"]
    
    for i, q in enumerate(questions):
        # Check required fields
        for field in required_fields:
            if field not in q:
                issues.append(f"Question {i+1} ({q.get('id', 'unknown')}): missing field '{field}'")
        
        # Count categories
        category = q.get("category", "unknown")
        stats["categories"][category] = stats["categories"].get(category, 0) + 1
        
        # Count difficulties
        difficulty = q.get("difficulty", "unknown")
        stats["difficulties"][difficulty] = stats["difficulties"].get(difficulty, 0) + 1
        
        # Check ground truth length
        gt = q.get("ground_truth", "")
        if len(gt) < 50:
            warnings.append(f"Question {q.get('id')}: Ground truth seems short ({len(gt)} chars)")
        
        # Check keywords
        if "keywords_must_have" in q:
            keywords = q["keywords_must_have"]
            ground_truth = q.get("ground_truth", "").lower()
            missing_keywords = [kw for kw in keywords if kw.lower() not in ground_truth]
            if missing_keywords:
                warnings.append(f"Question {q.get('id')}: Keywords not in ground truth: {missing_keywords}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "stats": stats
    }


def print_validation_results(results: Dict):
    """Print validation results in a readable format."""
    print("\n" + "="*70)
    print("📋 BASELINE DATASET VALIDATION RESULTS")
    print("="*70)
    
    if results["valid"]:
        print("\n✅ Dataset is VALID!")
    else:
        print("\n❌ Dataset has ISSUES!")
    
    # Print stats
    stats = results["stats"]
    print(f"\n📊 Statistics:")
    print(f"   Total Questions: {stats['total_questions']}")
    print(f"   \n   Categories:")
    for cat, count in stats["categories"].items():
        print(f"      - {cat}: {count}")
    print(f"   \n   Difficulties:")
    for diff, count in stats["difficulties"].items():
        print(f"      - {diff}: {count}")
    
    # Print issues
    if results["issues"]:
        print(f"\n❌ Issues ({len(results['issues'])}):")
        for issue in results["issues"]:
            print(f"   - {issue}")
    
    # Print warnings
    if results["warnings"]:
        print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
        for warning in results["warnings"]:
            print(f"   - {warning}")
    
    print("\n" + "="*70)


def preview_questions(dataset: Dict, limit: int = None):
    """
    Print question previews.
    
    Args:
        dataset: The dataset dict
        limit: Max number of questions to show (None = all)
    """
    questions = dataset.get("questions", [])
    
    if limit:
        questions = questions[:limit]
    
    print("\n" + "="*70)
    print(f"📝 QUESTION PREVIEWS ({len(questions)} questions)")
    print("="*70)
    
    for q in questions:
        print(f"\n{'─'*70}")
        print(f"ID: {q.get('id')} | Category: {q.get('category')} | Difficulty: {q.get('difficulty')}")
        print(f"{'─'*70}")
        print(f"\nQuestion (ID):")
        print(f"  {q.get('question', 'N/A')}")
        
        if "question_en" in q:
            print(f"\nQuestion (EN):")
            print(f"  {q.get('question_en')}")
        
        print(f"\nGround Truth:")
        gt = q.get('ground_truth', 'N/A')
        # Wrap long text
        if len(gt) > 100:
            print(f"  {gt[:100]}...")
            print(f"  ... [{len(gt)} total characters]")
        else:
            print(f"  {gt}")
        
        if "keywords_must_have" in q:
            print(f"\nKeywords: {', '.join(q['keywords_must_have'])}")
        
        if "evaluation_criteria" in q:
            print(f"\nEvaluation Criteria:")
            for criterion, desc in q["evaluation_criteria"].items():
                print(f"  - {criterion}: {desc}")
    
    print(f"\n{'='*70}\n")


def export_questions_only(dataset: Dict, output_file: str = "data/questions_only.txt"):
    """Export just the questions to a text file for easy review."""
    questions = dataset.get("questions", [])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("BASELINE EVALUATION QUESTIONS\n")
        f.write("="*70 + "\n\n")
        
        for i, q in enumerate(questions, 1):
            f.write(f"{i}. [{q.get('category')}] {q.get('question')}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write(f"Total: {len(questions)} questions\n")
    
    print(f"✅ Exported questions to: {output_file}")


def main():
    """Main validation and preview."""
    dataset_path = "data/baseline_eval_dataset.json"
    
    print("\n🔍 Loading dataset...")
    try:
        dataset = load_dataset(dataset_path)
    except FileNotFoundError:
        print(f"❌ Dataset file not found: {dataset_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return
    
    # Validate
    print("🔍 Validating dataset structure...")
    results = validate_dataset(dataset)
    print_validation_results(results)
    
    if results["valid"]:
        # Preview questions
        preview_questions(dataset, limit=3)
        
        print(f"\n💡 Showing 3/{results['stats']['total_questions']} questions.")
        print(f"   View full dataset at: {dataset_path}")
        
        # Export questions only
        export_questions_only(dataset)
        
        # Summary
        print("\n" + "="*70)
        print("✅ DATASET READY FOR USE")
        print("="*70)
        print(f"\nDataset: {dataset_path}")
        print(f"Questions: {results['stats']['total_questions']}")
        print(f"Categories: {list(results['stats']['categories'].keys())}")
        print(f"Status: VALID ✅")
        print("\nNext steps:")
        print("  1. Peer review ground truth answers")
        print("  2. Test with RAG system once built")
        print("  3. Expand to 100+ questions in Week 2")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()
