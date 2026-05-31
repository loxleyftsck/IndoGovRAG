"""
Legal Document Analyzer for IndoGovRAG

Analyzes Indonesian legal documents (contracts, agreements, MoU) by:
- Extracting and classifying clauses
- Identifying conflicts with applicable laws
- Assessing legal risks per clause
- Generating executive summaries

All analysis is based on Indonesian legal terminology and regulations.
"""

from __future__ import annotations

import re
import json
from datetime import datetime as _dt
from dataclasses import dataclass, field, asdict
from typing import Optional, Any


# =============================================================================
# CLAUSE TYPE CLASSIFICATION PATTERNS
# =============================================================================

CLAUSE_TYPES: dict[str, list[str]] = {
    "definisi": [
        "pengertian", "definisi", "yang dimaksud", "yang selanjutnya",
        "adalah", "selanjutnya disebut", "berarti", "diartikan"
    ],
    "hak": [
        "hak", "berhak", "rights", "wewenang", "otoritas", "kuasa",
        "mendapat", "diperkenankan", "dapat memperoleh", "memiliki hak"
    ],
    "kewajiban": [
        "kewajiban", "wajib", "harus", "obligations", "职责",
        "bertanggung jawab", "tanggung jawab", "melaksanakan",
        "haruslah", "seharusnya", "diwajibkan", "penuh"
    ],
    "larangan": [
        "dilarang", "tidak boleh", "larangan", "tidak diizinkan",
        "dilarang keras", "tidak diperbolehkan", "dilarang untuk",
        "melarang", "mencegah", "dilarang secara"
    ],
    "sanksi": [
        "sanksi", "denda", "penalty", "hukuman", "konsekuensi",
        "ganti rugi", "tanggung rugi", "kompensasi", "denda keterlambatan",
        "denda per hari", "penalti", "sanksi administratif", "punishment"
    ],
    "pembatalan": [
        "batalkan", "terminate", "pengakhiran", "pencabutan",
        "berakhir", "kedaluwarsa", "masa berlaku", "durasi",
        "jangka waktu", "pembatasan waktu", "masa berlaku"
    ],
    "force_majeure": [
        "force majeure", "kejadian tak terduga", "bencana alam",
        "musibah", "peristiwa memaksa", "keadaan kahar", "vis major",
        "diantara pihak", "gangguan yang tidak terduga"
    ],
    "penyelesaian_sengketa": [
        "arbitrase", "pengadilan", "mediasi", "negosiasi",
        "penyelesaian sengketa", "sengketa", "perselisihan",
        "gugatan", "keluhan", "dispute resolution", "court"
    ],
    "lainnya": []
}

# =============================================================================
# INDONESIAN LEGAL REFERENCE DATABASE
# =============================================================================

