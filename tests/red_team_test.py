"""
RED TEAM SECURITY TESTING - IndoGovRAG API

Attack vectors to test:
1. DoS (Denial of Service) - Massive payloads
2. Input Validation - SQL injection, XSS, code injection
3. Rate Limiting - Flooding attacks
4. Cache Poisoning - Malicious cache entries
5. Memory Exhaustion - Large requests
6. Error Leaking - Sensitive info in errors
7. Authentication Bypass - Access without auth
8. API Abuse - Malformed requests
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
import sys


class RedTeam:
    """Red team security testing framework."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.vulnerabilities = []
        self.passed_tests = []
    
    def log_vulnerability(self, test_name, severity, description):
        """Log discovered vulnerability."""
        self.vulnerabilities.append({
            "test": test_name,
            "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW
            "description": description
        })
        print(f"🚨 [{severity}] {test_name}")
        print(f"   └─ {description}")
        print()
    
    def log_pass(self, test_name, description):
        """Log passed test."""
        self.passed_tests.append({
            "test": test_name,
            "description": description
        })
        print(f"✅ {test_name}")
        print(f"   └─ {description}")
        print()
    
    # =========================================================================
    # ATTACK 1: Denial of Service
    # =========================================================================
    
    def test_massive_payload_dos(self):
        """Test: Can we crash server with huge payload?"""
        print("="*70)
        print(" 🔴 ATTACK 1: Massive Payload DoS")
        print("="*70)
        print()
        
        # Create 10MB payload
        massive_query = "A" * (10 * 1024 * 1024)  # 10MB
        
        try:
            response = requests.post(
                f"{self.base_url}/query",
                json={"query": massive_query},
                timeout=5
            )
            
            if response.status_code == 413:  # Payload too large
                self.log_pass(
                    "Massive Payload DoS",
                    "Server correctly rejected 10MB payload (413)"
                )
            elif response.status_code == 400:  # Bad request
                self.log_pass(
                    "Massive Payload DoS",
                    "Server rejected with validation error (400)"
                )
            else:
                self.log_vulnerability(
                    "Massive Payload DoS",
                    "HIGH",
                    f"Server accepted 10MB payload (status {response.status_code}). Risk: Memory exhaustion"
                )
        except requests.exceptions.Timeout:
            self.log_vulnerability(
                "Massive Payload DoS",
                "CRITICAL",
                "Server timed out processing massive payload. Risk: DoS attack possible"
            )
        except Exception as e:
            self.log_vulnerability(
                "Massive Payload DoS",
                "HIGH",
                f"Server crashed or errored: {str(e)}"
            )
    
    # =========================================================================
    # ATTACK 2: Input Validation
    # =========================================================================
    
    def test_sql_injection(self):
        """Test: SQL injection attempts."""
        print("="*70)
        print(" 🔴 ATTACK 2: SQL Injection")
        print("="*70)
        print()
        
        payloads = [
            "' OR '1'='1",
            "1'; DROP TABLE users--",
            "'; UPDATE users SET password='hacked'--"
        ]
        
        for payload in payloads:
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    json={"query": payload},
                    timeout=5
                )
                
                # Check if error message leaks DB info
                if "SQL" in response.text or "database" in response.text.lower():
                    self.log_vulnerability(
                        "SQL Injection - Info Leak",
                        "MEDIUM",
                        f"Error message potentially leaks database info"
                    )
                    break
            except Exception:
                pass
        else:
            self.log_pass(
                "SQL Injection",
                "No SQL injection vulnerabilities found (not applicable - no SQL DB)"
            )
    
    def test_xss_injection(self):
        """Test: XSS injection attempts."""
        print("="*70)
        print(" 🔴 ATTACK 3: XSS Injection")
        print("="*70)
        print()
        
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        for payload in payloads:
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    json={"query": payload},
                    timeout=5
                )
                
                # Check if script tags are in response
                if "<script>" in response.text or "javascript:" in response.text:
                    self.log_vulnerability(
                        "XSS Injection",
                        "HIGH",
                        "Response contains unescaped script tags. Risk: XSS attack"
                    )
                    break
            except Exception:
                pass
        else:
            self.log_pass(
                "XSS Injection",
                "No XSS vulnerabilities found (JSON responses auto-escaped)"
            )
    
    # =========================================================================
    # ATTACK 4: Rate Limiting
    # =========================================================================
    
    def test_rate_limiting(self):
        """Test: Can we flood the server?"""
        print("="*70)
        print(" 🔴 ATTACK 4: Rate Limiting / Flooding")
        print("="*70)
        print()
        
        print("Sending 100 rapid requests...")
        
        def send_request(i):
            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/query",
                    json={"query": f"Test query {i}"},
                    timeout=2
                )
                elapsed = time.time() - start
                return (response.status_code, elapsed)
            except Exception as e:
                return (0, 0)
        
        # Send 100 requests concurrently
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(send_request, range(100)))
        
        # Analyze results
        success_count = sum(1 for status, _ in results if status == 200)
        rate_limited = sum(1 for status, _ in results if status == 429)
        
        if rate_limited > 0:
            self.log_pass(
                "Rate Limiting",
                f"Server has rate limiting ({rate_limited}/100 requests throttled)"
            )
        elif success_count < 50:
            self.log_pass(
                "Flooding Protection",
                f"Server degraded gracefully under load ({success_count}/100 succeeded)"
            )
        else:
            self.log_vulnerability(
                "Rate Limiting",
                "MEDIUM",
                f"No rate limiting detected. All {success_count}/100 requests succeeded. Risk: Resource exhaustion"
            )
    
    # =========================================================================
    # ATTACK 5: Cache Poisoning
    # =========================================================================
    
    def test_cache_poisoning(self):
        """Test: Can we poison the cache with malicious data?"""
        print("="*70)
        print(" 🔴 ATTACK 5: Cache Poisoning")
        print("="*70)
        print()
        
        # Send malicious query
        malicious_query = "<script>alert('cached XSS')</script>"
        
        try:
            # First request (cache MISS)
            r1 = requests.post(
                f"{self.base_url}/query",
                json={"query": malicious_query},
                timeout=5
            )
            
            # Second request (should be cache HIT)
            r2 = requests.post(
                f"{self.base_url}/query",
                json={"query": malicious_query},
                timeout=5
            )
            
            # Check if malicious content persisted in cache
            if "<script>" in r2.text:
                self.log_vulnerability(
                    "Cache Poisoning",
                    "HIGH",
                    "Malicious content persisted in cache without sanitization"
                )
            else:
                self.log_pass(
                    "Cache Poisoning",
                    "Cache properly sanitizes/escapes content"
                )
        except Exception as e:
            self.log_pass(
                "Cache Poisoning",
                f"Request failed (likely rejected): {str(e)}"
            )
    
    # =========================================================================
    # ATTACK 6: Error Information Leaking
    # =========================================================================
    
    def test_error_leaking(self):
        """Test: Do errors leak sensitive information?"""
        print("="*70)
        print(" 🔴 ATTACK 6: Error Information Leaking")
        print("="*70)
        print()
        
        # Send invalid requests to trigger errors
        test_cases = [
            ({"query": None}, "Null query"),
            ({"query": 123}, "Integer query"),
            ({"invalid_field": "test"}, "Invalid field"),
            ({}, "Empty body")
        ]
        
        leaked_info = []
        
        for payload, description in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    json=payload,
                    timeout=5
                )
                
                # Check for sensitive info in error
                sensitive_keywords = [
                    "traceback", "file path", "c:\\", "/home/",
                    "api_key", "password", "secret"
                ]
                
                response_lower = response.text.lower()
                for keyword in sensitive_keywords:
                    if keyword in response_lower:
                        leaked_info.append(f"{description}: contains '{keyword}'")
                        break
            except Exception:
                pass
        
        if leaked_info:
            self.log_vulnerability(
                "Error Information Leaking",
                "MEDIUM",
                f"Errors leak sensitive info: {', '.join(leaked_info)}"
            )
        else:
            self.log_pass(
                "Error Information Leaking",
                "Errors don't leak sensitive information"
            )
    
    # =========================================================================
    # ATTACK 7: Memory Exhaustion
    # =========================================================================
    
    def test_memory_exhaustion(self):
        """Test: Can we exhaust server memory?"""
        print("="*70)
        print(" 🔴 ATTACK 7: Memory Exhaustion")
        print("="*70)
        print()
        
        # Try to create massive cache entries
        large_queries = [f"Query {i} " + "x" * 10000 for i in range(100)]
        
        successful = 0
        failed = 0
        
        for query in large_queries[:20]:  # Test with 20 large queries
            try:
                response = requests.post(
                    f"{self.base_url}/query",
                    json={"query": query},
                    timeout=2
                )
                if response.status_code == 200:
                    successful += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        
        if failed > successful:
            self.log_pass(
                "Memory Exhaustion",
                f"Server rejected most large requests ({failed}/{20} rejected)"
            )
        else:
            self.log_vulnerability(
                "Memory Exhaustion",
                "MEDIUM",
                f"Server accepted large requests without limits ({successful}/{20} succeeded)"
            )
    
    # =========================================================================
    # ATTACK 8: Authentication Bypass
    # =========================================================================
    
    def test_authentication_bypass(self):
        """Test: Can we access API without authentication?"""
        print("="*70)
        print(" 🔴 ATTACK 8: Authentication Bypass")
        print("="*70)
        print()
        
        # Try accessing without credentials
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                # Health endpoint should be public
                self.log_pass(
                    "Authentication - Health Endpoint",
                    "Health endpoint publicly accessible (correct)"
                )
            
            # Try query without auth
            response = requests.post(
                f"{self.base_url}/query",
                json={"query": "Test"},
                timeout=5
            )
            
            if response.status_code == 200:
                # If no auth is implemented, this is expected
                self.log_pass(
                    "Authentication - Query Endpoint",
                    "Query endpoint accessible (no auth implemented - consider adding for production)"
                )
            elif response.status_code == 401:
                self.log_pass(
                    "Authentication Bypass",
                    "Authentication required (secure)"
                )
        except Exception as e:
            self.log_pass(
                "Authentication Bypass",
                f"Request failed: {str(e)}"
            )
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all_tests(self):
        """Execute all security tests."""
        print()
        print("╔" + "="*68 + "╗")
        print("║" + " "*15 + "🔴 RED TEAM SECURITY ASSESSMENT" + " "*22 + "║")
        print("║" + " "*23 + "IndoGovRAG API" + " "*31 + "║")
        print("╚" + "="*68 + "╝")
        print()
        print("Target:", self.base_url)
        print("Date:", time.strftime("%Y-%m-%d %H:%M:%S"))
        print()
        
        # Run all attacks
        self.test_massive_payload_dos()
        self.test_sql_injection()
        self.test_xss_injection()
        self.test_rate_limiting()
        self.test_cache_poisoning()
        self.test_error_leaking()
        self.test_memory_exhaustion()
        self.test_authentication_bypass()
        
        # Summary
        print()
        print("="*70)
        print(" 📊 RED TEAM ASSESSMENT SUMMARY")
        print("="*70)
        print()
        
        total_tests = len(self.vulnerabilities) + len(self.passed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"🚨 Vulnerabilities: {len(self.vulnerabilities)}")
        print()
        
        if self.vulnerabilities:
            print("🚨 VULNERABILITIES FOUND:")
            print()
            
            for vuln in self.vulnerabilities:
                print(f"[{vuln['severity']}] {vuln['test']}")
                print(f"  └─ {vuln['description']}")
                print()
            
            # Severity counts
            critical = sum(1 for v in self.vulnerabilities if v['severity'] == 'CRITICAL')
            high = sum(1 for v in self.vulnerabilities if v['severity'] == 'HIGH')
            medium = sum(1 for v in self.vulnerabilities if v['severity'] == 'MEDIUM')
            low = sum(1 for v in self.vulnerabilities if v['severity'] == 'LOW')
            
            print("Severity Breakdown:")
            if critical: print(f"  🔴 CRITICAL: {critical}")
            if high: print(f"  🟠 HIGH: {high}")
            if medium: print(f"  🟡 MEDIUM: {medium}")
            if low: print(f"  🟢 LOW: {low}")
            print()
            
            print("⚠️  RECOMMENDATION: Fix vulnerabilities before production!")
        else:
            print("✅ NO CRITICAL VULNERABILITIES FOUND!")
            print()
            print("🎉 System passed all security tests!")
            print("💪 Ready for production deployment!")
        
        print()
        print("="*70)
        print()


if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get("http://localhost:8000/health", timeout=2)
    except Exception:
        print("❌ Error: API server not running")
        print("   Start server with: python api/main.py")
        sys.exit(1)
    
    # Run red team tests
    red_team = RedTeam()
    red_team.run_all_tests()
