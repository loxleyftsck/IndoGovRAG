"""
LLM-Based Re-ranking for RAG

Re-ranks retrieved chunks using LLM relevance scoring.
"""

import os
from typing import List, Dict
from dataclasses import dataclass
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RankedResult:
    """Re-ranked search result."""
    text: str
    chunk_id: str
    original_score: float
    relevance_score: float  # 0-10 from LLM
    final_score: float  # Combined score
    metadata: Dict


class LLMReranker:
    """
    LLM-based re-ranker using Gemini.
    
    Uses lightweight prompting to score chunk relevance without full generation.
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """
        Initialize re-ranker.
        
        Args:
            model_name: Gemini model to use
        """
        self.model_name = model_name
        
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.available = True
        else:
            self.model = None
            self.available = False
    
    def score_relevance(self, query: str, chunk: str) -> float:
        """
        Score relevance of chunk to query using LLM.
        
        Args:
            query: User query
            chunk: Text chunk
        
        Returns:
            Relevance score 0-10
        """
        if not self.available:
            return 5.0  # Neutral score if no API
        
        prompt = f"""Nilai relevansi teks berikut terhadap pertanyaan (skala 0-10):

Pertanyaan: {query}

Teks: {chunk[:500]}

Berikan HANYA angka 0-10 (10 = sangat relevan, 0 = tidak relevan).
Jawab dengan satu angka saja."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=5,
                    temperature=0.0,
                )
            )
            
            # Extract score
            score_text = response.text.strip()
            score = float(score_text)
            return min(max(score, 0.0), 10.0)  # Clamp to 0-10
            
        except Exception as e:
            print(f"⚠️  Re-ranking error: {e}")
            return 5.0  # Neutral score on error
    
    def rerank(
        self,
        query: str,
        results: List,  # SearchResult objects
        alpha: float = 0.5  # Weight for LLM score
    ) -> List[RankedResult]:
        """
        Re-rank search results using LLM.
        
        Args:
            query: Original query
            results: List of SearchResult objects
            alpha: Weight for LLM score (0-1)
                  final = alpha * llm_score + (1-alpha) * original_score
        
        Returns:
            List of RankedResult sorted by final score (descending)
        """
        if not results:
            return []
        
        ranked = []
        
        for result in results:
            # Get LLM relevance score
            llm_score = self.score_relevance(query, result.text)
            
            # Normalize LLM score to 0-1
            llm_score_norm = llm_score / 10.0
            
            # Normalize original score to 0-1 (assume it's already 0-1)
            orig_score_norm = result.score
            
            # Combine scores
            final_score = alpha * llm_score_norm + (1 - alpha) * orig_score_norm
            
            ranked.append(RankedResult(
                text=result.text,
                chunk_id=result.chunk_id,
                original_score=result.score,
                relevance_score=llm_score,
                final_score=final_score,
                metadata=result.metadata
            ))
        
        # Sort by final score (descending)
        ranked.sort(key=lambda x: x.final_score, reverse=True)
        
        return ranked
    
    def rerank_batch(
        self,
        queries: List[str],
        results_list: List[List],
        alpha: float = 0.5
    ) -> List[List[RankedResult]]:
        """Re-rank multiple query results."""
        return [
            self.rerank(q, r, alpha)
            for q, r in zip(queries, results_list)
        ]


# =============================================================================
# DEMO & TESTING
# =============================================================================

def demo_reranking():
    """Demo LLM-based re-ranking."""
    
    print("="*70)
    print(" 🧪 LLM RE-RANKING DEMO")
    print("="*70)
    print()
    
    reranker = LLMReranker()
    
    if not reranker.available:
        print("⚠️  GEMINI_API_KEY not set - using neutral scores")
        print("   Set GEMINI_API_KEY in .env to enable LLM re-ranking")
        print()
    else:
        print(f"✅ Using model: {reranker.model_name}")
        print()
    
    # Demo with synthetic results
    from dataclasses import dataclass
    
    @dataclass
    class DemoResult:
        text: str
        chunk_id: str
        score: float
        metadata: Dict
    
    query = "Apa syarat mendaftar BPJS Kesehatan?"
    
    demo_results = [
        DemoResult(
            text="BPJS Kesehatan memberikan jaminan kesehatan untuk seluruh rakyat Indonesia dengan berbagai manfaat.",
            chunk_id="chunk_1",
            score=0.75,
            metadata={}
        ),
        DemoResult(
            text="Untuk mendaftar BPJS Kesehatan diperlukan KTP dan Kartu Keluarga. Pendaftaran bisa dilakukan online atau di kantor BPJS.",
            chunk_id="chunk_2",
            score=0.65,
            metadata={}
        ),
        DemoResult(
            text="KTP elektronik berlaku seumur hidup dan tidak perlu diperpanjang.",
            chunk_id="chunk_3",
            score=0.70,
            metadata={}
        ),
    ]
    
    print(f"📝 Query: {query}")
    print()
    
    print("**Before Re-ranking (by vector similarity):**")
    for i, r in enumerate(demo_results, 1):
        print(f"{i}. Score: {r.score:.3f}")
        print(f"   {r.text[:100]}...")
        print()
    
    print("🔄 Re-ranking with LLM...")
    print()
    
    reranked = reranker.rerank(query, demo_results, alpha=0.6)
    
    print("**After Re-ranking (LLM + vector):**")
    for i, r in enumerate(reranked, 1):
        print(f"{i}. Score: {r.final_score:.3f} (LLM: {r.relevance_score:.1f}/10, Original: {r.original_score:.3f})")
        print(f"   {r.text[:100]}...")
        print()
    
    print("="*70)
    print("✅ Demo complete!")
    print()
    
    print("💡 Note: Re-ranking helps prioritize chunks that are")
    print("   semantically close AND contextually relevant to the query.")


if __name__ == "__main__":
    demo_reranking()
