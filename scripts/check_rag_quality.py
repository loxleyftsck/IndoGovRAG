"""Simple RAG Quality Checker"""
import sys
sys.path.insert(0, '.')

from src.rag.ollama_pipeline import OllamaRAGPipeline
import time

def main():
    print("\n" + "="*60)
    print("RAG QUALITY DEBUG")
    print("="*60 + "\n")
    
    # Initialize
    print("1. Initializing pipeline...")
    p = OllamaRAGPipeline()
    
    # Check corpus
    print(f"2. Document corpus: {p.vectorstore._collection.count()} documents")
    
    # Test query
    query = "Apa syarat membuat KTP elektronik?"
    print(f"3. Testing query: {query}\n")
    
    start = time.time()
    result = p.query(query)
    elapsed = time.time() - start
    
    print(f"✅ Response time: {elapsed:.1f}s\n")
    print("="*60)
    print("ANSWER:")
    print("="*60)
    print(result['answer'])
    print("\n" + "="*60)
    print(f"Sources used: {len(result.get('sources', []))}")
    
    for i, src in enumerate(result.get('sources', [])[:3], 1):
        print(f"  {i}. {src['metadata'].get('source', 'Unknown')}")
    
    print("\n" + "="*60)
    
    # Check for quality
    answer_lower = result['answer'].lower()
    keywords = ['17 tahun', 'kartu keluarga', 'fotokopi', 'formulir']
    
    print("\nQuality Check:")
    found = sum(1 for k in keywords if k in answer_lower)
    print(f"  Expected keywords found: {found}/{len(keywords)}")
    
    if found < 2:
        print("  ⚠️  WARNING: Answer may be incomplete!")
        print("  Possible issues:")
        print("     - Document corpus lacks KTP information")
        print("     - Retrieval not finding relevant chunks")
        print("     - LLM generation issue")
    else:
        print("  ✅ Answer seems reasonable")

if __name__ == "__main__":
    main()
