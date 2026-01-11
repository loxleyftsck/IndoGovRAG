"""
Faithfulness Judge - LLM-as-Judge for RAG Evaluation
Uses Ollama to evaluate if answers are faithful to retrieved context

Part of Ollama RAG evaluation suite
"""

import logging
from typing import Dict, List
from src.llm.ollama_llm import OllamaLLM

logger = logging.getLogger(__name__)


class FaithfulnessJudge:
    """
    Evaluate RAG answer faithfulness using LLM-as-judge pattern
    
    Uses local Ollama model to score how well the answer
    stays faithful to the retrieved context (0.0 - 1.0)
    """
    
    # Faithfulness threshold
    FAITHFULNESS_THRESHOLD = 0.7
    
    def __init__(self, judge_model: str = "llama3.1:8b"):
        """
        Initialize faithfulness judge
        
        Args:
            judge_model: Ollama model to use for judging
        """
        self.judge_llm = OllamaLLM(model=judge_model)
        self.stats = {
            "total_evaluations": 0,
            "avg_faithfulness": 0.0,
            "hallucination_count": 0
        }
        logger.info(f"✅ FaithfulnessJudge initialized with {judge_model}")
    
    def evaluate(
        self,
        question: str,
        context: str,
        answer: str
    ) -> Dict:
        """
        Evaluate answer faithfulness to context
        
        Args:
            question: Original question
            context: Retrieved context (concatenated chunks)
            answer: Generated answer
            
        Returns:
            Dict with:
                - score: float (0.0-1.0)
                - is_hallucination: bool
                - reasoning: str
                - success: bool
        """
        
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(question, context, answer)
        
        # Get judge response
        response = self.judge_llm.generate(
            prompt=prompt,
            temperature=0.1,  # Low temperature for consistent judging
            max_tokens=512
        )
        
        if not response['success']:
            logger.error("Faithfulness evaluation failed")
            return {
                "score": 0.5,  # Neutral score on error
                "is_hallucination": False,
                "reasoning": "Evaluation error",
                "success": False
            }
        
        # Parse score from response
        score, reasoning = self._parse_judge_response(response['text'])
        
        # Determine if hallucination
        is_hallucination = score < self.FAITHFULNESS_THRESHOLD
        
        # Update stats
        self.stats["total_evaluations"] += 1
        self.stats["avg_faithfulness"] = (
            (self.stats["avg_faithfulness"] * (self.stats["total_evaluations"] - 1) + score) /
            self.stats["total_evaluations"]
        )
        if is_hallucination:
            self.stats["hallucination_count"] += 1
        
        return {
            "score": score,
            "is_hallucination": is_hallucination,
            "reasoning": reasoning,
            "success": True
        }
    
    def _build_evaluation_prompt(self, question: str, context: str, answer: str) -> str:
        """Build evaluation prompt for LLM judge"""
        return f"""Tugas Anda: Evaluasi apakah JAWABAN setia pada KONTEKS yang diberikan.

PERTANYAAN:
{question}

KONTEKS (dari dokumen):
{context}

JAWABAN yang perlu dievaluasi:
{answer}

Berikan penilaian dalam format:
SKOR: [0.0 sampai 1.0]
ALASAN: [penjelasan singkat]

Kriteria penilaian:
- 1.0 = Jawaban sepenuhnya didukung oleh konteks, tidak ada informasi tambahan
- 0.7-0.9 = Sebagian besar didukung, sedikit interpretasi wajar
- 0.4-0.6 = Campuran informasi dari konteks dan luar konteks
- 0.0-0.3 = Banyak informasi yang tidak ada di konteks (halusinasi)

Berikan penilaian Anda:"""
    
    def _parse_judge_response(self, response_text: str) -> tuple:
        """
        Parse judge response to extract score and reasoning
        
        Returns:
            (score: float, reasoning: str)
        """
        try:
            # Look for SKOR: pattern
            score = 0.5  # default
            reasoning = response_text
            
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('SKOR:'):
                    # Extract number after SKOR:
                    score_str = line.replace('SKOR:', '').strip()
                    # Handle various formats: "0.8", "0,8", "8/10", etc.
                    score_str = score_str.replace(',', '.')
                    
                    # Try to parse as float
                    try:
                        score = float(score_str.split()[0])  # Take first number
                        # Clamp to 0-1
                        score = max(0.0, min(1.0, score))
                    except ValueError:
                        logger.warning(f"Could not parse score from: {score_str}")
                
                elif line.startswith('ALASAN:'):
                    reasoning = line.replace('ALASAN:', '').strip()
            
            return score, reasoning
            
        except Exception as e:
            logger.error(f"Error parsing judge response: {e}")
            return 0.5, response_text[:200]  # Return truncated response
    
    def get_stats(self) -> Dict:
        """Get evaluation statistics"""
        hallucination_rate = (
            self.stats["hallucination_count"] / self.stats["total_evaluations"] * 100
            if self.stats["total_evaluations"] > 0
            else 0.0
        )
        
        return {
            **self.stats,
            "hallucination_rate_percent": hallucination_rate,
            "threshold": self.FAITHFULNESS_THRESHOLD
        }


# Singleton
_faithfulness_judge = None


def get_faithfulness_judge(model: str = "llama3.1:8b") -> FaithfulnessJudge:
    """Get global FaithfulnessJudge instance"""
    global _faithfulness_judge
    if _faithfulness_judge is None:
        _faithfulness_judge = FaithfulnessJudge(judge_model=model)
    return _faithfulness_judge
