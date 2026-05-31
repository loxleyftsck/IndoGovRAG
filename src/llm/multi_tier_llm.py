"""
Multi-tier LLM Fallback System
Handle quota limits and API failures gracefully

Tier 0: Groq Llama 3.3 70B (PRIMARY - fastest, cheapest)
Tier 1: Groq Mixtral 8x7B (fallback)
Tier 2: Groq Gemma 2 9B (fallback)
Tier 3: Gemini Pro (legacy backup)
Tier 4: Gemini Flash (slowest fallback)
"""

from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import time
import os
import logging

# Configure module logger
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("indogov_errors")
from dataclasses import dataclass
from dotenv import load_dotenv


class LLMTier(Enum):
    """LLM tier priority."""
    GROQ_PRIMARY = "groq-llama-3.3-70b"
    GROQ_MIXTRAL = "groq-mixtral-8x7b"
    GROQ_GEMMA = "groq-gemma2-9b"
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    success: bool
    text: str
    model_used: str
    tokens_used: int
    latency_ms: float
    error: Optional[str] = None
    fallback_triggered: bool = False


class MultiTierLLM:
    """
    Multi-tier LLM with automatic fallback.
    
    Features:
    - Automatic fallback on quota/rate limits
    - Token usage tracking
    - Latency monitoring
    - Error handling with retries
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        enable_groq: bool = True,
        enable_flash_fallback: bool = True,
        enable_local_fallback: bool = False,
        quota_tracker = None
    ):
        """
        Initialize multi-tier LLM.

        Args:
            gemini_api_key: Gemini API key
            groq_api_key: Groq API key (reads from GROQ_API_KEY env if None)
            enable_groq: Enable Groq as primary (faster, cheaper)
            enable_flash_fallback: Enable Gemini Flash fallback
            enable_local_fallback: Enable local model fallback
            quota_tracker: Optional quota tracker instance
        """
        load_dotenv()

        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.enable_groq = enable_groq and bool(self.groq_api_key)
        self.enable_flash = enable_flash_fallback and bool(self.gemini_api_key)
        self.enable_local = enable_local_fallback
        self.quota_tracker = quota_tracker

        # Initialize models
        self._init_groq_client()
        self._init_gemini_models()

        # Stats
        self.stats = {
            "total_requests": 0,
            "groq_success": 0,
            "gemini_pro_success": 0,
            "gemini_flash_fallback": 0,
            "local_fallback": 0,
            "total_failures": 0,
            "retries_total": 0,
            "retries_exhausted": 0,
        }

        # Retry configuration
        self.max_retries = 3
        self.retry_backoff_seconds = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
        self.retryable_errors = ['timeout', 'rate', 'limit', '429', 'connection',
                                  'reset', 'unavailable', '503', '502', '500']
        self._last_retry_log_time = 0  # throttle duplicate log entries

    def _init_groq_client(self):
        """Initialize Groq client."""
        if not self.enable_groq:
            self.groq_client = None
            return

        try:
            from groq import Groq
            self.groq_client = Groq(api_key=self.groq_api_key)
            logger.info("[OK] Groq client initialized (Primary LLM)")
        except Exception as e:
            logger.warning(f"[WARN] Groq initialization failed: {e}")
            self.groq_client = None

    def _init_gemini_models(self):
        """Initialize Gemini models."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            
            self.gemini_pro = genai.GenerativeModel('gemini-pro')
            
            if self.enable_flash:
                self.gemini_flash = genai.GenerativeModel('gemini-1.5-flash')
            else:
                self.gemini_flash = None
            
            logger.info("[OK] Gemini models initialized")
        except Exception as e:
            logger.warning(f"[WARN] Gemini initialization failed (backup only): {e}")
            self.gemini_pro = None
            self.gemini_flash = None

    def _try_groq_llama(self, prompt: str, **kwargs) -> LLMResponse:
        """Try Groq Llama 3.3 70B (Tier 0 - Primary, fastest)."""
        custom_groq_key = kwargs.get('custom_groq_key')

        # Instantiate temporary client if custom key provided
        if custom_groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=custom_groq_key)
            except Exception as e:
                return LLMResponse(
                    success=False,
                    text="",
                    model_used="groq-llama-3.3-70b",
                    tokens_used=0,
                    latency_ms=0,
                    error=f"Failed to initialize custom Groq client: {e}"
                )
        else:
            client = self.groq_client

        if not client:
            return LLMResponse(
                success=False,
                text="",
                model_used="groq-llama-3.3-70b",
                tokens_used=0,
                latency_ms=0,
                error="Groq client not initialized"
            )

        try:
            start = time.time()

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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
                max_tokens=kwargs.get('max_output_tokens', 1024),
                temperature=kwargs.get('temperature', 0.1),
            )

            latency = (time.time() - start) * 1000
            text = response.choices[0].message.content or ""
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else 0

            # Track quota
            if self.quota_tracker and hasattr(response, 'usage'):
                self.quota_tracker.track_request(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    model="groq-llama-3.3-70b"
                )

            return LLMResponse(
                success=True,
                text=text,
                model_used="groq-llama-3.3-70b",
                tokens_used=tokens,
                latency_ms=latency
            )

        except Exception as e:
            error_msg = str(e)
            is_rate_limit = any(
                keyword in error_msg.lower()
                for keyword in ['rate', 'limit', '429', 'quota']
            )

            return LLMResponse(
                success=False,
                text="",
                model_used="groq-llama-3.3-70b",
                tokens_used=0,
                latency_ms=0,
                error=error_msg,
                fallback_triggered=is_rate_limit
            )

    def _try_gemini_pro(self, prompt: str, **kwargs) -> LLMResponse:
        """Try Gemini Pro (Tier 1)."""
        custom_gemini_key = kwargs.get('custom_gemini_key')
        original_key = self.gemini_api_key or os.getenv("GEMINI_API_KEY")
        model = self.gemini_pro
        
        if custom_gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=custom_gemini_key)
                model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                return LLMResponse(
                    success=False,
                    text="",
                    model_used="gemini-pro",
                    tokens_used=0,
                    latency_ms=0,
                    error=f"Failed to initialize custom Gemini Pro client: {e}"
                )

        if not model:
            return LLMResponse(
                success=False,
                text="",
                model_used="gemini-pro",
                tokens_used=0,
                latency_ms=0,
                error="Model not initialized"
            )
        
        try:
            # Check quota before request
            if self.quota_tracker:
                should_throttle, reason = self.quota_tracker.should_throttle()
                if should_throttle:
                    return LLMResponse(
                        success=False,
                        text="",
                        model_used="gemini-pro",
                        tokens_used=0,
                        latency_ms=0,
                        error=f"Quota limit: {reason}"
                    )
            
            start = time.time()
            # Generate using Gemini (with max_tokens for speed)
            # Merge default generation_config with any provided in kwargs
            default_gen_config = {
                "max_output_tokens": 512,  # Limit response length
                "temperature": 0.1
            }
            
            import google.generativeai as genai

            # If 'generation_config' is in kwargs, update it with defaults, then pass it.
            # Otherwise, create a new GenerationConfig object.
            if 'generation_config' in kwargs and isinstance(kwargs['generation_config'], dict):
                merged_gen_config_dict = {**default_gen_config, **kwargs['generation_config']}
                gen_config = genai.types.GenerationConfig(**merged_gen_config_dict)
                del kwargs['generation_config'] # Remove from kwargs to avoid double passing
            elif 'generation_config' in kwargs and isinstance(kwargs['generation_config'], genai.types.GenerationConfig):
                gen_config = kwargs['generation_config']
                del kwargs['generation_config']
            else:
                gen_config = genai.types.GenerationConfig(**default_gen_config)

            # Clean up custom keys from kwargs to avoid double-passing to generative model
            kwargs_clean = kwargs.copy()
            kwargs_clean.pop('custom_gemini_key', None)
            kwargs_clean.pop('custom_groq_key', None)

            response = model.generate_content(
                prompt,
                generation_config=gen_config,
                **kwargs_clean
            )
            latency = (time.time() - start) * 1000
            
            # Extract text
            text = response.text if hasattr(response, 'text') else ""
            
            # Estimate tokens (rough approximation)
            tokens = len(prompt.split()) + len(text.split())
            
            # Track quota
            if self.quota_tracker:
                self.quota_tracker.track_request(
                    input_tokens=len(prompt.split()),
                    output_tokens=len(text.split()),
                    model="gemini-pro"
                )
            
            return LLMResponse(
                success=True,
                text=text,
                model_used="gemini-pro",
                tokens_used=tokens,
                latency_ms=latency
            )
        
        except Exception as e:
            error_msg = str(e)
            
            # Check if quota/rate limit error
            is_quota_error = any(
                keyword in error_msg.lower() 
                for keyword in ['quota', 'rate', 'limit', '429']
            )
            
            return LLMResponse(
                success=False,
                text="",
                model_used="gemini-pro",
                tokens_used=0,
                latency_ms=0,
                error=error_msg,
                fallback_triggered=is_quota_error
            )
        finally:
            if custom_gemini_key and original_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=original_key)
                except Exception:
                    pass
    
    def _try_gemini_flash(self, prompt: str, **kwargs) -> LLMResponse:
        """Try Gemini Flash (Tier 2 - faster, cheaper)."""
        custom_gemini_key = kwargs.get('custom_gemini_key')
        original_key = self.gemini_api_key or os.getenv("GEMINI_API_KEY")
        model = self.gemini_flash

        if custom_gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=custom_gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                return LLMResponse(
                    success=False,
                    text="",
                    model_used="gemini-flash",
                    tokens_used=0,
                    latency_ms=0,
                    error=f"Failed to initialize custom Gemini Flash client: {e}"
                )

        if not model:
            return LLMResponse(
                success=False,
                text="",
                model_used="gemini-flash",
                tokens_used=0,
                latency_ms=0,
                error="Flash model not enabled"
            )
        
        try:
            start = time.time()
            kwargs_clean = kwargs.copy()
            kwargs_clean.pop('custom_gemini_key', None)
            kwargs_clean.pop('custom_groq_key', None)
            response = model.generate_content(prompt, **kwargs_clean)
            latency = (time.time() - start) * 1000
            
            text = response.text if hasattr(response, 'text') else ""
            tokens = len(prompt.split()) + len(text.split())
            
            return LLMResponse(
                success=True,
                text=text,
                model_used="gemini-flash",
                tokens_used=tokens,
                latency_ms=latency,
                fallback_triggered=True
            )
        
        except Exception as e:
            return LLMResponse(
                success=False,
                text="",
                model_used="gemini-flash",
                tokens_used=0,
                latency_ms=0,
                error=str(e)
            )
        finally:
            if custom_gemini_key and original_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=original_key)
                except Exception:
                    pass
    
    def _try_local_model(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Try local model (Tier 3 - offline mode).
        
        Note: This is a placeholder. Actual implementation would use:
        - Ollama with Llama 3 8B
        - GPT4All
        - HuggingFace transformers
        """
        if not self.enable_local:
            return LLMResponse(
                success=False,
                text="",
                model_used="local",
                tokens_used=0,
                latency_ms=0,
                error="Local model not enabled"
            )
        
        # Placeholder - would integrate with local model here
        return LLMResponse(
            success=False,
            text="",
            model_used="local",
            tokens_used=0,
            latency_ms=0,
            error="Local model not implemented (see docs for setup)"
        )
    
    def _is_retryable_error(self, error_message: str) -> bool:
        """Check if an error message indicates a retryable condition."""
        if not error_message:
            return False
        error_lower = error_message.lower()
        return any(keyword in error_lower for keyword in self.retryable_errors)

    def _log_failure(self, tier_name: str, attempt: int, error_message: str, final: bool = False):
        """Log LLM failures with throttling to avoid spam."""
        now = time.time()
        # Only log every 5 seconds minimum to avoid log spam
        if now - self._last_retry_log_time > 5 or final:
            level = "ERROR" if final else "WARN"
            error_logger.log(
                logging.ERROR if final else logging.WARNING,
                f"[{level}] {tier_name} failed (attempt {attempt}/{self.max_retries}): {error_message[:100]}"
            )
            self._last_retry_log_time = now

    def _retry_with_backoff(
        self,
        tier_func: Callable,
        tier_name: str,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        Execute LLM call with exponential backoff retry logic.

        Retry schedule: 1s, 2s, 4s (max 3 retries)

        Args:
            tier_func: The LLM tier function to call
            tier_name: Human-readable tier name
            prompt: The prompt to send
            **kwargs: Additional generation config

        Returns:
            LLMResponse with success/failure info
        """
        for attempt in range(1, self.max_retries + 1):
            response = tier_func(prompt, **kwargs)

            if response.success:
                # Log success after retries
                if attempt > 1:
                    error_logger.info(f"[OK] {tier_name} succeeded on attempt {attempt}")
                return response

            # Check if error is retryable
            is_retryable = self._is_retryable_error(response.error or "")

            if attempt < self.max_retries and is_retryable:
                # Calculate backoff time
                backoff_idx = min(attempt - 1, len(self.retry_backoff_seconds) - 1)
                backoff_time = self.retry_backoff_seconds[backoff_idx]

                self.stats["retries_total"] += 1
                self._log_failure(tier_name, attempt, response.error or "Unknown error")

                logger.info(f"[RETRY] {tier_name} failed (attempt {attempt}), "
                      f"retrying in {backoff_time}s...")
                time.sleep(backoff_time)
            else:
                # Last attempt or non-retryable error
                self._log_failure(tier_name, attempt, response.error or "Unknown error", final=True)

                if not is_retryable:
                    # Don't retry on non-retryable errors
                    return response

                # All retries exhausted
                self.stats["retries_exhausted"] += 1
                error_logger.error(f"[FAIL] {tier_name} exhausted {self.max_retries} retries")
                return response

        return response

    def generate(
        self,
        prompt: str,
        max_fallback_attempts: int = 2,
        **generation_config
    ) -> LLMResponse:
        """
        Generate response with automatic fallback and retry logic.

        Priority: Groq (fastest) → Gemini (backup)

        Each tier is retried up to 3 times with exponential backoff (1s, 2s, 4s)
        before falling back to the next tier.

        Args:
            prompt: Input prompt
            max_fallback_attempts: Max fallback tiers to try
            **generation_config: Additional generation parameters

        Returns:
            LLMResponse with result
        """
        self.stats["total_requests"] += 1

        # Try tiers in order (Groq is primary for speed)
        tiers = [
            ("Groq Llama 3.3 70B", self._try_groq_llama) if self.enable_groq or generation_config.get('custom_groq_key') else None,
            ("Gemini Pro", self._try_gemini_pro) if self.gemini_pro or generation_config.get('custom_gemini_key') else None,
            ("Gemini Flash", self._try_gemini_flash) if self.gemini_flash or generation_config.get('custom_gemini_key') else None,
            ("Local Model", self._try_local_model) if self.enable_local else None,
        ]

        # Filter out disabled tiers
        tiers = [t for t in tiers if t is not None]

        for tier_idx, (tier_name, tier_func) in enumerate(tiers):
            if tier_idx >= max_fallback_attempts + 1:
                break

            logger.info(f"Trying {tier_name}...")

            # Use retry logic for each tier
            response = self._retry_with_backoff(tier_func, tier_name, prompt, **generation_config)

            if response.success:
                logger.info(f"{tier_name} [OK] Success ({response.latency_ms:.0f}ms)")

                # Update stats
                if tier_idx == 0:
                    self.stats["groq_success"] += 1
                elif tier_idx == 1:
                    self.stats["gemini_pro_success"] += 1
                elif tier_idx == 2:
                    self.stats["gemini_flash_fallback"] += 1
                elif tier_idx == 3:
                    self.stats["local_fallback"] += 1

                return response
            else:
                logger.error(f"{tier_name} [ERR] Failed: {response.error}")

                # If not a fallback-triggering error, stop trying
                if not response.fallback_triggered and tier_idx == 0:
                    self.stats["total_failures"] += 1
                    return response

        # All tiers failed
        self.stats["total_failures"] += 1
        return LLMResponse(
            success=False,
            text="",
            model_used="none",
            tokens_used=0,
            latency_ms=0,
            error="All fallback tiers exhausted"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics including retry data."""
        total = self.stats["total_requests"]

        return {
            **self.stats,
            "success_rate": (
                (self.stats["groq_success"] +
                 self.stats["gemini_pro_success"] +
                 self.stats["gemini_flash_fallback"] +
                 self.stats["local_fallback"]) / max(total, 1)
            ),
            "fallback_rate": (
                (self.stats["gemini_flash_fallback"] +
                 self.stats["local_fallback"]) / max(total, 1)
            ),
            "retry_rate": (
                self.stats["retries_total"] / max(total, 1)
            ),
            "exhaustion_rate": (
                self.stats["retries_exhausted"] / max(total, 1)
            ),
        }
    
    def print_stats(self):
        """Print usage statistics."""
        stats = self.get_stats()

        logger.info("="*60)
        logger.info("[STAT] LLM FALLBACK + RETRY STATISTICS")
        logger.info("="*60)
        logger.info(f"Total Requests:       {stats['total_requests']}")
        logger.info(f"Groq Success:        {stats['groq_success']} ({stats['groq_success']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"Gemini Pro Success:  {stats['gemini_pro_success']} ({stats['gemini_pro_success']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"Gemini Flash Fallback: {stats['gemini_flash_fallback']} ({stats['gemini_flash_fallback']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"Local Fallback:      {stats['local_fallback']} ({stats['local_fallback']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"Total Failures:      {stats['total_failures']} ({stats['total_failures']/max(stats['total_requests'],1)*100:.1f}%)")
        logger.info(f"  └── Retries used:    {stats['retries_total']}")
        logger.info(f"  └── Retries exhausted: {stats['retries_exhausted']}")
        logger.info(f"Success Rate:        {stats['success_rate']*100:.1f}%")
        logger.info(f"Fallback Rate:       {stats['fallback_rate']*100:.1f}%")
        logger.info(f"Retry Rate:          {stats['retry_rate']*100:.1f}%")
        logger.info(f"Exhaustion Rate:     {stats['exhaustion_rate']*100:.1f}%")
        logger.info("="*60)


# =============================================================================
# DEMO & TESTING
# =============================================================================

def test_fallback_system():
    """Test the fallback system."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("[ERR] GEMINI_API_KEY not found in environment")
        logger.error("   Set it in .env file or export GEMINI_API_KEY=your-key")
        return

    logger.info("[TEST] Testing Multi-Tier LLM Fallback System")

    # Initialize with Flash fallback enabled
    llm = MultiTierLLM(
        gemini_api_key=api_key,
        enable_flash_fallback=True,
        enable_local_fallback=False  # Not implemented yet
    )

    # Test 1: Normal generation
    logger.info("Test 1: Normal Generation")

    response = llm.generate(
        prompt="Jelaskan RAG (Retrieval-Augmented Generation) dalam 2 kalimat.",
        temperature=0.7,
        max_output_tokens=100
    )

    if response.success:
        logger.info(f"[MSG] Response ({response.model_used}): {response.text}")
        logger.info(f"   Tokens: {response.tokens_used}, Latency: {response.latency_ms:.0f}ms")
    else:
        logger.error(f"[ERR] Failed: {response.error}")

    # Test 2: Multiple requests
    logger.info("Test 2: Multiple Requests (testing consistency)")

    test_prompts = [
        "Apa itu vector database?",
        "Apa perbedaan BM25 dan embedding?",
        "Jelaskan RAGAS evaluation metrics.",
    ]

    for i, prompt in enumerate(test_prompts, 1):
        logger.info(f"Request {i}: {prompt[:40]}...")
        response = llm.generate(prompt, max_output_tokens=50)

        if response.success:
            logger.info(f"   [OK] {response.model_used}: {len(response.text)} chars")
        else:
            logger.error(f"   [ERR] Failed: {response.error}")

    # Print stats
    llm.print_stats()

    logger.info("[OK] Fallback system test complete!")


if __name__ == "__main__":
    test_fallback_system()
