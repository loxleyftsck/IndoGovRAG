"""
Complete Week 1 Verification Script
Tests: Tracing + Metrics + Dashboard + Alerts
"""

import requests
import time
import sys
import json

def verify_week1_complete():
    """Verify all Week 1 observability features"""
    
    print("🔍 WEEK 1 COMPLETE VERIFICATION\n")
    print("="*60)
    
    scores = {
        "tracing": 0,
        "metrics": 0,
        "dashboard": 0,
        "alerts": 0
    }
    
    # === TRACING (30 points) ===
    print("\n📡 TRACING VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Request ID
        r = requests.post("http://localhost:8000/query", json={"query": "Test"}, timeout=30)
        if "X-Request-ID" in r.headers:
            print("✅ Request IDs present")
            scores["tracing"] += 10
        
        # 2. Jaeger running
        r = requests.get("http://localhost:16686", timeout=5)
        if r.status_code == 200:
            print("✅ Jaeger UI accessible")
            scores["tracing"] += 10
        
        # 3. Traces in Jaeger
        time.sleep(3)
        r = requests.get("http://localhost:16686/api/services")
        if 'indogovrag' in r.json().get('data', []):
            print("✅ Traces exported to Jaeger")
            scores["tracing"] += 10
    except Exception as e:
        print(f"❌ Tracing check failed: {e}")
    
    # === METRICS (30 points) ===
    print("\n📊 METRICS VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Metrics endpoint
        r = requests.get("http://localhost:8000/metrics", timeout=5)
        metrics_text = r.text
        
        required_metrics = [
            "indogovrag_queries_total",
            "indogovrag_query_latency_seconds",
            "indogovrag_query_cost_usd",
            "indogovrag_ragas_faithfulness"
        ]
        
        found_metrics = sum(1 for m in required_metrics if m in metrics_text)
        scores["metrics"] += int((found_metrics / len(required_metrics)) * 30)
        print(f"✅ Found {found_metrics}/{len(required_metrics)} required metrics")
        
    except Exception as e:
        print(f"❌ Metrics check failed: {e}")
    
    # === DASHBOARD (20 points) ===
    print("\n📈 DASHBOARD VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Prometheus running
        r = requests.get("http://localhost:9090/-/healthy", timeout=5)
        if r.status_code == 200:
            print("✅ Prometheus running")
            scores["dashboard"] += 5
        
        # 2. Prometheus scraping
        r = requests.get("http://localhost:9090/api/v1/targets")
        targets = r.json()['data']['activeTargets']
        if any(t['health'] == 'up' for t in targets):
            print("✅ Prometheus scraping targets")
            scores["dashboard"] += 5
        
        # 3. Grafana running
        r = requests.get("http://localhost:3001/api/health", timeout=5)
        if r.status_code == 200:
            print("✅ Grafana accessible")
            scores["dashboard"] += 5
        
        # 4. Datasource configured
        r = requests.get(
            "http://localhost:3001/api/datasources",
            auth=('admin', 'admin')
        )
        if len(r.json()) > 0:
            print("✅ Grafana datasource configured")
            scores["dashboard"] += 5
            
    except Exception as e:
        print(f"❌ Dashboard check failed: {e}")
    
    # === ALERTS (20 points) ===
    print("\n🚨 ALERTS VERIFICATION")
    print("-"*60)
    
    try:
        # 1. Alert rules loaded
        r = requests.get("http://localhost:9090/api/v1/rules")
        rules = r.json()['data']['groups']
        
        if len(rules) > 0:
            total_rules = sum(len(g['rules']) for g in rules)
            print(f"✅ {total_rules} alert rules loaded")
            scores["alerts"] += 10
            
            # Check for our rules
            rule_names = [r['name'] for g in rules for r in g['rules']]
            required_rules = ['HighLatencyP95', 'HighErrorRate', 'LowFaithfulness']
            found = sum(1 for r in required_rules if r in rule_names)
            if found >= 2:
                print(f"✅ Found {found}/{len(required_rules)} custom rules")
                scores["alerts"] += 10
    except Exception as e:
        print(f"❌ Alerts check failed: {e}")
    
    # === FINAL SCORE ===
    total_score = sum(scores.values())
    max_score = 100
    
    print("\n" + "="*60)
    print("📊 WEEK 1 FINAL SCORE")
    print("="*60)
    print(f"")
    print(f"Tracing:   {scores['tracing']}/30")
    print(f"Metrics:   {scores['metrics']}/30")
    print(f"Dashboard: {scores['dashboard']}/20")
    print(f"Alerts:    {scores['alerts']}/20")
    print(f"")
    print(f"TOTAL:     {total_score}/100 ({total_score}%)")
    print("="*60)
    
    if total_score >= 80:
        print("\n✅ WEEK 1 COMPLETE - Ready for Week 2!")
        print("\nNext steps:")
        print("  1. Review dashboards at http://localhost:3001")
        print("  2. Check alerts in Prometheus: http://localhost:9090/alerts")
        print("  3. Run observability score evaluation")
        print("  4. Proceed to Week 2 (Safety + Deployment)")
        return 0
    elif total_score >= 60:
        print("\n⚠️  WEEK 1 PARTIALLY COMPLETE")
        print("Fix remaining issues before Week 2")
        return 1
    else:
        print("\n❌ WEEK 1 INCOMPLETE")
        print("Review failed checks and retry")
        return 1

if __name__ == "__main__":
    sys.exit(verify_week1_complete())
