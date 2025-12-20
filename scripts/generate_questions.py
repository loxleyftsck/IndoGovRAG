"""
Semi-Automated Question Generator
Generate evaluation questions for Indonesian government documents

Usage:
1. python scripts/generate_questions.py --mode generate
2. Review and edit generated questions
3. python scripts/generate_questions.py --mode validate
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime


# Question templates by category
QUESTION_TEMPLATES = {
    'factual': [
        "Apa itu {concept}?",
        "Siapa yang berhak mendapatkan {benefit}?",
        "Bagaimana cara mendaftar {service}?",
        "Apa syarat untuk mendapatkan {document}?",
        "Kapan {law} mulai berlaku?",
        "Berapa lama masa berlaku {document}?",
        "Apa fungsi dari {institution}?",
        "Dimana bisa mengurus {service}?",
        "Apa saja jenis-jenis {category}?",
        "Apa perbedaan antara {item1} dan {item2}?",
    ],
    'multi_hop': [
        "Jika seseorang ingin {action1}, apakah perlu {action2}?",
        "Apa yang terjadi jika {condition1} dan {condition2}?",
        "Bagaimana hubungan antara {concept1} dengan {concept2}?",
        "Mengapa {policy} penting untuk {goal}?",
        "Apa dampak {regulation} terhadap {stakeholder}?",
    ],
    'summarization': [
        "Jelaskan prosedur lengkap untuk {process}.",
        "Rangkum hak dan kewajiban {role}.",
        "Apa saja tahapan dalam {procedure}?",
        "Jelaskan kebijakan pemerintah tentang {topic}.",
    ],
    'edge_case': [
        "Apa yang terjadi jika {document} hilang?",
        "Bagaimana mengurus {service} untuk WNI di luar negeri?",
        "Apakah ada sanksi jika tidak memiliki {document}?",
        "Bagaimana jika data di {document} salah?",
    ]
}

# Sample concepts for Indonesian government docs
CONCEPTS = {
    'document': ['KTP', 'KK', 'Akta Kelahiran', 'Paspor', 'SIM', 'NPWP'],
    'service': ['BPJS Kesehatan', 'bantuan sosial', 'izin usaha', 'sertifikat tanah'],
    'institution': ['Dukcapil', 'Imigrasi', 'BPN', 'Kemenaker'],
    'law': ['UU ITE', 'UU Pajak', 'PP tentang KTP'],
    'benefit': ['bantuan PKH', 'kartu prakerja', 'subsidi listrik'],
}


def generate_questions_from_templates(target_count: int = 100) -> List[Dict]:
    """
    Generate questions using templates.
    
    Args:
        target_count: Target number of questions
    
    Returns:
        List of question dicts
    """
    questions = []
    
    # Category distribution
    distribution = {
        'factual': int(target_count * 0.4),  # 40
        'multi_hop': int(target_count * 0.3),  # 30
        'summarization': int(target_count * 0.2),  # 20
        'edge_case': int(target_count * 0.1),  # 10
    }
    
    question_id = 1
    
    for category, count in distribution.items():
        templates = QUESTION_TEMPLATES[category]
        
        for i in range(count):
            template = templates[i % len(templates)]
            
            # Simple placeholder filling (manual review needed)
            question_text = template
            
            # Mark difficulty
            if i < count * 0.4:
                difficulty = "easy"
            elif i < count * 0.7:
                difficulty = "medium"
            else:
                difficulty = "hard"
            
            question = {
                "id": f"q{question_id:03d}",
                "question": question_text,
                "category": category,
                "difficulty": difficulty,
                "ground_truth_answer": f"[Manual review needed for q{question_id:03d}]",
                "reference_contexts": [],
                "requires_inference": category in ['multi_hop', 'edge_case'],
                "created_at": datetime.now().isoformat(),
                "reviewed": False
            }
            
            questions.append(question)
            question_id += 1
    
    return questions


def load_existing_dataset(filepath: str) -> Dict:
    """Load existing dataset."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "version": "2.0",
            "created": datetime.now().isoformat(),
            "total_questions": 0,
            "questions": []
        }


