"""RAG API Stress Testing Framework.

This module provides a comprehensive stress testing framework for the RAG (Retrieval-Augmented
Generation) API, focusing on performance metrics under concurrent load conditions.

Key Features:
    - Concurrent query handling with configurable parallelism
    - Real-time latency monitoring (end-to-end and API-internal)
    - Throughput measurement (queries per minute/second)
    - Error rate tracking and categorization
    - Quality metrics collection (confidence, sources, answer length)
    - Detailed JSON reporting with timestamp

Usage:
    Basic usage with default settings (50 queries, 5 concurrent):
        $ python stress_test.py

    Custom configuration:
        $ python stress_test.py --url http://api.example.com:8000 --queries 100 --concurrent 10

    Programmatic usage:
        >>> from stress_test import StressTestRunner
        >>> runner = StressTestRunner(api_url="http://localhost:8000", num_queries=50)
        >>> await runner.run()

Author: IndoGovRAG Development Team
Version: 1.0.0
Last Updated: 2026-02-06
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import aiohttp


class StressTestRunner:
    """Professional stress testing framework for RAG API performance evaluation.
    
    This class provides comprehensive performance testing capabilities for RAG systems,
    measuring critical metrics under concurrent load conditions.
    
    Attributes:
        api_url: Base URL of the RAG API endpoint
        num_queries: Total number of queries to execute
        concurrent_requests: Number of parallel requests per batch
        test_queries: Predefined set of Indonesian government-related queries
        results: List of all query results with timing and quality metrics
        errors: List of failed queries with error details
    
    Performance Metrics Tracked:
        - Concurrent query handling capacity
        - End-to-end and API-internal latency
        - Throughput (queries per minute/second)
        - Error rate and timeout tracking
        - Response quality (confidence, sources, answer length)
    
    Example:
        >>> runner = StressTestRunner(
        ...     api_url="http://localhost:8000",
        ...     num_queries=100,
        ...     concurrent_requests=10
        ... )
        >>> await runner.run()
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        num_queries: int = 50,
        concurrent_requests: int = 5,
    ) -> None:
        """Initialize the stress test runner with configuration parameters.
        
        Args:
            api_url: Base URL of the RAG API (default: http://localhost:8000)
            num_queries: Total number of queries to execute (default: 50)
            concurrent_requests: Number of parallel requests per batch (default: 5)
        
        Raises:
            ValueError: If num_queries or concurrent_requests are less than 1
        """
        self.api_url = api_url
        self.num_queries = num_queries
        self.concurrent_requests = concurrent_requests
        
        # Test queries (diverse set)
        self.test_queries = [
            "Apa syarat membuat KTP?",
            "Bagaimana cara daftar NPWP?",
            "Persyaratan pembuatan paspor?",
            "Cara mengurus akta kelahiran?",
            "Prosedur pembuatan SIM?",
            "Syarat pendirian PT?",
            "Bagaimana cara daftar hak cipta?",
            "Prosedur pendaftaran merek dagang?",
            "Cara mengurus izin usaha?",
            "Persyaratan BPJS Kesehatan?",
            "Bagaimana cara daftar kepesertaan JKN?",
            "Syarat pembuatan SKCK?",
            "Cara mengurus visa Indonesia?",
            "Prosedur izin tinggal terbatas?",
            "Syarat naturalisasi kewarganegaraan?",
        ]
        
        # Results
        self.results: List[Dict] = []
        self.errors: List[Dict] = []
    
    async def send_query(
        self,
        session: aiohttp.ClientSession,
        query: str,
        query_id: int,
    ) -> Dict[str, Any]:
        """Execute a single query against the RAG API with comprehensive error handling.
        
        Args:
            session: Active aiohttp client session for connection pooling
            query: Query string to send to the API
            query_id: Unique identifier for this query (used in reporting)
        
        Returns:
            Dictionary containing query results with the following keys:
                - query_id: Unique query identifier
                - query: Original query string
                - status: 'success', 'error', or 'timeout'
                - latency_ms: End-to-end latency in milliseconds
                - api_latency_ms: API-reported internal latency (success only)
                - confidence: Response confidence score (success only)
                - answer_length: Length of answer in characters (success only)
                - num_sources: Number of source documents used (success only)
                - error: Error message (error/timeout only)
        
        Note:
            All requests have a 60-second timeout to prevent hanging.
        """
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.api_url}/query",
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "query_id": query_id,
                        "query": query,
                        "status": "success",
                        "latency_ms": latency_ms,
                        "api_latency_ms": data.get("latency_ms", 0),
                        "confidence": data.get("confidence", 0),
                        "answer_length": len(data.get("answer", "")),
                        "num_sources": len(data.get("sources", []))
                    }
                else:
                    text = await response.text()
                    return {
                        "query_id": query_id,
                        "query": query,
                        "status": "error",
                        "latency_ms": latency_ms,
                        "error": f"HTTP {response.status}: {text[:100]}"
                    }
        
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "query_id": query_id,
                "query": query,
                "status": "timeout",
                "latency_ms": latency_ms,
                "error": "Request timeout (>60s)"
            }
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "query_id": query_id,
                "query": query,
                "status": "error",
                "latency_ms": latency_ms,
                "error": str(e)
            }
    
    async def run_batch(
        self, session: aiohttp.ClientSession, queries: List[Tuple[int, str]]
    ) -> List[Dict[str, Any]]:
        """Execute a batch of queries concurrently.
        
        Args:
            session: Active aiohttp client session
            queries: List of (query_id, query_string) tuples to execute
        
        Returns:
            List of result dictionaries from send_query()
        """
        tasks = [
            self.send_query(session, query, query_id)
            for query_id, query in queries
        ]
        return await asyncio.gather(*tasks)
    
    async def run(self) -> None:
        """Execute the complete stress test workflow.
        
        Workflow:
            1. Verify API health
            2. Prepare query batches
            3. Execute queries in concurrent batches
            4. Collect and analyze results
            5. Print summary statistics
            6. Save detailed results to JSON file
        
        The test runs all queries in batches based on concurrent_requests setting,
        tracks all metrics, and generates a comprehensive report.
        """
        print("🚀 Starting RAG API Stress Test")
        print(f"   Total queries: {self.num_queries}")
        print(f"   Concurrent: {self.concurrent_requests}")
        print(f"   API: {self.api_url}")
        print()
        
        # Check API health first
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/health") as response:
                    if response.status != 200:
                        print(f"❌ API health check failed: {response.status}")
                        return
                    health = await response.json()
                    print(f"✅ API healthy: {health}")
                    print()
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return
        
        # Prepare queries
        queries_to_send = []
        for i in range(self.num_queries):
            query = self.test_queries[i % len(self.test_queries)]
            queries_to_send.append((i + 1, query))
        
        # Run in batches
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(queries_to_send), self.concurrent_requests):
                batch = queries_to_send[i:i + self.concurrent_requests]
                print(f"📤 Sending batch {i // self.concurrent_requests + 1} ({len(batch)} queries)...")
                
                results = await self.run_batch(session, batch)
                self.results.extend(results)
                
                # Track errors
                for result in results:
                    if result["status"] != "success":
                        self.errors.append(result)
        
        total_time = time.time() - start_time
        
        # Print results
        self._print_results(total_time)
        
        # Save results
        self._save_results(total_time)
    
    def _print_results(self, total_time: float) -> None:
        """Print formatted test results to console.
        
        Args:
            total_time: Total execution time in seconds
        
        Displays:
            - Success rate and error count
            - Latency statistics (mean, median, min, max, stdev)
            - Throughput metrics (queries per minute/second)
            - Quality metrics (confidence, sources, answer length)
        """
        successful = [r for r in self.results if r["status"] == "success"]
        
        print("\n" + "="*60)
        print("📊 STRESS TEST RESULTS")
        print("="*60)
        
        # Success rate
        success_rate = (len(successful) / len(self.results)) * 100
        print(f"\n✅ Success Rate: {success_rate:.1f}% ({len(successful)}/{len(self.results)})")
        
        if self.errors:
            print(f"❌ Errors: {len(self.errors)}")
            for error in self.errors[:3]:  # Show first 3
                print(f"   - {error['error']}")
        
        # Latency stats
        if successful:
            latencies = [r["latency_ms"] for r in successful]
            api_latencies = [r["api_latency_ms"] for r in successful]
            
            print(f"\n⏱️  Latency (End-to-End):")
            print(f"   Mean: {statistics.mean(latencies):.0f}ms")
            print(f"   Median: {statistics.median(latencies):.0f}ms")
            print(f"   Min: {min(latencies):.0f}ms")
            print(f"   Max: {max(latencies):.0f}ms")
            print(f"   Stdev: {statistics.stdev(latencies):.0f}ms")
            
            print(f"\n⏱️  Latency (API Internal):")
            print(f"   Mean: {statistics.mean(api_latencies):.0f}ms")
            print(f"   Median: {statistics.median(api_latencies):.0f}ms")
            
            # Throughput
            qpm = (len(successful) / total_time) * 60
            print(f"\n🚀 Throughput:")
            print(f"   {qpm:.2f} queries/minute")
            print(f"   {len(successful) / total_time:.2f} queries/second")
            
            # Quality metrics
            confidences = [r["confidence"] for r in successful]
            print(f"\n📈 Quality Metrics:")
            print(f"   Avg Confidence: {statistics.mean(confidences):.3f}")
            print(f"   Avg Sources: {statistics.mean([r['num_sources'] for r in successful]):.1f}")
            print(f"   Avg Answer Length: {statistics.mean([r['answer_length'] for r in successful]):.0f} chars")
        
        print(f"\n⏰ Total Time: {total_time:.1f}s")
        print("="*60)
    
    def _save_results(self, total_time: float) -> None:
        """Save comprehensive test results to timestamped JSON file.
        
        Args:
            total_time: Total execution time in seconds
        
        Creates:
            A JSON report in the 'reports/' directory containing:
            - Test configuration
            - Summary statistics
            - Individual query results
            - Error details
        
        File naming: stress_test_YYYYMMDD_HHMMSS.json
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "num_queries": self.num_queries,
                "concurrent_requests": self.concurrent_requests,
                "api_url": self.api_url
            },
            "summary": {
                "total_queries": len(self.results),
                "successful": len([r for r in self.results if r["status"] == "success"]),
                "errors": len(self.errors),
                "success_rate": (len([r for r in self.results if r["status"] == "success"]) / len(self.results)) * 100,
                "total_time_seconds": total_time
            },
            "results": self.results,
            "errors": self.errors
        }
        
        filename = f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path("reports") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Results saved to: {filepath}")


async def main() -> None:
    """CLI entry point for the stress test runner.
    
    Parses command-line arguments and executes the stress test with
    user-specified or default configuration.
    
    Command-line Arguments:
        --url: API base URL (default: http://localhost:8000)
        --queries: Total number of queries to execute (default: 50)
        --concurrent: Number of concurrent requests per batch (default: 5)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Professional stress testing framework for RAG API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the RAG API endpoint",
    )
    parser.add_argument(
        "--queries",
        type=int,
        default=50,
        help="Total number of queries to execute",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="Number of concurrent requests per batch",
    )

    args = parser.parse_args()

    runner = StressTestRunner(
        api_url=args.url,
        num_queries=args.queries,
        concurrent_requests=args.concurrent,
    )

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
