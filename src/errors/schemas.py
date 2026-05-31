"""
Standardized Error Schema for IndoGovRAG
Defines error types, Indonesian messages, and user suggestions.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import time


class ErrorType(Enum):
    """Standard error types for the IndoGovRAG system."""
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_QUERY = "INVALID_QUERY"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    INITIALIZATION_FAILED = "INITIALIZATION_FAILED"
    PARSE_ERROR = "PARSE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    SYSTEM_OVERLOAD = "SYSTEM_OVERLOAD"


@dataclass
class Suggestion:
    """A user-facing suggestion or tip."""
    id: str
    text: str  # Indonesian text
    action: Optional[str] = None  # Optional action label
    type: str = "general"  # general, query_tweak, retry, contact_support


@dataclass
class ErrorResponse:
    """Standardized error response structure."""
    error_type: str
    code: str  # Short code like "DOC001"
    message: str  # Indonesian user-friendly message
    detail: Optional[str] = None  # Technical detail (optional, API only)
    suggestions: List[Suggestion] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    query: Optional[str] = None
    recoverable: bool = True  # Whether retrying might help

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        # Remove None values for cleaner output
        return {k: v for k, v in d.items() if v is not None}

    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API response format (hides internal details)."""
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "suggestions": [asdict(s) for s in self.suggestions],
            },
            "recoverable": self.recoverable,
            "timestamp": self.timestamp,
        }


# --- Pre-defined error responses in Indonesian ---

def _make_suggestions(*items: tuple) -> List[Suggestion]:
    """Helper to create suggestion lists from tuples."""
    return [
        Suggestion(id=f"sug_{i}", text=text, action=action, type=stype)
        for i, (text, action, stype) in enumerate(items)
    ]


# Error response templates
error_responses: Dict[ErrorType, ErrorResponse] = {
    ErrorType.DOCUMENT_NOT_FOUND: ErrorResponse(
        error_type="DOCUMENT_NOT_FOUND",
        code="DOC001",
        message="Dokumen yang Anda cari tidak ditemukan dalam basis data kami.",
        detail=None,
        suggestions=_make_suggestions(
            ("Coba kata kunci lain yang lebih umum", "Ganti kata kunci", "query_tweak"),
            ("Periksa ejaan pertanyaan Anda", "Periksa ulang", "query_tweak"),
            ("Hubungi admin jika dokumen seharusnya ada", "Hubungi kami", "contact_support"),
        ),
        recoverable=True,
    ),

    ErrorType.LLM_TIMEOUT: ErrorResponse(
        error_type="LLM_TIMEOUT",
        code="LLM001",
        message="Maaf, respons terlalu lama. Kami mengembalikan hasil pencarian dasar sebagai gantinya.",
        detail=None,
        suggestions=_make_suggestions(
            ("Coba pertanyaan yang lebih singkat", "Singkatkan pertanyaan", "query_tweak"),
            ("Sistem sedang sibuk, coba beberapa saat lagi", "Coba lagi nanti", "retry"),
            ("Pilih pertanyaan yang lebih spesifik", "Perkecil topik", "query_tweak"),
        ),
        recoverable=True,
    ),

    ErrorType.RATE_LIMITED: ErrorResponse(
        error_type="RATE_LIMITED",
        code="RATE001",
        message="Terlalu banyak permintaan. Silakan tunggu sebentar sebelum bertanya lagi.",
        detail=None,
        suggestions=_make_suggestions(
            ("Tunggu 30 detik sebelum mengirim pertanyaan baru", "Tunggu sebentar", "retry"),
            ("Kurangi frekuensi pertanyaan", "Kurangi beban", "general"),
            ("Hubungi admin jika Anda membutuhkan akses lebih tinggi", "Hubungi kami", "contact_support"),
        ),
        recoverable=True,
    ),

    ErrorType.INVALID_QUERY: ErrorResponse(
        error_type="INVALID_QUERY",
        code="QUERY001",
        message="Pertanyaan Anda tidak dapat diproses. Pastikan pertanyaan jelas dan terkait dengan dokumen pemerintah Indonesia.",
        detail=None,
        suggestions=_make_suggestions(
            ("Gunakan kata kunci tentang peraturan atau dokumen pemerintah", "Gunakan topik resmi", "query_tweak"),
            ("Pastikan pertanyaan dalam Bahasa Indonesia", "Gunakan Bahasa Indonesia", "query_tweak"),
            ("Hindari pertanyaan yang terlalu umum atau ambigu", "Buat pertanyaan spesifik", "query_tweak"),
        ),
        recoverable=True,
    ),

    ErrorType.RETRIEVAL_FAILED: ErrorResponse(
        error_type="RETRIEVAL_FAILED",
        code="RET001",
        message="Sistem pencarian mengalami masalah. Hasil pencarian dasar tetap ditampilkan.",
        detail=None,
        suggestions=_make_suggestions(
            ("Coba pertanyaan berbeda dengan kata kunci lain", "Ganti topik", "query_tweak"),
            ("Periksa koneksi internet Anda", "Periksa koneksi", "general"),
            ("Hubungi admin jika masalah terus berlanjut", "Hubungi kami", "contact_support"),
        ),
        recoverable=True,
    ),

    ErrorType.INITIALIZATION_FAILED: ErrorResponse(
        error_type="INITIALIZATION_FAILED",
        code="INIT001",
        message="Sistem sedang dalam perbaikan. Silakan coba lagi dalam beberapa menit.",
        detail=None,
        suggestions=_make_suggestions(
            ("Tunggu beberapa menit dan coba lagi", "Coba lagi nanti", "retry"),
            ("Periksa apakah layanan lain berfungsi正常", "Cek status", "general"),
        ),
        recoverable=True,
    ),

    ErrorType.PARSE_ERROR: ErrorResponse(
        error_type="PARSE_ERROR",
        code="PARSE001",
        message="Dokumen tidak dapat diproses dengan benar.",
        detail=None,
        suggestions=_make_suggestions(
            ("Pastikan file dalam format yang didukung (.txt, .pdf, .doc)", "Format yang didukung", "general"),
            ("Coba gunakan file dengan teks yang jelas", "Gunakan dokumen lain", "general"),
        ),
        recoverable=True,
    ),

    ErrorType.CONFIGURATION_ERROR: ErrorResponse(
        error_type="CONFIGURATION_ERROR",
        code="CFG001",
        message="Konfigurasi sistem bermasalah. Tim teknis telah diberitahu.",
        detail=None,
        suggestions=_make_suggestions(
            ("Tim teknis sedang menangani masalah ini", "Menunggu perbaikan", "general"),
        ),
        recoverable=False,
    ),

    ErrorType.SYSTEM_OVERLOAD: ErrorResponse(
        error_type="SYSTEM_OVERLOAD",
        code="SYS001",
        message="Server sedang mengalami beban tinggi. Silakan coba lagi nanti.",
        detail=None,
        suggestions=_make_suggestions(
            ("Kurangi jumlah permintaan dalam waktu dekat", "Kurangi beban", "retry"),
            ("Coba lagi dalam 5-10 menit", "Tunggu sebentar", "retry"),
        ),
        recoverable=True,
    ),
}


