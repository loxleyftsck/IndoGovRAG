"""
Simple Vector Store WITHOUT sentence-transformers

Uses simple TF-IDF + cosine similarity instead of neural embeddings.
Quick fix to get RAG working NOW!
"""

import json
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict


class SimpleVectorStore:
    """Simple vector store using TF-IDF (no neural networks)."""
    
    def __init__(self, persist_dir: str = "data/vector_db/simple"):
        """Initialize simple vector store."""
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Store documents in memory
        self.documents = []
        self.vectorizer = TfidfVectorizer(
            max_features=768,  # Match embedding dimension
            ngram_range=(1, 2),
            stop_words=None  # Keep Indonesian words
        )
        self.vectors = None
        
        # Load if exists
        self._load()
        
        print(f"✅ Simple Vector Store initialized")
        print(f"   Documents: {len(self.documents)}")
    
    def add_documents(self, docs: List[Dict]):
        """
        Add documents with validation.
        
        Args:
            docs: List of dicts with 'text', 'metadata'
        """
        # Validate each document
        validated_docs = []
        for i, doc in enumerate(docs):
            try:
                # Basic validation
                if 'text' not in doc:
                    raise ValueError(f"Document {i}: missing 'text' field")
                
                text = doc['text']
                metadata = doc.get('metadata', {})
                
                # Length check
                if len(text) > 50000:  # 50K chars max
                    raise ValueError(f"Document {i}: text too long ({len(text)} chars)")
                
                if not text.strip():
                    raise ValueError(f"Document {i}: empty text")
                
                # Sanitize metadata
                safe_metadata = {}
                allowed_keys = {'title', 'category', 'source', 'date'}
                for key in allowed_keys:
                    if key in metadata:
                        safe_metadata[key] = str(metadata[key])[:200]
                
                validated_docs.append({
                    'text': text.strip(),
                    'metadata': safe_metadata
                })
                
            except Exception as e:
                print(f"⚠️ Skipping invalid document {i}: {e}")
                continue
        
        if not validated_docs:
            raise ValueError("No valid documents to add")
        
        # Add validated documents
        self.documents.extend(validated_docs)
        
        # Recompute vectors
        all_texts = [d['text'] for d in self.documents]
        self.vectors = self.vectorizer.fit_transform(all_texts)
        
        # Save
        self._save()
        
        print(f"✅ Added {len(validated_docs)} documents (total: {len(self.documents)})")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            List of results with 'text', 'score', 'metadata'
        """
        if len(self.documents) == 0:
            return []
        
        # Vectorize query
        query_vec = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vec, self.vectors)[0]
        
        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'text': self.documents[idx]['text'],
                'score': float(similarities[idx]),
                'metadata': self.documents[idx].get('metadata', {})
            })
        
        return results
    
    def count(self) -> int:
        """Get document count."""
        return len(self.documents)
    
    def _save(self):
        """Save to disk."""
        save_path = self.persist_dir / "documents.json"
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
    
    def _load(self):
        """Load from disk."""
        save_path = self.persist_dir / "documents.json"
        if save_path.exists():
            with open(save_path, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
            
            if self.documents:
                all_texts = [d['text'] for d in self.documents]
                self.vectors = self.vectorizer.fit_transform(all_texts)


def load_sample_documents_simple():
    """Load Indonesian government documents - SIMPLE VERSION."""
    
    print("🔧 Loading Sample Documents (Simple Version - No Neural Networks)")
    print()
    
    # Sample documents
    docs = [
        {
            'text': """Kartu Tanda Penduduk Elektronik (KTP-el) adalah kartu tanda penduduk yang dilengkapi dengan chip elektronik. 
            Chip ini menyimpan biodata lengkap penduduk termasuk pas foto, tanda tangan, dan sidik jari. 
            NIK (Nomor Induk Kependudukan) bersifat unik, permanen, dan berlaku seumur hidup untuk setiap penduduk Indonesia.
            Setiap warga negara Indonesia yang telah berumur 17 tahun atau telah menikah wajib memiliki KTP elektronik.""",
            'metadata': {'title': 'KTP Elektronik', 'category': 'administrasi'}
        },
        {
            'text': """BPJS Kesehatan menyelenggarakan program Jaminan Kesehatan Nasional untuk seluruh penduduk Indonesia.
            Program ini memberikan perlindungan kesehatan agar peserta memperoleh manfaat pemeliharaan kesehatan dan perlindungan.
            Terdapat tiga kelas perawatan: Kelas I (biaya tertinggi), Kelas II (menengah), dan Kelas III (terendah).
            Peserta wajib membayar iuran bulanan sesuai dengan kelas perawatan yang dipilih.""",
            'metadata': {'title': 'BPJS Kesehatan', 'category': 'kesehatan'}
        },
        {
            'text': """Nomor Pokok Wajib Pajak (NPWP) adalah nomor identitas perpajakan untuk setiap wajib pajak.
            Mulai tahun 2023, NIK dapat digunakan sebagai NPWP untuk wajib pajak orang pribadi.
            NPWP diperlukan untuk berbagai keperluan administrasi seperti pelaporan SPT, pembukaan rekening bank, dan pengajuan kredit.
            Setiap wajib pajak yang memiliki penghasilan wajib melaporkan SPT Tahunan paling lambat 31 Maret setiap tahunnya.""",
            'metadata': {'title': 'NPWP', 'category': 'perpajakan'}
        },
        {
            'text': """Usaha Mikro Kecil dan Menengah (UMKM) dengan omzet di bawah Rp 4,8 miliar per tahun mendapat fasilitas pajak khusus.
            Tarif PPh final untuk UMKM adalah 0,5% dari omzet bruto.
            UMKM yang baru beroperasi dapat memanfaatkan insentif pajak dan kemudahan perizinan melalui sistem Online Single Submission (OSS).
            Pemerintah juga menyediakan program kredit usaha rakyat (KUR) untuk mendukung pengembangan UMKM.""",
            'metadata': {'title': 'UMKM', 'category': 'ekonomi'}
        },
        {
            'text': """Sistem pendidikan di Indonesia terdiri dari pendidikan formal, nonformal, dan informal.
            Pendidikan formal meliputi jenjang SD, SMP, SMA/SMK, dan Perguruan Tinggi.
            Pemerintah menyediakan program Kartu Indonesia Pintar (KIP) untuk membantu biaya pendidikan siswa dari keluarga kurang mampu.
            Selain itu, tersedia berbagai beasiswa seperti LPDP untuk pendidikan S2 dan S3 baik dalam maupun luar negeri.""",
            'metadata': {'title': 'Pendidikan', 'category': 'pendidikan'}
        },
    ]
    
    # Initialize store
    store = SimpleVectorStore()
    
    # Add documents
    store.add_documents(docs)
    
    # Test search
    print("\n🔍 Testing search...")
    results = store.search("Apa itu KTP elektronik?", top_k=2)
    
    if results:
        print("✅ Search working!")
        for i, res in enumerate(results, 1):
            print(f"   {i}. Score: {res['score']:.3f} | {res['metadata']['title']}")
            print(f"      Text: {res['text'][:80]}...")
    
    print(f"\n🎉 Simple vector store ready with {store.count()} documents!")
    print("   Using TF-IDF (no neural networks needed)")
    
    return store


if __name__ == "__main__":
    load_sample_documents_simple()
