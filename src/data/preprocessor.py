"""
Indonesian Text Preprocessing

Handles:
- Text normalization for Indonesian
- Language detection
- Special character handling
- Number/date normalization
"""

import re
from typing import Dict, List, Optional
from langdetect import detect, DetectorFactory
from dataclasses import dataclass

# Set seed for consistent language detection
DetectorFactory.seed = 0


@dataclass
class ProcessedText:
    """Preprocessed text with metadata."""
    original: str
    processed: str
    language: str
    confidence: float
    stats: Dict


class IndonesianPreprocessor:
    """
    Text preprocessor optimized for Indonesian government documents.
    
    Handles:
    - Indonesian-specific text normalization
    - Mixed Indonesian-English content
    - Special characters and formatting
    - Numbers and dates
    """
    
    # Common Indonesian abbreviations in government docs
    ABBREV_EXPANSIONS = {
        'UU': 'Undang-Undang',
        'PP': 'Peraturan Pemerintah',
        'Perpres': 'Peraturan Presiden',
        'Permen': 'Peraturan Menteri',
        'Kepres': 'Keputusan Presiden',
        'Kepmen': 'Keputusan Menteri',
        'SE': 'Surat Edaran',
        'NIK': 'Nomor Induk Kependudukan',
        'KTP': 'Kartu Tanda Penduduk',
        'KK': 'Kartu Keluarga',
        'NPWP': 'Nomor Pokok Wajib Pajak',
        'BPJS': 'Badan Penyelenggara Jaminan Sosial',
    }
    
    def __init__(
        self,
        expand_abbreviations: bool = False,
        preserve_numbers: bool = True,
        lowercase: bool = False
    ):
        """
        Initialize Indonesian preprocessor.
        
        Args:
            expand_abbreviations: Expand common abbreviations
            preserve_numbers: Keep numbers as-is
            lowercase: Convert to lowercase
        """
        self.expand_abbreviations = expand_abbreviations
        self.preserve_numbers = preserve_numbers
        self.lowercase = lowercase
    
    def preprocess(self, text: str) -> ProcessedText:
        """
        Preprocess Indonesian text.
        
        Args:
            text: Raw text
        
        Returns:
            ProcessedText with normalized text
        """
        original = text
        
        # Detect language
        language, confidence = self._detect_language(text)
        
        # Normalize text
        processed = self._normalize(text)
        
        # Get statistics
        stats = {
            'original_length': len(original),
            'processed_length': len(processed),
            'original_words': len(original.split()),
            'processed_words': len(processed.split()),
        }
        
        return ProcessedText(
            original=original,
            processed=processed,
            language=language,
            confidence=confidence,
            stats=stats
        )
    
    def _normalize(self, text: str) -> str:
        """Normalize Indonesian text."""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers (common in PDFs)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove headers/footers (heuristic)
        text = re.sub(r'^-+\s*$', '', text, flags=re.MULTILINE)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Normalize dashes
        text = text.replace('–', '-').replace('—', '-')
        
        # Fix common OCR errors in Indonesian
        text = text.replace('i,', 'i.').replace('I.', 'i.')
        
        # Expand abbreviations if enabled
        if self.expand_abbreviations:
            for abbrev, full in self.ABBREV_EXPANSIONS.items():
                # Match whole word only
                text = re.sub(
                    r'\b' + re.escape(abbrev) + r'\b',
                    full,
                    text
                )
        
        # Lowercase if enabled
        if self.lowercase:
            text = text.lower()
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def _detect_language(self, text: str) -> tuple[str, float]:
        """
        Detect text language.
        
        Returns:
            (language_code, confidence)
        """
        if not text or len(text.strip()) < 20:
            return ('unknown', 0.0)
        
        try:
            # Take first 1000 chars for detection
            sample = text[:1000]
            language = detect(sample)
            
            # Confidence heuristic:
            # Indonesian should have common words like: yang, dan, dengan, untuk, ini, itu
            indonesian_markers = [
                'yang', 'dan', 'dengan', 'untuk', 'ini', 'itu',
                'adalah', 'pada', 'dalam', 'oleh', 'tersebut',
                'tentang', 'kepada', 'sebagai', 'akan'
            ]
            
            sample_lower = sample.lower()
            marker_count = sum(
                1 for marker in indonesian_markers
                if marker in sample_lower
            )
            
            # Confidence based on markers
            confidence = min(marker_count / 5.0, 1.0)
            
            return (language, confidence)
        
        except Exception:
            return ('unknown', 0.0)
    
    def is_indonesian(
        self,
        text: str,
        min_confidence: float = 0.3
    ) -> bool:
        """
        Check if text is Indonesian.
        
        Args:
            text: Text to check
            min_confidence: Minimum confidence threshold
        
        Returns:
            True if Indonesian with sufficient confidence
        """
        language, confidence = self._detect_language(text)
        # Return True if langdetect says Indonesian OR confidence (marker-based) is high
        return language == 'id' or confidence >= min_confidence
    
    def clean_for_embedding(self, text: str) -> str:
        """
        Clean text specifically for embedding generation.
        
        More aggressive cleaning:
        - Remove special characters
        - Remove URLs
        - Remove emails
        - Normalize whitespace
        
        Args:
            text: Input text
        
        Returns:
            Cleaned text ready for embedding
        """
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove emails
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters (keep Indonesian letters)
        text = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Trim
        text = text.strip()
        
        return text


# =============================================================================
# TESTING
# =============================================================================

def demo_preprocessor():
    """Demo text preprocessing."""
    
    print("🧪 Indonesian Preprocessor Demo\n")
    
    # Sample Indonesian government text
    sample_text = """
    PERATURAN PRESIDEN REPUBLIK INDONESIA
    NOMOR 26 TAHUN 2009
    
    TENTANG
    
    PENERAPAN KARTU TANDA PENDUDUK 
    BERBASIS NOMOR INDUK KEPENDUDUKAN SECARA NASIONAL
    
    Pasal 1
    Dalam Peraturan Presiden ini, yang dimaksud dengan:
    
    1. Kartu Tanda Penduduk, yang selanjutnya disingkat KTP adalah identitas 
       resmi penduduk sebagai bukti diri yang diterbitkan oleh...
    
    2. NIK adalah nomor identitas penduduk yang bersifat unik atau khas,
       tunggal dan melekat pada seseorang yang terdaftar sebagai...
    """
    
    # Initialize preprocessor
    preprocessor = IndonesianPreprocessor(
        expand_abbreviations=True,
        lowercase=False
    )
    
    # Preprocess
    result = preprocessor.preprocess(sample_text)
    
    print("📊 Language Detection")
    print("="*60)
    print(f"Detected: {result.language}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Is Indonesian: {preprocessor.is_indonesian(sample_text)}")
    
    print("\n📝 Text Statistics")
    print("="*60)
    for key, value in result.stats.items():
        print(f"{key}: {value}")
    
    print("\n✂️  Preprocessed Text (first 500 chars)")
    print("="*60)
    print(result.processed[:500])
    
    print("\n🧹 Cleaned for Embedding")
    print("="*60)
    cleaned = preprocessor.clean_for_embedding(sample_text)
    print(cleaned[:300])
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo_preprocessor()
