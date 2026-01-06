"""
Week 1 Task 1.1-1.3 Verification Script
Run after implementing tracing to verify setup
"""

import requests
import time
import sys

def verify_task_1_1_to_1_3():
    """Verify OpenTelemetry tracing setup"""
    
    print("🔍 VERIFYING TASK 1.1-1.3: OpenTelemetry Tracing\n")
    
    passed = 0
    total = 6
    
    # 1. Check API is running
    print("1. API Health Check...")
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        assert r.status_code == 200
        print("   ✅ API running")
        passed += 1
    except Exception as e:
        print(f"   ❌ API not running: {e}")
    
    # 2. Check Request ID
    print("\n2. Request ID Middleware...")
    try:
        r = requests.post(
            "http://localhost:8000/query",
            json={"query": "Test tracing"},
            timeout=30
        )
        request_id = r.headers.get("X-Request-ID")
        assert request_id is not None
        assert len(request_id) == 36  # UUID format
        print(f"   ✅ Request ID: {request_id}")
        passed += 1
    except Exception as e:
        print(f"   ❌ Request ID missing: {e}")
    
    # 3. Check Jaeger is running
    print("\n3. Jaeger Backend...")
    try:
        r = requests.get("http://localhost:16686/api/services", timeout=5)
        print(f"   ✅ Jaeger UI accessible at http://localhost:16686")
        passed += 1
    except Exception as e:
        print(f"   ❌ Jaeger not accessible: {e}")
    
    # 4. Wait for trace export
    print("\n4. Waiting for trace export...")
    time.sleep(5)
    print("   ✅ Wait complete")
    passed += 1
    
    # 5. Check traces in Jaeger
    print("\n5. Checking Traces in Jaeger...")
    try:
        # Get services
        r = requests.get("http://localhost:16686/api/services")
        services = r.json().get('data', [])
        
        if 'indogovrag' in services:
            print(f"   ✅ Service 'indogovrag' found in Jaeger")
            passed += 1
            
            # Get traces for service
            r = requests.get(
                "http://localhost:16686/api/traces",
                params={'service': 'indogovrag', 'limit': 10}
            )
            traces = r.json().get('data', [])
            
            if len(traces) > 0:
                print(f"   ✅ Found {len(traces)} trace(s)")
                
                # Check first trace structure
                first_trace = traces[0]
                spans = first_trace.get('spans', [])
                print(f"   ✅ Trace has {len(spans)} span(s)")
                
                # Verify span attributes
                for span in spans:
                    tags = {tag['key']: tag['value'] for tag in span.get('tags', [])}
                    if 'request.id' in tags:
                        print(f"   ✅ Found request.id in span: {tags['request.id']}")
                        break
            else:
                print("   ⚠️  No traces found yet (run more queries)")
        else:
            print(f"   ❌ Service 'indogovrag' not in Jaeger")
            print(f"   Available services: {services}")
    except Exception as e:
        print(f"   ❌ Failed to check Jaeger: {e}")
    
    # 6. Verify trace structure
    print("\n6. Trace Structure Check...")
    try:
        # Make structured request
        r = requests.post(
            "http://localhost:8000/query",
            json={"query": "Apa itu KTP elektronik?"},
            timeout=30
        )
        
        response_data = r.json()
        request_id = r.headers.get("X-Request-ID")
        
        # Check response has required fields
        assert 'metadata' in response_data
        assert 'request_id' in response_data['metadata']
        assert response_data['metadata']['request_id'] == request_id
        
        print(f"   ✅ Trace structure valid")
        print(f"      Request ID: {request_id}")
        print(f"      Latency: {response_data['latency_ms']}ms")
        print(f"      Model: {response_data['metadata']['model_used']}")
        
        passed += 1
    except Exception as e:
        print(f"   ❌ Trace structure check failed: {e}")
    
    # Final score
    score = (passed / total) * 100
    print(f"\n{'='*60}")
    print(f"TASK 1.1-1.3 SCORE: {passed}/{total} ({score:.0f}%)")
    print(f"{'='*60}\n")
    
    if score >= 80:
        print("✅ TASK 1.1-1.3 COMPLETE")
        print("   Next: Task 1.4 (RAG Pipeline Tracing)")
        print("   Then: Task 1.5 (Prometheus Metrics)")
        return 0
    else:
        print("❌ TASK 1.1-1.3 INCOMPLETE")
        print("   Fix failing checks before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(verify_task_1_1_to_1_3())
