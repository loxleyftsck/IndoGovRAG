"""
PDF Text Extraction for Indonesian Government Documents

Supports:
- Text-based PDFs (PyPDF2)
- Complex layouts (pdfplumber fallback)
- Multi-page documents
- Metadata extraction
"""

import PyPDF2
import pdfplumber
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDocument:
    """Extracted PDF document with metadata."""
    file_path: str
    text: str
    num_pages: int
    metadata: Dict
    extraction_method: str
    success: bool
    error: Optional[str] = None


class PDFExtractor:
    """
    Extract text from PDF documents.
    
    Uses multi-strategy approach:
    1. PyPDF2 (fast, works for most PDFs)
    2. pdfplumber (fallback for complex layouts)
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize PDF extractor.
        
        Args:
            verbose: Print extraction progress
        """
        self.verbose = verbose
    
    def extract(self, pdf_path: str) -> ExtractedDocument:
        """
        Extract text from PDF using best available method.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            ExtractedDocument with text and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return ExtractedDocument(
                file_path=str(pdf_path),
                text="",
                num_pages=0,
                metadata={},
                extraction_method="none",
                success=False,
                error=f"File not found: {pdf_path}"
            )
        
        # Try PyPDF2 first (faster)
        result = self._extract_pypdf2(pdf_path)
        
        # If failed or empty, try pdfplumber
        if not result.success or len(result.text.strip()) < 100:
            if self.verbose:
                logger.debug(f"  PyPDF2 failed/empty, trying pdfplumber...")
            result = self._extract_pdfplumber(pdf_path)
        
        return result
    
    def _extract_pypdf2(self, pdf_path: Path) -> ExtractedDocument:
        """Extract using PyPDF2."""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                # Extract metadata
                metadata = {
                    'title': reader.metadata.get('/Title', '') if reader.metadata else '',
                    'author': reader.metadata.get('/Author', '') if reader.metadata else '',
                    'creator': reader.metadata.get('/Creator', '') if reader.metadata else '',
                }
                
                # Extract text from all pages
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                full_text = '\n\n'.join(text_parts)
                
                return ExtractedDocument(
                    file_path=str(pdf_path),
                    text=full_text,
                    num_pages=len(reader.pages),
                    metadata=metadata,
                    extraction_method='pypdf2',
                    success=True
                )
        
        except Exception as e:
            if self.verbose:
                logger.debug(f"  PyPDF2 error: {e}")
            return ExtractedDocument(
                file_path=str(pdf_path),
                text="",
                num_pages=0,
                metadata={},
                extraction_method='pypdf2',
                success=False,
                error=str(e)
            )
    
    def _extract_pdfplumber(self, pdf_path: Path) -> ExtractedDocument:
        """Extract using pdfplumber (better for complex layouts)."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                metadata = {
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                    'creator': pdf.metadata.get('Creator', ''),
                }
                
                # Extract text from all pages
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                full_text = '\n\n'.join(text_parts)
                
                return ExtractedDocument(
                    file_path=str(pdf_path),
                    text=full_text,
                    num_pages=len(pdf.pages),
                    metadata=metadata,
                    extraction_method='pdfplumber',
                    success=True
                )
        
        except Exception as e:
            if self.verbose:
                logger.debug(f"  pdfplumber error: {e}")
            return ExtractedDocument(
                file_path=str(pdf_path),
                text="",
                num_pages=0,
                metadata={},
                extraction_method='pdfplumber',
                success=False,
                error=str(e)
            )
    
    def extract_batch(
        self,
        pdf_paths: List[str],
        show_progress: bool = True
    ) -> List[ExtractedDocument]:
        """
        Extract text from multiple PDFs.
        
        Args:
            pdf_paths: List of PDF file paths
            show_progress: Show progress bar
        
        Returns:
            List of ExtractedDocument objects
        """
        from tqdm import tqdm
        
        results = []
        
        iterator = tqdm(pdf_paths, desc="Extracting PDFs") if show_progress else pdf_paths
        
        for pdf_path in iterator:
            if self.verbose:
                logger.info(f"\nExtracting: {Path(pdf_path).name}")
            
            result = self.extract(pdf_path)
            results.append(result)
        
        return results
    
    def get_stats(self, results: List[ExtractedDocument]) -> Dict:
        """Get extraction statistics."""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        total_pages = sum(r.num_pages for r in results if r.success)
        total_chars = sum(len(r.text) for r in results if r.success)
        
        methods = {}
        for r in results:
            if r.success:
                methods[r.extraction_method] = methods.get(r.extraction_method, 0) + 1
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / max(total, 1),
            'total_pages': total_pages,
            'total_characters': total_chars,
            'avg_chars_per_doc': total_chars / max(successful, 1),
            'extraction_methods': methods,
        }


# =============================================================================
# TESTING
# =============================================================================

def demo_extractor():
    """Demo PDF extraction."""

    logger.info("[TEST] PDF Extractor Demo\n")

    # Initialize extractor
    extractor = PDFExtractor(verbose=True)

    # Check if we have any PDFs
    pdf_dir = Path("data/documents/pdfs")

    if not pdf_dir.exists():
        logger.info(f"Creating directory: {pdf_dir}")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        logger.warning("[WARN]  No PDFs found!")
        logger.warning("   Please download PDFs using DATA_COLLECTION_GUIDE.md")
        logger.warning(f"   Place them in: {pdf_dir}")
        return

    # Find PDFs
    pdfs = list(pdf_dir.glob("*.pdf"))

    if not pdfs:
        logger.warning(f"[WARN]  No PDFs found in {pdf_dir}")
        logger.warning("   Download some PDFs first!")
        return

    logger.info(f"[DOC] Found {len(pdfs)} PDF(s)")
    logger.info("=" * 60)

    # Extract first PDF as demo
    if pdfs:
        result = extractor.extract(str(pdfs[0]))

        logger.info(f"Extracted: {Path(result.file_path).name}")
        logger.info(f"   Method: {result.extraction_method}")
        logger.info(f"   Success: {result.success}")
        logger.info(f"   Pages: {result.num_pages}")
        logger.info(f"   Characters: {len(result.text)}")

        if result.success:
            logger.info(f"\n[MSG] First 500 characters:")
            logger.info("-" * 60)
            logger.info(result.text[:500])
            logger.info("-" * 60)
        else:
            logger.error(f"\n[ERR] Error: {result.error}")

    logger.info("\n[OK] Demo complete!")


if __name__ == "__main__":
    demo_extractor()
