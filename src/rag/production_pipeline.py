"""
Production RAG Pipeline with Guardrails & Sampling Evaluation
Optimized for beta deployment with safety mechanisms

Features:
- Fast runtime (RAG only, no judge)
- Sampling evaluation (5-10% with judge)
- Guardrails (ambiguity, legal, out-of-scope)
- Full logging for monitoring
"""

import random
import logging
from typing import Dict, Optional
from datetime import datetime

from src.rag.ollama_pipeline import OllamaRAGPipeline
from src.evaluation.faithfulness_judge import FaithfulnessJudge, get_faithfulness_judge
from src.rag.guardrails import ProductionGuardrails, get_guardrails

logger = logging.getLogger(__name__)


class ProductionRAGPipeline:
    """
    Production-ready RAG pipeline for beta deployment
    
    Optimized for:
    - Fast response (RAG only by default)
    - Quality monitoring (optional sampling evaluation)
    - Safety (guardrails for edge cases)
    """
    
    def __init__(
        self,
        ollama_model: str = "llama3.1:8b",
        sampling_rate: float = 0.10,  # 10% sampled for evaluation
        enable_guardrails: bool = True
    ):
        """
        Initialize production pipeline
        
        Args:
            ollama_model: Ollama model name
            sampling_rate: % of queries to evaluate (0.0-1.0)
            enable_guardrails: Enable ambiguity/legal/scope checks
        """
        # Core RAG pipeline
        self.rag_pipeline = OllamaRAGPipeline(ollama_model=ollama_model)
        
        # Optional components
        self.judge = None  # Lazy loaded for sampling
        self.guardrails = get_guardrails() if enable_guardrails else None
        
        # Config
        self.sampling_rate = sampling_rate
        self.enable_guardrails = enable_guardrails
        
        # Stats
        self.stats = {
            "total_queries": 0,
            "sampled_queries": 0,
            "ambiguous_queries": 0,
            "legal_queries": 0,
            "out_of_scope_queries": 0
        }
        
        logger.info(f"✅ ProductionRAGPipeline initialized")
        logger.info(f"   Sampling rate: {sampling_rate*100:.0f}%")
        logger.info(f"   Guardrails: {'enabled' if enable_guardrails else 'disabled'}")
    
    def query(
        self,
        question: str,
        user_id: Optional[str] = None,
        force_evaluation: bool = False
    ) -> Dict:
        """
        Query production RAG system
        
        Args:
            question: User question
            user_id: Optional user ID for logging
            force_evaluation: Force faithfulness evaluation (for testing)
            
        Returns:
            Dict with answer, metadata, guardrail actions
        """
        start_time = datetime.now()
        self.stats["total_queries"] += 1
        
        # 1. Guardrails check (pre-query)
        classification = None
        if self.guardrails:
            classification = self.guardrails.classify_query(question)
            
            # Track stats
            if classification.is_ambiguous:
                self.stats["ambiguous_queries"] += 1
            if classification.is_legal:
                self.stats["legal_queries"] += 1
            if classification.is_out_of_scope:
                self.stats["out_of_scope_queries"] += 1
            
            # Handle out-of-scope immediately
            if classification.is_out_of_scope and classification.confidence < 0.3:
                logger.warning(f"Out-of-scope query detected: {question[:50]}...")
                return {
                    "answer": self.guardrails.format_out_of_scope_response(question),
                    "sources": [],
                    "guardrail_action": "out_of_scope",
                    "confidence": 0.0,
                    "model_used": "guardrail",
                    "latency_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
        
        # 2. Run RAG query
        rag_result = self.rag_pipeline.query(
            question=question,
            query_id=f"prod-{self.stats['total_queries']:06d}"
        )
        
        # 3. Apply guardrails (post-query)
        answer = rag_result['answer']
        guardrail_action = None
        
        if self.guardrails and classification:
            # Add legal disclaimer if needed
            if classification.is_legal:
                answer = self.guardrails.add_legal_disclaimer(answer, classification)
                guardrail_action = "legal_disclaimer"
            
            # Format ambiguous response if needed
            if classification.is_ambiguous and classification.confidence < 0.5:
                answer = self.guardrails.format_ambiguous_response(
                    query=question,
                    classification=classification,
                    attempted_answer=answer
                )
                guardrail_action = "ambiguous_clarification"
        
        # 4. Sampling evaluation (optional)
        faithfulness_score = None
        is_hallucination = None
        
        should_evaluate = (
            force_evaluation or
            (random.random() < self.sampling_rate and rag_result['model_used'] != 'error')
        )
        
        if should_evaluate:
            # Lazy load judge
            if self.judge is None:
                self.judge = get_faithfulness_judge()
            
            # Evaluate
            context = "\n\n".join(rag_result['contexts'][:3])
            eval_result = self.judge.evaluate(
                question=question,
                context=context,
                answer=rag_result['answer']  # Original answer before guardrails
            )
            
            faithfulness_score = eval_result['score']
            is_hallucination = eval_result['is_hallucination']
            self.stats["sampled_queries"] += 1
            
            logger.info(f"Sampled evaluation: {faithfulness_score:.2f} {'🚨 HALLUCINATION' if is_hallucination else '✅'}")
        
        # 5. Build final response
        result = {
            **rag_result,
            "answer": answer,  # Potentially modified by guardrails
            "guardrail_action": guardrail_action,
            "query_classification": classification.__dict__ if classification else None,
            "faithfulness_score": faithfulness_score,
            "is_hallucination": is_hallucination,
            "sampled": should_evaluate,
            "user_id": user_id
        }
        
        return result
    
    def get_stats(self) -> Dict:
        """Get production pipeline statistics"""
        return {
            **self.stats,
            "sampling_rate": self.sampling_rate,
            "evaluation_coverage": (
                self.stats["sampled_queries"] / self.stats["total_queries"] * 100
                if self.stats["total_queries"] > 0 else 0
            )
        }


# Singleton for production use
_production_pipeline = None

def get_production_pipeline(
    sampling_rate: float = 0.10,
    enable_guardrails: bool = True
) -> ProductionRAGPipeline:
    """Get global production pipeline instance"""
    global _production_pipeline
    if _production_pipeline is None:
        _production_pipeline = ProductionRAGPipeline(
            sampling_rate=sampling_rate,
            enable_guardrails=enable_guardrails
        )
    return _production_pipeline
