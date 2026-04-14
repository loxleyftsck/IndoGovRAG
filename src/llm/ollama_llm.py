"""
Ollama LLM Wrapper - Local LLM via Ollama
Zero cost, privacy-first alternative to cloud LLM APIs

Features:
- Local inference (no API costs)
- Multi-model support
- Indonesian language optimized
- Drop-in replacement for cloud LLMs
"""

import requests
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OllamaLLM:
    """
    Local LLM via Ollama HTTP API
    
    Example:
        llm = OllamaLLM(model="llama3.1:8b")
        response = llm.generate("Apa itu KTP elektronik?")
        print(response['text'])
    """
    
    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434"
    ):
        """
        Initialize Ollama LLM client
        
        Args:
            model: Ollama model name (e.g., 'llama3.1:8b', 'qwen2.5:7b')
            base_url: Ollama server URL
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/chat"
        
        # Statistics
        self.stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_errors": 0,
            "avg_latency_ms": 0.0
        }
        
        # Verify Ollama is running
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama server is accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if self.model in model_names:
                    logger.info(f"✅ Ollama connected: {self.model} available")
                else:
                    logger.warning(f"⚠️ Model {self.model} not found. Available: {model_names}")
                    logger.info(f"Run: ollama pull {self.model}")
            else:
                logger.warning(f"⚠️ Ollama server not responding correctly")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ollama not running at {self.base_url}: {e}")
            logger.info("Start Ollama: Keep `ollama serve` running or use Ollama desktop app")
    
    def generate(self, prompt: str, **kwargs) -> Dict:
        """
        Generate response using Ollama
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
                - temperature: float (default: 0.7)
                - max_tokens: int (default: 2048)
                - top_p: float (default: 0.9)
                
        Returns:
            Dict with:
                - text: str - Generated response
                - model: str - Model used
                - tokens: int - Estimated tokens
                - success: bool - Whether generation succeeded
                - latency_ms: float - Generation time
        """
        start_time = time.time()
        self.stats["total_calls"] += 1
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Anda adalah asisten AI yang membantu menjawab pertanyaan tentang dokumen pemerintah Indonesia. Berikan jawaban yang akurat, jelas, dan berbasis pada konteks yang diberikan."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 2048),
                    "top_p": kwargs.get("top_p", 0.9),
                }
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=kwargs.get("timeout", 120)  # Ollama can be slow
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract text from response
            text = data.get("message", {}).get("content", "")
            
            # Estimate tokens (rough approximation: 1.3 tokens per word)
            tokens = int(len(text.split()) * 1.3)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Update stats
            self.stats["total_tokens"] += tokens
            self.stats["avg_latency_ms"] = (
                (self.stats["avg_latency_ms"] * (self.stats["total_calls"] - 1) + latency_ms) /
                self.stats["total_calls"]
            )
            
            return {
                "text": text,
                "model": self.model,
                "tokens": tokens,
                "success": True,
                "latency_ms": latency_ms
            }
            
        except requests.exceptions.Timeout:
            self.stats["total_errors"] += 1
            logger.error(f"Ollama timeout after {kwargs.get('timeout', 120)}s")
            return {
                "text": "Maaf, sistem AI lokal sedang lambat. Silakan coba lagi.",
                "model": "error",
                "tokens": 0,
                "success": False,
                "error": "timeout",
                "latency_ms": (time.time() - start_time) * 1000
            }
            
        except requests.exceptions.RequestException as e:
            self.stats["total_errors"] += 1
            logger.error(f"Ollama API error: {e}")
            return {
                "text": "Maaf, terjadi kesalahan pada sistem AI lokal.",
                "model": "error",
                "tokens": 0,
                "success": False,
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000
            }
    
    def get_stats(self) -> Dict:
        """Get LLM usage statistics"""
        return {
            "backend": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            **self.stats
        }


# Singleton instance
_ollama_llm = None


def get_ollama_llm(model: str = "llama3.1:8b") -> OllamaLLM:
    """Get global OllamaLLM instance (singleton)"""
    global _ollama_llm
    if _ollama_llm is None or _ollama_llm.model != model:
        _ollama_llm = OllamaLLM(model=model)
    return _ollama_llm
