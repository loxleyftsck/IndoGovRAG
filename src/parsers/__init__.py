"""
Parser Module for Indonesian Legal Documents
"""

from .legal_pdf_extractor import IndonesianPDFExtractor, create_pdf_extractor, PDFMetadata

__all__ = ["IndonesianPDFExtractor", "create_pdf_extractor", "PDFMetadata"]
