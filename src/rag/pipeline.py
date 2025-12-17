"""
RAG Pipeline - Complete Query System
Integrates all components for Indonesian government document Q&A
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.retrieval.vector_search import VectorStore
from src.llm.multi_tier_llm import MultiTierLLM
from src.rag.prompts import build_prompt, SYSTEM_PROMPT
from src.monitoring.gemini_quota_tracker import GeminiQuotaTracker


class RAGPipeline:
    """
    Complete RAG pipeline for Indonesian government documents.
    
    Components:
    1. Vector retrieval (ChromaDB + multilingual-e5-base)
    2. Multi-tier LLM (Gemini Pro → Flash → Local)
    3. Indonesian-optimized prompts
    4. Response generation with citations
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        llm: Optional[MultiTierLLM] = None,
        quota_tracker: Optional[GeminiQuotaTracker] = None,
        top_k: int = 5
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            vector_store: Vector store instance (created if None)
            llm: LLM instance (created if None)
            quota_tracker: Quota tracker (created if None)
            top_k: Number of chunks to retrieve
        """
        # Initialize vector store
        self.vector_store = vector_store or VectorStore()
        
        # Initialize quota tracker
        self.quota_tracker = quota_tracker or GeminiQuotaTracker()
        
        # Initialize LLM (load API key from .env if creating new instance)
        if llm:
            self.llm = llm
        else:
            from dotenv import load_dotenv
            import os
            
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                print("⚠️  GEMINI_API_KEY not found in .env file")
                print("   LLM will not work without API key")
                self.llm = None
            else:
                self.llm = MultiTierLLM(
                    gemini_api_key=api_key,
                    quota_tracker=self.quota_tracker
                )
        
        self.top_k = top_k
        
        print("✅ RAG Pipeline initialized")
        print(f"   Top-K: {top_k}")
        print(f"   Vector Store: {self.vector_store.collection.count()} chunks")
        print(f"   LLM: {'Ready' if self.llm else 'Not configured'}")
    
    def query(
        self,
        question: str,
        filter_metadata: Optional[Dict] = None,
        include_sources: bool = True
    ) -> Dict:
        """
        Query the RAG system.
        
        Args:
            question: User question in Indonesian
            filter_metadata: Optional metadata filters
            include_sources: Include source citations
        
        Returns:
            Dict with 'answer', 'sources', 'retrieved_chunks'
        """
        # 1. Retrieve relevant chunks
        print(f"\n🔍 Retrieving context for: {question[:50]}...")
        
        results = self.vector_store.search(
            query=question,
            n_results=self.top_k,
            filter_metadata=filter_metadata
        )
        
        if not results:
            return {
                'answer': "Maaf, saya tidak menemukan informasi yang relevan dalam dokumen.",
                'sources': [],
                'retrieved_chunks': [],
                'confidence': 0.0
            }
        
        print(f"   Found {len(results)} relevant chunks")
        
        # 2. Prepare chunks for prompting
        chunks = []
        for result in results:
            chunks.append({
                'text': result.text,
                'metadata': result.metadata,
                'score': result.score
            })
        
        # 3. Build prompt
        prompt = build_prompt(
            question=question,
            chunks=chunks,
            include_metadata=include_sources
        )
        
        # 4. Generate answer with LLM
        if not self.llm:
            return {
                'answer': "LLM tidak tersedia. Pastikan GEMINI_API_KEY sudah diatur di .env file.",
                'sources': [],
                'retrieved_chunks': chunks,
                'confidence': 0.0,
                'model_used': 'none'
            }
        
        print("🤖 Generating answer with Gemini...")
        
        response = self.llm.generate(
            prompt=prompt
        )
        
        answer = response['text']
        model_used = response['model']
        
        print(f"   Model: {model_used}")
        print(f"   Answer length: {len(answer)} chars")
        
        # 5. Format sources
        sources = []
        if include_sources:
            seen_docs = set()
            for chunk in chunks:
                doc_id = chunk['metadata'].get('doc_id', 'Unknown')
                if doc_id not in seen_docs:
                    sources.append({
                        'doc_id': doc_id,
                        'doc_type': chunk['metadata'].get('doc_type', ''),
                        'year': chunk['metadata'].get('year', ''),
                        'score': chunk['score']
                    })
                    seen_docs.add(doc_id)
        
        # 6. Calculate confidence (average retrieval score)
        confidence = sum(c['score'] for c in chunks) / len(chunks)
        
        return {
            'answer': answer,
            'sources': sources,
            'retrieved_chunks': chunks,
            'confidence': confidence,
            'model_used': model_used
        }
    
    def get_stats(self) -> Dict:
        """Get pipeline statistics."""
        return {
            'vector_store_chunks': self.vector_store.collection.count(),
            'quota_stats': self.quota_tracker.get_stats(),
            'llm_stats': self.llm.get_stats()
        }


# =============================================================================
# DEMO & TESTING
# =============================================================================

def demo_rag_pipeline():
    """Demo RAG pipeline with sample queries."""
    
    print("🧪 RAG Pipeline Demo\n")
    print("="*60)
    
    # Check if vector store has data
    store = VectorStore()
    
    if store.collection.count() == 0:
        print("⚠️  Vector store is empty!")
        print("   Run vector_search.py demo first to add sample data")
        return
    
    # Initialize pipeline
    print("\n🔧 Initializing RAG Pipeline...")
    rag = RAGPipeline(vector_store=store, top_k=3)
    
    # Sample Indonesian queries
    queries = [
        "Apa itu KTP elektronik?",
        "Siapa yang wajib memiliki KTP?",
        "Apa fungsi Nomor Induk Kependudukan?",
    ]
    
    print("\n" + "="*60)
    print("📝 Testing Queries")
    print("="*60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {query}")
        print("="*60)
        
        # Query RAG
        result = rag.query(query)
        
        # Display results
        print(f"\n💬 Answer:")
        print(f"{result['answer']}")
        
        print(f"\n📚 Sources ({len(result['sources'])}):")
        for source in result['sources']:
            print(f"  - {source['doc_type']} {source['doc_id']} ({source['year']}) [Score: {source['score']:.3f}]")
        
        print(f"\n📊 Confidence: {result['confidence']:.2%}")
        print(f"🤖 Model: {result['model_used']}")
    
    # Pipeline stats
    print(f"\n{'='*60}")
    print("📈 Pipeline Statistics")
    print("="*60)
    stats = rag.get_stats()
    print(f"Vector Store Chunks: {stats['vector_store_chunks']}")
    print(f"LLM Calls: {stats['llm_stats']['total_calls']}")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo_rag_pipeline()
