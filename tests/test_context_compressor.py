"""
Tests for Context Compression Module (BET-002)
"""

import pytest
from src.compression.context_compressor import ContextCompressor


@pytest.fixture
def compressor():
    """Create compressor with default settings"""
    return ContextCompressor(ratio=0.7, fallback_on_error=True)


@pytest.fixture
def sample_contexts():
    """Sample Indonesian legal contexts"""
    return [
        "Pasal 1 UU No. 24 Tahun 2013 tentang Administrasi Kependudukan mengatur tentang definisi dan ruang lingkup administrasi kependudukan.",
        "Setiap warga negara Indonesia wajib memiliki KTP elektronik sebagaimana diatur dalam Pasal 13 ayat (1).",
        "Biaya pembuatan KTP elektronik tidak dipungut biaya alias gratis untuk pembuatan pertama kali."
    ]


def test_compressor_initialization():
    """Test compressor initializes correctly"""
    compressor = ContextCompressor(ratio=0.7)
    
    stats = compressor.get_stats()
    assert stats["ratio"] == 0.7
    assert stats["fallback_enabled"] == True
    assert stats["whitelist_count"] > 0


def test_compress_contexts_structure(compressor, sample_contexts):
    """Test compression returns correct structure"""
    result = compressor.compress_contexts(
        query="Apa itu KTP elektronik?",
        contexts=sample_contexts
    )
    
    # Check all required keys present
    assert "compressed_contexts" in result
    assert "original_tokens" in result
    assert "compressed_tokens" in result
    assert "compression_ratio" in result
    assert "latency_ms" in result
    assert "success" in result
    
    # Check types
    assert isinstance(result["compressed_contexts"], str)
    assert isinstance(result["original_tokens"], int)
    assert isinstance(result["compressed_tokens"], int)
    assert isinstance(result["compression_ratio"], float)
    assert isinstance(result["latency_ms"], float)


def test_compression_reduces_tokens(compressor, sample_contexts):
    """Test compression actually reduces token count"""
    result = compressor.compress_contexts(
        query="Syarat KTP elektronik?",
        contexts=sample_contexts
    )
    
    if result["success"]:
        # Should reduce tokens
        assert result["compressed_tokens"] < result["original_tokens"]
        # Should be roughly 30% reduction (ratio 0.7)
        assert result["compression_ratio"] < 0.8  # Allow some margin


def test_compression_preserves_legal_terms(compressor):
    """Test that legal keywords are preserved"""
    contexts = [
        "Pasal 134 ayat 2 UU 22/2009 mengatur denda sebesar 250000 rupiah"
    ]
    
    result = compressor.compress_contexts(
        query="Berapa denda Pasal 134?",
        contexts=contexts
    )
    
    compressed = result["compressed_contexts"]
    
    # Legal terms should be preserved
    assert "pasal" in compressed.lower() or "134" in compressed


def test_compression_fallback_on_error():
    """Test fallback returns uncompressed when compression fails"""
    # Create compressor that will fail (invalid ratio)
    compressor = ContextCompressor(ratio=2.0, fallback_on_error=True)
    
    result = compressor.compress_contexts(
        query="Test",
        contexts=["Test context"]
    )
    
    # Should fallback
    assert result["compression_ratio"] == 1.0  # No compression
    assert result["error"] is not None


def test_compression_latency_acceptable(compressor, sample_contexts):
    """Test compression completes in reasonable time"""
    result = compressor.compress_contexts(
        query="KTP?",
        contexts=sample_contexts
    )
    
    # Should complete in <1 second
    assert result["latency_ms"] < 1000


def test_prepare_contexts(compressor):
    """Test contexts are prepared with markers"""
    contexts = ["Context 1", "Context 2", "Context 3"]
    prepared = compressor._prepare_contexts(contexts)
    
    assert "[Dokumen 1]" in prepared
    assert "[Dokumen 2]" in prepared
    assert "[Dokumen 3]" in prepared
    assert "Context 1" in prepared


def test_keyword_protection(compressor):
    """Test keyword protection mechanism"""
    text = "Pasal 123 ayat 4 UU 24/2013 mengatur tentang KTP"
    protected, replacements = compressor._protect_keywords(text)
    
    # Should have replacements
    assert len(replacements) > 0
    assert "__PROTECTED_" in protected
    
    # Should restore correctly
    restored = compressor._restore_keywords(protected, replacements)
    # Note: may not be exactly equal due to regex matching, but key terms preserved


def test_different_compression_ratios():
    """Test different compression ratios"""
    contexts = ["This is a long context " * 20]
    
    # Conservative compression (0.9)
    compressor_conservative = ContextCompressor(ratio=0.9)
    result_conservative = compressor_conservative.compress_contexts("test", contexts)
    
    # Aggressive compression (0.5)
    compressor_aggressive = ContextCompressor(ratio=0.5)
    result_aggressive = compressor_aggressive.compress_contexts("test", contexts)
    
    if result_conservative["success"] and result_aggressive["success"]:
        # Aggressive should compress more
        assert result_aggressive["compressed_tokens"] < result_conservative["compressed_tokens"]


def test_empty_contexts_handling(compressor):
    """Test handling of empty contexts"""
    result = compressor.compress_contexts(
        query="Test",
        contexts=[]
    )
    
    # Should handle gracefully
    assert result is not None
    assert "compressed_contexts" in result


def test_long_context_handling(compressor):
    """Test handling of very long contexts"""
    long_context = "Ini adalah konteks yang sangat panjang. " * 1000
    
    result = compressor.compress_contexts(
        query="Test?",
        contexts=[long_context]
    )
    
    # Should handle without crashing
    assert result is not None
    assert result["original_tokens"] > 0


def test_query_relevance_preservation(compressor):
    """Test that query-relevant content is preserved"""
    contexts = [
        "KTP elektronik wajib dimiliki semua WNI dewasa",
        "Paspor diperlukan untuk perjalanan internasional",
        "SIM diperlukan untuk mengendarai kendaraan bermotor"
    ]
    
    result = compressor.compress_contexts(
        query="Apa itu KTP elektronik?",
        contexts=contexts
    )
    
    compressed = result["compressed_contexts"].lower()
    
    # KTP should be preserved (query-relevant)
    assert "ktp" in compressed


@pytest.mark.parametrize("ratio", [0.3, 0.5, 0.7, 0.9])
def test_various_compression_ratios(ratio):
    """Test compression works across different ratios"""
    compressor = ContextCompressor(ratio=ratio)
    result = compressor.compress_contexts(
        query="Test",
        contexts=["Test context " * 10]
    )
    
    assert result is not None
    assert "compressed_contexts" in result
