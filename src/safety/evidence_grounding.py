"""
Evidence Grounding Module
Prevents hallucinations by checking retrieval quality before generation
"""

from typing import Tuple, List, Dict, Optional


class EvidenceGrounding:
    """
    Evidence sufficiency checker for RAG pipeline
    Returns "I don't know" when evidence is insufficient
    """
    
    def __init__(
        self, 
        min_score: float = 0.5,
        min_docs: int = 1,
        language: str = "id"  # Indonesian
    ):
        """
        Initialize evidence grounding
        
        Args:
            min_score: Minimum retrieval score (0-1)
            min_docs: Minimum number of docs required
            language: Response language (id/en)
        """
        self.min_score = min_score
        self.min_docs = min_docs
        self.language = language
    
    def check_sufficiency(
        self, 
        query: str, 
        retrieved_docs: List[Dict]
    ) -> Tuple[bool, str, float]:
        """
        Check if retrieved documents sufficient to answer question
        
        Args:
            query: User question
            retrieved_docs: List of retrieved documents with scores
            
        Returns:
            (is_sufficient, reason, max_score)
        """
        # Case 1: No documents retrieved
        if not retrieved_docs:
            return False, "no_documents", 0.0
        
        # Case 2: Too few documents
        if len(retrieved_docs) < self.min_docs:
            return False, f"insufficient_count_{len(retrieved_docs)}", 0.0
        
        # Case 3: Low relevance scores
        max_score = max(doc.get('score', 0.0) for doc in retrieved_docs)
        
        if max_score < self.min_score:
            return False, f"low_relevance_{max_score:.2f}", max_score
        
        # Sufficient evidence found
        return True, "sufficient", max_score
    
    def get_response(
        self, 
        reason: str, 
        retrieved_docs: Optional[List[Dict]] = None,
        include_sources: bool = True
    ) -> Dict:
        """
        Generate "I don't know" response with explanation
        
        Returns full RAG response structure
        """
        # Base response
        response = {
            'answer': self._format_answer(reason, retrieved_docs),
            'sources': [],
            'confidence': 0.0,
            'metadata': {
                'evidence_sufficient': False,
                'reason': reason,
                'grounding_triggered': True
            }
        }
        
        # Add retrieved source info (even if insufficient)
        if include_sources and retrieved_docs:
            response['sources'] = [
                {
                    'doc_id': doc.get('doc_id', 'unknown'),
                    'score': doc.get('score', 0.0),
                    'excerpt': doc.get('text', '')[:100]
                }
                for doc in retrieved_docs[:3]  # Top 3
            ]
            response['metadata']['attempted_sources'] = len(retrieved_docs)
        
        return response
    
    def _format_answer(
        self, 
        reason: str, 
        retrieved_docs: Optional[List[Dict]] = None
    ) -> str:
        """
        Format "I don't know" answer based on reason
        
        Templates vary by failure reason for better UX
        """
        templates = {
            "id": {  # Indonesian
                "no_documents": (
                    "Maaf, tidak ditemukan dokumen yang relevan untuk menjawab "
                    "pertanyaan Anda. Silakan coba pertanyaan yang lebih spesifik "
                    "atau gunakan kata kunci lain."
                ),
                "insufficient_count": (
                    "Maaf, hanya ditemukan sedikit informasi terkait pertanyaan Anda. "
                    "Dokumen yang tersedia mungkin tidak cukup lengkap untuk memberikan "
                    "jawaban yang akurat."
                ),
                "low_relevance": (
                    "Maaf, tidak ada informasi yang cukup relevan di dokumen sumber "
                    "untuk menjawab pertanyaan ini. Pertanyaan Anda mungkin di luar "
                    "cakupan dokumen peraturan pemerintah yang tersedia."
                ),
                "out_of_domain": (
                    "Maaf, pertanyaan Anda tampaknya di luar topik dokumen pemerintah "
                    "yang tersedia. Sistem ini khusus untuk informasi seputar peraturan "
                    "dan layanan pemerintah Indonesia."
                ),
                "default": (
                    "Maaf, tidak dapat memberikan jawaban yang akurat berdasarkan "
                    "dokumen yang tersedia."
                )
            },
            "en": {  # English (for testing/international users)
                "no_documents": (
                    "Sorry, no relevant documents were found to answer your question. "
                    "Please try a more specific question or different keywords."
                ),
                "insufficient_count": (
                    "Sorry, only limited information was found related to your question. "
                    "The available documents may not be comprehensive enough for an accurate answer."
                ),
                "low_relevance": (
                    "Sorry, there is not enough relevant information in the source documents "
                    "to answer this question. Your question may be outside the scope of "
                    "available government regulation documents."
                ),
                "out_of_domain": (
                    "Sorry, your question appears to be outside the topic of available "
                    "government documents. This system specializes in Indonesian government "
                    "regulations and services."
                ),
                "default": (
                    "Sorry, unable to provide an accurate answer based on available documents."
                )
            }
        }
        
        # Determine template key
        if reason == "no_documents":
            key = "no_documents"
        elif reason.startswith("insufficient_count"):
            key = "insufficient_count"
        elif reason.startswith("low_relevance"):
            key = "low_relevance"
        else:
            key = "default"
        
        # Get template
        template = templates[self.language].get(key, templates[self.language]["default"])
        
        # Add source info if available
        if retrieved_docs and len(retrieved_docs) > 0:
            source_info = "\n\nDokumen yang ditemukan:"
            for i, doc in enumerate(retrieved_docs[:3], 1):
                doc_id = doc.get('doc_id', 'unknown')
                score = doc.get('score', 0.0)
                source_info += f"\n{i}. {doc_id} (relevansi: {score:.2f})"
            
            template += source_info
        
        return template


