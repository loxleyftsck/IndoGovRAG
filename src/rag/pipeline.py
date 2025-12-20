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
        top_k: int = 3  # Reduced from 5 for faster retrieval
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
                print()
                print("   For experiments, API key is REQUIRED.")
                print("   Add to .env file: GEMINI_API_KEY=your_key_here")
                print()
                raise ValueError(
                    "GEMINI_API_KEY required for RAG experiments. "
                    "Add to .env file or set LLM_REQUIRED=false for testing."
                )
            
            self.llm = MultiTierLLM(
                gemini_api_key=api_key,
                quota_tracker=self.quota_tracker
            )
        
        self.top_k = top_k
        
        # Week 3: Experiment configuration
        self.config = None
        self.last_token_count = 0
        
        print("✅ RAG Pipeline initialized")
        print(f"   Top-K: {top_k}")
        print(f"   Vector Store: {self.vector_store.collection.count()} chunks")
        print(f"   LLM: {'Ready' if self.llm else 'Not configured'}")
    
    def configure(self, config):
        """
        Apply experiment configuration for Week 3 A/B testing.
        
        Args:
            config: ExperimentConfig object or dict with parameters
        """
        # Support both ExperimentConfig objects and dicts
        if hasattr(config, '__dict__'):
            self.config = config
        else:
            # Simple dict-based config
            from types import SimpleNamespace
            self.config = SimpleNamespace(**config)
        
        # Update parameters
        if hasattr(self.config, 'top_k'):
            self.top_k = self.config.top_k
        
        print(f"🔧 Pipeline configured:")
        print(f"   Retrieval: {getattr(self.config, 'retrieval_method', 'vector')}")
        print(f"   Chunk size: {getattr(self.config, 'chunk_size', 512)}")
        print(f"   Top-K: {self.top_k}")
        print(f"   Alpha: {getattr(self.config, 'alpha', 1.0)}")

    
    def query(
        self,
        question: str,
        filter_metadata: Optional[Dict] = None,
        include_sources: bool = True
    ) -> Dict:
        """
        Query the RAG system with comprehensive error handling.
        
        Args:
            question: User question in Indonesian
            filter_metadata: Optional metadata filters
            include_sources: Include source citations
        
        Returns:
            Dict with 'answer', 'sources', 'retrieved_chunks'
        """
        import time
        query_start = time.time()
        stage_times = {}  # Track timing for each stage
        
        # 1. Retrieve relevant chunks (based on config or default to vector)
        retrieval_start = time.time()
        print(f"\n🔍 Retrieving context for: {question[:50]}...")
        
        retrieval_method = getattr(self.config, 'retrieval_method', 'vector') if self.config else 'vector'
        alpha = getattr(self.config, 'alpha', 1.0) if self.config else 1.0
        
        # Choose retrieval method
        if retrieval_method == 'hybrid':
            results = self.vector_store.hybrid_search(
                query=question,
                n_results=self.top_k,
                alpha=alpha,
                filter_metadata=filter_metadata
            )
        else:
            # Vector-only (default)
            results = self.vector_store.search(
                query=question,
                n_results=self.top_k,
                filter_metadata=filter_metadata
            )
        
        # Enhanced None check
        if results is None or not results:
            print(f"   ⚠️ No results returned from vector store")
            return {
                'answer': "Maaf, saya tidak menemukan informasi yang relevan dalam dokumen.",
                'sources': [],
                'contexts': [],
                'retrieved_chunks': [],
                'confidence': 0.0,
                'tokens_used': 0
            }
        
        print(f"   Method: {retrieval_method}")
        if retrieval_method == 'hybrid':
            print(f"   Alpha: {alpha} ({'vector' if alpha > 0.7 else 'BM25' if alpha < 0.3 else 'balanced'})")
        print(f"   Found {len(results)} relevant chunks")
        stage_times['retrieval'] = (time.time() - retrieval_start) * 1000
        print(f"   ⏱️ Retrieval: {stage_times['retrieval']:.0f}ms")
        
        # 2. Prepare chunks for prompting
        chunks = []
        try:
            for result in results:
                # Handle both SearchResult objects and dicts
                if hasattr(result, 'text'):
                    # SearchResult object
                    chunks.append({
                        'text': result.text,
                        'metadata': result.metadata,
                        'score': result.score
                    })
                elif isinstance(result, dict):
                    # Dict format
                    chunks.append({
                        'text': result.get('text', ''),
                        'metadata': result.get('metadata', {}),
                        'score': result.get('score', 0.0)
                    })
                else:
                    print(f"   ⚠️ Unknown result type: {type(result)}")
        except Exception as e:
            print(f"   ❌ Error processing results: {e}")
            return {
                'answer': f"Maaf, terjadi kesalahan saat memproses hasil pencarian: {str(e)}",
                'sources': [],
                'contexts': [],
                'retrieved_chunks': [],
                'confidence': 0.0,
                'tokens_used': 0
            }
        
        # 3. Build prompt
        prompt_start = time.time()
        prompt = build_prompt(
            question=question,
            chunks=chunks,
            include_metadata=include_sources
        )
        stage_times['prompt_build'] = (time.time() - prompt_start) * 1000
        print(f"   ⏱️ Prompt building: {stage_times['prompt_build']:.0f}ms")
        
        # 4. Generate answer with LLM
        if not self.llm:
            return {
                'answer': "Maaf, fitur AI tidak tersedia saat ini.",
                'sources': [],
                'retrieved_chunks': chunks,
                'contexts': [],
                'confidence': 0.0,
                'model_used': 'none',
                'tokens_used': 0
            }
        
        print("🤖 Generating answer with Gemini...")
        
        try:
            response = self.llm.generate(
                prompt=prompt
            )
        except Exception as llm_error:
            print(f"   ❌ LLM generation failed: {llm_error}")
            return {
                'answer': "Maaf, AI mengalami kesulitan memproses pertanyaan Anda. Silakan coba lagi.",
                'sources': [],
                'retrieved_chunks': chunks,
                'contexts': [c['text'] for c in chunks],
                'confidence': 0.0,
                'model_used': 'error',
                'tokens_used': 0
            }
        
        answer = response['text']
        model_used = response['model']
        stage_times['llm_generation'] = (time.time() - retrieval_start - stage_times['retrieval']/1000 - stage_times['prompt_build']/1000) * 1000
        
        print(f"   Model: {model_used}")
        print(f"   Answer length: {len(answer)} chars")
        print(f"   ⏱️ LLM generation: {stage_times.get('llm_generation', 0):.0f}ms")
        
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
        confidence = sum(c['score'] for c in chunks) / len(chunks) if chunks else 0.0
        
        # 7. Track token usage
        self.last_token_count = response.get('tokens', 0)
        
        # 8. Profiling summary
        total_time = (time.time() - query_start) * 1000
        print(f"\n📊 Performance Profile:")
        print(f"   Total: {total_time:.0f}ms")
        print(f"   Breakdown: Retrieval={stage_times.get('retrieval', 0):.0f}ms, "
              f"Prompt={stage_times.get('prompt_build', 0):.0f}ms, "
              f"LLM={stage_times.get('llm_generation', 0):.0f}ms")
        
        # 9. Prepare contexts list for RAGAS
        contexts = [c['text'] for c in chunks]
        
        return {
            'answer': answer,
            'sources': sources,
            'contexts': contexts,  # For RAGAS evaluation
            'retrieved_chunks': chunks,
            'confidence': confidence,
            'model_used': model_used,
            'tokens_used': self.last_token_count
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
