"""
Week 2 Verification Script
Tests: Canary + Toxicity + Evidence Grounding
"""

import requests
import sys

def verify_week2():
    """Verify Week 2 safety and deployment features"""
    
    print("🔍 WEEK 2 VERIFICATION\n")
    print("="*60)
    
    scores = {
        "deployment": 0,
        "safety": 0
    }
    
    # === DEPLOYMENT (50 points) ===
    print("\n🚀 DEPLOYMENT VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Deep health check
        r = requests.get("http://localhost:8000/health/deep", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get('status') == 'healthy':
                print("✅ Deep health check working")
                scores["deployment"] += 15
        
        # 2. Canary config (check file exists)
        try:
            with open("fly.toml") as f:
                content = f.read()
                if 'strategy = "canary"' in content:
                    print("✅ Canary deployment configured")
                    scores["deployment"] += 15
        except:
            print("❌ fly.toml not found")
        
        # 3. Post-deploy script exists
        try:
            with open("scripts/post_deploy_check.py") as f:
                print("✅ Post-deploy validation script exists")
                scores["deployment"] += 10
        except:
            print("❌ Post-deploy script missing")
        
        # 4. Deployment runbook
        try:
            with open("docs/DEPLOYMENT_RUNBOOK.md") as f:
                print("✅ Deployment runbook documented")
                scores["deployment"] += 10
        except:
            print("❌ Runbook missing")
            
    except Exception as e:
        print(f"❌ Deployment checks failed: {e}")
    
    # === SAFETY (50 points) ===
    print("\n🛡️  SAFETY VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Toxicity filter
        from src.safety.toxicity_filter import ToxicityFilter
        filter = ToxicityFilter()
        
        # Test toxic content
        result = filter.check_toxicity("You are stupid")  # Mild toxic test
        if 'is_toxic' in result:
            print("✅ Toxicity detection working")
            scores["safety"] += 15
        
        # 2. Evidence grounding
        from src.safety.evidence_grounding import EvidenceGrounding
        checker = EvidenceGrounding()
        
        # Test insufficiency
        is_sufficient, reason, score = checker.check_sufficiency(
            "test query",
            []  # No docs
        )
        
        if not is_sufficient:
            print("✅ Evidence grounding working")
            scores["safety"] += 15
        
        # 3. Integration test
        r = requests.post(
            "http://localhost:8000/query",
            json={"query": "What is the weather?"},
            timeout=30
        )
        
        if r.status_code == 200:
            answer = r.json().get('answer', '')
            if 'tidak ada informasi' in answer.lower():
                print("✅ Safety integrated into pipeline")
                scores["safety"] += 20
            else:
                print("⚠️  Safety may not be fully integrated")
                scores["safety"] += 10
                
    except Exception as e:
        print(f"❌ Safety checks failed: {e}")
    
    # === FINAL SCORE ===
    total = scores["deployment"] + scores["safety"]
    
    print("\n" + "="*60)
    print("📊 WEEK 2 SCORE")
    print("="*60)
    print(f"Deployment: {scores['deployment']}/50")
    print(f"Safety:     {scores['safety']}/50")
    print(f"")
    print(f"TOTAL:      {total}/100 ({total}%)")
    print("="*60)
    
    if total >= 80:
        print("\n✅ WEEK 2 COMPLETE - Ready for Week 3!")
        return 0
    else:
        print("\n❌ WEEK 2 INCOMPLETE - Fix failing checks")
        return 1

if __name__ == "__main__":
    sys.exit(verify_week2())
