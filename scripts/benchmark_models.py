"""
Model Comparison Benchmark Script

Compares different Ollama models for Indonesian RAG:
- Llama 3.1 8B Q4_K_M (current)
- Qwen 2.5 7B (challenger)
- Sahabat-AI (Indonesian specialist)

Metrics:
- Latency (P50, P95, P99)
- Quality (faithfulness, relevancy)
- RAM usage
- Token count
"""

import time
import psutil
import os
from typing import Dict, List
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.ollama_pipeline import OllamaRAGPipeline

# Test queries (Indonesian government documents)
TEST_QUERIES = [
    "Apa syarat membuat KTP elektronik?",
    "Bagaimana cara mengurus akta kelahiran?",
    "Apa fungsi Kartu Keluarga?",
    "Berapa lama masa berlaku KTP?",
    "Dokumen apa saja yang diperlukan untuk membuat paspor?",
    "Apa perbedaan KTP biasa dan KTP elektronik?",
    "Bagaimana prosedur pembuatan NPWP?",
    "Apa itu NIK dan fungsinya?",
    "Berapa biaya pembuatan KTP?",
    "Dimana bisa mengurus surat pindah domisili?",
]

def benchmark_model(model_name: str, queries: List[str]) -> Dict:
    """Benchmark a single model"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing Model: {model_name}")
    print(f"{'='*60}\n")
    
    # Initialize pipeline
    pipeline = OllamaRAGPipeline(ollama_model=model_name)
    
    results = {
        "model": model_name,
        "latencies": [],
        "ram_usage_mb": [],
        "total_tokens": 0,
        "errors": 0,
        "success_count": 0,
    }
    
    process = psutil.Process(os.getpid())
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] Query: {query[:50]}...")
        
        try:
            # Measure RAM before
            ram_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Execute query
            start_time = time.time()
            result = pipeline.query(
                question=query,
                filter_metadata=None,
                include_sources=True
            )
            latency = (time.time() - start_time) * 1000  # ms
            
            # Measure RAM after
            ram_after = process.memory_info().rss / 1024 / 1024  # MB
            ram_delta = ram_after - ram_before
            
           # Store metrics
            results["latencies"].append(latency)
            results["ram_usage_mb"].append(ram_delta)
            results["success_count"] += 1
            
            print(f"  ✅ Latency: {latency:.0f}ms | RAM: +{ram_delta:.1f}MB")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results["errors"] += 1
    
    # Calculate statistics
    if results["latencies"]:
        results["latency_p50"] = sorted(results["latencies"])[len(results["latencies"]) // 2]
        results["latency_p95"] = sorted(results["latencies"])[int(len(results["latencies"]) * 0.95)]
        results["latency_mean"] = sum(results["latencies"]) / len(results["latencies"])
        results["ram_mean"] = sum(results["ram_usage_mb"]) / len(results["ram_usage_mb"])
    
    return results


def print_comparison(all_results: List[Dict]):
    """Print comparison table"""
    print(f"\n{'='*80}")
    print("📊 COMPARISON RESULTS")
    print(f"{'='*80}\n")
    
    print(f"{'Model':<35} {'P50 (ms)':<12} {'P95 (ms)':<12} {'Mean (ms)':<12} {'RAM (MB)':<12} {'Success'}")
    print(f"{'-'*80}")
    
    for r in all_results:
        if r["latencies"]:
            print(f"{r['model']:<35} "
                  f"{r['latency_p50']:<12.0f} "
                  f"{r['latency_p95']:<12.0f} "
                  f"{r['latency_mean']:<12.0f} "
                  f"{r['ram_mean']:<12.1f} "
                  f"{r['success_count']}/{len(TEST_QUERIES)}")
        else:
            print(f"{r['model']:<35} NO DATA (all failed)")
    
    print(f"\n{'='*80}\n")
    
    # Recommendation
    if len(all_results) > 1 and all_results[0].get('latencies'):
        fastest = min(all_results, key=lambda x: x.get("latency_mean", float('inf')))
        print(f"⚡ Fastest Model: {fastest['model']}")
        print(f"   Average: {fastest.get('latency_mean', 0):.0f}ms")
        print(f"   P95: {fastest.get('latency_p95', 0):.0f}ms\n")


def main():
    """Run benchmark"""
    print("""
    🔬 IndoGovRAG Model Comparison Benchmark
    
    This script will test multiple models and compare:
    - Latency (response time)
    - RAM usage
    - Success rate
    
    Models to test:
    1. llama3.1:8b-instruct-q4_K_M (current)
    2. qwen2.5:7b (if available)
    
    Note: Make sure models are pulled first with `ollama pull <model>`
    """)
    
    models = [
        "llama3.1:8b-instruct-q4_K_M",  # Current
    ]
    
    # Check if Qwen available
    import subprocess
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "qwen2.5" in result.stdout:
            models.append("qwen2.5:7b")
            print("✅ Qwen 2.5 detected, will include in comparison\n")
        else:
            print("⚠️ Qwen 2.5 not found, run: ollama pull qwen2.5:7b\n")
    except:
        pass
    
    # Run benchmarks
    all_results = []
    for model in models:
        try:
            results = benchmark_model(model, TEST_QUERIES)
            all_results.append(results)
        except Exception as e:
            print(f"❌ Failed to benchmark {model}: {e}")
    
    # Print comparison
    if all_results:
        print_comparison(all_results)
        
        # Save results
        output_file = Path(__file__).parent.parent / "reports" / "model_comparison.txt"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, "w") as f:
            f.write("IndoGovRAG Model Comparison Results\n")
            f.write("=" * 80 + "\n\n")
            for r in all_results:
                f.write(f"Model: {r['model']}\n")
                f.write(f"  Latency P50: {r.get('latency_p50', 0):.0f}ms\n")
                f.write(f"  Latency P95: {r.get('latency_p95', 0):.0f}ms\n")
                f.write(f"  Latency Mean: {r.get('latency_mean', 0):.0f}ms\n")
                f.write(f"  RAM Mean: {r.get('ram_mean', 0):.1f}MB\n")
                f.write(f"  Success: {r['success_count']}/{len(TEST_QUERIES)}\n\n")
        
        print(f"💾 Results saved to: {output_file}")
    else:
        print("❌ No results to compare!")


if __name__ == "__main__":
    main()
