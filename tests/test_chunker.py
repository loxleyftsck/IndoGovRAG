"""
Unit Tests for Document Chunking (src/data/chunker.py)
Tests: paragraph splitting, sentence splitting, token counting,
       semantic chunking, coherence scoring, metadata detection
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.data.chunker import DocumentChunker, Chunk


# =============================================================================
# Helper Fixtures
# =============================================================================

@pytest.fixture
def chunker():
    """Create a default chunker for tests."""
    return DocumentChunker(chunk_size=150, overlap=20, min_chunk_size=30)


@pytest.fixture
def small_chunker():
    """Create a small chunker for edge case tests."""
    return DocumentChunker(chunk_size=50, overlap=10, min_chunk_size=20)


# =============================================================================
# Token Counting
# =============================================================================

class TestTokenCounting:
    def test_count_tokens_single_word(self, chunker):
        result = chunker._count_tokens("KTP")
        assert result >= 1

    def test_count_tokens_phrase(self, chunker):
        result = chunker._count_tokens("Kartu Tanda Penduduk Indonesia")
        assert result >= 3

    def test_count_tokens_empty_string(self, chunker):
        result = chunker._count_tokens("")
        assert result == 0

    def test_count_tokens_long_text(self, chunker):
        text = " ".join(["kata"] * 100)
        result = chunker._count_tokens(text)
        assert result > 50


# =============================================================================
# Paragraph Splitting
# =============================================================================

class TestParagraphSplitting:
    def test_split_double_newline_paragraphs(self, chunker):
        text = "Paragraf satu.\n\nParagraf dua.\n\nParagraf tiga."
        result = chunker._split_paragraphs(text)
        assert len(result) == 3
        assert "Paragraf satu" in result[0]

    def test_split_removes_empty_paragraphs(self, chunker):
        text = "A\n\n\n\n\nB"
        result = chunker._split_paragraphs(text)
        assert "" not in result
        assert len(result) == 2

    def test_split_single_paragraph(self, chunker):
        text = "Hanya satu paragraf tanpa pemisah."
        result = chunker._split_paragraphs(text)
        assert len(result) == 1

    def test_split_strips_whitespace(self, chunker):
        text = "   \n   Spasi luar   \n   "
        result = chunker._split_paragraphs(text)
        assert all(p.strip() == p for p in result)


# =============================================================================
# Sentence Splitting
# =============================================================================

class TestSentenceSplitting:
    def test_split_sentences_period(self, chunker):
        text = "Kalimat pertama. Kalimat kedua! Apakah kamu?"
        result = chunker._split_sentences(text)
        assert len(result) >= 3

    def test_split_preserves_content(self, chunker):
        text = "Ayam. Kucing. Anjing."
        result = chunker._split_sentences(text)
        assert "Ayam" in result[0]
        assert "Kucing" in result[1]

    def test_split_empty_input(self, chunker):
        result = chunker._split_sentences("")
        assert result == []

    def test_split_no_punctuation(self, chunker):
        text = "Tidak ada tanda baca di sini"
        result = chunker._split_sentences(text)
        # Returns single item when no split
        assert len(result) >= 1


# =============================================================================
# Basic Chunking
# =============================================================================

class TestBasicChunking:
    def test_chunk_returns_list(self, chunker):
        text = "Ini adalah dokumen yang cukup panjang untuk di-chunk menjadi beberapa bagian."
        result = chunker.chunk(text, "doc1", {})
        assert isinstance(result, list)

    def test_chunk_returns_chunk_objects(self, chunker):
        text = "Kalimat satu. Kalimat dua. Kalimat tiga. Kalimat empat. Kalimat lima."
        result = chunker.chunk(text, "doc2", {})
        assert len(result) > 0
        assert all(isinstance(c, Chunk) for c in result)

    def test_chunk_doc_id_set(self, chunker):
        text = "A" * 500
        result = chunker.chunk(text, "perpres_26_2009", {})
        for chunk in result:
            assert chunk.doc_id == "perpres_26_2009"

    def test_chunk_metadata_passed(self, chunker):
        text = "Contoh teks."
        meta = {"doc_type": "Perpres", "year": "2009"}
        result = chunker.chunk(text, "doc3", meta)
        if result:
            assert result[0].metadata.get("doc_type") == "Perpres"
            assert result[0].metadata.get("year") == "2009"

    def test_chunk_empty_text_returns_empty(self, chunker):
        result = chunker.chunk("", "doc_empty", {})
        assert result == []

    def test_chunk_short_text_single_chunk(self, chunker):
        text = "Dokumen pendek."
        result = chunker.chunk(text, "doc4", {})
        assert len(result) == 1

    def test_chunk_multiple_paragraphs(self, chunker):
        text = "Paragraf pertama.\n\nParagraf kedua.\n\nParagraf ketiga."
        result = chunker.chunk(text, "doc5", {})
        assert len(result) >= 1

    def test_chunk_very_long_text(self, chunker):
        text = "Kalimat pengujian. " * 100
        result = chunker.chunk(text, "doc_long", {})
        assert len(result) > 1


# =============================================================================
# Metadata Detection
# =============================================================================

class TestMetadataDetection:
    def test_has_title_uppercase(self, chunker):
        assert chunker._has_title("PERATURAN PRESIDEN NOMOR 26 TAHUN 2009")
        assert not chunker._has_title("ini adalah paragraf biasa")

    def test_has_title_bab_pattern(self, chunker):
        assert chunker._has_title("BAB I KETENTUAN UMUM")
        assert chunker._has_title("Pasal 1")
        assert chunker._has_title("Bagian Kedua")

    def test_has_title_lowercase_start(self, chunker):
        assert not chunker._has_title("tidak ada judul di sini")

    def test_has_list_numbered(self, chunker):
        text = "1. Item pertama\n2. Item kedua\n3. Item ketiga"
        assert chunker._has_list(text)

    def test_has_list_bullet(self, chunker):
        text = "- Item satu\n- Item dua"
        assert chunker._has_list(text)

    def test_has_list_false(self, chunker):
        text = "Ini adalah teks biasa tanpa daftar."
        assert not chunker._has_list(text)

    def test_has_numbers_true(self, chunker):
        text = "Pasal 1 mengatur tentang hal penting."
        assert chunker._has_numbers(text)

    def test_has_numbers_false(self, chunker):
        text = "Tidak ada angka di sini"
        assert not chunker._has_numbers(text)


# =============================================================================
# Overlap Text
# =============================================================================

class TestOverlapText:
    def test_overlap_empty_chunks(self, chunker):
        result = chunker._get_overlap_text([])
        assert result == ""

    def test_overlap_single_chunk(self, chunker):
        result = chunker._get_overlap_text(["Satu"])
        assert result == "Satu"

    def test_overlap_returns_last_chunk(self, chunker):
        chunks = ["First", "Second", "Third paragraph"]
        result = chunker._get_overlap_text(chunks)
        assert "Third" in result


# =============================================================================
# Coherence Scoring
# =============================================================================

class TestCoherenceScoring:
    def test_coherence_complete_sentence(self, chunker):
        chunk = Chunk(
            text="PERATURAN PRESIDEN REPUBLIK INDONESIA.",
            doc_id="doc1", chunk_id=0,
            start_char=0, end_char=50,
            num_tokens=10,
            metadata={"has_title": True}
        )
        score = chunker.calculate_coherence(chunk)
        assert 0.0 <= score <= 1.0

    def test_coherence_lowercase_start_penalty(self, chunker):
        chunk = Chunk(
            text="kalimat ini dimulai dengan huruf kecil dan tidak ada judul.",
            doc_id="doc2", chunk_id=0,
            start_char=0, end_char=80,
            num_tokens=20,
            metadata={}
        )
        score = chunker.calculate_coherence(chunk)
        assert score < 1.0

    def test_coherence_no_ending_punctuation_penalty(self, chunker):
        chunk = Chunk(
            text="Teks ini tidak diakhiri tanda baca",
            doc_id="doc3", chunk_id=0,
            start_char=0, end_char=40,
            num_tokens=15,
            metadata={}
        )
        score = chunker.calculate_coherence(chunk)
        assert score < 1.0

    def test_coherence_title_bonus(self, chunker):
        chunk = Chunk(
            text="BAB I KETENTUAN UMUM.",
            doc_id="doc4", chunk_id=0,
            start_char=0, end_char=30,
            num_tokens=35,  # Above min_chunk_size (30) to avoid short-chunk penalty
            metadata={"has_title": True}
        )
        score = chunker.calculate_coherence(chunk)
        assert score >= 1.0

    def test_coherence_very_short_chunk_penalty(self, chunker):
        chunk = Chunk(
            text="x.",  # Lowercase to trigger start penalty (-0.2) + short penalty (-0.3) = 0.5 < 0.7
            doc_id="doc5", chunk_id=0,
            start_char=0, end_char=2,
            num_tokens=1,
            metadata={}
        )
        score = chunker.calculate_coherence(chunk)
        assert score < 0.7

    def test_coherence_bounded_0_1(self, chunker):
        # Should never be negative or above 1
        for _ in range(20):
            text = "Kata " * 5
            chunk = Chunk(
                text=text, doc_id="doc6", chunk_id=0,
                start_char=0, end_char=len(text),
                num_tokens=15,
                metadata={"has_title": False}
            )
            score = chunker.calculate_coherence(chunk)
            assert 0.0 <= score <= 1.0


# =============================================================================
# Chunk Properties
# =============================================================================

class TestChunkProperties:
    def test_chunk_has_incremental_ids(self, chunker):
        text = "A" * 200 + "\n\n" + "B" * 200 + "\n\n" + "C" * 200
        result = chunker.chunk(text, "doc_ids", {})
        ids = [c.chunk_id for c in result]
        assert ids == sorted(ids)

    def test_chunk_char_positions(self, chunker):
        text = "Paragraph one here.\n\nParagraph two here."
        result = chunker.chunk(text, "doc_pos", {})
        for chunk in result:
            assert chunk.end_char >= chunk.start_char

    def test_chunk_token_count_positive(self, chunker):
        text = "Ini teks yang cukup panjang untuk punya token."
        result = chunker.chunk(text, "doc_token", {})
        for chunk in result:
            assert chunk.num_tokens >= 0


# =============================================================================
# Edge Cases
# =============================================================================

class TestChunkerEdgeCases:
    def test_chunk_only_whitespace(self, chunker):
        result = chunker.chunk("   \n\n   \n", "doc_ws", {})
        # whitespace-only may return empty list or single chunk
        assert isinstance(result, list)

    def test_chunk_single_word(self, chunker):
        result = chunker.chunk("KTP", "doc_word", {})
        # Single word may be too small (under min_chunk_size)
        assert isinstance(result, list)

    def test_chunk_with_special_characters(self, chunker):
        text = "Pasal 1@#$%\n\nItem 2!@#%\n\nData &^"
        result = chunker.chunk(text, "doc_special", {})
        assert isinstance(result, list)

    def test_chunk_indonesian_text(self, chunker):
        text = """
        KETENTUAN UMUM

        Pasal 1
        Dalam peraturan ini yang dimaksud dengan:

        1. Kartu Tanda Penduduk yang selanjutnya disingkat KTP adalah identitas resmi.
        2. Nomor Induk Kependudukan yang selanjutnya disingkat NIK.
        3. Database Kependudukan adalah kumpulan data secara sistematis.
        """
        result = chunker.chunk(text, "perpres_26_2009", {"doc_type": "Perpres"})
        assert len(result) > 0
        # All chunks should have doc_type in metadata
        for chunk in result:
            assert chunk.metadata.get("doc_type") == "Perpres"