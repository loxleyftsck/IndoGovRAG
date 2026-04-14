"""
Smart Retrieval with Legal/Operational Awareness

Routes queries to appropriate document types:
- Legal queries → Legal documents first
- Operational queries → Operational documents first
"""

from typing import List, Dict
import re

class SmartRetriever:
    """
    Smart retrieval that understands query intent
    """
    
    # Query type indicators
    LEGAL_QUERY_PATTERNS = [
        r'dasar\s+hukum',
        r'\bpasal\b',
        r'\bayat\b',
        r'\buu\b',
        r'peraturan',
        r'undang[-\s]undang',
        r'legal\s+basis',
        r'aturan\s+(tentang|mengenai)',
    ]
    
    OPERATIONAL_QUERY_PATTERNS = [
        r'cara\s+(membuat|mengurus|bikin)',
        r'gimana\s+(bikin|buat)',
        r'bagaimana\s+(cara|proses)',
        r'syarat\s+(apa|membuat)',
        r'prosedur',
        r'langkah[-\s]langkah',
        r'tutorial',
        r'panduan',
    ]
    
    def detect_query_type(self, query: str) -> str:
        """
        Detect if query is legal or operational
        
        Returns:
            'legal', 'operational', or 'mixed'
        """
        query_lower = query.lower()
        
        legal_match = any(re.search(pattern, query_lower) 
                         for pattern in self.LEGAL_QUERY_PATTERNS)
        
        operational_match = any(re.search(pattern, query_lower) 
                               for pattern in self.OPERATIONAL_QUERY_PATTERNS)
        
        if legal_match and not operational_match:
            return 'legal'
        elif operational_match and not legal_match:
            return 'operational'
        else:
            return 'mixed'
    
    def smart_retrieve(self, query: str, vector_store, top_k: int = 5) -> List[Dict]:
        """
        Smart retrieval based on query type
        
        Args:
            query: User query
            vector_store: Vector store instance
            top_k: Total results to return
            
        Returns:
            List of retrieved documents with scores
        """
        query_type = self.detect_query_type(query)
        
        if query_type == 'legal':
            # Legal query: Prioritize legal documents
            return self._retrieve_legal_first(query, vector_store, top_k)
        
        elif query_type == 'operational':
            # Operational query: Prioritize operational documents
            return self._retrieve_operational_first(query, vector_store, top_k)
        
        else:
            # Mixed: Balanced retrieval
            return self._retrieve_balanced(query, vector_store, top_k)
    
    def _retrieve_legal_first(self, query: str, vector_store, top_k: int) -> List[Dict]:
        """Retrieve with legal docs prioritized"""
        # Get legal docs (70%)
        legal_k = int(top_k * 0.7)
        operational_k = top_k - legal_k
        
        # Search legal
        legal_results = vector_store.search(
            query,
            k=legal_k,
            filter={'metadata.is_legal': True}
        )
        
        # Search operational
        operational_results = vector_store.search(
            query,
            k=operational_k,
            filter={'metadata.is_legal': False}
        )
        
        return legal_results + operational_results
    
    def _retrieve_operational_first(self, query: str, vector_store, top_k: int) -> List[Dict]:
        """Retrieve with operational docs prioritized"""
        # Get operational docs (70%)
        operational_k = int(top_k * 0.7)
        legal_k = top_k - operational_k
        
        # Search operational
        operational_results = vector_store.search(
            query,
            k=operational_k,
            filter={'metadata.is_legal': False}
        )
        
        # Search legal
        legal_results = vector_store.search(
            query,
            k=legal_k,
            filter={'metadata.is_legal': True}
        )
        
        return operational_results + legal_results
    
    def _retrieve_balanced(self, query: str, vector_store, top_k: int) -> List[Dict]:
        """Balanced retrieval"""
        # 50-50 split
        legal_k = top_k // 2
        operational_k = top_k - legal_k
        
        legal_results = vector_store.search(
            query,
            k=legal_k,
            filter={'metadata.is_legal': True}
        )
        
        operational_results = vector_store.search(
            query,
            k=operational_k,
            filter={'metadata.is_legal': False}
        )
        
        return legal_results + operational_results


# Example usage
if __name__ == "__main__":
    retriever = SmartRetriever()
    
    # Test query detection
    test_queries = [
        "Apa dasar hukum KTP elektronik?",           # Legal
        "Gimana cara bikin KTP?",                    # Operational
        "Syarat dan dasar hukum pembuatan akta",     # Mixed
    ]
    
    print("="*60)
    print("🧠 Smart Retrieval - Query Type Detection")
    print("="*60 + "\n")
    
    for query in test_queries:
        qtype = retriever.detect_query_type(query)
        print(f"Query: {query}")
        print(f"Type: {qtype.upper()}")
        print()
    
    print("="*60)
    print("✅ Smart retrieval ready!")
    print("="*60)
