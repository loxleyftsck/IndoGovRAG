"""
Custom Embedding Wrapper - Bypass sentence-transformers Issues

Uses transformers library directly to generate embeddings.
Compatible with existing ChromaDB setup.
"""

from typing import List
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np


class CustomEmbeddingFunction:
    """
    Custom embedding function for ChromaDB.
    
    Uses transformers directly instead of sentence-transformers.
    """
    
    def __init__(self, model_name: str = "intfloat/multilingual-e5-base"):
        """
        Initialize embedding model.
        
        Args:
            model_name: HuggingFace model name
        """
        print(f"🔧 Loading embedding model: {model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()  # Set to evaluation mode
        
        # Move to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        
        print(f"✅ Model loaded on {self.device}")
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        # Tokenize
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        
        # Move to device
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**encoded)
            
            # Mean pooling
            embeddings = self._mean_pooling(
                outputs.last_hidden_state,
                encoded['attention_mask']
            )
            
            # Normalize
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        # Convert to list
        return embeddings.cpu().numpy().tolist()
    
    def _mean_pooling(self, hidden_states, attention_mask):
        """Mean pooling over token embeddings."""
        # Expand attention mask
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
        
        # Sum embeddings
        sum_embeddings = torch.sum(hidden_states * input_mask_expanded, 1)
        
        # Count tokens
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        return sum_embeddings / sum_mask


# =============================================================================
# CHROMADB INTEGRATION
# =============================================================================

def get_custom_embedding_function(model_name: str = "intfloat/multilingual-e5-base"):
    """
    Get custom embedding function for ChromaDB.
    
    Usage:
        embedding_fn = get_custom_embedding_function()
        collection = client.get_or_create_collection(
            name="test",
            embedding_function=embedding_fn
        )
    
    Returns:
        CustomEmbeddingFunction instance
    """
    return CustomEmbeddingFunction(model_name)


# =============================================================================
# TESTING
# =============================================================================

def test_embeddings():
    """Test custom embeddings."""
    print("🧪 Testing Custom Embeddings\n")
    
    # Initialize
    emb_fn = CustomEmbeddingFunction()
    
    # Test texts (Indonesian)
    texts = [
        "Kartu Tanda Penduduk elektronik",
        "BPJS Kesehatan Indonesia",
        "Nomor Pokok Wajib Pajak"
    ]
    
    print(f"📝 Embedding {len(texts)} texts...")
    embeddings = emb_fn(texts)
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    print(f"   Embedding dimension: {len(embeddings[0])}")
    print(f"   First embedding (first 5 values): {embeddings[0][:5]}")
    
    # Test similarity
    print("\n🔍 Testing similarity...")
    emb1 = np.array(embeddings[0])
    emb2 = np.array(embeddings[1])
    emb3 = np.array(embeddings[2])
    
    sim_12 = np.dot(emb1, emb2)
    sim_13 = np.dot(emb1, emb3)
    
    print(f"   Similarity (KTP vs BPJS): {sim_12:.3f}")
    print(f"   Similarity (KTP vs NPWP): {sim_13:.3f}")
    
    print("\n✅ Custom embeddings working!")


if __name__ == "__main__":
    test_embeddings()
