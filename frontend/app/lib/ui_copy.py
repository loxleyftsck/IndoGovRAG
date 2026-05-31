"""
Indonesian UI Microcopy, Cool Quotes, and Inspirational Text for IndoGovRAG.
All text is in Bahasa Indonesia — authoritative, inspiring, and authentic.
"""

from typing import TypedDict


class HeroQuote(TypedDict):
    text: str
    author: str
    context: str


class UICopy(TypedDict):
    homepage: dict
    search: dict
    results: dict
    legal_philosophy: dict
    errors: dict
    filters: dict
    pagination: dict
    confidence: dict
    doc_types: dict
    status: dict
    navigation: dict


# ─── Core UI Copy ─────────────────────────────────────────────────────────────

UI_COPY: UICopy = {
    "homepage": {
        "hero_headline": "Pencarian Regulasi Indonesia yang Akurat & Terpercaya",
        "hero_subhead": (
            "Telusuri ribuan dokumen hukum Indonesia dengan kecerdasan buatan — "
            "dari Undang-Undang hingga Peraturan Menteri"
        ),
        "hero_placeholder": "Ketik pertanyaan hukum Anda di sini...",
        "hero_cta": "Mulai Pencarian",
        "hero_secondary": "Atau telusuri kategori",
        "stats_label": "chunk terindeks",
        "stats_docs": "dokumen",
        "feature_cepat_title": "Cepat & Akurat",
        "feature_cepat_desc": "Respons waktu di bawah 100ms dengan intelligent caching dan hybrid search",
        "feature_ai_title": "AI-Powered",
        "feature_ai_desc": "Hybrid search + LLM re-ranking untuk akurasi maksimal dalam pencarian hukum",
        "feature_gratis_title": "100% Gratis",
        "feature_gratis_desc": "Biaya operasional Rp0 dengan efisiensi 40% lebih tinggi dari metode tradisional",
        "feature_cta": "Coba sekarang",
        "popular_label": "Pencarian populer:",
    },

    "search": {
        "empty_title": "Mulai Pencarian Dokumen Hukum",
        "empty_subtitle": (
            "Gunakan filter untuk mempersempit hasil atau ketik pertanyaan Anda secara spesifik"
        ),
        "loading_text": "Menganalisis regulasi terkait...",
        "no_results": "Tidak ditemukan regulasi yang relevan",
        "no_results_tip": "Coba gunakan istilah yang lebih umum atau kurang spesifik",
        "loading_short": "Memuat...",
        "refine_hint": "Coba kata kunci lain atau perluas pencarian Anda",
        "recent_searches": "Pencarian Terbaru",
        "clear_history": "Hapus Riwayat",
    },

    "results": {
        "confidence_label": "Tingkat Kepercayaan",
        "relevance_label": "Tingkat Relevansi",
        "source_label": "Sumber Resmi",
        "citation_prefix": "Merujuk pada",
        "disclaimer": (
            "Informasi ini bersifat referensi. Untuk kepastian hukum, "
            "konsultasikan dengan ahli hukum."
        ),
        "high_confidence_note": (
            "Jawaban ini didukung oleh regulasi resmi dengan tingkat kepercayaan tinggi"
        ),
        "low_confidence_note": (
            "Jawaban ini berdasarkan regulasi yang mungkin sudah diubah atau dicabut. "
            "Verifikasi dengan sumber resmi."
        ),
        "answer_label": "Jawaban",
        "sources_label": "Referensi Sumber",
        "sources_count": "sumber",
        "view_sources": "Lihat daftar sumber",
        "cached_badge": "Cached",
        "hybrid_badge": "Hibrida",
        "basic_mode_badge": "Mode Dasar",
        "confidence_stat": "Confidence",
        "latency_stat": "Waktu Respons",
        "chunks_stat": "Chunks",
        "features_stat": "Fitur",
        "expand_badge": "Expand",
        "rerank_badge": "Rerank",
        "helpful_question": "Apakah jawaban ini membantu?",
        "helpful_yes": "Ya, membantu",
        "helpful_no": "Tidak",
        "no_sources_available": "Tidak ada sumber tersedia",
        "no_sources_note": "Informasi ditampilkan tanpa referensi dokumen.",
    },

    "legal_philosophy": {
        "tagline": '"Hukum tanpa keadilan adalah neraka tanpa penjaga"',
        "attribution": "— Konsep Hukum Indonesia",
        "footer_note": (
            "Didukung oleh kecerdasan buatan dengan verifikasi dari dokumen hukum resmi"
        ),
        "system_status": (
            "Sistem RAG aktif — mengambil dari basis data regulasi nasional"
        ),
        "powered_by": "Didukung oleh AI",
        "verification_note": "Verifikasi dari dokumen hukum resmi",
    },

    "errors": {
        "timeout": (
            "Waktu pencarian habis. Regulasi yang Anda cari mungkin memerlukan "
            "waktu lebih lama untuk diambil."
        ),
        "not_found": "Regulasi tidak ditemukan dalam database kami.",
        "rate_limit": "Terlalu banyak permintaan. Silakan tunggu sebentar.",
        "generic": "Terjadi kesalahan sistem. Tim kami sudah diberitahu.",
        "network": "Tidak dapat terhubung ke server",
        "network_tip": "Pastikan server backend berjalan di http://localhost:8000",
        "server_error": "Terjadi kesalahan server",
        "server_error_tip": "Server tidak dapat memproses permintaan Anda",
        "error_detail": "Lihat detail error",
        "retry": "Coba lagi",
        "view_results": "Lihat hasil pencarian",
        "try_these": "Mungkin perlu dicoba:",
    },

    "filters": {
        "active_filters": "Filter Aktif",
        "clear_all": "Hapus Semua",
        "no_filter": "Tidak ada filter aktif",
        "result_count": "{count} regulasi ditemukan",
        "filter_by_type": "Filter berdasarkan jenis",
        "filter_by_year": "Filter berdasarkan tahun",
        "filter_by_status": "Filter berdasarkan status",
        "filter_by_instansi": "Filter berdasarkan instansi",
        "year_range": "Rentang Tahun",
    },

    "pagination": {
        "showing": "Menampilkan {start}–{end} dari {total}",
        "prev": "Sebelumnya",
        "next": "Selanjutnya",
        "page": "Halaman {current} dari {total}",
        "first": "Pertama",
        "last": "Terakhir",
    },

    "confidence": {
        "very_high": "Sangat Yakin",
        "high": "Yakin",
        "medium": "Cukup Yakin",
        "low": "Kurang Yakin",
        "very_low": "Tidak Yakin",
    },

    "doc_types": {
        "UU": "Undang-Undang Dasar / Undang-Undang",
        "PP": "Peraturan Pemerintah",
        "Perpres": "Peraturan Presiden",
        "Permen": "Peraturan Menteri",
        "Perda": "Peraturan Daerah",
        "POJK": "Peraturan Otoritas Jasa Keuangan",
        "SE": "Surat Edaran",
    },

    "status": {
        "berlaku": "Berlaku",
        "direvisi": "Sedang Direvisi",
        "dicabut": "Sudah Dicabut",
    },

    "navigation": {
        "home": "Beranda",
        "search": "Pencarian",
        "about": "Tentang",
        "contact": "Kontak",
        "docs": "Dokumentasi",
    },

    "history": {
        "title": "Riwayat Pencarian",
        "count_label": "pertanyaan",
        "empty_title": "Belum ada riwayat",
        "empty_note": "Pertanyaan yang Anda tanya akan muncul di sini",
        "clear_all": "Hapus Semua",
        "close": "Tutup riwayat",
        "helpful_tag": "Membantu",
        "not_helpful_tag": "Kurang membantu",
    },

    "loading": {
        "searching_docs": "Mencari dokumen relevan...",
        "processing_query": "Memproses pertanyaan Anda...",
        "fetching_sources": "Mengambil sumber informasi...",
        "query_understanding": "Memahami pertanyaan Anda...",
        "retrieval": "Mengambil dokumen regulasi...",
        "legal_reasoning": "Menganalisis konteks hukum...",
        "synthesis": "Merangkai jawaban dari sumber resmi...",
    },

    "warnings": {
        "timeout_soft": "Proses memerlukan waktu lebih lama...",
        "timeout_hard": "Waktu respons habis — menampilkan hasil dasar",
        "timeout_hard_sub": "Server memerlukan waktu lebih dari 15 detik. Hasil pencarian dasar ditampilkan.",
        "timeout_soft_sub": "Sudah berjalan selama {elapsed} detik. Harap tunggu...",
        "low_confidence": "Tingkat keyakinan rendah",
        "very_low_confidence": "Tingkat keyakinan sangat rendah",
        "verify_source": "Silakan verifikasi informasi dari sumber resmi.",
        "very_low_verify": "Jawaban mungkin tidak akurat. Silakan verifikasi informasi dari sumber resmi.",
        "no_chunks": "Tidak ada dokumen yang ditemukan",
        "no_chunks_sub": "Tidak ada dokumen yang cocok dengan pertanyaan Anda. Coba gunakan kata kunci lain.",
        "superseded": "PERHATIAN: Dokumen mungkin sudah tidak berlaku",
        "superseded_sub": (
            "Dokumen yang digunakan sebagai sumber mungkin sudah digantikan atau tidak berlaku lagi. "
            "Silakan periksa peraturan terbaru sebelum menggunakan informasi ini."
        ),
        "fallback": "Jawaban dari pencarian dasar (tanpa AI lanjutan)",
        "retry_button": "Coba lagi",
        "reload_button": "Muat ulang halaman",
    },
}


