#!/usr/bin/env python3
"""
Phase 7 (Tier 1) Load Test for IndoGovRAG
Tests concurrent request handling and system stability
"""

import concurrent.futures
import time
import requests
import json
from datetime import datetime
import argparse
import sys

API_ENDPOINT = "http://localhost:8000/query"  # Fixed: was /api/query
HEALTH_ENDPOINT = "http://localhost:8000/health"
TIMEOUT = 30

def send_query(query_text, run_id):
    """Send single query, return latency + status"""
    start = time.time()
    try:
        response = requests.post(
            API_ENDPOINT,
            json={"query": query_text, "options": {}},  # Fixed: added options
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        latency = time.time() - start
        status = "OK" if response.status_code == 200 else f"ERROR_{response.status_code}"
        
        return {
            "run_id": run_id,
            "latency": latency,
            "status": status,
            "status_code": response.status_code
        }
    except requests.exceptions.Timeout:
        return {
            "run_id": run_id,
            "latency": TIMEOUT,
            "status": "TIMEOUT",
            "status_code": 0
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "run_id": run_id,
            "latency": time.time() - start,
            "status": f"CONNECTION_ERROR",
            "status_code": 0,
            "error": str(e)[:100]
        }
    except Exception as e:
        return {
            "run_id": run_id,
            "latency": time.time() - start,
            "status": f"ERROR",
            "status_code": 0,
            "error": str(e)[:100]
        }

def run_load_test(n_queries=50, n_concurrent=5):
    """Run load test with concurrent queries"""
    
    test_queries = [
        "Apa itu KTP elektronik?",
        "Bagaimana cara mengurus paspor?",
        "Syarat dan ketentuan layanan e-KTP",
        "Berapa lama waktu proses administrasi?",
        "Apa perbedaan KTP dan KTP-el?",
        "Dokumen apa saja untuk pembuatan KK?",
        "Prosedur perpanjangan paspor",
        "Biaya pembuatan akta kelahiran"
    ]
    
    print(f"\n{'='*70}")
    print(f"PHASE 7 (TIER 1) LOAD TEST")
    print(f"{'='*70}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Total Queries: {n_queries}")
    print(f"Concurrent Workers: {n_concurrent}")
    print(f"API Endpoint: {API_ENDPOINT}")
    print(f"{'='*70}\n")
    
    results = []
    start_time = time.time()
    
    # Check API reachable first
    try:
        test_response = requests.get(
            HEALTH_ENDPOINT,  # Fixed: use constant
            timeout=5
        )
        print(f"✅ API Health Check: {test_response.status_code}")
    except Exception as e:
        print(f"❌ API Health Check Failed: {e}")
        print(f"   Make sure API is running: python api/main.py\n")
        return False
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_concurrent) as executor:
        futures = []
        for i in range(n_queries):
            query = test_queries[i % len(test_queries)]
            future = executor.submit(send_query, query, i)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if len(results) % 10 == 0:
                print(f"Progress: {len(results)}/{n_queries} queries completed")
    
    total_time = time.time() - start_time
    
    # Analyze results
    latencies = [r["latency"] for r in results]
    ok_count = sum(1 for r in results if r["status"] == "OK")
    error_count = len(results) - ok_count
    connection_errors = sum(1 for r in results if "CONNECTION" in r["status"])
    timeouts = sum(1 for r in results if r["status"] == "TIMEOUT")
    
    if not latencies:
        print("\n❌ No results collected. Test failed.\n")
        return False
    
    sorted_lat = sorted(latencies)
    p50 = sorted_lat[len(sorted_lat) // 2]
    p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
    p99 = sorted_lat[min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)]
    
    print(f"\n{'='*70}")
    print(f"RESULTS")
    print(f"{'='*70}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Success Rate: {ok_count}/{len(results)} ({100*ok_count/len(results):.1f}%)")
    print(f"Errors: {error_count}")
    if connection_errors > 0:
        print(f"  - Connection Errors: {connection_errors}")
    if timeouts > 0:
        print(f"  - Timeouts: {timeouts}")
    print(f"\nLatency Statistics:")
    print(f"  Avg: {sum(latencies)/len(latencies):.2f}s")
    print(f"  Min: {min(latencies):.2f}s")
    print(f"  Max: {max(latencies):.2f}s")
    print(f"  P50: {p50:.2f}s")
    print(f"  P95: {p95:.2f}s")
    print(f"  P99: {p99:.2f}s")
    print(f"{'='*70}\n")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "n_queries": n_queries,
            "n_concurrent": n_concurrent,
            "api_endpoint": API_ENDPOINT
        },
        "results": {
            "total_time_seconds": round(total_time, 2),
            "success_rate": f"{100*ok_count/len(results):.1f}%",
            "ok_count": ok_count,
            "error_count": error_count,
            "connection_errors": connection_errors,
            "timeouts": timeouts,
            "latency": {
                "avg": f"{sum(latencies)/len(latencies):.2f}s",
                "min": f"{min(latencies):.2f}s",
                "max": f"{max(latencies):.2f}s",
                "p50": f"{p50:.2f}s",
                "p95": f"{p95:.2f}s",
                "p99": f"{p99:.2f}s"
            }
        },
        "pass_criteria": {
            "success_rate_target": "≥95%",
            "success_rate_actual": f"{100*ok_count/len(results):.1f}%",
            "pass": ok_count >= len(results) * 0.95
        }
    }
    
    report_file = f"reports/load_test_phase7_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📁 Report saved: {report_file}\n")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}\n")
    
    # Pass/Fail decision
    success = ok_count >= len(results) * 0.95
    if success:
        print("✅ LOAD TEST PASSED (Success rate ≥95%)")
    else:
        print(f"❌ LOAD TEST FAILED (Success rate {100*ok_count/len(results):.1f}% < 95%)")
    
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IndoGovRAG Load Test")
    parser.add_argument("--queries", type=int, default=50, help="Total queries to send")
    parser.add_argument("--concurrent", type=int, default=5, help="Concurrent workers")
    args = parser.parse_args()
    
    success = run_load_test(n_queries=args.queries, n_concurrent=args.concurrent)
    sys.exit(0 if success else 1)
