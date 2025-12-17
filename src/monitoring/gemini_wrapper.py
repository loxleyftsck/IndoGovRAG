"""
Gemini API Wrapper with Automatic Quota Tracking
100% FREE - No external services needed!

Usage:
    from src.monitoring.gemini_wrapper import GeminiClient
    
    client = GeminiClient(api_key="your-key")
    response = client.generate(prompt="What is RAG?")
    
    # Quota tracked automatically!
"""

import google.generativeai as genai
from typing import Optional, Dict, List
import time
from src.monitoring.gemini_quota_tracker import GeminiQuotaTracker


class GeminiClient:
    """Gemini API client with built-in quota tracking."""
    
    def __init__(
        self, 
        api_key: str,
        model_name: str = "gemini-pro",
        quota_tracker: Optional[GeminiQuotaTracker] = None
    ):
        """
        Initialize Gemini client with quota tracking.
        
        Args:
            api_key: Your Gemini API key
            model_name: Model to use (default: gemini-pro)
            quota_tracker: Optional custom tracker (creates one if None)
        """
        self.api_key = api_key
        self.model_name = model_name
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Setup quota tracker
        self.tracker = quota_tracker or GeminiQuotaTracker()
    
    def _count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Note: This is an approximation. Ideally use model.count_tokens()
        but keeping this simple for free tier.
        """
        # Simple approximation: ~4 chars per token
        return len(text) // 4
    
    def generate(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: int = 60,
        **generation_config
    ) -> Dict:
        """
        Generate response with automatic quota tracking and retry logic.
        
        Args:
            prompt: Input prompt
            max_retries: Max retries on rate limit (default: 3)
            retry_delay: Seconds to wait between retries (default: 60)
            **generation_config: Additional config (temperature, max_tokens, etc.)
        
        Returns:
            Dict with response, quota info, and alerts
        """
        # Check if we should throttle BEFORE making request
        should_throttle, reason = self.tracker.should_throttle()
        if should_throttle:
            print(f"⏸️  Pre-check throttle: {reason}")
            print(f"   Waiting {retry_delay}s before retry...")
            time.sleep(retry_delay)
        
        # Estimate input tokens
        input_tokens = self._count_tokens(prompt)
        
        # Try making the request
        for attempt in range(max_retries):
            try:
                # Make API call
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Estimate output tokens
                response_text = response.text if hasattr(response, 'text') else ""
                output_tokens = self._count_tokens(response_text)
                
                # Track quota
                tracking_result = self.tracker.track_request(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=self.model_name,
                    query_preview=prompt[:100]
                )
                
                # Print alerts if any
                if tracking_result["alerts"]:
                    print(f"\n{'='*60}")
                    print("⚠️  QUOTA ALERTS:")
                    for alert in tracking_result["alerts"]:
                        print(f"   {alert['message']}")
                    print(f"{'='*60}\n")
                
                return {
                    "success": True,
                    "response": response_text,
                    "raw_response": response,
                    "quota": tracking_result,
                }
            
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a quota/rate limit error
                if "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"⏸️  Rate limit hit (attempt {attempt+1}/{max_retries})")
                        print(f"   Waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {
                            "success": False,
                            "error": "Rate limit exceeded after max retries",
                            "error_details": error_msg,
                        }
                else:
                    # Other error, don't retry
                    return {
                        "success": False,
                        "error": "API error",
                        "error_details": error_msg,
                    }
        
        return {
            "success": False,
            "error": "Max retries exceeded",
        }
    
    def generate_batch(
        self,
        prompts: List[str],
        delay_between_requests: float = 0.5,
        **generation_config
    ) -> List[Dict]:
        """
        Generate responses for multiple prompts with automatic pacing.
        
        Args:
            prompts: List of input prompts
            delay_between_requests: Seconds to wait between requests (default: 0.5)
            **generation_config: Additional config for generation
        
        Returns:
            List of response dicts
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"Processing {i+1}/{len(prompts)}...", end=" ")
            
            result = self.generate(prompt, **generation_config)
            results.append(result)
            
            if result["success"]:
                print("✅")
            else:
                print(f"❌ {result.get('error', 'Unknown error')}")
            
            # Wait before next request (respect rate limits)
            if i < len(prompts) - 1:
                time.sleep(delay_between_requests)
        
        return results
    
    def get_quota_status(self) -> Dict:
        """Get current quota usage status."""
        return self.tracker.get_status()
    
    def print_quota_status(self):
        """Print human-readable quota status."""
        self.tracker.print_status()


# =============================================================================
# DEMO / TESTING
# =============================================================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment!")
        print("💡 Set it in .env file or export GEMINI_API_KEY=your-key")
        exit(1)
    
    print("🧪 Testing Gemini Client with Quota Tracking\n")
    
    # Initialize client
    client = GeminiClient(api_key=api_key)
    
    # Check initial status
    client.print_quota_status()
    
    # Test single generation
    print("📝 Testing single generation...\n")
    result = client.generate(
        prompt="Explain RAG (Retrieval-Augmented Generation) in 2 sentences.",
        temperature=0.7,
        max_output_tokens=100
    )
    
    if result["success"]:
        print(f"✅ Response: {result['response']}\n")
    else:
        print(f"❌ Error: {result['error']}\n")
    
    # Test batch generation
    print("📝 Testing batch generation...\n")
    test_prompts = [
        "What is a vector database?",
        "What is semantic search?",
        "What is chunking in RAG?",
    ]
    
    batch_results = client.generate_batch(test_prompts)
    
    print(f"\n✅ Processed {len(batch_results)} prompts")
    print(f"   Successful: {sum(1 for r in batch_results if r['success'])}")
    print(f"   Failed: {sum(1 for r in batch_results if not r['success'])}")
    
    # Check final status
    print()
    client.print_quota_status()
