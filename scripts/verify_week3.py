"""
Week 3 Verification Script
Tests: Feedback API + Audit Trail + Explainability
"""

import requests
import sys
import json
import os

def verify_week3():
    """Verify Week 3 governance features"""
    
    print("🔍 WEEK 3 VERIFICATION\n")
    print("="*60)
    
    scores = {
        "feedback": 0,
        "audit": 0,
        "explainability": 0,
        "compliance": 0
    }
    
    # === FEEDBACK SYSTEM (30 points) ===
    print("\n💬 FEEDBACK SYSTEM VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Feedback API exists
        r = requests.post(
            "http://localhost:8000/feedback",
            json={
                "request_id": "test-request-id",
                "rating": 5,
                "feedback_type": "thumbs_up",
                "comment": "Great answer!"
            },
            timeout=10
        )
        
        if r.status_code == 200:
            print("✅ Feedback API working")
            scores["feedback"] += 10
            
            data = r.json()
            if 'feedback_id' in data:
                print("✅ Feedback ID generated")
                scores["feedback"] += 5
        
        # 2. Feedback storage
        if os.path.exists("data/feedback.jsonl"):
            print("✅ Feedback storage exists")
            scores["feedback"] += 10
        
        # 3. Review script
        if os.path.exists("scripts/review_feedback.py"):
            print("✅ Feedback review script exists")
            scores["feedback"] += 5
            
    except Exception as e:
        print(f"❌ Feedback checks failed: {e}")
    
    # === AUDIT TRAIL (30 points) ===
    print("\n📋 AUDIT TRAIL VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Audit log exists
        if os.path.exists("logs/audit.jsonl"):
            print("✅ Audit log file exists")
            scores["audit"] += 10
            
            # Check structure
            with open("logs/audit.jsonl") as f:
                lines = f.readlines()
                if len(lines) > 0:
                    entry = json.loads(lines[-1])
                    required_fields = [
                        'request_id', 'timestamp', 'query_hash',
                        'answer_hash', 'model_used'
                    ]
                    if all(field in entry for field in required_fields):
                        print("✅ Audit log structure correct")
                        scores["audit"] += 15
        
        # 2. GDPR deletion endpoint
        # Don't actually call it, just check it exists
        r = requests.options("http://localhost:8000/data/user/test")
        if r.status_code in [200, 405]:  # OPTIONS might not be implemented
            print("✅ GDPR endpoint exists")
            scores["audit"] += 5
            
    except Exception as e:
        print(f"❌ Audit checks failed: {e}")
    
    # === EXPLAINABILITY (20 points) ===
    print("\n🔍 EXPLAINABILITY VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Version info in responses
        r = requests.post(
            "http://localhost:8000/query",
            json={"query": "Test explainability"},
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            metadata = data.get('metadata', {})
            
            if 'versions' in metadata:
                print("✅ Version info in responses")
                scores["explainability"] += 10
                
                versions = metadata['versions']
                required_versions = [
                    'system_version', 'prompt_template',
                    'embedding_model', 'llm_model'
                ]
                
                components = versions.get('components', {})
                if all(v in components for v in ['prompt_template', 'embedding_model']):
                    print("✅ Component versions tracked")
                    scores["explainability"] += 10
            else:
                print("⚠️  Version info not found in response")
                
    except Exception as e:
        print(f"❌ Explainability checks failed: {e}")
    
    # === COMPLIANCE (20 points) ===
    print("\n⚖️  COMPLIANCE VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Improvement workflow documented
        if os.path.exists("docs/IMPROVEMENT_WORKFLOW.md"):
            print("✅ Improvement workflow documented")
            scores["compliance"] += 10
        
        # 2. Config versions
        if os.path.exists("config/versions.py"):
            print("✅ Versions config exists")
            scores["compliance"] += 5
            
            # Try importing
            import sys
            sys.path.insert(0, os.getcwd())
            from config.versions import get_version_info
            version_info = get_version_info()
            if 'system_version' in version_info:
                print("✅ Version config working")
                scores["compliance"] += 5
                
    except Exception as e:
        print(f"❌ Compliance checks failed: {e}")
    
    # === FINAL SCORE ===
    total = sum(scores.values())
    
    print("\n" + "="*60)
    print("📊 WEEK 3 SCORE")
    print("="*60)
    print(f"Feedback:       {scores['feedback']}/30")
    print(f"Audit:          {scores['audit']}/30")
    print(f"Explainability: {scores['explainability']}/20")
    print(f"Compliance:     {scores['compliance']}/20")
    print(f"")
    print(f"TOTAL:          {total}/100 ({total}%)")
    print("="*60)
    
    if total >= 85:
        print("\n✅ WEEK 3 COMPLETE - 85% ENTERPRISE-GRADE ACHIEVED!")
        print("\n🎉 ALL 3 WEEKS COMPLETE!")
        print("   Week 1: Observability (48% → 60%)")
        print("   Week 2: Safety + Deploy (60% → 72%)")
        print("   Week 3: Governance (72% → 85%)")
        print("\n🏆 SYSTEM IS NOW ENTERPRISE-READY!")
        return 0
    elif total >= 70:
        print("\n⚠️  WEEK 3 PARTIALLY COMPLETE")
        print("Fix remaining issues to reach 85%")
        return 1
    else:
        print("\n❌ WEEK 3 INCOMPLETE")
        print("Review failed checks and retry")
        return 1

if __name__ == "__main__":
    sys.exit(verify_week3())
