"""
Optimized RAG Pipeline with Phase 1.5 Integrations
Integrates compression, caching, rollout manager, and metrics

Part of Phase 1.5 BET-004
"""

import time
import logging
from typing import Dict, List, Optional

from src.rag.pipeline import RAGPipeline as BaseRAGPipeline
from src.compression.context_compressor import ContextCompressor
from src.caching.semantic_cache import SemanticCache
from src.monitoring.cost_tracker import get_cost_tracker
from src.evaluation.online_evaluator import get_online_evaluator
from src.safety.rollout_manager import get_rollout_manager
from config.config_manager import get_config_manager

# Metrics
from src.monitoring.metrics import (
    observe_compression_latency,
    observe_cache_latency,
    track_cache_hit,
    track_cache_miss,
    track_cost_savings,
    track_tokens,
    track_quality_score,
    observe_latency
)

logger = logging.getLogger(__name__)


class OptimizedRAGPipeline(BaseRAGPipeline):
    """
    RAG Pipeline with Phase 1.5 optimizations
    
    Features:
    - Context compression (30% token reduction)
    - Semantic caching (52% hit rate target)
    - Gradual rollout (0% → 10% → 50% → 100%)
    - Circuit breaker protection
    - Real-time quality monitoring
    - Cost tracking
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize optimized pipeline"""
        super().__init__(*args, **kwargs)
        
        # Get singletons
        self.config_manager = get_config_manager()
        self.rollout_manager = get_rollout_manager()
        self.cost_tracker = get_cost_tracker()
        self.online_evaluator = get_online_evaluator()
        
        # Get active configuration
        config = self.config_manager.get_config()
        
        # Initialize compressor if enabled
        if config.enable_compression:
            self.compressor = ContextCompressor(
                ratio=config.compression_ratio,
                fallback_on_error=True
            )
            logger.info(f"Compression enabled: ratio={config.compression_ratio}")
        else:
            self.compressor = None
        
        # Initialize cache if enabled
        if config.enable_cache:
            self.cache = SemanticCache(
                threshold=config.cache_threshold,
                ttl_days=config.cache_ttl_days,
                backend="memory"  # Use Redis in production
            )
            logger.info(f"Cache enabled: threshold={config.cache_threshold}")
        else:
            self.cache = None
        
        logger.info(f"Optimized RAG Pipeline initialized with config: {config.name}")
    
    def query(
        self,
        question: str,
        user_id: Optional[str] = None,
        filter_metadata: Optional[Dict] = None,
        include_sources: bool = True
    ) -> Dict:
        """
        Query with optimizations and rollout control
        
        Args:
            question: User question
            user_id: User ID for consistent rollout assignment
            filter_metadata: Optional metadata filters
            include_sources: Include source citations
            
        Returns:
            Dict with answer, sources, and metrics
        """
        query_start = time.time()
        
        # Check rollout manager
        use_optimization = self.rollout_manager.should_use_optimization(user_id)
        
        try:
            if use_optimization:
                result = self._optimized_query(question, filter_metadata, include_sources)
            else:
                result = self._baseline_query(question, filter_metadata, include_sources)
            
            # Record success
            self.rollout_manager.record_success()
            
            # Track latency
            observe_latency(time.time() - query_start)
            
            # Online evaluation (10% sample)
            if self.online_evaluator.should_evaluate():
                self.online_evaluator.evaluate_query(
                    question=question,
                    answer=result['answer'],
                    contexts=result.get('contexts', [])
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            # Record failure
            self.rollout_manager.record_failure(e)
            # Fallback to baseline
            return self._baseline_query(question, filter_metadata, include_sources)
    
    def _optimized_query(
        self,
        question: str,
        filter_metadata: Optional[Dict],
        include_sources: bool
    ) -> Dict:
        """Execute query with optimizations (compression + cache)"""
        
        # 1. Check cache first
        if self.cache:
            cache_start = time.time()
            cached = self.cache.get(question)
            cache_latency = (time.time() - cache_start) * 1000
            
            observe_cache_latency(cache_latency / 1000)  # Convert to seconds
            
            if cached:
                # Cache HIT
                similarity = cached['_cache_metadata']['similarity']
                track_cache_hit(similarity)
                
                # Track cost savings
                cost_savings = self.cost_tracker.calculate_cache_savings(cache_hit=True)
                track_cost_savings(cost_savings, source='cache')
                
                logger.info(f"✅ Cache HIT (similarity={similarity:.3f}, latency={cache_latency:.0f}ms)")
                return cached
            else:
                # Cache MISS
                track_cache_miss()
                logger.debug("Cache MISS - proceeding to retrieval")
        
        # 2. Retrieve contexts (from base class)
        retrieval_start = time.time()
        contexts = self._retrieve_contexts(question, filter_metadata)
        
        if not contexts:
            return {
                'answer': "Maaf, saya tidak menemukan informasi yang relevan.",
                'sources': [],
                'contexts': [],
                'confidence': 0.0
            }
        
        # 3. Compress contexts
        if self.compressor:
            compression_start = time.time()
            compression_result = self.compressor.compress_contexts(
                query=question,
                contexts=[c['text'] for c in contexts]
            )
            
            compression_latency = compression_result['latency_ms'] / 1000  # Convert to seconds
            observe_compression_latency(compression_latency)
            
            if compression_result['success']:
                compressed_text = compression_result['compressed_contexts']
                compression_ratio = compression_result['compression_ratio']
                
                # Track cost savings from compression
                savings = self.cost_tracker.calculate_compression_savings(
                    compression_result['original_tokens'],
                    compression_result['compressed_tokens']
                )
                track_cost_savings(savings, source='compression')
                
                logger.info(f"✅ Compression: {compression_ratio:.2f} ratio, {savings:.5f} USD saved")
            else:
                compressed_text = "\n\n".join([c['text'] for c in contexts])
                compression_ratio = 1.0
                logger.warning("Compression failed, using uncompressed")
        else:
            compressed_text = "\n\n".join([c['text'] for c in contexts])
            compression_ratio = 1.0
        
        # 4. Generate answer with LLM (use compressed text)
        from src.rag.prompts import build_prompt
        
        prompt = build_prompt(
            question=question,
            chunks=contexts,  # Keep original for source extraction
            include_metadata=include_sources
        )
        
        # Override context in prompt with compressed version
        prompt = prompt.replace(
            "\n\n".join([c['text'] for c in contexts]),
            compressed_text
        )
        
        llm_response = self.llm.generate(prompt=prompt)
        answer = llm_response['text']
        
        # 5. Track tokens
        input_tokens = int(len(compressed_text) / 4)  # Rough estimate
        output_tokens = int(len(answer) / 4)
        track_tokens(input_tokens, output_tokens)
        
        # 6. Build result
        result = {
            'answer': answer,
            'sources': self._extract_sources(contexts) if include_sources else [],
            'contexts': [c['text'] for c in contexts],
            'confidence': sum(c['score'] for c in contexts) / len(contexts),
            'model_used': llm_response['model'],
            'optimization_used': True,
            'compression_ratio': compression_ratio,
            'cache_hit': False
        }
        
        # 7. Cache result
        if self.cache:
            self.cache.set(question, result)
        
        # 8. Track cost
        cost_info = self.cost_tracker.record_query_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            compression_ratio=compression_ratio,
            cache_hit=False
        )
        
        return result
    
    def _baseline_query(
        self,
        question: str,
        filter_metadata: Optional[Dict],
        include_sources: bool
    ) -> Dict:
        """Execute baseline query without optimizations"""
        # Use base class query method
        result = super().query(question, filter_metadata, include_sources)
        result['optimization_used'] = False
        result['compression_ratio'] = 1.0
        result['cache_hit'] = False
        
        # Track cost (baseline)
        input_tokens = 1000  # Avg baseline
        output_tokens = 200
        self.cost_tracker.record_query_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            compression_ratio=1.0,
            cache_hit=False
        )
        
        return result
    
    def _retrieve_contexts(self, question: str, filter_metadata: Optional[Dict]) -> List[Dict]:
        """Retrieve contexts using vector search"""
        results = self.vector_store.search(
            query=question,
            n_results=self.top_k,
            filter_metadata=filter_metadata
        )
        
        if not results:
            return []
        
        chunks = []
        for result in results:
            if hasattr(result, 'text'):
                chunks.append({
                    'text': result.text,
                    'metadata': result.metadata,
                    'score': result.score
                })
            elif  isinstance(result, dict):
                chunks.append({
                    'text': result.get('text', ''),
                    'metadata': result.get('metadata', {}),
                    'score': result.get('score', 0.0)
                })
        
        return chunks
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract unique sources from chunks"""
        sources = []
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
        
        return sources
    
    def get_optimization_stats(self) -> Dict:
        """Get optimization statistics"""
        return {
            "config": self.config_manager.get_stats(),
            "rollout": self.rollout_manager.get_rollout_stats(),
            "cost": self.cost_tracker.get_metrics(),
            "cache": self.cache.get_stats() if self.cache else {},
            "compressor": self.compressor.get_stats() if self.compressor else {},
            "evaluator": self.online_evaluator.get_stats(),
        }
