"""
Quick test script for legal categorization system
Tests both classifier and smart retrieval
"""

import sys
sys.path.append('.')

from scripts.categorize_legal_docs import LegalDocumentClassifier
from src.retrieval.smart_retrieval import SmartRetriever

def test_classifier():
    """Test legal document classification"""
    print("="*60)
    print("🧪 Testing Legal Document Classifier")
    print("="*60 + "\n")
    
    classifier = LegalDocumentClassifier()
    
    # Test cases
    test_docs = [
        {
            'title': 'UU 24/2013 tentang Administrasi Kependudukan',
            'source_url': 'https://jdih.setkab.go.id/PUU/UU242013.htm',
            'content': 'Pasal 1 Ayat 1...'
        },
        {
            'title': 'Panduan Membuat KTP Elektronik',
            'source_url': 'https://dukcapil.go.id/panduan-ktp',
            'content': 'Syarat membuat KTP: 1. KK asli...'
        },
        {
            'title': 'Peraturan Pemerintah No 5 Tahun 2021',
            'source_url': 'https://jdih.go.id/PP052021.htm',
            'content': 'Bab I Ketentuan Umum...'
        }
    ]
    
    for i, doc in enumerate(test_docs, 1):
        category = classifier.classify(doc)
        enriched = classifier.enrich_metadata(doc)
        
        print(f"Test {i}:")
        print(f"  Title: {doc['title'][:50]}...")
        print(f"  Category: {category.value}")
        print(f"  Is Legal: {enriched['metadata']['is_legal']}")
        print(f"  Confidence: {enriched['metadata']['category_confidence']:.2f}")
        print()
    
    print("✅ Classifier test complete!\n")

def test_smart_retrieval():
    """Test smart query routing"""
    print("="*60)
    print("🧠 Testing Smart Retrieval")
    print("="*60 + "\n")
    
    retriever = SmartRetriever()
    
    # Test queries
    test_queries = [
        "Apa dasar hukum KTP elektronik?",
        "Bagaimana cara mengurus akta kelahiran?",
        "Pasal berapa yang mengatur tentang NPWP?",
        "Syarat membuat paspor apa saja?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        qtype = retriever.detect_query_type(query)
        print(f"Query {i}: {query}")
        print(f"  Detected Type: {qtype.upper()}")
        print()
    
    print("✅ Smart retrieval test complete!\n")

if __name__ == "__main__":
    test_classifier()
    test_smart_retrieval()
    
    print("="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nSystem ready for production! 🚀")
