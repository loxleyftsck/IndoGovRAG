"""
Groq LLM Module for IndoGovRAG
Optimized for Indonesian RAG with fast inference

Model Recommendations for Indonesian:
- llama-3.3-70b-versatile: Best overall (primary)
- mixtral-8x7b-32768: Good multilingual support (fallback 1)
- gemma2-9b-it: Lightweight, decent quality (fallback 2)
"""

from typing import Optional, Dict, Any, List
from enum import Enum
import time
from dataclasses import dataclass
import os
import logging

logger = logging.getLogger(__name__)


class GroqModel(str, Enum):
    """Groq models optimized for Indonesian RAG."""
    LLAMA_3_3_70B = "llama-3.3-70b-versatile"  # Primary - best quality
    MIXTRAL_8X7B = "mixtral-8x7b-32768"  # Fallback 1 - good multilingual
    GEMMA2_9B = "gemma2-9b-it"  # Fallback 2 - lightweight
    LLAMA_3_1_8B = "llama-3.1-8b-instant"  # Fastest, lower quality


@dataclass
class GroqResponse:
    """Standardized Groq LLM response."""
    success: bool
    text: str
    model_used: str
    tokens_used: int
    latency_ms: float
    error: Optional[str] = None
    fallback_triggered: bool = False
    finish_reason: Optional[str] = None


