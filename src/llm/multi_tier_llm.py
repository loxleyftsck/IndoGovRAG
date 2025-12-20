"""
Multi-tier LLM Fallback System
Handle quota limits and API failures gracefully

Tier 1: Gemini Pro (primary)
Tier 2: Gemini Flash (faster, cheaper fallback)
Tier 3: Local model (offline mode - optional)
"""

from typing import Optional, Dict, Any, List
from enum import Enum
import time
from dataclasses import dataclass


class LLMTier(Enum):
    """LLM tier priority."""
    PRIMARY = "gemini-pro"
    FALLBACK_1 = "gemini-flash"
    FALLBACK_2 = "local-llama"  # Optional


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
        gemini_api_key: str,
        enable_flash_fallback: bool = True,
        enable_local_fallback: bool = False,
        quota_tracker = None
    ):
        """
        Initialize multi-tier LLM.
        
        Args:
            gemini_api_key: Gemini API key
            enable_flash_fallback: Enable Gemini Flash fallback
            enable_local_fallback: Enable local model fallback
            quota_tracker: Optional quota tracker instance
        """
        self.api_key = gemini_api_key
        self.enable_flash = enable_flash_fallback
        self.enable_local = enable_local_fallback
        self.quota_tracker = quota_tracker
        
        # Initialize models
        self._init_gemini_models()
        
        # Stats
        self.stats = {
            "total_requests": 0,
            "gemini_pro_success": 0,
            "gemini_flash_fallback": 0,
            "local_fallback": 0,
            "total_failures": 0,
        }
    
    def _init_gemini_models(self):
        """Initialize Gemini models."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            self.gemini_pro = genai.GenerativeModel('gemini-pro')
            
            if self.enable_flash:
                self.gemini_flash = genai.GenerativeModel('gemini-1.5-flash')
            else:
                self.gemini_flash = None
            
            print("✅ Gemini models initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            self.gemini_pro = None
            self.gemini_flash = None
    
    def _try_gemini_pro(self, prompt: str, **kwargs) -> LLMResponse:
        """Try Gemini Pro (Tier 1)."""
        if not self.gemini_pro:
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
            
            # If 'generation_config' is in kwargs, update it with defaults, then pass it.
            # Otherwise, create a new GenerationConfig object.
            if 'generation_config' in kwargs and isinstance(kwargs['generation_config'], dict):
                merged_gen_config_dict = {**default_gen_config, **kwargs['generation_config']}
                gen_config = genai.types.GenerationConfig(**merged_gen_config_dict)
                del kwargs['generation_config'] # Remove from kwargs to avoid double passing
            elif 'generation_config' in kwargs and isinstance(kwargs['generation_config'], genai.types.GenerationConfig):
                # If it's already a GenerationConfig object, we can't easily merge dicts.
                # For simplicity, we'll let the user-provided GenerationConfig take precedence.
                # If the user wants to override max_output_tokens/temperature, they should do it in their object.
                gen_config = kwargs['generation_config']
                del kwargs['generation_config']
            else:
                gen_config = genai.types.GenerationConfig(**default_gen_config)

            response = self.gemini_pro.generate_content(
                prompt,
                generation_config=gen_config,
                **kwargs
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
    
    def _try_gemini_flash(self, prompt: str, **kwargs) -> LLMResponse:
        """Try Gemini Flash (Tier 2 - faster, cheaper)."""
        if not self.gemini_flash:
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
            response = self.gemini_flash.generate_content(prompt, **kwargs)
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
    
    def generate(
        self,
        prompt: str,
        max_fallback_attempts: int = 2,
        **generation_config
    ) -> LLMResponse:
        """
        Generate response with automatic fallback.
        
        Args:
            prompt: Input prompt
            max_fallback_attempts: Max fallback tiers to try
            **generation_config: Additional generation parameters
        
        Returns:
            LLMResponse with result
        """
        self.stats["total_requests"] += 1
        
        # Try tiers in order
        tiers = [
            ("Gemini Pro", self._try_gemini_pro),
            ("Gemini Flash", self._try_gemini_flash) if self.enable_flash else None,
            ("Local Model", self._try_local_model) if self.enable_local else None,
        ]
        
        # Filter out disabled tiers
        tiers = [(name, func) for name, func in tiers if func is not None]
        
        for tier_idx, (tier_name, tier_func) in enumerate(tiers):
            if tier_idx >= max_fallback_attempts + 1:
                break
            
            print(f"🔄 Trying {tier_name}...", end=" ")
            
            response = tier_func(prompt, **generation_config)
            
            if response.success:
                print(f"✅ Success ({response.latency_ms:.0f}ms)")
                
                # Update stats
                if tier_idx == 0:
                    self.stats["gemini_pro_success"] += 1
                elif tier_idx == 1:
                    self.stats["gemini_flash_fallback"] += 1
                elif tier_idx == 2:
                    self.stats["local_fallback"] += 1
                
                return response
            else:
                print(f"❌ Failed: {response.error}")
                
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
        """Get usage statistics."""
        total = self.stats["total_requests"]
        
        return {
            **self.stats,
            "success_rate": (
                (self.stats["gemini_pro_success"] + 
                 self.stats["gemini_flash_fallback"] + 
                 self.stats["local_fallback"]) / max(total, 1)
            ),
            "fallback_rate": (
                (self.stats["gemini_flash_fallback"] + 
                 self.stats["local_fallback"]) / max(total, 1)
            ),
        }
    
    def print_stats(self):
        """Print usage statistics."""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 LLM FALLBACK STATISTICS")
        print("="*60)
        print(f"Total Requests:       {stats['total_requests']}")
        print(f"Gemini Pro Success:   {stats['gemini_pro_success']} ({stats['gemini_pro_success']/max(stats['total_requests'],1)*100:.1f}%)")
        print(f"Gemini Flash Fallback: {stats['gemini_flash_fallback']} ({stats['gemini_flash_fallback']/max(stats['total_requests'],1)*100:.1f}%)")
        print(f"Local Fallback:       {stats['local_fallback']} ({stats['local_fallback']/max(stats['total_requests'],1)*100:.1f}%)")
        print(f"Total Failures:       {stats['total_failures']} ({stats['total_failures']/max(stats['total_requests'],1)*100:.1f}%)")
        print(f"\nSuccess Rate:         {stats['success_rate']*100:.1f}%")
        print(f"Fallback Rate:        {stats['fallback_rate']*100:.1f}%")
        print("="*60 + "\n")


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
        print("❌ GEMINI_API_KEY not found in environment")
        print("   Set it in .env file or export GEMINI_API_KEY=your-key")
        return
    
    print("🧪 Testing Multi-Tier LLM Fallback System\n")
    
    # Initialize with Flash fallback enabled
    llm = MultiTierLLM(
        gemini_api_key=api_key,
        enable_flash_fallback=True,
        enable_local_fallback=False  # Not implemented yet
    )
    
    # Test 1: Normal generation
    print("Test 1: Normal Generation")
    print("-" * 60)
    
    response = llm.generate(
        prompt="Jelaskan RAG (Retrieval-Augmented Generation) dalam 2 kalimat.",
        temperature=0.7,
        max_output_tokens=100
    )
    
    if response.success:
        print(f"\n📝 Response ({response.model_used}):")
        print(f"   {response.text}")
        print(f"   Tokens: {response.tokens_used}, Latency: {response.latency_ms:.0f}ms")
    else:
        print(f"\n❌ Failed: {response.error}")
    
    # Test 2: Multiple requests
    print("\n\nTest 2: Multiple Requests (testing consistency)")
    print("-" * 60)
    
    test_prompts = [
        "Apa itu vector database?",
        "Apa perbedaan BM25 dan embedding?",
        "Jelaskan RAGAS evaluation metrics.",
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nRequest {i}: {prompt[:40]}...")
        response = llm.generate(prompt, max_output_tokens=50)
        
        if response.success:
            print(f"   ✅ {response.model_used}: {len(response.text)} chars")
        else:
            print(f"   ❌ Failed: {response.error}")
    
    # Print stats
    llm.print_stats()
    
    print("✅ Fallback system test complete!")


if __name__ == "__main__":
    test_fallback_system()
