"""
Indonesian Embedding Model Benchmarking
Compare different embedding models for Indonesian text retrieval

Models tested:
1. multilingual-e5-base (baseline)
2. IndoBERT (Indonesian-specific)
3. LaBSE (Language-agnostic BERT)

Criteria:
- Retrieval quality (semantic similarity)
- Speed (encoding time)
- Model size (memory usage)
"""

import time
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import torch


@dataclass
class BenchmarkResult:
    """Results for a single model benchmark."""
    model_name: str
    avg_encoding_time: float
    embedding_dim: int
    model_size_mb: float
    similarity_scores: Dict[str, float]
    memory_footprint_mb: float


class IndonesianEmbeddingBenchmark:
    """Benchmark embedding models for Indonesian text."""
    
    # Test queries (Indonesian government doc scenarios)
    TEST_QUERIES = [
        "Bagaimana cara mengurus KTP elektronik?",
        "Persyaratan membuat paspor baru",
        "Prosedur pendaftaran CPNS 2024",
        "Syarat mendapatkan bantuan sosial",
        "Cara mengajukan izin usaha online",
    ]
    
    # Sample documents (simulated Indonesian gov doc chunks)
    SAMPLE_DOCS = [
        "KTP elektronik dapat diurus dengan membawa Kartu Keluarga asli, akta kelahiran, dan pas foto 3x4. Datang ke Disdukcapil terdekat untuk perekaman biometrik.",
        "Paspor baru memerlukan dokumen: KTP elektronik, Kartu Keluarga, akta lahir, dan foto 4x6 latar belakang putih. Proses pembuatan memakan waktu 3-5 hari kerja.",
        "Pendaftaran CPNS dilakukan melalui portal SSCASN dengan menggunakan NIK dan email aktif. Pelamar harus melengkapi data pribadi dan mengunggah ijazah.",
        "Bantuan sosial diberikan kepada keluarga miskin yang terdaftar di DTKS dengan kriteria penghasilan di bawah upah minimum regional.",
        "Izin usaha dapat diajukan melalui sistem OSS (Online Single Submission) dengan mendaftar NIB terlebih dahulu. Proses dilakukan secara elektronik tanpa datang ke kantor.",
        "SIM dapat diperpanjang 30 hari sebelum masa berlaku habis dengan membawa SIM lama dan KTP. Proses perpanjangan memerlukan tes kesehatan sederhana.",
        "Akta kelahiran harus dilaporkan maksimal 60 hari setelah kelahiran anak. Dokumen yang diperlukan: surat keterangan lahir dari bidan/dokter dan KK orang tua.",
        "NPWP dapat dibuat secara online melalui ereg.pajak.go.id dengan mengunggah foto KTP dan selfie. Kartu NPWP dikirim ke alamat dalam waktu 14 hari.",
    ]
    
    def __init__(self):
        """Initialize benchmark."""
        self.models = {}
        self.results = {}
    
    def load_model(self, model_name: str, hf_model_id: str) -> bool:
        """
        Load an embedding model.
        
        Args:
            model_name: Display name for the model
            hf_model_id: HuggingFace model ID
        
        Returns:
            True if loaded successfully
        """
        try:
            print(f"Loading {model_name} ({hf_model_id})...", end=" ")
            start = time.time()
            
            model = SentenceTransformer(hf_model_id)
            
            load_time = time.time() - start
            print(f"✅ ({load_time:.2f}s)")
            
            self.models[model_name] = {
                "model": model,
                "hf_id": hf_model_id
            }
            return True
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            return False
    
    def get_model_size(self, model: SentenceTransformer) -> float:
        """
        Estimate model size in MB.
        
        Args:
            model: SentenceTransformer model
        
        Returns:
            Size in MB
        """
        param_size = sum(p.nelement() * p.element_size() for p in model.parameters())
        buffer_size = sum(b.nelement() * b.element_size() for b in model.buffers())
        size_mb = (param_size + buffer_size) / (1024 ** 2)
        return size_mb
    
    def benchmark_model(self, model_name: str) -> BenchmarkResult:
        """
        Benchmark a single model.
        
        Args:
            model_name: Name of the loaded model
        
        Returns:
            BenchmarkResult with all metrics
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded")
        
        model_info = self.models[model_name]
        model = model_info["model"]
        
        print(f"\n{'='*70}")
        print(f"Benchmarking: {model_name}")
        print(f"{'='*70}")
        
        # 1. Model size
        model_size = self.get_model_size(model)
        print(f"Model size: {model_size:.2f} MB")
        
        # 2. Embedding dimension
        test_embedding = model.encode(["test"])[0]
        embedding_dim = len(test_embedding)
        print(f"Embedding dimension: {embedding_dim}")
        
        # 3. Encoding speed
        print(f"\nTesting encoding speed...")
        encoding_times = []
        
        for query in self.TEST_QUERIES:
            start = time.time()
            _ = model.encode([query])
            encoding_times.append(time.time() - start)
        
        avg_encoding_time = np.mean(encoding_times) * 1000  # Convert to ms
        print(f"Avg encoding time: {avg_encoding_time:.2f} ms")
        
        # 4. Retrieval quality (semantic similarity)
        print(f"\nTesting retrieval quality...")
        query_embeddings = model.encode(self.TEST_QUERIES)
        doc_embeddings = model.encode(self.SAMPLE_DOCS)
        
        # Calculate cosine similarity
        query_embeddings_norm = query_embeddings / np.linalg.norm(query_embeddings, axis=1, keepdims=True)
        doc_embeddings_norm = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        
        similarity_matrix = np.dot(query_embeddings_norm, doc_embeddings_norm.T)
        
        # Expected matches (manually defined)
        expected_matches = {
            0: 0,  # KTP query → KTP doc
            1: 1,  # Paspor query → Paspor doc
            2: 2,  # CPNS query → CPNS doc
            3: 3,  # Bantuan sosial query → Bantuan doc
            4: 4,  # Izin usaha query → OSS doc
        }
        
        similarity_scores = {}
        
        for query_idx, expected_doc_idx in expected_matches.items():
            query_text = self.TEST_QUERIES[query_idx]
            doc_text = self.SAMPLE_DOCS[expected_doc_idx]
            
            # Get similarity to expected doc
            expected_sim = similarity_matrix[query_idx, expected_doc_idx]
            
            # Get rank of expected doc
            ranks = np.argsort(similarity_matrix[query_idx])[::-1]
            expected_rank = np.where(ranks == expected_doc_idx)[0][0] + 1
            
            similarity_scores[f"Q{query_idx+1}"] = {
                "similarity": float(expected_sim),
                "rank": int(expected_rank),
                "query_preview": query_text[:40] + "...",
            }
            
            print(f"  Q{query_idx+1}: sim={expected_sim:.3f}, rank={expected_rank}/8")
        
        # Calculate Hit@1 and MRR
        ranks = [scores["rank"] for scores in similarity_scores.values()]
        hit_at_1 = sum(1 for r in ranks if r == 1) / len(ranks)
        mrr = np.mean([1.0 / r for r in ranks])
        
        print(f"\nRetrieval Metrics:")
        print(f"  Hit@1: {hit_at_1:.2%} ({sum(1 for r in ranks if r == 1)}/{len(ranks)} correct)")
        print(f"  MRR: {mrr:.3f}")
        
        # 5. Memory footprint during inference
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            _ = model.encode(self.SAMPLE_DOCS)
            memory_mb = torch.cuda.max_memory_allocated() / (1024 ** 2)
        else:
            memory_mb = model_size  # Approximate with model size
        
        return BenchmarkResult(
            model_name=model_name,
            avg_encoding_time=avg_encoding_time,
            embedding_dim=embedding_dim,
            model_size_mb=model_size,
            similarity_scores={
                "hit_at_1": hit_at_1,
                "mrr": mrr,
                "avg_similarity": np.mean([s["similarity"] for s in similarity_scores.values()]),
            },
            memory_footprint_mb=memory_mb,
        )
    
    def run_benchmark(self, models_to_test: List[Tuple[str, str]]) -> Dict[str, BenchmarkResult]:
        """
        Run benchmark on multiple models.
        
        Args:
            models_to_test: List of (model_name, hf_model_id) tuples
        
        Returns:
            Dict of model_name -> BenchmarkResult
        """
        results = {}
        
        for model_name, hf_model_id in models_to_test:
            if self.load_model(model_name, hf_model_id):
                try:
                    result = self.benchmark_model(model_name)
                    results[model_name] = result
                    self.results[model_name] = result
                except Exception as e:
                    print(f"❌ Benchmark failed for {model_name}: {e}")
        
        return results
    
    def print_comparison(self):
        """Print comparison table of all benchmarked models."""
        if not self.results:
            print("No benchmark results available")
            return
        
        print("\n" + "="*90)
        print("📊 EMBEDDING MODEL COMPARISON")
        print("="*90)
        
        # Header
        print(f"\n{'Model':<25} {'Dim':<8} {'Size(MB)':<12} {'Speed(ms)':<12} {'Hit@1':<10} {'MRR':<10}")
        print("-" * 90)
        
        # Sort by Hit@1 (best first)
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1].similarity_scores["hit_at_1"],
            reverse=True
        )
        
        for model_name, result in sorted_results:
            print(f"{model_name:<25} "
                  f"{result.embedding_dim:<8} "
                  f"{result.model_size_mb:<12.2f} "
                  f"{result.avg_encoding_time:<12.2f} "
                  f"{result.similarity_scores['hit_at_1']:<10.2%} "
                  f"{result.similarity_scores['mrr']:<10.3f}")
        
        print("-" * 90)
        
        # Recommendation
        best_model = sorted_results[0][0]
        best_result = sorted_results[0][1]
        
        print(f"\n🏆 RECOMMENDATION: {best_model}")
        print(f"   Reasons:")
        print(f"   - Hit@1: {best_result.similarity_scores['hit_at_1']:.2%}")
        print(f"   - MRR: {best_result.similarity_scores['mrr']:.3f}")
        print(f"   - Speed: {best_result.avg_encoding_time:.2f} ms/query")
        print(f"   - Size: {best_result.model_size_mb:.2f} MB")
        
        print("\n" + "="*90)
    
    def export_results(self, filepath: str = "data/embedding_benchmark_results.json"):
        """Export benchmark results to JSON."""
        import json
        from pathlib import Path
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            "benchmark_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_queries": self.TEST_QUERIES,
            "num_test_docs": len(self.SAMPLE_DOCS),
            "results": {}
        }
        
        for model_name, result in self.results.items():
            export_data["results"][model_name] = {
                "hf_model_id": self.models[model_name]["hf_id"],
                "embedding_dim": result.embedding_dim,
                "model_size_mb": result.model_size_mb,
                "avg_encoding_time_ms": result.avg_encoding_time,
                "hit_at_1": result.similarity_scores["hit_at_1"],
                "mrr": result.similarity_scores["mrr"],
                "avg_similarity": result.similarity_scores["avg_similarity"],
                "memory_footprint_mb": result.memory_footprint_mb,
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results exported to: {filepath}")


def main():
    """Run the benchmark."""
    print("\n" + "🚀" * 35)
    print("  INDONESIAN EMBEDDING MODEL BENCHMARK")
    print("  Comparing models for Indonesian gov doc retrieval")
    print("🚀" * 35)
    
    benchmark = IndonesianEmbeddingBenchmark()
    
    # Models to test
    models_to_test = [
        ("multilingual-e5-base", "intfloat/multilingual-e5-base"),
        ("LaBSE", "sentence-transformers/LaBSE"),
        # IndoBERT requires different handling, skipping for now
        # ("IndoBERT", "indobenchmark/indobert-base-p1"),
    ]
    
    print(f"\n📋 Will benchmark {len(models_to_test)} models:")
    for name, hf_id in models_to_test:
        print(f"   - {name} ({hf_id})")
    
    print(f"\n📊 Test configuration:")
    print(f"   Test queries: {len(benchmark.TEST_QUERIES)}")
    print(f"   Sample docs: {len(benchmark.SAMPLE_DOCS)}")
    
    input("\nPress Enter to start benchmark...")
    
    # Run benchmark
    results = benchmark.run_benchmark(models_to_test)
    
    # Print comparison
    if results:
        benchmark.print_comparison()
        benchmark.export_results()
    else:
        print("\n❌ No models were successfully benchmarked")
    
    print("\n" + "="*90)
    print("✅ Benchmark complete!")
    print("="*90 + "\n")


if __name__ == "__main__":
    main()
