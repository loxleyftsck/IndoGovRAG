"""
Vector Store - ChromaDB Setup
For Indonesian Government Documents RAG

Features:
- ChromaDB local persistence
- Batch embedding generation
- Semantic search
- Metadata filtering
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
import time

import chromadb
from chromadb.config import Settings

from .query_expander import QueryExpander
from .bm25_search import BM25Search

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Vector search result."""
    chunk_id: str
    text: str
    score: float
    metadata: Dict


class VectorStore:
    """
    ChromaDB vector store for RAG.

    Uses multilingual-e5-base for Indonesian text embeddings.
    Optimizations:
    - Singleton embedding model (loaded once per process)
    - LRU-cached per-text embeddings in CustomEmbeddingFunction
    - Per-instance BM25 index cache in hybrid_search
    - In-memory search results cache (LRU, 128 entries)
    """

    # Class-level search results cache: max 128 entries, TTL 60s
    _search_cache: Dict[str, List] = {}
    _search_cache_meta: Dict[str, float] = {}
    _SEARCH_CACHE_MAX = 128
    _SEARCH_CACHE_TTL = 60.0

    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "indonesian_gov_docs",
        embedding_model: str = "intfloat/multilingual-e5-base"
    ):
        """
        Initialize vector store.

        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of collection
            embedding_model: HuggingFace embedding model
        """
        if persist_directory is None:
            persist_directory = "data/vector_db/chroma"
        self.persist_directory = Path(persist_directory).resolve().as_posix()
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Setup embedding function using our custom implementation
        from src.embeddings.custom_embeddings import CustomEmbeddingFunction
        self.embedding_function = CustomEmbeddingFunction()

        # Get or create collection — avoid embedding function conflict on existing collections
        existing = [c.name for c in self.client.list_collections()]
        if collection_name in existing:
            # Collection was created with a different embedding function; get it without re-specifying
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"[OK] Loaded existing collection '{collection_name}' ({self.collection.count()} chunks)")
        else:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )

        logger.info("[OK] Vector store initialized")
        logger.info("   Collection: %s", collection_name)
        logger.info("   Documents: %s", self.collection.count())
    
    # ─── In-memory search results cache ─────────────────────────────────────

    @staticmethod
    def _search_cache_key(query: str, n_results: int, filter_key: str) -> str:
        """Generate a cache key for search results."""
        return f"{query[:200]}|{n_results}|{filter_key}"

    @classmethod
    def _get_cached_results(cls, query: str, n_results: int,
                            filter_metadata: Optional[Dict]) -> Optional[List]:
        """Return cached search results if they exist and are fresh."""
        fk = str(sorted(filter_metadata.items())) if filter_metadata else ""
        key = cls._search_cache_key(query, n_results, fk)
        if key in cls._search_cache and key in cls._search_cache_meta:
            age = time.time() - cls._search_cache_meta[key]
            if age < cls._SEARCH_CACHE_TTL:
                logger.debug(f"[CACHE] Search cache hit ({age:.1f}s old)")
                return cls._search_cache[key]
        return None

    @classmethod
    def _cache_results(cls, query: str, n_results: int,
                       filter_metadata: Optional[Dict], results: List) -> None:
        """Store search results in the in-memory cache (LRU eviction)."""
        fk = str(sorted(filter_metadata.items())) if filter_metadata else ""
        key = cls._search_cache_key(query, n_results, fk)
        if len(cls._search_cache) >= cls._SEARCH_CACHE_MAX:
            oldest = min(cls._search_cache_meta, key=lambda k: cls._search_cache_meta[k])
            cls._search_cache.pop(oldest, None)
            cls._search_cache_meta.pop(oldest, None)
        cls._search_cache[key] = results
        cls._search_cache_meta[key] = time.time()

    def add_chunks(
        self,
        chunks: List[Dict],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> int:
        """
        Add document chunks to vector store.
        
        Args:
            chunks: List of chunk dicts with 'text', 'id', 'metadata'
            batch_size: Batch size for embedding generation
            show_progress: Show progress bar
        
        Returns:
            Number of chunks added
        """
        from tqdm import tqdm
        
        total_added = 0
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare batch data
            ids = [chunk['id'] for chunk in batch]
            texts = [chunk['text'] for chunk in batch]
            metadatas = [chunk['metadata'] for chunk in batch]
            
            # Add to collection (embeddings generated automatically)
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            total_added += len(batch)
            
            if show_progress:
                progress = (i + batch_size) / len(chunks) * 100
                logger.debug(f"  Progress: {min(progress, 100):.1f}% ({total_added}/{len(chunks)})")

        logger.info(f"[OK] Added {total_added} chunks to vector store")
        return total_added
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
        use_query_expansion: bool = False
    ) -> List[SearchResult]:
        """
        Semantic search for similar chunks.

        Results are cached in-memory for 60 seconds (LRU, 128 entries)
        to avoid redundant ChromaDB + embedding lookups on repeated queries.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            use_query_expansion: Expand query with synonyms

        Returns:
            List of SearchResult objects
        """
        # Fast path: serve from cache without embedding or DB calls
        cached = self._get_cached_results(query, n_results, filter_metadata)
        if cached is not None:
            return cached

        # Expand query if enabled
        if use_query_expansion:
            expander = QueryExpander()
            expanded = expander.expand(query)
            search_query = expanded.expanded
        else:
            search_query = query

        # Query collection — ChromaDB rejects empty {} as "where" filter
        _chroma_where = filter_metadata if filter_metadata else None
        results = self.collection.query(
            query_texts=[search_query],
            n_results=n_results,
            where=_chroma_where
        )

        # Parse results
        search_results = []

        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                result = SearchResult(
                    chunk_id=results['ids'][0][i],
                    text=results['documents'][0][i],
                    score=1 - results['distances'][0][i],  # Convert distance to similarity
                    metadata=results['metadatas'][0][i]
                )
                search_results.append(result)

        # Cache results keyed on the ORIGINAL query (before expansion)
        self._cache_results(query, n_results, filter_metadata, search_results)

        return search_results
    
    def hybrid_search(
        self,
        query: str,
        n_results: int = 5,
        alpha: float = 0.5,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Hybrid search combining BM25 (lexical) and semantic (vector) search.

        Args:
            query: Search query
            n_results: Number of results to return
            alpha: Fusion weight (0=BM25 only, 0.5=equal, 1=semantic only)
            filter_metadata: Optional metadata filters

        Returns:
            List of SearchResult objects with fused scores
        """
        # Guard against None filter_metadata
        if filter_metadata is None:
            filter_metadata = {}

        # Get semantic search results
        semantic_results = self.search(query, n_results=n_results * 2, filter_metadata=filter_metadata)

        if semantic_results is None:
            semantic_results = []

        if not semantic_results:
            return []

        # Build/cached BM25 index from corpus (cache key includes filter_metadata keys)
        cache_key = str(sorted(filter_metadata.items())) if filter_metadata else "__unfiltered__"
        if not hasattr(self, '_bm25_cache'):
            self._bm25_cache: Dict[str, BM25Search] = {}

        if cache_key not in self._bm25_cache:
            # Build BM25 index for this filter scope (limit2000 for performance)
            all_data = self.collection.get(
                where=filter_metadata if filter_metadata else None,
                limit=2000
            )

            if not all_data['documents']:
                self._bm25_cache[cache_key] = None
            else:
                bm25_docs = [
                    {
                        'text': doc,
                        'doc_id': doc_id,
                        'metadata': meta
                    }
                    for doc, doc_id, meta in zip(
                        all_data['documents'],
                        all_data['ids'],
                        all_data['metadatas']
                    )
                ]
                self._bm25_cache[cache_key] = BM25Search(bm25_docs)
                logger.debug(f"[BM25] Indexed {len(bm25_docs)} docs for hybrid search")

        bm25 = self._bm25_cache.get(cache_key)

        if not bm25:
            return semantic_results  # Fall back to semantic only

        bm25_results = bm25.search(query, n_results=n_results * 2)

        # Create score dictionaries
        semantic_scores = {r.chunk_id: r.score for r in semantic_results}
        bm25_scores = {r.doc_id: r.score for r in bm25_results}

        # Normalize scores to [0, 1]
        max_semantic = max(semantic_scores.values()) if semantic_scores else 1.0
        max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0

        # Prevent division by zero if all scores are 0
        max_semantic = max(max_semantic, 1e-10)
        max_bm25 = max(max_bm25, 1e-10)

        normalized_semantic = {k: v / max_semantic for k, v in semantic_scores.items()}
        normalized_bm25 = {k: v / max_bm25 for k, v in bm25_scores.items()}

        # Fuse scores: hybrid_score = alpha * semantic + (1-alpha) * bm25
        fused_scores = {}
        all_doc_ids = set(normalized_semantic.keys()) | set(normalized_bm25.keys())

        for doc_id in all_doc_ids:
            s_score = normalized_semantic.get(doc_id, 0.0)
            b_score = normalized_bm25.get(doc_id, 0.0)
            fused_scores[doc_id] = alpha * s_score + (1 - alpha) * b_score

        # Sort by fused score
        sorted_ids = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:n_results]

        # Build final results
        hybrid_results = []
        doc_map = {r.chunk_id: r for r in (semantic_results or [])}

        for doc_id, score in sorted_ids:
            if doc_id in doc_map:
                result = doc_map[doc_id]
                hybrid_results.append(SearchResult(
                    chunk_id=result.chunk_id,
                    text=result.text,
                    score=score,  # Use fused score
                    metadata={
                        **result.metadata,
                        'semantic_score': normalized_semantic.get(doc_id, 0.0),
                        'bm25_score': normalized_bm25.get(doc_id, 0.0),
                        'alpha': alpha
                    }
                ))

        return hybrid_results
    
    def get_stats(self) -> Dict:
        """Get vector store statistics."""
        stats = {
            'total_chunks': self.collection.count(),
            'collection_name': self.collection.name,
            'persist_directory': str(self.persist_directory),
        }
        
        # Get sample to analyze metadata
        if stats['total_chunks'] > 0:
            sample = self.collection.peek(limit=100)
            
            if sample['metadatas']:
                # Aggregate metadata
                doc_types = {}
                categories = {}
                
                for meta in sample['metadatas']:
                    doc_type = meta.get('doc_type', 'unknown')
                    category = meta.get('category', 'unknown')
                    
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                    categories[category] = categories.get(category, 0) + 1
                
                stats['doc_types'] = doc_types
                stats['categories'] = categories
        
        return stats
    
    def delete_all(self):
        """Delete all chunks from collection."""
        count = self.collection.count()
        
        if count > 0:
            # Get all IDs
            all_data = self.collection.get()
            
            if all_data['ids']:
                self.collection.delete(ids=all_data['ids'])
                logger.info("[DELETE] Deleted %s chunks", count)
        else:
            logger.info("[INFO] Collection already empty")
    
    def save_index(self, filepath: str = "data/vector_index_info.json"):
        """Save vector store index information."""
        stats = self.get_stats()
        
        index_info = {
            **stats,
            'embedding_model': 'intfloat/multilingual-e5-base',
            'embedding_dimension': 768,
            'distance_metric': 'cosine',
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(index_info, f, indent=2)
        
        logger.info("[SAVE] Index info saved to: %s", filepath)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def prepare_chunks_for_indexing(chunks: List) -> List[Dict]:
    """
    Convert Chunk objects to dict format for indexing.
    
    Args:
        chunks: List of Chunk objects from chunker.py
    
    Returns:
        List of dicts with 'id', 'text', 'metadata'
    """
    prepared = []
    
    for chunk in chunks:
        prepared.append({
            'id': f"{chunk.doc_id}_chunk_{chunk.chunk_id}",
            'text': chunk.text,
            'metadata': {
                **chunk.metadata,
                'doc_id': chunk.doc_id,
                'chunk_id': chunk.chunk_id,
                'num_tokens': chunk.num_tokens,
                'coherence_score': chunk.coherence_score or 0.0,
            }
        })
    
    return prepared


# =============================================================================
# TESTING
# =============================================================================

def demo_vector_store():
    """Demo vector store functionality."""

    logger.info("[TEST] Vector Store Demo\n")

    # Initialize vector store
    logger.info("[CONFIG] Initializing ChromaDB...")
    store = VectorStore()

    # Sample Indonesian government text chunks
    sample_chunks = [
        {
            'id': 'perpres_26_2009_chunk_0',
            'text': 'Kartu Tanda Penduduk (KTP) adalah identitas resmi penduduk sebagai bukti diri yang diterbitkan oleh Instansi Pelaksana yang berlaku di seluruh wilayah Negara Kesatuan Republik Indonesia.',
            'metadata': {
                'doc_id': 'perpres_26_2009',
                'doc_type': 'Perpres',
                'category': 'civil_administration',
                'year': '2009'
            }
        },
        {
            'id': 'perpres_26_2009_chunk_1',
            'text': 'Nomor Induk Kependudukan (NIK) adalah nomor identitas penduduk yang bersifat unik atau khas, tunggal dan melekat pada seseorang yang terdaftar sebagai Penduduk Indonesia.',
            'metadata': {
                'doc_id': 'perpres_26_2009',
                'doc_type': 'Perpres',
                'category': 'civil_administration',
                'year': '2009'
            }
        },
        {
            'id': 'pp_40_2019_chunk_0',
            'text': 'BPJS Kesehatan menyelenggarakan program Jaminan Kesehatan Nasional untuk memberikan jaminan kesehatan yang berkesinambungan bagi seluruh penduduk Indonesia.',
            'metadata': {
                'doc_id': 'pp_40_2019',
                'doc_type': 'PP',
                'category': 'social_assistance',
                'year': '2019'
            }
        }
    ]

    # Add chunks
    logger.info("Adding sample chunks...")
    store.add_chunks(sample_chunks, show_progress=False)

    # Get statistics
    logger.info("[STAT] Vector Store Statistics:")
    logger.info("=" * 60)
    stats = store.get_stats()
    for key, value in stats.items():
        logger.info(f"{key}: {value}")

    # Test search
    logger.info("[SEARCH] Semantic Search Test:")
    logger.info("=" * 60)

    queries = [
        "Apa itu KTP elektronik?",
        "Bagaimana cara mendaftar BPJS Kesehatan?",
        "Nomor identitas penduduk Indonesia"
    ]

    for query in queries:
        logger.info(f"Query: {query}")
        results = store.search(query, n_results=2)

        for i, result in enumerate(results, 1):
            logger.info(f"  Result {i}:")
            logger.info(f"    Score: {result.score:.3f}")
            logger.info(f"    Doc: {result.metadata.get('doc_id')}")
            logger.info(f"    Text: {result.text[:100]}...")

    # Save index info
    logger.info("Saving index information...")
    store.save_index()

    logger.info("[OK] Demo complete!")
    logger.info(f"ChromaDB persisted at: {store.persist_directory}")


if __name__ == "__main__":
    demo_vector_store()
