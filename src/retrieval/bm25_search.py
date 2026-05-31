"""
BM25 Lexical Search Implementation

Provides BM25 ranking for keyword-based search to complement semantic search.
Used in hybrid search for better retrieval performance.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from rank_bm25 import BM25Okapi
from functools import lru_cache
import re

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4096)
def _tokenize_cached(text: str) -> Tuple[str, ...]:
    """
    LRU-cached tokenization (4096 entries).
    Returns a tuple so it is hashable and cacheable.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s]', ' ', text)
    tokens = text.split()
    tokens = tuple(t for t in tokens if len(t) > 2)
    return tokens


@dataclass
class BM25Result:
    """BM25 search result."""
    text: str
    score: float
    doc_id: str
    metadata: Dict


class BM25Search:
    """
    BM25 lexical search for Indonesian documents.
    
    Features:
    - BM25Okapi algorithm
    - Indonesian tokenization
    - Document indexing
    - Batch search
    """
    
    def __init__(self, documents: Optional[List[Dict]] = None):
        """
        Initialize BM25 search.
        
        Args:
            documents: List of documents to index
        """
        self.documents = []
        self.corpus_tokens = []
        self.bm25 = None
        
        if documents:
            self.index_documents(documents)
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Indonesian text for BM25.
        Uses a module-level LRU cache so repeated tokenizations are instant.

        Args:
            text: Input text

        Returns:
            List of tokens (lowercase words)
        """
        return list(_tokenize_cached(text))
    
    def index_documents(self, documents: List[Dict]):
        """
        Index documents for BM25 search.
        
        Args:
            documents: List of dicts with 'text', 'doc_id', 'metadata'
        """
        self.documents = documents
        
        # Tokenize all documents
        self.corpus_tokens = [
            self.tokenize(doc['text'])
            for doc in documents
        ]
        
        # Create BM25 index
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)

        logger.debug(f"[OK] Indexed {len(documents)} documents for BM25 search")
    
    def search(
        self,
        query: str,
        n_results: int = 5
    ) -> List[BM25Result]:
        """
        Search documents using BM25.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of BM25Result sorted by score (descending)
        """
        if not self.bm25:
            return []
        
        # Tokenize query
        query_tokens = self.tokenize(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:n_results]
        
        # Create results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                doc = self.documents[idx]
                results.append(BM25Result(
                    text=doc['text'],
                    score=float(scores[idx]),
                    doc_id=doc.get('doc_id', f'doc_{idx}'),
                    metadata=doc.get('metadata', {})
                ))
        
        return results
    
    def get_stats(self) -> Dict:
        """Get BM25 index statistics."""
        return {
            'total_documents': len(self.documents),
            'avg_doc_length': sum(len(t) for t in self.corpus_tokens) / len(self.corpus_tokens) if self.corpus_tokens else 0,
            'vocab_size': len(set(token for doc in self.corpus_tokens for token in doc)),
        }


# =============================================================================
# DEMO & TESTING
# =============================================================================

def demo_bm25():
    """Demo BM25 search."""
    
    logger.info("[TEST] BM25 Search Demo")
    
    # Sample documents (Indonesian government docs)
    documents = [
        {
            'text': 'KTP elektronik adalah kartu tanda penduduk dengan chip elektronik untuk menyimpan data.',
            'doc_id': 'doc1',
            'metadata': {'type': 'Perpres'}
        },
        {
            'text': 'NIK adalah nomor induk kependudukan yang unik untuk setiap penduduk Indonesia.',
            'doc_id': 'doc2',
            'metadata': {'type': 'UU'}
        },
        {
            'text': 'BPJS Kesehatan memberikan jaminan kesehatan untuk seluruh rakyat Indonesia.',
            'doc_id': 'doc3',
            'metadata': {'type': 'PP'}
        },
        {
            'text': 'Kartu Keluarga memuat data tentang susunan anggota keluarga.',
            'doc_id': 'doc4',
            'metadata': {'type': 'Perpres'}
        },
    ]
    
    # Initialize BM25
    bm25 = BM25Search(documents)
    
    # Test queries
    queries = [
        "KTP elektronik",
        "nomor identitas",
        "kesehatan rakyat",
        "data keluarga"
    ]
    
    logger.info("[STAT] BM25 Index Stats:")
    stats = bm25.get_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    for query in queries:
        logger.info(f"[SEARCH] Query: '{query}'")
        results = bm25.search(query, n_results=2)

        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. Score: {result.score:.3f}")
            logger.info(f"     Text: {result.text[:60]}...")
            logger.info(f"     Doc: {result.doc_id}")

    logger.info("[OK] Demo complete!")


if __name__ == "__main__":
    demo_bm25()
