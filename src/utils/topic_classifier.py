"""
Topic Classifier for Legal Query Classification
Tags Indonesian legal queries into: pidana/perdata/pajak/ketenagakerjaan/pertanahan/bisnis/administrasi
Uses keyword-based matching for fast classification without ML dependencies.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class LegalTopic(Enum):
    """Indonesian legal topic categories."""
    PIDANA = "pidana"        # Criminal law
    PERDATA = "perdata"     # Civil law
    PAJAK = "pajak"         # Tax law
    KETENAGAKERJAAN = "ketenagakerjaan"  # Labor/employment law
    PERTANAHAN = "pertanahan"  # Land/property law
    BISNIS = "bisnis"       # Business/commercial law
    ADMINISTRASI = "administrasi"  # Administrative/government law
    UMUM = "umum"           # General/not classified


@dataclass
class TopicResult:
    """Result of topic classification."""
    primary_topic: LegalTopic
    confidence_score: float  # 0.0 - 1.0
    all_topics: List[LegalTopic]  # All topics with matches, sorted by score
    matched_keywords: List[str]
    is_high_stakes: bool  # True for pidana/pajak/ketenagakerjaan/pertanahan


# High-stakes topics requiring additional disclaimer
HIGH_STAKES_TOPICS = {
    LegalTopic.PIDANA,
    LegalTopic.PAJAK,
    LegalTopic.KETENAGAKERJAAN,
    LegalTopic.PERTANAHAN,
}


class TopicClassifier:
    """
    Keyword-based topic classifier for Indonesian legal queries.

    Uses keyword matching to classify queries into legal topic categories.
    Designed for fast classification with no ML dependencies.
    """

    # Topic keyword definitions (Indonesian)
    TOPIC_KEYWORDS: Dict[LegalTopic, List[str]] = {
        LegalTopic.PIDANA: [
            "pidana", "hukum pidana", "pasal", "kejahatan", "kriminal",
            "pencurian", "penipuan", "pembunuhan", "narkoba", "narkotika",
            "penjara", "hukuman", "tersangka", "terdakwa", "terdakwa",
            "delik", "delik pidana", "korupsi", "suap", "penyuapan",
            "pengeroyokan", "pelecehan", "pemerkosaan", "pencabulan",
            "cukai", "illegal", "tindak pidana", "criminal", "crime",
            "penuntutan", "jaksa", "pengadilan", "mk", "mahkamah agung",
            "penahanan", "spkt", "laporan polisi", "laporan polisi"
        ],
        LegalTopic.PERDATA: [
            "perdata", "hukum perdata", "sipil", "gugatan", "klien",
            "hak sipil", "waris", "warisan", "testamen", "wasiat",
            "perceraian", "cerai", "harta", "suami", "istri",
            "kawin", "nikah", "akta", "notaris", "surat perjanjian",
            "kontrak", " MOU", "mou", "deal", "gugatan perdata",
            "sengketa", "mediasi", "arbitrase", "litigasi",
            "penggugat", "tergugat", "hak asuh", "nafkah",
            "pembagian", "tanah", "bangunan", "rumah", "tanah",
            "hibah", "donasi", "hadiah", "pidana", "pidana"
        ],
        LegalTopic.PAJAK: [
            "pajak", "ppn", "ppn", "pph", "pph 21", "pph 22", "pph 23",
            "pph 25", "pph 26", "pph final", "pajak penghasilan",
            "pajak pertambahan nilai", "pajak bumi dan bangunan", "pbb",
            "bphtb", "bea", "bea materai", "cukai",
            "npwp", "nomor pokok wajib pajak", "spt", "surat pemberitahuan",
            "kode billing", "pembayaran pajak", "penyetoran",
            "tax", "taxation", "taxes", "fiskal", "perpajakan",
            "tax amnesty", "tax holiday", "tax deduction", "tax incentive",
            "validasi", "faktur pajak", "e-faktur", "pajak daerah",
            "retribusi", "pendapatan", "penerimaan negara",
            "stts", "spm", "spp", "surat setoran pajak"
        ],
        LegalTopic.KETENAGAKERJAAN: [
            "tenaga kerja", "pekerja", "karyawan", "karyawati",
            "lowongan", "rekrutmen", "recruitment", "seleksi",
            "kontrak kerja", "pkwt", "perjanjian kerja",
            "pkwtt", "masa percobaan", "probation", "out probation",
            "upah", "gaji", "lembur", "lemburan", "overtime",
            "cuti", "cuti tahunan", "cuti sakit", "maternity", "melahirkan",
            "hari raya", "thr", "tunjangan", "bonus", "insentif",
            "buruh", "serikat pekerja", "serikat buruh", "sp/sb",
            "ksp", "ksb", "kspi", "kspi", "demo", "demonstrasi",
            "mogok", "strike", "PHK", "pemutusan hubungan kerja",
            "pesangon", "kompensasi", "jamsostek", "bpjs ketenagakerjaan",
            "jht", "jkp", "jkk", "jkm", "accident", "jamsos",
            "perburuhan", "perusahaan", "tdk", "PKB", "PKWT",
            "normatif", "ketenagakerjaan", "k3", "keselamatan kerja",
            "hlk", "hk", "penerapan", "pemagangan", "magang",
            "outsourcing", "outsource", "distributor", "agen",
            "fleksibel", "flexible", "wirausaha", "enterpreneur",
            "K3", "safety", "higiene", "industrial"
        ],
        LegalTopic.PERTANAHAN: [
            "tanah", "pertanahan", "agraria", "agraria", "hak ulayat",
            "hak milik", "hm", "hak guna bangunan", "hgb",
            "hak pakai", "hp", "hak pengelolaan", "hak sewa",
            "sertifikat", "sertifikasi", "sertifikat tanah",
            "shm", "shgb", "shp", "ppat", "ppat",
            "akta tanah", "pendaftaran tanah", "bea perolehan",
            "bpptb", "bphtb", "njop", "nilai jual objek pajak",
            "tanah negara", "tanah wakaf", "wakaf", "perwakafan",
            "pemanfaatan tanah", "ganti rugi", "kompensasi tanah",
            "evakuasi", "relokasi", "penguasaan", "sengketa tanah",
            "konflik tanah", "aduan tanah", "hak tanah", "status tanah",
            "lahan", "kavling", "kapling", "plot", "plat",
            "imb", "izin membangun", "izin lokasi", "ipr", "ipla",
            "tgh", "girik", "nib", "num", "nomor urut tanah",
            "land", "property", "estate", "survey", "pengukuran",
            "kadaster", "cadaster", "peta", "plotting",
            "c1", "c2", "c3", "daerah", "inventarisasi",
            "land reform", "reforma agraria", "redistribusi"
        ],
        LegalTopic.BISNIS: [
            "bisnis", "perusahaan", "company", "badan usaha",
            "pt", "perseroan terbatas", "cv", "commanditaire vennootschap",
            "fa", "firma", "pt cv fa", "yayasan", "foundation",
            "koordinator", "koperasi", "koper", "koperasi",
            "permodalan", "modal", "investasi", "investor",
            "saham", "stock", "obligasi", "bond", "debt",
            "akuisisi", "merger", " merger", "akuisisi",
            "spin off", "corporate", "merger", "joint venture",
            "joint", "ventura", "patnership", "franchise", "waralaba",
            "lisensi", "license", "izin usaha", "nib",
            "oss", "online single submission", "siup",
            "tdp", "surat izin tempat usaha", "iuj", "izin usaha jasa",
            "nib", "api", "api-u", "api-p", "aper", "aperiso",
            "indomaret", "alfamart", "hypermarket", "toko",
            "retail", "distributor", "grosir", "agen", "subagent",
            "franchise", "waralaba", "biz", "bisnisplan",
            "proposal", "feasibility", "studi kelayakan",
            "franchisor", "franchisee", "mitra", "partner",
            "restoran", "cafe", "hotel", "homestay", "villa",
            "klinik", "apotek", "farmasi", "medis", "kesehatan",
            "legal", "hukum", "legalitas", "legalisir", "legalisasi",
            "drafting", "kontrak", "perjanjian", "agreement",
            "mou", "notulensi", "risalah", "contract", "akta"
        ],
        LegalTopic.ADMINISTRASI: [
            "administrasi", "administrasi publik", "pemerintahan",
            "pelayanan publik", "layanan publik", "e-government",
            "egov", "digital", "elektronik", "online", "sistem",
            "ktp", "kartu tanda penduduk", "kk", "kartu keluarga",
            "akta kelahiran", "akta kematian", "surat kematian",
            "kelahiran", "kematian", "kelahiran", "akta",
            "akta nikah", "akta cerai", "surat izin",
            "surat keputusan", "sk", "peraturan", "perda",
            "pergub", "perbup", "sktt", "kartri", "kitas",
            "kitap", "visti", "visa", "passport", "passpor",
            "imigran", "wna", "warga negara asing", "expat",
            "pelayanan", "service", "izin", "license",
            "permohonan", "apply", "application", "pengajuan",
            "persetujuan", "approval", "rekomendasi", "recom",
            "bupati", "walikota", "gubernur", "kepala daerah",
            "sekda", "sekretaris daerah", "dirjen", "direktur jenderal",
            "menpan", "menlh", "menteri", "mentri", "department",
            "dinas", "bidang", "seksi", "subbidang", "subseksi",
            "kecamatan", "kelurahan", "desa", "kampung", "rw", "rt",
            "ppt", "ppt", "ppt", "ppt", "ppt",
            "formulir", "blanko", "dokumen", "dokumentasi",
            "arsip", "dokumentasi", "dokumen", "berkas",
            "registrasi", "pendaftaran", "pendaftaran", "enrollment",
            "biodata", "profile", "data", "database",
            "rt rw", "surat keterangan", "suket", "keterangan domisili",
            "domisili", "usaha", "tempat tinggal", "tinggal",
            "ceklab", "cek kesehatan", "medical", "rs", "rumah sakit"
        ],
    }

    def __init__(self):
        """Initialize topic classifier with keyword index."""
        # Build reverse lookup: keyword -> topic
        self._keyword_to_topic: Dict[str, LegalTopic] = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                self._keyword_to_topic[keyword.lower()] = topic

        # Build topic word sets for faster matching
        self._topic_word_sets: Dict[LegalTopic, set] = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            self._topic_word_sets[topic] = set(k.lower() for k in keywords)

    def classify(self, query: str) -> TopicResult:
        """
        Classify a legal query into topic categories.

        Args:
            query: User query string in Indonesian

        Returns:
            TopicResult with primary topic, confidence, all matches

        Examples:
            >>> classifier = TopicClassifier()
            >>> result = classifier.classify("Bagaimana cara membuat PT?")
            >>> print(result.primary_topic)  # LegalTopic.BISNIS
        """
        if not query or not query.strip():
            return TopicResult(
                primary_topic=LegalTopic.UMUM,
                confidence_score=0.0,
                all_topics=[],
                matched_keywords=[],
                is_high_stakes=False
            )

        # Normalize query
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Count matches per topic
        topic_scores: Dict[LegalTopic, float] = {}
        topic_matches: Dict[LegalTopic, List[str]] = {}

        for topic, word_set in self._topic_word_sets.items():
            matches = query_words & word_set
            if matches:
                topic_scores[topic] = len(matches)
                topic_matches[topic] = list(matches)

        if not topic_scores:
            return TopicResult(
                primary_topic=LegalTopic.UMUM,
                confidence_score=0.0,
                all_topics=[],
                matched_keywords=[],
                is_high_stakes=False
            )

        # Sort by score
        sorted_topics = sorted(
            topic_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Calculate confidence based on match ratio
        query_word_count = len(query_words)
        top_score = sorted_topics[0][1]
        max_possible = sum(1 for kw in self.TOPIC_KEYWORDS[sorted_topics[0][0]] if kw.lower() in query_words)

        # Confidence: ratio of matches to possible matches in top topic
        confidence = min(top_score / max(1, max_possible), 1.0)

        all_topics = [t for t, _ in sorted_topics]
        primary_topic = sorted_topics[0][0]
        matched_keywords = topic_matches.get(primary_topic, [])

        return TopicResult(
            primary_topic=primary_topic,
            confidence_score=confidence,
            all_topics=all_topics,
            matched_keywords=matched_keywords,
            is_high_stakes=primary_topic in HIGH_STAKES_TOPICS
        )

    def is_high_stakes_topic(self, topic: LegalTopic) -> bool:
        """Check if a topic requires additional disclaimer."""
        return topic in HIGH_STAKES_TOPICS

    def get_topic_label(self, topic: LegalTopic) -> str:
        """Get human-readable label for a topic."""
        labels = {
            LegalTopic.PIDANA: "Hukum Pidana",
            LegalTopic.PERDATA: "Hukum Perdata",
            LegalTopic.PAJAK: "Perpajakan",
            LegalTopic.KETENAGAKERJAAN: "Ketenagakerjaan",
            LegalTopic.PERTANAHAN: "Pertanahan",
            LegalTopic.BISNIS: "Bisnis & Perusahaan",
            LegalTopic.ADMINISTRASI: "Administrasi Publik",
            LegalTopic.UMUM: "Umum",
        }
        return labels.get(topic, topic.value)

    def get_all_topics(self) -> List[LegalTopic]:
        """Return all available topic categories."""
        return list(LegalTopic)


# Singleton instance for reuse
_classifier_instance: Optional[TopicClassifier] = None


def get_topic_classifier() -> TopicClassifier:
    """Get singleton topic classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = TopicClassifier()
    return _classifier_instance