# ─── Rotating Hero Quotes ─────────────────────────────────────────────────────

HERO_QUOTES: list[HeroQuote] = [
    {
        "text": '"Tidak ada negara tanpa hukum, tidak ada hukum tanpa negara"',
        "author": "Karl Olivecrona",
        "context": "Teori Hukum Realis Skandinavia",
    },
    {
        "text": '"Keadilan bukan hanya tentang memberi setiap orang apa yang menjadi haknya, tetapi juga memastikan hukum diterapkan secara adil bagi semua"',
        "author": "Konsep Hukum Pancasila",
        "context": "Sila ke-4: Kerakyatan",
    },
    {
        "text": '"Hukum progresif adalah hukum yang berkeadilan — hukum yang tidak hanya berlaku secara formil, tetapi juga memenuhi rasa keadilan masyarakat"',
        "author": "Prof. Dr. Satjipto Rahardjo",
        "context": "Teori Hukum Progresif",
    },
    {
        "text": '"Negara hukum yang sejati adalah negara yang menempatkan hukum sebagai panglima tertinggi, bukan kekuasaan atau kehendak seorang individu"',
        "author": "Prof. Dr. Mochtar Kusumaatmadja",
        "context": "Mantan Ketua Mahkamah Konstitusi",
    },
    {
        "text": '"Pancasila adalah dasar negara yang memberi arah pada seluruh hukum Indonesia. Tanpa Pancasila, hukum kehilangan jiwanya"',
        "author": "Prof. Dr. Jimly Asshiddiqie",
        "context": "Guru Besar Hukum Tata Negara UI",
    },
    {
        "text": '"Hukum adat tidak tertulis tetapi berlaku living law — hukum yang hidup dalam masyarakat. Ketidaktertulisannya bukan berarti ketidakberlakuan"',
        "author": "Prof. Dr. Soerojo Wignyodipuro",
        "context": "Guru Besar Hukum Adat",
    },
    {
        "text": '"Hukum harus bersifat adil, bijaksana, dan bermanfaat bagi rakyat. Tanpa ketiganya, hukum hanya akan menjadi sekadar teks tanpa jiwa"',
        "author": "M. Yahya Harahap",
        "context": "Hakim Agung & Pakar Hukum Acara",
    },
    {
        "text": '"Permusyawaratan adalah jiwa dari demokrasi Indonesia. Dalam hukum, musyawarah berarti mencari keadilan substantif, bukan sekadar prosedural"',
        "author": "Prof. Dr. Jimly Asshiddiqie",
        "context": "Guru Besar Hukum Tata Negara UI",
    },
    {
        "text": '"Pembagian kekuasaan bukan sekadar teknis, melainkan penjamin bahwa kebebasan individu tidak dapat diabaikan oleh satu tangan kekuasaan saja"',
        "author": "Charles-Louis de Secondat, Baron de Montesquieu",
        "context": "Teori Pemisahan Kekuasaan",
    },
    {
        "text": '"Hukum Indonesia dibangun di atas tiga sendi: hukum adat, hukum Islam, dan hukum Barat (BW). Ketiganya saling memperkaya"',
        "author": "Prof. Dr. Soerojo Wignyodipuro",
        "context": "Guru Besar Hukum Adat",
    },
]