# --- Helper functions ---

def get_error_response(error_type: ErrorType, query: Optional[str] = None) -> ErrorResponse:
    """Get a pre-defined error response, optionally tagged with the query."""
    err = error_responses.get(error_type, error_responses[ErrorType.INVALID_QUERY])
    err.query = query
    err.timestamp = time.time()
    return err


def create_error_response(
    error_type: ErrorType,
    message: Optional[str] = None,
    detail: Optional[str] = None,
    suggestions: Optional[List[Dict[str, str]]] = None,
    recoverable: bool = True,
    query: Optional[str] = None,
) -> ErrorResponse:
    """Create a custom error response, overriding defaults."""
    base = error_responses.get(error_type, error_responses[ErrorType.INVALID_QUERY])
    return ErrorResponse(
        error_type=error_type.value,
        code=base.code,
        message=message or base.message,
        detail=detail,
        suggestions=[
            Suggestion(
                id=s.get('id', f"custom_{i}"),
                text=s['text'],
                action=s.get('action'),
                type=s.get('type', 'general')
            )
            for i, s in enumerate(suggestions or [])
        ],
        recoverable=recoverable,
        query=query,
        timestamp=time.time()
    )


def create_success_response(
    answer: str,
    sources: List[str],
    confidence: float,
    latency_ms: float,
    metadata: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a standardized success response with optional warnings."""
    response = {
        "success": True,
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "metadata": metadata or {},
    }
    if warnings:
        response["warnings"] = warnings
    return response


def create_fallback_response(
    original_error: ErrorType,
    bm25_answer: str,
    chunks: List[Dict],
    query: str,
) -> Dict[str, Any]:
    """Create a fallback response when LLM fails — BM25-only with notice."""
    warning_msg = get_error_response(original_error, query).message
    return {
        "success": True,
        "answer": bm25_answer,
        "sources": [],
        "confidence": 0.0,
        "latency_ms": 0,
        "metadata": {
            "chunks_retrieved": len(chunks),
            "fallback_mode": True,
            "error_code": error_responses[original_error].code,
        },
        "warnings": [
            warning_msg,
            "Jawaban ini dihasilkan dari pencarian dasar (tanpa AI lanjutan). "
            "Hasil mungkin kurang lengkap.",
        ],
        "suggestions": [
            {"id": "sug_retry", "text": "Coba pertanyaan lain", "action": "Coba lagi", "type": "retry"},
            {"id": "sug_contact", "text": "Hubungi admin jika masalah berlanjut", "action": "Hubungi kami", "type": "contact_support"},
        ]
    }


# --- Low-confidence warning helpers ---

LOW_CONFIDENCE_THRESHOLD = 0.4


def check_confidence_warnings(confidence: float) -> List[str]:
    """Return Indonesian warning messages based on confidence level."""
    warnings = []
    if confidence < 0.2:
        warnings.append("⚠️ Tingkat keyakinan sangat rendah. Jawaban mungkin tidak akurat.")
    elif confidence < LOW_CONFIDENCE_THRESHOLD:
        warnings.append("⚠️ Tingkat keyakinan rendah. Silakan verifikasi informasi dari sumber resmi.")
    return warnings


def check_chunk_count_warning(chunks: List) -> Optional[str]:
    """Return a warning if no chunks were retrieved."""
    if not chunks or len(chunks) == 0:
        return ("Tidak ada dokumen yang cocok dengan pertanyaan Anda. "
                "Coba gunakan kata kunci lain atau表述 yang lebih spesifik.")
    return None


# --- Superseded document warning ---

SUPERSEDED_WARNING_BANNER = (
    "⚠️ PERHATIAN: Dokumen yang digunakan mungkin sudah tidak berlaku. "
    "Silakan periksa peraturan terbaru sebelum menggunakan informasi ini."
)


def check_superseded_document(sources: List[Dict]) -> Optional[str]:
    """Check if any source document is marked as superseded."""
    for source in sources:
        status = source.get('metadata', {}).get('status', '')
        if status in ('superseded', 'expired', 'replaced'):
            return SUPERSEDED_WARNING_BANNER
    return None