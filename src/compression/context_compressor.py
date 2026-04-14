"""
Context Compression Module using LLMLingua
Reduces prompt tokens by 30% (ratio 0.7) while preserving key information

Part of Phase 1.5 Cost & Latency Optimization (BET-002)
"""

import time
import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)


class ContextCompressor:
    """
    Compress retrieved contexts before LLM generation using LLMLingua
    
    Config #8: ratio 0.7 (keep 70% of tokens, remove 30%)
    
    Features:
    - Intelligent compression preserving query-relevant content
    - Keyword whitelisting (legal terms, numbers, dates)
    - Graceful fallback on errors
    - Metrics logging
    """
    
    def __init__(
        self,
        ratio: float = 0.7,
        model_name: str = "llmlingua",
        timeout_ms: int = 1000,
        fallback_on_error: bool = True,
        whitelist_keywords: Optional[List[str]] = None
    ):
        """
        Initialize context compressor
        
        Args:
            ratio: Compression ratio (0-1). 0.7 = keep 70%, remove 30%
            model_name: "llmlingua" or "llmlingua2"
            timeout_ms: Max compression time in milliseconds
            fallback_on_error: Return uncompressed on error
            whitelist_keywords: Keywords to never compress
        """
        self.ratio = ratio
        self.timeout_ms = timeout_ms
        self.fallback_on_error = fallback_on_error
        
        # Default whitelist: legal terms, numbers, dates
        if whitelist_keywords is None:
            self.whitelist_keywords = [
                # Legal terms (Indonesian)
                "pasal", "ayat", "undang-undang", "peraturan",
                "pemerintah", "presiden", "menteri", "uu", "perpres",
                # Preserve numbers and dates
                r"\d+",  # Any numbers
                r"\d{2}/\d{2}/\d{4}",  # Dates DD/MM/YYYY
                r"\d{4}/\d+",  # Law references like 2013/24
            ]
        else:
            self.whitelist_keywords = whitelist_keywords
        
        # Initialize compressor
        try:
            from llmlingua import PromptCompressor
            
            # Choose model
            if model_name == "llmlingua2":
                model = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
            else:
                model = "NousResearch/Llama-2-7b-hf"  # Default LLMLingua
            
            self.compressor = PromptCompressor(
                model_name=model,
                device_map="auto"  # Use GPU if available
            )
            self.initialized = True
            logger.info(f"ContextCompressor initialized: model={model_name}, ratio={ratio}")
            
        except ImportError:
            logger.error("LLMLingua not installed. Run: pip install llmlingua")
            self.initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize compressor: {e}")
            self.initialized = False
    
    def compress_contexts(
        self,
        query: str,
        contexts: List[str],
        target_token: Optional[int] = None
    ) -> Dict:
        """
        Compress list of contexts while preserving query-relevant information
        
        Args:
            query: User query (used to preserve relevant content)
            contexts: List of retrieved context strings
            target_token: Optional target token count (overrides ratio)
            
        Returns:
            {
                "compressed_contexts": str,
                "original_tokens": int,
                "compressed_tokens": int,
                "compression_ratio": float,
                "latency_ms": float,
                "success": bool,
                "error": Optional[str]
            }
        """
        start_time = time.time()
        
        # Check if initialized
        if not self.initialized:
            error_msg = "Compressor not initialized (LLMLingua missing)"
            logger.warning(error_msg)
            if self.fallback_on_error:
                return self._fallback_response(contexts, error_msg, start_time)
            else:
                raise RuntimeError(error_msg)
        
        # Combine contexts with markers
        full_context = self._prepare_contexts(contexts)
        
        # Protect whitelisted keywords
        protected_context, replacements = self._protect_keywords(full_context)
        
        try:
            # Compress with timeout
            compressed = self._compress_with_timeout(
                protected_context,
                query,
                target_token
            )
            
            # Restore protected keywords
            compressed_text = self._restore_keywords(
                compressed['compressed_prompt'],
                replacements
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "compressed_contexts": compressed_text,
                "original_tokens": compressed['origin_tokens'],
                "compressed_tokens": compressed['compressed_tokens'],
                "compression_ratio": compressed['compressed_tokens'] / compressed['origin_tokens'],
                "latency_ms": latency_ms,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Compression failed: {str(e)}"
            logger.error(error_msg)
            
            if self.fallback_on_error:
                return self._fallback_response(contexts, error_msg, start_time)
            else:
                raise
    
    def _prepare_contexts(self, contexts: List[str]) -> str:
        """Combine contexts with document markers"""
        marked = []
        for i, ctx in enumerate(contexts):
            marked.append(f"[Dokumen {i+1}]\n{ctx}")
        return "\n\n".join(marked)
    
    def _protect_keywords(self, text: str) -> tuple:
        """
        Replace whitelisted keywords with placeholders to prevent compression
        
        Returns:
            (protected_text, replacements_dict)
        """
        replacements = {}
        protected = text
        
        for i, keyword in enumerate(self.whitelist_keywords):
            # Find all matches (handles regex patterns)
            matches = re.finditer(keyword, text, re.IGNORECASE)
            for match in matches:
                original = match.group()
                placeholder = f"__PROTECTED_{i}_{len(replacements)}__"
                replacements[placeholder] = original
                protected = protected.replace(original, placeholder, 1)
        
        return protected, replacements
    
    def _restore_keywords(self, compressed_text: str, replacements: Dict) -> str:
        """Restore protected keywords from placeholders"""
        restored = compressed_text
        for placeholder, original in replacements.items():
            restored = restored.replace(placeholder, original)
        return restored
    
    def _compress_with_timeout(self, text: str, query: str, target_token: Optional[int]) -> Dict:
        """Compress with timeout protection"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Compression exceeded {self.timeout_ms}ms")
        
        # Set timeout (Unix only)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_ms // 1000)  # Convert to seconds
        except AttributeError:
            # Windows doesn't support SIGALRM, skip timeout
            pass
        
        try:
            compressed = self.compressor.compress_prompt(
                text,
                rate=self.ratio,
                target_token=target_token,
                condition_in_question=query,  # Keep query-relevant content
                condition_compare=True,
                use_sentence_level_filter=True
            )
            return compressed
        finally:
            try:
                signal.alarm(0)  # Cancel timeout
            except AttributeError:
                pass
    
    def _fallback_response(self, contexts: List[str], error: str, start_time: float) -> Dict:
        """Return uncompressed contexts as fallback"""
        full_context = self._prepare_contexts(contexts)
        latency_ms = (time.time() - start_time) * 1000
        
        # Estimate tokens (rough: 1 token ≈ 4 chars)
        estimated_tokens = len(full_context) // 4
        
        logger.warning(f"Compression failed, returning uncompressed. Error: {error}")
        
        return {
            "compressed_contexts": full_context,
            "original_tokens": estimated_tokens,
            "compressed_tokens": estimated_tokens,
            "compression_ratio": 1.0,  # No compression
            "latency_ms": latency_ms,
            "success": False,
            "error": error
        }
    
    def get_stats(self) -> Dict:
        """Get compressor statistics"""
        return {
            "initialized": self.initialized,
            "ratio": self.ratio,
            "timeout_ms": self.timeout_ms,
            "fallback_enabled": self.fallback_on_error,
            "whitelist_count": len(self.whitelist_keywords)
        }
