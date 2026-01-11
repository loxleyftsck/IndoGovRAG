"""
Production Guardrails for IndoGovRAG Beta
Handles ambiguous queries, legal disclaimers, and safety checks

Based on Level 2 robustness evaluation results
"""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class QueryClassification:
    """Classification of query for guardrail routing"""
    is_ambiguous: bool
    is_legal: bool
    is_out_of_scope: bool
    confidence: float
    suggested_clarification: Optional[str] = None


class ProductionGuardrails:
    """
    Production guardrails for beta deployment
    
    Features:
    - Ambiguous query detection & clarification
    - Legal disclaimer injection
    - Out-of-scope detection
    """
    LEGAL_KEYWORDS = [
        'dasar hukum', 'sanksi', 'pidana', 'perdata', 'peraturan',
        'undang-undang', 'pasal', 'ayat', 'berlaku', 'sah',
        'hukum', 'legal', 'yuridis', 'perda', 'perpres'
    ]
    
    # Ambiguous query patterns
    AMBIGUOUS_PATTERNS = [
        r'\b(berapa lama|kapan|waktu)\b.*\?$',  # Time-related without context
        r'^\s*(itu|ini)\s*\?$',  # Just "itu?" or "ini?"
        r'\b(bagaimana|gimana)\s*\?$',  # Just "how?" without subject
        r'\b(syarat|persyaratan)\s*\?$',  # "requirements?" without specifying what for
        r'\b(dokumen|berkas)\s*(apa|mana)\s*\?$',  # "what documents?" too vague
    ]
    
    # Out-of-scope indicators
    OUT_OF_SCOPE_PATTERNS = [
        r'\b(harga|biaya|tarif|ongkos)\b',  # Pricing
        r'\b(alamat|lokasi|tempat|kantor.*mana)\b',  # Location
        r'\b(jam|jadwal|buka|tutup)\b',  # Schedule
        r'\b(presiden|menteri|gubernur|siapa)\b',  # Current officials
        r'\b(telepon|telp|kontak|email|wa|whatsapp)\b',  # Contact
    ]
    
    def classify_query(self, query: str) -> QueryClassification:
        """
        Classify query for guardrail routing
        
        Args:
            query: User question
            
        Returns:
            QueryClassification with flags and suggestions
        """
        query_lower = query.lower().strip()
        
        # Check ambiguity
        is_ambiguous = any(
            re.search(pattern, query_lower, re.IGNORECASE)
            for pattern in self.AMBIGUOUS_PATTERNS
        )
        
        # Check legal domain
        is_legal = any(
            keyword in query_lower
            for keyword in self.LEGAL_KEYWORDS
        )
        
        # Check out-of-scope
        is_out_of_scope = any(
            re.search(pattern, query_lower, re.IGNORECASE)
            for pattern in self.OUT_OF_SCOPE_PATTERNS
        )
        
        # Generate clarification if ambiguous
        clarification = None
        if is_ambiguous:
            clarification = self._generate_clarification(query_lower)
        
        # Confidence (inverse of ambiguity/out-of-scope)
        confidence = 1.0
        if is_ambiguous:
            confidence -= 0.3
        if is_out_of_scope:
            confidence -= 0.4
        confidence = max(0.0, confidence)
        
        return QueryClassification(
            is_ambiguous=is_ambiguous,
            is_legal=is_legal,
            is_out_of_scope=is_out_of_scope,
            confidence=confidence,
            suggested_clarification=clarification
        )
    
    def _generate_clarification(self, query_lower: str) -> str:
        """Generate clarification suggestion for ambiguous query"""
        if 'berapa lama' in query_lower or 'kapan' in query_lower:
            return "Mohon sebutkan dokumen atau layanan yang dimaksud (contoh: 'Berapa lama proses pembuatan KTP?')"
        elif query_lower.strip() in ['itu?', 'ini?']:
            return "Mohon sebutkan secara spesifik dokumen atau informasi yang dimaksud"
        elif 'bagaimana' in query_lower or 'gimana' in query_lower:
            return "Mohon lengkapi pertanyaan dengan dokumen atau proses yang ingin ditanyakan"
        elif 'syarat' in query_lower or 'persyaratan' in query_lower:
            return "Mohon sebutkan dokumen atau layanan yang dimaksud (contoh: 'Apa persyaratan membuat paspor?')"
        else:
            return "Mohon perjelas pertanyaan Anda untuk mendapatkan jawaban yang lebih akurat"
    
    
    def add_legal_disclaimer(self, answer: str, query_classification: QueryClassification) -> str:
        """
        Add legal disclaimer to answer if needed
        
        Args:
            answer: Generated answer
            query_classification: Classification result
            
        Returns:
            Answer with disclaimer if legal domain
        """
        if not query_classification.is_legal:
            return answer
        
        disclaimer = """

---
**⚠️ Disclaimer Legal:**
Informasi di atas merupakan ringkasan dari dokumen peraturan yang tersedia. Ini BUKAN nasihat hukum yang mengikat. Untuk keperluan hukum formal atau interpretasi yang memerlukan kepastian yuridis, mohon konsultasikan dengan instansi berwenang atau ahli hukum."""
        
        return answer + disclaimer
    
    def format_ambiguous_response(
        self,
        query: str,
        classification: QueryClassification,
        attempted_answer: Optional[str] = None
    ) -> str:
        """
        Format response for ambiguous query
        
        Args:
            query: Original query
            classification: Classification result
            attempted_answer: Optional answer if system tried anyway
            
        Returns:
            Formatted response with clarification
        """
        response = f"**Pertanyaan Anda:** {query}\n\n"
        
        if classification.suggested_clarification:
            response += f"**Klarifikasi diperlukan:** {classification.suggested_clarification}\n\n"
        
        if attempted_answer:
            response += "**Kemungkinan jawaban berdasarkan interpretasi kami:**\n\n"
            response += attempted_answer
            response += "\n\nℹ️ *Mohon konfirmasi apakah ini yang dimaksud, atau perjelas pertanyaan Anda untuk jawaban yang lebih akurat.*"
        else:
            response += "Silakan perjelas pertanyaan Anda agar kami dapat memberikan informasi yang tepat."
        
        return response
    
    def format_out_of_scope_response(self, query: str) -> str:
        """Format response for out-of-scope query"""
        return f"""Maaf, pertanyaan "{query}" berada di luar cakupan informasi yang tersedia saat ini.

Sistem ini menyediakan informasi tentang:
- Dokumen kependudukan (KTP, KK, Akta, NIK)
- Prosedur administrasi kependudukan
- Peraturan terkait layanan Dukcapil

Untuk informasi tentang harga, lokasi kantor, jadwal layanan, atau kontak instansi, silakan hubungi kantor Dinas Kependudukan dan Pencatatan Sipil setempat atau kunjungi situs web resmi mereka."""


# Singleton
_guardrails = None

def get_guardrails() -> ProductionGuardrails:
    """Get global guardrails instance"""
    global _guardrails
    if _guardrails is None:
        _guardrails = ProductionGuardrails()
    return _guardrails
