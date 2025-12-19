"""
Quick Document Loader - Bypass TensorFlow Issue

Loads sample Indonesian government documents directly to vector store.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.vector_search import VectorStore, prepare_chunks_for_indexing
from src.data.chunker import Chunk

def load_sample_documents():
    """Load Indonesian government document samples."""
    
    print("🔧 Loading Sample Indonesian Government Documents...")
    print()
    
    # Sample documents about Indonesian government topics
    documents = [
        {
            'doc_id': 'ktp_elektronik_001',
            'title': 'KTP Elektronik', 
            'text': """Kartu Tanda Penduduk Elektronik (KTP-el) adalah kartu tanda penduduk yang dilengkapi dengan chip elektronik. 
            Chip ini menyimpan biodata lengkap penduduk termasuk pas foto, tanda tangan, dan sidik jari. 
            NIK (Nomor Induk Kependudukan) bersifat unik, permanen, dan berlaku seumur hidup untuk setiap penduduk Indonesia.
            Setiap warga negara Indonesia yang telah berumur 17 tahun atau telah menikah wajib memiliki KTP elektronik.""",
            'category': 'administrasi_kependudukan'
        },
        {
            'doc_id': 'bpjs_kesehatan_001',
            'title': 'BPJS Kesehatan',
            'text': """BPJS Kesehatan menyelenggarakan program Jaminan Kesehatan Nasional untuk seluruh penduduk Indonesia.
            Program ini memberikan perlindungan kesehatan agar peserta memperoleh manfaat pemeliharaan kesehatan dan perlindungan.
            Terdapat tiga kelas perawatan: Kelas I (biaya tertinggi), Kelas II (menengah), dan Kelas III (terendah).
            Peserta wajib membayar iuran bulanan sesuai dengan kelas perawatan yang dipilih.""",
            'category': 'kesehatan'
        },
        {
            'doc_id': 'npwp_identitas_001',
            'title': 'NPWP dan Perpajakan',
            'text': """Nomor Pokok Wajib Pajak (NPWP) adalah nomor identitas perpajakan untuk setiap wajib pajak.
            Mulai tahun 2023, NIK dapat digunakan sebagai NPWP untuk wajib pajak orang pribadi.
            NPWP diperlukan untuk berbagai keperluan administrasi seperti pelaporan SPT, pembukaan rekening bank, dan pengajuan kredit.
            Setiap wajib pajak yang memiliki penghasilan wajib melaporkan SPT Tahunan paling lambat 31 Maret setiap tahunnya.""",
            'category': 'perpajakan'
        },
        {
            'doc_id': 'umkm_001',
            'title': 'UMKM dan Perpajakan',
            'text': """Usaha Mikro Kecil dan Menengah (UMKM) dengan omzet di bawah Rp 4,8 miliar per tahun mendapat fasilitas pajak khusus.
            Tarif PPh final untuk UMKM adalah 0,5% dari omzet bruto.
            UMKM yang baru beroperasi dapat memanfaatkan insentif pajak dan kemudahan perizinan melalui sistem Online Single Submission (OSS).
            Pemerintah juga menyediakan program kredit usaha rakyat (KUR) untuk mendukung pengembangan UMKM.""",
            'category': 'ekonomi'
        },
        {
            'doc_id': 'pendidikan_001',
            'title': 'Sistem Pendidikan Indonesia',
            'text': """Sistem pendidikan di Indonesia terdiri dari pendidikan formal, nonformal, dan informal.
            Pendidikan formal meliputi jenjang SD, SMP, SMA/SMK, dan Perguruan Tinggi.
            Pemerintah menyediakan program Kartu Indonesia Pintar (KIP) untuk membantu biaya pendidikan siswa dari keluarga kurang mampu.
            Selain itu, tersedia berbagai beasiswa seperti LPDP untuk pendidikan S2 dan S3 baik dalam maupun luar negeri.""",
            'category': 'pendidikan'
        },
    ]
    
    # Initialize vector store
    print("📦 Initializing Vector Store...")
    store = VectorStore()
    
    # Create chunks from documents
    chunks = []
    chunk_id = 0
    
    for doc in documents:
        # Simple chunking (just use whole document for now)
        chunk = Chunk(
            doc_id=doc['doc_id'],
            chunk_id=chunk_id,
            text=doc['text'].strip(),
            num_tokens=len(doc['text'].split()),
            metadata={
                'title': doc['title'],
                'category': doc['category'],
                'doc_type': 'sample',
                'source': 'manual_load'
            }
        )
        chunks.append(chunk)
        chunk_id += 1
    
    # Prepare for indexing
    print(f"📝 Preparing {len(chunks)} chunks...")
    prepared_chunks = prepare_chunks_for_indexing(chunks)
    
    # Add to vector store
    print("💾 Adding to vector store...")
    store.add_chunks(prepared_chunks, show_progress=True)
    
    # Verify
    count = store.collection.count()
    print()
    print(f"✅ Successfully loaded {count} documents!")
    print()
    
    # Test search
    print("🔍 Testing search...")
    results = store.search("Apa itu KTP elektronik?", n_results=2)
    
    if results:
        print("✅ Search working!")
        print(f"   Top result: {results[0].text[:100]}...")
        for i, res in enumerate(results, 1):
            print(f"   {i}. Score: {res.score:.3f} | {res.metadata.get('title')}")
    else:
        print("⚠️  No results found")
    
    print()
    print(f"🎉 Vector store ready with {count} documents!")
    print("   Now you can run RAG queries!")
    
    return count

if __name__ == "__main__":
    load_sample_documents()
