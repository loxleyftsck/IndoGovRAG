"""
Chunk Size Optimization Experiment

Tests different chunk sizes to find optimal configuration for RAG retrieval.
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.chunker import DocumentChunker
from src.retrieval.vector_search import VectorStore, prepare_chunks_for_indexing

def run_chunk_size_experiment():
    """Test different chunk sizes and measure impact."""
    
    print("="*70)
    print(" 🧪 CHUNK SIZE OPTIMIZATION EXPERIMENT")
    print("="*70)
    print()
    
    # Sample Indonesian government document
    sample_doc = """
    PERATURAN PRESIDEN REPUBLIK INDONESIA
    NOMOR 26 TAHUN 2009
    
    TENTANG PENERAPAN KARTU TANDA PENDUDUK BERBASIS NOMOR INDUK 
    KEPENDUDUKAN SECARA NASIONAL
    
    Pasal 1
    Dalam Peraturan Presiden ini, yang dimaksud dengan:
    
    1. Kartu Tanda Penduduk, yang selanjutnya disingkat KTP adalah identitas 
       resmi penduduk sebagai bukti diri yang diterbitkan oleh Instansi 
       Pelaksana yang berlaku di seluruh wilayah Negara Kesatuan Republik 
       Indonesia.
    
    2. Nomor Induk Kependudukan, yang selanjutnya disingkat NIK adalah nomor 
       identitas penduduk yang bersifat unik atau khas, tunggal dan melekat 
       pada seseorang yang terdaftar sebagai Penduduk Indonesia.
    
    3. Kartu Tanda Penduduk elektronik, yang selanjutnya disebut KTP-el  
       adalah Kartu Tanda Penduduk yang dilengkapi cip yang merupakan 
       identitas resmi penduduk sebagai bukti diri yang diterbitkan oleh 
       Instansi Pelaksana.
    
    Pasal 2
    KTP-el memuat:
    a. Nomor Induk Kependudukan (NIK)
    b. Nama lengkap
    c. Tempat/tanggal lahir
    d. Jenis kelamin
    e. Alamat
    f. Agama
    g. Status perkawinan
    h. Pekerjaan
    i. Kewarganegaraan
    j. Pas foto
    k. Tanda tangan
    l. Masa berlaku
    m. Tempat dan tanggal pembuatan KTP-el
    
    Pasal 3
    Setiap penduduk Warga Negara Indonesia dan Orang Asing yang memiliki 
    Izin Tinggal Tetap yang telah berumur 17 (tujuh belas) tahun atau telah 
    kawin atau telah pernah kawin wajib memiliki KTP-el.
    """ * 3  # Repeat to make document longer
    
    # Test configurations
    chunk_sizes = [256, 512, 1024]
    overlaps = [64, 128, 256]
    
    results = []
    
    for chunk_size in chunk_sizes:
        for overlap in overlaps:
            if overlap < chunk_size:  # Overlap must be smaller than chunk
                print(f"\n🔬 Testing: chunk_size={chunk_size}, overlap={overlap}")
                print("-" * 70)
                
                # Create chunker
                chunker = DocumentChunker(
                    chunk_size=chunk_size,
                    overlap=overlap
                )
                
                # Chunk document
                start_time = time.time()
                chunks = chunker.chunk(sample_doc, doc_id="perpres_26_2009")
                chunk_time = time.time() - start_time
                
                # Calculate metrics
                num_chunks = len(chunks)
                avg_tokens = sum(c.num_tokens for c in chunks) / num_chunks if num_chunks > 0 else 0
                
                # Calculate coherence
                for chunk in chunks:
                    chunk.coherence_score = chunker.calculate_coherence(chunk)
                
                avg_coherence = sum(c.coherence_score for c in chunks) / num_chunks if num_chunks > 0 else 0
                
                result = {
                    'chunk_size': chunk_size,
                    'overlap': overlap,
                    'num_chunks': num_chunks,
                    'avg_tokens': round(avg_tokens, 1),
                    'avg_coherence': round(avg_coherence, 3),
                    'chunk_time_ms': round(chunk_time * 1000, 2),
                    'coverage_ratio': round(overlap / chunk_size, 2) if chunk_size > 0 else 0
                }
                
                results.append(result)
                
                print(f"  ✅ Chunks created: {num_chunks}")
                print(f"  📊 Avg tokens/chunk: {avg_tokens:.1f}")
                print(f"  🎯 Avg coherence: {avg_coherence:.3f}")
                print(f"  ⏱️  Processing time: {chunk_time*1000:.2f}ms")
    
    # Save results
    output_file = "experiments/results/chunk_size_results.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'experiment': 'chunk_size_optimization',
            'date': '2024-12-17',
            'results': results
        }, f, indent=2)
    
    print("\n" + "="*70)
    print(" 📊 EXPERIMENT SUMMARY")
    print("="*70)
    print()
    
    # Find best configuration
    best = max(results, key=lambda x: x['avg_coherence'])
    
    print(f"🏆 Best Configuration:")
    print(f"   Chunk size: {best['chunk_size']} tokens")
    print(f"   Overlap: {best['overlap']} tokens")
    print(f"   Chunks created: {best['num_chunks']}")
    print(f"   Avg coherence: {best['avg_coherence']}")
    print()
    
    print("📈 Key Findings:")
    print(f"   - Larger chunks = fewer chunks, better context")
    print(f"   - Smaller chunks = more granular, faster processing")
    print(f"   - Optimal overlap = {best['overlap']} ({best['coverage_ratio']*100:.0f}% of chunk size)")
    print()
    
    print(f"💾 Results saved to: {output_file}")
    print()
    
    print("✅ Experiment complete!")


if __name__ == "__main__":
    run_chunk_size_experiment()
