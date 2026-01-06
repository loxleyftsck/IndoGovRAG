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
    
    
    # Legal domain indicators
    LEGAL_KEYWORDS = [
        'dasar hukum', 'sanksi', 'pidana', 'perdata', 'peraturan',
        'undang-undang', 'pasal', 'ayat', 'berlaku', 'sah',
        'hukum', 'legal', 'yuridis', 'perda', 'perpres'
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
    
    def _generate_clarification(self, query: str) -> str:
        """Generate clarification prompt for ambiguous query"""
        
        
        # Generic clarification
        return "Untuk memberikan jawaban yang sesuai, mohon perjelas pertanyaan Anda dengan menyebutkan jenis dokumen atau layanan kependudukan yang dimaksud."
    
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