# ─── Motivational Subtitles ───────────────────────────────────────────────────

MOTIVATIONAL_SUBTITLE: list[str] = [
    "Karena hukum yang jelas = negara yang kuat",
    "Satu pertanyaan, ribuan regulasi dalam hitungan detik",
    "Regulasi resmi, jawaban instan",
    "Pancasila tertanam dalam setiap regulasi",
    "Hukum untuk semua, keadilan untuk setiap orang",
    "AI memahami hukum Indonesia secara mendalam",
    "Dari UUD 1945 hingga Perda — satu platform untuk semuanya",
    "Bertanya hukum, jawaban dari regulasi resmi",
]


# ─── Agent Stage Labels (for loading states) ─────────────────────────────────

AGENT_STAGES: list[str] = [
    "Memahami pertanyaan Anda...",
    "Mengambil dokumen regulasi...",
    "Menganalisis konteks hukum...",
    "Merangkai jawaban dari sumber resmi...",
]


# ─── Helper Functions ─────────────────────────────────────────────────────────

def get_ui_copy(section: str, key: str | None = None) -> str | dict:
    """Get a specific UI copy text by section and optional key."""
    section_data = UI_COPY.get(section, {})
    if key:
        return section_data.get(key, "")
    return section_data


def get_random_hero_quote() -> HeroQuote:
    """Return a random hero quote."""
    import random
    return random.choice(HERO_QUOTES)


def get_random_motivational_subtitle() -> str:
    """Return a random motivational subtitle."""
    import random
    return random.choice(MOTIVATIONAL_SUBTITLE)


def format_pagination(showing: str, start: int, end: int, total: int) -> str:
    """Format pagination string with interpolated values."""
    return showing.format(start=start, end=end, total=total)


def format_result_count(count: int) -> str:
    """Format result count string."""
    return UI_COPY["filters"]["result_count"].format(count=count)