class GroqLLM:
    """
    Groq LLM with automatic fallback for IndoGovRAG.

    Features:
    - Ultra-fast inference (Groq's LPUs)
    - Multi-tier fallback (70B → Mixtral → Gemma)
    - Indonesian-optimized models
    - Token usage tracking
    - Rate limit handling
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        primary_model: GroqModel = GroqModel.LLAMA_3_3_70B,
        fallback_models: Optional[List[GroqModel]] = None,
        enable_streaming: bool = False,
        quota_tracker=None
    ):
        """
        Initialize Groq LLM.

        Args:
            api_key: Groq API key (reads from GROQ_API_KEY env if None)
            primary_model: Primary model to use
            fallback_models: List of fallback models in order
            enable_streaming: Enable streaming responses
            quota_tracker: Optional quota tracker
        """
        from dotenv import load_dotenv
        load_dotenv()

        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Add to .env: "
                "GROQ_API_KEY=gsk_..."
            )

        self.primary_model = primary_model
        self.fallback_models = fallback_models or [
            GroqModel.MIXTRAL_8X7B,
            GroqModel.GEMMA2_9B
        ]
        self.enable_streaming = enable_streaming
        self.quota_tracker = quota_tracker

        # Initialize client
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            logger.info(f"[OK] Groq client initialized with model: {primary_model}")
        except Exception as e:
            logger.error(f"[ERR] Failed to initialize Groq client: {e}")
            raise

        # Stats
        self.stats = {
            "total_requests": 0,
            "primary_success": 0,
            "fallback_1_success": 0,
            "fallback_2_success": 0,
            "total_failures": 0,
            "total_tokens": 0,
        }

    def _make_request(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> GroqResponse:
        """
        Make request to Groq API.

        Args:
            prompt: Input prompt
            model: Model name
            max_tokens: Max output tokens
            temperature: Sampling temperature

        Returns:
            GroqResponse
        """
        try:
            start = time.time()

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Anda adalah asisten AI yang membantu menjawab pertanyaan "
                            "tentang dokumen pemerintahan Indonesia. Berikan jawaban "
                            "yang akurat, ringkas, dan berdasarkan konteks yang diberikan. "
                            "Gunakan bahasa Indonesia yang formal dan jelas."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            latency = (time.time() - start) * 1000

            # Extract response
            text = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            finish_reason = response.choices[0].finish_reason

            # Track quota
            if self.quota_tracker:
                self.quota_tracker.track_request(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    model=model
                )

            self.stats["total_tokens"] += tokens_used

            return GroqResponse(
                success=True,
                text=text,
                model_used=model,
                tokens_used=tokens_used,
                latency_ms=latency,
                finish_reason=finish_reason
            )

        except Exception as e:
            error_msg = str(e)

            # Check if rate limit/quota error
            is_rate_limit = any(
                keyword in error_msg.lower()
                for keyword in ['rate', 'limit', '429', 'quota', 'too many']
            )

            return GroqResponse(
                success=False,
                text="",
                model_used=model,
                tokens_used=0,
                latency_ms=0,
                error=error_msg,
                fallback_triggered=is_rate_limit
            )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        max_fallback_attempts: int = 2,
        **kwargs
    ) -> GroqResponse:
        """
        Generate response with automatic fallback.

        Args:
            prompt: Input prompt (Indonesian)
            max_tokens: Max output tokens
            temperature: Sampling temperature (lower = more focused)
            max_fallback_attempts: Number of fallback models to try
            **kwargs: Additional parameters

        Returns:
            GroqResponse with result
        """
        self.stats["total_requests"] += 1

        # Models to try (primary + fallbacks)
        models_to_try = [self.primary_model] + self.fallback_models
        models_to_try = models_to_try[:max_fallback_attempts + 1]

        for attempt, model in enumerate(models_to_try):
            model_name = model.value if isinstance(model, GroqModel) else model

            logger.debug(f"[TRY] Trying {model_name}...")

            response = self._make_request(
                prompt=prompt,
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if response.success:
                logger.debug(f"[OK] {response.latency_ms:.0f}ms ({response.tokens_used} tokens)")

                # Update stats
                if attempt == 0:
                    self.stats["primary_success"] += 1
                elif attempt == 1:
                    self.stats["fallback_1_success"] += 1
                else:
                    self.stats["fallback_2_success"] += 1

                return response
            else:
                logger.error(f"[ERR] {response.error}")

                # If not a retryable error, stop
                if not response.fallback_triggered and attempt == 0:
                    self.stats["total_failures"] += 1
                    return response

        # All models failed
        self.stats["total_failures"] += 1
        return GroqResponse(
            success=False,
            text="",
            model_used="none",
            tokens_used=0,
            latency_ms=0,
            error="All fallback models exhausted"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        total = max(self.stats["total_requests"], 1)

        return {
            **self.stats,
            "success_rate": (
                (self.stats["primary_success"] +
                 self.stats["fallback_1_success"] +
                 self.stats["fallback_2_success"]) / total
            ),
            "fallback_rate": (
                (self.stats["fallback_1_success"] +
                 self.stats["fallback_2_success"]) / total
            ),
            "avg_tokens_per_request": self.stats["total_tokens"] / total
        }

    def print_stats(self):
        """Print usage statistics."""
        stats = self.get_stats()

        logger.info("[STAT] GROQ LLM STATISTICS")
        logger.info(f"Total Requests:         {stats['total_requests']}")
        logger.info(f"Primary (70B):          {stats['primary_success']} ({stats['primary_success']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"Fallback 1 (Mixtral):   {stats['fallback_1_success']} ({stats['fallback_1_success']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"Fallback 2 (Gemma):     {stats['fallback_2_success']} ({stats['fallback_2_success']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"Total Failures:         {stats['total_failures']} ({stats['total_failures']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"Success Rate:           {stats['success_rate']*100:.1f}%")
        logger.info(f"Fallback Rate:          {stats['fallback_rate']*100:.1f}%")
        logger.info(f"Total Tokens:           {stats['total_tokens']:,}")
        logger.info(f"Avg Tokens/Request:     {stats['avg_tokens_per_request']:.0f}")


# =============================================================================
# DEMO & TESTING
# =============================================================================

def test_groq_llm():
    """Test Groq LLM with Indonesian queries."""
    logger.info("[TEST] Testing Groq LLM for IndoGovRAG")

    # Initialize
    llm = GroqLLM()

    # Test queries
    test_queries = [
        "Apa itu KTP elektronik dan apa fungsinya?",
        "Jelaskan prosedur pembuatan SIM A.",
        "Apa saja persyaratan untuk membuat paspor baru?",
    ]

    logger.info("Testing Indonesian RAG Queries")

    for i, query in enumerate(test_queries, 1):
        logger.info(f"Query {i}: {query[:50]}...")

        response = llm.generate(
            prompt=query,
            max_tokens=512,
            temperature=0.1
        )

        if response.success:
            logger.info(f"[CHAT] Jawaban: {response.text[:200]}...")
            logger.info(f"[STAT] Model: {response.model_used}, Tokens: {response.tokens_used}, Latency: {response.latency_ms:.0f}ms")
        else:
            logger.error(f"[ERR] Gagal: {response.error}")

    # Print stats
    llm.print_stats()
    logger.info("[OK] Test selesai!")


if __name__ == "__main__":
    test_groq_llm()