LEGAL_REFERENCES: dict[str, dict[str, Any]] = {
    # Personal Data Protection
    "UU 27/2022": {
        "title": "UU No. 27 Tahun 2022 tentang Perlindungan Data Pribadi (PDP)",
        "articles": {
            "penalty_high": {
                "pattern": r"denda\s+\d+%\s+per\s+hari",
                "limit": "Maksimum 3 bulan berdasarkan UU 27/2022 Pasal 51",
                "risk": "high"
            },
            "unlimited_retention": {
                "pattern": r"simpan\s+selamanya|retensi\s+tidak\s+terbatas",
                "limit": "PDP wajib dihapus setelah tujuan terpenuhi (Pasal 16)",
                "risk": "high"
            }
        }
    },
    # Consumer Protection
    "UU 8/1999": {
        "title": "UU No. 8 Tahun 1999 tentang Perlindungan Konsumen",
        "articles": {
            "unfair_terms": {
                "pattern": r"hak\s+untuk\s+mengubah\s+tanpa\x20persetujuan",
                "limit": "Klausul tidak boleh menghilangkan hak konsumen (Pasal 18)",
                "risk": "medium"
            }
        }
    },
    # Civil Code (KUH Perdata)
    "KUHPerdata": {
        "title": "Kitab Undang-Undang Hukum Perdata (Burgerlijk Wetboek)",
        "articles": {
            "interest_rate": {
                "pattern": r"bunga\s+\d+%|\d+%.*per\s+tahun",
                "limit": "Bunga melebihi bunga tertinggi dapat disesuaikan (Pasal 1765)",
                "risk": "medium"
            }
        }
    },
    # Contract Law
    "Psl 1320 KUHPerdata": {
        "title": "Pasal 1320 KUHPerdata - Syarat Sah Perjanjian",
        "articles": {
            "coercion": {
                "pattern": r"wajib\s+menerima|harus\x20menyetujui\x20tanpa",
                "limit": "Perjanjian bisa dibatalkan karena paksaan (Pasal 1323)",
                "risk": "high"
            }
        }
    },
    # Electronic Information
    "UU 11/2008": {
        "title": "UU No. 11 Tahun 2008 tentang Informasi dan Transaksi Elektronik (ITE)",
        "articles": {
            "electronic_signature": {
                "pattern": r"tanda\x20tangan\x20elektronik|TTE",
                "limit": "TTE memiliki kekuatan hukum yang sah (Pasal 1 ayat 10)",
                "risk": "low"
            }
        }
    },
    # Construction
    "UU 2/2017": {
        "title": "UU No. 2 Tahun 2017 tentang Jasa Konstruksi",
        "articles": {
            "unlimited_liability": {
                "pattern": r"tanggung\x20jawab\x20tak\x20terbatas",
                "limit": "Liabilitas konstruksi diatur berdasarkan KSO/kontrak (Pasal 42)",
                "risk": "medium"
            }
        }
    },
    # Job Creation (Omnibus Law)
    "UU 11/2020": {
        "title": "UU No. 11 Tahun 2020 tentang Cipta Kerja (Ciptaker)",
        "articles": {
            "fixed_term_contract": {
                "pattern": r"kontrak\x20kerja\x20tertentu|PKWT",
                "limit": "Maksimum 5 tahun dengan kemungkinan perpanjangan 5 tahun (Pasal 59)",
                "risk": "medium"
            }
        }
    },
    # PPh Final for SMEs
    "UU 1/2024": {
        "title": "UU No. 1 Tahun 2024 tentang Harmonisasi Peraturan Perpajakan",
        "articles": {
            "sme_penalty_limit": {
                "pattern": r"denda\s+1%|1%\s+per\s+hari",
                "limit": "Denda dihitung dari pokok pajak, maksimum sesuai expiry",
                "risk": "high"
            }
        }
    }
}

# =============================================================================
# RISK PATTERNS
# =============================================================================

