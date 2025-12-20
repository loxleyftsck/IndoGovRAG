"""
Query Expansion for Indonesian RAG

Expands queries with synonyms and related terms to improve recall.
"""

from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class ExpandedQuery:
    """Expanded query result."""
    original: str
    expanded: str
    added_terms: List[str]
    expansion_count: int


class QueryExpander:
    """
    Query expansion for Indonesian government documents.
    
    Features:
    - Synonym expansion
    - Acronym expansion  
    - Related term addition
    - Context-aware expansion
    """
    
    # Indonesian government document synonyms
    SYNONYMS = {
        # Identity documents
        'ktp': ['kartu tanda penduduk', 'identitas penduduk', 'e-ktp', 'ktp elektronik'],
        'nik': ['nomor induk kependudukan', 'nomor identitas', 'nomor ktp'],
        'kk': ['kartu keluarga', 'kartu keluarga'],
        'npwp': ['nomor pokok wajib pajak', 'nomor pajak'],
        
        # Healthcare
        'bpjs': ['badan penyelenggara jaminan sosial'],
        'bpjs kesehatan': ['jkn', 'jaminan kesehatan nasional'],
        'bpjs ketenagakerjaan': ['jamsostek'],
        'puskesmas': ['pusat kesehatan masyarakat', 'faskes tingkat pertama'],
        'rumah sakit': ['rs', 'faskes'],
        
        # Social programs
        'pkh': ['program keluarga harapan', 'bantuan sosial'],
        'kartu prakerja': ['prakerja', 'program prakerja'],
        'kip': ['kartu indonesia pintar'],
        'blt': ['bantuan langsung tunai'],
        
        # Business/taxation
        'oss': ['online single submission', 'sistem oss'],
        'nib': ['nomor induk berusaha'],
        'siup': ['surat izin usaha perdagangan'],
        'umkm': ['usaha mikro kecil menengah', 'usaha kecil'],
        
        # Employment
        'spt': ['surat pemberitahuan tahunan'],
        'tka': ['tenaga kerja asing'],
        'upah minimum': ['ump', 'umk', 'umin'],
        'kontrak kerja': ['perjanjian kerja', 'pkwt', 'pkwtt'],
        
        # Education
        'beasiswa': ['bantuan pendidikan'],
        'lpdp': ['lembaga pengelola dana pendidikan'],
        'ppdb': ['penerimaan peserta didik baru'],
        'ijazah': ['surat keterangan lulus', 'sertifikat'],
        
        # Property
        'shm': ['sertifikat hak milik'],
        'shgb': ['sertifikat hak guna bangunan'],
        'imb': ['izin mendirikan bangunan'],
        'pbb': ['pajak bumi dan bangunan'],
        
        # General terms
        'daftar': ['mendaftar', 'pendaftaran', 'registrasi'],
        'urus': ['mengurus', 'pengurusan', 'proses'],
        'syarat': ['persyaratan', 'ketentuan'],
        'cara': ['prosedur', 'tata cara', 'langkah'],
    }
    
    # Common Indonesian stop words (don't expand)
    STOP_WORDS = {
        'adalah', 'ada', 'yang', 'dan', 'atau', 'dari', 'di', 'ke', 'untuk',
        'dengan', 'pada', 'dalam', 'oleh', 'itu', 'ini', 'bisa', 'dapat',
        'akan', 'sudah', 'telah', 'jika', 'apabila', 'bagaimana', 'apa'
    }
    
    def __init__(self, max_expansions: int = 3):
        """
        Initialize query expander.
        
        Args:
            max_expansions: Maximum number of expansion terms to add
        """
        self.max_expansions = max_expansions
        
        # Build reverse index for faster lookup
        self.term_to_expansions = {}
        for key, synonyms in self.SYNONYMS.items():
            # Key itself maps to synonyms
            self.term_to_expansions[key] = synonyms
            # Each synonym also maps to key + other synonyms
            for syn in synonyms:
                if syn not in self.term_to_expansions:
                    self.term_to_expansions[syn] = [key] + [s for s in synonyms if s != syn]
    
    def expand(self, query: str) -> ExpandedQuery:
        """
        Expand query with synonyms and related terms.
        
        Args:
            query: Original query
        
        Returns:
            ExpandedQuery with expanded terms
        """
        original = query
        query_lower = query.lower()
        
        # Find matching terms
        added_terms = []
        seen = set()
        
        # Try to match multi-word phrases first (longer matches first)
        tokens = query_lower.split()
        
        # Sort keys by length (longer first) for better matching
        sorted_keys = sorted(self.term_to_expansions.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            if key in query_lower and key not in seen:
                # Get expansions for this term
                expansions = self.term_to_expansions[key]
                
                # Add up to max_expansions per term
                for exp in expansions[:self.max_expansions]:
                    if exp not in query_lower and exp not in seen:
                        added_terms.append(exp)
                        seen.add(exp)
                
                seen.add(key)
        
        # Build expanded query
        if added_terms:
            expanded = f"{original} {' '.join(added_terms)}"
        else:
            expanded = original
        
        return ExpandedQuery(
            original=original,
            expanded=expanded,
            added_terms=added_terms,
            expansion_count=len(added_terms)
        )
    
    def expand_batch(self, queries: List[str]) -> List[ExpandedQuery]:
        """Expand multiple queries."""
        return [self.expand(q) for q in queries]


# =============================================================================
# DEMO & TESTING
# =============================================================================

def demo_query_expansion():
    """Demo query expansion."""
    
    print("=" * 70)
    print(" 🧪 QUERY EXPANSION DEMO")
    print("=" * 70)
    print()
    
    expander = QueryExpander(max_expansions=3)
    
    # Test queries
    test_queries = [
        "Apa itu KTP elektronik?",
        "Bagaimana cara mendaftar BPJS Kesehatan?",
        "Berapa iuran BPJS kelas 3?",
        "Syarat mendaftar Kartu Prakerja",
        "Cara urus NPWP online",
        "Prosedur daftar beasiswa LPDP",
        "Bagaimana klaim BPJS?",
        "Apa perbedaan SHM dan SHGB?",
        "Cara mendapat NIB untuk usaha?",
        "Berapa upah minimum regional?",
    ]
    
    print("📝 Query Expansion Results:\\n")
    
    for i, query in enumerate(test_queries, 1):
        result = expander.expand(query)
        
        print(f"{i}. Original: {result.original}")
        
        if result.expansion_count > 0:
            print(f"   ✅ Expanded ({result.expansion_count} terms added):")
            print(f"   → {result.expanded}")
            print(f"   Added: {', '.join(result.added_terms)}")
        else:
            print(f"   ℹ️  No expansion needed")
        
        print()
    
    # Statistics
    results = expander.expand_batch(test_queries)
    total_expansions = sum(r.expansion_count for r in results)
    avg_expansions = total_expansions / len(results)
    
    print("=" * 70)
    print(" 📊 STATISTICS")
    print("=" * 70)
    print(f"Queries tested: {len(test_queries)}")
    print(f"Total expansions: {total_expansions}")
    print(f"Avg expansions per query: {avg_expansions:.2f}")
    print(f"Queries expanded: {sum(1 for r in results if r.expansion_count > 0)}")
    print()
    
    print("✅ Demo complete!")


if __name__ == "__main__":
    demo_query_expansion()