# === USAGE EXAMPLES ===

def example_usage():
    """Examples of evidence grounding in action"""
    
    checker = EvidenceGrounding(min_score=0.5, min_docs=1)
    
    # Example 1: No documents found
    print("="*60)
    print("EXAMPLE 1: No Documents")
    print("="*60)
    query = "What is the weather today?"
    docs = []
    
    is_sufficient, reason, score = checker.check_sufficiency(query, docs)
    print(f"Sufficient: {is_sufficient}")
    print(f"Reason: {reason}")
    print(f"Response:")
    response = checker.get_response(reason, docs)
    print(response['answer'])
    
    # Example 2: Low relevance
    print("\n" + "="*60)
    print("EXAMPLE 2: Low Relevance")
    print("="*60)
    query = "Berapa gaji presiden?"
    docs = [
        {'doc_id': 'uu_24_2013', 'score': 0.35, 'text': 'Tentang KTP elektronik...'},
        {'doc_id': 'perpres_26', 'score': 0.28, 'text': 'Tentang paspor...'}
    ]
    
    is_sufficient, reason, score = checker.check_sufficiency(query, docs)
    print(f"Sufficient: {is_sufficient}")
    print(f"Reason: {reason}")
    print(f"Max Score: {score}")
    print(f"Response:")
    response = checker.get_response(reason, docs, include_sources=True)
    print(response['answer'])
    
    # Example 3: Sufficient evidence
    print("\n" + "="*60)
    print("EXAMPLE 3: Sufficient Evidence")
    print("="*60)
    query = "Apa syarat membuat KTP?"
    docs = [
        {'doc_id': 'uu_24_2013', 'score': 0.89, 'text': 'Syarat KTP: KK, Akta Lahir...'},
        {'doc_id': 'perpres_26', 'score': 0.76, 'text': 'Prosedur KTP elektronik...'}
    ]
    
    is_sufficient, reason, score = checker.check_sufficiency(query, docs)
    print(f"Sufficient: {is_sufficient}")
    print(f"Reason: {reason}")
    print(f"Max Score: {score}")
    print(f"✅ Evidence sufficient - proceed to LLM generation")


if __name__ == "__main__":
    example_usage()
