"""
Brand Taglines for IndoGovRAG Platform.
Indonesian legal AI platform — authoritative, inspiring, and memorable.
"""

TAGLINES: list[str] = [
    "Regulasi Resmi. Jawaban Instan.",
    "Hukum yang Jelas. Negara yang Kuat.",
    "Cerdas. Cepat. Terverifikasi.",
    "AI untuk Keadilan.",
    "Pancasila dalam Setiap Regulasi.",
    "Tanya Hukum, Temukan Regulasi.",
    "Dari Ribuan Regulasi, Satu Jawaban.",
    "Regulasi Indonesia. AI memahami Nuansa.",
    "Hukum untuk Rakyat, Dilayani Teknologi.",
    "Ketika AI Memahami Hukum Indonesia.",
    "Kebenaran Regulasi. Kecepatan AI.",
    "Hukum yang Terbuka untuk Semua.",
    "Satu Platform. Ribuan Regulasi.",
    "AI Bertanya, Regulasi Menjawab.",
    "Cerdas Hukum. Cepat Akses.",
]


def get_random_tagline() -> str:
    """Return a random tagline."""
    import random
    return random.choice(TAGLINES)


def get_tagline_by_index(index: int) -> str:
    """Return a tagline by its index (useful for rotation)."""
    return TAGLINES[index % len(TAGLINES)]