RISK_PATTERNS: dict[str, dict[str, Any]] = {
    "high": [
        (r"denda\s+\d+\s*%.*per\s+hari", "Denda per hari berlebihan - mungkin unenforceable"),
        (r"tanggung\x20jawab\s+tidak\x20terbatas", "Tidak ada batasan tanggung jawab - risiko tinggi"),
        (r"batalkan\s+tanpa\x20notifikasi", "Pembatalan tanpa pemberitahuan - tidak fair"),
        (r"hak\s+untuk\x20mengubah\s+sepihak", "Perubahan sepihak - berpotensi violate UU 8/1999"),
        (r"wajib\s+menerima\s+semua\x20perubahan", "Klausul tidak fair - bisa dibatalkan"),
        (r"simpan\s+data\s+selamanya", "Retensi data tanpa batas - violate UU PDP"),
        (r"pidana\s+\d+\s+tahun", "Ancaman sanksi pidana - perlu review hukum"),
        (r"洩漏\s+data|kelalaian\s+berat", "Potensi kebocoran data - risiko tinggi"),
    ],
    "medium": [
        (r"arbitrase\s+wajib", "Arbitrase wajib - pertimbangkan pilihan yang lebih netral"),
        (r"hak\s+untuk\s+memindahtangankan", "Pengalihan hak - perlu persetujuan tertulis"),
        (r"kontrak\s+auto\x20renew", "Perpanjangan otomatis - berikan opsi terminasi"),
        (r"penalty\s+\d+\s*%", "Denda terlalu tinggi - perlu review proporsionalitas"),
        (r"penggunaan\s+data\s+untuk\x20pemasaran", "Penggunaan data marketing - perlu consent eksplisit"),
        (r"komisi\s+\d+%.*per\x20bulan", "Komisi berulang - pastikan tidak masuk zona riba"),
        (r"jaminan\s+\d+%.*harga", "Jaminan terlalu besar - pertimbangkan % yang wajar"),
    ],
    "low": [
        (r"definisi", "Klausul definisi - risiko rendah"),
        (r"huruf\x20kecil|maksimum\s+\d+\s+hari", "Klausul standar - risiko rendah"),
        (r"periode\x20cooling\x20off", "Periode pembatalan - praktik yang baik"),
        (r"dispute\s+resolution", "Klausul penyelesaian sengketa - risiko rendah"),
    ]
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ClauseResult:
    """Structured result for a single clause."""
    id: int
    type: str
    text: str
    risk_level: str
    warning: str
    related_laws: list[str]
    conflict_detected: bool

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if not d["warning"]:
            del d["warning"]
        if not d["related_laws"]:
            del d["related_laws"]
        return d


@dataclass
class AnalysisSummary:
    """Summary statistics for the analyzed document."""
    total_clauses: int
    high_risk: int
    medium_risk: int
    low_risk: int
    compliance_issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentAnalysisResult:
    """Complete analysis result for a legal document."""
    summary: AnalysisSummary
    clauses: list[ClauseResult]
    raw_document_length: int
    document_type_hint: str
    analyzed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "clauses": [c.to_dict() for c in self.clauses],
            "raw_document_length": self.raw_document_length,
            "document_type_hint": self.document_type_hint,
            "analyzed_at": self.analyzed_at,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# =============================================================================
# LEGAL DOCUMENT ANALYZER
# =============================================================================

class LegalDocumentAnalyzer:
    """
    Analyzer for Indonesian legal documents.

    Analyzes contracts, agreements, and MoUs to:
    - Extract and classify clauses
    - Check conflicts with Indonesian laws
    - Assess risk levels
    - Generate executive summaries

    Usage:
        analyzer = LegalDocumentAnalyzer()
        result = analyzer.analyze_document(contract_text)
        print(result.to_json())
    """

    # Clause splitting patterns
    CLAUSE_SPLITTERS = [
        # Standard numbering: Pasal, Ayat, Bagian
        r"(?:pasal\s+\d+[^\n]*)",
        r"(?:ayat\s+\d+[^\n]*)",
        r"(?:bagian\s+\d+[^\n]*)",
        # Numbered clauses: I., 1., 1.1, a), b), Article
        r"(?:^(?:[IVXivx]+\s*[.)]\s*.+)$)",
        r"(?:^(?:\d+[.)]\s*.+)$)",
        r"(?:^(?:[a-z][.)]\s*.+)$)",
        r"(?:^article\s+\d+[^\n]*)",
        # Headers
        r"(?:(?:^|\n)\s*(?:pasal|bagian|ayat|article|section|klausul)[^\n]{0,50})",
    ]

    def __init__(
        self,
        vector_store: Any = None,
        use_vector_search: bool = True,
        strict_mode: bool = False
    ):
        """
        Initialize the Legal Document Analyzer.

        Args:
            vector_store: Optional vector store instance for conflict checking
            use_vector_search: Whether to use vector store for law searches
            strict_mode: If True, more clauses flagged as risk
        """
        self.vector_store = vector_store
        self.use_vector_search = use_vector_search and vector_store is not None
        self.strict_mode = strict_mode

    # ------------------------------------------------------------------ #
    # PUBLIC API
    # ------------------------------------------------------------------ #

    def analyze_document(self, text: str) -> DocumentAnalysisResult:
        """
        Perform full analysis of a legal document.

        Args:
            text: Full text of the legal document

        Returns:
            DocumentAnalysisResult with clauses, risks, and summary
        """
        if not text or not text.strip():
            raise ValueError("Document text is empty")

        # Extract clauses
        clauses = self.extract_clauses(text)

        # Identify conflicts
        clauses = self.identify_conflicts(clauses)

        # Assess risks
        clauses = self.assess_risks(clauses)

        # Build summary
        summary = self._build_summary(clauses)

        # Determine document type hint
        doc_type = self._detect_document_type(text)

        return DocumentAnalysisResult(
            summary=summary,
            clauses=clauses,
            raw_document_length=len(text),
            document_type_hint=doc_type,
            analyzed_at=_dt.now().strftime("%Y-%m-%dT%H:%M:%S"),
        )

    def extract_clauses(self, text: str) -> list[ClauseResult]:
        """
        Parse and extract clauses from document text.

        Args:
            text: Full document text

        Returns:
            List of ClauseResult objects
        """
        if not text or not text.strip():
            return []

        # Split into candidate clauses
        segments = self._split_into_segments(text)

        if not segments:
            # Fallback: split by double newlines or periods
            segments = [s.strip() for s in re.split(r"\n\n+|\.\s+", text) if s.strip()]

        clauses: list[ClauseResult] = []
        for idx, segment in enumerate(segments, 1):
            segment = segment.strip()
            if len(segment) < 20:  # Skip very short fragments
                continue

            clause_type = self._classify_clause(segment)
            risk_level = self._quick_risk_assessment(segment, clause_type)

            clauses.append(ClauseResult(
                id=idx,
                type=clause_type,
                text=segment,
                risk_level=risk_level,
                warning="",
                related_laws=[],
                conflict_detected=False,
            ))

        return clauses

    def identify_conflicts(self, clauses: list[ClauseResult]) -> list[ClauseResult]:
        """
        Check clauses against Indonesian legal references.

        Args:
            clauses: List of ClauseResult from extract_clauses()

        Returns:
            Updated clauses with conflict detection and related laws
        """
        for clause in clauses:
            detected_issues: list[str] = []
            detected_laws: list[str] = []

            clause_lower = clause.text.lower()

            # Check each law reference
            for law_key, law_info in LEGAL_REFERENCES.items():
                for detail_key, detail in law_info["articles"].items():
                    pattern = detail["pattern"]
                    if re.search(pattern, clause_lower, re.IGNORECASE):
                        detected_issues.append(
                            f"{law_info['title']} - {detail.get('limit', '')}"
                        )
                        detected_laws.append(law_key)
                        clause.conflict_detected = True

            if clause.conflict_detected:
                clause.related_laws = list(set(detected_laws))
                clause.warning = "; ".join(detected_issues)

            # Vector store check for additional conflicts
            if self.use_vector_search and clause.conflict_detected:
                self._check_vector_store_conflicts(clause)

        return clauses

    def assess_risks(self, clauses: list[ClauseResult]) -> list[ClauseResult]:
        """
        Assess and upgrade risk levels for each clause.

        Args:
            clauses: List of ClauseResult (from identify_conflicts)

        Returns:
            Updated clauses with risk levels
        """
        for clause in clauses:
            current_risk = clause.risk_level

            # Check risk patterns
            for risk_key in ("high", "medium", "low"):
                for pattern, reason in RISK_PATTERNS[risk_key]:
                    if re.search(pattern, clause.text, re.IGNORECASE):
                        # Upgrade risk if higher than current
                        risk_order = {"low": 1, "medium": 2, "high": 3}
                        if risk_order[risk_key] > risk_order.get(current_risk, 0):
                            current_risk = risk_key

                        # Append warning
                        if reason and reason not in clause.warning:
                            sep = "; " if clause.warning else ""
                            clause.warning += sep + reason

            clause.risk_level = current_risk

        return clauses

    def generate_summary(self, text: str) -> str:
        """
        Generate an executive summary of the document.

        Args:
            text: Full document text

        Returns:
            Human-readable executive summary in Indonesian
        """
        if not text or not text.strip():
            return "Dokumen kosong. Tidak dapat menghasilkan ringkasan."

        result = self.analyze_document(text)
        s = result.summary

        lines: list[str] = [
            "===== RINGKASAN EKSEKUTIF DOKUMEN HUKUM =====",
            "",
            f"Total Klausul Terdeteksi : {s.total_clauses}",
            f"Klausul Risiko Tinggi   : {s.high_risk}",
            f"Klausul Risiko Sedang   : {s.medium_risk}",
            f"Klausul Risiko Rendah   : {s.low_risk}",
            "",
        ]

        if s.compliance_issues:
            lines.append("MASALAH KEPATUHAN TERDETEKSI:")
            for issue in s.compliance_issues:
                lines.append(f"  - {issue}")
            lines.append("")

        if result.clauses:
            lines.append("TOP RISIKO:")
            for clause in result.clauses:
                if clause.risk_level in ("high", "medium"):
                    lines.append(
                        f"  [Klausul {clause.id}] [{clause.risk_level.upper()}] "
                        f"{clause.type}: {clause.text[:80]}..."
                    )

        doc_type = result.document_type_hint
        if doc_type:
            lines.append(f"\nTipe Dokumen Terdeteksi: {doc_type}")

        lines.append(f"\nDurasi Analisis: {result.analyzed_at}")
        lines.append("=" * 45)

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # PRIVATE HELPERS
    # ------------------------------------------------------------------ #

    def _split_into_segments(self, text: str) -> list[str]:
        """Split document text into clause segments."""
        # Try multiple splitting strategies

        # Strategy 1: Numbered patterns
        # Look for patterns like "Pasal 1", "1.", "a)", "Article 1"
        pattern = r"(?<=\n)(?=\d+\.|Pasal\s+\d+|Article\s+\d+|[IVXivx]+\.|^[a-z]\))"
        segments = [s.strip() for s in re.split(pattern, text) if s.strip()]

        if len(segments) > 2:
            # Reassemble small fragments
            merged = self._merge_small_segments(segments)
            return merged

        # Strategy 2: Split by double newlines
        segments = [s.strip() for s in re.split(r"\n\n+", text) if len(s.strip()) > 20]
        if len(segments) > 1:
            return self._merge_small_segments(segments)

        # Strategy 3: Split by single newlines
        segments = [s.strip() for s in re.split(r"\n+", text) if len(s.strip()) > 30]
        if len(segments) > 2:
            return self._merge_small_segments(segments)

        return [text]

    def _merge_small_segments(self, segments: list[str]) -> list[str]:
        """Merge very short segments with neighbors."""
        merged: list[str] = []
        buffer = ""

        for seg in segments:
            if len(seg) < 30:
                buffer = (buffer + " " + seg).strip()
            else:
                if buffer:
                    merged.append(buffer)
                    buffer = ""
                merged.append(seg)

        if buffer:
            merged.append(buffer)

        return merged

    def _classify_clause(self, text: str) -> str:
        """Classify clause type based on keyword matching."""
        text_lower = text.lower()

        best_type = "lainnya"
        best_score = 0

        for clause_type, keywords in CLAUSE_TYPES.items():
            if clause_type == "lainnya":
                continue
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_type = clause_type

        return best_type

    def _quick_risk_assessment(self, text: str, clause_type: str) -> str:
        """Quick initial risk assessment based on clause type."""
        text_lower = text.lower()

        # Hardcoded high-risk keywords
        high_risk_keywords = [
            "denda per hari", "denda 1%", "1% per hari", "tidak terbatas",
            "tanpa batasan", "pembatalan sepihak", "batalkan sepihak",
            "siapa pun juga", "kebijakan pribadi", "privasi",
            "pidana", "penjara", "hukuman penjara"
        ]
        for kw in high_risk_keywords:
            if kw in text_lower:
                return "high"

        medium_risk_keywords = [
            "arbitrase", "denda", "penalty", "konsekuensi",
            "perpanjangan", "auto renew", "pengalihan",
            "ganti rugi", "komisi"
        ]
        for kw in medium_risk_keywords:
            if kw in text_lower:
                return "medium"

        return "low"

    def _build_summary(self, clauses: list[ClauseResult]) -> AnalysisSummary:
        """Build summary statistics from clauses."""
        high = sum(1 for c in clauses if c.risk_level == "high")
        medium = sum(1 for c in clauses if c.risk_level == "medium")
        low = sum(1 for c in clauses if c.risk_level == "low")

        compliance_issues: list[str] = []
        seen_conflicts: set[str] = set()

        for clause in clauses:
            if clause.conflict_detected and clause.warning:
                for law in clause.related_laws:
                    if law not in seen_conflicts:
                        seen_conflicts.add(law)
                        compliance_issues.append(
                            f"Klausul {clause.id} berbenturan dengan {law}"
                        )

        return AnalysisSummary(
            total_clauses=len(clauses),
            high_risk=high,
            medium_risk=medium,
            low_risk=low,
            compliance_issues=compliance_issues,
        )

    def _detect_document_type(self, text: str) -> str:
        """Detect likely document type from content."""
        text_lower = text.lower()

        type_scores: dict[str, int] = {
            "Perjanjian Kerja Sama (PKS)": 0,
            "Memorandum of Understanding (MoU)": 0,
            "Kontrak Pengadaan Barang/Jasa": 0,
            "Perjanjian Sewa": 0,
            "Perjanjian Pinjaman": 0,
            "Non-Disclosure Agreement (NDA)": 0,
            "General Contract": 0,
        }

        indicators: dict[str, list[str]] = {
            "Perjanjian Kerja Sama (PKS)": [
                "kerja sama", "kerjasama", "mitra", "kolaborasi",
                "para pihak", "pihak pertama", "pihak kedua"
            ],
            "Memorandum of Understanding (MoU)": [
                "mou", "memorandum of understanding", "nota kesepahaman",
                "kehormatan", "non-binding", "maksud dan tujuan"
            ],
            "Kontrak Pengadaan Barang/Jasa": [
                "pengadaan", "barang", "jasa", "pelelangan",
                "kontrak prestasi", "pekerjaan konstruksi", "spk"
            ],
            "Perjanjian Sewa": [
                "sewa", "menyewakan", "rent", "hunian", "gedung",
                "tanah", "kendaraan", "peralatan"
            ],
            "Perjanjian Pinjaman": [
                "pinjaman", "pemberi pinjaman", "penerima pinjaman",
                "bunga", "angsuran", "jatuh tempo", "kredit"
            ],
            "Non-Disclosure Agreement (NDA)": [
                "rahasia", "kerahasiaan", "confidential", "nda",
                "mengungkapkan", "g disclosure", "tidak boleh"
            ],
        }

        for doc_type, keywords in indicators.items():
            for kw in keywords:
                if kw in text_lower:
                    type_scores[doc_type] += 1

        # Sort by score descending
        best = max(type_scores, key=type_scores.get)
        if type_scores[best] == 0:
            return "General Contract"
        return best

    def _check_vector_store_conflicts(self, clause: ClauseResult) -> None:
        """Check clause against vector store for additional conflict detection."""
        if not self.use_vector_search or not self.vector_store:
            return

        try:
            results = self.vector_store.search(clause.text, top_k=3)
            for result in results:
                if result.get("score", 0) > 0.7:
                    # High similarity - potential conflict
                    metadata = result.get("metadata", {})
                    source = metadata.get("title", metadata.get("source", "Unknown"))
                    law_note = f"Similar regulation found: {source}"
                    if law_note not in clause.warning:
                        sep = "; " if clause.warning else ""
                        clause.warning += sep + law_note
                        if source not in clause.related_laws:
                            clause.related_laws.append(source)
        except Exception:
            # Vector store search failed - silently continue
            pass


# =============================================================================
# FACTORY FUNCTION (backward compatible)
# =============================================================================

def create_analyzer(
    vector_store: Any = None,
    use_vector_search: bool = True,
    strict_mode: bool = False
) -> LegalDocumentAnalyzer:
    """
    Factory function to create a LegalDocumentAnalyzer instance.

    Args:
        vector_store: Optional vector store for conflict checking
        use_vector_search: Enable vector store lookup
        strict_mode: Enable stricter risk detection

    Returns:
        LegalDocumentAnalyzer instance
    """
    return LegalDocumentAnalyzer(
        vector_store=vector_store,
        use_vector_search=use_vector_search,
        strict_mode=strict_mode,
    )


# =============================================================================
# DEMO / TESTING
# =============================================================================

SAMPLE_CONTRACT = """
PERJANJIAN KERJA SAMA

antara

PT GOVERNMENT TECH SOLUSI (Pihak Pertama)

dan

PT DIGITAL INOVASI INDONESIA (Pihak Kedua)

Nomor: 012/PKS/GTS/DII/2024

PASAL 1 - DEFINISI DAN PENGERTIAN

1.1. "Para Pihak" adalah PT Government Tech Solusi dan PT Digital Inovasi Indonesia
     yang selanjutnya disebut bersama-sama sebagai "Para Pihak" dan sendiri-sendiri
     sebagai "Pihak".

1.2. "Layanan" adalah seluruh layanan Teknologi Informasi yang diberikan oleh
     Pihak Pertama kepada Pihak Kedua sesuai dengan lingkup perjanjian ini.

1.3. "Data Pribadi" adalah setiap data tentang seseorang baik yang teridentifikasi
     maupun dapat diidentifikasi berdasarkan peraturan perundang-undangan yang berlaku.

1.4. "Force Majeure" adalah setiap kejadian di luar kendali Para Pihak yang
     tidak dapat Diprediksi dan tidak dapat dihindari walau telah采取了 upaya .

PASAL 2 - LINGKUP KERJA SAMA

2.1. Pihak Pertama sepakat memberikan Layanan kepada Pihak Kedua berupa:
     a) Pengembangan sistem informasi government;
     b) Integrasi data dengan sistem resmi;
     c) Pelatihan dan pendampingan pengguna.

2.2. Ruang lingkup pekerjaan sebagaimana dimaksud pada ayat (1) mengacu pada
     lampiran yang merupakan bagian tidak terpisahkan dari perjanjian ini.

PASAL 3 - HAK DAN KEWAJIBAN PARA PIHAK

3.1. Hak Pihak Pertama:
     a) Menerima pembayaran tepat waktu sesuai jadwal yang disepakati;
     b) Mengakses data dan sistem Pihak Kedua yang diperlukan untuk layanan;
     c) Menunjuk pihak ketiga sebagai subkontraktor dengan persetujuan Pihak Kedua.

3.2. Kewajiban Pihak Kedua:
     a) Membayar biaya layanan sesuai ketentuan dalam Pasal 5;
     b) Menyediakan data dan akses yang diperlukan paling lambat 14 hari kerja;
     c) Menunjuk penanggung jawab proyek dalam 7 hari setelah penandatanganan.

3.3. Para Pihak berhak untuk mengubah jadwal dan lingkup kerja sama
     melalui amendemen yang disepakati bersama secara tertulis.

PASAL 4 - BIAYA DAN PEMBAYARAN

4.1. Biaya total layanan adalah Rp 5.000.000.000 (lima miliar rupiah),
     tidak termasuk pajak yang berlaku.

4.2. Pembayaran dilakukan secara bertahap sesuai milestone:
     a) 30% saat penandatanganan perjanjian;
     b) 40% saat completion milestone pertama;
     c) 30% setelah serah terima final.

4.3. Keterlambatan pembayaran dikenai denda 1% (satu persen) per hari
     dari total tagihan yang belum dibayar.

4.4. Para Pihak wajib melakukan rekonsiliasi tagihan setiap bulan
     dan menyelesaikannya dalam waktu 30 hari kalender.

PASAL 5 - JANGKA WAKTU DAN PENGAKHIRAN

5.1. Perjanjian ini berlaku untuk jangka waktu 3 (tiga) tahun, terhitung
     sejak tanggal penandatanganan.

5.2. Perjanjian dapat diperpanjang dengan amendemen tertulis yang
     disepakati Para Pihak paling lambat 60 hari sebelum berakhir.

5.3. Automatic renewal akan berlaku jika tidak ada pemberitahuan
     pembatalan dari salah satu Pihak 90 hari sebelum jatuh tempo.

5.4. Para Pihak dapat mengakhiri perjanjian ini secara sepihak
     dengan pemberitahuan tertulis 30 hari sebelumnya.

PASAL 6 - PENYELESAIAN SENGKETA

6.1. Segala perselisihan yang timbul dari perjanjian ini akan
     diselesaikan melalui musyawarah untuk mufakat.

6.2. Apabila musyawarah tidak mencapai kesepakatan dalam waktu 30 hari,
     sengketa akan diselesaikan melalui Arbitrase sesuai rules BANI
     dengan kursi di Jakarta.

6.3. Keputusan arbitrator bersifat final dan mengikat Para Pihak.

PASAL 7 - LARANGAN DAN PEMBATASAN

7.1. Para Pihak dilarang untuk mengungkapkan informasi rahasia kepada
     pihak ketiga manapun tanpa persetujuan tertulis dari pihak lainnya.

7.2. Pihak Kedua dilarang untuk memindahtangankan hak dan kewajiban
     dari perjanjian ini kepada pihak lain tanpa persetujuan Pihak Pertama.

7.3. Dilarang menggunakan data dari perjanjian ini untuk keperluan
     di luar yang telah disepakati.

PASAL 8 - SANKSI DAN PENALTI

8.1. Pelanggaran atas Pasal 7 akan dikenakan sanksi denda sebesar
     Rp 500.000.000 (lima ratus juta rupiah) per pelanggaran.

8.2. Keterlambatan penyelesaian pekerjaan dikenai penalty 0.5% per hari
     dari nilai kontrak yang tertunda.

8.3. Kegagalan pihak dalam memenuhi kewajiban lebih dari 60 hari
     memberikan hak kepada pihak lainnya untuk membatalkan perjanjian.

8.4. Tidak ada batasan tanggung jawab untuk pelanggaran data pribadi.

PASAL 9 - KEADAAN KAHR (FORCE MAJEURE)

9.1. Tidak satu Pihak pun yang dapat dimintai tanggung jawab atas
     kegagalan выполнения обязательств jika disebabkan oleh Force Majeure.

9.2. Keadaan Force Majeure harus dikomunikasikan secara tertulis
     dalam waktu 14 hari sejak terjadinya kejadian.

PASAL 10 - PENUTUP

10.1. Hal-hal yang belum diatur dalam perjanjian ini akan diatur
      dalam addendum/keterangan tambahan yang merupakan bagian tidak
      terpisahkan dari perjanjian ini.

10.2. Perjanjian ini dibuat dalam rangkap 2 (dua) bermaterai cukup
      dan memiliki kekuatan hukum yang sama.
"""


def _safe_print(text: str, max_len: int = 200) -> None:
    """Print with safe Unicode handling for Windows console."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace problematic chars with ASCII equivalents
        safe = (
            text.replace("—", "--")   # em dash
            .replace("–", "-")         # en dash
            .replace("‘", "'")         # left single quote
            .replace("’", "'")         # right single quote
            .replace("“", '"')         # left double quote
            .replace("”", '"')         # right double quote
        )
        # Remove any remaining non-cp1252 chars
        safe = safe.encode("cp1252", errors="replace").decode("cp1252")
        print(safe)


def run_demo() -> None:
    """Run demonstration of the Legal Document Analyzer."""
    print("=" * 60)
    print("  LEGAL DOCUMENT ANALYZER - INDoGovRAG")
    print("  Indonesian Legal Document Analysis Demo")
    print("=" * 60)
    print()

    # Initialize analyzer (without vector store for standalone demo)
    analyzer = LegalDocumentAnalyzer(use_vector_search=False)

    # Run full analysis
    print("[1] Running full document analysis...")
    result = analyzer.analyze_document(SAMPLE_CONTRACT)

    print(f"    Document type : {result.document_type_hint}")
    print(f"    Total clauses: {result.summary.total_clauses}")
    print(f"    High risk     : {result.summary.high_risk}")
    print(f"    Medium risk   : {result.summary.medium_risk}")
    print(f"    Low risk      : {result.summary.low_risk}")
    print()

    if result.summary.compliance_issues:
        print("[!] COMPLIANCE ISSUES DETECTED:")
        for issue in result.summary.compliance_issues:
            print(f"    - {issue}")
        print()

    # Show clauses by risk level
    print("[2] Clauses by Risk Level:")
    print("-" * 60)
    for clause in result.clauses:
        flag = "[!]" if clause.risk_level in ("high", "medium") else "   "
        _safe_print(f"{flag} [{clause.risk_level.upper():5}] [{clause.type:22}] #{clause.id}")
        _safe_print(f"    {clause.text[:100]}...")
        if clause.warning:
            _safe_print(f"    WARNING: {clause.warning}")
        print()

    # Generate executive summary
    print("[3] Executive Summary:")
    print("-" * 60)
    _safe_print(analyzer.generate_summary(SAMPLE_CONTRACT))

    # Raw JSON output (first 1500 chars)
    print("\n[4] Raw JSON Output (truncated):")
    print("-" * 60)
    json_out = result.to_json(indent=2)
    _safe_print(json_out[:1500] + ("\n... [truncated]" if len(json_out) > 1500 else ""))

    print("\n" + "=" * 60)
    print("  Demo completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()