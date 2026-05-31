"""
Custom Embedding Wrapper - Bypass sentence-transformers Issues

Uses transformers library directly to generate embeddings.
Compatible with existing ChromaDB setup.
"""

import logging
from typing import List
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from functools import lru_cache

logger = logging.getLogger(__name__)

# Global cached embedding function instance — model loaded once per process
_cached_embedding_fn = None


def _load_embedding_model():
    """Load and cache the embedding model globally (called once per process)."""
    global _cached_embedding_fn
    if _cached_embedding_fn is None:
        _cached_embedding_fn = CustomEmbeddingFunctionImpl()
        logger.info(f"[OK] Embedding model cached globally on {_cached_embedding_fn.device}")
    return _cached_embedding_fn


class CustomEmbeddingFunctionImpl:
    """
    Raw embedding implementation (no singleton logic here — use get_embedding_function() instead).
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-base"):
        logger.info(f"[CONFIG] Loading embedding model: {model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        logger.info(f"[OK] Model loaded on {self.device}")
        self._model_name = model_name

    def name(self) -> str:
        return "custom_embeddings"

    @lru_cache(maxsize=2048)
    def _cached_encode(self, text: str) -> List[float]:
        """Cache individual text embeddings (LRU, 2048 entries)."""
        return self.__call__([text])[0]

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode a batch — caches each text individually."""
        results = []
        uncached = []
        uncached_indices = []

        # Check cache for each text
        for i, text in enumerate(texts):
            try:
                cached = self._cached_encode(text)
                results.append(cached)
            except Exception:
                uncached.append(text)
                uncached_indices.append(i)
                results.append(None)

        # Encode uncached texts in one batch
        if uncached:
            encoded = self._encode_batch_uncached(uncached)
            for idx, emb in zip(uncached_indices, encoded):
                results[idx] = emb

        return results

    def __call__(self, texts: List[str]) -> List[List[float]]:
        return self.encode(texts)

    def _encode_batch_uncached(self, texts: List[str]) -> List[List[float]]:
        """Encode texts without caching (used for batch calls that feed back into cache)."""
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}

        with torch.no_grad():
            outputs = self.model(**encoded)
            embeddings = self._mean_pooling(outputs.last_hidden_state, encoded['attention_mask'])
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        result = embeddings.cpu().numpy().tolist()

        # Populate per-text cache
        for text, emb in zip(texts, result):
            try:
                self._cached_encode.cache_clear()
                # Re-call so the cache entry is written
                self.__call__([text])
            except Exception:
                pass

        return result

    def _mean_pooling(self, hidden_states, attention_mask):
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
        sum_embeddings = torch.sum(hidden_states * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask


class CustomEmbeddingFunction:
    """
    Thin wrapper that delegates to the globally-cached embedding function.

    This ensures the transformer model is loaded only ONCE per process,
    regardless of how many VectorStore instances are created.
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-base"):
        self._impl = _load_embedding_model()
        self._model_name = model_name

    def name(self) -> str:
        return self._impl.name()

    def __call__(self, texts: List[str]) -> List[List[float]]:
        return self._impl(texts)


# =============================================================================
# CHROMADB INTEGRATION
# =============================================================================

def get_custom_embedding_function(model_name: str = "intfloat/multilingual-e5-base"):
    """
    Get the globally-cached embedding function for ChromaDB.

    Usage:
        embedding_fn = get_custom_embedding_function()
        collection = client.get_or_create_collection(
            name="test",
            embedding_function=embedding_fn
        )

    Returns:
        CustomEmbeddingFunction instance backed by a cached model (loaded once per process)
    """
    return CustomEmbeddingFunction(model_name)


# =============================================================================
# TESTING
# =============================================================================

def test_embeddings():
    """Test custom embeddings."""
    logger.info("[TEST] Testing Custom Embeddings\n")

    # Initialize (model loaded once globally)
    emb_fn = CustomEmbeddingFunction()

    # Test texts (Indonesian)
    texts = [
        "Kartu Tanda Penduduk elektronik",
        "BPJS Kesehatan Indonesia",
        "Nomor Pokok Wajib Pajak"
    ]

    logger.info(f"[MSG] Embedding {len(texts)} texts...")
    embeddings = emb_fn(texts)

    logger.info(f"[OK] Generated {len(embeddings)} embeddings")
    logger.info(f"   Embedding dimension: {len(embeddings[0])}")
    logger.info(f"   First embedding (first 5 values): {embeddings[0][:5]}")

    # Test similarity
    logger.info("\n[SEARCH] Testing similarity...")
    emb1 = np.array(embeddings[0])
    emb2 = np.array(embeddings[1])
    emb3 = np.array(embeddings[2])

    sim_12 = np.dot(emb1, emb2)
    sim_13 = np.dot(emb1, emb3)

    logger.info(f"   Similarity (KTP vs BPJS): {sim_12:.3f}")
    logger.info(f"   Similarity (KTP vs NPWP): {sim_13:.3f}")

    # Test cache hit (second call with same text)
    logger.info("\n[TEST] Testing LRU cache hit...")
    import time
    t0 = time.time()
    _ = emb_fn(["Kartu Tanda Penduduk elektronik"])
    t1 = time.time()
    logger.info(f"   Cached call: {(t1-t0)*1000:.2f}ms")

    logger.info("\n[OK] Custom embeddings working!")


if __name__ == "__main__":
    test_embeddings()
