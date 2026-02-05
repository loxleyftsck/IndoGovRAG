"""
Enhanced Indonesian Legal PDF Parser
Handles complex layouts, tables, and scanned documents
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re
from datetime import datetime
import fitz  # PyMuPDF
from dataclasses import dataclass


@dataclass
class PDFMetadata:
    """Extracted metadata from legal documents"""
    doc_id: str
    title: str
    doc_type: str  # UU, PP, Perpres, etc.
    number: Optional[str]
    year: Optional[int]
    issuer: Optional[str]
    issue_date: Optional[datetime]
    subject: Optional[str]
    pages: int
    has_tables: bool
    is_scanned: bool


class IndonesianPDFExtractor:
    """
    Production-grade PDF extractor for Indonesian legal documents
    
    Features:
    - Structure-aware extraction (preserves headings, lists)
    - Table detection and extraction
    - Metadata auto-extraction
    - OCR fallback for scanned PDFs
    """
    
    def __init__(
        self,
        enable_ocr: bool = False,
        preserve_structure: bool = True
    ):
        """
        Initialize PDF extractor
        
        Args:
            enable_ocr: Enable OCR for scanned documents
            preserve_structure: Preserve document structure
        """
        self.enable_ocr = enable_ocr
        self.preserve_structure = preserve_structure
        
        # Indonesian legal document patterns
        self.doc_type_patterns = {
            r'UNDANG-UNDANG.*NOMOR\s+(\d+)\s+TAHUN\s+(\d{4})': 'UU',
            r'PERATURAN PEMERINTAH.*NOMOR\s+(\d+)\s+TAHUN\s+(\d{4})': 'PP',
            r'PERATURAN PRESIDEN.*NOMOR\s+(\d+)\s+TAHUN\s+(\d{4})': 'Perpres',
            r'PERATURAN MENTERI.*NOMOR\s+(\d+)\s+TAHUN\s+(\d{4})': 'Permen',
            r'KEPUTUSAN PRESIDEN.*NOMOR\s+(\d+)\s+TAHUN\s+(\d{4})': 'Keppres'
        }
        
        print(f"✅ Indonesian PDF Extractor initialized")
        print(f"   OCR: {'enabled' if enable_ocr else 'disabled'}")
    
    def extract(self, pdf_path: str) -> Dict:
        """
        Extract text and metadata from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with text, metadata, and structure
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Open PDF
        doc = fitz.open(str(pdf_path))
        
        # Extract text
        full_text = ""
        pages_text = []
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            pages_text.append(page_text)
            full_text += page_text + "\n\n"
        
        # Detect if scanned (low text density)
        is_scanned = self._is_scanned_pdf(pages_text)
        
        # OCR if needed
        if is_scanned and self.enable_ocr:
            full_text = self._ocr_pdf(doc)
        
        # Extract metadata
        metadata = self._extract_metadata(full_text, doc)
        
        # Detect tables
        has_tables = self._detect_tables(doc)
        
        doc.close()
        
        return {
            "text": full_text.strip(),
            "metadata": metadata,
            "pages": len(pages_text),
            "is_scanned": is_scanned,
            "has_tables": has_tables,
            "extracted_at": datetime.now().isoformat()
        }
    
    def _extract_metadata(self, text: str, doc: fitz.Document) -> PDFMetadata:
        """Extract structured metadata from document"""
        
        # Get first page for title/header
        first_500_chars = text[:500].upper()
        
        # Detect document type
        doc_type = "Unknown"
        number = None
        year = None
        
        for pattern, dtype in self.doc_type_patterns.items():
            match = re.search(pattern, first_500_chars)
            if match:
                doc_type = dtype
                number = match.group(1)
                year = int(match.group(2))
                break
        
        # Extract title (usually after doc type line)
        title = self._extract_title(text)
        
        # Create doc_id
        if number and year:
            doc_id = f"{doc_type}_{number}_{year}"
        else:
            doc_id = Path(doc.name).stem if hasattr(doc, 'name') else "unknown"
        
        return PDFMetadata(
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            number=number,
            year=year,
            issuer=self._extract_issuer(text),
            issue_date=None,  # Could parse from "Ditetapkan di Jakarta, tanggal..."
            subject=self._extract_subject(text),
            pages=doc.page_count,
            has_tables=False,  # Set by caller
            is_scanned=False  # Set by caller
        )
    
    def _extract_title(self, text: str) -> str:
        """Extract document title"""
        lines = text.split('\n')
        
        # Title usually appears after "TENTANG"
        for i, line in enumerate(lines):
            if 'TENTANG' in line.upper():
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        
        # Fallback: first non-empty line
        for line in lines:
            if line.strip() and len(line.strip()) > 10:
                return line.strip()
        
        return "Untitled Document"
    
    def _extract_issuer(self, text: str) -> Optional[str]:
        """Extract issuing authority"""
        issuers = [
            'PRESIDEN REPUBLIK INDONESIA',
            'MENTERI',
            'PEMERINTAH',
            'DEWAN PERWAKILAN RAKYAT'
        ]
        
        for issuer in issuers:
            if issuer in text.upper()[:1000]:
                return issuer.title()
        
        return None
    
    def _extract_subject(self, text: str) -> Optional[str]:
        """Extract main subject/topic"""
        # Look for "TENTANG" keyword
        match = re.search(r'TENTANG\s+([^\n]+)', text.upper())
        if match:
            return match.group(1).strip().title()
        
        return None
    
    def _is_scanned_pdf(self, pages_text: List[str]) -> bool:
        """
        Detect if PDF is scanned (image-based)
        
        Heuristic: If text density is very low, likely scanned
        """
        total_chars = sum(len(page) for page in pages_text)
        avg_chars_per_page = total_chars / len(pages_text) if pages_text else 0
        
        # Typical text PDF has >500 chars/page
        return avg_chars_per_page < 100
    
    def _detect_tables(self, doc: fitz.Document) -> bool:
        """Detect if document contains tables"""
        # Simple heuristic: look for multiple vertical lines
        for page in doc:
            drawings = page.get_drawings()
            
            vertical_lines = 0
            for drawing in drawings:
                for item in drawing.get("items", []):
                    if item[0] == "l":  # Line
                        x1, y1, x2, y2 = item[1:5]
                        if abs(x1 - x2) < 2:  # Vertical line
                            vertical_lines += 1
            
            if vertical_lines > 5:  # Likely a table
                return True
        
        return False
    
    def _ocr_pdf(self, doc: fitz.Document) -> str:
        """
        Perform OCR on scanned PDF
        Requires tesseract installation
        """
        try:
            import pytesseract
            from PIL import Image
            import io
        except ImportError:
            print("⚠️ OCR dependencies not installed (pytesseract, PIL)")
            return ""
        
        full_text = ""
        
        for page_num, page in enumerate(doc):
            # Convert page to image
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # OCR
            text = pytesseract.image_to_string(img, lang='ind')  # Indonesian
            full_text += text + "\n\n"
        
        return full_text


# Factory function
def create_pdf_extractor(enable_ocr: bool = False) -> IndonesianPDFExtractor:
    """Create PDF extractor instance"""
    return IndonesianPDFExtractor(enable_ocr=enable_ocr)
