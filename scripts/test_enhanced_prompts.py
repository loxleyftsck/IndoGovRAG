"""
Test Enhanced Prompts - Immediate Validation

Quick test to validate Tier 1 prompt improvements
"""

import sys
sys.path.insert(0, '.')

from src.rag.ollama_pipeline import OllamaRAGPipeline
import time

def test_answer_quality():
    """Test improved answer quality with enhanced prompts"""
    
    print("\n" + "="*60)
    print("TESTING ENHANCED PROMPTS (Tier 1)")
    print("="*60 + "\n")
    
    # Initialize pipeline (will use new prompts)
    pipeline = OllamaRAGPipeline()
    
    test_cases = [
        {
            "query": "Apa syarat membuat KTP elektronik?",
            "expected_keywords": ["17 tahun", "Kartu Keluarga", "formulir"],
            "expected_citation": ["Pasal", "UU"]
        },
        {
            "query": "Bagaimana cara mengurus akta kelahiran?",
            "expected_keywords": ["60 hari", "surat keterangan", "dokter"],
            "expected_citation": ["Pasal", "UU"]
        }
    ]
    
    total_score = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}")
        print(f"Query: {test['query']}")
        print("-" * 60)
        
        start = time.time()
        result = pipeline.query(test['query'])
        elapsed = time.time() - start
        
        answer = result['answer']
        
        # Check keywords
        found_keywords = sum(1 for kw in test['expected_keywords'] 
                           if kw.lower() in answer.lower())
        keyword_score = found_keywords / len(test['expected_keywords'])
        
        # Check citations
        has_citation = any(cit in answer for cit in test['expected_citation'])
        citation_score = 1.0 if has_citation else 0.0
        
        # Overall score
        test_score = (keyword_score * 0.7) + (citation_score * 0.3)
        total_score += test_score
        
        # Display
        print(f"\nAnswer Preview:")
        print(answer[:300] + "..." if len(answer) > 300 else answer)
        print(f"\nMetrics:")
        print(f"  Keywords: {found_keywords}/{len(test['expected_keywords'])} ({keyword_score*100:.0f}%)")
        print(f"  Citation: {'✓' if has_citation else '✗'}")
        print(f"  Test Score: {test_score*100:.0f}%")
        print(f"  Response Time: {elapsed:.1f}s")
        print("\n" + "="*60)
    
    # Final score
    avg_score = (total_score / len(test_cases)) * 100
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Average Quality Score: {avg_score:.1f}%")
    
    if avg_score >= 80:
        print("✅ EXCELLENT - Enhanced prompts working well!")
    elif avg_score >= 60:
        print("⚠️  GOOD - Some improvement, may need more tuning")
    else:
        print("❌ NEEDS IMPROVEMENT - Consider Tier 2 optimizations")
    
    print(f"{'='*60}\n")
    
    return avg_score

if __name__ == "__main__":
    score = test_answer_quality()
    
    print("\nNext Steps:")
    if score >= 80:
        print("  ✅ Tier 1 successful! Consider Tier 2 (document audit)")
    else:
        print("  ⚠️  May need to check document corpus quality")
        print("  ⚠️  Consider adding few-shot examples to prompts")
