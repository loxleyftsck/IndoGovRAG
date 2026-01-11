"""
P0 Pre-Flight Validation
Quick check to ensure all P0 components are ready for execution
"""

import os
import sys
from pathlib import Path
import subprocess
import json


def check_file_exists(path: str, description: str) -> bool:
    """Check if file exists"""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists


def check_prometheus_running() -> bool:
    """Check if Prometheus is accessible"""
    try:
        import requests
        response = requests.get("http://localhost:9090/-/healthy", timeout=2)
        running = response.status_code == 200
        status = "✅" if running else "⚠️"
        print(f"{status} Prometheus running: http://localhost:9090")
        return running
    except:
        print("⚠️  Prometheus not accessible (may not be running)")
        return False


def check_production_logs() -> bool:
    """Check if production logs exist"""
    log_dir = Path("logs")
    if not log_dir.exists():
        print(f"❌ Logs directory missing: logs/")
        return False
    
    log_files = list(log_dir.glob("ollama_queries_*.jsonl"))
    if log_files:
        print(f"✅ Production logs found: {len(log_files)} files")
        
        # Count queries
        total_queries = 0
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    total_queries += sum(1 for line in f if line.strip())
            except:
                pass
        
        print(f"   Total queries logged: {total_queries}")
        return True
    else:
        print("⚠️  No production logs found (run some queries first)")
        return False


def check_ollama_running() -> bool:
    """Check if Ollama is running with llama3.1:8b"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "llama3.1:8b" in result.stdout:
            print("✅ Ollama running with llama3.1:8b")
            return True
        else:
            print("⚠️  Ollama running but llama3.1:8b not found")
            print("   Run: ollama pull llama3.1:8b")
            return False
    except:
        print("❌ Ollama not accessible")
        print("   Ensure Ollama is installed and running")
        return False


def main():
    print("\n" + "="*60)
    print("🔍 P0 WEEK 1 PRE-FLIGHT VALIDATION")
    print("="*60 + "\n")
    
    checks = []
    
    # 1. Core files
    print("📁 CHECKING FILES...")
    checks.append(check_file_exists("prometheus/alerts/quality_drift.yml", "Drift alerts"))
    checks.append(check_file_exists("scripts/extract_review_samples.py", "Sample extractor"))
    checks.append(check_file_exists("scripts/analyze_review_baseline.py", "Baseline analyzer"))
    checks.append(check_file_exists("grafana/dashboards/cache_performance.json", "Cache dashboard"))
    checks.append(check_file_exists("grafana/dashboards/latency_breakdown.json", "Latency dashboard"))
    
    print("\n🔧 CHECKING SERVICES...")
    checks.append(check_ollama_running())
    checks.append(check_prometheus_running())
    
    print("\n📊 CHECKING DATA...")
    checks.append(check_production_logs())
    
    # Summary
    print("\n" + "="*60)
    passed = sum(checks)
    total = len(checks)
    
    print(f"RESULTS: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED - READY FOR P0 EXECUTION!")
        print("\nNext step:")
        print("   Follow: docs/P0_WEEK1_EXECUTION.md")
    elif passed >= total * 0.7:
        print("\n⚠️  MOSTLY READY - Some warnings")
        print("\nYou can proceed, but:")
        print("   - Review warnings above")
        print("   - Fix critical issues (❌)")
        print("   - Optional checks (⚠️) are nice-to-have")
    else:
        print("\n❌ NOT READY - Fix issues before proceeding")
        print("\nRequired:")
        print("   1. Fix all ❌ errors")
        print("   2. Rerun this script")
        print("   3. Then follow P0_WEEK1_EXECUTION.md")
    
    print("="*60 + "\n")
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
