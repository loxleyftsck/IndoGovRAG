"""
Vector Store - ChromaDB Setup
For Indonesian Government Documents RAG

Features:
- ChromaDB local persistence
- Batch embedding generation
- Semantic search
- Metadata filtering
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import json


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
    """
    
    def __init__(
        self,
        persist_directory: str = "data/vector_db/chroma",
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
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Setup embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model,
            device="cpu"  # Use "cuda" if GPU available
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )
        
        print(f"✅ Vector store initialized")
        print(f"   Collection: {collection_name}")
        print(f"   Documents: {self.collection.count()}")
    
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
                print(f"  Progress: {min(progress, 100):.1f}% ({total_added}/{len(chunks)})")
        
        print(f"✅ Added {total_added} chunks to vector store")
        return total_added
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Semantic search for similar chunks.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of SearchResult objects
        """
        # Query collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata
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
        from .bm25_search import BM25Search
        
        # Get semantic search results
        semantic_results = self.search(query, n_results=n_results * 2, filter_metadata=filter_metadata)
        
        if not semantic_results:
            return []
        
        # Initialize BM25 with current corpus
        all_data = self.collection.get(
            where=filter_metadata,
            limit=1000  # Limit for performance
        )
        
        if not all_data['documents']:
            return semantic_results  # Fall back to semantic only
        
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
        
        bm25 = BM25Search(bm25_docs)
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
        doc_map = {r.chunk_id: r for r in semantic_results}
        
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
                print(f"🗑️  Deleted {count} chunks")
        else:
            print("ℹ️  Collection already empty")
    
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
        
        print(f"💾 Index info saved to: {filepath}")


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
    
    print("🧪 Vector Store Demo\n")
    
    # Initialize vector store
    print("🔧 Initializing ChromaDB...")
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
    print("\n📥 Adding sample chunks...")
    store.add_chunks(sample_chunks, show_progress=False)
    
    # Get statistics
    print("\n📊 Vector Store Statistics:")
    print("="*60)
    stats = store.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Test search
    print("\n🔍 Semantic Search Test:")
    print("="*60)
    
    queries = [
        "Apa itu KTP elektronik?",
        "Bagaimana cara mendaftar BPJS Kesehatan?",
        "Nomor identitas penduduk Indonesia"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = store.search(query, n_results=2)
        
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Score: {result.score:.3f}")
            print(f"    Doc: {result.metadata.get('doc_id')}")
            print(f"    Text: {result.text[:100]}...")
    
    # Save index info
    print("\n💾 Saving index information...")
    store.save_index()
    
    print("\n✅ Demo complete!")
    print(f"\n📍 ChromaDB persisted at: {store.persist_directory}")


if __name__ == "__main__":
    demo_vector_store()
