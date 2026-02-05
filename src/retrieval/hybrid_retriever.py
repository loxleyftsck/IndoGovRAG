"""
Hybrid Retrieval: BM25 (Keyword) + Dense (Semantic) Fusion
Optimized for Indonesian legal documents
"""

from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
import numpy as np
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """Single retrieval result with score"""
    doc_id: str
    text: str
    score: float
    metadata: Dict[str, Any]
    rank: int
    source: str  # 'bm25', 'dense', or 'hybrid'


class HybridRetriever:
    """
    Hybrid retrieval combining keyword (BM25) and semantic (dense) search
    
    Fusion methods:
    - Reciprocal Rank Fusion (RRF) - rank-based, robust
    - Linear combination - score-based
    - Weighted fusion - configurable weights
    """
    
    def __init__(
        self,
        vector_store,  # ChromaDB or similar
        fusion_method: str = "rrf",  # 'rrf', 'linear', 'weighted'
        bm25_weight: float = 0.3,
        dense_weight: float = 0.7,
        top_k: int = 5
    ):
        """
        Initialize hybrid retriever
        
        Args:
            vector_store: Dense vector store (ChromaDB)
            fusion_method: Fusion strategy
            bm25_weight: Weight for BM25 scores (linear/weighted)
            dense_weight: Weight for dense scores (linear/weighted)
            top_k: Number of results to return
        """
        self.vector_store = vector_store
        self.fusion_method = fusion_method
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.top_k = top_k
        
        # BM25 index (lazy loaded)
        self.bm25_index: Optional[BM25Okapi] = None
        self.bm25_corpus: List[Dict] = []
        
        print(f"✅ Hybrid Retriever initialized")
        print(f"   Fusion: {fusion_method}")
        print(f"   Weights: BM25={bm25_weight}, Dense={dense_weight}")
    
    def build_bm25_index(self, documents: List[Dict]):
        """
        Build BM25 index from documents
        
        Args:
            documents: List of document dicts with 'text' and 'metadata'
        """
        # Tokenize documents (simple word-based for now)
        tokenized_corpus = [
            doc["text"].lower().split()
            for doc in documents
        ]
        
        # Build BM25 index
        self.bm25_index = BM25Okapi(tokenized_corpus)
        self.bm25_corpus = documents
        
        print(f"✅ BM25 index built with {len(documents)} documents")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """
        Perform hybrid retrieval
        
        Args:
            query: Search query
            top_k: Number of results (overrides instance default)
            filter_metadata: Optional metadata filters
            
        Returns:
            List of retrieval results, sorted by score
        """
        k = top_k or self.top_k
        
        # 1. BM25 retrieval (keyword)
        bm25_results = self._bm25_search(query, k=k*2)  # Get more for fusion
        
        # 2. Dense retrieval (semantic)
        dense_results = self._dense_search(query, k=k*2, filter_metadata=filter_metadata)
        
        # 3. Fuse results
        if self.fusion_method == "rrf":
            fused = self._reciprocal_rank_fusion(bm25_results, dense_results, k=k)
        elif self.fusion_method == "linear":
            fused = self._linear_fusion(bm25_results, dense_results, k=k)
        elif self.fusion_method == "weighted":
            fused = self._weighted_fusion(bm25_results, dense_results, k=k)
        else:
            raise ValueError(f"Unknown fusion method: {self.fusion_method}")
        
        return fused[:k]
    
    def _bm25_search(self, query: str, k: int) -> List[RetrievalResult]:
        """BM25 keyword search"""
        if self.bm25_index is None or not self.bm25_corpus:
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:k]
        
        results = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] > 0:  # Only include if there's some relevance
                doc = self.bm25_corpus[idx]
                results.append(RetrievalResult(
                    doc_id=doc.get("doc_id", f"bm25_{idx}"),
                    text=doc["text"],
                    score=float(scores[idx]),
                    metadata=doc.get("metadata", {}),
                    rank=rank + 1,
                    source="bm25"
                ))
        
        return results
    
    def _dense_search(
        self,
        query: str,
        k: int,
        filter_metadata: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """Dense vector search"""
        # Query vector store
        vector_results = self.vector_store.search(
            query=query,
            n_results=k,
            filter_metadata=filter_metadata
        )
        
        results = []
        for rank, result in enumerate(vector_results[:k]):
            results.append(RetrievalResult(
                doc_id=result.metadata.get("doc_id", f"dense_{rank}"),
                text=result.text,
                score=result.score,
                metadata=result.metadata,
                rank=rank + 1,
                source="dense"
            ))
        
        return results
    
    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[RetrievalResult],
        dense_results: List[RetrievalResult],
        k: int,
        rrf_k: int = 60  # RRF constant
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion (RRF)
        Score = sum(1 / (k + rank)) for each list
        """
        # Collect all unique documents
        doc_scores = {}
        
        # Add BM25 ranks
        for result in bm25_results:
            doc_id = result.doc_id
            rrf_score = 1.0 / (rrf_k + result.rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
        
        # Add dense ranks
        for result in dense_results:
            doc_id = result.doc_id
            rrf_score = 1.0 / (rrf_k + result.rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
        
        # Create combined results
        doc_map = {}
        for result in bm25_results + dense_results:
            if result.doc_id not in doc_map:
                doc_map[result.doc_id] = result
        
        # Sort by RRF score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]
        
        combined = []
        for rank, (doc_id, score) in enumerate(sorted_docs):
            result = doc_map[doc_id]
            combined.append(RetrievalResult(
                doc_id=doc_id,
                text=result.text,
                score=score,
                metadata=result.metadata,
                rank=rank + 1,
                source="hybrid"
            ))
        
        return combined
    
    def _linear_fusion(
        self,
        bm25_results: List[RetrievalResult],
        dense_results: List[RetrievalResult],
        k: int
    ) -> List[RetrievalResult]:
        """
        Linear score combination
        Score_final = w1 * Score_BM25_norm + w2 * Score_dense_norm
        """
        # Normalize scores to [0, 1]
        bm25_scores = [r.score for r in bm25_results]
        dense_scores = [r.score for r in dense_results]
        
        if bm25_scores:
            max_bm25 = max(bm25_scores)
            if max_bm25 > 0:
                for r in bm25_results:
                    r.score = r.score / max_bm25
        
        if dense_scores:
            max_dense = max(dense_scores)
            if max_dense > 0:
                for r in dense_results:
                    r.score = r.score / max_dense
        
        # Combine scores
        doc_scores = {}
        doc_map = {}
        
        for result in bm25_results:
            doc_id = result.doc_id
            doc_scores[doc_id] = self.bm25_weight * result.score
            doc_map[doc_id] = result
        
        for result in dense_results:
            doc_id = result.doc_id
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + self.dense_weight * result.score
            if doc_id not in doc_map:
                doc_map[doc_id] = result
        
        # Sort and return
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]
        
        combined = []
        for rank, (doc_id, score) in enumerate(sorted_docs):
            result = doc_map[doc_id]
            combined.append(RetrievalResult(
                doc_id=doc_id,
                text=result.text,
                score=score,
                metadata=result.metadata,
                rank=rank + 1,
                source="hybrid"
            ))
        
        return combined
    
    def _weighted_fusion(
        self,
        bm25_results: List[RetrievalResult],
        dense_results: List[RetrievalResult],
        k: int
    ) -> List[Retrieval Result]:
        """Weighted fusion (alias for linear with configurable weights)"""
        return self._linear_fusion(bm25_results, dense_results, k)


# Singleton
_hybrid_retriever = None

def get_hybrid_retriever(vector_store, **kwargs) -> HybridRetriever:
    """Get or create global hybrid retriever instance"""
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever(vector_store=vector_store, **kwargs)
    return _hybrid_retriever
