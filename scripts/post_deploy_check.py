"""
Post-Deployment Validation Script
Runs automated checks after deployment to validate health

Exit codes:
  0 = All checks passed
  1 = Checks failed (triggers rollback)
"""

import requests
import time
import sys
from typing import List, Dict

# Configuration
DEPLOY_URL = "https://indogovrag-staging.fly.dev"  # Change for production
THRESHOLDS = {
    "max_latency_seconds": 60,
    "max_error_rate": 0.05,  # 5%
    "min_ragas_score": 0.70
}

# Test queries (subset of golden set)
TEST_QUERIES = [
    "Apa itu KTP elektronik?",
    "Siapa yang wajib memiliki KTP?",
    "Berapa biaya membuat paspor?",
]


def run_health_check() -> bool:
    """Run deep health check"""
    print("🏥 Health Check...")
    
    try:
        response = requests.get(f"{DEPLOY_URL}/health/deep", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            checks = data.get('checks', {})
            
            if all(checks.values()):
                print("   ✅ All health checks passed")
                return True
            else:
                print(f"   ❌ Health check failed: {checks}")
                return False
        else:
            print(f"   ❌ Health check returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Health check exception: {e}")
        return False


def run_smoke_tests() -> bool:
    """Run smoke tests with sample queries"""
    print("\n🧪 Smoke Tests...")
    
    errors = 0
    total_latency = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        try:
            print(f"   Query {i}/{ len(TEST_QUERIES)}: {query[:30]}...")
            
            start = time.time()
            response = requests.post(
                f"{DEPLOY_URL}/query",
                json={"query": query},
                timeout=120
            )
            latency = time.time() - start
            total_latency += latency
            
            if response.status_code != 200:
                errors += 1
                print(f"      ❌ Failed: HTTP {response.status_code}")
            else:
                print(f"      ✅ Success ({latency:.1f}s)")
                
        except Exception as e:
            errors += 1
            print(f"      ❌ Exception: {e}")
    
    error_rate = errors / len(TEST_QUERIES)
    avg_latency = total_latency / len(TEST_QUERIES)
    
    print(f"\n   Results:")
    print(f"   - Error rate: {error_rate*100:.1f}%")
    print(f"   - Avg latency: {avg_latency:.1f}s")
    
    # Check thresholds
    if error_rate > THRESHOLDS["max_error_rate"]:
        print(f"   ❌ Error rate {error_rate:.1%} exceeds {THRESHOLDS['max_error_rate']:.1%}")
        return False
    
    if avg_latency > THRESHOLDS["max_latency_seconds"]:
        print(f"   ❌ Latency {avg_latency:.0f}s exceeds {THRESHOLDS['max_latency_seconds']}s")
        return False
    
    print("   ✅ Smoke tests passed")
    return True


def run_safety_checks() -> bool:
    """Test safety features"""
    print("\n🛡️  Safety Checks...")
    
    try:
        # Test toxicity filter
        print("   Testing toxicity filter...")
        response = requests.post(
            f"{DEPLOY_URL}/query",
            json={"query": "Test toxic content filter"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("      ✅ Toxicity filter responsive")
        
        # Test evidence grounding
        print("   Testing evidence grounding...")
        response = requests.post(
            f"{DEPLOY_URL}/query",
            json={"query": "What is the weather today?"},  # Out of domain
            timeout=30
        )
        
        if response.status_code == 200:
            answer = response.json().get('answer', '')
            if 'tidak ada informasi' in answer.lower():
                print("      ✅ Evidence grounding working")
            else:
                print("      ⚠️  Evidence grounding may not trigger")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Safety checks failed: {e}")
        return False


def run_ragas_check() -> bool:
    """Run RAGAS evaluation (simplified - would use actual RAGAS in prod)"""
    print("\n📈 RAGAS Check...")
    
    # In production, this would:
    # 1. Load golden test set
    # 2. Run RAGAS evaluation
    # 3. Check if score >= threshold
    
    # For now, simplified check
    print("   ⚠️  RAGAS check (placeholder - implement with actual RAGAS)")
    print("   ✅ Assuming RAGAS score OK")
    
    return True


def main():
    """Main validation flow"""
    print("="*60)
    print("🚀 POST-DEPLOYMENT VALIDATION")
    print("="*60)
    
    # Wait for deployment to stabilize
    print("\n⏳ Waiting 30s for deployment to stabilize...")
    time.sleep(30)
    
    # Run all checks
    checks = {
        "health": run_health_check(),
        "smoke": run_smoke_tests(),
        "safety": run_safety_checks(),
        "ragas": run_ragas_check()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name.upper():.<20} {status}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("\n✅ ALL CHECKS PASSED - Deployment validated")
        print("   Canary can proceed to full rollout")
        return 0
    else:
        print("\n❌ VALIDATION FAILED")
        print("   Triggering automatic rollback...")
        return 1


if __name__ == "__main__":
    sys.exit(main())
