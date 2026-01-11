"""
RAG Pipeline with Ollama Local LLM
Zero-cost alternative to cloud LLM APIs
"""

import time
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

from src.rag.pipeline import RAGPipeline
from src.llm.ollama_llm import OllamaLLM

logger = logging.getLogger(__name__)


class OllamaRAGPipeline(RAGPipeline):
    """
    RAG Pipeline using local Ollama LLM
    
    Drop-in replacement for cloud-based pipeline with:
    - Zero API costs
    - Full privacy (local inference)
    - Indonesian language support
    - Structured JSON logging
    """
    
    def __init__(self, *args, ollama_model: str = "llama3.1:8b-instruct-q4_K_M", **kwargs):
        """
        Initialize RAG pipeline with Ollama
        
        Args:
            ollama_model: Ollama model name
            *args, **kwargs: Passed to base RAGPipeline
        """
        # Initialize base pipeline (without LLM)
        self.vector_store = kwargs.get('vector_store')
        if not self.vector_store:
            from src.retrieval.vector_search import VectorStore
            self.vector_store = VectorStore()
        
        self.top_k = kwargs.get('top_k', 3)
        self.config = None
        self.last_token_count = 0
        
        # Initialize Ollama LLM
        self.llm = OllamaLLM(model=ollama_model)
        self.llm_backend = "ollama"
        
        # Query counter for structured logging
        self.query_count = 0
        
        logger.info(f"✅ OllamaRAGPipeline initialized with {ollama_model}")
        logger.info(f"   Vector Store: {self.vector_store.collection.count()} chunks")
    
    def _log_query(self, query_data: Dict):
        """Log query with structured JSON format"""
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_id": f"q-{self.query_count:04d}",
            **query_data
        }
        
        # Log as JSON (can be parsed by log aggregators)
        logger.info(f"QUERY_LOG: {json.dumps(log_entry, ensure_ascii=False)}")
    
    def query(
        self,
        question: str,
        filter_metadata: Optional[Dict] = None,
        include_sources: bool = True,
        query_id: Optional[str] = None
    ) -> Dict:
        """
        Query RAG system with Ollama LLM
        
        Args:
            question: User question in Indonesian
            filter_metadata: Optional metadata filters
            include_sources: Include source citations
            query_id: Optional external query ID
            
        Returns:
            Dict with answer, sources, metadata
        """
        query_start = time.time()
        self.query_count += 1
        
        # Use provided query_id or generate one
        if not query_id:
            query_id = f"q-{self.query_count:04d}"
        
        # 1. Retrieve contexts
        print(f"\n🔍 Retrieving context for: {question[:50]}...")
        
        results = self.vector_store.search(
            query=question,
            n_results=self.top_k,
            filter_metadata=filter_metadata
        )
        
        if not results:
            result = {
                'answer': "Maaf, saya tidak menemukan informasi yang relevan.",
                'sources': [],
                'contexts': [],
                'confidence': 0.0,
                'model_used': 'none',
                'tokens_used': 0,
                'latency_ms': (time.time() - query_start) * 1000,
                'query_id': query_id
            }
            
            # Log empty result
            self._log_query({
                "query_id": query_id,
                "query": question,
                "chunks_retrieved": 0,
                "model_used": "none",
                "latency_ms": result['latency_ms'],
                "tokens_used": 0,
                "status": "no_context"
            })
            
            return result
        
        print(f"   Found {len(results)} chunks")
        
        # 2. Build prompt
        from src.rag.prompts import build_prompt
        
        chunks = []
        for result in results:
            if hasattr(result, 'text'):
                chunks.append({
                    'text': result.text,
                    'metadata': result.metadata,
                    'score': result.score
                })
        
        prompt = build_prompt(
            question=question,
            chunks=chunks,
            include_metadata=include_sources
        )
        
        # 3. Generate with Ollama
        print(f"🤖 Generating answer with Ollama ({self.llm.model})...")
        
        llm_response = self.llm.generate(prompt=prompt)
        
        answer = llm_response['text']
        model_used = llm_response['model']
        tokens_used = llm_response['tokens']
        llm_latency = llm_response['latency_ms']
        
        print(f"   Model: {model_used}")
        print(f"   Tokens: {tokens_used}")
        print(f"   Answer length: {len(answer)} chars")
        
        # 4. Format sources
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
        
        # 5. Calculate confidence
        confidence = sum(c['score'] for c in chunks) / len(chunks) if chunks else 0.0
        
        total_time = (time.time() - query_start) * 1000
        print(f"\n📊 Total time: {total_time:.0f}ms")
        
        result = {
            'answer': answer,
            'sources': sources,
            'contexts': [c['text'] for c in chunks],
            'confidence': confidence,
            'model_used': model_used,
            'tokens_used': tokens_used,
            'latency_ms': total_time,
            'llm_backend': 'ollama',
            'query_id': query_id
        }
        
        # 6. Structured logging
        self._log_query({
            "query_id": query_id,
            "query": question,
            "chunks_retrieved": len(chunks),
            "model_used": model_used,
            "tokens_used": tokens_used,
            "latency_ms": total_time,
            "llm_latency_ms": llm_latency,
            "confidence": confidence,
            "answer_length": len(answer),
            "status": "success"
        })
        
        return result
