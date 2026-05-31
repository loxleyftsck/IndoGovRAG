"""
Query Expansion for Indonesian RAG

Expands queries with synonyms and related terms to improve recall.
"""

import logging
from typing import List, Dict, Set
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


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
            self.term_to_expansions[key] = synonyms
            for syn in synonyms:
                if syn not in self.term_to_expansions:
                    self.term_to_expansions[syn] = [key] + [s for s in synonyms if s != syn]

        # Per-instance LRU-cached expand function bound to class-level state
        self._expand_cached = _make_expand_cached(self.term_to_expansions, self.max_expansions)

    def expand(self, query: str) -> ExpandedQuery:
        """
        Expand query with synonyms and related terms.
        Results are cached via LRU (512 entries) so repeated identical queries
        are resolved instantly without any processing.

        Args:
            query: Original query

        Returns:
            ExpandedQuery with expanded terms
        """
        return self._expand_cached(query)

    def expand_batch(self, queries: List[str]) -> List[ExpandedQuery]:
        """Expand multiple queries."""
        return [self.expand(q) for q in queries]


# =============================================================================
# DEMO & TESTING
# =============================================================================

# Module-level cached expand functions — one per unique (term_index_id, max_expansions) combo
_cached_expanders: Dict[tuple, callable] = {}


def _make_expand_cached(term_to_expansions: Dict, max_expansions: int):
    """Create an LRU-cached expand function bound to specific term config (called once per QueryExpander instance)."""
    key = (id(term_to_expansions), max_expansions)
    if key not in _cached_expanders:
        @lru_cache(maxsize=512)
        def cached_expand(query: str) -> ExpandedQuery:
            """Pure expand logic — runs inside lru_cache."""
            original = query
            query_lower = query.lower()
            added_terms = []
            seen = set()

            sorted_keys = sorted(term_to_expansions.keys(), key=len, reverse=True)

            for term_key in sorted_keys:
                if term_key in query_lower and term_key not in seen:
                    expansions = term_to_expansions[term_key]
                    for exp in expansions[:max_expansions]:
                        if exp not in query_lower and exp not in seen:
                            added_terms.append(exp)
                            seen.add(exp)
                    seen.add(term_key)

            expanded = f"{original} {' '.join(added_terms)}" if added_terms else original

            return ExpandedQuery(
                original=original,
                expanded=expanded,
                added_terms=added_terms,
                expansion_count=len(added_terms)
            )

        _cached_expanders[key] = cached_expand
    return _cached_expanders[key]


def demo_query_expansion():
    """Demo query expansion."""

    logger.info("[TEST] QUERY EXPANSION DEMO")
    logger.info("=" * 70)
    logger.info("")

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

    logger.info("[MSG] Query Expansion Results:\n")

    for i, query in enumerate(test_queries, 1):
        result = expander.expand(query)

        logger.info(f"{i}. Original: {result.original}")

        if result.expansion_count > 0:
            logger.info(f"   [OK] Expanded ({result.expansion_count} terms added):")
            logger.info(f"   -> {result.expanded}")
            logger.info(f"   Added: {', '.join(result.added_terms)}")
        else:
            logger.info(f"   [INFO]  No expansion needed")

        logger.info("")

    # Statistics
    results = expander.expand_batch(test_queries)
    total_expansions = sum(r.expansion_count for r in results)
    avg_expansions = total_expansions / len(results)

    logger.info("=" * 70)
    logger.info("[STAT] STATISTICS")
    logger.info("=" * 70)
    logger.info(f"Queries tested: {len(test_queries)}")
    logger.info(f"Total expansions: {total_expansions}")
    logger.info(f"Avg expansions per query: {avg_expansions:.2f}")
    logger.info(f"Queries expanded: {sum(1 for r in results if r.expansion_count > 0)}")
    logger.info("")

    logger.info("[OK] Demo complete!")


if __name__ == "__main__":
    demo_query_expansion()