def validate_dataset(filepath: str) -> Dict:
    """
    Validate dataset quality.
    
    Checks:
    - All questions have required fields
    - Ground truth answers provided
    - Category distribution correct
    - No duplicates
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data.get('questions', [])
    
    issues = []
    stats = {
        'total': len(questions),
        'by_category': {},
        'by_difficulty': {},
        'missing_ground_truth': 0,
        'not_reviewed': 0,
        'duplicates': 0,
    }
    
    seen_questions = set()
    
    for q in questions:
        # Check required fields
        required = ['id', 'question', 'category', 'ground_truth_answer']
        for field in required:
            if field not in q or not q[field]:
                issues.append(f"Question {q.get('id', '???')}: Missing {field}")
        
        # Check ground truth
        if '[Manual review needed]' in q.get('ground_truth_answer', ''):
            stats['missing_ground_truth'] += 1
            issues.append(f"Question {q['id']}: Ground truth not provided")
        
        # Check reviewed status
        if not q.get('reviewed', False):
            stats['not_reviewed'] += 1
        
        # Check duplicates
        q_text = q.get('question', '').lower()
        if q_text in seen_questions:
            stats['duplicates'] += 1
            issues.append(f"Question {q['id']}: Duplicate question text")
        seen_questions.add(q_text)
        
        # Category stats
        cat = q.get('category', 'unknown')
        stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
        
        # Difficulty stats
        diff = q.get('difficulty', 'unknown')
        stats['by_difficulty'][diff] = stats['by_difficulty'].get(diff, 0) + 1
    
    return {
        'valid': len(issues) == 0,
        'total_issues': len(issues),
        'issues': issues[:10],  # First 10 issues
        'stats': stats
    }


def print_validation_report(report: Dict):
    """Print validation report."""
    print("\n" + "="*70)
    print(" 📊 DATASET VALIDATION REPORT")
    print("="*70)
    print()
    
    stats = report['stats']
    
    print(f"Total Questions: {stats['total']}")
    print()
    
    print("Category Distribution:")
    for cat, count in stats['by_category'].items():
        pct = count / stats['total'] * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")
    print()
    
    print("Difficulty Distribution:")
    for diff, count in stats['by_difficulty'].items():
        pct = count / stats['total'] * 100
        print(f"  {diff}: {count} ({pct:.1f}%)")
    print()
    
    print("Quality Checks:")
    print(f"  Missing ground truth: {stats['missing_ground_truth']}")
    print(f"  Not reviewed: {stats['not_reviewed']}")
    print(f"  Duplicates: {stats['duplicates']}")
    print()
    
    if report['valid']:
        print("✅ Dataset is valid!")
    else:
        print(f"⚠️  Found {report['total_issues']} issues")
        print("\nFirst 10 Issues:")
        for issue in report['issues']:
            print(f"  - {issue}")
    
    print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate evaluation questions")
    parser.add_argument(
        '--mode',
        choices=['generate', 'validate'],
        default='generate',
        help='Mode: generate or validate'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of questions to generate'
    )
    parser.add_argument(
        '--output',
        default='data/baseline_eval_dataset_v2.json',
        help='Output file path'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'generate':
        print(f"🔄 Generating {args.count} questions...")
        
        # Load existing or create new
        data = load_existing_dataset(args.output)
        
        # Generate questions
        new_questions = generate_questions_from_templates(args.count)
        
        # Update dataset
        data['questions'] = new_questions
        data['total_questions'] = len(new_questions)
        data['last_updated'] = datetime.now().isoformat()
        
        # Save
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Generated {len(new_questions)} questions")
        print(f"📄 Saved to: {args.output}")
        print()
        print("⚠️  IMPORTANT: Manual review required!")
        print("   1. Review question templates")
        print("   2. Fill in placeholders")
        print("   3. Add ground truth answers")
        print("   4. Add reference contexts")
        print("   5. Mark as reviewed: true")
        print()
        print(f"Then run: python {__file__} --mode validate --output {args.output}")
    
    elif args.mode == 'validate':
        print(f"🔍 Validating dataset: {args.output}")
        
        if not Path(args.output).exists():
            print(f"❌ File not found: {args.output}")
            return
        
        report = validate_dataset(args.output)
        print_validation_report(report)


if __name__ == "__main__":
    main()
