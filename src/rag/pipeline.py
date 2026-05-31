"""
RAG Pipeline - Complete Query System
Integrates all components for Indonesian government document Q&A
"""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Configure module logger
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.retrieval.vector_search import VectorStore
from src.llm.multi_tier_llm import MultiTierLLM
from src.rag.prompts import build_prompt, SYSTEM_PROMPT
from src.monitoring.gemini_quota_tracker import GeminiQuotaTracker
from src.retrieval.query_expander import QueryExpander
from src.retrieval.reranker import LLMReranker
from src.retrieval.query_cache import QueryCache


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
        # VectorStore.__init__ creates a new CustomEmbeddingFunction each time,
        # which now delegates to a globally-cached model — no reloading overhead.
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
            groq_key = os.getenv("GROQ_API_KEY")
            gemini_key = os.getenv("GEMINI_API_KEY")

            if groq_key:
                logger.info("[TRY] Using Groq as primary LLM (fastest)")
                self.llm = MultiTierLLM(
                    groq_api_key=groq_key,
                    gemini_api_key=gemini_key,
                    quota_tracker=self.quota_tracker
                )
            elif gemini_key:
                logger.warning("[WARN] Using Gemini (Groq not configured)")
                self.llm = MultiTierLLM(
                    gemini_api_key=gemini_key,
                    quota_tracker=self.quota_tracker
                )
            else:
                logger.warning("[WARN] No LLM API key found!")
                logger.warning("Add GROQ_API_KEY to .env for fastest results")
                logger.warning("Or add GEMINI_API_KEY as backup")
                raise ValueError(
                    "GROQ_API_KEY or GEMINI_API_KEY required. "
                    "Add to .env file."
                )
        
        self.top_k = top_k
        
        # Week 3: Experiment configuration
        self.config = None
        self.last_token_count = 0

        # Initialize optional components
        self.query_expander = QueryExpander()
        self.reranker = None  # Lazy init - only if needed
        self.query_cache = QueryCache(max_size=1000, default_ttl=3600)  # 1 hour TTL

        logger.info("[OK] RAG Pipeline initialized")
        logger.info(f"   Top-K: {top_k}")
        logger.info(f"   Vector Store: {self.vector_store.collection.count()} chunks")
        logger.info(f"   LLM: {'Ready' if self.llm else 'Not configured'}")
    
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
        
        logger.info(f"[CONFIG] Pipeline configured:")
        logger.info(f"   Retrieval: {getattr(self.config, 'retrieval_method', 'vector')}")
        logger.info(f"   Chunk size: {getattr(self.config, 'chunk_size', 512)}")
        logger.info(f"   Top-K: {self.top_k}")
        logger.info(f"   Alpha: {getattr(self.config, 'alpha', 1.0)}")

    
    def query(
        self,
        question: str,
        filter_metadata: Optional[Dict] = None,
        include_sources: bool = True,
        use_cache: bool = True,
        custom_groq_key: Optional[str] = None,
        custom_gemini_key: Optional[str] = None
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

        # Check cache first (if enabled)
        if use_cache and self.query_cache:
            cached = self.query_cache.get(question)
            if cached:
                logger.info(f"[CACHE] Hit! Returning cached result")
                return {
                    **cached,
                    'from_cache': True,
                    'answer': f"[Cached] {cached['answer']}"  # Mark as cached
                }

        # 0. Optional query expansion
        use_expansion = getattr(self.config, 'use_query_expansion', True) if self.config else True
        use_reranking = getattr(self.config, 'use_reranking', False) if self.config else False

        expanded_query = question
        if use_expansion and self.query_expander:
            expanded = self.query_expander.expand(question)
            if expanded.expansion_count > 0:
                expanded_query = expanded.expanded
                logger.info(f"   Expanded: {expanded.added_terms}")

        # 1. Retrieve relevant chunks (based on config or default to vector)
        retrieval_start = time.time()
        logger.info(f"Retrieving context for: {question[:50]}...")
        
        retrieval_method = getattr(self.config, 'retrieval_method', 'vector') if self.config else 'vector'
        alpha = getattr(self.config, 'alpha', 1.0) if self.config else 1.0
        
        # Choose retrieval method (use expanded query)
        if retrieval_method == 'hybrid':
            results = self.vector_store.hybrid_search(
                query=expanded_query,
                n_results=self.top_k,
                alpha=alpha,
                filter_metadata=filter_metadata
            )
        else:
            # Vector-only (default)
            results = self.vector_store.search(
                query=expanded_query,
                n_results=self.top_k,
                filter_metadata=filter_metadata
            )
        
        # Enhanced None check
        if results is None or not results:
            logger.warning(f"   [WARN] No results returned from vector store")
            return {
                'answer': "Maaf, saya tidak menemukan informasi yang relevan dalam dokumen.",
                'sources': [],
                'contexts': [],
                'retrieved_chunks': [],
                'confidence': 0.0,
                'tokens_used': 0
            }
        
        logger.info(f"   Method: {retrieval_method}")
        if retrieval_method == 'hybrid':
            logger.info(f"   Alpha: {alpha} ({'vector' if alpha > 0.7 else 'BM25' if alpha < 0.3 else 'balanced'})")
        logger.info(f"   Found {len(results)} relevant chunks")
        stage_times['retrieval'] = (time.time() - retrieval_start) * 1000
        logger.debug(f"   [TIME] Retrieval: {stage_times['retrieval']:.0f}ms")

        # 1b. Optional LLM re-ranking
        if use_reranking and results:
            logger.info("   [RANK] Re-ranking with LLM...")
            if self.reranker is None:
                self.reranker = LLMReranker()

            # Build a working list from results
            results_list = []
            for result in results:
                if hasattr(result, 'text'):
                    results_list.append({
                        'text': result.text,
                        'metadata': result.metadata,
                        'score': result.score
                    })
                else:
                    results_list.append({
                        'text': result.get('text', ''),
                        'metadata': result.get('metadata', {}),
                        'score': result.get('score', 0.0)
                    })

            try:
                ranked_chunks = []
                for chunk in results_list:
                    relevance = self.reranker.score_relevance(question, chunk['text'])
                    # Combine original score with relevance
                    combined = (chunk['score'] * 0.5 + (relevance / 10) * 0.5)
                    ranked_chunks.append({
                        **chunk,
                        'relevance_score': relevance,
                        'score': combined
                    })

                # Re-sort by combined score
                sorted_results = sorted(ranked_chunks, key=lambda x: x['score'], reverse=True)
                logger.info(f"   Re-ranked {len(sorted_results)} chunks")
            except Exception as e:
                logger.warning(f"   [WARN] Re-ranking failed, using original order: {e}")
        
        # 2. Prepare chunks for prompting
        # Use re-ranked results if available, otherwise rebuild from results
        if use_reranking and results and 'sorted_results' in dir() and sorted_results:
            chunks = sorted_results
        else:
            chunks = []
            for result in results:
                if hasattr(result, 'text'):
                    chunks.append({
                        'text': result.text,
                        'metadata': result.metadata,
                        'score': result.score
                    })
                elif isinstance(result, dict):
                    chunks.append({
                        'text': result.get('text', ''),
                        'metadata': result.get('metadata', {}),
                        'score': result.get('score', 0.0)
                    })
                else:
                    logger.warning(f"   [WARN] Unknown result type: {type(result)}")

        # 3. Build prompt
        prompt_start = time.time()
        prompt = build_prompt(
            question=question,
            chunks=chunks,
            include_metadata=include_sources
        )
        stage_times['prompt_build'] = (time.time() - prompt_start) * 1000
        logger.debug(f"   [TIME] Prompt building: {stage_times['prompt_build']:.0f}ms")
        
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
        
        logger.info("[AI] Generating answer with Groq/Gemini...")

        try:
            response = self.llm.generate(
                prompt=prompt,
                custom_groq_key=custom_groq_key,
                custom_gemini_key=custom_gemini_key
            )
        except Exception as llm_error:
            logger.error(f"   [ERR] LLM generation failed: {llm_error}")
            return {
                'answer': "Maaf, AI mengalami kesulitan memproses pertanyaan Anda. Silakan coba lagi.",
                'sources': [],
                'retrieved_chunks': chunks,
                'contexts': [c['text'] for c in chunks],
                'confidence': 0.0,
                'model_used': 'error',
                'tokens_used': 0
            }

        # Handle both GroqResponse and LLMResponse formats
        answer = response.text if hasattr(response, 'text') else response.get('text', '')
        model_used = response.model_used if hasattr(response, 'model_used') else response.get('model', 'unknown')
        tokens_used = response.tokens_used if hasattr(response, 'tokens_used') else response.get('tokens', 0)

        # Fix unit mismatch: retrieval_start is seconds, stage_times are ms
        llm_end = time.time()
        stage_times['llm_generation'] = (llm_end - retrieval_start) * 1000 - stage_times['retrieval'] - stage_times['prompt_build']

        logger.info(f"   Model: {model_used}")
        logger.debug(f"   Answer length: {len(answer)} chars")
        logger.debug(f"   [TIME] LLM generation: {stage_times.get('llm_generation', 0):.0f}ms")
        
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
        self.last_token_count = tokens_used
        
        # 8. Profiling summary
        total_time = (time.time() - query_start) * 1000
        logger.info(f"[STAT] Performance Profile:")
        logger.info(f"   Total: {total_time:.0f}ms")
        logger.info(f"   Breakdown: Retrieval={stage_times.get('retrieval', 0):.0f}ms, "
              f"Prompt={stage_times.get('prompt_build', 0):.0f}ms, "
              f"LLM={stage_times.get('llm_generation', 0):.0f}ms")
        
        # 9. Prepare contexts list for RAGAS
        contexts = [c['text'] for c in chunks]

        # Cache the result (before return)
        cache_result = {
            'answer': answer,
            'sources': sources,
            'contexts': contexts,
            'retrieved_chunks': chunks,
            'confidence': confidence,
            'model_used': model_used,
            'tokens_used': self.last_token_count,
            'from_cache': False
        }
        if use_cache and self.query_cache:
            self.query_cache.put(question, cache_result)

        return cache_result
    
    def get_stats(self) -> Dict:
        """Get pipeline statistics."""
        cache_stats = {}
        if self.query_cache:
            cache_stats = {
                'cache_size': len(self.query_cache.cache),
                'cache_hits': self.query_cache.hits,
                'cache_misses': self.query_cache.misses,
                'cache_hit_rate': (
                    self.query_cache.hits / max(1, self.query_cache.hits + self.query_cache.misses)
                )
            }

        return {
            'vector_store_chunks': self.vector_store.collection.count(),
            'quota_stats': self.quota_tracker.get_stats(),
            'llm_stats': self.llm.get_stats(),
            **cache_stats
        }


# =============================================================================
# DEMO & TESTING
# =============================================================================

def demo_rag_pipeline():
    """Demo RAG pipeline with sample queries."""

    logger.info("[TEST] RAG Pipeline Demo")
    logger.info("="*60)

    # Check if vector store has data
    store = VectorStore()

    if store.collection.count() == 0:
        logger.warning("[WARN] Vector store is empty!")
        logger.warning("   Run vector_search.py demo first to add sample data")
        return

    # Initialize pipeline
    logger.info("Initializing RAG Pipeline...")
    rag = RAGPipeline(vector_store=store, top_k=3)

    # Sample Indonesian queries
    queries = [
        "Apa itu KTP elektronik?",
        "Siapa yang wajib memiliki KTP?",
        "Apa fungsi Nomor Induk Kependudukan?",
    ]

    logger.info("Testing Queries")
    logger.info("="*60)

    for i, query in enumerate(queries, 1):
        logger.info(f"Query {i}: {query}")

        # Query RAG
        result = rag.query(query)

        # Display results
        logger.info(f"[CHAT] Answer: {result['answer']}")
        logger.info(f"Sources ({len(result['sources'])}): {result['sources']}")
        logger.info(f"Confidence: {result['confidence']:.2%}")
        logger.info(f"Model: {result['model_used']}")

    # Pipeline stats
    stats = rag.get_stats()
    logger.info(f"Vector Store Chunks: {stats['vector_store_chunks']}")
    logger.info(f"LLM Calls: {stats['llm_stats']['total_calls']}")
    logger.info("[OK] Demo complete!")


if __name__ == "__main__":
    demo_rag_pipeline()
