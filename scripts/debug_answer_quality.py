"""
Comprehensive RAG Answer Quality Debugger

Systematically checks all components:
1. Document corpus quality
2. Retrieval effectiveness  
3. Prompt engineering
4. LLM generation quality
"""

import sys
sys.path.insert(0, '.')

from src.rag.ollama_pipeline import OllamaRAGPipeline
import json

def check_document_corpus():
    """Check what documents are available"""
    print("="*60)
    print("1. CHECKING DOCUMENT CORPUS")
    print("="*60)
    
    pipeline = OllamaRAGPipeline()
    
    # Get collection info
    collection = pipeline.retriever.vectorstore._collection
    count = collection.count()
    
    print(f"✅ Total documents in vector store: {count}")
    
    # Sample some documents
    results = collection.get(limit=5, include=['documents', 'metadatas'])
    
    print(f"\n📄 Sample documents:")
    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
        print(f"\n{i}. Source: {meta.get('source', 'Unknown')}")
        print(f"   Preview: {doc[:150]}...")
    
    print("\n" + "="*60 + "\n")
    return count

def test_retrieval(query: str):
    """Test retrieval quality for a query"""
    print("="*60)
    print("2. TESTING RETRIEVAL")
    print("="*60)
    print(f"Query: {query}\n")
    
    pipeline = OllamaRAGPipeline()
    
    # Get raw retrieval results
    retriever = pipeline.retriever
    results = retriever.retrieve(query, top_k=5)
    
    print(f"✅ Retrieved: {len(results)} chunks\n")
    
    for i, chunk in enumerate(results, 1):
        print(f"\n{i}. Score: {chunk.get('score', 0):.3f}")
        print(f"   Source: {chunk['metadata'].get('source', 'Unknown')}")
        print(f"   Content: {chunk['content'][:200]}...")
    
    print("\n" + "="*60 + "\n")
    return results

def test_generation(query: str, context: str):
    """Test LLM generation with given context"""
    print("="*60)
    print("3. TESTING LLM GENERATION")
    print("="*60)
    
    from src.llm.ollama_llm import OllamaLLM
    
    llm = OllamaLLM(model="llama3.1:8b-instruct-q4_K_M")
    
    prompt = f"""Berdasarkan konteks berikut, jawab pertanyaan dengan akurat dan lengkap.

Konteks:
{context}

Pertanyaan: {query}

Jawaban (dalam bahasa Indonesia, lengkap dan akurat):"""
    
    print(f"📝 Generating answer...")
    print(f"   Model: llama3.1:8b-instruct-q4_K_M")
    print(f"   Context length: {len(context)} chars\n")
    
    answer = llm.generate(prompt)
    
    print(f"✅ Generated Answer:")
    print(f"{answer}\n")
    
    print("="*60 + "\n")
    return answer

def full_pipeline_test(query: str):
    """Test full RAG pipeline"""
    print("="*60)
    print("4. FULL PIPELINE TEST")
    print("="*60)
    print(f"Query: {query}\n")
    
    pipeline = OllamaRAGPipeline()
    
    print("🚀 Running full RAG pipeline...\n")
    result = pipeline.query(query)
    
    print(f"✅ Answer:")
    print(f"{result['answer']}\n")
    
    print(f"📚 Sources used: {len(result.get('sources', []))}")
    for i, source in enumerate(result.get('sources', [])[:3], 1):
        print(f"   {i}. {source['metadata'].get('source', 'Unknown')}")
    
    print("\n" + "="*60 + "\n")
    return result

def diagnose_answer_quality(query: str, expected_keywords: list):
    """Diagnose why answer might be incorrect"""
    print("="*60)
    print("5. ANSWER QUALITY DIAGNOSIS")
    print("="*60)
    
    # Run full test
    result = full_pipeline_test(query)
    answer = result['answer']
    
    # Check for expected keywords
    print(f"\n🔍 Checking for expected content:\n")
    
    missing_keywords = []
    found_keywords = []
    
    for keyword in expected_keywords:
        if keyword.lower() in answer.lower():
            found_keywords.append(keyword)
            print(f"   ✅ Found: '{keyword}'")
        else:
            missing_keywords.append(keyword)
            print(f"   ❌ Missing: '{keyword}'")
    
    # Diagnosis
    print(f"\n📊 Diagnosis:")
    print(f"   Keywords found: {len(found_keywords)}/{len(expected_keywords)}")
    
    if len(missing_keywords) > len(found_keywords):
        print(f"   ⚠️  ISSUE: Answer missing critical information!")
        print(f"   Possible causes:")
        print(f"      1. Relevant documents not in corpus")
        print(f"      2. Retrieval not finding right chunks")
        print(f"      3. LLM not extracting information correctly")
        print(f"      4. Prompt engineering needs improvement")
    else:
        print(f"   ✅ Answer seems adequate")
    
    print("\n" + "="*60 + "\n")
    
    return {
        'answer': answer,
        'found_keywords': found_keywords,
        'missing_keywords': missing_keywords,
        'quality_score': len(found_keywords) / len(expected_keywords)
    }

def main():
    """Run comprehensive debugging"""
    print("""
    🔬 RAG ANSWER QUALITY DEBUGGER
    ===============================
    Comprehensive testing of all RAG components
    
    """)
    
    # Test query
    query = "Apa syarat membuat KTP elektronik?"
    expected = [
        "17 tahun",
        "Kartu Keluarga",
        "fotokopi",
        "formulir",
        "domisili"
    ]
    
    # Step 1: Check corpus
    doc_count = check_document_corpus()
    
    if doc_count < 10:
        print("⚠️  WARNING: Very few documents in corpus (< 10)")
        print("   This will severely limit answer quality!")
        print("   Recommendation: Add more government document sources\n")
    
    # Step 2: Test retrieval
    chunks = test_retrieval(query)
    
    if not chunks:
        print("❌ CRITICAL: No documents retrieved!")
        print("   System cannot answer without context")
        print("   Check: Document corpus and embedding model\n")
        return
    
    # Step 3: Test generation with retrieved context
    context = "\n\n".join([c['content'] for c in chunks[:3]])
    generated = test_generation(query, context)
    
    # Step 4: Full pipeline
    diagnosis = diagnose_answer_quality(query, expected)
    
    # Final recommendation
    print("="*60)
    print("🎯 RECOMMENDATIONS")
    print("="*60)
    
    if diagnosis['quality_score'] < 0.5:
        print("\n⚠️  ANSWER QUALITY: POOR")
        print("\nPriority Actions:")
        print("1. Add more specific documents about KTP elektronik")
        print("2. Improve chunking strategy (currently 500 tokens)")
        print("3. Test with different prompts")
        print("4. Consider fine-tuning retrieval threshold")
    elif diagnosis['quality_score'] < 0.8:
        print("\n⚠️  ANSWER QUALITY: MODERATE")
        print("\nSuggested Improvements:")
        print("1. Add supplementary documents")
        print("2. Optimize prompt for completeness")
        print("3. Increase retrieval top_k (current: 5)")
    else:
        print("\n✅ ANSWER QUALITY: GOOD")
        print("\nAnswer contains most expected information")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