from functools import lru_cache
from typing import Optional, List, Dict


@lru_cache(maxsize=512)
def classify_query(query: str) -> TopicResult:
    """
    Convenience function to classify a query.

    Args:
        query: User query string in Indonesian

    Returns:
        TopicResult with classification details
    """
    return get_topic_classifier().classify(query)


# =============================================================================
# TESTS
# =============================================================================

def test_classifier():
    """Test the topic classifier with sample queries."""
    test_queries = [
        ("Bagaimana cara membuat PT baru?", LegalTopic.BISNIS),
        ("Apa sanksi pidana untuk pencurian?", LegalTopic.PIDANA),
        ("Bagaimana cara menghitung PPH 21?", LegalTopic.PAJAK),
        ("Apa hak pekerja saat di-PHK?", LegalTopic.KETENAGAKERJAAN),
        ("Bagaimana proses sertifikasi tanah?", LegalTopic.PERTANAHAN),
        ("Syarat bikin KTP elektronik apa saja?", LegalTopic.ADMINISTRASI),
        ("Pembagian waris dalam hukum Islam", LegalTopic.PERDATA),
        ("Pelayanan administrasi KTP", LegalTopic.ADMINISTRASI),
        ("Sanksi pajak jika telat bayar", LegalTopic.PAJAK),
        ("Hak pekerja kontrak", LegalTopic.KETENAGAKERJAAN),
    ]

    classifier = TopicClassifier()
    print("=" * 70)
    print("TOPIC CLASSIFIER TEST RESULTS")
    print("=" * 70)

    passed = 0
    for query, expected in test_queries:
        result = classifier.classify(query)
        status = "PASS" if result.primary_topic == expected else "FAIL"
        if status == "PASS":
            passed += 1

        print(f"\n[{status}] Query: {query}")
        print(f"   Expected: {expected.value}")
        print(f"   Got: {result.primary_topic.value} (conf: {result.confidence_score:.2f})")
        print(f"   High-stakes: {result.is_high_stakes}")
        if result.matched_keywords:
            print(f"   Keywords: {result.matched_keywords}")

    print(f"\n{'='*70}")
    print(f"Results: {passed}/{len(test_queries)} passed")
    print("=" * 70)


if __name__ == "__main__":
    test_classifier()