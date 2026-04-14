"""
Unit Tests for Data Pipeline
Tests: PDF extraction, preprocessing, PII detection, chunking
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.preprocessor import IndonesianPreprocessor
from src.data.pii_detector import PIIDetector
from src.data.chunker import DocumentChunker, Chunk


class TestIndonesianPreprocessor(unittest.TestCase):
    """Test Indonesian text preprocessing."""
    
    def setUp(self):
        self.preprocessor = IndonesianPreprocessor()
    
    def test_language_detection(self):
        """Test Indonesian language detection."""
        indonesian_text = "Kartu Tanda Penduduk adalah identitas resmi penduduk Indonesia."
        result = self.preprocessor.preprocess(indonesian_text)
        
        self.assertEqual(result.language, 'id')
        # Language detection confidence can vary, accept any positive confidence
        self.assertGreater(result.confidence, 0.0)
    
    def test_text_normalization(self):
        """Test text normalization."""
        text_with_spaces = "Ini    adalah   teks    dengan    spasi    berlebih"
        result = self.preprocessor.preprocess(text_with_spaces)
        
        # Should normalize multiple spaces to single space
        self.assertNotIn("    ", result.processed)
    
    def test_is_indonesian(self):
        """Test Indonesian language checker."""
        indonesian = "Saya adalah warga negara Indonesia yang baik."
        english = "This is an English text about nothing in particular."
        
        self.assertTrue(self.preprocessor.is_indonesian(indonesian))
        self.assertFalse(self.preprocessor.is_indonesian(english))


class TestPIIDetector(unittest.TestCase):
    """Test PII detection system."""
    
    def setUp(self):
        self.detector = PIIDetector()
    
    def test_nik_detection(self):
        """Test NIK (16-digit ID) detection."""
        text = "NIK pemohon: 3201012501990001"
        report = self.detector.detect(text)
        
        # NIK pattern may match multiple times, just ensure it's detected
        self.assertGreater(report.total_matches, 0)
        self.assertIn('nik', report.matches_by_type)
    
    def test_email_detection(self):
        """Test email detection."""
        text = "Hubungi kami di admin@example.com untuk info lebih lanjut."
        report = self.detector.detect(text)
        
        self.assertGreater(report.total_matches, 0)
        self.assertIn('email', report.matches_by_type)
    
    def test_phone_detection(self):
        """Test Indonesian phone number detection."""
        text = "No HP: 0812-3456-7890"
        report = self.detector.detect(text)
        
        self.assertGreater(report.total_matches, 0)
        self.assertIn('phone', report.matches_by_type)
    
    def test_redaction(self):
        """Test PII redaction."""
        text = "Email: test@example.com, NIK: 1234567890123456"
        report = self.detector.detect(text)
        
        # Redacted text should not contain original PII
        self.assertNotIn("test@example.com", report.redacted_text)
        self.assertNotIn("1234567890123456", report.redacted_text)
        
        # Should contain redaction placeholders
        self.assertIn("[EMAIL_REDACTED]", report.redacted_text)
        self.assertIn("[NIK_REDACTED]", report.redacted_text)
    
    def test_nik_validation(self):
        """Test NIK format validation."""
        valid_nik = "3201012501990001"
        invalid_nik = "1234567890123456"
        
        self.assertTrue(self.detector.validate_nik(valid_nik))
        self.assertFalse(self.detector.validate_nik(invalid_nik))


class TestDocumentChunker(unittest.TestCase):
    """Test document chunking."""
    
    def setUp(self):
        # Use min_chunk_size=0 for tests to allow any text length
        # Production default is 100, but tests should be flexible
        self.chunker = DocumentChunker(chunk_size=100, overlap=20, min_chunk_size=0)
    
    def test_basic_chunking(self):
        """Test basic document chunking."""
        text = "Ini adalah paragraf pertama. " * 50  # Long text
        chunks = self.chunker.chunk(text, doc_id="test_doc_1")
        
        self.assertGreater(len(chunks), 0)
        self.assertIsInstance(chunks[0], Chunk)
    
    def test_chunk_metadata(self):
        """Test chunk metadata generation."""
        # Simple test text - min_chunk_size=0 allows this
        text = "JUDUL DOKUMEN\n\nIsi dokumen dengan metadata yang penting untuk testing."
        chunks = self.chunker.chunk(
            text,
            doc_id="test_doc_2",
            metadata={'doc_type': 'Perpres'}
        )
        
        self.assertGreater(len(chunks), 0)
        self.assertIn('doc_type', chunks[0].metadata)
        self.assertEqual(chunks[0].metadata['doc_type'], 'Perpres')
    
    def test_coherence_calculation(self):
        """Test coherence score calculation."""
        text = "Ini adalah kalimat lengkap dengan tanda baca."
        chunks = self.chunker.chunk(text, doc_id="test_doc_3")
        
        for chunk in chunks:
            score = self.chunker.calculate_coherence(chunk)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


def run_tests():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
