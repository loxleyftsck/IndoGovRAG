
import requests
import json
import time
import sys
from typing import Dict, List

# Configuration
API_URL = "http://localhost:8000/query"
PASS_THRESHOLD = 80.0

# Test Questions mapped to expected citations/keywords
TEST_CASES = [
    {
        "category": "Basic Requirement",
        "query": "Apa syarat pembuatan paspor baru?",
        "expected_keywords": ["KTP", "KK", "Akta"],
        "expected_citation_indicators": ["Pasal", "Peraturan", "Nomor", "UU"]
    },
    {
        "category": "Legal Hierarchy",
        "query": "Apakah ada sanksi jika tidak membayar BPJS?",
        "expected_keywords": ["sanksi", "denda", "pelayanan publik"],
        "expected_citation_indicators": ["UU", "Perpres", "Instruksi Presiden"]
    },
    {
        "category": "Out of Context",
        "query": "Siapa pemenang Piala Dunia 2022?",
        "expected_keywords": ["Maaf", "tidak ditemukan", "dokumen"],
        "expected_citation_indicators": [] # Should not cite laws for football
    }
]

def check_professional_format(answer: str) -> dict:
    """Check if answer follows the strict IndoGov AI format."""
    score = 0
    checks = {
        "structured_format": False,
        "citation_presence": False,
        "formal_tone": False
    }
    
    # 1. Check Structure (Ringkasan, Penjelasan, Referensi)
    # We look for structured markers like distinct paragraphs or bullet points
    if "\n" in answer and ("-" in answer or "1." in answer):
        checks["structured_format"] = True
        score += 40
        
    # 2. Check Citation Presence
    citations = ["UU", "Undang-Undang", "Peraturan", "Pasal", "Ayat", "No.", "Tahun"]
    if any(c in answer for c in citations):
        checks["citation_presence"] = True
        score += 40
    elif "Maaf" in answer: # Exception for out of context
        checks["citation_presence"] = True
        score += 40
        
    # 3. Check Formal Tone (No informal words)
    informal_words = ["aku", "kamu", "nggak", "gimana", "kok"]
    if not any(w in answer.lower() for w in informal_words):
        checks["formal_tone"] = True
        score += 20
        
    return {"score": score, "details": checks}

def run_assessment():
    print("🤖 INDOGOV AI - AUTOMATED PROJECT EVALUATOR")
    print("===========================================")
    print(f"Target: {API_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-------------------------------------------\n")

    total_score = 0
    max_score = len(TEST_CASES) * 100
    results = []

    for test in TEST_CASES:
        print(f"📋 Testing: {test['category']}")
        print(f"   Query: {test['query']}")
        
        start_time = time.time()
        try:
            response = requests.post(API_URL, json={"query": test['query']})
            response.raise_for_status()
            data = response.json()
            latency = (time.time() - start_time) * 1000
            
            answer = data.get('answer', '')
            sources = data.get('sources', [])
            confidence = data.get('confidence', 0.0)
            
            # Evaluate
            eval_result = check_professional_format(answer)
            format_score = eval_result['score']
            
            # Keywords check
            keyword_match = any(k.lower() in answer.lower() for k in test['expected_keywords'])
            if keyword_match:
                format_score = min(100, format_score + 10) # Bonus for accuracy
            
            print(f"   ✅ Latency: {latency:.2f}ms")
            print(f"   ✅ Confidence: {confidence:.2f}")
            print(f"   ✅ Format Score: {eval_result['score']}/100")
            print(f"   📝 Answer snippet: {answer[:100]}...")
            print("-------------------------------------------")
            
            total_score += format_score
            results.append({
                "query": test['query'],
                "score": format_score,
                "latency": latency,
                "passed": format_score >= 80
            })

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({"query": test['query'], "score": 0, "passed": False}) 
            
    # Final Report
    avg_score = total_score / len(TEST_CASES)
    grade = "A" if avg_score >= 90 else "B" if avg_score >= 80 else "C"
    
    print("\n📊 FINAL ASSESSMENT REPORT")
    print("==========================")
    print(f"Average Quality Score: {avg_score:.1f}/100")
    print(f"Project Grade: {grade}")
    print(f"System Status: {'✅ PASSED' if avg_score >= PASS_THRESHOLD else '❌ FAILED'}")
    
    if avg_score >= PASS_THRESHOLD:
        print("\n🏆 CERTIFIED: READY FOR PRODUCTION")
        sys.exit(0)
    else:
        print("\n⚠️ IMPROVEMENTS REQUIRED")
        sys.exit(1)

if __name__ == "__main__":
    # Wait for API to warm up
    print("Waiting 5s for API to settle...")
    time.sleep(5)
    run_assessment()
